"""Avvio di GlucoBar all'accensione o all'accesso.

Windows: valore "GlucoBar" nella chiave Run dell'utente. È la stessa voce che crea
l'installer (installer/glucobar.iss, [Registry]), così si può accendere e spegnere sia
dall'installer sia con `glucobar set autostart=...`.
Mac: un LaunchAgent dell'utente (~/Library/LaunchAgents), acceso dal menu di GlucoBar
o con `glucobar set autostart=...`.
"""

import os
import plistlib
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE = "GlucoBar"
MAC_LABEL = "io.github.jackfaz.glucobar"
MAC_AGENT = os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents",
                         MAC_LABEL + ".plist")


def gui_exe():
    """GlucoBar accanto all'eseguibile corrente (solo nella versione installata).
    Sul Mac è GlucoBar.app/Contents/MacOS/GlucoBar."""
    if not getattr(sys, "frozen", False):
        return None
    name = "GlucoBar.exe" if sys.platform == "win32" else "GlucoBar"
    path = os.path.join(os.path.dirname(sys.executable), name)
    return path if os.path.exists(path) else None


def is_enabled():
    if sys.platform == "darwin":
        return os.path.exists(MAC_AGENT)
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
    if sys.platform == "darwin":
        return _set_mac(enabled)
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


def _set_mac(enabled):
    if not enabled:
        try:
            os.remove(MAC_AGENT)
        except FileNotFoundError:
            pass
        return True
    exe = gui_exe()
    if not exe:
        return False
    os.makedirs(os.path.dirname(MAC_AGENT), exist_ok=True)
    with open(MAC_AGENT, "wb") as f:
        plistlib.dump({"Label": MAC_LABEL, "ProgramArguments": [exe], "RunAtLoad": True,
                       "ProcessType": "Interactive"}, f)
    return True


def refresh():
    """Sul Mac l'app si può spostare: l'avvio all'accesso punta sempre a dov'è ora."""
    if sys.platform == "darwin" and is_enabled() and gui_exe():
        _set_mac(True)
