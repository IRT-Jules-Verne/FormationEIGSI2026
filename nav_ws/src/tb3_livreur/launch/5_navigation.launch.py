"""Partie 5 : naviguer avec Nav2.

    ros2 launch tb3_livreur 5_navigation.launch.py [carte:=...] [panne:=0]

Lance la localisation (4_localisation.launch.py) puis les serveurs Nav2 (config/nav2.yaml) :
  - planner_server    : costmap globale + planificateur (NavFn) -> /plan
  - controller_server : costmap locale + contrôleur (DWB) -> /cmd_vel_nav, /local_plan
  - smoother_server   : lissage du chemin
  - behavior_server   : comportements de reprise (spin, backup, wait...)
  - bt_navigator      : l'action /navigate_to_pose, orchestrée par un behavior tree
  - waypoint_follower : suite de buts
  - velocity_smoother : lisse /cmd_vel_nav -> /cmd_vel (c'est lui qui parle au robot)
  - lifecycle_manager_navigation : configure puis active tous ces nœuds, dans l'ordre.

Argument panne:=N (partie 6, diagnostic) : introduit UNE anomalie dans la chaîne.
  1  le simulateur publie le lidar sur un autre topic
  2  amcl n'est plus géré par le lifecycle manager
  3  la sortie du velocity_smoother ne va plus vers /cmd_vel
  4  le lidar est monté à l'envers (tourné de 180°)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

# Les configurations de launch sont globales : chaque fichier de paramètres a son propre
# nom d'argument (params_amcl, params_nav2) pour ne pas s'écraser entre launch inclus.
ARGS_LOCALISATION = ['carte', 'sim', 'urdf', 'robot', 'x', 'y', 'yaw', 'derive',
                     'publier_monde', 'obstacle_sur_clic', 'params_amcl']


def generate_launch_description():
    dossier = get_package_share_directory('tb3_livreur')
    panne = LaunchConfiguration('panne')
    params = LaunchConfiguration('params_nav2')

    # Traduction de l'argument panne en réglages concrets
    scan_topic = PythonExpression(["'scan_brut' if '", panne, "' == '1' else 'scan'"])
    amcl_gere = PythonExpression(["'false' if '", panne, "' == '2' else 'true'"])
    sortie_smoother = PythonExpression(["'cmd_vel_lisse' if '", panne, "' == '3' else 'cmd_vel'"])
    scan_yaw = PythonExpression(["'3.14159' if '", panne, "' == '4' else '0.0'"])

    # >>> À COMPLÉTER 8 : une liste Python de chaînes : les noms (argument name=) des sept
    # Node(...) lancés plus bas, sous le commentaire « Les serveurs Nav2 ».
    # Ordre de démarrage : le contrôleur (et sa costmap locale) d'abord, le bt_navigator après
    # les serveurs qu'il appelle, le velocity_smoother en dernier. L'ordre des Node(...) dans
    # le fichier convient. Forme attendue : ['nom_1', 'nom_2', ...]
    noeuds_navigation = []

    return LaunchDescription([
        DeclareLaunchArgument('carte', default_value=os.path.join(dossier, 'maps', 'atelier.yaml')),
        DeclareLaunchArgument('params_nav2', default_value=os.path.join(dossier, 'config', 'nav2.yaml')),
        DeclareLaunchArgument('params_amcl', default_value=os.path.join(dossier, 'config', 'amcl.yaml')),
        DeclareLaunchArgument('sim', default_value='true'),
        DeclareLaunchArgument('urdf', default_value=os.path.join(dossier, 'urdf', 'burger.urdf.xacro')),
        DeclareLaunchArgument('robot', default_value='burger'),
        DeclareLaunchArgument('derive', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('panne', default_value='0'),
        DeclareLaunchArgument('publier_monde', default_value='false'),
        DeclareLaunchArgument('obstacle_sur_clic', default_value='false'),

        # scoped=True : rviz='false' ne doit pas écraser l'argument rviz de ce launch
        GroupAction(scoped=True, actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(dossier, 'launch', '4_localisation.launch.py')),
            launch_arguments=dict({a: LaunchConfiguration(a) for a in ARGS_LOCALISATION},
                                  scan_topic=scan_topic, scan_yaw=scan_yaw,
                                  amcl_gere=amcl_gere, rviz='false').items())]),

        # Les serveurs Nav2 : sept nœuds à cycle de vie, à activer par le lifecycle manager
        Node(package='nav2_controller', executable='controller_server', name='controller_server',
             output='screen', parameters=[params],
             remappings=[('cmd_vel', 'cmd_vel_nav')]),
        Node(package='nav2_smoother', executable='smoother_server', name='smoother_server',
             output='screen', parameters=[params]),
        Node(package='nav2_planner', executable='planner_server', name='planner_server',
             output='screen', parameters=[params]),
        Node(package='nav2_behaviors', executable='behavior_server', name='behavior_server',
             output='screen', parameters=[params]),
        Node(package='nav2_bt_navigator', executable='bt_navigator', name='bt_navigator',
             output='screen', parameters=[params]),
        Node(package='nav2_waypoint_follower', executable='waypoint_follower',
             name='waypoint_follower', output='screen', parameters=[params]),
        Node(package='nav2_velocity_smoother', executable='velocity_smoother',
             name='velocity_smoother', output='screen', parameters=[params],
             remappings=[('cmd_vel', 'cmd_vel_nav'), ('cmd_vel_smoothed', sortie_smoother)]),
        # Démarré avec un délai, comme dans 4_localisation : sinon « configure » peut partir
        # avant la fin de la découverte DDS et le lifecycle manager abandonne.
        TimerAction(period=3.0, actions=[
            Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                 name='lifecycle_manager_navigation', output='screen',
                 parameters=[{'autostart': True, 'node_names': noeuds_navigation}])]),
        # Filet de sécurité (Windows), comme dans 4_localisation
        Node(package='tb3_loopback_sim', executable='veilleur', name='veilleur_navigation',
             output='screen', parameters=[{'noeuds': noeuds_navigation, 'delai': 15.0}]),

        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', os.path.join(dossier, 'rviz', 'navigation.rviz')],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
