"""Impostazioni (senza password) e log, in %APPDATA%\\GlucoBar."""

import json
import os
import sys
import time

APP_NAME = "GlucoBar"

IS_MAC = sys.platform == "darwin"

# Elementi che si possono mostrare, anche insieme. Sul Mac non c'è la barra delle
# applicazioni: "tray" è il valore nella barra dei menu, in alto a destra
ELEMENTS = ("tray", "window", "desktop") if IS_MAC else ("taskbar", "tray", "window", "desktop")


def _config_dir():
    if sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_NAME)
    if IS_MAC:
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    return os.path.join(os.path.expanduser("~"), ".config", "glucobar")


CONFIG_DIR = _config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_PATH = os.path.join(CONFIG_DIR, "glucobar.log")
# File della prima versione (script Python), importato al primo avvio
LEGACY_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".glicemia_widget.json")

# Ogni quanto leggere il dato (secondi): le scelte del menu e il minimo. Sotto i 10 s non
# arriverebbe niente di nuovo (Libre ogni minuto, Dexcom ogni 5) e i servizi rischiano di
# bloccare l'account per troppe richieste.
REFRESH_CHOICES = (10, 30, 60, 120, 300)
MIN_REFRESH = 10

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
    "show_delta": False,        # variazione dalla lettura prima (es. "3 min +5")
    "app_version": "4.16.0",    # LibreLinkUp: si aggiorna se il server ne chiede una più recente
    "language": "auto",         # "auto" oppure it, en, es, fr, de, pt
    # cosa mostrare, anche più cose insieme: taskbar (valore sulla barra),
    # tray (icona col numero vicino all'orologio), window, desktop
    "elements": ["tray"] if IS_MAC else ["taskbar", "tray"],
    # finestrella
    "window_x": None,
    "window_y": None,
    "window_scale": 1.0,        # dimensione (si cambia trascinando l'angolo in basso a destra)
    # barra delle applicazioni
    "taskbar_monitor": 1,       # 1 = principale, 2 = secondo monitor, ...
    "taskbar_side": "right",    # "right" = vicino all'orologio
    "taskbar_offset": 0,        # spostamento extra in pixel
    "taskbar_bg": None,         # es. "#202020" per forzare il colore di sfondo
    "taskbar_text": None,       # colore dei minuti sotto il valore (None = come la barra)
    "taskbar_transparent": True,
    "taskbar_scale": 1.0,       # dimensione del valore sulla barra (0.85 - 1.25)
    "hover_chart": True,        # un secondo col mouse sul valore: compare il grafico
    # pannello sullo sfondo
    "desktop_x": None,
    "desktop_y": None,
    "desktop_w": 460,
    "desktop_h": 300,
    "desktop_hours": 12,        # 3, 6 o 12
    "desktop_alpha": 0.92,      # trasparenza del pannello (1 = opaco)
    "desktop_locked": False,    # True = non si sposta né si ridimensiona
    "desktop_on_top": False,    # True = sopra le altre finestre invece che dietro
    # aspetto: tema "auto" (come Windows o macOS), "dark" o "light"; colori del valore
    # "standard" o "colorblind" (adatti al daltonismo)
    "theme": "auto",
    "palette": "standard",
    # colori scelti a mano dalla finestra Impostazioni (None = quelli della tavolozza)
    "color_in_range": None,
    "color_high": None,
    "color_very_high": None,
    "color_low": None,
    "color_stale": None,
    # colori di finestrella, pannello e messaggi scelti a mano, per tema:
    # {"dark": {"bg": "#101010", ...}, "light": {...}} (vedi theme.UI_KEYS)
    "ui_colors": {},
    # avvisi facoltativi (spenti di default): glicemia bassa, molto alta, nessun dato
    "alert_low": False,
    "alert_high": False,
    "alert_stale": False,
    "alerts_note_shown": False,
    # avviso di nuova versione: una richiesta al giorno a GitHub
    "update_check": True,
    "update_checked_at": 0,
    "update_notified": None,
    "auto_update": False,       # Windows: installa da solo le nuove versioni
    "last_version": None,       # per dire "aggiornato alla x.y.z" al primo avvio
    # LibreLinkUp: persona seguita (se più d'una) e sensore in uso, per i promemoria di
    # fine sensore e la richiesta di sostituzione
    "patient_id": None,
    "sensor_life_days": 14,     # 15 per i sensori Plus
    "sensor_sn": None,
    "sensor_activated": None,
    "sensor_notified": [],
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
    return chosen or [ELEMENTS[0]]


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
