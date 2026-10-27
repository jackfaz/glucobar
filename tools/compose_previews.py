"""Crea le anteprime per l'installer e il README.

Uso (su Linux con Xvfb, dopo aver fotografato le viste con dati di prova):
    python tools/compose_previews.py CARTELLA_FOTO

CARTELLA_FOTO contiene {lingua}_{taskbar|window|desktop}.png. Produce:
    assets/previews/{lingua}_base.png        desktop vuoto, 320x200, per l'installer
    assets/previews/{lingua}_{elemento}.png  ritaglio di ogni elemento al suo posto
    assets/previews/layout.json              dove va ogni ritaglio sopra la base
    docs/preview_{elemento}.png              640x400, in inglese, per il README

L'installer mostra la base e sopra solo i ritagli degli elementi spuntati: così
l'anteprima corrisponde sempre alla combinazione scelta.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from glucobar.i18n import LANGUAGES, STRINGS  # noqa: E402
from glucobar.tray import make_icon  # noqa: E402

W, H = 640, 400          # anteprime del README: una porzione dello schermo, 1:1
BAR_H = 48
SS = 4                   # la barra si disegna 4 volte più grande, poi si rimpicciolisce
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GREEN = "#3ecf6e"
ICON = (225, 225, 225)

# Scena dell'installer: disegnata a 480x300 e rimpicciolita a 320x200
SCENE_W, SCENE_H = 480, 300
OUT_W, OUT_H = 320, 200
SCENE_TRAY_X = 276


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def wallpaper(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=(int(58 - 30 * k), int(110 - 70 * k), int(165 - 90 * k)))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((w * 0.47, h * 0.1, w * 1.19, h * 1.05), fill=(120, 170, 230, 70))
    g.ellipse((-w * 0.19, h * 0.45, w * 0.41, h * 1.3), fill=(90, 60, 160, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img.paste(glow, (0, 0), glow)
    return img


def taskbar_strip(w, tray_x, apps_x, apps=5):
    """Barra in stile Windows 11, disegnata a SS× e poi rimpicciolita (bordi morbidi).
    tray_x: inizio dell'area di notifica (il posto dell'icona di GlucoBar resta vuoto)."""
    k = SS
    bar = Image.new("RGBA", (w * k, BAR_H * k), (28, 28, 28, 255))
    d = ImageDraw.Draw(bar)
    d.line((0, 0, w * k, 0), fill=(46, 46, 46), width=k)
    cy = BAR_H // 2

    def sq(x, y, sw, sh, **kw):
        d.rounded_rectangle((x * k, y * k, (x + sw) * k, (y + sh) * k), **kw)

    def start(x0):   # il logo a quattro quadrati
        for dx, dy in ((0, 0), (11, 0), (0, 11), (11, 11)):
            sq(x0 + dx, cy - 11 + dy, 10, 10, radius=k, fill=(76, 194, 255))

    def search(x0):   # lente
        d.ellipse((x0 * k, (cy - 9) * k, (x0 + 14) * k, (cy + 5) * k), outline=ICON,
                  width=int(1.8 * k))
        d.line(((x0 + 12) * k, (cy + 3) * k, (x0 + 18) * k, (cy + 9) * k), fill=ICON,
               width=int(2 * k))

    def folder(x0):   # Esplora file, con l'indicatore di app aperta
        sq(x0, cy - 9, 10, 6, radius=2 * k, fill=(232, 176, 44))
        sq(x0, cy - 6, 24, 17, radius=2 * k, fill=(250, 204, 72))
        sq(x0 + 8, cy + 17, 8, 2, radius=k, fill=(170, 170, 170))

    def browser(x0):   # cerchio con onda
        c = (x0 + 12, cy)
        d.ellipse(((c[0] - 12) * k, (c[1] - 12) * k, (c[0] + 12) * k, (c[1] + 12) * k),
                  fill=(24, 132, 216))
        d.arc(((c[0] - 9) * k, (c[1] - 4) * k, (c[0] + 9) * k, (c[1] + 14) * k), 180, 360,
              fill=(92, 214, 140), width=int(4 * k))

    def mail(x0):   # busta
        sq(x0, cy - 9, 24, 18, radius=2 * k, fill=(30, 110, 200))
        d.line(((x0 + 1) * k, (cy - 8) * k, (x0 + 12) * k, (cy + 1) * k, (x0 + 23) * k,
                (cy - 8) * k), fill=(200, 225, 255), width=int(1.6 * k), joint="curve")

    for i, draw in enumerate((start, search, folder, browser, mail)[:apps]):
        draw(apps_x + i * 40 - (4 if i >= 2 else 0))

    # Area di notifica: freccetta ^, Wi-Fi, volume
    x0 = tray_x + 50
    d.line(((x0 - 5) * k, (cy + 3) * k, x0 * k, (cy - 2) * k, (x0 + 5) * k, (cy + 3) * k),
           fill=ICON, width=int(1.5 * k), joint="curve")
    cx, by = tray_x + 71, cy + 7
    for r in (5, 9.5, 14):
        d.arc(((cx - r) * k, (by - r) * k, (cx + r) * k, (by + r) * k), 225, 315,
              fill=ICON, width=int(1.7 * k))
    d.ellipse(((cx - 1.6) * k, (by - 1.6) * k, (cx + 1.6) * k, (by + 1.6) * k), fill=ICON)
    x0 = tray_x + 90
    d.polygon([(x0 * k, (cy - 3) * k), ((x0 + 4) * k, (cy - 3) * k), ((x0 + 9) * k, (cy - 8) * k),
               ((x0 + 9) * k, (cy + 8) * k), ((x0 + 4) * k, (cy + 3) * k), (x0 * k, (cy + 3) * k)],
              fill=ICON)
    for r in (5, 9):
        d.arc(((x0 + 9 - r) * k, (cy - r) * k, (x0 + 9 + r) * k, (cy + r) * k), -50, 50,
              fill=ICON, width=int(1.6 * k))
    # Orologio su due righe, allineato a destra
    f = font(12 * k)
    d.text(((w - 14) * k, (cy - 2) * k), "19:17", font=f, fill="white", anchor="rs")
    d.text(((w - 14) * k, (cy + 15) * k), "27/10/2026", font=f, fill="white", anchor="rs")
    return bar.resize((w, BAR_H), Image.LANCZOS)


def desktop(w, h, tray_x, apps_x, apps=5):
    img = wallpaper(w, h)
    img.paste(taskbar_strip(w, tray_x, apps_x, apps), (0, h - BAR_H))
    return img


def tray_icon(img, tray_x, value="140"):
    """L'icona di GlucoBar vicino all'orologio."""
    icon = make_icon(value, GREEN).resize((24, 24), Image.LANCZOS)
    img.paste(icon, (tray_x + 8, img.height - BAR_H + 12), icon)


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


def shot(shots, lang, name, rgba=False):
    img = Image.open(os.path.join(shots, f"{lang}_{name}.png"))
    return img.convert("RGBA" if rgba else "RGB")


def scaled(img, factor):
    return img.resize((round(img.width * factor), round(img.height * factor)), Image.LANCZOS)


# ---- anteprime del README: un elemento per immagine ----
def compose(shots, lang, mode):
    tray_x = 436
    img = desktop(W, H, tray_x, apps_x=148)
    d = ImageDraw.Draw(img)
    if mode == "taskbar":
        view = keyed(shot(shots, lang, "taskbar"))
        img.paste(view, (tray_x - view.width - 4, H - BAR_H), view)
    elif mode == "window":
        view = shot(shots, lang, "window")
        shadowed(img, view, (W - view.width - 24, 24))
    elif mode == "desktop":
        view = shot(shots, lang, "desktop")
        shadowed(img, view, (24, 22))
    else:  # icona vicino all'orologio: evidenziata, con il suggerimento
        tray_icon(img, tray_x)
        cx, cy = tray_x + 20, H - BAR_H + 24
        d.ellipse((cx - 19, cy - 19, cx + 19, cy + 19), outline="#ffd166", width=3)
        tip = f"140 ↗ mg/dL · {STRINGS[lang]['now']}"
        f = font(14)
        tw = d.textlength(tip, font=f)
        x0, y0 = min(cx - tw / 2 - 12, W - tw - 34), H - BAR_H - 52
        d.rounded_rectangle((x0, y0, x0 + tw + 24, y0 + 34), radius=8, fill="#2b2b2b",
                            outline="#444444")
        d.text((x0 + 12, y0 + 9), tip, font=f, fill="white")
    if mode in ("taskbar", "tray"):   # ingrandite sull'angolo dell'orologio
        img = img.crop((W - 320, H - 200, W, H)).resize((W, H), Image.LANCZOS)
    return img


# ---- scena a strati dell'installer ----
def scene(shots, lang, element=None):
    """Desktop 480x300 con al più un elemento, sempre nello stesso posto.
    Ritorna (immagine, riquadro dell'elemento compresa l'ombra)."""
    img = desktop(SCENE_W, SCENE_H, SCENE_TRAY_X, apps_x=14, apps=4)
    top = SCENE_H - BAR_H
    if element is None:
        return img, None
    if element == "taskbar":
        view = keyed(shot(shots, lang, "taskbar"))
        x = SCENE_TRAY_X - view.width - 4
        img.paste(view, (x, top), view)
        return img, (x, top, x + view.width, SCENE_H)
    if element == "tray":
        tray_icon(img, SCENE_TRAY_X)
        return img, (SCENE_TRAY_X + 4, top + 8, SCENE_TRAY_X + 36, top + 40)
    if element == "window":
        view = scaled(shot(shots, lang, "window"), 0.85)
        x, y = SCENE_W - view.width - 16, 16
    else:  # desktop
        view = scaled(shot(shots, lang, "desktop"), 0.52)
        x, y = 16, 16
    shadowed(img, view, (x, y))
    return img, (x - 14, y - 10, x + view.width + 16, y + view.height + 22)


def installer_layers(shots, out):
    """Base + un ritaglio per elemento, già a 320x200; layout.json con le posizioni."""
    k = OUT_W / SCENE_W
    layout = {"width": OUT_W, "height": OUT_H, "layers": {}}
    for lang in LANGUAGES:
        base, _ = scene(shots, lang)
        base.resize((OUT_W, OUT_H), Image.LANCZOS).save(
            os.path.join(out, f"{lang}_base.png"), optimize=True)
        for element in ("taskbar", "tray", "window", "desktop"):
            full, (x0, y0, x1, y1) = scene(shots, lang, element)
            box = (int(x0 * k), int(y0 * k), min(OUT_W, round(x1 * k)), min(OUT_H, round(y1 * k)))
            small = full.resize((OUT_W, OUT_H), Image.LANCZOS).crop(box)
            small.save(os.path.join(out, f"{lang}_{element}.png"), optimize=True)
            layout["layers"][element] = {"x": box[0], "y": box[1],
                                         "w": box[2] - box[0], "h": box[3] - box[1]}
    with open(os.path.join(out, "layout.json"), "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2)


def main(shots):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "previews")
    docs = os.path.join(root, "docs")
    os.makedirs(out, exist_ok=True)
    os.makedirs(docs, exist_ok=True)
    installer_layers(shots, out)
    for mode in ("taskbar", "window", "desktop", "tray"):
        compose(shots, "en", mode).save(os.path.join(docs, f"preview_{mode}.png"), optimize=True)


if __name__ == "__main__":
    main(sys.argv[1])
