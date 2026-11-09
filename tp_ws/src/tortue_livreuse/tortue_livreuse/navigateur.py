"""Noeud 'navigateur' : conduit la tortue jusqu'a un lieu nomme.

Deroulement d'une livraison :
  1. On recoit un nom de lieu sur le topic /destination      (TOPIC, abonnement)
     ou des coordonnees sur /destination_point (envoyees par exemple depuis RViz)
  2. La tortue s'oriente vers le lieu                         (ACTION, client)
     -> action /turtle1/rotate_absolute fournie par turtlesim
  3. La tortue avance tout droit jusqu'au lieu                (TOPICS)
     -> lit sa position sur /turtle1/pose, envoie ses vitesses sur /turtle1/cmd_vel
  4. Arrivee : on previent la fabrique de colis               (SERVICE, client)
     -> service /livraison fourni par le noeud 'fabrique'

Le noeud publie aussi son etat sur le topic /statut (texte lisible).

Pour envoyer une tortue a la boulangerie :
  ros2 topic pub --once /destination std_msgs/msg/String "{data: boulangerie}"
"""

import math

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import PointStamped, Twist
from std_msgs.msg import String
from std_srvs.srv import Trigger
from turtlesim.action import RotateAbsolute
from turtlesim.msg import Pose

from tortue_livreuse.lieux import LIEUX

# >>> MODIFIABLE : distance (en metres turtlesim) a partir de laquelle on considere
#     que la tortue est arrivee.
TOLERANCE = 0.1


class Navigateur(Node):

    def __init__(self):
        super().__init__('navigateur')

        # PARAMETRE : vitesse lineaire max, modifiable a chaud :
        #   ros2 param set /navigateur vitesse 4.0
        self.declare_parameter('vitesse', 2.0)

        # TOPICS
        self.create_subscription(String, 'destination', self.recevoir_destination, 10)
        self.create_subscription(PointStamped, 'destination_point', self.recevoir_point, 10)
        self.create_subscription(Pose, 'turtle1/pose', self.recevoir_pose, 10)
        self.pub_vitesse = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)
        self.pub_statut = self.create_publisher(String, 'statut', 10)

        # ACTION (client) : rotation fournie par turtlesim
        self.client_rotation = ActionClient(self, RotateAbsolute, 'turtle1/rotate_absolute')

        # SERVICE (client) : fourni par le noeud 'fabrique'
        self.client_livraison = self.create_client(Trigger, 'livraison')

        self.pose = None          # derniere position connue de la tortue
        self.cible = None         # (nom, x, y) du lieu vise, None si au repos
        self.en_route = False     # True pendant la phase "avancer tout droit"

        # Boucle de conduite : 10 fois par seconde
        self.create_timer(0.1, self.conduire)

        self.annoncer(f'Pret. Lieux connus : {", ".join(LIEUX)}')

    # ------------------------------------------------------------------ outils
    def annoncer(self, texte):
        """Affiche dans le terminal ET publie sur le topic /statut."""
        self.get_logger().info(texte)
        self.pub_statut.publish(String(data=texte))

    def recevoir_pose(self, msg):
        self.pose = msg

    # --------------------------------------------------- 1. ordre de livraison
    def recevoir_destination(self, msg):
        """Ordre par NOM de lieu (topic /destination)."""
        nom = msg.data.strip().lower()
        if nom not in LIEUX:
            self.get_logger().warn(f'Lieu inconnu "{nom}". Lieux connus : {", ".join(LIEUX)}')
            return
        x, y = LIEUX[nom]
        self.partir(nom, x, y)

    def recevoir_point(self, msg):
        """Ordre par COORDONNEES (topic /destination_point, envoye par exemple depuis RViz)."""
        x = min(max(msg.point.x, 0.5), 10.5)   # on reste dans la fenetre turtlesim
        y = min(max(msg.point.y, 0.5), 10.5)
        self.partir('point libre', x, y)

    def partir(self, nom, x, y):
        if self.cible is not None:
            self.get_logger().warn(f'Deja en livraison vers {self.cible[0]}, ordre "{nom}" ignore')
            return
        if self.pose is None:
            self.get_logger().warn('Position de la tortue encore inconnue (turtlesim lance ?)')
            return

        self.cible = (nom, x, y)
        self.annoncer(f'Nouvelle livraison : {nom} ({x}, {y})')
        self.orienter_vers(x, y)

    # ------------------------------------------------- 2. s'orienter (ACTION)
    def orienter_vers(self, x, y):
        angle = math.atan2(y - self.pose.y, x - self.pose.x)
        if not self.client_rotation.wait_for_server(timeout_sec=2.0):
            self.get_logger().error('Action turtle1/rotate_absolute indisponible')
            self.cible = None
            return

        but = RotateAbsolute.Goal()
        but.theta = angle
        self.annoncer(f'Rotation vers {math.degrees(angle):.0f} degres...')
        envoi = self.client_rotation.send_goal_async(but, feedback_callback=self.retour_rotation)
        envoi.add_done_callback(self.but_accepte)

    def retour_rotation(self, feedback_msg):
        # FEEDBACK de l'action : angle restant a parcourir
        reste = feedback_msg.feedback.remaining
        self.get_logger().info(f'  ... reste {math.degrees(reste):.0f} degres', throttle_duration_sec=0.3)

    def but_accepte(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Rotation refusee par turtlesim')
            self.cible = None
            return
        handle.get_result_async().add_done_callback(self.rotation_terminee)

    def rotation_terminee(self, future):
        # RESULTAT de l'action : angle effectivement parcouru
        # (turtlesim le renvoie avec un signe inverse, on affiche donc sa valeur absolue)
        delta = future.result().result.delta
        self.annoncer(f'Orientee (rotation de {abs(math.degrees(delta)):.0f} degres). En route !')
        self.en_route = True

    # ------------------------------------------------- 3. avancer (TOPICS)
    def conduire(self):
        if not self.en_route or self.pose is None:
            return

        nom, x, y = self.cible
        dx, dy = x - self.pose.x, y - self.pose.y
        distance = math.hypot(dx, dy)

        cmd = Twist()
        if distance > TOLERANCE:
            vitesse_max = self.get_parameter('vitesse').value
            # On ralentit en approchant, et on corrige un peu le cap en route
            ecart_cap = math.atan2(dy, dx) - self.pose.theta
            ecart_cap = math.atan2(math.sin(ecart_cap), math.cos(ecart_cap))
            cmd.linear.x = min(vitesse_max, 1.5 * distance)
            cmd.angular.z = 4.0 * ecart_cap
            self.pub_vitesse.publish(cmd)
            return

        # Arrivee : on s'arrete
        self.pub_vitesse.publish(cmd)  # Twist nul = arret
        self.en_route = False
        self.annoncer(f'Arrivee a {nom} !')
        self.appeler_livraison()

    # ------------------------------------------------- 4. livrer (SERVICE)
    def appeler_livraison(self):
        if not self.client_livraison.service_is_ready():
            self.get_logger().warn('Service /livraison indisponible (noeud fabrique lance ?)')
            self.cible = None
            return
        futur = self.client_livraison.call_async(Trigger.Request())
        futur.add_done_callback(self.livraison_terminee)

    def livraison_terminee(self, future):
        reponse = future.result()
        self.annoncer(f'Reponse de la fabrique : {reponse.message}')
        self.cible = None  # pret pour une nouvelle livraison


def main(args=None):
    rclpy.init(args=args)
    node = Navigateur()
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
