"""Mini TP « Découverte de Nav2 » (1 h 30) : pixi run decouverte etape:=...

    etape:=odometrie  [derive:=true|false]   le robot, RViz, l'odométrie qui dérive
    etape:=slam       [derive:=true|false]   cartographie par téléopération (slam_toolbox)
    etape:=navigation [carte:=nav_ws/ma_carte.yaml]   AMCL + Nav2 sur une carte

Autonome : n'utilise que des fichiers complets (TurtleBot3 Waffle des démonstrations du
cours, configurations config/waffle_*.yaml) et le simulateur tb3_loopback_sim. Il ne
dépend pas des fichiers à compléter du TP navigation (package tb3_livreur).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription, LogInfo,
                            OpaqueFunction, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

ETAPES = ('odometrie', 'slam', 'navigation')

# Départ de l'étape odométrie : le seul coin de l'atelier où un carré de 2 m tient
DEPART_CARRE = (0.4, 0.6)

NOEUDS_LOCALISATION = ['map_server', 'amcl']
NOEUDS_NAVIGATION = ['controller_server', 'smoother_server', 'planner_server',
                     'behavior_server', 'bt_navigator', 'waypoint_follower',
                     'velocity_smoother']


def gestion(nom, noeuds, delai_veilleur):
    """Lifecycle manager (démarré 3 s après les serveurs) et veilleur de secours."""
    return [
        TimerAction(period=3.0, actions=[
            Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                 name=f'lifecycle_manager_{nom}', output='screen',
                 parameters=[{'autostart': True, 'node_names': noeuds}])]),
        Node(package='tb3_loopback_sim', executable='veilleur', name=f'veilleur_{nom}',
             output='screen', parameters=[{'noeuds': noeuds, 'delai': delai_veilleur}]),
    ]


def trouver_carte(carte, racine):
    """Accepte un chemin absolu, relatif au dossier courant ou au dépôt, avec ou sans .yaml."""
    candidats = [carte, os.path.join(racine, carte), os.path.join(racine, 'nav_ws', carte)]
    for c in list(candidats):
        if not c.endswith('.yaml'):
            candidats.append(c + '.yaml')
    for c in candidats:
        if os.path.isfile(c):
            return os.path.abspath(c)
    raise RuntimeError(f'Carte introuvable : {carte} (essayes : {candidats})')


def lancer(context):
    etape = LaunchConfiguration('etape').perform(context)
    if etape not in ETAPES:
        return [LogInfo(msg=f'\nChoisir une etape : pixi run decouverte etape:=' +
                        '|'.join(ETAPES) + '\n')]
    derive = LaunchConfiguration('derive').perform(context)
    demo = get_package_share_directory('cours_ros2_demo')
    tp = get_package_share_directory('tb3_livreur')
    sim = get_package_share_directory('tb3_loopback_sim')
    config = os.path.join(demo, 'config')

    x, y = DEPART_CARRE if etape == 'odometrie' else (0.0, 0.0)
    description = ParameterValue(
        Command(['xacro ', os.path.join(demo, 'urdf', 'waffle.urdf.xacro')]), value_type=str)

    actions = [
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen',
             parameters=[{'robot_description': description}]),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(sim, 'launch', 'simulateur.launch.py')),
            launch_arguments={
                'robot': 'waffle', 'x': str(x), 'y': str(y), 'derive': derive,
                'publier_monde': 'true' if etape == 'odometrie' else 'false',
                'obstacle_sur_clic': 'true' if etape == 'navigation' else 'false',
            }.items()),
    ]

    if etape == 'odometrie':
        # Le repère odom est posé sur la pose de départ, dans la salle : tout ce qui est
        # dessiné via odom (robot, trace, scan) montre ce que CROIT l'odométrie, et la pose
        # vraie du simulateur montre où est réellement le robot.
        actions.append(Node(
            package='tf2_ros', executable='static_transform_publisher', name='map_vers_odom',
            arguments=['--x', str(x), '--y', str(y), '--frame-id', 'map',
                       '--child-frame-id', 'odom']))
        rviz = os.path.join(demo, 'rviz', 'decouverte_odometrie.rviz')

    elif etape == 'slam':
        actions.append(Node(
            package='slam_toolbox', executable='async_slam_toolbox_node', name='slam_toolbox',
            output='screen', parameters=[os.path.join(config, 'waffle_slam.yaml')]))
        rviz = os.path.join(tp, 'rviz', 'slam.rviz')

    else:  # navigation
        racine = os.environ.get('PIXI_PROJECT_ROOT', os.getcwd())
        carte = trouver_carte(LaunchConfiguration('carte').perform(context), racine)
        params = os.path.join(config, 'waffle_nav2.yaml')
        actions += [
            LogInfo(msg=f'Carte : {carte}'),
            Node(package='nav2_map_server', executable='map_server', name='map_server',
                 output='screen', parameters=[{'yaml_filename': carte}]),
            Node(package='nav2_amcl', executable='amcl', name='amcl', output='screen',
                 parameters=[os.path.join(config, 'waffle_amcl.yaml')]),
            Node(package='nav2_controller', executable='controller_server',
                 name='controller_server', output='screen', parameters=[params],
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
                 remappings=[('cmd_vel', 'cmd_vel_nav'), ('cmd_vel_smoothed', 'cmd_vel')]),
        ]
        actions += gestion('localisation', NOEUDS_LOCALISATION, 12.0)
        actions += gestion('navigation', NOEUDS_NAVIGATION, 15.0)
        rviz = os.path.join(tp, 'rviz', 'navigation.rviz')

    actions.append(Node(package='rviz2', executable='rviz2', name='rviz2',
                        arguments=['-d', rviz]))
    return actions


def generate_launch_description():
    demo = get_package_share_directory('cours_ros2_demo')
    return LaunchDescription([
        DeclareLaunchArgument('etape', default_value='aucune',
                              description='odometrie | slam | navigation'),
        DeclareLaunchArgument('derive', default_value='true',
                              description='false : odometrie parfaite (pas de glissement)'),
        DeclareLaunchArgument('carte', default_value=os.path.join(demo, 'maps', 'atelier.yaml'),
                              description='carte pour l etape navigation'),
        OpaqueFunction(function=lancer),
    ])
