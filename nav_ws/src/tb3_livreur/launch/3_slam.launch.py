"""Partie 3 : cartographier en téléopérant.

    ros2 launch tb3_livreur 3_slam.launch.py [sim:=true] [derive:=true]

Lance le robot (2_robot.launch.py), slam_toolbox en mode cartographie (config/slam.yaml)
et RViz (slam.rviz). La téléopération au clavier se lance dans un AUTRE terminal :

    ros2 run teleop_twist_keyboard teleop_twist_keyboard

slam_toolbox lit /scan et TF (odom -> base_footprint -> base_scan), publie /map et la
transformation map -> odom.

Sauvegarde de la carte, une fois la salle couverte :

    ros2 run nav2_map_server map_saver_cli -f maps/atelier --ros-args -p save_map_timeout:=15.0
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

ARGS_ROBOT = ['sim', 'urdf', 'robot', 'x', 'y', 'yaw', 'derive', 'publier_monde']


def generate_launch_description():
    dossier = get_package_share_directory('tb3_livreur')

    return LaunchDescription([
        DeclareLaunchArgument('sim', default_value='true'),
        DeclareLaunchArgument('urdf', default_value=os.path.join(dossier, 'urdf', 'burger.urdf.xacro')),
        DeclareLaunchArgument('robot', default_value='burger'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('derive', default_value='true'),
        DeclareLaunchArgument('publier_monde', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('params_slam', default_value=os.path.join(dossier, 'config', 'slam.yaml')),

        # scoped=True : rviz='false' ne doit pas écraser l'argument rviz de ce launch
        GroupAction(scoped=True, actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(dossier, 'launch', '2_robot.launch.py')),
            launch_arguments=dict({a: LaunchConfiguration(a) for a in ARGS_ROBOT},
                                  rviz='false').items())]),

        Node(package='slam_toolbox', executable='async_slam_toolbox_node',
             name='slam_toolbox', output='screen',
             parameters=[LaunchConfiguration('params_slam')]),

        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', os.path.join(dossier, 'rviz', 'slam.rviz')],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
