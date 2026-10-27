"""Avvio di GlucoBar.

    GlucoBar.exe                  riparte nell'ultima modalità usata
    GlucoBar.exe --mode desktop   parte in quella modalità (e la ricorda)
    GlucoBar.exe --set-mode tray --set-language it
                                  salva solo le scelte (usato dall'installer) ed esce
"""

import argparse
import os
import sys
import traceback

from . import __version__, credentials
from .config import LOG_PATH, load_config, log, save_config, trim_log
from .controller import MODES
from .i18n import LANGUAGES, set_language, t

MUTEX_NAME = "GlucoBar"   # lo stesso di AppMutex in installer/glucobar.iss
_instance_mutex = None    # resta aperto finché il programma gira


def already_running():
    """Una sola copia di GlucoBar: si cambia modalità dall'icona."""
    global _instance_mutex
    if sys.platform != "win32":
        return False
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    _instance_mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS


def run(mode):
    from .taskbar import enable_dpi_awareness
    enable_dpi_awareness()  # prima di creare qualsiasi finestra

    cfg = load_config()
    if mode:
        cfg["mode"] = mode
    set_language(cfg["language"])

    if not cfg["email"] or not credentials.get_password(cfg["email"]):
        from .ui_common import ask_credentials
        if not ask_credentials(cfg):
            return

    from .controller import Controller
    Controller(cfg).run()


def save_choices(mode, language):
    cfg = load_config()
    if mode:
        cfg["mode"] = mode
    if language:
        cfg["language"] = language
    save_config(cfg)
    log(f"scelte salvate: modalità={cfg['mode']} lingua={cfg['language']}")


def self_test():
    """Per la build: carica tutte le parti nell'exe (moduli mancanti = errore)."""
    try:
        from . import controller, desktop, taskbar, tray, window  # noqa: F401
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
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("--set-mode", choices=MODES)
    parser.add_argument("--set-language", choices=sorted(LANGUAGES) + ["auto"])
    parser.add_argument("--version", action="version", version=f"GlucoBar {__version__}")
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.set_mode or args.set_language:
        save_choices(args.set_mode, args.set_language)
        return 0
    if already_running():
        return 0
    trim_log()
    log(f"GlucoBar {__version__} avvio (Python {sys.version.split()[0]})")
    try:
        run(args.mode)
    except Exception:
        log("ERRORE:\n" + traceback.format_exc())
        show_crash()
        os._exit(1)
    # Uscita netta anche se un thread dell'icona è rimasto appeso: un processo
    # rimasto in vita terrebbe il mutex e GlucoBar non si potrebbe più riaprire
    os._exit(0)
