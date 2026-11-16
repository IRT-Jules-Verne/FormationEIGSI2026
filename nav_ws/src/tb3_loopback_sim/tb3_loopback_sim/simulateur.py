"""Simulateur « loopback » 2D du TurtleBot3 pour le TP navigation.

Idée (reprise de nav2_loopback_sim, Nav2 Jazzy, Apache-2.0) : pas de physique, pas de 3D.
Le simulateur reçoit /cmd_vel, intègre les vitesses pour obtenir la pose du robot, et
produit exactement ce que publie le vrai robot (turtlebot3_bringup) :

    /cmd_vel  ->  [ simulateur ]  ->  /odom, /scan, /joint_states, TF odom -> base_footprint

Différences pédagogiques avec l'original :
  - le monde est un fichier PGM + YAML chargé par le simulateur (la « vraie salle ») ;
  - l'odométrie DÉRIVE (facteurs d'échelle + bruit), comme sur un vrai robot ;
  - le robot ne traverse pas les murs ;
  - des obstacles amovibles (palettes) s'ajoutent et se retirent par service ;
  - la transformation map -> odom n'est PAS publiée par défaut : c'est le rôle du SLAM
    ou d'AMCL. Le simulateur garde la vérité terrain pour calculer le scan.

Le scan est calculé par lancer de rayons dans le monde, depuis la position du lidar obtenue
avec TF (base_footprint -> base_scan) : si le modèle du robot ne déclare pas base_scan,
il n'y a pas de scan. Son orientation, elle, est celle du capteur réel (scan_yaw_reel) et
non celle de l'URDF : un lidar déclaré à l'envers dans le modèle se voit dans RViz.
"""

import math
import os
import random

from geometry_msgs.msg import PointStamped, PoseStamped, PoseWithCovarianceStamped
from geometry_msgs.msg import Quaternion, TransformStamped, Twist
from nav_msgs.msg import OccupancyGrid, Odometry
import numpy as np
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState, LaserScan
from tf2_ros import Buffer, TransformBroadcaster, TransformListener
from turtlesim.srv import Kill, Spawn

from .monde import Monde


def quaternion_depuis_yaw(yaw):
    q = Quaternion()
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


def yaw_depuis_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class Pose2D:
    """Une pose plane (x, y, yaw), avec l'intégration d'une commande (v, w) pendant dt."""

    def __init__(self, x=0.0, y=0.0, yaw=0.0):
        self.x, self.y, self.yaw = x, y, yaw

    def apres(self, v, w, dt):
        """Pose obtenue après avoir suivi (v, w) pendant dt (arc de cercle exact)."""
        if abs(w) < 1e-6:
            return Pose2D(self.x + v * dt * math.cos(self.yaw),
                          self.y + v * dt * math.sin(self.yaw), self.yaw)
        r = v / w
        yaw2 = self.yaw + w * dt
        return Pose2D(self.x + r * (math.sin(yaw2) - math.sin(self.yaw)),
                      self.y - r * (math.cos(yaw2) - math.cos(self.yaw)), yaw2)

    def compose(self, autre):
        """self ⊕ autre : la pose 'autre', exprimée dans le repère de self."""
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return Pose2D(self.x + c * autre.x - s * autre.y,
                      self.y + s * autre.x + c * autre.y, self.yaw + autre.yaw)

    def inverse(self):
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return Pose2D(-(c * self.x + s * self.y), -(-s * self.x + c * self.y), -self.yaw)

    def vers_transform(self, parent, enfant, stamp):
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = parent
        t.child_frame_id = enfant
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation = quaternion_depuis_yaw(self.yaw)
        return t


