"""Noeud minimal pour la demonstration D8 : du code au noeud.

Publie un message texte sur /bonjour toutes les secondes et l'affiche dans le terminal.
Pour la demo : modifier MESSAGE, reconstruire, recharger l'overlay, relancer.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

MESSAGE = 'Bonjour depuis cours_ros2_demo (version 1)'


class Bonjour(Node):

    def __init__(self):
        super().__init__('bonjour')
        self.publisher = self.create_publisher(String, 'bonjour', 10)
        self.compteur = 0
        self.create_timer(1.0, self.tick)

    def tick(self):
        msg = String()
        msg.data = f'{MESSAGE} #{self.compteur}'
        self.publisher.publish(msg)
        self.get_logger().info(msg.data)
        self.compteur += 1


def main(args=None):
    rclpy.init(args=args)
    node = Bonjour()
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
