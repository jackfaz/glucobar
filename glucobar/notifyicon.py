"""Icona sempre visibile vicino all'orologio, invece che sotto la freccetta ^.

Windows 11 mette ogni icona nuova nel pannello della freccetta. Quando l'utente la
trascina sulla barra (o la attiva in Impostazioni > Personalizzazione > Barra delle
applicazioni > Altre icone), Windows scrive IsPromoted=1 nella voce dell'icona sotto
HKCU\\Control Panel\\NotifyIconSettings. GlucoBar fa lo stesso, una volta sola: se poi
l'utente la rimette sotto la freccetta, la scelta resta la sua.

La voce la crea Explorer qualche secondo dopo la comparsa dell'icona, e porta il
percorso dell'eseguibile (con la cartella scritta come GUID, es.
{F1B32785-...}\\Programs\\GlucoBar\\GlucoBar.exe): si riconosce dal nome del file.
Non è un'interfaccia documentata da Microsoft.
"""

import ntpath
import sys

KEY = r"Control Panel\NotifyIconSettings"


def promote(exe_name, key=KEY):
    """Rende visibili le icone di `exe_name`; True se ne ha trovata almeno una."""
    if sys.platform != "win32":
        return False
    import winreg
    found = False
    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key)
    except OSError:
        return False   # Windows 10: le icone si mostrano da Impostazioni
    with root:
        index = 0
        while True:
            try:
                name = winreg.EnumKey(root, index)
            except OSError:
                break
            index += 1
            try:
                with winreg.OpenKey(root, name, 0,
                                    winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as icon:
                    path = winreg.QueryValueEx(icon, "ExecutablePath")[0]
                    if ntpath.basename(str(path)).lower() != exe_name.lower():
                        continue
                    winreg.SetValueEx(icon, "IsPromoted", 0, winreg.REG_DWORD, 1)
                    found = True
            except OSError:
                continue
    return found
