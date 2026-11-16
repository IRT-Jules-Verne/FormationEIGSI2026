"""Dessine le monde « atelier MecaTri » et l'enregistre en PGM + YAML.

Usage (environnement pixi actif) :
    ros2 run tb3_loopback_sim generer_monde [dossier_de_sortie]

Le monde fait 12 m x 8 m, résolution 5 cm. Le dessin se fait en mètres depuis le coin
bas-gauche ; le repère map a son origine 1 m plus loin dans chaque direction (ORIGINE),
de sorte que le robot démarre en (0, 0) : la carte construite par SLAM depuis ce point a
le même repère que le monde. Tout est dessiné avec des fonctions simples (rectangle,
disque, mur) pour que le fichier reste lisible et modifiable.

Contenu (voir lieux.yaml pour les coordonnées utiles au TP) :
  - murs extérieurs, un pilier, une armoire électrique ;
  - la cellule de tri MecaTri (convoyeur, robot, bacs A/B/rejet) au centre ;
  - des machines (presse, fraiseuse, cuve) et des caisses ;
  - deux étagères qui forment un passage étroit de 0,70 m vers poste_B ;
  - deux alcôves identiques (ambiguïté de localisation) ;
  - une table dont le lidar ne voit que les quatre pieds ;
  - trois postes de livraison, matérialisés uniquement dans lieux.yaml.
"""

import os
import sys

import numpy as np

LARGEUR_M = 12.0
HAUTEUR_M = 8.0
RESOLUTION = 0.05
DEPART = (1.0, 1.0)      # position de depart du robot, dans les coordonnees du dessin
ORIGINE = (-1.0, -1.0)   # origine du repere map : le robot demarre donc en (0, 0)

# Lieux nommés (x, y, yaw) dans le repère map : utilisés par mission.py et par l'énoncé.
LIEUX = {
    'depart':   (0.0, 0.0, 0.0),
    'cellule':  (5.0, 1.2, 1.5708),    # devant le convoyeur, face à la cellule
    'poste_A':  (0.2, 6.0, 3.1416),    # coin haut-gauche
    'poste_B':  (10.2, 5.3, -1.5708),  # zone haut-droite, derrière le passage étroit
    'rejet':    (9.8, 0.8, -1.5708),   # coin bas-droit
    'alcove_1': (2.0, 6.2, 1.5708),
    'alcove_2': (5.0, 6.2, 1.5708),
}


class Dessin:

    def __init__(self):
        self.l = int(round(LARGEUR_M / RESOLUTION))
        self.h = int(round(HAUTEUR_M / RESOLUTION))
        # 254 = libre, 0 = occupé, 205 = inconnu (conventions de map_saver).
        self.img = np.full((self.h, self.l), 254, dtype=np.uint8)

    def _ij(self, x, y):
        # coordonnées du dessin (coin bas-gauche = 0, 0)
        return int(round(x / RESOLUTION)), int(round(y / RESOLUTION))

    def rectangle(self, x0, y0, x1, y1, valeur=0):
        i0, j0 = self._ij(min(x0, x1), min(y0, y1))
        i1, j1 = self._ij(max(x0, x1), max(y0, y1))
        i0, i1 = max(i0, 0), min(i1, self.l)
        j0, j1 = max(j0, 0), min(j1, self.h)
        self.img[j0:j1, i0:i1] = valeur

    def disque(self, cx, cy, r, valeur=0):
        ys, xs = np.mgrid[0:self.h, 0:self.l]
        xs = xs * RESOLUTION + RESOLUTION / 2
        ys = ys * RESOLUTION + RESOLUTION / 2
        self.img[(xs - cx) ** 2 + (ys - cy) ** 2 <= r * r] = valeur

    def mur(self, x0, y0, x1, y1, epaisseur=0.10):
        """Segment de mur horizontal ou vertical."""
        e = epaisseur / 2
        if abs(x1 - x0) < 1e-9:
            self.rectangle(x0 - e, y0, x0 + e, y1)
        else:
            self.rectangle(x0, y0 - e, x1, y0 + e)

    def enregistrer(self, dossier, nom):
        os.makedirs(dossier, exist_ok=True)
        pgm = os.path.join(dossier, nom + '.pgm')
        donnees = np.flipud(self.img)  # ligne 0 du fichier = haut de l'image = y maximal
        with open(pgm, 'wb') as f:
            f.write(f'P5\n# Monde {nom} genere par tb3_loopback_sim\n{self.l} {self.h}\n255\n'
                    .encode())
            f.write(donnees.tobytes())
        with open(os.path.join(dossier, nom + '.yaml'), 'w', encoding='utf-8') as f:
            f.write(f'image: {nom}.pgm\n')
            f.write(f'resolution: {RESOLUTION}\n')
            f.write(f'origin: [{ORIGINE[0]}, {ORIGINE[1]}, 0.0]\n')
            f.write('negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.25\n')
        with open(os.path.join(dossier, 'lieux.yaml'), 'w', encoding='utf-8') as f:
            f.write('# Lieux nommes de l atelier MecaTri (repere map : x, y en m, yaw en rad)\n')
            for nom_lieu, (x, y, yaw) in LIEUX.items():
                f.write(f'{nom_lieu}: [{x}, {y}, {yaw}]\n')
        return pgm


