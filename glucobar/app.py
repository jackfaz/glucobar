"""Avvio di GlucoBar.

    GlucoBar.exe                          mostra gli elementi scelti l'ultima volta
    GlucoBar.exe --show desktop,tray      mostra questi elementi (e li ricorda)
    GlucoBar.exe --set-elements taskbar,tray --set-language it --set-source libre
                                          salva solo le scelte (usato dall'installer)
    GlucoBar.exe --forget                 cancella password e impostazioni
    GlucoBar.exe --quit                   chiude la copia aperta (installer, disinstallazione)

Elementi: taskbar (valore sulla barra), tray (icona vicino all'orologio),
window (finestrella), desktop (pannello sullo sfondo).
"""

import argparse
import os
import sys
import time
import traceback

from . import __version__, instance
from .config import ELEMENTS, LOG_PATH, forget_everything, load_config, log, \
    normalize_elements, save_config, trim_log
from .i18n import LANGUAGES, set_language, t
from .sources import SOURCES, account_ready

def elements_arg(text):
    """"taskbar,tray" -> ["taskbar", "tray"] (per argparse)."""
    items = [e.strip() for e in text.split(",") if e.strip()]
    wrong = [e for e in items if e not in ELEMENTS]
    if wrong or not items:
        raise argparse.ArgumentTypeError(
            f"elementi validi: {', '.join(ELEMENTS)} (separati da virgola)")
    return normalize_elements(items)


def run(elements):
    from .taskbar import enable_dpi_awareness
    enable_dpi_awareness()  # prima di creare qualsiasi finestra

    cfg = load_config()
    if elements:
        cfg["elements"] = elements
    set_language(cfg["language"])

    from . import autostart
    autostart.refresh()   # Mac: l'app può essere stata spostata

    if not account_ready(cfg) and cfg.get("email"):
        wait_for_credentials(cfg)
    if not account_ready(cfg):
        from .ui_common import ask_credentials
        if not ask_credentials(cfg):
            return

    from .controller import Controller
    Controller(cfg).run()


def wait_for_credentials(cfg, attempts=10, delay=3):
    """Account già configurato ma password non letta: all'avvio con Windows il Gestione
    credenziali può non essere ancora pronto. Riprova per una trentina di secondi prima
    di chiederla di nuovo, e annota il motivo nel log."""
    from . import credentials
    for attempt in range(attempts):
        log(f"password di {cfg['source']} non letta ({credentials.last_problem}), "
            f"tentativo {attempt + 1} di {attempts}")
        if credentials.last_problem == "saved for another account":
            return   # c'è, ma per un altro account: inutile aspettare
        time.sleep(delay)
        if account_ready(cfg):
            log("password letta dopo l'attesa")
            return


def save_choices(elements, language, source=None):
    cfg = load_config()
    if elements:
        cfg["elements"] = elements
    if language:
        cfg["language"] = language
    if source and source != cfg["source"]:
        cfg["source"] = source
        cfg["email"] = ""   # l'account dell'altro servizio non vale più
    save_config(cfg)
    log(f"scelte salvate: elementi={','.join(cfg['elements'])} lingua={cfg['language']} "
        f"sensore={cfg['source']}")


def self_test():
    """Per la build: carica tutte le parti nell'exe (moduli mancanti = errore)."""
    try:
        from . import (alerts, controller, desktop, dexcom, instance,  # noqa: F401
                       librelinkup, menus, nightscout, notify, peek, sensor, settings,
                       sound, support, theme, updates, window)
        if sys.platform == "darwin":
            from . import macbar  # noqa: F401
            log("self-test ok (barra dei menu del Mac)")
        else:
            from . import notifyicon, taskbar, tray  # noqa: F401
            import pystray
            log(f"self-test ok (pystray backend {pystray.Icon.__module__})")
        return 0
    except Exception:
        log("self-test FALLITO:\n" + traceback.format_exc())
        return 1


def show_crash():
    import tkinter as tk
    from tkinter import messagebox
    last_line = traceback.format_exc().strip().splitlines()[-1]
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("GlucoBar",
                         f"{t('crash')}\n\n{last_line}\n\n{t('crash_details')}\n{LOG_PATH}")
    root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="GlucoBar")
    parser.add_argument("--show", type=elements_arg, metavar="ELEMENTI")
    parser.add_argument("--set-elements", type=elements_arg, metavar="ELEMENTI")
    parser.add_argument("--set-language", choices=sorted(LANGUAGES) + ["auto"])
    parser.add_argument("--set-source", choices=SOURCES)
    parser.add_argument("--version", action="version", version=f"GlucoBar {__version__}")
    parser.add_argument("--forget", action="store_true",
                        help="cancella password e impostazioni (usato dalla disinstallazione)")
    parser.add_argument("--quit", action="store_true",
                        help="chiude GlucoBar se è aperto (usato da installer e disinstallazione)")
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.forget:
        forget_everything()
        return 0
    if args.quit:
        return 0 if instance.request_quit() else 1
    if args.set_elements or args.set_language or args.set_source:
        save_choices(args.set_elements, args.set_language, args.set_source)
        return 0
    # Una sola copia di GlucoBar: cosa mostrare si sceglie dal menu
    if instance.already_running():
        return 0
    trim_log()
    log(f"GlucoBar {__version__} avvio (Python {sys.version.split()[0]})")
    try:
        run(args.show)
    except Exception:
        log("ERRORE:\n" + traceback.format_exc())
        show_crash()
        os._exit(1)
    # Uscita netta anche se un thread dell'icona è rimasto appeso: un processo
    # rimasto in vita terrebbe il mutex e GlucoBar non si potrebbe più riaprire
    os._exit(0)
