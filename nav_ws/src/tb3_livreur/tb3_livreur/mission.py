"""Partie 7 : une mission de livraison, lieu par lieu, avec Nav2.

    ros2 run tb3_livreur mission                      # tournée par défaut
    ros2 run tb3_livreur mission poste_A rejet        # tournée choisie
    ros2 run tb3_livreur mission --ecouter            # attend des noms sur /destination

Prérequis : 5_navigation.launch.py lancé et pose initiale donnée dans RViz.

Le nœud utilise nav2_simple_commander.BasicNavigator, un client Python de l'action
/navigate_to_pose. C'est l'équivalent, pour Nav2, du « navigateur » de la tortue livreuse :
on donne un lieu, on suit l'avancement, on obtient un résultat.
"""

import math
import sys

from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from std_msgs.msg import String

# Coordonnées des lieux dans le repère map (x en m, y en m, yaw en rad).
# Relevées dans RViz avec l'outil « Publish Point » (topic /clicked_point).
LIEUX = {
    'depart':  (0.0, 0.0, 0.0),
    'cellule': (5.0, 1.2, 1.5708),
    'poste_A': (0.2, 6.0, 3.1416),
    'poste_B': (10.2, 5.3, -1.5708),
    'rejet':   (9.8, 0.8, -1.5708),
}

TOURNEE_PAR_DEFAUT = ['cellule', 'poste_A', 'cellule', 'poste_B', 'depart']


def pose_depuis_lieu(navigateur, nom):
    x, y, yaw = LIEUX[nom]
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigateur.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def aller_a(navigateur, nom):
    """Envoie le but, affiche l'avancement, renvoie True si le lieu est atteint."""
    if nom not in LIEUX:
        navigateur.get_logger().warn(f'Lieu inconnu : {nom} (lieux : {", ".join(LIEUX)})')
        return False
    navigateur.get_logger().info(f'--> En route vers {nom}')
    navigateur.goToPose(pose_depuis_lieu(navigateur, nom))

    while not navigateur.isTaskComplete():
        retour = navigateur.getFeedback()
        if retour is not None:
            navigateur.get_logger().info(
                f'    reste {retour.distance_remaining:.2f} m, '
                f'{retour.number_of_recoveries} reprise(s)',
                throttle_duration_sec=2.0)

    resultat = navigateur.getResult()
    if resultat == TaskResult.SUCCEEDED:
        navigateur.get_logger().info(f'    {nom} atteint')
        return True
    if resultat == TaskResult.CANCELED:
        navigateur.get_logger().warn(f'    mission vers {nom} annulee')
    else:
        navigateur.get_logger().error(f'    echec vers {nom}')
    return False


def main(args=None):
    rclpy.init(args=args)
    argv = [a for a in sys.argv[1:] if not a.startswith('--ros-args')]
    ecouter = '--ecouter' in argv
    tournee = [a for a in argv if not a.startswith('--')] or TOURNEE_PAR_DEFAUT

    navigateur = BasicNavigator()
    navigateur.get_logger().info("Attente de Nav2 (amcl et bt_navigator actifs, pose initiale recue)...")
    navigateur.waitUntilNav2Active(localizer='amcl')

    if ecouter:
        # Bonus : la même interface que la tortue livreuse, un nom de lieu sur /destination
        navigateur.get_logger().info("En ecoute sur /destination (std_msgs/String)")
        file_attente = []
        navigateur.create_subscription(String, 'destination',
                                       lambda msg: file_attente.append(msg.data), 10)
        try:
            while rclpy.ok():
                rclpy.spin_once(navigateur, timeout_sec=0.2)
                if file_attente:
                    aller_a(navigateur, file_attente.pop(0))
        except KeyboardInterrupt:
            pass
    else:
        try:
            for lieu in tournee:
                if not aller_a(navigateur, lieu):
                    break
            navigateur.get_logger().info('Tournee terminee')
        except KeyboardInterrupt:
            navigateur.cancelTask()

    navigateur.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