def dessiner_atelier():
    d = Dessin()
    # Murs extérieurs
    d.rectangle(0.0, 0.0, LARGEUR_M, 0.15)
    d.rectangle(0.0, HAUTEUR_M - 0.15, LARGEUR_M, HAUTEUR_M)
    d.rectangle(0.0, 0.0, 0.15, HAUTEUR_M)
    d.rectangle(LARGEUR_M - 0.15, 0.0, LARGEUR_M, HAUTEUR_M)

    # Cellule de tri MecaTri (au centre)
    d.rectangle(4.0, 3.0, 8.0, 3.5)      # convoyeur, 4 m de long
    d.rectangle(5.6, 3.5, 6.4, 4.3)      # socle du robot de tri, derrière le convoyeur
    d.rectangle(4.2, 3.6, 4.8, 4.2)      # bac A
    d.rectangle(7.2, 3.6, 7.8, 4.2)      # bac B
    d.rectangle(6.0, 4.5, 6.6, 5.1)      # bac rejet
    d.rectangle(4.0, 4.4, 4.1, 5.4)      # grillage de protection gauche
    d.rectangle(7.9, 4.4, 8.0, 5.4)      # grillage de protection droit

    # Machines
    d.rectangle(2.3, 0.15, 3.6, 0.9)     # presse
    d.rectangle(8.2, 0.15, 9.2, 1.3)     # fraiseuse
    d.disque(9.9, 0.9, 0.25)             # cuve ronde
    d.rectangle(0.15, 3.6, 0.75, 4.8)    # armoire électrique
    d.disque(3.0, 4.6, 0.18)             # pilier rond

    # Table : seuls les pieds (5 cm) sont dans le plan du lidar
    for px in (1.6, 2.6):
        for py in (2.4, 3.2):
            d.rectangle(px - 0.025, py - 0.025, px + 0.025, py + 0.025)

    # Caisses
    d.rectangle(10.3, 2.8, 11.0, 3.5)
    d.rectangle(10.9, 3.5, 11.5, 4.0)

    # Passage étroit vers poste_B : deux étagères séparées de 0,70 m. Le robot fait 0,24 m, mais
    # dans la carte SLAM les murs s'épaississent d'une cellule de chaque côté et le scan en direct,
    # décalé par l'erreur de localisation, rétrécit encore le passage dans la costmap.
    d.rectangle(8.3, 5.4, 9.42, 7.85)    # étagère gauche, jusqu'au mur du haut
    d.rectangle(10.12, 5.4, 10.7, 7.1)   # étagère droite -> couloir x dans [9.42, 10.12]
    d.rectangle(10.7, 5.4, 11.85, 5.5)   # cloison qui ferme le contournement par la droite
    # Le couloir débouche au-dessus de l'étagère droite (y > 7.1) sur la zone de poste_B,
    # qui n'est donc accessible que par ce passage de 0,70 m.

    # Deux alcôves identiques sur le mur du haut (ouvertes vers le bas), à x = 3 et x = 6
    for cx in (3.0, 6.0):
        d.mur(cx - 0.6, 6.5, cx - 0.6, 7.85, 0.10)
        d.mur(cx + 0.6, 6.5, cx + 0.6, 7.85, 0.10)
    return d


def main(args=None):
    argv = sys.argv[1:] if args is None else args
    dossier = argv[0] if argv else os.path.join(os.getcwd(), 'mondes')
    d = dessiner_atelier()
    pgm = d.enregistrer(dossier, 'atelier_mecatri')
    print(f'Monde ecrit : {pgm} ({d.l} x {d.h} cellules, {RESOLUTION} m/cellule)')


if __name__ == '__main__':
    main()
