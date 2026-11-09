"""Noeud 'carte' : affiche la ville de la tortue dans RViz et permet de la piloter a la souris.

Ce que fait ce noeud :
  - TF          : publie la transformation  world -> turtle1  a partir de /turtle1/pose
                  (RViz sait ainsi ou se trouve la tortue)
  - TOPIC       : publie le trajet parcouru sur /trajet          (nav_msgs/msg/Path)
  - TOPIC       : publie un dessin de la tortue sur /tortue_marker (visualization_msgs/msg/Marker)
  - MARQUEURS INTERACTIFS (serveur 'carte') :
      * chaque lieu de lieux.py est un bouton : un clic publie son nom sur /destination
      * un drapeau rouge deplacable : clic droit > "Livrer ici" publie sa position
        sur /destination_point (geometry_msgs/msg/PointStamped)

Le repere 'world' correspond a la fenetre turtlesim : (0, 0) en bas a gauche, (11, 11) en haut a droite.
"""

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PointStamped, PoseStamped, TransformStamped
from interactive_markers import InteractiveMarkerServer, MenuHandler
from nav_msgs.msg import Path
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster
from turtlesim.msg import Pose
from visualization_msgs.msg import InteractiveMarker, InteractiveMarkerControl, Marker

from tortue_livreuse.lieux import LIEUX

REPERE = 'world'

# >>> MODIFIABLE : couleur (rouge, vert, bleu entre 0 et 1) des lieux dans RViz
COULEUR_LIEUX = (0.2, 0.4, 1.0)


def quaternion_depuis_cap(theta):
    """Convertit un angle autour de l'axe z (radians) en quaternion (x, y, z, w)."""
    return 0.0, 0.0, math.sin(theta / 2.0), math.cos(theta / 2.0)


def forme(type_marker, echelle, couleur, z=0.0):
    """Petit utilitaire pour creer un Marker (forme simple) deja colore."""
    m = Marker()
    m.type = type_marker
    m.scale.x, m.scale.y, m.scale.z = echelle
    m.color.r, m.color.g, m.color.b = couleur
    m.color.a = 1.0
    m.pose.position.z = z
    m.pose.orientation.w = 1.0
    return m


