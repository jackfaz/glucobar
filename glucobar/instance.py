"""Una sola copia di GlucoBar alla volta, e un modo per chiederle di chiudersi.

Il mutex "GlucoBar" esiste finché GlucoBar è aperto. L'evento "GlucoBar.Quit" lo
crea la copia aperta: chi lo segnala (installer, disinstallazione, `glucobar stop`)
le chiede di uscire in modo ordinato, così l'icona sparisce subito dall'orologio.
Solo Windows: altrove non fa niente.
"""

import sys
import time

MUTEX_NAME = "GlucoBar"
QUIT_EVENT = "GlucoBar.Quit"

SYNCHRONIZE = 0x00100000
EVENT_MODIFY_STATE = 0x0002
ERROR_ALREADY_EXISTS = 183

_mutex = None   # resta aperto finché il programma gira


def _kernel32():
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    for name in ("CreateMutexW", "OpenMutexW", "CreateEventW", "OpenEventW"):
        getattr(kernel32, name).restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.SetEvent.argtypes = [ctypes.c_void_p]
    kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    return ctypes, kernel32


def already_running():
    """Crea il mutex; True se c'era già (un'altra copia è aperta)."""
    global _mutex
    if sys.platform != "win32":
        return False
    ctypes, kernel32 = _kernel32()
    _mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return ctypes.get_last_error() == ERROR_ALREADY_EXISTS


def is_running():
    if sys.platform != "win32":
        return False
    _ctypes, kernel32 = _kernel32()
    handle = kernel32.OpenMutexW(SYNCHRONIZE, False, MUTEX_NAME)
    if handle:
        kernel32.CloseHandle(handle)
        return True
    return False


def quit_event():
    """Per la copia aperta: l'evento da controllare (None fuori da Windows)."""
    if sys.platform != "win32":
        return None
    _ctypes, kernel32 = _kernel32()
    return kernel32.CreateEventW(None, True, False, QUIT_EVENT)


def quit_requested(event):
    if not event:
        return False
    _ctypes, kernel32 = _kernel32()
    return kernel32.WaitForSingleObject(event, 0) == 0   # WAIT_OBJECT_0: segnalato


def request_quit(timeout=5.0):
    """Chiede a GlucoBar di chiudersi e aspetta che lo faccia.
    True se ora non è più aperto (o non lo era)."""
    if not is_running():
        return True
    _ctypes, kernel32 = _kernel32()
    event = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, QUIT_EVENT)
    if not event:
        return False   # versione senza evento: chi chiama deve chiuderlo in altro modo
    kernel32.SetEvent(event)
    kernel32.CloseHandle(event)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_running():
            return True
        time.sleep(0.2)
    return not is_running()
