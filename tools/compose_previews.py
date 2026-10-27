"""Crea le anteprime delle modalità per l'installer e il README.

Uso (su Linux con Xvfb, dopo aver fotografato le viste con dati di prova):
    python tools/compose_previews.py CARTELLA_FOTO

CARTELLA_FOTO contiene {lingua}_{taskbar|window|desktop}.png. Produce:
    assets/previews/{lingua}_{modalità}.png   320x200, per l'installer
    docs/preview_{modalità}.png               640x400, in inglese, per il README
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from glucobar.i18n import LANGUAGES, STRINGS  # noqa: E402
from glucobar.tray import make_icon  # noqa: E402

W, H = 640, 400          # una porzione dello schermo, a grandezza reale
BAR_H = 48
TRAY_X = 470             # inizio dell'area icone/orologio
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GREEN = "#3ecf6e"


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def desktop():
    """Sfondo con gradiente e barra delle applicazioni in stile Windows 11."""
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(58 - 30 * k), int(110 - 70 * k), int(165 - 90 * k)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((300, 40, 760, 420), fill=(120, 170, 230, 70))
    g.ellipse((-120, 180, 260, 520), fill=(90, 60, 160, 60))
    img.paste(glow.filter(ImageFilter.GaussianBlur(40)), (0, 0), glow.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(img)
    top = H - BAR_H
    d.rectangle((0, top, W, H), fill="#1c1c1c")
    d.line((0, top, W, top), fill="#2e2e2e")
    # app al centro
    for i, col in enumerate(("#3b82f6", "#f59e0b", "#10b981", "#8b5cf6", "#ef4444")):
        x = 150 + i * 40
        d.rounded_rectangle((x, top + 10, x + 28, top + 38), radius=6, fill=col)
    # area di notifica: freccetta, wifi, volume, orologio
    d.text((TRAY_X + 40, top + 14), "^", font=font(16), fill="#d0d0d0")
    d.arc((TRAY_X + 62, top + 16, TRAY_X + 80, top + 34), 220, 320, fill="#d0d0d0", width=2)
    d.polygon([(TRAY_X + 88, top + 20), (TRAY_X + 94, top + 20), (TRAY_X + 100, top + 15),
               (TRAY_X + 100, top + 33), (TRAY_X + 94, top + 28), (TRAY_X + 88, top + 28)],
              fill="#d0d0d0")
    d.text((W - 16, top + 5), "19:17", font=font(12), fill="white", anchor="ra")
    d.text((W - 16, top + 27), "27/10/2026", font=font(12), fill="white", anchor="ra")
    return img


def tray_icon(img, value="140"):
    """L'icona di GlucoBar vicino all'orologio: c'è in tutte le modalità."""
    icon = make_icon(value, GREEN).resize((24, 24), Image.LANCZOS)
    img.paste(icon, (TRAY_X + 8, H - BAR_H + 12), icon)


def shadowed(base, overlay, pos, radius=10):
    shadow = Image.new("RGBA", (overlay.width + 40, overlay.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle((20, 24, overlay.width + 20, overlay.height + 24),
                                     fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius))
    base.paste(shadow, (pos[0] - 20, pos[1] - 20), shadow)
    base.paste(overlay, pos)


def keyed(img, key=(0x1f, 0x1f, 0x1f), tol=10):
    """Rende trasparente lo sfondo della vista "barra", come fa Windows."""
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if max(abs(r - key[0]), abs(g - key[1]), abs(b - key[2])) <= tol:
                px[x, y] = (r, g, b, 0)
    return img


def compose(shots, lang, mode):
    img = desktop()
    tray_icon(img)
    d = ImageDraw.Draw(img)
    if mode == "taskbar":
        view = keyed(Image.open(os.path.join(shots, f"{lang}_taskbar.png")))
        img.paste(view, (TRAY_X - view.width - 4, H - BAR_H), view)
    elif mode == "window":
        view = Image.open(os.path.join(shots, f"{lang}_window.png")).convert("RGB")
        shadowed(img, view, (W - view.width - 24, 24))
    elif mode == "desktop":
        view = Image.open(os.path.join(shots, f"{lang}_desktop.png")).convert("RGB")
        shadowed(img, view, (24, 22))
    else:  # solo icona: evidenzia l'icona e mostra il suggerimento
        cx, cy = TRAY_X + 20, H - BAR_H + 24
        d.ellipse((cx - 19, cy - 19, cx + 19, cy + 19), outline="#ffd166", width=3)
        tip = f"140 ↗ mg/dL · {STRINGS[lang]['now']}"
        f = font(14)
        tw = d.textlength(tip, font=f)
        x0, y0 = min(cx - tw / 2 - 12, W - tw - 34), H - BAR_H - 52
        d.rounded_rectangle((x0, y0, x0 + tw + 24, y0 + 34), radius=8, fill="#2b2b2b",
                            outline="#444444")
        d.text((x0 + 12, y0 + 9), tip, font=f, fill="white")
    return img


def for_installer(img, mode):
    """320x200: barra e icona ingrandite sull'angolo dell'orologio, il resto intero."""
    if mode in ("taskbar", "tray"):
        return img.crop((W - 320, H - 200, W, H))
    return img.resize((320, 200), Image.LANCZOS)


def main(shots):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "previews")
    docs = os.path.join(root, "docs")
    os.makedirs(out, exist_ok=True)
    os.makedirs(docs, exist_ok=True)
    for lang in LANGUAGES:
        for mode in ("taskbar", "window", "desktop", "tray"):
            img = compose(shots, lang, mode)
            small = for_installer(img, mode)
            small.save(os.path.join(out, f"{lang}_{mode}.png"), optimize=True)
            if lang == "en":
                big = small.resize((W, H), Image.LANCZOS) if mode in ("taskbar", "tray") else img
                big.save(os.path.join(docs, f"preview_{mode}.png"), optimize=True)


if __name__ == "__main__":
    main(sys.argv[1])
