"""Testi dell'interfaccia in italiano e inglese."""

import locale
import sys

STRINGS = {
    "it": {
        "connecting": "connessione…",
        "now": "ora",
        "min_ago": "{n} min fa",
        "min_short": "{n} min",
        "error_short": "errore",
        "stale": "DATO VECCHIO",
        "menu_refresh": "Aggiorna ora",
        "menu_unit": "Cambia unità (mg/dL ↔ mmol/L)",
        "menu_to_mmol": "Passa a mmol/L",
        "menu_to_mgdl": "Passa a mg/dL",
        "menu_account": "Cambia account…",
        "menu_side": "Sposta a sinistra / a destra",
        "menu_monitor": "Sposta sull'altro monitor",
        "menu_quit": "Esci",
        "cred_title": "GlucoBar – account LibreLinkUp",
        "cred_email": "Email dell'account LibreLinkUp\n(quello che SEGUE il sensore):",
        "cred_password": "Password:",
        "err_session": "Sessione scaduta",
        "err_offline": "Nessuna connessione",
        "err_http": "Errore HTTP {code}",
        "err_credentials": "Email o password errate",
        "err_terms": "Apri l'app LibreLinkUp sul telefono e accetta i termini d'uso, poi riprova",
        "err_login": "Login fallito: {msg}",
        "err_redirects": "Login fallito: troppi reindirizzamenti",
        "err_unexpected": "Risposta inattesa (stato {status})",
        "err_no_patient": "Nessun paziente collegato: invita questo account dall'app LibreLink",
        "err_no_password": "Password mancante: usa «Cambia account…»",
        "err_generic": "Errore: {msg}",
        "crash": "GlucoBar si è fermato per un errore.",
        "crash_details": "I dettagli sono in:",
    },
    "en": {
        "connecting": "connecting…",
        "now": "now",
        "min_ago": "{n} min ago",
        "min_short": "{n} min",
        "error_short": "error",
        "stale": "OLD READING",
        "menu_refresh": "Refresh now",
        "menu_unit": "Switch unit (mg/dL ↔ mmol/L)",
        "menu_to_mmol": "Switch to mmol/L",
        "menu_to_mgdl": "Switch to mg/dL",
        "menu_account": "Change account…",
        "menu_side": "Move left / right",
        "menu_monitor": "Move to the other monitor",
        "menu_quit": "Quit",
        "cred_title": "GlucoBar – LibreLinkUp account",
        "cred_email": "LibreLinkUp account email\n(the one that FOLLOWS the sensor):",
        "cred_password": "Password:",
        "err_session": "Session expired",
        "err_offline": "No connection",
        "err_http": "HTTP error {code}",
        "err_credentials": "Wrong email or password",
        "err_terms": "Open the LibreLinkUp app on your phone and accept the terms of use, then retry",
        "err_login": "Login failed: {msg}",
        "err_redirects": "Login failed: too many redirects",
        "err_unexpected": "Unexpected response (status {status})",
        "err_no_patient": "No patient linked: invite this account from the LibreLink app",
        "err_no_password": "Missing password: use “Change account…”",
        "err_generic": "Error: {msg}",
        "crash": "GlucoBar stopped because of an error.",
        "crash_details": "Details are in:",
    },
}

_lang = None


def detect_language():
    if sys.platform == "win32":
        try:
            import ctypes
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return "it" if langid & 0x3FF == 0x10 else "en"
        except Exception:
            pass
    try:
        name = locale.getlocale()[0] or ""
    except ValueError:
        name = ""
    return "it" if name.lower().startswith("it") else "en"


def set_language(preference):
    """preference: "auto", "it" oppure "en"."""
    global _lang
    _lang = preference if preference in STRINGS else detect_language()


def t(key, **kwargs):
    lang = _lang or detect_language()
    text = STRINGS[lang].get(key) or STRINGS["en"][key]
    return text.format(**kwargs) if kwargs else text
