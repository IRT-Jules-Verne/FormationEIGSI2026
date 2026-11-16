# Correction — TP TurtleBot3 livreur (Nav2)

Document encadrant. Ne pas distribuer avec l'énoncé. Les fichiers complets (URDF, YAML, launch, mission.py) sont ceux de cette branche ; la version à trous de `main` est produite par `outils/trous_tp_navigation.py`.

## Préparation de la séance

- `pixi run nav-build` sur un poste de référence la veille ; vérifier `ros2 launch tb3_livreur 5_navigation.launch.py` avec `carte:=.../maps/atelier_secours.yaml`.
- Les trous attendus par partie : 1 à 3 (URDF), 4 et 5 (SLAM), 6 et 7 (AMCL), 8 et 9 (Nav2), 10 (mission). Un étudiant qui saute un trou obtient une erreur explicite au lancement (`A_COMPLETER` n'est pas un repère, `0.0` n'est pas un rayon).
- Chronométrage de référence (tests automatiques) : tour de cartographie complet 6 min à 0,2 m/s ; un but traversant l'atelier 60 à 90 s ; la tournée `cellule → poste_A → cellule → poste_B → depart` environ 6 min.
- Valeurs attendues dans les fichiers : voir la section « Fichiers » en fin de document.

## Réponses aux questions

**Q1.** Non : l'URDF décrit la structure, pas l'état. L'angle vient de `/joint_states`, publié par `joint_state_publisher_gui` (curseurs), par le simulateur, ou par `turtlebot3_node` à partir des encodeurs sur le vrai robot. Sans `/joint_states`, RViz signale les roues en erreur (« No transform from wheel_left_link »).

**Q2.** y négatif pour la roue droite (y vers la gauche, REP 103) : `y="${-roue_entraxe / 2}"` soit −0,080 m.

**Q3.** `base_link` aurait deux parents (`base_footprint` et la roulette) : `robot_state_publisher` refuse le modèle (« link base_link already has a parent » ou arbre non connexe), rien ne s'affiche. Un URDF est un arbre.

**Q4.** `base_footprint` est au sol (z = 0), `base_link` 10 mm plus haut. `tf2_echo base_footprint base_link` : translation `[0, 0, 0.010]`. Nav2 et AMCL raisonnent dans le plan avec `base_footprint`.

**Q5.** 360 rayons (`angle_increment` ≈ 0,01745 rad), `range_min` 0,12 m, `range_max` 3,5 m, `frame_id: base_scan`. `inf` : rien touché avant `range_max` (le simulateur suit la convention `inf` ; certains drivers mettent 0 ou `range_max`).

**Q6.** Le message `/scan` est identique ; `tf2_echo base_link base_scan` montre une rotation de π ; RViz dessine les points de l'autre côté. Correction dans l'URDF. Lien avec le cas 1 du mini-cas de diagnostic du cours (« le scan tourne autour du robot », slide 100 du support Nav2).

**Q7.** `odom → base_footprint` est publié par le simulateur (`ros2 node info /simulateur` : publieur `/tf`), par `turtlebot3_node` sur le vrai robot. Avec `Fixed Frame = base_footprint`, le robot reste fixe à l'écran et c'est le monde (scan, trace) qui bouge.

**Q8.** Non. Après un carré de 2 m, l'odométrie accuse typiquement 10 à 20 cm et 5 à 15° d'écart (dérive 2 % linéaire, 5 % angulaire, bruit). Avec `derive:=false`, elle revient exactement. L'erreur d'orientation est la plus pénalisante : elle se transforme en erreur de position sur les segments suivants.

**Q9.** La dérive ferait apparaître des murs dédoublés, des pièces déformées, une alcôve qui ne se referme pas. slam_toolbox recale chaque scan (scan matching) et ferme les boucles. `map → odom` vaut l'identité au départ puis s'écarte : c'est la correction accumulée (mesurée après le tour complet : environ 1 m et 13°).

**Q10.** 0 = occupé (noir), 254 = libre, 205 = inconnu (gris) ; `origin` = coin bas-gauche de l'image dans `map` (ici environ `[-0.9, -0.95, 0]`) ; 237 × 158 pixels × 0,05 = 11,9 m × 7,9 m. La table : quatre points ; le robot pourrait passer dessous selon la carte. D'où la retouche.

**Q11.** Non : deux publieurs de `map → odom` (TF accepte les deux, et la transformation alterne entre deux valeurs : le scan saute dans RViz, AMCL et SLAM se contredisent). Une transformation, un responsable.

**Q12.** `ros2 lifecycle get /amcl` → `active [3]` grâce au lifecycle manager (`configure` puis `activate`). Avec `amcl_gere:=false` : `unconfigured [1]`, aucune transformation `map → odom`, RViz affiche « Fixed Frame map does not exist », les particules n'apparaissent pas.

