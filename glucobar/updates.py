"""Avviso di nuova versione: una richiesta al giorno a GitHub per sapere qual è
l'ultima release (le pre-release non contano). Non manda nessun dato: solo la
richiesta pubblica dell'ultima versione. Si spegne con update_check=false."""

import json
import re
import urllib.request

from . import __version__

API = "https://api.github.com/repos/jackfaz/glucobar/releases/latest"
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


def latest_release(timeout=15):
    """(versione, pagina) dell'ultima release; eccezione se GitHub non risponde."""
    req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": f"GlucoBar/{__version__}"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        data = json.load(res)
    return data["tag_name"].lstrip("v"), data.get("html_url") or RELEASES
