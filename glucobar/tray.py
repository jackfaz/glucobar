"""Modalità "icona": il valore come icona nell'area di notifica, vicino all'orologio.

L'icona mostra il numero colorato; passandoci sopra col mouse compaiono freccia di
tendenza e minuti trascorsi. Clic destro per il menu.
"""

import os
import threading
import time

import pystray
from PIL import Image, ImageDraw, ImageFont

from .config import save_config
from .i18n import t
from .librelinkup import TREND_ARROWS, LibreLinkUp, fetch_safely
from .ui_common import GREY, age_minutes, color_for, fmt_value, is_stale

ICON_SIZE = 64  # Windows la rimpicciolisce da solo


def find_font_file():
    windir = os.environ.get("WINDIR", r"C:\Windows")
    candidates = [
        os.path.join(windir, "Fonts", "segoeuib.ttf"),
        os.path.join(windir, "Fonts", "arialbd.ttf"),
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


FONT_FILE = find_font_file()


def load_font(size):
    if FONT_FILE:
        return ImageFont.truetype(FONT_FILE, size)
    return ImageFont.load_default(size=size)


def make_icon(text, color):
    """Disegna il testo il più grande possibile dentro l'icona."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    size = ICON_SIZE
    while size > 8:
        font = load_font(size)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        if right - left <= ICON_SIZE and bottom - top <= ICON_SIZE:
            break
        size -= 2
    x = (ICON_SIZE - (right - left)) / 2 - left
    y = (ICON_SIZE - (bottom - top)) / 2 - top
    draw.text((x, y), text, font=font, fill=color)
    return img


class TrayGlucose:
    def __init__(self, cfg):
        self.cfg = cfg
        self.client = LibreLinkUp(cfg)
        self.current = None
        self.error = None
        self.wake = threading.Event()
        self.running = True

        self.icon = pystray.Icon(
            "glucobar",
            make_icon("…", GREY),
            "GlucoBar: " + t("connecting"),
            menu=pystray.Menu(
                pystray.MenuItem(t("menu_refresh"), self.on_refresh, default=True),
                pystray.MenuItem(
                    lambda item: t("menu_to_mmol") if self.cfg["unit"] == "mg/dL"
                    else t("menu_to_mgdl"),
                    self.on_toggle_unit),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(t("menu_quit"), self.on_quit),
            ),
        )

    # ---- menu ----
    def on_refresh(self, _icon=None, _item=None):
        self.wake.set()

    def on_toggle_unit(self, _icon=None, _item=None):
        self.cfg["unit"] = "mmol/L" if self.cfg["unit"] == "mg/dL" else "mg/dL"
        save_config(self.cfg)
        self.render()

    def on_quit(self, _icon=None, _item=None):
        self.running = False
        self.wake.set()
        self.icon.stop()

    # ---- dati ----
    def loop(self, icon):
        icon.visible = True
        last_fetch = 0
        while self.running:
            if self.wake.is_set() or time.time() - last_fetch >= self.cfg["refresh_seconds"]:
                self.wake.clear()
                last_fetch = time.time()
                current, _history, self.error = fetch_safely(self.client)
                if current:
                    self.current = current
            self.render()
            self.wake.wait(15)  # aggiorna i "minuti fa" ogni 15 s

    def render(self):
        c = self.current
        if not c:
            self.icon.icon = make_icon("--", GREY)
            self.icon.title = "GlucoBar: " + (self.error or t("connecting"))
            return

        age = age_minutes(c)
        stale = is_stale(self.cfg, c)
        value = fmt_value(self.cfg, c["mgdl"])
        arrow = "" if stale else TREND_ARROWS.get(c["trend"], "")

        self.icon.icon = make_icon(value, GREY if stale else color_for(self.cfg, c["mgdl"]))
        when = t("now") if age == 0 else t("min_ago", n=age)
        title = f"{value} {arrow} {self.cfg['unit']} · {when}"
        if stale:
            title += " · " + t("stale")
        if self.error:
            title += f"\n⚠ {self.error}"
        self.icon.title = title[:127]  # limite di Windows per il tooltip

    def run(self):
        self.icon.run(setup=self.loop)