**Q13.** Sans mouvement, aucune mise à jour (`update_min_d`, `update_min_a`) : le nuage ne bouge pas. En roulant vers un coin, les particules incompatibles avec le scan sont rééchantillonnées. `max_particles: 50` : convergence rapide mais fragile (peut manquer la bonne pose) ; `5000` : plus lent (`/particle_cloud` plus lourd), pas plus précis ici.

**Q14.** Dans l'alcôve, le nuage garde deux groupes (une par alcôve) : même scan. En sortant, la cellule de tri (à droite de l'alcôve 1, en dessous de l'alcôve 2) tranche : un groupe disparaît.

**Q15.** La pose estimée et la prédiction par odométrie depuis cette pose. Symptôme : scan décalé des murs, `/amcl_pose` cohérente avec rien. Reprise : nouvelle pose initiale (immédiat), ou localisation globale puis quelques mètres (plus lent, peut échouer dans une zone symétrique). Mettre `recovery_alpha_slow/fast` > 0 permettrait une détection automatique partielle.

**Q16.** Rayon englobant √(0,069² + 0,089²) = 0,113 m → `robot_radius: 0.12` (marge 7 mm). Vitesses 0,22 m/s et 2,84 rad/s (contrôleur **et** velocity_smoother, sinon l'un écrête l'autre). Costmap locale dans `odom` : repère continu, pas de saut quand AMCL corrige ; `robot_base_frame: base_footprint`.

**Q17.** Globale : toute la carte, couches `static_layer`, `obstacle_layer`, `inflation_layer`, fréquence 1 Hz, pour le planificateur. Locale : fenêtre roulante 3 × 3 m (`rolling_window: true`), `obstacle_layer` + `inflation_layer`, 5 Hz, pour le contrôleur. Coûts : 0 libre, 1–252 croissant, 253 inscrit, 254 létal, 255 inconnu.

**Q18.** Couloir 0,70 m dans l'atelier, environ 0,60 m libre sur la carte SLAM (murs épaissis d'une cellule de chaque côté), moins encore dans la costmap quand le scan en direct, décalé par l'erreur d'AMCL, remarque les mêmes murs. Robot 0,12 : zone létale 0,12 de chaque côté, bande libre d'une vingtaine de centimètres au centre → franchissable avec n'importe quelle inflation (0,35 couvre tout le couloir : coût élevé mais fini). `robot_radius: 0.40` : 0,80 > 0,70, plus de bande libre → le planificateur refuse (« failed to create plan »). Inflation = préférence, rayon = contrainte. Pièges vécus en préparation : à 0,36, 0,44 puis 0,56 m, la carte SLAM et le scan en direct fermaient le couloir pour un rayon de 0,12, ou piégeaient le robot dedans (DWB ne trouvait plus de trajectoire sans collision) ; d'où 0,70 m.

**Q19.** `/local_plan` à ~20 Hz (`controller_frequency`), `/plan` à ~1 Hz (`RateController hz="1.0"` dans le BT par défaut). Nav2 replanifie en continu pendant le suivi.

**Q20.** La couche `obstacle_layer` (marking) des deux costmaps ; le chemin global est recalculé à la prochaine replanification (≤ 1 s). Au retrait, le clearing par les rayons libère les cellules quand le lidar les traverse ; dans la globale, la palette peut rester tant qu'aucun rayon ne passe par là.

**Q21.** But dans un mur : `planner_server` : « Failed to create a plan », résultat `ABORTED` après les reprises du BT. But dans l'inconnu : accepté si `allow_unknown: true`. Annulation : `send_goal` affiche `CANCELED`, `/cmd_vel` passe à zéro (le velocity_smoother relaie l'arrêt ; sur un vrai robot, vérifier qu'il s'arrête physiquement).

**Q22 — Pannes.**

| Panne | Variable modifiée | Symptôme | Commande qui tranche | Où corriger |
|---|---|---|---|---|
| 1 | le simulateur publie le lidar sur `/scan_brut` | pas de scan dans RViz, AMCL muet (« cannot publish a pose »), costmaps vides, but refusé ou robot aveugle | `ros2 topic list` (`/scan_brut`), `ros2 topic info /scan -v` : 3 abonnés, 0 publieur | remapping du launch / `scan_topic` |
| 2 | `amcl` absent de `node_names` | pas de `map → odom`, « Fixed Frame map does not exist », `bt_navigator` attend la pose initiale | `ros2 lifecycle get /amcl` → `unconfigured` | `node_names` dans 4_localisation |
| 3 | sortie du velocity_smoother remappée vers `/cmd_vel_lisse` | plan calculé, local_plan publié, robot immobile, puis échec de progression | `ros2 topic info /cmd_vel -v` : 1 abonné (simulateur), 0 publieur ; `ros2 topic list` montre `/cmd_vel_lisse` | remapping du launch |
| 4 | lidar tourné de 180° (`scan_yaw`) | scan à l'envers, AMCL diverge dès que le robot bouge, obstacles marqués derrière le robot | `tf2_echo base_link base_scan` : yaw = 3,14 | URDF (`scan_joint`) |

