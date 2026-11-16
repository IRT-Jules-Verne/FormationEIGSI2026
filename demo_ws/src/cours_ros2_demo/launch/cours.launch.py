"""Démonstrations du cours ROS 2 « Navigation autonome avec Nav2 » (FormationEIGSI_NAV2Opensource.pdf).

    pixi run cours demo:=4.5            # depuis la racine du dépôt (recommandé)
    ros2 launch cours_ros2_demo cours.launch.py demo:=4.5   [panne:=1]

Sans argument, affiche la liste des démonstrations. Chaque démonstration lance les nœuds
nécessaires (sur le TurtleBot3 Waffle, dans l'atelier MecaTri) et affiche dans le terminal
les commandes à taper pendant la présentation, une observation à la fois.

Les scénarios réutilisent les launch files du TP (package tb3_livreur, workspace nav_ws)
avec la description et les configurations du Waffle fournies dans ce package.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

# ---------------------------------------------------------------------------------------
# Table des démonstrations : numéro -> (slide du cours, titre, launch du TP, arguments,
# commandes à montrer). Les commandes sont affichées, pas exécutées.
# ---------------------------------------------------------------------------------------
SCENARIOS = {
    # --- Outils et architecture (slides 1 a 11) ---
    '4.1': dict(
        slide=11, titre='Les outils d observation : node, topic, action, RViz',
        launch='2_robot', args={'rviz': 'false'},
        commandes=[
            'ros2 node list',
            'ros2 topic list',
            'ros2 topic info /scan -v           # qui publie, qui lit, quelle QoS',
            'ros2 topic echo /scan --once --no-arr',
            'ros2 action list -t                # vide : Nav2 n est pas lance',
            'ros2 run tf2_tools view_frames     # puis ouvrir le PDF',
        ]),
    # --- Comment je me deplace ? (slides 15 a 24) ---
    '4.2': dict(
        slide=17, titre='cmd_vel : une vitesse demandee, pas un deplacement ; Twist ; duree de validite',
        launch='2_robot', args={'rviz': 'true'},
        commandes=[
            'ros2 topic type /cmd_vel                                                      # Twist (slide 18)',
            'ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}}"   # 10 cm ? non : 0,5 s puis arret (slide 20)',
            'ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}}"    # avance tant qu on publie',
            'ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.5}}"   # positif : a gauche (slide 19)',
            'ros2 topic echo /odom --once        # ce que le robot croit avoir fait (slide 22)',
            'Arbitrage (slide 21) : lancer en plus teleop_twist_keyboard : deux publieurs, le robot suit le dernier message recu',
        ]),
    '4.3': dict(
        slide=23, titre='L odometrie derive : le carre qui ne se referme pas',
        # Depart en (0.4, 0.6) : le seul coin de l atelier ou un carre de 2 m (vers +x puis +y) tient
        launch='2_robot', args={'rviz': 'true', 'publier_map_odom_tf': 'true', 'publier_monde': 'true',
                                'x': '0.4', 'y': '0.6'},
        commandes=[
            'Dans RViz (panneau Displays) : Fixed Frame = map ; cocher "Monde (simulateur, demo)" et "Pose vraie (simulateur)"',
            '  -> la vraie salle et la vraie pose (verite terrain) s affichent a cote de la trace odometrique, qui s en ecarte',
            'ros2 run tb3_loopback_sim pilote --carre 2.0      # un carre de 2 m',
            'ros2 run tf2_ros tf2_echo odom base_footprint     # odom ne revient pas a zero',
            'Relancer avec derive:=false pour comparer : pixi run cours demo:=4.3 derive:=false',
        ]),
    # --- Comment je me repere dans l espace ? (slides 26 a 56) ---
    '4.4': dict(
        slide=27, titre='Le contrat LaserScan et le repere du lidar',
        launch='2_robot', args={'rviz': 'true'},
        commandes=[
            'ros2 interface show sensor_msgs/msg/LaserScan',
            'ros2 topic echo /scan --once --no-arr     # frame_id, angle_min, increment, range_min/max',
            'ros2 run tf2_ros tf2_echo base_link base_scan',
            'Table pres du depart : seuls les pieds sont vus (slide 28)',
        ]),
    '4.5': dict(
        slide=35, titre='Demonstration TF dans RViz : lire l arbre, changer le Fixed Frame',
        launch='2_robot', args={'rviz': 'true'},
        commandes=[
            'ros2 run tf2_ros tf2_echo odom base_footprint',
            'ros2 run teleop_twist_keyboard teleop_twist_keyboard   # puis Fixed Frame : base_link, odom, map (absent)',
            'ros2 run tf2_tools view_frames                         # qui publie quoi (slide 33)',
            'Variante lidar a l envers : pixi run cours demo:=4.5b',
        ]),
    '4.5b': dict(
        slide=35, titre='TF dans RViz : le mur tourne avec le robot (lidar monte a 180 degres)',
        launch='2_robot', args={'rviz': 'true', 'scan_yaw': '3.14159'},
        commandes=[
            'ros2 run teleop_twist_keyboard teleop_twist_keyboard',
            'ros2 run tf2_ros tf2_echo base_link base_scan     # la rotation de 180 degres est la',
            'ros2 topic echo /scan --once --no-arr             # le message, lui, n a pas change',
        ]),
    '4.6': dict(
        slide=39, titre='Du modele aux transformations : URDF + /joint_states -> /tf, /tf_static',
        launch='1_modele', args={'gui': 'true', 'rviz': 'true'},
        commandes=[
            'ros2 topic echo /joint_states --once',
            'ros2 topic echo /tf_static --once      # les liaisons fixes, une seule fois',
            'ros2 topic hz /tf                      # les roues, en continu (bouger les curseurs)',
            'ros2 node info /robot_state_publisher',
            'xacro $(ros2 pkg prefix cours_ros2_demo)/share/cours_ros2_demo/urdf/waffle.urdf.xacro | Select-String joint   # slides 36 a 38',
        ]),
    '4.7': dict(
        slide=65, titre='Demonstration de localisation : AMCL, pose initiale, convergence, ambiguite',
        # rviz_config : fichier du dossier rviz/ de ce package (complete dans lancer)
        launch='4_localisation', args={'rviz': 'true', 'rviz_config': 'localisation.rviz'},
        commandes=[
            'RViz au lancement : carte, scan, nuage AMCL (vert, pose initiale (0,0) de waffle_amcl.yaml),',
            '  pose AMCL avec son ellipse de covariance (bleu), pose vraie (magenta), trace odometrique, TF map/odom/base_footprint',
            'Dans RViz : 2D Pose Estimate legerement faux, puis teleop : le nuage se resserre (slide 52)',
            'ros2 run teleop_twist_keyboard teleop_twist_keyboard',
            'ros2 run tf2_ros tf2_echo map odom                                       # la correction d AMCL (slide 40)',
            'ros2 service call /reinitialize_global_localization std_srvs/srv/Empty   # localisation globale (slide 56)',
            'ros2 topic pub --once /simulateur/teleporter geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: 5.0, y: 6.2}, orientation: {z: 0.707, w: 0.707}}}}"   # robot kidnappe dans une alcove (slide 54)',
            'ros2 lifecycle get /amcl                                                 # noeud a cycle de vie (slide 69)',
        ]),
    # --- Comment faire une carte ? (slides 58 a 64) ---
    '4.8': dict(
        slide=61, titre='SLAM Toolbox en action : la carte se construit, la boucle se ferme',
        launch='3_slam', args={'rviz': 'true'},
        commandes=[
            'ros2 run tb3_loopback_sim pilote           # tour automatique de l atelier (6 min)',
            'ros2 run tf2_ros tf2_echo map odom         # la correction appliquee par le SLAM',
            'ros2 run nav2_map_server map_saver_cli -f carte_demo --ros-args -p save_map_timeout:=15.0',
        ]),
    # --- Planifier et suivre un chemin (slides 67 a 101) ---
    '4.9': dict(
        slide=75, titre='Costmaps, inflation, rayon du robot et passage etroit',
        launch='5_navigation', args={'rviz': 'true'},
        commandes=[
            'Dans RViz : 2D Pose Estimate puis Nav2 Goal vers le poste B (en haut a droite, derriere le couloir)',
            'ros2 param get /global_costmap/global_costmap plugins                                  # les couches (slide 77)',
            'ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.15    # (slide 81)',
            'ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 1.0',
            'ros2 param set /global_costmap/global_costmap robot_radius 0.45   # le couloir (0,70 m) devient infranchissable pour le Waffle (slide 78)',
            'ros2 topic hz /plan ; ros2 topic hz /local_plan                   # planner 1 Hz, controleur 20 Hz (slides 84, 91)',
        ]),
    '4.10': dict(
        slide=101, titre='Demonstration du trajet complet : but, chemin, obstacle, annulation',
        launch='5_navigation', args={'rviz': 'true', 'obstacle_sur_clic': 'true'},
        commandes=[
            'Dans RViz : 2D Pose Estimate, puis Nav2 Goal ; outil Publish Point = poser une palette',
            'ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 0.2, y: 6.0}, orientation: {w: 1.0}}}}" --feedback   # slide 70',
            'ros2 topic echo /cmd_vel',
            'ros2 service call /simulateur/ajouter_obstacle turtlesim/srv/Spawn "{x: 0.5, y: 3.5, name: palette}"',
            'ros2 service call /simulateur/retirer_obstacle turtlesim/srv/Kill "{name: palette}"',
            'ros2 param get /controller_server goal_checker.xy_goal_tolerance   # progression et arrivee (slide 95)',
            'Ctrl+C sur send_goal = annulation : verifier /cmd_vel et l arret effectif',
        ]),
    '4.11': dict(
        slide=99, titre='Diagnostiquer par couches : une panne preparee',
        launch='5_navigation', args={'rviz': 'true'}, panne=True,
        commandes=[
            'pixi run cours demo:=4.11 panne:=1   (1 lidar sur un autre topic, 2 amcl non gere, 3 cmd_vel perdu, 4 lidar a l envers)',
            'ros2 topic info /scan -v',
            'ros2 lifecycle get /amcl',
            'ros2 topic info /cmd_vel -v',
            'ros2 run tf2_ros tf2_echo base_link base_scan',
        ]),
}


def lancer(context):
    demo = LaunchConfiguration('demo').perform(context)
    if demo not in SCENARIOS:
        lignes = ['', 'Demonstrations disponibles (pixi run cours demo:=NUMERO) :']
        for num, sc in SCENARIOS.items():
            lignes.append(f'  {num:5s}  slide {sc["slide"]:3d}  {sc["titre"]}')
        if demo not in ('', 'liste'):
            lignes.append(f'\nDemo inconnue : {demo}')
        return [LogInfo(msg='\n'.join(lignes))]

    sc = SCENARIOS[demo]
    dossier_demo = get_package_share_directory('cours_ros2_demo')
    dossier_tp = get_package_share_directory('tb3_livreur')

    # Le Waffle de démonstration : description et configurations propres à ce package
    args = {
        'urdf': os.path.join(dossier_demo, 'urdf', 'waffle.urdf.xacro'),
        'robot': 'waffle',
        'carte': os.path.join(dossier_demo, 'maps', 'atelier.yaml'),
        'params_amcl': os.path.join(dossier_demo, 'config', 'waffle_amcl.yaml'),
        'derive': LaunchConfiguration('derive').perform(context),
        'params_slam': os.path.join(dossier_demo, 'config', 'waffle_slam.yaml'),
        'params_nav2': os.path.join(dossier_demo, 'config', 'waffle_nav2.yaml'),
    }
    args.update(sc.get('args', {}))
    if 'rviz_config' in args:
        args['rviz_config'] = os.path.join(dossier_demo, 'rviz', args['rviz_config'])
    if sc.get('panne'):
        args['panne'] = LaunchConfiguration('panne').perform(context)

    bandeau = ['', '=' * 78,
               f'  DEMO {demo} (slide {sc["slide"]}) : {sc["titre"]}',
               '=' * 78,
               '  Dans un autre terminal (pixi run nav), une commande a la fois :']
    bandeau += ['    ' + c for c in sc['commandes']]
    bandeau += ['=' * 78, '']

    return [
        LogInfo(msg='\n'.join(bandeau)),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(dossier_tp, 'launch', sc['launch'] + '.launch.py')),
            launch_arguments=args.items()),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('demo', default_value='', description='numero de la demonstration'),
        # Défaut 0 (aucune panne) : les configurations de launch sont globales, une valeur
        # par défaut à 1 ici s'appliquerait aussi aux démos 4.9 et 4.10 (lidar sur /scan_brut).
        DeclareLaunchArgument('panne', default_value='0',
                              description='demo 4.11 : panne:=1..4 (0 = aucune)'),
        DeclareLaunchArgument('derive', default_value='true'),
        OpaqueFunction(function=lancer),
    ])
