"""Impostazioni (senza password) e log, in %APPDATA%\\GlucoBar."""

import json
import os
import sys
import time

APP_NAME = "GlucoBar"


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
    "email": "",                # account LibreLinkUp (la password sta in Gestione credenziali)
    "region": "eu",             # si aggiorna da sola se il server reindirizza
    "unit": "mg/dL",            # oppure "mmol/L"
    "low": 70,                  # soglie in mg/dL
    "high": 180,
    "very_high": 250,
    "refresh_seconds": 60,
    "stale_minutes": 15,        # oltre questo il valore è mostrato in grigio
    "app_version": "4.16.0",    # si aggiorna da sola se il server ne chiede una più recente
    "language": "auto",         # "auto", "it" o "en"
    # finestrella
    "window_x": None,
    "window_y": None,
    # barra delle applicazioni
    "taskbar_monitor": 1,       # 1 = principale, 2 = secondo monitor, ...
    "taskbar_side": "right",    # "right" = vicino all'orologio
    "taskbar_offset": 0,        # spostamento extra in pixel
    "taskbar_bg": None,         # es. "#202020" per forzare il colore di sfondo
    "taskbar_transparent": True,
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


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    elif os.path.exists(LEGACY_CONFIG_PATH):
        cfg = _import_legacy(cfg)
    return cfg


def _import_legacy(cfg):
    """Importa impostazioni e password dalla prima versione (script Python)."""
    from . import credentials
    try:
        with open(LEGACY_CONFIG_PATH, "r", encoding="utf-8") as f:
            legacy = json.load(f)
    except (OSError, ValueError):
        return cfg
    password = legacy.pop("password", "")
    for key in DEFAULT_CONFIG:
        if key in legacy:
            cfg[key] = legacy[key]
    if cfg["email"] and password:
        credentials.set_password(cfg["email"], password)
    save_config(cfg)
    log(f"impostazioni importate da {LEGACY_CONFIG_PATH}")
    return cfg
