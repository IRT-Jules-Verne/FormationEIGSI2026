"""Fabrique la version « à trous » du package tb3_livreur à partir de la version complète.

Usage (depuis la racine du dépôt, sur la branche main, après avoir récupéré les fichiers
complets depuis la branche nav2-correction) :

    python outils/trous_tp_navigation.py [dossier_du_package]

Chaque trou est repéré par « >>> À COMPLÉTER n », n correspondant à la numérotation de
l'énoncé (nav_ws/TP_turtlebot_navigation.md). Le script s'arrête si un point d'ancrage
n'est pas trouvé : les fichiers complets ont alors changé et il faut mettre à jour ce script.
"""

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Dossier du package à transformer (un autre dossier peut être donné en argument, pour tester)
PKG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RACINE, 'nav_ws', 'src', 'tb3_livreur')

TROUS = {
    'urdf/burger.urdf.xacro': [
        ('  <xacro:roue prefixe="right" y="${-roue_entraxe / 2}"/>\n',
         '  <!-- >>> À COMPLÉTER 1 : l appel de la macro pour la roue droite (voir la roue gauche) -->\n'),
        ('    <origin xyz="-0.081 0 -0.004" rpy="0 0 0"/>\n',
         '    <origin xyz="0 0 0" rpy="0 0 0"/>  <!-- >>> À COMPLÉTER 2 : 81 mm derrière le centre, 4 mm sous base_link -->\n'),
        ('''  <joint name="scan_joint" type="fixed">
    <parent link="base_link"/>
    <child link="base_scan"/>
    <origin xyz="-0.032 0 0.172" rpy="0 0 $(arg scan_yaw)"/>
  </joint>
''',
         '''  <!-- >>> À COMPLÉTER 3 : le joint fixe « scan_joint », de base_link vers base_scan,
       d'origine xyz="-0.032 0 0.172" et rpy="0 0 $(arg scan_yaw)" (sur le modèle de imu_joint).
       Tant qu'il manque, le lien base_scan n'est rattaché à rien : pas de TF, donc pas de scan. -->
'''),
    ],
    'config/slam.yaml': [
        ('    odom_frame: odom              # publié par l\'odométrie (simulateur ou vrai robot)\n',
         '    odom_frame: A_COMPLETER       # >>> À COMPLÉTER 4 : le repère publié par l\'odométrie\n'),
        ('    map_frame: map                # le repère que slam_toolbox crée et publie (map -> odom)\n',
         '    map_frame: A_COMPLETER        # >>> À COMPLÉTER 4 : le repère que slam_toolbox crée\n'),
        ('    base_frame: base_footprint    # le repère du robot au sol\n',
         '    base_frame: A_COMPLETER       # >>> À COMPLÉTER 4 : le repère du robot au sol\n'),
        ('    scan_topic: /scan\n',
         '    scan_topic: A_COMPLETER       # >>> À COMPLÉTER 4 : le topic du lidar\n'),
        ('    mode: mapping                 # mapping : on construit la carte ; localization : carte figée\n',
         '    mode: A_COMPLETER             # >>> À COMPLÉTER 4 : mapping (on construit la carte) ou localization\n'),
        ('    max_laser_range: 3.5          # portée du LDS-01 (m) ; les rayons plus longs sont ignorés\n',
         '    max_laser_range: 0.0          # >>> À COMPLÉTER 4 : portée du LDS-01 (m)\n'),
    ],
    'launch/3_slam.launch.py': [
        ('''        Node(package='slam_toolbox', executable='async_slam_toolbox_node',
             name='slam_toolbox', output='screen',
             parameters=[LaunchConfiguration('params_slam')]),
''',
         '''        # >>> À COMPLÉTER 5 : le nœud de cartographie, sur le modèle du nœud rviz2 ci-dessous :
        #   package 'slam_toolbox', exécutable 'async_slam_toolbox_node', nom 'slam_toolbox',
        #   output='screen', parameters=[LaunchConfiguration('params_slam')]
'''),
    ],
    'config/amcl.yaml': [
        ('    base_frame_id: base_footprint   # le robot\n',
         '    base_frame_id: A_COMPLETER      # >>> À COMPLÉTER 6 : le repère du robot\n'),
        ('    odom_frame_id: odom             # publié par l\'odométrie\n',
         '    odom_frame_id: A_COMPLETER      # >>> À COMPLÉTER 6 : le repère de l\'odométrie\n'),
        ('    global_frame_id: map            # la carte ; AMCL publie map -> odom\n',
         '    global_frame_id: A_COMPLETER    # >>> À COMPLÉTER 6 : le repère de la carte\n'),
        ('    scan_topic: scan\n',
         '    scan_topic: A_COMPLETER         # >>> À COMPLÉTER 6\n'),
        ('    laser_max_range: 3.5            # portée du LDS-01\n',
         '    laser_max_range: 0.0            # >>> À COMPLÉTER 6 : portée du LDS-01 (m)\n'),
        ('    min_particles: 500\n    max_particles: 2000\n',
         '    min_particles: 0                # >>> À COMPLÉTER 6 : quelques centaines\n'
         '    max_particles: 0                # >>> À COMPLÉTER 6 : quelques milliers\n'),
        ('    update_min_d: 0.2               # mise à jour après 20 cm parcourus...\n'
         '    update_min_a: 0.2               # ... ou 0,2 rad tournés\n',
         '    update_min_d: 0.0               # >>> À COMPLÉTER 6 : mise à jour après N m parcourus...\n'
         '    update_min_a: 0.0               # >>> À COMPLÉTER 6 : ... ou N rad tournés\n'),
    ],
    'launch/4_localisation.launch.py': [
        ("NOEUDS_LOCALISATION = ['map_server', 'amcl']\n",
         "NOEUDS_LOCALISATION = []  # >>> À COMPLÉTER 7 : les deux nœuds, dans l'ordre de démarrage\n"),
    ],
    'config/nav2.yaml': [
        ('      xy_goal_tolerance: 0.15\n      yaw_goal_tolerance: 0.25\n      stateful: true\n',
         '      xy_goal_tolerance: 0.0        # >>> À COMPLÉTER 8 : tolérance d\'arrivée en position (m)\n'
         '      yaw_goal_tolerance: 0.0       # >>> À COMPLÉTER 8 : tolérance d\'arrivée en orientation (rad)\n'
         '      stateful: true\n'),
        ('      max_vel_x: 0.22          # limite du Burger (m/s)\n',
         '      max_vel_x: 0.0           # >>> À COMPLÉTER 8 : vitesse linéaire maximale du Burger (m/s)\n'),
        ('      max_vel_theta: 2.84      # limite du Burger (rad/s)\n',
         '      max_vel_theta: 0.0       # >>> À COMPLÉTER 8 : vitesse angulaire maximale du Burger (rad/s)\n'),
        ('      max_speed_xy: 0.22\n',
         '      max_speed_xy: 0.0        # >>> À COMPLÉTER 8 : comme max_vel_x\n'),
        ('      global_frame: odom            # repère continu : pas de saut quand AMCL corrige\n'
         '      robot_base_frame: base_footprint\n      rolling_window: true\n',
         '      global_frame: A_COMPLETER     # >>> À COMPLÉTER 8 : un repère continu, sans saut\n'
         '      robot_base_frame: A_COMPLETER # >>> À COMPLÉTER 8 : le repère du robot au sol\n'
         '      rolling_window: true\n'),
        ('      robot_radius: 0.12            # rayon englobant du Burger\n',
         '      robot_radius: 0.0             # >>> À COMPLÉTER 8 : rayon englobant du Burger (m), avec marge\n'),
        ('      global_frame: map\n      robot_base_frame: base_footprint\n      robot_radius: 0.12\n',
         '      global_frame: A_COMPLETER     # >>> À COMPLÉTER 8 : le repère de la carte\n'
         '      robot_base_frame: A_COMPLETER # >>> À COMPLÉTER 8\n'
         '      robot_radius: 0.0             # >>> À COMPLÉTER 8 : comme la costmap locale\n'),
        ('        inflation_radius: 0.35\n',
         '        inflation_radius: 0.0         # >>> À COMPLÉTER 8 : portée du coût autour des obstacles (m)\n'),
        ('        inflation_radius: 0.35      # m : au-delà, coût nul ; en dessous, coût décroissant\n',
         '        inflation_radius: 0.0       # >>> À COMPLÉTER 8 : même valeur que la costmap locale\n'),
        ('    max_velocity: [0.22, 0.0, 2.84]\n    min_velocity: [-0.22, 0.0, -2.84]\n',
         '    max_velocity: [0.0, 0.0, 0.0]    # >>> À COMPLÉTER 8 : [vx, vy, vtheta] maximales du Burger\n'
         '    min_velocity: [0.0, 0.0, 0.0]    # >>> À COMPLÉTER 8 : les mêmes, négatives\n'),
    ],
    'launch/5_navigation.launch.py': [
        ("""    noeuds_navigation = ['controller_server', 'smoother_server', 'planner_server',
                         'behavior_server', 'bt_navigator', 'waypoint_follower',
                         'velocity_smoother']
""",
         """    # >>> À COMPLÉTER 9 : les sept serveurs lancés ci-dessous, dans l'ordre de démarrage
    # (le contrôleur et ses costmaps d'abord, le bt_navigator après ceux qu'il appelle)
    noeuds_navigation = []
"""),
    ],
    'tb3_livreur/mission.py': [
        ("""    'cellule': (5.0, 1.2, 1.5708),
    'poste_A': (0.2, 6.0, 3.1416),
    'poste_B': (10.2, 5.3, -1.5708),
    'rejet':   (9.8, 0.8, -1.5708),
""",
         """    'cellule': (0.0, 0.0, 0.0),   # >>> À COMPLÉTER 10 : relever x, y dans RViz (Publish Point)
    'poste_A': (0.0, 0.0, 0.0),   # >>> À COMPLÉTER 10
    'poste_B': (0.0, 0.0, 0.0),   # >>> À COMPLÉTER 10
    'rejet':   (0.0, 0.0, 0.0),   # >>> À COMPLÉTER 10
"""),
    ],
}

