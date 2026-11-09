"""Lance toute l'application AVEC RViz : turtlesim + fabrique + navigateur + carte + rviz2.

Usage (environnement pixi actif, overlay tp_ws charge) :
    ros2 launch tortue_livreuse livraison_rviz.launch.py

Dans RViz :
  - clic gauche sur un lieu (disque bleu)      -> la tortue y va
  - glisser le drapeau rouge, puis clic droit > "Livrer ici"
  - outil "Publish Point" (barre du haut), puis clic sur la carte
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    dossier = get_package_share_directory('tortue_livreuse')

    return LaunchDescription([
        # On reutilise le launch de base (turtlesim + fabrique + navigateur)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(dossier, 'launch', 'livraison.launch.py'))
        ),
        Node(
            package='tortue_livreuse',
            executable='carte',
            name='carte',
            output='screen',
            emulate_tty=True,
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', os.path.join(dossier, 'rviz', 'carte.rviz')],
        ),
    ])
