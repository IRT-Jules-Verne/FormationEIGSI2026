"""D11 : regroupe dans un fichier les reglages montres en D6 (parametre) et D7 (namespace).

Lance turtlesim dans le namespace /robot2 avec un fond rouge (background_r = 200),
et une teleoperation dans le meme namespace (toutes ses interfaces suivent).

Usage (cmd active par Pixi, overlay charge) :
    ros2 launch cours_ros2_demo turtlesim_demo.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
            namespace='robot2',
            parameters=[{'background_r': 200}],
        ),
        # La teleoperation lit le clavier : elle doit avoir son propre terminal.
        # Sous Windows on la lance a part :
        #   ros2 run turtlesim turtle_teleop_key --ros-args -r __ns:=/robot2
    ])
