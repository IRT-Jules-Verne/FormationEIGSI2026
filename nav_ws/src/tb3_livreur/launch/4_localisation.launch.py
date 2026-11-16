"""Partie 4 : se localiser dans une carte connue.

    ros2 launch tb3_livreur 4_localisation.launch.py [carte:=.../maps/atelier.yaml]

Lance le robot (2_robot.launch.py), puis :
  - map_server : charge la carte (image + YAML) et la publie sur /map ;
  - amcl : filtre à particules ; lit /scan, /map, TF et /initialpose, publie /amcl_pose,
    /particle_cloud et la transformation map -> odom ;
  - lifecycle_manager_localisation : fait passer map_server puis amcl par les états
    configure -> activate (les nœuds Nav2 sont des nœuds à cycle de vie).

Donnez ensuite la pose initiale dans RViz (outil « 2D Pose Estimate »).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
                            OpaqueFunction, TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

ARGS_ROBOT = ['sim', 'urdf', 'robot', 'x', 'y', 'yaw', 'derive', 'publier_monde',
              'scan_yaw', 'scan_topic', 'obstacle_sur_clic']

# Nœuds à cycle de vie pilotés par le lifecycle manager, dans l'ordre de démarrage :
# d'abord la carte, puis la localisation qui en a besoin.
NOEUDS_LOCALISATION = ['map_server', 'amcl']


def gestion_du_cycle_de_vie(context):
    """Lifecycle manager (retardé) et veilleur, avec la liste des nœuds calculée maintenant.

    L'argument amcl_gere:=false retire amcl de la liste (exercice de diagnostic, panne 2).
    La liste est calculée ici, au moment où le launch est lu, parce que le lifecycle manager
    démarre avec un délai : lancé en même temps que map_server et amcl, il peut envoyer
    « configure » avant que DDS ait fini de découvrir les nœuds ; l'appel est alors perdu et
    il abandonne (« Failed to change state for node »).
    """
    amcl_gere = LaunchConfiguration('amcl_gere').perform(context)
    noeuds_geres = [n for n in NOEUDS_LOCALISATION if n != 'amcl' or amcl_gere == 'true']
    return [
        TimerAction(period=3.0, actions=[
            Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                 name='lifecycle_manager_localisation', output='screen',
                 parameters=[{'autostart': True, 'node_names': noeuds_geres}])]),
        # Filet de sécurité (Windows) : si le lifecycle manager a abandonné, le veilleur
        # termine lui-même configure / activate au bout de 12 s (voir tb3_loopback_sim).
        Node(package='tb3_loopback_sim', executable='veilleur', name='veilleur_localisation',
             output='screen', parameters=[{'noeuds': noeuds_geres, 'delai': 12.0}]),
    ]


def generate_launch_description():
    dossier = get_package_share_directory('tb3_livreur')
    carte = LaunchConfiguration('carte')

    return LaunchDescription([
        DeclareLaunchArgument('carte', default_value=os.path.join(dossier, 'maps', 'atelier.yaml'),
                              description='fichier YAML de la carte produite en partie 3'),
        DeclareLaunchArgument('params_amcl', default_value=os.path.join(dossier, 'config', 'amcl.yaml')),
        DeclareLaunchArgument('sim', default_value='true'),
        DeclareLaunchArgument('urdf', default_value=os.path.join(dossier, 'urdf', 'burger.urdf.xacro')),
        DeclareLaunchArgument('robot', default_value='burger'),
        DeclareLaunchArgument('derive', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('rviz_config',
                              default_value=os.path.join(dossier, 'rviz', 'navigation.rviz'),
                              description='fichier .rviz ouvert par RViz'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('scan_yaw', default_value='0.0'),
        DeclareLaunchArgument('scan_topic', default_value='scan'),
        DeclareLaunchArgument('amcl_gere', default_value='true'),
        DeclareLaunchArgument('publier_monde', default_value='false'),
        DeclareLaunchArgument('obstacle_sur_clic', default_value='false'),

        # scoped=True : rviz='false' ne doit pas écraser l'argument rviz de ce launch
        GroupAction(scoped=True, actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(dossier, 'launch', '2_robot.launch.py')),
            launch_arguments=dict({a: LaunchConfiguration(a) for a in ARGS_ROBOT},
                                  rviz='false').items())]),

        Node(package='nav2_map_server', executable='map_server', name='map_server',
             output='screen', parameters=[{'yaml_filename': carte}]),

        Node(package='nav2_amcl', executable='amcl', name='amcl', output='screen',
             parameters=[LaunchConfiguration('params_amcl')]),

        # Lifecycle manager (retardé de 3 s) et veilleur : voir gestion_du_cycle_de_vie
        OpaqueFunction(function=gestion_du_cycle_de_vie),

        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', LaunchConfiguration('rviz_config')],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