**Q23.** Un but daté et repéré, un feedback (distance restante, reprises, temps), un résultat explicite, une annulation ; un topic de coordonnées n'a ni acceptation, ni suivi, ni fin. Même mécanique que `RotateAbsolute`.

**Q24.** `TaskResult.FAILED` après les reprises du BT (le planificateur ne trouve plus de chemin) ; `mission.py` affiche « echec vers poste_B » et arrête la tournée.

**Q25.** Non (la structure) ; non (des vitesses) ; AMCL ou SLAM ; non (un chemin, suivi par le contrôleur qui produit des vitesses).

## Fichiers : valeurs attendues

- `burger.urdf.xacro` : `<xacro:roue prefixe="right" y="${-roue_entraxe / 2}"/>` ; roulette `xyz="-0.081 0 -0.004"` ; `scan_joint` fixe, `base_link → base_scan`, `xyz="-0.032 0 0.172"`.
- `slam.yaml` : `odom_frame: odom`, `map_frame: map`, `base_frame: base_footprint`, `scan_topic: /scan`, `mode: mapping`, `max_laser_range: 3.5`.
- `3_slam.launch.py` : `Node(package='slam_toolbox', executable='async_slam_toolbox_node', name='slam_toolbox', output='screen', parameters=[LaunchConfiguration('params_slam')])`.
- `amcl.yaml` : `base_footprint`, `odom`, `map`, `scan`, `laser_max_range: 3.5`, `min_particles: 500`, `max_particles: 2000`, `update_min_d: 0.2`, `update_min_a: 0.2` (tolérance : 300–1000 / 1000–5000 / 0,1–0,3).
- `4_localisation.launch.py` : `NOEUDS_LOCALISATION = ['map_server', 'amcl']`.
- `nav2.yaml` : `robot_radius: 0.12` (0,11–0,15 accepté), `inflation_radius: 0.35` (0,2–0,6 accepté, justifié), `max_vel_x`/`max_speed_xy: 0.22`, `max_vel_theta: 2.84` (une valeur plus basse, justifiée par la prudence, est acceptable), `velocity_smoother` idem, costmap locale `global_frame: odom`, globale `map`, `robot_base_frame: base_footprint`, `topic: /scan`, tolérances 0,15 m / 0,25 rad (0,1–0,3).
- `5_navigation.launch.py` : les sept serveurs : `controller_server, smoother_server, planner_server, behavior_server, bt_navigator, waypoint_follower, velocity_smoother`.
- `mission.py` : `cellule (5.0, 1.2)`, `poste_A (0.2, 6.0)`, `poste_B (10.2, 5.3)`, `rejet (9.8, 0.8)` (± 0,3 m).

## Résultats des tests de référence (poste de développement, 15 novembre 2026)

- SLAM : tour automatique de 62 m avec dérive (9 min 24 s à 0,2 m/s, `ros2 run tb3_loopback_sim pilote`) ; erreur finale de l'estimation 3 à 4 cm ; `map → odom` final ≈ (−0,93 m, 2,80 m, −0,23 rad). La carte obtenue est `maps/atelier_secours.*` (image dans `nav_ws/images/carte_atelier_slam.png`).
- AMCL : après un carré de 2 m avec dérive, erreur 8 cm / 0,5°.
- Nav2 (carte de secours, pose initiale (0, 0)) : cellule 30 s, poste B par le couloir 150 s (le contrôleur hésite dans le couloir entièrement couvert par l'inflation, quelques reprises), rejet 50 s, retour au départ avec une palette sur le trajet 63 s, tournée `mission cellule depart` réussie. Aucune collision dans le simulateur.
- Deux réglages Nav2 indispensables sous Windows, déjà dans `nav2.yaml` : `default_server_timeout: 500` (20 par défaut) et le profil Fast DDS sans mémoire partagée (`outils/fastdds_sans_shm.xml`, activé par pixi).
- `map_saver_cli` : nécessite `--ros-args -p save_map_timeout:=15.0` sous Windows (le délai par défaut de 2 s échoue).
- Inclusions de launch dans un `GroupAction(scoped=True)` : `launch` ne cloisonne pas les configurations, donc le `rviz='false'` passé au launch inclus écrasait l'argument `rviz` du launch parent et RViz ne démarrait jamais dans les parties 2 à 5 (seul `1_modele` l'ouvrait). Corrigé dans `2_robot`, `3_slam`, `4_localisation`, `5_navigation`.
- Lifecycle manager démarré avec 3 s de retard (`TimerAction` dans `4_localisation` et `5_navigation`) : lancé en même temps que les serveurs, il envoyait parfois `configure` avant la fin de la découverte DDS et abandonnait (`Failed to change state for node: map_server`), d'où une carte absente dans RViz. Reprise sans relancer : service `manage_nodes` avec `command: 0` (voir Dépannage de l'énoncé). Trois lancements de suite sans échec après le correctif.
