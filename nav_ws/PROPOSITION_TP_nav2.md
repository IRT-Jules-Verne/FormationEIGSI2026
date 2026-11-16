# Proposition v2 — TP ROS 2 : navigation autonome d'un TurtleBot3 Burger (Nav2)

**Durée cible :** 6 h 30 – 7 h (suivi et correction compris)   **Public :** étudiants ayant suivi le module 4 (Nav2) et fait le TP « tortue livreuse »   **Organisation :** individuel, PC Windows + environnement Pixi du cours. Pas de robot réel prévu ; le passage au réel doit rester possible en changeant un seul launch.

> Version 2 du 15 novembre 2026, après tes retours : questions posées **avant** chaque manipulation avec des pistes à explorer, SLAM raccourci, monde fictif avec obstacles, dérive d'odométrie activée, pas de robot réel, travail individuel, démos de cours dans `demo_ws`. Les paquets Nav2 / slam_toolbox / turtlebot3_description sont validés sur ta machine.

---

## 1. Ce qui ne change pas par rapport à la v1

- **Fil conducteur :** construire la chaîne couche par couche (modèle → lidar → SLAM → AMCL → Nav2 → mission) et savoir à chaque étape **qui publie quelle transformation TF**. C'est exactement la slide 22 du cours (« Qui publie chaque transformation ? ») et la vérification collective de la slide 95.
- **Simulateur loopback embarqué** (`tb3_loopback_sim`, adaptation Python de la version Jazzy) : consomme `/cmd_vel`, produit `/odom`, `/scan`, `odom → base_footprint`. Même contrat que `turtlebot3_bringup` (slide 14 : « Nav2 retrouve des interfaces comparables »). Ajouts : dérive d'odométrie, bruit de scan, collision avec les murs, carte « monde » cachée servie à part, `publish_map_odom_tf: false`, pas d'horloge simulée.
- **Code fourni, trous à compléter** (`>>> À COMPLÉTER`), points de contrôle visibles par l'encadrant, aide-mémoire et dépannage en fin d'énoncé, PDF généré par `outils/md_vers_pdf.py`.
- Les behavior trees ne sont pas configurés : 5 minutes au bilan pour montrer le XML `navigate_to_pose_w_replanning_and_recovery.xml` que le cours a déjà schématisé (slide 67).

## 2. Nouveau format des questions : prédire, explorer, puis retenir

Chaque étape de l'énoncé suit le même gabarit, calé sur la méthode du cours (« faire prédire avant de montrer ») :

```markdown
### 2.3 Le repère du lidar

**Q6 — Avant de manipuler.** Si l'on tourne le lidar de 180° dans l'URDF, sans toucher
au capteur, que devient l'affichage du scan dans RViz ? Les données du message /scan
changent-elles ? Notez votre prédiction (un croquis suffit).

**Pistes à explorer** (5 min, avant de lire la suite)
- Repérez le joint de `base_scan` dans `burger.urdf.xacro` et son attribut `rpy`.
- Comparez `ros2 topic echo /scan --once` avant et après la modification.
- Dans RViz, affichez TF et regardez l'orientation du repère `base_scan`.

**Manipulation.** Mettez `rpy="0 0 3.14159"`, reconstruisez, relancez, observez. Remettez 0.

**Ce qu'il faut retenir.** Le message /scan est identique : les distances sont exprimées
dans `base_scan`. Seule la transformation `base_link → base_scan` a changé, et RViz place
donc les mêmes points ailleurs. Sur un vrai robot, un lidar monté à l'envers se corrige
dans l'URDF, pas dans le driver.
```

Règles que je m'impose :

