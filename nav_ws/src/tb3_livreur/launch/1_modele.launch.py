"""Partie 1 : le modèle du robot, sans simulateur.

    ros2 launch tb3_livreur 1_modele.launch.py [gui:=true] [rviz:=true]

Lance :
  - robot_state_publisher : lit l'URDF (produit par xacro) et publie les transformations
    fixes sur /tf_static et les transformations des articulations mobiles sur /tf, à
    partir de /joint_states ;
  - joint_state_publisher_gui : des curseurs pour faire tourner les roues (publie
    /joint_states) ;
  - rviz2 avec la configuration modele.rviz.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    dossier = get_package_share_directory('tb3_livreur')
    urdf = LaunchConfiguration('urdf')
    scan_yaw = LaunchConfiguration('scan_yaw')

    # xacro transforme le fichier .urdf.xacro en URDF ; le résultat devient le paramètre
    # robot_description de robot_state_publisher.
    robot_description = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', urdf, ' scan_yaw:=', scan_yaw]),
        value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument('urdf', default_value=os.path.join(dossier, 'urdf', 'burger.urdf.xacro')),
        DeclareLaunchArgument('scan_yaw', default_value='0.0',
                              description='rotation du lidar autour de z (rad)'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),

        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen',
             parameters=[{'robot_description': robot_description}]),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
             name='joint_state_publisher_gui',
             condition=IfCondition(LaunchConfiguration('gui'))),
        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', os.path.join(dossier, 'rviz', 'modele.rviz')],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
