"""Nuove versioni: una richiesta al giorno a GitHub per sapere qual è l'ultima release
(le pre-release non contano: sono quelle ancora segnalate per errore dagli antivirus).
Non manda nessun dato. Si spegne con update_check=false.

Su Windows GlucoBar può anche installarla: scarica l'installer della release, ne
controlla l'impronta SHA-256 data da GitHub e lo avvia in modalità silenziosa.
L'installer chiude GlucoBar, sostituisce i file e lo riapre, tenendo le impostazioni.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

from . import __version__

# GLUCOBAR_UPDATE_API: un server di prova (vedi la build)
API = os.environ.get("GLUCOBAR_UPDATE_API") or \
    "https://api.github.com/repos/jackfaz/glucobar/releases/latest"
RELEASES = "https://github.com/jackfaz/glucobar/releases/latest"
INTERVAL = 24 * 3600


def parse_version(text):
    """"v0.9.0" -> (0, 9, 0); None se non è una versione."""
    match = re.match(r"v?(\d+)\.(\d+)(?:\.(\d+))?$", (text or "").strip())
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def is_newer(latest, current=__version__):
    a, b = parse_version(latest), parse_version(current)
    return bool(a and b and a > b)


def _get(url, timeout):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": f"GlucoBar/{__version__}"})
    return urllib.request.urlopen(req, timeout=timeout)


def parse_release(data):
    """Dalla risposta di GitHub: versione, pagina e installer per Windows (se c'è)."""
    version = data["tag_name"].lstrip("v")
    release = {"version": version, "page": data.get("html_url") or RELEASES,
               "installer": None, "sha256": None}
    assets = data.get("assets") or []
    # prima l'installer col numero di versione, poi quello col nome fisso
    for wanted in (f"GlucoBar-Setup-{version}.exe", "GlucoBar-Setup.exe"):
        asset = next((a for a in assets if a.get("name") == wanted), None)
        if asset:
            digest = asset.get("digest") or ""
            release["installer"] = asset["browser_download_url"]
            release["sha256"] = digest[7:].lower() if digest.startswith("sha256:") else None
            break
    return release


def latest_release(timeout=15):
    """Ultima release (vedi parse_release); eccezione se GitHub non risponde."""
    with _get(API, timeout) as res:
        return parse_release(json.load(res))


def can_install():
    """Installazione automatica: solo nella versione installata per Windows."""
    return sys.platform == "win32" and getattr(sys, "frozen", False)


def download(release, folder=None, timeout=120):
    """Scarica l'installer e ne controlla impronta e formato. Ritorna il percorso."""
    folder = folder or os.path.join(tempfile.gettempdir(), "GlucoBar-update")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"GlucoBar-Setup-{release['version']}.exe")
    digest = hashlib.sha256()
    with _get(release["installer"], timeout) as res, open(path, "wb") as f:
        while True:
            chunk = res.read(1 << 16)
            if not chunk:
                break
            digest.update(chunk)
            f.write(chunk)
    with open(path, "rb") as f:
        if f.read(2) != b"MZ":
            raise ValueError("not a Windows program")
    if release["sha256"] and digest.hexdigest() != release["sha256"]:
        os.remove(path)
        raise ValueError("SHA-256 does not match")
    return path


def installer_args(exe=None):
    """Installazione silenziosa nello stesso posto di quella attuale: per l'utente
    (cartella AppData, senza permessi da amministratore) o per tutti."""
    exe = os.path.normcase(os.path.abspath(exe or sys.executable))
    local = os.path.normcase(os.path.abspath(os.environ.get("LOCALAPPDATA") or "~"))
    scope = "/CURRENTUSER" if exe.startswith(local) else "/ALLUSERS"
    return ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", scope]


def run_installer(path):
    """Avvia l'installer staccato da GlucoBar: lui chiuderà GlucoBar e lo riaprirà."""
    flags = 0x00000008 | 0x00000200   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([path] + installer_args(), creationflags=flags, close_fds=True)