- La question est **posée avant** et annonce ce que la manipulation va permettre de répondre. Elle demande une **prédiction** (dessin, phrase, valeur) que l'étudiant peut confronter au résultat.
- Les pistes sont des **actions d'observation** (une commande, un panneau RViz, un fichier à ouvrir), jamais la réponse déguisée. Deux ou trois pistes, pas plus.
- « Ce qu'il faut retenir » donne la solution en trois ou quatre lignes, **après** la manipulation. Les réponses détaillées (valeurs attendues, captures) vont dans la correction, sur la branche séparée.
- Une question par concept, environ **24 questions** sur le TP (contre 26 en v1 : j'ai fusionné celles qui se recouvraient).

## 3. Le monde fictif : l'atelier MecaTri

Je propose de réutiliser le cas client du cours (« cellule robotisée de tri », société fictive MecaTri) : le Burger devient le **robot de livraison de l'atelier**, qui amène les bacs A, B et Rejet depuis la cellule de tri vers trois postes. Le monde (image PGM 12 × 8 m, résolution 5 cm, jamais affichée aux étudiants) contient :

| Élément du monde | Ce qu'il sert à montrer | Partie |
|---|---|---|
| Cellule de tri (convoyeur + robot) au centre, trois postes dans trois coins | Les lieux nommés de la mission (`cellule`, `poste_A`, `poste_B`, `rejet`) | 6 |
| Un **passage étroit** de 0,70 m entre deux étagères (le Burger fait 0,178 m) | Inflation, rayon du robot, slide 76 du cours (« mini-cas : le passage étroit ») | 5 |
| Deux **alcôves identiques** symétriques | Ambiguïté de localisation, slide 50 du cours | 4 |
| Une zone « hors plan » : une table dont on ne voit que les pieds | Ce qu'un lidar 2D manque (slide 17) ; la carte montre 4 points, pas un rectangle | 3 |
| Un **obstacle amovible** (palette), ajouté par un service du simulateur | Couche obstacle vs couche statique, replanification, démo D4 du cours | 5 |

Le service `ajouter_obstacle` / `retirer_obstacle` du simulateur modifie la grille interne utilisée pour le raycast, sans relancer quoi que ce soit : c'est ce qui permet la démo « ajouter un obstacle puis annuler » du cours et l'exercice de la partie 5.

## 4. Déroulé horaire (v2)

| Heure | Partie | Durée | Point de contrôle |
|---|---|---|---|
| 0:00 | 0. Mise en route, rappel du schéma TF du cours, tableau « qui publie quoi » vide | 15 min | `pixi run nav-build` passe |
| 0:15 | 1. Le modèle du robot (URDF, robot_state_publisher, TF) | 45 min | Burger dans RViz, roues qui tournent |
| 1:00 | 2. Le lidar et son repère ; le simulateur ; l'odométrie dérive | 45 min | Scan affiché, `tf2_echo base_footprint base_scan` correct, dérive observée |
| 1:45 | Pause | 15 min | |
| 2:00 | 3. Cartographier en téléopérant, sauvegarder, retoucher | 40 min | `maps/atelier.pgm` fermé et propre |
| 2:40 | 4. Se localiser : map_server, AMCL, lifecycle, robot kidnappé, alcôves | 50 min | Nuage convergé, `map → odom` par AMCL |
| 3:30 | Pause déjeuner | 45 min | |
| 4:15 | 5. Naviguer : nav2.yaml, serveurs, costmaps, passage étroit, palette | 75 min | But atteint, palette contournée, passage étroit franchi ou refusé selon l'inflation |
| 5:30 | 6. Diagnostiquer une panne (3 pannes préparées, une variable modifiée chacune) | 35 min | Fiche « symptôme → hypothèse → commande → verdict » |
| 6:05 | 7. Mission autonome en Python (`nav2_simple_commander`) | 30 min | Tournée cellule → poste_A → poste_B |
| 6:35 | 8. Bilan : tableau TF corrigé, `view_frames` final, 5 min sur le BT | 15 min | |
| 6:50 | Fin (marge 10 min) | | |

Total activités : 5 h 50 ; avec pauses : 6 h 50. Si le chronométrage réel déborde, la partie 7 passe en « pour aller plus loin » (le TP reste complet sans elle). La partie 6 est nouvelle : elle répond directement à l'objectif 4 du module (« diagnostiquer une panne à partir de données observables ») et à la méthode « une seule variable modifiée » de la démo D5.

## 5. Contenu détaillé (questions avant manipulation)

### Partie 0 — Mise en route (15 min)

Rappels (préparer le terminal, `colcon build`), puis distribution du tableau à remplir au fil du TP :

| Transformation | Publiée par | Partie |
|---|---|---|
| `base_footprint → base_link`, roues, `base_scan` | ? | 1–2 |
| `odom → base_footprint` | ? | 2 |
| `map → odom` pendant la cartographie | ? | 3 |
| `map → odom` pendant la navigation | ? | 4 |

### Partie 1 — Le modèle du robot (45 min)

- **Q1** Un URDF suffit-il pour connaître l'angle actuel d'une roue ? (reprise de la slide 28). Pistes : `ros2 topic list` avec et sans `joint_state_publisher_gui` ; `ros2 node info /robot_state_publisher`. Manipulation : lancer `1_modele.launch.py`, bouger les curseurs.
- **Q2** Pourquoi deux repères `base_footprint` et `base_link` ? Pistes : `tf2_echo base_footprint base_link` ; regarder la hauteur de `base_link` ; penser au sol. Manipulation : compléter la roue droite, la roulette et les joints `continuous` dans `burger.urdf.xacro`.
- **Q3** Quelles transformations vont dans `/tf_static` plutôt que `/tf`, et pourquoi ? Pistes : `ros2 topic echo /tf_static --once`, `ros2 topic hz /tf`. Manipulation : `view_frames`, premier arbre TF du TP.
- **Q4** Si on inverse `parent` et `child` d'un joint, que voit-on ? Prédire, essayer, remettre.
- Point de contrôle : Burger complet dans RViz, comparaison avec le modèle officiel de `turtlebot3_description` (maillages 3D, même structure).

### Partie 2 — Le lidar, le simulateur, l'odométrie (45 min)

- **Q5** D'après le cours, combien de rayons et quelle portée a le LDS-01 ? Que signifie `inf` dans `ranges` ? Pistes : `ros2 interface show sensor_msgs/msg/LaserScan`, `ros2 topic echo /scan --once`. Manipulation : compléter le lien `base_scan` (position donnée), lancer `2_robot.launch.py`, pose initiale avec *2D Pose Estimate*.
- **Q6** Lidar tourné de 180° : voir le gabarit du §2.
- **Q7** Qui publie `odom → base_footprint` ? Avec `Fixed Frame = base_footprint`, qu'est-ce qui bouge dans RViz ? Pistes : `ros2 node info /tb3_loopback_sim`, changer le Fixed Frame (c'est la démo D2 du cours, refaite par l'étudiant). Manipulation : téléop au clavier.
- **Q8** Faites un carré de 2 m de côté à la téléop et revenez au départ : l'odométrie revient-elle à zéro ? (slide 40, « exercice mental » devenu réel). Pistes : `tf2_echo odom base_footprint` avant et après ; relancer avec `odom_drift_lin:=0.0`. Retenir : `odom` est continu mais dérive ; on ne navigue pas longtemps avec `odom` seul.
- Point de contrôle : `tf2_echo base_footprint base_scan` donne la translation attendue.

### Partie 3 — Cartographier (40 min)

- **Q9** Pourquoi ne suffit-il pas de coller tous les scans selon l'odométrie ? (slide 53). Pistes : relancer le SLAM avec une dérive forte (`odom_drift_ang:=0.3`) et regarder les murs se dédoubler ou non ; comparer `map → odom` à l'identité avec `tf2_echo map odom`. Manipulation : compléter `slam.yaml` (frames, topic, résolution, portée) et `3_slam.launch.py` ; cartographier lentement, fermer la boucle.
- **Q10** Dans l'image sauvegardée, que valent les pixels libre / occupé / inconnu, et que représente `origin` dans le YAML ? Pistes : ouvrir le `.yaml`, mesurer la taille de l'image, `ros2 topic echo /map --once` (champ `info`). Manipulation : `map_saver_cli`, ouvrir le PGM dans un éditeur, **retoucher** (effacer un artefact, dessiner un mur virtuel devant la table à pieds).
- Point de contrôle : `maps/atelier.pgm` fermé, table représentée par un rectangle dessiné à la main (ce que le lidar ne voit pas, slide 17).

### Partie 4 — Se localiser (50 min)

- **Q11** Peut-on lancer SLAM et AMCL en même temps ? (slide 22 et 59). Pistes : `view_frames` avec les deux lancés, regarder la ligne `map → odom`. Manipulation : arrêter le SLAM, compléter `amcl.yaml` et `4_localisation.launch.py` (map_server, amcl, lifecycle_manager).
- **Q12** Le nœud `amcl` apparaît dans `ros2 node list` : est-il prêt ? (slide 65). Pistes : `ros2 lifecycle get /amcl` avant et après avoir retiré `amcl` de `node_names`. Retenir : configure → activate, rôle du lifecycle manager.
- **Q13** Pourquoi faut-il bouger pour que le nuage de particules converge ? (slides 46–48). Pistes : donner la pose initiale puis ne rien faire 30 s ; téléopérer vers un angle de mur. Manipulation : observer `ParticleCloud`, essayer `max_particles: 50` puis `5000`.
- **Q14** Robot placé dans une des deux alcôves identiques, pose initiale inconnue : AMCL peut-il trancher ? (slide 50). Pistes : `ros2 service call /reinitialize_global_localization`, téléopérer **sans sortir** de l'alcôve, puis en sortir. Retenir : il faut une observation distinctive.
- **Q15** Robot kidnappé : on déplace le robot (service du simulateur) sans prévenir AMCL. Quelle information devient trompeuse, et comment s'en remettre ? (slide 52).
- Point de contrôle : `tf2_echo map base_footprint` suit le robot, tableau TF lignes 3 et 4 remplies.

### Partie 5 — Naviguer (75 min)

- **Q16** Le Burger fait 138 × 178 mm : quel `robot_radius` ? Quelle marge ? Et quelles vitesses maximales ? (slides 72, 74). Manipulation : compléter `nav2.yaml` (rayon, vitesses, frames, source d'observation `scan`, tolérances) et `5_navigation.launch.py` (les sept serveurs + lifecycle manager).
- **Q17** Pourquoi deux costmaps, et laquelle est « roulante » ? (slides 69–70). Pistes : afficher les deux dans RViz, envoyer un *Nav2 Goal*, regarder laquelle suit le robot ; `ros2 param get /local_costmap/local_costmap rolling_window`.
- **Q18** Passage étroit de 0,36 m : le robot passe-t-il avec `inflation_radius: 0.55` ? Avec `0.15` ? Qu'est-ce qui change entre un **coût** et une **cellule létale** ? (slides 73, 75, 76). Pistes : afficher la costmap globale et regarder la couleur du passage ; `ros2 param set` à chaud sur l'inflation puis renvoyer le même but.
- **Q19** `/plan` et `/local_plan` : lequel est recalculé le plus souvent, et pourquoi ? Pistes : `ros2 topic hz` sur les deux pendant un déplacement.
- **Q20** On pose une palette sur le chemin (service `ajouter_obstacle`) : quelle couche de costmap la voit ? Que se passe-t-il si on la retire ? (slides 70–71, marking / clearing). Manipulation : palette, observer la replanification, retirer, observer le clearing.
- **Q21** But dans un mur ou dans l'inconnu : que répond Nav2 ? Pistes : lire la sortie de `planner_server` et `bt_navigator`, `ros2 action list -t`. Puis `ros2 action send_goal /navigate_to_pose ... --feedback` et une annulation : le robot s'arrête-t-il vraiment ? (slide 37 et démo D4 : « observer l'arrêt effectif »).
- Point de contrôle : capture RViz avec les deux costmaps et un but atteint ; palette contournée.

### Partie 6 — Diagnostiquer une panne (35 min)

Trois pannes préparées, lancées par `ros2 launch tb3_livreur 5_navigation.launch.py panne:=N`. Une seule variable modifiée à chaque fois, l'étudiant ne sait pas laquelle. Il remplit une fiche : symptôme observé, hypothèse, commande d'observation, verdict, correction (c'est la méthode des slides 92–93).

| Panne | Variable modifiée | Symptôme | Commande qui tranche |
|---|---|---|---|
| 1 | `frame_id` du scan remappé vers `laser` (inexistant) | Scan absent dans RViz, costmap locale vide, AMCL muet | `ros2 topic echo /scan --once` (header), `view_frames` |
| 2 | `amcl` retiré de `node_names` du lifecycle manager | Pas de `map → odom`, RViz « Fixed Frame map does not exist » | `ros2 lifecycle get /amcl` |
| 3 | `cmd_vel` du velocity smoother remappé vers `cmd_vel_nav` (boucle fermée nulle part) | Plan calculé, le robot ne bouge pas | `ros2 topic info /cmd_vel -v` : pas de publisher |

Les trois reprennent les mini-cas de la slide 93. Une quatrième, plus subtile (QoS `reliable` sur un abonné `/scan` best effort), en bonus.

### Partie 7 — Mission autonome (30 min)

- **Q22** Entre un topic de coordonnées et l'action `NavigateToPose`, qu'est-ce que l'action apporte à une mission ? (slide 66, lien avec `RotateAbsolute` du TP 1). Pistes : `ros2 interface show nav2_msgs/action/NavigateToPose`.
- Manipulation : lire `mission.py` (`BasicNavigator`, `waitUntilNav2Active`, `goToPose`, feedback), compléter le dictionnaire des lieux (`cellule`, `poste_A`, `poste_B`, `rejet`) en relevant les coordonnées avec *Publish Point*, lancer la tournée.
- **Q23** Que renvoie `getResult()` si la palette bloque le seul accès à `poste_B` ? Pistes : relire le BT simplifié (slide 68) ; ajouter la palette pendant la tournée.
- Bonus : abonner `mission.py` à `/destination` (String) pour retrouver l'interface de la tortue livreuse.

### Partie 8 — Bilan (15 min)

Tableau TF corrigé, `view_frames` final contre celui de la partie 1, **Q24** (vérification collective de la slide 95, en 30 s chacune), 5 min sur le XML du BT.

## 6. Démos de cours dans `demo_ws` : `pixi run cours demo:=XXX`

`demo_ws` contient déjà des démos D6, D7, D8 et D11 d'un module précédent. Les démonstrations du support Nav2 (FormationEIGSI_NAV2Opensource.pdf) sont numérotées **4.1 à 4.11**, dans l'ordre des sections du cours : `pixi run cours demo:=4.5`. Un seul launch `cours.launch.py` dans `cours_ros2_demo` prend l'argument `demo` et inclut le bon scénario. Les scénarios Nav2 réutilisent le simulateur et les packages de `nav_ws` (la tâche `cours` charge les deux overlays).

| Démo | Slide (support Nav2) | Ce qui est lancé | Ce qu'on montre, en une commande à la fois |
|---|---|---|---|
| 4.1 | 11 | Robot simulé, sans RViz | `ros2 node list`, `ros2 topic info /scan -v`, `ros2 action list -t` (vide avant Nav2), `view_frames` |
| 4.2 | 17–21 | Robot + RViz | `ros2 topic type /cmd_vel` ; une seule publication de `linear.x = 0.1` avance 0,5 s puis s'arrête (durée de validité) ; `angular.z` positif tourne à gauche ; arbitrage avec la téléop |
| 4.3 | 23 | Robot + RViz, vérité terrain affichée | Le carré de 2 m au pilote automatique : `odom` ne revient pas à zéro ; `derive:=false` pour comparer |
| 4.4 | 27–28 | Robot + RViz | Le contrat `LaserScan`, `tf2_echo base_link base_scan`, la table dont on ne voit que les pieds |
| 4.5 | 35 | Robot + RViz | Changer le Fixed Frame, `tf2_echo odom base_footprint`, `view_frames` (qui publie quoi, slide 33) ; variante `4.5b` lidar tourné de 180° : « le mur tourne avec le robot » |
| 4.6 | 36–39 | `robot_state_publisher` + curseurs, sans simulateur | URDF → `/joint_states` → `/tf` et `/tf_static` ; sortie de `xacro` |
| 4.7 | 65 (et 40, 52–56) | map_server + AMCL + RViz | Pose initiale légèrement fausse, convergence, `tf2_echo map odom`, localisation globale, robot kidnappé dans une alcôve, `ros2 lifecycle get /amcl` |
| 4.8 | 61 | SLAM + RViz | Carte qui se construit au pilote automatique, fermeture de boucle, sauvegarde |
| 4.9 | 75–82, 84, 91 | Nav2 complet + RViz | Couches, inflation 0,15 vs 1,0 à chaud, `robot_radius` 0,45 ferme le couloir, fréquences de `/plan` et `/local_plan` |
| 4.10 | 101 (et 70, 95) | Nav2 complet + RViz, palette au clic | But, chemin, `/cmd_vel`, palette ajoutée par service, tolérances d'arrivée, annulation et arrêt effectif |
| 4.11 | 99–100 | Nav2 avec `panne:=N` | Une variable modifiée, diagnostic par couches devant les étudiants |

Deux détails d'implémentation : la démo utilise le **Waffle** (voir question 2 ci-dessous), et chaque scénario affiche dans le terminal les deux ou trois commandes à taper pendant la démo, pour ne pas avoir à les chercher.

## 7. Arborescence (v2)

```
nav_ws/
├── TP_turtlebot_navigation.md, TP_turtlebot_navigation.pdf, images/
└── src/
    ├── tb3_loopback_sim/            # fourni, lu mais pas modifié
    │   ├── tb3_loopback_sim/simulateur.py, utils.py, line_iterator.py
    │   ├── launch/simulateur.launch.py
    │   ├── mondes/atelier_mecatri.pgm/.yaml      # monde caché
    │   └── srv/ (ou std_srvs) ajouter_obstacle, retirer_obstacle, teleporter
    └── tb3_livreur/                 # package des étudiants
        ├── urdf/burger.urdf.xacro                   # trous parties 1–2
        ├── launch/1_modele, 2_robot (sim:=true|false), 3_slam, 4_localisation, 5_navigation (panne:=0..4)
        ├── config/slam.yaml, amcl.yaml, nav2.yaml   # trous parties 3–5
        ├── config/pannes/panne_1.yaml …             # surcharges de paramètres
        ├── maps/                                    # carte de l'étudiant
        ├── rviz/modele.rviz, slam.rviz, navigation.rviz
        └── tb3_livreur/mission.py
demo_ws/src/cours_ros2_demo/
        ├── launch/cours.launch.py + scenarios/4_1.launch.py … 4_10.launch.py
        └── config/waffle_nav2.yaml, waffle_amcl.yaml, waffle_slam.yaml, waffle.urdf.xacro
```

`pixi.toml` : `nav-build`, `nav`, `nav-pdf`, `cours` (= build des deux workspaces puis `python outils/cours.py` qui charge les overlays et lance `ros2 launch cours_ros2_demo cours.launch.py demo:=…`).

## 8. Plan de travail après tes réponses

1. `pixi.toml` (dépendances validées, tâches) et `tb3_loopback_sim` (simulateur, monde MecaTri, services).
2. Chaîne complète **sans trous** (Burger) testée de bout en bout : c'est la correction.
3. Démos `demo_ws` 4.1 → 4.10 (Waffle).
4. Trous, pannes, énoncé au format question → pistes → manipulation → retenir, captures, PDF.
5. Branche `nav2-correction` : fichiers complétés, réponses aux 24 questions, fiches pannes.
6. Chronométrage réel sur ta machine.
