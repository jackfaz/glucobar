"""Converte assets/previews/*.png in BMP per l'installer (Inno Setup legge solo BMP).

Uso: python tools/previews_to_bmp.py   ->   installer/build/previews/*.bmp
"""

import glob
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "previews")
DST = os.path.join(ROOT, "installer", "build", "previews")

os.makedirs(DST, exist_ok=True)
files = sorted(glob.glob(os.path.join(SRC, "*.png")))
for path in files:
    name = os.path.splitext(os.path.basename(path))[0] + ".bmp"
    Image.open(path).convert("RGB").save(os.path.join(DST, name))
print(f"{len(files)} anteprime convertite in {DST}")
