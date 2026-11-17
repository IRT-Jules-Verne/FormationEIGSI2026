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
         # Le joint reste présent (seule sa position est fausse) : sans lui, base_scan serait
         # une seconde racine et robot_state_publisher refuserait tout le modèle dès la partie 1.
         '''  <joint name="scan_joint" type="fixed">
    <parent link="base_link"/>
    <child link="base_scan"/>
    <!-- >>> À COMPLÉTER 3 : le lidar est 32 mm derrière le centre du châssis, 172 mm au-dessus de base_link.
         Tant que xyz vaut 0 0 0, le lidar est dessiné (et le scan mesuré) au centre du châssis. -->
    <origin xyz="0 0 0" rpy="0 0 $(arg scan_yaw)"/>
  </joint>
'''),
    ],
    'config/slam.yaml': [
        ('''    # --- Repères et topics : doivent correspondre au robot ---
    odom_frame: odom              # publié par l'odométrie (simulateur ou vrai robot)
    map_frame: map                # le repère que slam_toolbox crée et publie (map -> odom)
    base_frame: base_footprint    # le repère du robot au sol
    scan_topic: /scan
''',
         '''    # --- Repères et topics : doivent correspondre au robot ---
    # >>> À COMPLÉTER 4 : les noms EXACTS, tels que le robot les publie. Pour les trouver,
    #     lancez le robot seul (ros2 launch tb3_livreur 2_robot.launch.py), puis :
    #       ros2 topic list -t                          -> quel topic est un sensor_msgs/msg/LaserScan ?
    #       ros2 topic echo /odom --once --field header.frame_id   -> le repère de l'odométrie
    #       ros2 topic echo /odom --once --field child_frame_id    -> le repère du robot qu'elle déplace
    #       ros2 run tf2_tools view_frames              -> l'arbre TF (frames_*.pdf) : qui est parent de qui ?
    #     map_frame n'existe pas encore dans l'arbre : c'est slam_toolbox qui le crée, au-dessus
    #     de l'odométrie. Prenez le nom standard (REP 105, cours), celui que rviz/slam.rviz
    #     utilise comme « Fixed Frame ».
    odom_frame: A_COMPLETER       # >>> À COMPLÉTER 4 : le repère publié par l'odométrie
    map_frame: A_COMPLETER        # >>> À COMPLÉTER 4 : le repère que slam_toolbox crée
    base_frame: A_COMPLETER       # >>> À COMPLÉTER 4 : le repère du robot au sol
    scan_topic: A_COMPLETER       # >>> À COMPLÉTER 4 : le topic du lidar
'''),
        ('    mode: mapping                 # mapping : on construit la carte ; localization : carte figée\n',
         '    mode: A_COMPLETER             # >>> À COMPLÉTER 4 : mapping (on construit la carte) ou localization\n'),
        ('    max_laser_range: 3.5          # portée du LDS-01 (m) ; les rayons plus longs sont ignorés\n',
         '    max_laser_range: 0.0          # >>> À COMPLÉTER 4 : portée du LDS-01 (m)\n'),
    ],
    # 3_slam.launch.py : fourni complet (plus de trou dans les launch, sauf les listes de nœuds)
    'config/amcl.yaml': [
        ('''    # --- Repères et topics ---
    base_frame_id: base_footprint   # le robot
    odom_frame_id: odom             # publié par l'odométrie
    global_frame_id: map            # la carte ; AMCL publie map -> odom
    scan_topic: scan
''',
         '''    # --- Repères et topics ---
    # >>> À COMPLÉTER 5 : les mêmes que dans slam.yaml, avec les mêmes moyens de vérification
    #     (robot lancé) : ros2 topic list -t, ros2 topic echo /odom --once --field header.frame_id
    #     (et --field child_frame_id), ros2 run tf2_tools view_frames.
    #     Pour la carte : le repère dans lequel /map est publiée. Avec le SLAM lancé :
    #       ros2 topic echo /map --once --field header.frame_id
    #     (map_server publie la carte fournie dans ce même repère.)
    base_frame_id: A_COMPLETER      # >>> À COMPLÉTER 5 : le repère du robot
    odom_frame_id: A_COMPLETER      # >>> À COMPLÉTER 5 : le repère de l'odométrie
    global_frame_id: A_COMPLETER    # >>> À COMPLÉTER 5 : le repère de la carte
    scan_topic: A_COMPLETER         # >>> À COMPLÉTER 5 : le topic du lidar
'''),
        ('    laser_max_range: 3.5            # portée du LDS-01\n',
         '    laser_max_range: 0.0            # >>> À COMPLÉTER 5 : portée du LDS-01 (m)\n'),
        ('    min_particles: 500\n    max_particles: 2000\n',
         '    min_particles: 0                # >>> À COMPLÉTER 5 : quelques centaines (nuage concentré)\n'
         '    max_particles: 0                # >>> À COMPLÉTER 5 : quelques milliers (nuage étalé)\n'),
        ('    update_min_d: 0.2               # mise à jour après 20 cm parcourus...\n'
         '    update_min_a: 0.2               # ... ou 0,2 rad tournés\n',
         '    update_min_d: 0.0               # >>> À COMPLÉTER 5 : distance (m), de l\'ordre d\'une à deux\n'
         '                                    #     longueurs de robot...\n'
         '    update_min_a: 0.0               # >>> À COMPLÉTER 5 : ... ou angle (rad), de l\'ordre de 10 à 20°\n'),
    ],
    'launch/4_localisation.launch.py': [
        ("NOEUDS_LOCALISATION = ['map_server', 'amcl']\n",
         "# >>> À COMPLÉTER 6 : une liste Python de chaînes : les noms (argument name=) des deux\n"
         "# nœuds lancés plus bas, sous le commentaire « Les deux nœuds à cycle de vie ».\n"
         "# Le lifecycle manager les configure puis les active dans l'ordre de la liste :\n"
         "# celui qui fournit une donnée avant celui qui en a besoin.\n"
         "# Forme attendue : ['nom_1', 'nom_2']\n"
         "NOEUDS_LOCALISATION = []\n"),
    ],
    'config/nav2.yaml': [
        ('      xy_goal_tolerance: 0.15\n      yaw_goal_tolerance: 0.25\n      stateful: true\n',
         '      xy_goal_tolerance: 0.0        # >>> À COMPLÉTER 7 : tolérance d\'arrivée en position (m)\n'
         '      yaw_goal_tolerance: 0.0       # >>> À COMPLÉTER 7 : tolérance d\'arrivée en orientation (rad)\n'
         '      stateful: true\n'),
        ('      xy_goal_tolerance: 0.15\n      trans_stopped_velocity',
         '      xy_goal_tolerance: 0.0   # >>> À COMPLÉTER 7 : la même que celle du goal_checker\n'
         '      trans_stopped_velocity'),
        ('      max_vel_x: 0.22          # limite du Burger (m/s)\n',
         '      max_vel_x: 0.0           # >>> À COMPLÉTER 7 : vitesse linéaire maximale du Burger (m/s)\n'),
        ('      max_vel_theta: 2.84      # limite du Burger (rad/s)\n',
         '      max_vel_theta: 0.0       # >>> À COMPLÉTER 7 : vitesse angulaire maximale du Burger (rad/s)\n'),
        ('      max_speed_xy: 0.22\n',
         '      max_speed_xy: 0.0        # >>> À COMPLÉTER 7 : comme max_vel_x\n'),
        ('      global_frame: odom            # repère continu : pas de saut quand AMCL corrige\n'
         '      robot_base_frame: base_footprint\n      rolling_window: true\n',
         '      global_frame: A_COMPLETER     # >>> À COMPLÉTER 7 : un repère fixe dans la salle à court\n'
         '                                    #     terme et continu (sans saut quand AMCL corrige)\n'
         '      robot_base_frame: A_COMPLETER # >>> À COMPLÉTER 7 : le repère du robot au sol\n'
         '      rolling_window: true\n'),
        ('      robot_radius: 0.12            # rayon englobant du Burger\n',
         '      robot_radius: 0.0             # >>> À COMPLÉTER 7 : rayon du cercle englobant le Burger (m), voir Q16\n'),
        ('      global_frame: map\n      robot_base_frame: base_footprint\n      robot_radius: 0.12\n',
         '      global_frame: A_COMPLETER     # >>> À COMPLÉTER 7 : le repère de la carte\n'
         '      robot_base_frame: A_COMPLETER # >>> À COMPLÉTER 7\n'
         '      robot_radius: 0.0             # >>> À COMPLÉTER 7 : comme la costmap locale\n'),
        ('        inflation_radius: 0.35\n',
         '        inflation_radius: 0.0         # >>> À COMPLÉTER 7 : portée du coût (m) : 2 à 3 fois robot_radius\n'),
        ('        inflation_radius: 0.35      # m : au-delà, coût nul ; en dessous, coût décroissant\n',
         '        inflation_radius: 0.0       # >>> À COMPLÉTER 7 : même valeur que la costmap locale\n'),
        ('    max_velocity: [0.22, 0.0, 2.84]\n    min_velocity: [-0.22, 0.0, -2.84]\n',
         '    max_velocity: [0.0, 0.0, 0.0]    # >>> À COMPLÉTER 7 : [vx, vy, vtheta] maximales du Burger\n'
         '    min_velocity: [0.0, 0.0, 0.0]    # >>> À COMPLÉTER 7 : les mêmes, négatives\n'),
    ],
    'launch/5_navigation.launch.py': [
        ("""    noeuds_navigation = ['controller_server', 'smoother_server', 'planner_server',
                         'behavior_server', 'bt_navigator', 'waypoint_follower',
                         'velocity_smoother']
""",
         """    # >>> À COMPLÉTER 8 : une liste Python de chaînes : les noms (argument name=) des sept
    # Node(...) lancés plus bas, sous le commentaire « Les serveurs Nav2 ».
    # Ordre de démarrage : le contrôleur (et sa costmap locale) d'abord, le bt_navigator après
    # les serveurs qu'il appelle, le velocity_smoother en dernier. L'ordre des Node(...) dans
    # le fichier convient. Forme attendue : ['nom_1', 'nom_2', ...]
    noeuds_navigation = []
"""),
    ],
    'tb3_livreur/mission.py': [
        ("""    'cellule': (5.0, 1.2, 1.5708),
    'poste_A': (0.2, 6.0, 3.1416),
    'poste_B': (10.2, 5.3, -1.5708),
    'rejet':   (9.8, 0.8, -1.5708),
""",
         """    'cellule': (0.0, 0.0, 0.0),   # >>> À COMPLÉTER 9 : relever x, y dans RViz (Publish Point)
    'poste_A': (0.0, 0.0, 0.0),   # >>> À COMPLÉTER 9
    'poste_B': (0.0, 0.0, 0.0),   # >>> À COMPLÉTER 9
    'rejet':   (0.0, 0.0, 0.0),   # >>> À COMPLÉTER 9
"""),
    ],
}

# Les deux occurrences de « topic: /scan » (costmaps locale et globale)
TROUS_MULTIPLES = {
    'config/nav2.yaml': [
        ('          topic: /scan\n',
         '          topic: A_COMPLETER        # >>> À COMPLÉTER 7 : le topic du lidar\n'),
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
