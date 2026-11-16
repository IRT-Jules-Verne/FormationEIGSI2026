"""Plan annoté de l'atelier MecaTri, dessiné sur la carte SLAM fournie (maps/atelier).

Usage : pixi run --frozen python outils/plan_atelier.py nav_ws/src/tb3_livreur/maps/atelier.yaml nav_ws/images/plan_atelier.png
Les coordonnées des éléments viennent de tb3_loopback_sim/generer_monde.py (décalées de -1 m : repère map).
"""
import sys
import math
import numpy as np
import yaml
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrow

carte_yaml, sortie = sys.argv[1], sys.argv[2]
info = yaml.safe_load(open(carte_yaml, encoding='utf-8'))
img = np.array(Image.open(carte_yaml.replace('.yaml', '.pgm')))
res = info['resolution']
ox, oy = info['origin'][:2]
h, w = img.shape
ext = [ox, ox + w * res, oy, oy + h * res]

fig, ax = plt.subplots(figsize=(13, 9.5), dpi=120)
ax.imshow(img, cmap='gray', vmin=0, vmax=255, extent=ext, origin='upper')

# Éléments de l'atelier, coordonnées dans le repère map (m) : (x0, y0, x1, y1)
BLEU, ORANGE, VERT, VIOLET = '#1f6fb5', '#d9730d', '#2e8b57', '#7b3fa0'


def zone(x0, y0, x1, y1, nom, couleur=BLEU, dx=0, dy=0, ha='center', taille=10):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=True, alpha=0.18,
                           ec=couleur, fc=couleur, lw=1.5))
    ax.text((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, nom, ha=ha, va='center',
            fontsize=taille, color=couleur, weight='bold')


zone(3.0, 2.0, 7.0, 4.4, 'Cellule de tri\n(convoyeur, robot, bacs)', ORANGE, dy=1.65)
zone(1.3, -0.85, 2.6, -0.1, 'Presse', dy=0.6)
zone(7.2, -0.85, 8.2, 0.3, 'Fraiseuse', dy=0.85)
ax.add_patch(Circle((8.9, -0.1), 0.25, fc=BLEU, ec=BLEU, alpha=0.18, lw=1.5))
ax.text(8.9, 0.35, 'Cuve', ha='center', fontsize=10, color=BLEU, weight='bold')
zone(-0.85, 2.6, -0.25, 3.8, 'Armoire\nélectrique', dx=0.75, ha='left')
ax.add_patch(Circle((2.0, 3.6), 0.18, fc=BLEU, ec=BLEU, alpha=0.18, lw=1.5))
ax.text(2.3, 3.6, 'Pilier', va='center', fontsize=10, color=BLEU, weight='bold')
zone(0.55, 1.35, 1.65, 2.25, 'Table\n(4 pieds)')
zone(9.3, 1.8, 10.5, 3.0, 'Caisses', dy=0.85)
zone(7.3, 4.4, 8.42, 6.85, 'Étagère', VIOLET)
zone(9.12, 4.4, 9.7, 6.1, 'Éta-\ngère', VIOLET)
ax.annotate('Couloir étroit\n(0,70 m)', xy=(8.77, 5.0), xytext=(8.77, 3.75), ha='center',
            fontsize=10, color=VIOLET, weight='bold',
            arrowprops=dict(arrowstyle='->', color=VIOLET, lw=1.5))
for cx, nom in ((2.0, 'Alcôve 1'), (5.0, 'Alcôve 2')):
    zone(cx - 0.6, 5.5, cx + 0.6, 6.85, nom, VIOLET, taille=9)

# Lieux de livraison (positions approximatives, à relever précisément dans RViz)
for x, y, nom, dx, dy in ((5.0, 1.2, 'cellule', 0.25, -0.35), (0.2, 6.0, 'poste_A', 0.3, -0.4),
                          (10.2, 5.3, 'poste_B', 0.05, 0.55), (9.8, 0.8, 'rejet', -0.3, 0.2)):
    ax.add_patch(Circle((x, y), 0.17, fc=VERT, ec='white', lw=1.5, zorder=5))
    ax.text(x + dx, y + dy, nom, fontsize=12, color=VERT, weight='bold', zorder=6,
            ha='left' if dx > 0 else 'right',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=VERT, alpha=0.9))

# Départ du robot : (0, 0), orienté vers +x
ax.add_patch(FancyArrow(0, 0, 0.55, 0, width=0.06, head_width=0.22, head_length=0.18,
                        fc='#c0392b', ec='#c0392b', zorder=6))
ax.add_patch(Circle((0, 0), 0.12, fc='#c0392b', ec='white', lw=1.5, zorder=7))
ax.text(0.15, 0.35, 'Départ (0, 0)', fontsize=11, color='#c0392b', weight='bold')

ax.set_xticks(range(math.ceil(ext[0]), math.floor(ext[1]) + 1))
ax.set_yticks(range(math.ceil(ext[2]), math.floor(ext[3]) + 1))
ax.grid(color='#888', lw=0.5, alpha=0.5)
ax.set_xlabel('x (m), repère map')
ax.set_ylabel('y (m), repère map')
ax.set_xlim(ext[0], ext[1])
ax.set_ylim(ext[2], ext[3])
ax.set_title("Atelier MecaTri : plan de la carte fournie (maps/atelier)", fontsize=13)
fig.tight_layout()
fig.savefig(sortie)
print('ok', sortie, img.shape, ext)
