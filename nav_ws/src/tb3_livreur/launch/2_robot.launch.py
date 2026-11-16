"""Partie 2 : le robot complet = modèle + simulateur (ou robot réel).

    ros2 launch tb3_livreur 2_robot.launch.py [sim:=true] [rviz:=true] [x:=0.0 y:=0.0 yaw:=0.0]
                                              [derive:=true] [scan_yaw:=0.0]

  sim:=true   (défaut) lance le simulateur loopback dans l'atelier MecaTri. Il publie
              /odom, /scan, /joint_states et la transformation odom -> base_footprint.
  sim:=false  ne lance que le modèle : on suppose qu'un vrai TurtleBot3 (turtlebot3_bringup)
              est joignable sur le réseau et publie les mêmes interfaces.

Dans les deux cas, robot_state_publisher publie les transformations du modèle, et c'est
grâce à base_footprint -> base_scan que le simulateur sait où placer le lidar.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Arguments transmis tels quels au simulateur
ARGS_SIM = ['x', 'y', 'yaw', 'derive', 'publier_monde', 'publier_map_odom_tf',
            'obstacle_sur_clic', 'scan_topic', 'robot']


def generate_launch_description():
    dossier = get_package_share_directory('tb3_livreur')
    dossier_sim = get_package_share_directory('tb3_loopback_sim')

    return LaunchDescription([
        DeclareLaunchArgument('sim', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('urdf', default_value=os.path.join(dossier, 'urdf', 'burger.urdf.xacro')),
        DeclareLaunchArgument('robot', default_value='burger'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('derive', default_value='true',
                              description="false : odometrie parfaite"),
        DeclareLaunchArgument('scan_yaw', default_value='0.0'),
        DeclareLaunchArgument('scan_topic', default_value='scan',
                              description='topic sur lequel le simulateur publie le lidar'),
        DeclareLaunchArgument('publier_monde', default_value='false'),
        DeclareLaunchArgument('publier_map_odom_tf', default_value='false'),
        DeclareLaunchArgument('obstacle_sur_clic', default_value='false'),

        # Le modèle (robot_state_publisher), sans curseurs ni RViz : /joint_states vient
        # du simulateur ou du vrai robot.
        # GroupAction(scoped=True) : les arguments passés à l'inclusion (rviz='false'...)
        # restent dans l'inclusion ; sinon ils écrasent ceux de ce launch (launch ne cloisonne
        # pas les configurations) et le RViz ci-dessous ne démarre jamais.
        GroupAction(scoped=True, actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(dossier, 'launch', '1_modele.launch.py')),
            launch_arguments={'gui': 'false', 'rviz': 'false',
                              'urdf': LaunchConfiguration('urdf'),
                              'scan_yaw': LaunchConfiguration('scan_yaw')}.items())]),

        # Le simulateur, à la place du robot réel
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(dossier_sim, 'launch', 'simulateur.launch.py')),
            condition=IfCondition(LaunchConfiguration('sim')),
            launch_arguments={a: LaunchConfiguration(a) for a in ARGS_SIM}.items()),

        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', os.path.join(dossier, 'rviz', 'robot.rviz')],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
