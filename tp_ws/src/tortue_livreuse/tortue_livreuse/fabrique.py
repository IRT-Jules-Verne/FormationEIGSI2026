"""Noeud 'fabrique' : depose un colis (= une nouvelle tortue) a chaque livraison.

  - Il FOURNIT le service /livraison   (type std_srvs/srv/Trigger)  -> SERVICE, serveur
  - Il APPELLE le service /spawn       (type turtlesim/srv/Spawn)   -> SERVICE, client
  - Il ECOUTE le topic /turtle1/pose   (type turtlesim/msg/Pose)    -> TOPIC, abonnement
    pour savoir ou deposer le colis.

Test a la main, sans le navigateur :
  ros2 service call /livraison std_srvs/srv/Trigger
"""

import rclpy
from rclpy.node import Node

from std_srvs.srv import Trigger
from turtlesim.msg import Pose
from turtlesim.srv import Spawn

# >>> MODIFIABLE : prefixe du nom des tortues creees (colis_1, colis_2, ...)
PREFIXE = 'colis'

# >>> MODIFIABLE : decalage (x, y) du colis par rapport a la tortue livreuse
DECALAGE = (0.0, -0.6)


class Fabrique(Node):

    def __init__(self):
        super().__init__('fabrique')

        self.create_service(Trigger, 'livraison', self.livrer)       # serveur
        self.client_spawn = self.create_client(Spawn, 'spawn')       # client
        self.create_subscription(Pose, 'turtle1/pose', self.recevoir_pose, 10)

        self.pose = None
        self.compteur = 0
        self.get_logger().info('Fabrique prete, en attente de /livraison')

    def recevoir_pose(self, msg):
        self.pose = msg

    def livrer(self, requete, reponse):
        """Appele a chaque requete sur /livraison. Doit remplir et renvoyer 'reponse'."""
        if self.pose is None or not self.client_spawn.service_is_ready():
            reponse.success = False
            reponse.message = 'Impossible : turtlesim n\'est pas pret'
            return reponse

        self.compteur += 1
        demande = Spawn.Request()
        demande.x = self.pose.x + DECALAGE[0]
        demande.y = self.pose.y + DECALAGE[1]
        demande.theta = self.pose.theta
        demande.name = f'{PREFIXE}_{self.compteur}'

        # Appel asynchrone : on n'attend pas la reponse de turtlesim ici
        # (attendre dans un callback bloquerait le noeud).
        self.client_spawn.call_async(demande)

        reponse.success = True
        reponse.message = f'{demande.name} depose en ({demande.x:.1f}, {demande.y:.1f})'
        self.get_logger().info(reponse.message)
        return reponse


def main(args=None):
    rclpy.init(args=args)
    node = Fabrique()
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
