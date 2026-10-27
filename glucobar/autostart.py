"""Avvio di GlucoBar con Windows: valore "GlucoBar" nella chiave Run dell'utente.

È la stessa voce che crea l'installer (installer/glucobar.iss, [Registry]), così si
può accendere e spegnere sia dall'installer sia con `glucobar set autostart=...`.
"""

import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE = "GlucoBar"


def gui_exe():
    """GlucoBar.exe accanto all'eseguibile corrente (solo nella versione installata)."""
    if not getattr(sys, "frozen", False):
        return None
    path = os.path.join(os.path.dirname(sys.executable), "GlucoBar.exe")
    return path if os.path.exists(path) else None


def is_enabled():
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, VALUE)
        return True
    except OSError:
        return False


def set_enabled(enabled):
    """True se l'impostazione è stata applicata."""
    if sys.platform != "win32":
        return False
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            exe = gui_exe()
            if not exe:
                return False
            winreg.SetValueEx(key, VALUE, 0, winreg.REG_SZ, f'"{exe}"')
        else:
            try:
                winreg.DeleteValue(key, VALUE)
            except FileNotFoundError:
                pass
    return True
