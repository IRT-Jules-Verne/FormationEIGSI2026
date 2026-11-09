"""Convertit un enonce Markdown (avec images et schemas Mermaid) en PDF.

Principe : Markdown -> HTML (python-markdown) -> PDF (Edge ou Chrome en mode headless).
Les images sont cherchees relativement au fichier Markdown.
Le rendu Mermaid utilise mermaid.js depuis un CDN : il faut une connexion Internet.

Usage (depuis la racine du depot) :
    pixi run tp-pdf
ou directement :
    pixi exec -s python=3.12 -s markdown python outils/md_vers_pdf.py tp_ws/TP_tortue_livreuse.md
"""

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

NAVIGATEURS = [
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
]

CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 22pt; border-bottom: 3px solid #2b6cb0; padding-bottom: 4px; }
h2 { font-size: 15pt; color: #2b6cb0; border-bottom: 1px solid #cbd5e0; padding-bottom: 2px; margin-top: 1.4em; }
h2.partie { break-before: page; }
h3 { font-size: 12pt; margin-top: 1.2em; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 9.5pt; background: #edf2f7; padding: 1px 3px; border-radius: 3px; }
pre { background: #f4f6f8; border: 1px solid #d9dee4; border-radius: 4px; padding: 8px 10px; white-space: pre-wrap; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 0.8em 0; break-inside: avoid; }
th, td { border: 1px solid #cbd5e0; padding: 4px 8px; vertical-align: top; }
th { background: #edf2f7; }
img { max-width: 100%; max-height: 10.5cm; display: block; margin: 0.6em auto; border: 1px solid #d9dee4; break-inside: avoid; }
td img { max-height: 7cm; }
blockquote { border-left: 4px solid #2b6cb0; background: #ebf4ff; margin: 0.8em 0; padding: 4px 12px; }
pre.mermaid { background: none; border: none; text-align: center; }
"""


def convertir(chemin_md: Path) -> Path:
    texte = chemin_md.read_text(encoding='utf-8')

    # Les blocs ```mermaid deviennent des <pre class="mermaid"> que mermaid.js dessinera
    def bloc_mermaid(m):
        return f'\n<pre class="mermaid">\n{html.escape(m.group(1))}</pre>\n'
    texte = re.sub(r'^```mermaid\n(.*?)^```', bloc_mermaid, texte, flags=re.S | re.M)

    corps = markdown.markdown(texte, extensions=['tables', 'fenced_code', 'sane_lists'])
    # Chaque "Partie" commence sur une nouvelle page
    corps = corps.replace('<h2>Partie', '<h2 class="partie">Partie')
    corps = corps.replace('<h2>Pour aller plus loin', '<h2 class="partie">Pour aller plus loin')

    titre = re.search(r'^# (.+)$', texte, flags=re.M)
    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<title>{html.escape(titre.group(1) if titre else chemin_md.stem)}</title>
<style>{CSS}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});</script>
</head><body>
{corps}
</body></html>"""

    # Le HTML temporaire est cree a cote du .md pour que les chemins des images restent valides
    chemin_md = chemin_md.resolve()
    chemin_html = chemin_md.with_suffix('.tmp.html')
    chemin_pdf = chemin_md.with_suffix('.pdf')
    chemin_html.write_text(page, encoding='utf-8')

    navigateur = next((n for n in NAVIGATEURS if os.path.exists(n)), None)
    if navigateur is None:
        sys.exit('Edge ou Chrome introuvable')
    # Profil separe : sinon un Edge deja ouvert recupere la commande et rien n'est imprime
    profil = Path(tempfile.mkdtemp(prefix='md_vers_pdf_'))
    try:
        subprocess.run([
            navigateur, '--headless', '--disable-gpu', '--no-pdf-header-footer',
            f'--user-data-dir={profil}',
            '--virtual-time-budget=15000',
            f'--print-to-pdf={chemin_pdf}',
            chemin_html.resolve().as_uri(),
        ], check=True, capture_output=True, timeout=120)
    finally:
        chemin_html.unlink(missing_ok=True)
        shutil.rmtree(profil, ignore_errors=True)
    if not chemin_pdf.exists():
        sys.exit('Echec : le navigateur n\'a pas produit de PDF')
    return chemin_pdf


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pdf = convertir(Path(sys.argv[1]))
    print(f'PDF genere : {pdf}')
