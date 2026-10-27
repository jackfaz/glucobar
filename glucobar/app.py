"""Avvio di GlucoBar: GlucoBar.exe --mode taskbar|window|tray"""

import argparse
import sys
import traceback

from . import __version__, credentials
from .config import LOG_PATH, load_config, log, trim_log
from .i18n import set_language, t

MODES = ("taskbar", "window", "tray")

_instance_mutex = None  # resta aperto finché il programma gira


def already_running(mode):
    """Una sola copia per modalità (avvio automatico + doppio clic)."""
    global _instance_mutex
    if sys.platform != "win32":
        return False
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    # Stesso nome usato da AppMutex nell'installer (installer/glucobar.iss)
    _instance_mutex = kernel32.CreateMutexW(None, False, f"GlucoBar-{mode}")
    return ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS


def run(mode):
    if mode == "taskbar":
        from .taskbar import enable_dpi_awareness
        enable_dpi_awareness()  # prima di creare qualsiasi finestra

    cfg = load_config()
    set_language(cfg["language"])

    if not cfg["email"] or not credentials.get_password(cfg["email"]):
        from .ui_common import ask_credentials
        if not ask_credentials(cfg):
            return

    if mode == "taskbar":
        from .taskbar import TaskbarGlucose
        TaskbarGlucose(cfg).run()
    elif mode == "window":
        from .window import GlucoseWindow
        GlucoseWindow(cfg).run()
    else:
        from .tray import TrayGlucose
        TrayGlucose(cfg).run()


def self_test():
    """Per la build: carica tutte le modalità nell'exe (moduli mancanti = errore)."""
    try:
        from . import taskbar, tray, window  # noqa: F401
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
    parser.add_argument("--mode", choices=MODES, default="taskbar")
    parser.add_argument("--version", action="version", version=f"GlucoBar {__version__}")
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if already_running(args.mode):
        return 0
    trim_log()
    log(f"GlucoBar {__version__} avvio modalità {args.mode} (Python {sys.version.split()[0]})")
    try:
        run(args.mode)
    except Exception:
        log("ERRORE:\n" + traceback.format_exc())
        show_crash()
        return 1
    return 0
