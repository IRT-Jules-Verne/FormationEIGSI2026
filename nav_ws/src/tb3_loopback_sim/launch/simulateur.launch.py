"""Lance le simulateur seul, dans le monde de l'atelier MecaTri.

Usage :
    ros2 launch tb3_loopback_sim simulateur.launch.py [x:=0.0 y:=0.0 yaw:=0.0]
        [derive:=true|false] [publier_map_odom_tf:=false] [publier_monde:=false]

Le simulateur a besoin de la transformation base_footprint -> base_scan (publiée par
robot_state_publisher à partir du modèle URDF) pour produire un scan : lancez aussi le
modèle du robot (package tb3_livreur, launch 2_robot.launch.py le fait pour vous).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    yaw = LaunchConfiguration('yaw')
    derive = LaunchConfiguration('derive')
    publier_map_odom_tf = LaunchConfiguration('publier_map_odom_tf')
    publier_monde = LaunchConfiguration('publier_monde')
    obstacle_sur_clic = LaunchConfiguration('obstacle_sur_clic')
    monde = LaunchConfiguration('monde')
    scan_topic = LaunchConfiguration('scan_topic')

    robot = LaunchConfiguration('robot')

    # Dimensions et limites selon le modèle (fiches ROBOTIS) : rayon de collision,
    # vitesses maximales, entraxe des roues (pour /joint_states).
    def selon_robot(burger, waffle):
        return PythonExpression(['str(', str(waffle), ') if "', robot, '" == "waffle" else str(', str(burger), ')'])

    parametres_communs = {
        'pose_x': x,
        'pose_y': y,
        'pose_yaw': yaw,
        'publier_map_odom_tf': publier_map_odom_tf,
        'publier_monde': publier_monde,
        'obstacle_sur_clic': obstacle_sur_clic,
        'monde': monde,
        'rayon_collision': selon_robot(0.10, 0.20),
        'vitesse_max_lin': selon_robot(0.22, 0.26),
        'vitesse_max_ang': selon_robot(2.84, 1.82),
        'roue_entraxe': selon_robot(0.160, 0.287),
    }

    return LaunchDescription([
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('derive', default_value='true',
                              description="false : odometrie parfaite (sans derive ni bruit)"),
        DeclareLaunchArgument('publier_map_odom_tf', default_value='false'),
        DeclareLaunchArgument('publier_monde', default_value='false'),
        DeclareLaunchArgument('obstacle_sur_clic', default_value='false'),
        DeclareLaunchArgument('monde', default_value='',
                              description='fichier YAML du monde (vide = atelier MecaTri)'),
        DeclareLaunchArgument('scan_topic', default_value='scan',
                              description='nom du topic du lidar (exercice de diagnostic)'),
        DeclareLaunchArgument('robot', default_value='burger',
                              description='burger ou waffle : dimensions et vitesses limites'),

        Node(package='tb3_loopback_sim', executable='simulateur', name='simulateur',
             output='screen', emulate_tty=True,
             condition=IfCondition(derive),
             remappings=[('scan', scan_topic)],
             parameters=[parametres_communs]),
        Node(package='tb3_loopback_sim', executable='simulateur', name='simulateur',
             output='screen', emulate_tty=True,
             condition=UnlessCondition(derive),
             remappings=[('scan', scan_topic)],
             parameters=[parametres_communs,
                         {'odom_derive_lin': 0.0, 'odom_derive_ang': 0.0,
                          'odom_bruit_lin': 0.0, 'odom_bruit_ang': 0.0}]),
    ])