class Simulateur(Node):

    def __init__(self):
        super().__init__('simulateur')

        # ----- paramètres -----
        p = self.declare_parameters('', [
            ('monde', ''),                       # fichier YAML du monde (vide = atelier MecaTri)
            ('pose_x', 0.0),                    # pose de départ dans le monde (repère map)
            ('pose_y', 0.0),
            ('pose_yaw', 0.0),
            ('demarrer_immediatement', True),   # faux : attendre un message sur initialpose
            ('ecouter_initialpose', True),      # le clic « 2D Pose Estimate » téléporte le robot
            ('periode', 0.02),                  # période d'intégration (s)
            ('base_frame_id', 'base_footprint'),
            ('odom_frame_id', 'odom'),
            ('map_frame_id', 'map'),
            ('scan_frame_id', 'base_scan'),
            ('publier_map_odom_tf', False),     # vrai seulement pour les démos sans localisation
            ('publier_monde', False),           # publie la vraie carte sur ~/monde (démos)
            ('vitesse_max_lin', 0.22),          # limites du Burger (m/s, rad/s)
            ('vitesse_max_ang', 2.84),
            ('rayon_collision', 0.10),          # disque utilisé pour détecter les murs
            ('collisions', True),
            # Odométrie : erreur d'échelle (sans unité) et bruit (écart-type par seconde)
            ('odom_derive_lin', 0.02),
            ('odom_derive_ang', 0.05),
            ('odom_bruit_lin', 0.005),
            ('odom_bruit_ang', 0.01),
            ('graine', 42),
            # Lidar LDS-01 : 360 rayons, 0,12 - 3,5 m, 5 Hz ; bruit gaussien sur les distances
            ('scan_periode', 0.2),
            ('scan_nombre', 360),
            ('scan_portee_min', 0.12),
            ('scan_portee_max', 3.5),
            ('scan_bruit', 0.005),
            # Orientation PHYSIQUE du lidar sur le robot (rad). Elle ne vient pas de TF : si
            # l'URDF déclare le lidar tourné (scan_yaw), le capteur réel, lui, ne tourne pas.
            ('scan_yaw_reel', 0.0),
            # Roues (pour /joint_states) : rayon et entraxe du Burger
            ('roue_rayon', 0.033),
            ('roue_entraxe', 0.160),
            ('joint_gauche', 'wheel_left_joint'),
            ('joint_droit', 'wheel_right_joint'),
            ('publier_joint_states', True),
            # Obstacles amovibles
            ('taille_obstacle', 0.4),
            ('obstacle_sur_clic', False),       # Publish Point dans RViz pose une palette
        ])
        prm = {x.name: x.value for x in p}

        self.base_frame = prm['base_frame_id']
        self.odom_frame = prm['odom_frame_id']
        self.map_frame = prm['map_frame_id']
        self.scan_frame = prm['scan_frame_id']
        self.periode = float(prm['periode'])
        self.publier_map_odom_tf = bool(prm['publier_map_odom_tf'])
        self.v_max = float(prm['vitesse_max_lin'])
        self.w_max = float(prm['vitesse_max_ang'])
        self.rayon_collision = float(prm['rayon_collision'])
        self.collisions = bool(prm['collisions'])
        self.derive_lin = float(prm['odom_derive_lin'])
        self.derive_ang = float(prm['odom_derive_ang'])
        self.bruit_lin = float(prm['odom_bruit_lin'])
        self.bruit_ang = float(prm['odom_bruit_ang'])
        self.scan_nombre = int(prm['scan_nombre'])
        self.scan_portee_min = float(prm['scan_portee_min'])
        self.scan_portee_max = float(prm['scan_portee_max'])
        self.scan_bruit = float(prm['scan_bruit'])
        self.scan_yaw_reel = float(prm['scan_yaw_reel'])
        self.roue_rayon = float(prm['roue_rayon'])
        self.roue_entraxe = float(prm['roue_entraxe'])
        self.joint_gauche = prm['joint_gauche']
        self.joint_droit = prm['joint_droit']
        self.publier_joint_states = bool(prm['publier_joint_states'])
        self.taille_obstacle = float(prm['taille_obstacle'])
        self.alea = random.Random(int(prm['graine']))

        # ----- monde -----
        fichier = prm['monde']
        if not fichier:
            from ament_index_python.packages import get_package_share_directory
            fichier = os.path.join(get_package_share_directory('tb3_loopback_sim'),
                                   'mondes', 'atelier_mecatri.yaml')
        self.monde = Monde(fichier)
        self.get_logger().info(
            f'Monde charge : {fichier} ({self.monde.largeur} x {self.monde.hauteur} cellules, '
            f'{self.monde.resolution} m/cellule)')

        # ----- état -----
        self.pose_vraie = None      # Pose2D dans map (vérité terrain)
        self.pose_odom = Pose2D()   # Pose2D dans odom (ce que le robot croit)
        self.cmd = None
        self.cmd_date = self.get_clock().now()
        self.v_odom = 0.0
        self.w_odom = 0.0
        self.angle_roue_g = 0.0
        self.angle_roue_d = 0.0
        self.pose_base_vers_scan = None
        self.compteur_obstacles = 0
        self.derniere_collision = None

        # ----- interfaces ROS -----
        self.tf_broadcaster = TransformBroadcaster(self)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.create_subscription(Twist, 'cmd_vel', self.sur_cmd_vel, 10)
        if bool(prm['ecouter_initialpose']):
            self.create_subscription(PoseWithCovarianceStamped, 'initialpose',
                                     self.sur_teleportation, 10)
        self.create_subscription(PoseWithCovarianceStamped, '~/teleporter',
                                 self.sur_teleportation, 10)
        if bool(prm['obstacle_sur_clic']):
            self.create_subscription(PointStamped, 'clicked_point', self.sur_clic, 10)

        self.pub_odom = self.create_publisher(Odometry, 'odom', 10)
        qos_capteur = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                                 durability=DurabilityPolicy.VOLATILE, depth=5)
        self.pub_scan = self.create_publisher(LaserScan, 'scan', qos_capteur)
        self.pub_joints = self.create_publisher(JointState, 'joint_states', 10)
        self.pub_pose_vraie = self.create_publisher(PoseStamped, '~/pose_vraie', 10)
        if bool(prm['publier_monde']):
            qos_carte = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                                   durability=DurabilityPolicy.TRANSIENT_LOCAL, depth=1)
            self.pub_monde = self.create_publisher(OccupancyGrid, '~/monde', qos_carte)
            self.publier_le_monde()
        else:
            self.pub_monde = None

        self.create_service(Spawn, '~/ajouter_obstacle', self.srv_ajouter_obstacle)
        self.create_service(Kill, '~/retirer_obstacle', self.srv_retirer_obstacle)

        self.create_timer(self.periode, self.pas_de_temps)
        self.create_timer(float(prm['scan_periode']), self.publier_scan)

        if bool(prm['demarrer_immediatement']):
            self.teleporter(float(prm['pose_x']), float(prm['pose_y']), float(prm['pose_yaw']))
        else:
            self.get_logger().info(
                "En attente d'une pose initiale (outil « 2D Pose Estimate » de RViz)")
        self.get_logger().info('Simulateur pret')

    # ------------------------------------------------------------------ callbacks

    def sur_cmd_vel(self, msg):
        self.cmd = msg
        self.cmd_date = self.get_clock().now()

    def sur_teleportation(self, msg):
        yaw = yaw_depuis_quaternion(msg.pose.pose.orientation)
        self.teleporter(msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)

    def sur_clic(self, msg):
        self.ajouter_obstacle(msg.point.x, msg.point.y, 0.0, '')

    def srv_ajouter_obstacle(self, req, rep):
        rep.name = self.ajouter_obstacle(req.x, req.y, req.theta, req.name)
        return rep

    def srv_retirer_obstacle(self, req, rep):
        if req.name == 'tous':
            for nom in list(self.monde.obstacles):
                self.monde.retirer_obstacle(nom)
            self.get_logger().info('Tous les obstacles retires')
        elif self.monde.retirer_obstacle(req.name):
            self.get_logger().info(f'Obstacle « {req.name} » retire')
        else:
            self.get_logger().warn(f'Aucun obstacle nomme « {req.name} »')
        self.publier_le_monde()
        return rep

    # ------------------------------------------------------------------ actions

    def teleporter(self, x, y, yaw):
        """Place le robot (vérité terrain) sans toucher à l'odométrie."""
        self.pose_vraie = Pose2D(x, y, yaw)
        self.get_logger().info(f'Robot place en x={x:.2f} y={y:.2f} yaw={yaw:.2f} (repere map)')

    def ajouter_obstacle(self, x, y, yaw, nom):
        if not nom:
            self.compteur_obstacles += 1
            nom = f'palette{self.compteur_obstacles}'
        self.monde.ajouter_obstacle(nom, x, y, yaw, self.taille_obstacle)
        self.get_logger().info(f'Obstacle « {nom} » ajoute en x={x:.2f} y={y:.2f}')
        self.publier_le_monde()
        return nom

    def publier_le_monde(self):
        if self.pub_monde is None:
            return
        msg = OccupancyGrid()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.map_frame
        msg.info.resolution = self.monde.resolution
        msg.info.width = self.monde.largeur
        msg.info.height = self.monde.hauteur
        msg.info.origin.position.x = self.monde.origine_x
        msg.info.origin.position.y = self.monde.origine_y
        msg.info.origin.orientation.w = 1.0
        msg.data = self.monde.grille.flatten().astype(np.int8).tolist()
        self.pub_monde.publish(msg)

    # ------------------------------------------------------------------ boucle

    def pas_de_temps(self):
        if self.pose_vraie is None:
            return
        maintenant = self.get_clock().now()
        dt = self.periode

        # 1. Commande courante (périmée après 0,5 s : le robot s'arrête si plus personne ne publie)
        v = w = 0.0
        if self.cmd is not None and maintenant - self.cmd_date < Duration(seconds=0.5):
            v = max(-self.v_max, min(self.v_max, self.cmd.linear.x))
            w = max(-self.w_max, min(self.w_max, self.cmd.angular.z))

        # 2. Vérité terrain : mouvement exact, bloqué par les murs
        if v != 0.0 or w != 0.0:
            candidate = self.pose_vraie.apres(v, w, dt)
            if self.collisions and not self.monde.disque_libre(
                    candidate.x, candidate.y, self.rayon_collision):
                # On laisse tourner sur place, mais pas avancer dans le mur.
                candidate = self.pose_vraie.apres(0.0, w, dt)
                v = 0.0
                if (self.derniere_collision is None or
                        maintenant - self.derniere_collision > Duration(seconds=2.0)):
                    self.get_logger().warn('Collision : le robot touche un obstacle')
                    self.derniere_collision = maintenant
            self.pose_vraie = candidate

        # 3. Odométrie : ce que mesurent les encodeurs, avec dérive et bruit
        self.v_odom = v * (1.0 + self.derive_lin) + (
            self.alea.gauss(0.0, self.bruit_lin) if v != 0.0 else 0.0)
        self.w_odom = w * (1.0 + self.derive_ang) + (
            self.alea.gauss(0.0, self.bruit_ang) if (v != 0.0 or w != 0.0) else 0.0)
        self.pose_odom = self.pose_odom.apres(self.v_odom, self.w_odom, dt)

        # 4. Roues (cinématique différentielle, slide « deux vitesses de roues »)
        v_g = self.v_odom - self.w_odom * self.roue_entraxe / 2.0
        v_d = self.v_odom + self.w_odom * self.roue_entraxe / 2.0
        self.angle_roue_g += v_g / self.roue_rayon * dt
        self.angle_roue_d += v_d / self.roue_rayon * dt

        # 5. Publications
        stamp = maintenant.to_msg()
        self.tf_broadcaster.sendTransform(
            self.pose_odom.vers_transform(self.odom_frame, self.base_frame, stamp))
        if self.publier_map_odom_tf:
            map_vers_odom = self.pose_vraie.compose(self.pose_odom.inverse())
            self.tf_broadcaster.sendTransform(
                map_vers_odom.vers_transform(self.map_frame, self.odom_frame, stamp))

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.pose_odom.x
        odom.pose.pose.position.y = self.pose_odom.y
        odom.pose.pose.orientation = quaternion_depuis_yaw(self.pose_odom.yaw)
        odom.twist.twist.linear.x = self.v_odom
        odom.twist.twist.angular.z = self.w_odom
        for i in (0, 7, 35):
            odom.pose.covariance[i] = 0.01
            odom.twist.covariance[i] = 0.01
        self.pub_odom.publish(odom)

        if self.publier_joint_states:
            js = JointState()
            js.header.stamp = stamp
            js.name = [self.joint_gauche, self.joint_droit]
            js.position = [self.angle_roue_g, self.angle_roue_d]
            js.velocity = [v_g / self.roue_rayon, v_d / self.roue_rayon]
            self.pub_joints.publish(js)

        vraie = PoseStamped()
        vraie.header.stamp = stamp
        vraie.header.frame_id = self.map_frame
        vraie.pose.position.x = self.pose_vraie.x
        vraie.pose.position.y = self.pose_vraie.y
        vraie.pose.orientation = quaternion_depuis_yaw(self.pose_vraie.yaw)
        self.pub_pose_vraie.publish(vraie)

    # ------------------------------------------------------------------ lidar

    def chercher_pose_du_lidar(self):
        """Position du lidar : base_footprint -> base_scan dans TF (robot_state_publisher).

        Seule la translation vient de TF. L'orientation est celle du capteur réel
        (paramètre scan_yaw_reel) : si on la prenait dans TF, un lidar déclaré à l'envers
        dans l'URDF tournerait aussi dans la simulation, et l'erreur ne se verrait pas.
        """
        try:
            t = self.tf_buffer.lookup_transform(self.base_frame, self.scan_frame,
                                                rclpy.time.Time())
        except Exception as e:  # noqa: BLE001 - toute erreur TF se traite pareil
            self.get_logger().warn(
                f'Pas de scan : transformation {self.base_frame} -> {self.scan_frame} '
                f'introuvable ({type(e).__name__}). Le modele du robot est-il lance ?',
                throttle_duration_sec=5.0)
            return None
        tr = t.transform.translation
        self.pose_base_vers_scan = Pose2D(tr.x, tr.y, self.scan_yaw_reel)
        return self.pose_base_vers_scan

    def publier_scan(self):
        if self.pose_vraie is None:
            return
        base_vers_scan = self.chercher_pose_du_lidar()
        if base_vers_scan is None:
            return
        lidar = self.pose_vraie.compose(base_vers_scan)

        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.scan_frame
        msg.angle_min = 0.0
        msg.angle_increment = 2.0 * math.pi / self.scan_nombre
        msg.angle_max = msg.angle_increment * (self.scan_nombre - 1)
        msg.time_increment = 0.0
        msg.scan_time = 0.2
        msg.range_min = self.scan_portee_min
        msg.range_max = self.scan_portee_max

        angles = msg.angle_min + msg.angle_increment * np.arange(self.scan_nombre)
        distances = self.monde.lancer_rayons(lidar.x, lidar.y, lidar.yaw, angles,
                                             self.scan_portee_min, self.scan_portee_max)
        if self.scan_bruit > 0.0:
            fini = np.isfinite(distances)
            distances[fini] += np.random.default_rng(
                self.alea.getrandbits(32)).normal(0.0, self.scan_bruit, fini.sum()).astype(
                    np.float32)
        msg.ranges = distances.tolist()
        self.pub_scan.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = Simulateur()
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
