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
TRAY_X = 436             # inizio dell'area icone/orologio
SS = 4                   # la barra si disegna 4 volte più grande, poi si rimpicciolisce
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GREEN = "#3ecf6e"
ICON = (225, 225, 225)


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def wallpaper():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(58 - 30 * k), int(110 - 70 * k), int(165 - 90 * k)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((300, 40, 760, 420), fill=(120, 170, 230, 70))
    g.ellipse((-120, 180, 260, 520), fill=(90, 60, 160, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img.paste(glow, (0, 0), glow)
    return img


def taskbar_strip():
    """Barra in stile Windows 11, disegnata a SS× e poi rimpicciolita (bordi morbidi)."""
    k = SS
    bar = Image.new("RGBA", (W * k, BAR_H * k), (28, 28, 28, 255))
    d = ImageDraw.Draw(bar)
    d.line((0, 0, W * k, 0), fill=(46, 46, 46), width=k)
    cy = BAR_H // 2

    def sq(x, y, w, h, **kw):
        d.rounded_rectangle((x * k, y * k, (x + w) * k, (y + h) * k), **kw)

    # Start: il logo a quattro quadrati
    x0 = 148
    for dx, dy in ((0, 0), (11, 0), (0, 11), (11, 11)):
        sq(x0 + dx, cy - 11 + dy, 10, 10, radius=k, fill=(76, 194, 255))
    # Ricerca: lente
    x0 = 188
    d.ellipse(((x0) * k, (cy - 9) * k, (x0 + 14) * k, (cy + 5) * k), outline=ICON, width=int(1.8 * k))
    d.line(((x0 + 12) * k, (cy + 3) * k, (x0 + 18) * k, (cy + 9) * k), fill=ICON, width=int(2 * k))
    # Esplora file (cartella), con l'indicatore di app aperta
    x0 = 224
    sq(x0, cy - 9, 10, 6, radius=2 * k, fill=(232, 176, 44))
    sq(x0, cy - 6, 24, 17, radius=2 * k, fill=(250, 204, 72))
    sq(x0 + 8, cy + 17, 8, 2, radius=k, fill=(170, 170, 170))
    # Browser: cerchio con onda
    x0, c = 264, (276, cy)
    d.ellipse(((c[0] - 12) * k, (c[1] - 12) * k, (c[0] + 12) * k, (c[1] + 12) * k), fill=(24, 132, 216))
    d.arc(((c[0] - 9) * k, (c[1] - 4) * k, (c[0] + 9) * k, (c[1] + 14) * k), 180, 360,
          fill=(92, 214, 140), width=int(4 * k))
    # Posta: busta
    x0 = 304
    sq(x0, cy - 9, 24, 18, radius=2 * k, fill=(30, 110, 200))
    d.line(((x0 + 1) * k, (cy - 8) * k, (x0 + 12) * k, (cy + 1) * k, (x0 + 23) * k, (cy - 8) * k),
           fill=(200, 225, 255), width=int(1.6 * k), joint="curve")

    # Area di notifica: freccetta ^
    x0 = 486
    d.line(((x0 - 5) * k, (cy + 3) * k, x0 * k, (cy - 2) * k, (x0 + 5) * k, (cy + 3) * k),
           fill=ICON, width=int(1.5 * k), joint="curve")
    # Wi-Fi: tre archi e un punto
    cx, by = 507, cy + 7
    for r in (5, 9.5, 14):
        d.arc(((cx - r) * k, (by - r) * k, (cx + r) * k, (by + r) * k), 225, 315,
              fill=ICON, width=int(1.7 * k))
    d.ellipse(((cx - 1.6) * k, (by - 1.6) * k, (cx + 1.6) * k, (by + 1.6) * k), fill=ICON)
    # Volume: altoparlante con due onde
    x0 = 526
    d.polygon([(x0 * k, (cy - 3) * k), ((x0 + 4) * k, (cy - 3) * k), ((x0 + 9) * k, (cy - 8) * k),
               ((x0 + 9) * k, (cy + 8) * k), ((x0 + 4) * k, (cy + 3) * k), (x0 * k, (cy + 3) * k)],
              fill=ICON)
    for r in (5, 9):
        d.arc(((x0 + 9 - r) * k, (cy - r) * k, (x0 + 9 + r) * k, (cy + r) * k), -50, 50,
              fill=ICON, width=int(1.6 * k))
    # Orologio su due righe, allineato a destra
    f = font(12 * k)
    d.text(((W - 14) * k, (cy - 2) * k), "19:17", font=f, fill="white", anchor="rs")
    d.text(((W - 14) * k, (cy + 15) * k), "27/10/2026", font=f, fill="white", anchor="rs")
    return bar.resize((W, BAR_H), Image.LANCZOS)


def desktop():
    img = wallpaper()
    img.paste(taskbar_strip(), (0, H - BAR_H))
    return img


def tray_icon(img, value="140"):
    """L'icona di GlucoBar vicino all'orologio."""
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
    else:  # icona vicino all'orologio: evidenziata, con il suggerimento
        tray_icon(img)
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
