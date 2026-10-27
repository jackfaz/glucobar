"""Una sola copia di GlucoBar alla volta, e un modo per chiederle di chiudersi.

Windows: il mutex "GlucoBar" esiste finché GlucoBar è aperto; l'evento "GlucoBar.Quit"
lo crea la copia aperta e chi lo segnala (installer, disinstallazione, `glucobar stop`)
le chiede di uscire in modo ordinato, così l'icona sparisce subito dall'orologio.
Mac (e Linux, per lo sviluppo): un file glucobar.lock tenuto bloccato finché GlucoBar è
aperto, e un file quit.request che la copia aperta controlla.
"""

import os
import sys
import time

MUTEX_NAME = "GlucoBar"
QUIT_EVENT = "GlucoBar.Quit"

SYNCHRONIZE = 0x00100000
EVENT_MODIFY_STATE = 0x0002
ERROR_ALREADY_EXISTS = 183

IS_WIN = sys.platform == "win32"
_lock = None   # mutex (Windows) o file bloccato (altrove): resta aperto finché il programma gira


def _paths():
    from .config import CONFIG_DIR
    return (os.path.join(CONFIG_DIR, "glucobar.lock"),
            os.path.join(CONFIG_DIR, "quit.request"))


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
    """Prende il posto di copia aperta; True se c'era già un'altra copia."""
    global _lock
    if IS_WIN:
        ctypes, kernel32 = _kernel32()
        _lock = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        return ctypes.get_last_error() == ERROR_ALREADY_EXISTS
    import fcntl
    lock_path, quit_path = _paths()
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    handle = open(lock_path, "a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return True
    _lock = handle
    try:
        os.remove(quit_path)   # una richiesta rimasta da prima non vale per questa copia
    except OSError:
        pass
    return False


def is_running():
    if IS_WIN:
        _ctypes, kernel32 = _kernel32()
        handle = kernel32.OpenMutexW(SYNCHRONIZE, False, MUTEX_NAME)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    import fcntl
    lock_path, _quit_path = _paths()
    if _lock is not None:
        return True   # siamo noi la copia aperta
    try:
        with open(lock_path, "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle, fcntl.LOCK_UN)
        return False
    except OSError:
        return True


def quit_event():
    """Per la copia aperta: cosa controllare per sapere se deve chiudersi."""
    if IS_WIN:
        _ctypes, kernel32 = _kernel32()
        return kernel32.CreateEventW(None, True, False, QUIT_EVENT)
    return _paths()[1]


def quit_requested(event):
    if not event:
        return False
    if IS_WIN:
        _ctypes, kernel32 = _kernel32()
        return kernel32.WaitForSingleObject(event, 0) == 0   # WAIT_OBJECT_0: segnalato
    if os.path.exists(event):
        try:
            os.remove(event)
        except OSError:
            pass
        return True
    return False


def request_quit(timeout=5.0):
    """Chiede a GlucoBar di chiudersi e aspetta che lo faccia.
    True se ora non è più aperto (o non lo era)."""
    if not is_running():
        return True
    if IS_WIN:
        _ctypes, kernel32 = _kernel32()
        event = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, QUIT_EVENT)
        if not event:
            return False   # versione senza evento: chi chiama deve chiuderlo in altro modo
        kernel32.SetEvent(event)
        kernel32.CloseHandle(event)
    else:
        with open(_paths()[1], "w") as request:
            request.write("quit\n")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_running():
            return True
        time.sleep(0.2)
    return not is_running()