# Les deux occurrences de « topic: /scan » (costmaps locale et globale)
TROUS_MULTIPLES = {
    'config/nav2.yaml': [
        ('          topic: /scan\n',
         '          topic: A_COMPLETER        # >>> À COMPLÉTER 8 : le topic du lidar\n'),
    ],
}


def main():
    erreurs = 0
    for fichier, remplacements in TROUS.items():
        chemin = os.path.join(PKG, *fichier.split('/'))
        texte = open(chemin, encoding='utf-8').read()
        for ancre, trou in remplacements:
            if texte.count(ancre) != 1:
                print(f'{fichier} : ancre introuvable ou multiple :\n{ancre}')
                erreurs += 1
                continue
            texte = texte.replace(ancre, trou)
        for ancre, trou in TROUS_MULTIPLES.get(fichier, []):
            if texte.count(ancre) == 0:
                print(f'{fichier} : ancre introuvable :\n{ancre}')
                erreurs += 1
            texte = texte.replace(ancre, trou)
        open(chemin, 'w', encoding='utf-8', newline='\n').write(texte)
        print(f'{fichier} : {texte.count("À COMPLÉTER")} trous')
    if erreurs:
        sys.exit(f'{erreurs} ancre(s) manquante(s) : fichiers complets modifiés ?')


if __name__ == '__main__':
    main()
