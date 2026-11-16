"""Pilote automatique de test : conduit le robot simulé de point en point.

    ros2 run tb3_loopback_sim pilote                 # tour de l'atelier (cartographie)
    ros2 run tb3_loopback_sim pilote 3.0,1.5 6.0,2.0 # liste de points x,y (repère map)
    ros2 run tb3_loopback_sim pilote --carre 2.0     # un carré de 2 m de côté puis retour

Il TRICHE : il lit la pose vraie publiée par le simulateur (/simulateur/pose_vraie) et
publie /cmd_vel. Il sert à cartographier sans clavier (démos, carte de secours, tests),
pas à naviguer : il n'évite pas les obstacles. Les points doivent être reliés en ligne
droite par de l'espace libre.
"""

import math
import sys

from geometry_msgs.msg import PoseStamped, Twist
import rclpy
from rclpy.node import Node

# Tour de cartographie de l'atelier MecaTri (couloirs libres, boucle fermée)
TOUR_ATELIER = [
    (0.0, 0.0), (0.0, 0.8), (2.6, 0.8), (5.0, 1.0), (8.0, 1.0), (9.8, 0.8), (10.0, 1.4),
    (8.8, 1.4), (8.0, 3.0), (8.0, 4.0), (8.6, 3.6), (8.6, 6.5), (10.2, 6.3), (10.2, 5.3),
    (10.2, 6.3), (8.6, 6.5), (8.6, 3.6), (7.8, 1.4), (5.0, 1.2), (2.6, 0.8), (1.1, 1.0),
    (1.1, 2.6), (1.4, 4.5), (2.0, 5.0), (2.0, 6.2), (2.0, 5.0), (4.0, 4.8), (6.0, 4.8),
    (6.3, 4.0), (6.0, 4.8), (5.0, 5.0), (5.0, 6.2), (5.0, 5.0), (2.0, 5.0), (0.2, 5.5),
    (0.0, 4.5), (0.4, 2.0), (0.0, 0.0),
]


class Pilote(Node):

    def __init__(self, points, v_max=0.2, w_max=1.5):
        super().__init__('pilote')
        self.points = list(points)
        self.v_max, self.w_max = v_max, w_max
        self.pose = None
        self.create_subscription(PoseStamped, '/simulateur/pose_vraie', self.sur_pose, 10)
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_timer(0.05, self.boucle)
        self.get_logger().info(f'{len(self.points)} points a rejoindre')

    def sur_pose(self, msg):
        q = msg.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.pose = (msg.pose.position.x, msg.pose.position.y, yaw)

    def boucle(self):
        if self.pose is None:
            return
        if not self.points:
            self.pub.publish(Twist())
            self.get_logger().info('Arrive au dernier point')
            raise SystemExit
        x, y, yaw = self.pose
        bx, by = self.points[0]
        dx, dy = bx - x, by - y
        distance = math.hypot(dx, dy)
        if distance < 0.1:
            self.points.pop(0)
            return
        erreur_cap = math.atan2(math.sin(math.atan2(dy, dx) - yaw),
                                math.cos(math.atan2(dy, dx) - yaw))
        cmd = Twist()
        cmd.angular.z = max(-self.w_max, min(self.w_max, 2.0 * erreur_cap))
        # On avance seulement quand on regarde à peu près vers le point (rotation d'abord)
        if abs(erreur_cap) < 0.3:
            cmd.linear.x = min(self.v_max, 0.8 * distance + 0.05)
        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    argv = [a for a in sys.argv[1:] if not a.startswith('--ros-args')]
    if argv and argv[0] == '--carre':
        c = float(argv[1]) if len(argv) > 1 else 2.0
        points = None  # construit après réception de la pose
        node = Pilote([])
        while node.pose is None:
            rclpy.spin_once(node, timeout_sec=0.1)
        x, y, yaw = node.pose
        coins = [(x + c, y), (x + c, y + c), (x, y + c), (x, y)]
        node.points = coins
        node.get_logger().info(f'Carre de {c} m depuis ({x:.2f}, {y:.2f})')
    elif argv:
        points = [tuple(float(v) for v in a.split(',')) for a in argv]
        node = Pilote(points)
    else:
        node = Pilote(TOUR_ATELIER)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
