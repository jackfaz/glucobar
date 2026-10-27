"""L'icona di GlucoBar nell'area di notifica, vicino all'orologio.

Mostra il valore colorato (passandoci sopra: freccia e minuti) e, col clic destro,
il menu: cosa mostrare, unità, lingua, account, esci. Si può nascondere: il menu
resta disponibile col clic destro sugli altri elementi.
"""

import os
import traceback

import pystray
from PIL import Image, ImageDraw, ImageFont

from . import i18n
from .config import ELEMENTS, log, save_config
from .i18n import LANGUAGES, t
from .sources import TREND_ARROWS
from .ui_common import GREY, age_minutes, asset_path, color_for, fmt_value, is_stale

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
        self.icon = pystray.Icon("glucobar", self.logo, "GlucoBar", menu=self.build_menu())

    def build_menu(self):
        ctl = self.ctl

        def do(fn, *args):
            # i clic arrivano dal thread dell'icona: li esegue il thread di Tk
            return lambda: ctl.post(fn, *args)

        def show_item(element):
            return pystray.MenuItem(lambda item: t(f"mode_{element}"),
                                    do(ctl.toggle_element, element),
                                    checked=lambda item: ctl.shown(element))

        def lang_item(code, name):
            return pystray.MenuItem(name, do(ctl.set_language, code), radio=True,
                                    checked=lambda item: i18n.current_language() == code)

        return pystray.Menu(
            pystray.MenuItem(lambda item: t("menu_refresh"), do(ctl.refresh), default=True),
            pystray.MenuItem(lambda item: t("menu_show"),
                             pystray.Menu(*[show_item(e) for e in ELEMENTS])),
            pystray.MenuItem(lambda item: t("menu_unit"), do(ctl.toggle_unit)),
            pystray.MenuItem(lambda item: t("menu_language"),
                             pystray.Menu(*[lang_item(c, n) for c, n in LANGUAGES.items()])),
            pystray.MenuItem(lambda item: t("menu_account"), do(ctl.change_account)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: t("menu_quit"), do(ctl.quit)),
        )

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
        arrow = "" if stale else TREND_ARROWS.get(c["trend"], "")
        self.icon.icon = make_icon(value, GREY if stale else color_for(cfg, c["mgdl"]))
        when = t("now") if age == 0 else t("min_ago", n=age)
        title = f"{value} {arrow} {cfg['unit']} · {when}"
        if stale:
            title += " · " + t("stale")
        if ctl.error:
            title += f"\n⚠ {ctl.error}"
        self.icon.title = title[:127]  # limite di Windows per il tooltip
