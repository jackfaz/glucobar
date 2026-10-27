"""Prepara le anteprime per l'installer (Inno Setup legge solo BMP).

Uso: python tools/previews_to_bmp.py
  assets/previews/*.png         ->  installer/build/previews/*.bmp
  assets/previews/layout.json   ->  installer/build/preview_layout.iss  (#define con le
                                    posizioni dei ritagli sopra la base)
"""

import glob
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "previews")
BUILD = os.path.join(ROOT, "installer", "build")
DST = os.path.join(BUILD, "previews")

os.makedirs(DST, exist_ok=True)
files = sorted(glob.glob(os.path.join(SRC, "*.png")))
for path in files:
    name = os.path.splitext(os.path.basename(path))[0] + ".bmp"
    Image.open(path).convert("RGB").save(os.path.join(DST, name))

with open(os.path.join(SRC, "layout.json"), encoding="utf-8") as f:
    layout = json.load(f)
lines = ["; Generato da tools/previews_to_bmp.py: non modificare a mano",
         f'#define PreviewW {layout["width"]}',
         f'#define PreviewH {layout["height"]}']
for element, r in layout["layers"].items():
    for key in ("x", "y", "w", "h"):
        lines.append(f"#define Layer_{element}_{key} {r[key]}")
with open(os.path.join(BUILD, "preview_layout.iss"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"{len(files)} anteprime convertite in {DST}; posizioni in preview_layout.iss")
