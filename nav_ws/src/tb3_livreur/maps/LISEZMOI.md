Dossier des cartes.

- `atelier.pgm` / `atelier.yaml` : la carte que vous produisez en partie 3 avec
  `ros2 run nav2_map_server map_saver_cli -f maps/atelier` (depuis `nav_ws/src/tb3_livreur`).
  Reconstruisez ensuite le workspace (`colcon build`) pour que les launch files la trouvent.
- `atelier_secours.pgm` / `atelier_secours.yaml` : carte de secours, à utiliser avec
  `carte:=.../maps/atelier_secours.yaml` si la vôtre n'est pas exploitable.
