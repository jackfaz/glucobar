"""Colori di GlucoBar: tema chiaro o scuro (anche automatico, come Windows o macOS) e
due tavolozze per il valore, quella standard (verde, arancione, rosso) e una per chi
distingue male il rosso dal verde (blu, giallo/arancione, vermiglione: colori di
Okabe e Ito, leggibili con tutte le forme comuni di daltonismo)."""

import subprocess
import sys
import time

THEMES = ("auto", "dark", "light")
PALETTES = ("standard", "colorblind")

_BASE = {
    False: dict(bg="#1e1f22", fg="#f2f2f2", dim="#8a8d93", grey="#9a9da3", panel="#15171c",
                grid="#2a2d35", line="#c9ccd1", grip="#4a4d55", error="#ff4d4f"),
    True: dict(bg="#f4f4f5", fg="#1d1f23", dim="#62666d", grey="#8a8d93", panel="#ffffff",
               grid="#e1e3e6", line="#4d5157", grip="#b4b7bd", error="#c62828"),
}
# (palette, chiaro) -> nel range, alto, basso o molto alto, fascia del range nei grafici
_VALUES = {
    ("standard", False): ("#3ecf6e", "#f5a524", "#ff4d4f", "#1b3325"),
    ("standard", True): ("#1e9e4a", "#c77800", "#d32f2f", "#e2f4e8"),
    ("colorblind", False): ("#56b4e9", "#f0e442", "#e66100", "#1b2c38"),
    ("colorblind", True): ("#0072b2", "#e69f00", "#a0153e", "#e0edf6"),
}


class Palette:
    def __init__(self, palette, light):
        self.light = light
        for name, value in _BASE[light].items():
            setattr(self, name, value)
        self.in_range, self.high, self.danger, self.band = _VALUES[(palette, light)]

    def value(self, cfg, mgdl):
        """Colore di una misura: fuori dalle soglie basso/molto alto, sopra l'obiettivo,
        nel range."""
        if mgdl < cfg["low"] or mgdl > cfg["very_high"]:
            return self.danger
        if mgdl > cfg["high"]:
            return self.high
        return self.in_range


_cache = {}


def _cached(name, fn, seconds=10):
    """Il tema di sistema si legge al massimo ogni 10 secondi."""
    hit = _cache.get(name)
    if hit and time.monotonic() - hit[0] < seconds:
        return hit[1]
    value = fn()
    _cache[name] = (time.monotonic(), value)
    return value


def _windows_flag(name):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            return winreg.QueryValueEx(key, name)[0] == 1
    except OSError:
        return False


def _mac_light():
    try:
        out = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"],
                             capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return "dark" not in out.lower()   # la chiave esiste solo col tema scuro


def apps_light():
    """Tema chiaro scelto per le app in Windows o macOS."""
    if sys.platform == "win32":
        return _cached("apps", lambda: _windows_flag("AppsUseLightTheme"))
    if sys.platform == "darwin":
        return _cached("apps", _mac_light)
    return False


def taskbar_light():
    """Barra delle applicazioni (Windows) o barra dei menu (Mac) chiara."""
    if sys.platform == "win32":
        return _cached("taskbar", lambda: _windows_flag("SystemUsesLightTheme"))
    return apps_light()


def is_light(cfg):
    theme = cfg.get("theme", "auto")
    if theme == "auto":
        return apps_light()
    return theme == "light"


def palette(cfg, light=None):
    """Colori per le finestre di GlucoBar (light=None: secondo il tema scelto) oppure,
    con light=True/False, per stare sopra una barra chiara o scura."""
    name = cfg.get("palette", "standard")
    if name not in PALETTES:
        name = "standard"
    return Palette(name, is_light(cfg) if light is None else bool(light))
