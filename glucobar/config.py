"""Impostazioni (senza password) e log, in %APPDATA%\\GlucoBar."""

import json
import os
import sys
import time

APP_NAME = "GlucoBar"

# Elementi che si possono mostrare, anche insieme
ELEMENTS = ("taskbar", "tray", "window", "desktop")


def _config_dir():
    if sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_NAME)
    return os.path.join(os.path.expanduser("~"), ".config", "glucobar")


CONFIG_DIR = _config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_PATH = os.path.join(CONFIG_DIR, "glucobar.log")
# File della prima versione (script Python), importato al primo avvio
LEGACY_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".glicemia_widget.json")

DEFAULT_CONFIG = {
    "source": "libre",          # "libre" (LibreLinkUp) oppure "dexcom" (Dexcom Share)
    # account del sensore: email (Dexcom anche telefono o nome utente);
    # la password sta in Gestione credenziali, una voce per sorgente
    "email": "",
    "region": "eu",             # LibreLinkUp: si aggiorna da sola se il server reindirizza
    "dexcom_region": "ous",     # Dexcom: "ous" fuori dagli USA, "us", "jp"
    "unit": "mg/dL",            # oppure "mmol/L"
    "low": 70,                  # soglie in mg/dL
    "high": 180,
    "very_high": 250,
    "refresh_seconds": 60,
    "stale_minutes": 15,        # oltre questo il valore è mostrato in grigio
    "app_version": "4.16.0",    # LibreLinkUp: si aggiorna se il server ne chiede una più recente
    "language": "auto",         # "auto" oppure it, en, es, fr, de, pt
    # cosa mostrare, anche più cose insieme: taskbar (valore sulla barra),
    # tray (icona col numero vicino all'orologio), window, desktop
    "elements": ["taskbar", "tray"],
    # finestrella
    "window_x": None,
    "window_y": None,
    # barra delle applicazioni
    "taskbar_monitor": 1,       # 1 = principale, 2 = secondo monitor, ...
    "taskbar_side": "right",    # "right" = vicino all'orologio
    "taskbar_offset": 0,        # spostamento extra in pixel
    "taskbar_bg": None,         # es. "#202020" per forzare il colore di sfondo
    "taskbar_transparent": True,
    # pannello sullo sfondo
    "desktop_x": None,
    "desktop_y": None,
    "desktop_w": 460,
    "desktop_h": 300,
    "desktop_hours": 12,        # 3, 6 o 12
    "desktop_alpha": 0.92,      # trasparenza del pannello (1 = opaco)
    "desktop_locked": False,    # True = non si sposta né si ridimensiona
    "tray_hint_shown": False,   # notifica "dov'è l'icona" già mostrata
    "tray_promoted": False,     # icona già resa visibile accanto all'orologio (una volta sola)
}


def log(msg):
    """L'exe non ha console: annota tutto in un file."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def trim_log(max_bytes=1_000_000):
    try:
        if os.path.getsize(LOG_PATH) > max_bytes:
            os.replace(LOG_PATH, LOG_PATH + ".old")
    except OSError:
        pass


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in cfg.items() if k != "password"}, f, indent=2)
    if sys.platform != "win32":
        os.chmod(CONFIG_PATH, 0o600)


def normalize_elements(elements):
    """Elementi validi, senza doppioni, nell'ordine di ELEMENTS; mai vuoto."""
    chosen = [e for e in ELEMENTS if e in (elements or [])]
    return chosen or ["taskbar"]


def peek_config():
    """Impostazioni salvate così come sono, senza importazioni né pulizie
    (per accorgersi delle modifiche fatte da `glucobar set` o `glucobar setup`)."""
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        return None
    cfg["elements"] = normalize_elements(cfg["elements"])
    return cfg


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        cfg.update(saved)
        if "elements" not in saved and "mode" in saved:
            # 0.2.0: una modalità alla volta, sempre con l'icona vicino all'orologio
            cfg["elements"] = [saved["mode"], "tray"]
        cfg.pop("mode", None)
        _scrub_legacy()
    elif os.path.exists(LEGACY_CONFIG_PATH):
        cfg = _import_legacy(cfg)
    cfg["elements"] = normalize_elements(cfg["elements"])
    return cfg


def _scrub_legacy():
    """Le versioni fino alla 0.3.0 importavano il vecchio file senza togliere la
    password in chiaro: la toglie ora (le impostazioni sono già state importate)."""
    try:
        with open(LEGACY_CONFIG_PATH, "r", encoding="utf-8") as f:
            legacy = json.load(f)
        if "password" not in legacy and legacy.get("imported_to_glucobar"):
            return
        legacy.pop("password", None)
        legacy["imported_to_glucobar"] = True
        with open(LEGACY_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(legacy, f, indent=2)
        log(f"password in chiaro tolta da {LEGACY_CONFIG_PATH}")
    except (OSError, ValueError):
        pass


def _import_legacy(cfg):
    """Importa impostazioni e password dalla prima versione (script Python)."""
    from . import credentials
    try:
        with open(LEGACY_CONFIG_PATH, "r", encoding="utf-8") as f:
            legacy = json.load(f)
    except (OSError, ValueError):
        return cfg
    if legacy.get("imported_to_glucobar"):
        # già importato una volta: dopo una disinstallazione "cancella tutto"
        # non deve ricomparire niente
        return cfg
    password = legacy.pop("password", "")
    for key in DEFAULT_CONFIG:
        if key in legacy:
            cfg[key] = legacy[key]
    if cfg["email"] and password:
        credentials.set_password(cfg["email"], password, "libre")
    save_config(cfg)
    # la password non resta in chiaro nel vecchio file
    legacy["imported_to_glucobar"] = True
    try:
        with open(LEGACY_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(legacy, f, indent=2)
    except OSError:
        pass
    log(f"impostazioni importate da {LEGACY_CONFIG_PATH} (password tolta dal vecchio file)")
    return cfg


def forget_everything():
    """Cancella password, impostazioni, log e il file della prima versione.
    Usata dalla disinstallazione quando si sceglie di eliminare tutto."""
    import shutil
    from . import credentials
    try:
        credentials.delete_password()
    except OSError:
        pass
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    try:
        os.remove(LEGACY_CONFIG_PATH)
    except OSError:
        pass
