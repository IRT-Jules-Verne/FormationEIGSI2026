"""Lance toute l'application : turtlesim + fabrique + navigateur.

Usage (environnement pixi actif, overlay tp_ws charge) :
    ros2 launch tortue_livreuse livraison.launch.py

Puis, dans un autre terminal :
    ros2 topic pub --once /destination std_msgs/msg/String "{data: boulangerie}"
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
        ),
        Node(
            package='tortue_livreuse',
            executable='fabrique',
            name='fabrique',
            output='screen',
            emulate_tty=True,  # affiche les messages des noeuds Python sans delai
        ),
        Node(
            package='tortue_livreuse',
            executable='navigateur',
            name='navigateur',
            output='screen',
            emulate_tty=True,
            # >>> MODIFIABLE : valeur initiale du parametre 'vitesse'
            parameters=[{'vitesse': 2.0}],
        ),
    ])
