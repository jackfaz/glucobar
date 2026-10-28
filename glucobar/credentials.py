"""Password dell'account del sensore nel Gestione credenziali di Windows o nel
Portachiavi del Mac (cifrate dal sistema), una voce per servizio: LibreLinkUp, Dexcom
e Nightscout (il token).

Su Linux, usato solo per sviluppo, finisce in un file leggibile solo dall'utente.
"""

import json
import os
import sys

from .config import CONFIG_DIR

# Perché l'ultima get_password ha dato None (per il log): "not found", "saved for another
# account" o l'errore di Windows
last_problem = None

# sorgente (vedi sources.SOURCES) -> voce nel Gestione credenziali
TARGETS = {"libre": "GlucoBar:LibreLinkUp", "dexcom": "GlucoBar:Dexcom",
           "nightscout": "GlucoBar:Nightscout"}   # per Nightscout: il token

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    _advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    _advapi32.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
    _advapi32.CredWriteW.restype = wintypes.BOOL
    _advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                    ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
    _advapi32.CredReadW.restype = wintypes.BOOL
    _advapi32.CredFree.argtypes = [ctypes.c_void_p]
    _advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    _advapi32.CredDeleteW.restype = wintypes.BOOL
    ERROR_NOT_FOUND = 1168

    def set_password(email, password, source="libre"):
        blob = password.encode("utf-16-le")
        buf = ctypes.create_string_buffer(blob, len(blob))
        cred = CREDENTIALW()
        cred.Type = CRED_TYPE_GENERIC
        cred.TargetName = TARGETS[source]
        cred.UserName = email
        cred.CredentialBlobSize = len(blob)
        cred.CredentialBlob = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
        cred.Persist = CRED_PERSIST_LOCAL_MACHINE
        if not _advapi32.CredWriteW(ctypes.byref(cred), 0):
            raise OSError(ctypes.get_last_error(), "CredWriteW non riuscita")

    def get_password(email, source="libre"):
        global last_problem
        p = ctypes.POINTER(CREDENTIALW)()
        if not _advapi32.CredReadW(TARGETS[source], CRED_TYPE_GENERIC, 0, ctypes.byref(p)):
            code = ctypes.get_last_error()
            last_problem = "not found" if code == ERROR_NOT_FOUND else f"Windows error {code}"
            return None
        try:
            cred = p.contents
            if (cred.UserName or "").lower() != (email or "").lower():
                last_problem = "saved for another account"
                return None
            last_problem = None
            return ctypes.string_at(cred.CredentialBlob,
                                    cred.CredentialBlobSize).decode("utf-16-le")
        finally:
            _advapi32.CredFree(p)

    def _delete(source):
        if _advapi32.CredDeleteW(TARGETS[source], CRED_TYPE_GENERIC, 0):
            return True
        if ctypes.get_last_error() == ERROR_NOT_FOUND:
            return False
        raise OSError(ctypes.get_last_error(), "CredDeleteW non riuscita")

elif sys.platform == "darwin":
    # Portachiavi di macOS (tramite keyring): una voce per servizio, con dentro
    # account e password, così "cambia account" sostituisce quella vecchia
    _ACCOUNT = "GlucoBar"

    def _keychain():
        from keyring.backends import macOS
        return macOS.Keyring()

    def set_password(email, password, source="libre"):
        _keychain().set_password(TARGETS[source], _ACCOUNT,
                                 json.dumps({"email": email, "password": password}))

    def get_password(email, source="libre"):
        try:
            data = json.loads(_keychain().get_password(TARGETS[source], _ACCOUNT) or "{}")
        except Exception:
            return None
        if data.get("email", "").lower() != (email or "").lower():
            return None
        return data.get("password")

    def _delete(source):
        from keyring.errors import PasswordDeleteError
        try:
            _keychain().delete_password(TARGETS[source], _ACCOUNT)
            return True
        except PasswordDeleteError:
            return False

else:
    _DIR = CONFIG_DIR

    def _path(source):
        # "GlucoBar:LibreLinkUp" -> credentials-LibreLinkUp.json
        return os.path.join(_DIR, f"credentials-{TARGETS[source].split(':')[-1]}.json")

    def set_password(email, password, source="libre"):
        os.makedirs(_DIR, exist_ok=True)
        with open(_path(source), "w", encoding="utf-8") as f:
            json.dump({"email": email, "password": password}, f)
        os.chmod(_path(source), 0o600)

    def get_password(email, source="libre"):
        try:
            with open(_path(source), "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return None
        if data.get("email", "").lower() != (email or "").lower():
            return None
        return data.get("password")

    def _delete(source):
        try:
            os.remove(_path(source))
            return True
        except FileNotFoundError:
            return False


def delete_password(source=None):
    """True se c'era almeno una password e l'ha cancellata (senza sorgente: tutte)."""
    deleted = False
    for name in [source] if source else list(TARGETS):
        deleted = _delete(name) or deleted
    return deleted
