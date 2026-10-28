"""`glucobar report`: riepilogo da incollare in una segnalazione su GitHub.

Raccoglie versione, Windows, schermi, impostazioni e le ultime righe del log.
Toglie le cose personali: email, nome utente nei percorsi, valori di glicemia.
"""

import os
import re
import sys

from . import __version__, autostart, credentials, i18n
from .config import LOG_PATH

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
READING = re.compile(r"\b\d{1,3}(?:[.,]\d)?(?= ?(?:mg/dL|mmol/L))")


def redact(text, cfg=None):
    """Toglie email, cartella utente (che contiene il nome) e valori di glicemia."""
    home = os.path.expanduser("~")
    if len(home) > 3:
        text = re.sub(re.escape(home), "%USERPROFILE%", text, flags=re.I)
    if cfg and cfg.get("email"):
        text = re.sub(re.escape(cfg["email"]), "<email>", text, flags=re.I)
    text = EMAIL.sub("<email>", text)
    text = re.sub(r"(token=|api-secret[:=]\s*)[^&\s]+", r"\1<token>", text, flags=re.I)
    return READING.sub("<value>", text)


def windows_version():
    if sys.platform != "win32":
        import platform
        return platform.platform()
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            def value(name, default=""):
                try:
                    return winreg.QueryValueEx(key, name)[0]
                except OSError:
                    return default
            build = int(value("CurrentBuild", "0") or 0)
            # ProductName dice "Windows 10" anche su Windows 11
            name = "Windows 11" if build >= 22000 else "Windows 10"
            edition = value("EditionID")
            return f"{name} {edition} {value('DisplayVersion')} (build {build}.{value('UBR', 0)})"
    except OSError:
        return "Windows (unknown version)"


def _registry_flag(path, name):
    if sys.platform != "win32":
        return None
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None


def screens():
    """Barre delle applicazioni trovate, con posizione e monitor (solo Windows)."""
    if sys.platform != "win32":
        return []
    from .taskbar import all_taskbars, monitor_rect, window_rect
    lines = []
    for i, bar in enumerate(all_taskbars(), 1):
        ml, mt, mr, mb = monitor_rect(bar)
        lines.append(f"taskbar {i}: {window_rect(bar)} on monitor {mr - ml}x{mb - mt} at ({ml},{mt})")
    return lines


def dpi():
    if sys.platform != "win32":
        return "-"
    import ctypes
    try:
        return f"{ctypes.windll.user32.GetDpiForSystem() * 100 // 96}%"
    except (AttributeError, OSError):
        return "?"


def in_path():
    folders = os.environ.get("PATH", "").lower().split(os.pathsep)
    return any(f.rstrip("\\/").endswith(os.path.join("glucobar", "bin")) for f in folders)


def build_report(cfg, running, log_lines=40):
    if sys.platform == "win32":
        # scala e coordinate reali, come le vede GlucoBar (non quelle "virtuali")
        from .taskbar import enable_dpi_awareness
        enable_dpi_awareness()
    yes = lambda flag: "yes" if flag else "no"  # noqa: E731
    password = bool(cfg.get("email") and credentials.get_password(cfg["email"], cfg["source"]))
    nightscout = cfg["source"] == "nightscout"
    alignment = _registry_flag(r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                               "TaskbarAl")
    light = _registry_flag(r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                           "SystemUsesLightTheme")
    rows = [
        ("GlucoBar", f"{__version__} ({'installed' if getattr(sys, 'frozen', False) else 'from source'})"),
        ("Windows", windows_version()),
        ("Scaling", dpi()),
        ("Theme", {None: "-", 0: "dark", 1: "light"}.get(light, str(light))),
        ("Taskbar alignment", {None: "-", 0: "left", 1: "center"}.get(alignment, str(alignment))),
        ("Language", f"{cfg['language']} (shown: {i18n.current_language()})"),
        ("Shown", ", ".join(cfg["elements"])),
        # soglie scritte senza "mg/dL" subito dopo: non sono letture, non vanno nascoste
        ("Unit / thresholds", f"{cfg['unit']}, low {cfg['low']}, high {cfg['high']}, "
                              f"very high {cfg['very_high']} (in mg/dL)"),
        ("Taskbar settings", f"monitor {cfg['taskbar_monitor']}, side {cfg['taskbar_side']}, "
                             f"offset {cfg['taskbar_offset']}, transparent "
                             f"{yes(cfg['taskbar_transparent'])}, bg {cfg['taskbar_bg'] or 'auto'}"),
        ("Look", f"theme {cfg.get('theme', 'auto')}, colours {cfg.get('palette', 'standard')}"),
        ("Alerts", ", ".join(k for k in ("low", "high", "stale") if cfg.get(f"alert_{k}"))
                   or "off"),
        ("Update check", yes(cfg.get("update_check", True))),
        ("Desktop panel", f"{cfg['desktop_w']}x{cfg['desktop_h']}, {cfg['desktop_hours']} h, "
                          f"opacity {cfg['desktop_alpha']}, locked {yes(cfg['desktop_locked'])}"),
        ("Account", ("site set, " + ("token saved" if password else "no token"))
                    if nightscout and cfg.get("email") else
                    "email and password saved" if password else
                    "email saved, password missing" if cfg.get("email") else "not set up"),
        ("Sensor", f"Dexcom Share, region {cfg['dexcom_region']}" if cfg["source"] == "dexcom"
                   else "Nightscout" if nightscout
                   else f"LibreLinkUp, region {cfg['region']}, app version {cfg['app_version']}, "
                        f"sensor life {cfg.get('sensor_life_days', 14)} days"),
        ("Running", yes(running)),
        ("Start with Windows", yes(autostart.is_enabled())),
        ("glucobar in PATH", yes(in_path())),
    ]
    out = ["```text", "GlucoBar diagnostic report"]
    out += [f"{name + ':':<20} {value}" for name, value in rows]
    for line in screens():
        out.append(f"{'Screen:':<20} {line}")
    out.append("")
    out.append(f"Last {log_lines} log lines ({LOG_PATH}):")
    try:
        with open(LOG_PATH, encoding="utf-8", errors="replace") as f:
            out += [line.rstrip("\n") for line in f.readlines()[-log_lines:]]
    except OSError:
        out.append("(no log)")
    out.append("```")
    return redact("\n".join(out), cfg)


def copy_to_clipboard(text):
    """True se il testo è finito negli appunti di Windows."""
    if sys.platform != "win32":
        return False
    import ctypes
    from ctypes import wintypes
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    data = text.encode("utf-16-le") + b"\0\0"
    if not user32.OpenClipboard(None):
        return False
    try:
        user32.EmptyClipboard()
        handle = kernel32.GlobalAlloc(0x0002, len(data))   # GMEM_MOVEABLE
        pointer = kernel32.GlobalLock(handle)
        ctypes.memmove(pointer, data, len(data))
        kernel32.GlobalUnlock(handle)
        return bool(user32.SetClipboardData(13, handle))   # CF_UNICODETEXT
    finally:
        user32.CloseClipboard()
