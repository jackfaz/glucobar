"""Password LibreLinkUp nel Gestione credenziali di Windows (cifrata dal sistema).

Su Linux/macOS, usati solo per sviluppo, finisce in un file leggibile solo dall'utente.
"""

import json
import os
import sys

from .config import CONFIG_DIR

TARGET = "GlucoBar:LibreLinkUp"

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

    def set_password(email, password):
        blob = password.encode("utf-16-le")
        buf = ctypes.create_string_buffer(blob, len(blob))
        cred = CREDENTIALW()
        cred.Type = CRED_TYPE_GENERIC
        cred.TargetName = TARGET
        cred.UserName = email
        cred.CredentialBlobSize = len(blob)
        cred.CredentialBlob = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
        cred.Persist = CRED_PERSIST_LOCAL_MACHINE
        if not _advapi32.CredWriteW(ctypes.byref(cred), 0):
            raise OSError(ctypes.get_last_error(), "CredWriteW non riuscita")

    def get_password(email):
        p = ctypes.POINTER(CREDENTIALW)()
        if not _advapi32.CredReadW(TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(p)):
            return None
        try:
            cred = p.contents
            if (cred.UserName or "").lower() != (email or "").lower():
                return None
            return ctypes.string_at(cred.CredentialBlob,
                                    cred.CredentialBlobSize).decode("utf-16-le")
        finally:
            _advapi32.CredFree(p)

    def delete_password():
        """True se c'era una password e l'ha cancellata."""
        if _advapi32.CredDeleteW(TARGET, CRED_TYPE_GENERIC, 0):
            return True
        if ctypes.get_last_error() == ERROR_NOT_FOUND:
            return False
        raise OSError(ctypes.get_last_error(), "CredDeleteW non riuscita")

else:
    _PATH = os.path.join(CONFIG_DIR, "credentials.json")

    def set_password(email, password):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump({"email": email, "password": password}, f)
        os.chmod(_PATH, 0o600)

    def get_password(email):
        try:
            with open(_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return None
        if data.get("email", "").lower() != (email or "").lower():
            return None
        return data.get("password")

    def delete_password():
        try:
            os.remove(_PATH)
            return True
        except FileNotFoundError:
            return False
