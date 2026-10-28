"""L'icona di GlucoBar nell'area di notifica, vicino all'orologio.

Mostra il valore colorato (passandoci sopra: freccia e minuti) e, col clic destro,
il menu di GlucoBar (lo stesso degli altri elementi, vedi menus.py). Si può nascondere: il menu
resta disponibile col clic destro sugli altri elementi.
"""

import os
import traceback

import pystray
from PIL import Image, ImageDraw, ImageFont

from .config import log, save_config
from .i18n import t
from .menus import to_pystray
from .theme import palette, taskbar_light
from .ui_common import GREY, age_minutes, asset_path, beside_value, fmt_value, is_stale

ICON_SIZE = 64  # Windows la rimpicciolisce da solo
WM_RBUTTONUP = 0x0205
# Su Windows pystray costruisce il menu una volta e lo tiene pronto: va ricostruito al
# clic destro (vedi _Icon), non dall'esterno
BUILD_ON_CLICK = hasattr(pystray.Icon, "_on_notify") and hasattr(pystray.Icon, "_update_menu")


class _Icon(pystray.Icon):
    """Il menu viene costruito al clic destro, nel thread dell'icona, appena prima di
    mostrarlo. Prima lo ricostruiva il controller a ogni lettura (ogni 10-15 secondi), da
    un altro thread: pystray distruggeva il menu anche mentre era aperto, i sottomenu non
    si aprivano e funzionava solo Esci."""

    def _on_notify(self, wparam, lparam):
        if BUILD_ON_CLICK and lparam == WM_RBUTTONUP:
            self._update_menu()
        return super()._on_notify(wparam, lparam)


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
    """Il testo alto quanto tutta l'icona; se è troppo largo (es. "199") viene stretto
    in orizzontale, come un carattere condensato, invece di essere rimpicciolito:
    Windows mostra l'icona a 16-24 pixel e le cifre devono restare leggibili."""
    font = load_font(ICON_SIZE * 2)   # disegnato grande e poi ridotto: bordi più puliti
    left, top, right, bottom = font.getbbox(text)
    glyphs = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    ImageDraw.Draw(glyphs).text((-left, -top), text, font=font, fill=color)
    width = min(ICON_SIZE, round(glyphs.width * ICON_SIZE / glyphs.height))
    glyphs = glyphs.resize((width, ICON_SIZE), Image.LANCZOS)
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    img.paste(glyphs, ((ICON_SIZE - width) // 2, 0), glyphs)
    return img


def logo_icon():
    try:
        return Image.open(asset_path("glucobar.png")).resize((ICON_SIZE, ICON_SIZE))
    except OSError:
        return make_icon("G", GREY)


class TrayIcon:
    def __init__(self, ctl):
        self.ctl = ctl
        self.ready = False   # l'icona esiste davvero solo dopo _setup
        self.logo = logo_icon()
        self.icon = _Icon("glucobar", self.logo, "GlucoBar", menu=self.build_menu())

    def build_menu(self):
        # su Windows ricostruito a ogni clic destro (_Icon), altrove da update_menu()
        return pystray.Menu(lambda: to_pystray(self.ctl.menu_items(), self.ctl.post))

    def start(self):
        # Su Windows l'icona gira in un suo thread, accanto al ciclo di Tkinter
        self.icon.run_detached(setup=self._setup)

    def _setup(self, icon):
        cfg = self.ctl.cfg
        icon.visible = "tray" in cfg["elements"]
        self.ready = True
        log("icona nell'area di notifica creata")
        if icon.visible:
            # Windows 11 nasconde le icone nuove sotto la freccetta ^
            self.ctl.post(self.ctl.promote_tray)

    def show_hint(self):
        """Spiega dov'è l'icona, se non è riuscito a metterla accanto all'orologio."""
        cfg = self.ctl.cfg
        if cfg.get("tray_hint_shown"):
            return
        try:
            self.icon.notify(t("tray_hint"), "GlucoBar")
        except Exception as e:
            log(f"notifica non mostrata: {e}")
        cfg["tray_hint_shown"] = True
        save_config(cfg)

    def set_visible(self, visible):
        if not self.ready:
            return   # ci pensa _setup, leggendo cfg["elements"]
        try:
            self.icon.visible = visible
        except Exception:
            log("visibilità dell'icona non cambiata:\n" + traceback.format_exc())

    def update_menu(self):
        if BUILD_ON_CLICK:
            return   # ci pensa _Icon al prossimo clic destro
        try:
            self.icon.update_menu()
        except Exception:
            pass

    def stop(self):
        try:
            self.icon.stop()
        except Exception:
            pass

    def render(self):
        ctl, cfg, c = self.ctl, self.ctl.cfg, self.ctl.current
        if not c:
            self.icon.icon = self.logo
            self.icon.title = "GlucoBar: " + (ctl.error or t("connecting"))
            return
        age = age_minutes(c)
        stale = is_stale(cfg, c)
        value = fmt_value(cfg, c["mgdl"])
        arrow = beside_value(cfg, ctl.history, c)
        pal = palette(cfg, light=taskbar_light())
        color = pal.stale if stale else pal.value(cfg, c["mgdl"])
        self.icon.icon = make_icon(value, color)
        when = t("now") if age == 0 else t("min_ago", n=age)
        title = f"{value} {arrow} {cfg['unit']} · {when}"
        if stale:
            title += " · " + t("stale")
        if ctl.error:
            title += f"\n⚠ {ctl.error}"
        self.icon.title = title[:127]  # limite di Windows per il tooltip
