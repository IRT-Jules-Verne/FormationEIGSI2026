"""Le « monde » du simulateur : une grille d'occupation chargée depuis un couple PGM + YAML.

C'est la salle réelle, telle que le lidar simulé la voit. Elle n'est jamais publiée aux
étudiants (sauf en démo) : ils doivent la découvrir en cartographiant.

Format : le même que celui de nav2_map_server (image PGM en niveaux de gris, YAML avec
resolution, origin, occupied_thresh, free_thresh, negate). On peut donc aussi charger une
carte produite par map_saver_cli pour en faire un monde.
"""

import math
import os

import numpy as np
import yaml


class Monde:
    """Grille d'occupation + obstacles amovibles + lancer de rayons vectorisé."""

    OCCUPE = 100
    LIBRE = 0
    INCONNU = -1

    def __init__(self, fichier_yaml):
        with open(fichier_yaml, encoding='utf-8') as f:
            meta = yaml.safe_load(f)
        self.resolution = float(meta['resolution'])
        self.origine_x = float(meta['origin'][0])
        self.origine_y = float(meta['origin'][1])
        seuil_occupe = float(meta.get('occupied_thresh', 0.65))
        seuil_libre = float(meta.get('free_thresh', 0.25))
        negate = int(meta.get('negate', 0))

        image = meta['image']
        if not os.path.isabs(image):
            image = os.path.join(os.path.dirname(fichier_yaml), image)
        pixels = lire_pgm(image)  # (hauteur, largeur), uint8, ligne 0 = haut de l'image

        # Convention map_server : la ligne 0 de l'image est le HAUT, donc la plus grande y.
        # On retourne l'image pour que grille[0] soit la ligne y = origine_y.
        pixels = np.flipud(pixels).astype(np.float32)
        occupation = pixels / 255.0 if negate else (255.0 - pixels) / 255.0

        self.hauteur, self.largeur = occupation.shape
        self.grille_base = np.full((self.hauteur, self.largeur), self.INCONNU, dtype=np.int8)
        self.grille_base[occupation >= seuil_occupe] = self.OCCUPE
        self.grille_base[occupation <= seuil_libre] = self.LIBRE

        self.obstacles = {}  # nom -> (x, y, yaw, taille)
        self.grille = self.grille_base.copy()

    # ----- conversions -----

    def monde_vers_grille(self, x, y):
        return (int(math.floor((x - self.origine_x) / self.resolution)),
                int(math.floor((y - self.origine_y) / self.resolution)))

    def dans_grille(self, ix, iy):
        return 0 <= ix < self.largeur and 0 <= iy < self.hauteur

    def occupe(self, x, y):
        """Vrai si la cellule contenant (x, y) est occupée (ou hors du monde)."""
        ix, iy = self.monde_vers_grille(x, y)
        if not self.dans_grille(ix, iy):
            return True
        return self.grille[iy, ix] == self.OCCUPE

    def disque_libre(self, x, y, rayon):
        """Vrai si aucune cellule occupée ne touche le disque de centre (x, y)."""
        if self.occupe(x, y):
            return False
        for k in range(12):
            a = 2.0 * math.pi * k / 12
            if self.occupe(x + rayon * math.cos(a), y + rayon * math.sin(a)):
                return False
        return True

    # ----- obstacles amovibles -----

    def ajouter_obstacle(self, nom, x, y, yaw=0.0, taille=0.4):
        self.obstacles[nom] = (float(x), float(y), float(yaw), float(taille))
        self._recalculer()

    def retirer_obstacle(self, nom):
        if nom not in self.obstacles:
            return False
        del self.obstacles[nom]
        self._recalculer()
        return True

    def _recalculer(self):
        self.grille = self.grille_base.copy()
        for (x, y, yaw, taille) in self.obstacles.values():
            demi = taille / 2.0
            c, s = math.cos(yaw), math.sin(yaw)
            # On échantillonne le carré avec un pas d'une demi-cellule.
            pas = self.resolution / 2.0
            n = max(1, int(taille / pas) + 1)
            for i in range(n):
                for j in range(n):
                    u = -demi + i * pas
                    v = -demi + j * pas
                    px = x + c * u - s * v
                    py = y + s * u + c * v
                    ix, iy = self.monde_vers_grille(px, py)
                    if self.dans_grille(ix, iy):
                        self.grille[iy, ix] = self.OCCUPE

    # ----- lidar -----

    def lancer_rayons(self, x, y, yaw, angles, portee_min, portee_max):
        """Distance au premier obstacle pour chaque angle (relatif à yaw).

        Retourne un tableau float32 avec inf quand rien n'est touché avant portee_max.
        Vectorisé avec numpy : 360 rayons x 140 pas restent très rapides.
        """
        pas = self.resolution / 2.0
        distances = np.arange(pas, portee_max + pas, pas, dtype=np.float32)  # (M,)
        directions = yaw + angles  # (N,)
        xs = x + distances[None, :] * np.cos(directions)[:, None]
        ys = y + distances[None, :] * np.sin(directions)[:, None]
        ix = np.floor((xs - self.origine_x) / self.resolution).astype(np.int32)
        iy = np.floor((ys - self.origine_y) / self.resolution).astype(np.int32)
        dedans = (ix >= 0) & (ix < self.largeur) & (iy >= 0) & (iy < self.hauteur)
        touche = np.zeros(ix.shape, dtype=bool)
        touche[dedans] = self.grille[iy[dedans], ix[dedans]] == self.OCCUPE
        # Un rayon qui sort du monde est considéré comme touchant le bord (mur extérieur).
        touche |= ~dedans
        existe = touche.any(axis=1)
        premier = touche.argmax(axis=1)
        resultat = np.where(existe, distances[premier], np.inf).astype(np.float32)
        resultat[resultat < portee_min] = np.inf
        return resultat


def lire_pgm(chemin):
    """Lit un PGM binaire (P5) ou ASCII (P2) sans dépendre de PIL."""
    with open(chemin, 'rb') as f:
        donnees = f.read()
    # En-tête : P5/P2, largeur, hauteur, valeur max, avec commentaires possibles (#...).
    jetons = []
    i = 0
    while len(jetons) < 4:
        while i < len(donnees) and donnees[i:i + 1].isspace():
            i += 1
        if donnees[i:i + 1] == b'#':
            while donnees[i:i + 1] not in (b'\n', b''):
                i += 1
            continue
        debut = i
        while i < len(donnees) and not donnees[i:i + 1].isspace():
            i += 1
        jetons.append(donnees[debut:i])
    magique, largeur, hauteur, maxval = jetons[0], int(jetons[1]), int(jetons[2]), int(jetons[3])
    i += 1  # un seul blanc après maxval
    if magique == b'P5':
        tableau = np.frombuffer(donnees[i:i + largeur * hauteur], dtype=np.uint8)
    elif magique == b'P2':
        tableau = np.array(donnees[i:].split(), dtype=np.int32).astype(np.uint8)
    else:
        raise ValueError(f'{chemin} : format PGM non reconnu ({magique!r})')
    if maxval != 255:
        tableau = (tableau.astype(np.float32) * 255.0 / maxval).astype(np.uint8)
    return tableau.reshape((hauteur, largeur))