class Carte(Node):

    def __init__(self):
        super().__init__('carte')

        # TF : diffuseur de transformations
        self.tf = TransformBroadcaster(self)

        # TOPICS
        self.create_subscription(Pose, 'turtle1/pose', self.recevoir_pose, 10)
        self.pub_destination = self.create_publisher(String, 'destination', 10)
        self.pub_point = self.create_publisher(PointStamped, 'destination_point', 10)
        self.pub_trajet = self.create_publisher(Path, 'trajet', 10)
        self.pub_tortue = self.create_publisher(Marker, 'tortue_marker', 10)

        self.trajet = Path()
        self.trajet.header.frame_id = REPERE
        self.dernier_point = None

        # MARQUEURS INTERACTIFS
        self.serveur = InteractiveMarkerServer(self, 'carte')
        for nom, (x, y) in LIEUX.items():
            self.ajouter_lieu(nom, x, y)
        self.ajouter_drapeau(5.5, 3.5)
        self.serveur.applyChanges()

        self.create_timer(0.5, self.publier_tortue)
        self.get_logger().info('Carte prete : ouvrez RViz (repere fixe "world")')

    # ------------------------------------------------------- TF + trajet
    def recevoir_pose(self, pose):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = REPERE          # repere parent
        t.child_frame_id = 'turtle1'        # repere enfant
        t.transform.translation.x = pose.x
        t.transform.translation.y = pose.y
        (t.transform.rotation.x, t.transform.rotation.y,
         t.transform.rotation.z, t.transform.rotation.w) = quaternion_depuis_cap(pose.theta)
        self.tf.sendTransform(t)

        # On ajoute un point au trajet seulement si la tortue a bouge
        if self.dernier_point is None or abs(pose.x - self.dernier_point[0]) + abs(pose.y - self.dernier_point[1]) > 0.05:
            p = PoseStamped()
            p.header.frame_id = REPERE
            p.pose.position.x, p.pose.position.y = pose.x, pose.y
            self.trajet.poses.append(p)
            self.trajet.poses = self.trajet.poses[-2000:]
            self.dernier_point = (pose.x, pose.y)
            self.trajet.header.stamp = t.header.stamp
            self.pub_trajet.publish(self.trajet)

    def publier_tortue(self):
        # Le marker est exprime dans le repere 'turtle1' : il suit la TF automatiquement
        m = forme(Marker.ARROW, (0.6, 0.25, 0.25), (0.1, 0.8, 0.2), z=0.15)
        m.header.frame_id = 'turtle1'
        m.ns, m.id = 'tortue', 0
        m.frame_locked = True
        self.pub_tortue.publish(m)

    # ------------------------------------------------------- lieux cliquables
    def ajouter_lieu(self, nom, x, y):
        im = InteractiveMarker()
        im.header.frame_id = REPERE
        im.name = f'lieu_{nom}'
        im.description = nom
        im.pose.position.x, im.pose.position.y = x, y
        im.pose.orientation.w = 1.0
        im.scale = 1.0

        bouton = InteractiveMarkerControl()
        bouton.interaction_mode = InteractiveMarkerControl.BUTTON
        bouton.always_visible = True
        bouton.markers.append(forme(Marker.CYLINDER, (0.6, 0.6, 0.1), COULEUR_LIEUX))
        im.controls.append(bouton)

        self.serveur.insert(im, feedback_callback=self.clic_lieu)

    def clic_lieu(self, feedback):
        if feedback.event_type != feedback.BUTTON_CLICK:
            return
        nom = feedback.marker_name.removeprefix('lieu_')
        self.get_logger().info(f'Clic sur {nom} : envoi sur /destination')
        self.pub_destination.publish(String(data=nom))

    # ------------------------------------------------------- drapeau deplacable
    def ajouter_drapeau(self, x, y):
        im = InteractiveMarker()
        im.header.frame_id = REPERE
        im.name = 'drapeau'
        im.description = 'Clic droit > Livrer ici'
        im.pose.position.x, im.pose.position.y = x, y
        im.pose.orientation.w = 1.0
        im.scale = 1.0

        # Controle "deplacer dans le plan" : le plan est perpendiculaire a l'axe
        # donne par l'orientation du controle (ici l'axe z -> plan x/y du sol)
        glisser = InteractiveMarkerControl()
        glisser.interaction_mode = InteractiveMarkerControl.MOVE_PLANE
        glisser.orientation.w = 0.7071
        glisser.orientation.y = 0.7071
        glisser.always_visible = True
        glisser.markers.append(forme(Marker.SPHERE, (0.4, 0.4, 0.4), (1.0, 0.1, 0.1), z=0.2))
        im.controls.append(glisser)

        # Le menu s'ouvre au clic droit sur le drapeau
        menu_ctrl = InteractiveMarkerControl()
        menu_ctrl.interaction_mode = InteractiveMarkerControl.MENU
        im.controls.append(menu_ctrl)

        self.serveur.insert(im)
        self.menu = MenuHandler()
        self.menu.insert('Livrer ici', callback=self.livrer_au_drapeau)
        self.menu.apply(self.serveur, 'drapeau')

    def livrer_au_drapeau(self, feedback):
        p = PointStamped()
        p.header.frame_id = REPERE
        p.header.stamp = self.get_clock().now().to_msg()
        p.point.x = feedback.pose.position.x
        p.point.y = feedback.pose.position.y
        self.get_logger().info(f'Drapeau en ({p.point.x:.1f}, {p.point.y:.1f}) : envoi sur /destination_point')
        self.pub_point.publish(p)


def main(args=None):
    rclpy.init(args=args)
    node = Carte()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
