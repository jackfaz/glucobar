"""Client per Nightscout, il sito open source dove molti raccolgono i dati del sensore
(Libre, Dexcom, Medtronic, Eversense, xDrip+, Juggluco, AndroidAPS, ...).

API documentata (/api/v1). L'"account" è l'indirizzo del sito; se il sito non è
pubblico serve un token di accesso in sola lettura (Admin Tools, ruolo "readable").
Si accetta anche l'API_SECRET, mandato come SHA-1 nell'intestazione api-secret.
"""

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from . import credentials
from .config import save_config
from .i18n import t
from .sources import SourceError

HISTORY_HOURS = 24
# Le risposte più vecchie danno la tendenza come numero (come Dexcom)
TREND_NAMES = {1: "DoubleUp", 2: "SingleUp", 3: "FortyFiveUp", 4: "Flat",
               5: "FortyFiveDown", 6: "SingleDown", 7: "DoubleDown"}


class NightscoutError(SourceError):
    pass


def normalize_url(url):
    """"mionome.herokuapp.com/" -> "https://mionome.herokuapp.com"."""
    url = (url or "").strip().rstrip("/")
    if url and "://" not in url:
        url = "https://" + url
    return url


class Nightscout:
    def __init__(self, cfg, save=save_config, password=None):
        """`password`: il token da provare prima di salvarlo (glucobar setup)."""
        self.cfg = cfg
        self.save = save
        self.password = password
        self.use_secret = False   # il token si è rivelato un API_SECRET
        self.connection = None    # Nightscout non dice quando è stato messo il sensore

    @property
    def base_url(self):
        return normalize_url(self.cfg["email"])

    def _token(self):
        if self.password is not None:
            return self.password
        return credentials.get_password(self.cfg["email"], "nightscout") or ""

    def _get(self, path, params):
        token = self._token()
        params = dict(params)
        headers = {"Accept": "application/json", "User-Agent": "GlucoBar"}
        if token and self.use_secret:
            headers["api-secret"] = hashlib.sha1(token.encode()).hexdigest()
        elif token:
            params["token"] = token
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                if token and not self.use_secret:
                    self.use_secret = True   # forse è l'API_SECRET: riprova così
                    return self._get(path, params_without_token(params))
                raise NightscoutError(t("err_nightscout_auth")) from e
            if e.code == 404:
                raise NightscoutError(t("err_nightscout_url")) from e
            raise NightscoutError(t("err_http", code=e.code)) from e
        except urllib.error.URLError as e:
            raise NightscoutError(t("err_offline")) from e
        except ValueError as e:   # risposta non JSON: non è un sito Nightscout
            raise NightscoutError(t("err_nightscout_url")) from e

    def fetch(self):
        """Ritorna (misura_corrente, storico): ogni misura è {mgdl, trend, time}."""
        if not self.base_url.startswith(("http://", "https://")):
            raise NightscoutError(t("err_nightscout_url"))
        since = int((time.time() - HISTORY_HOURS * 3600) * 1000)
        raw = self._get("/api/v1/entries/sgv.json",
                        {"count": 2000, "find[date][$gte]": since})
        if not isinstance(raw, list):
            raise NightscoutError(t("err_nightscout_url"))
        history = sorted((parse_entry(e) for e in raw if e.get("sgv") and e.get("date")),
                         key=lambda m: m["time"])
        if not history:
            raise NightscoutError(t("err_nightscout_no_data"))
        return history[-1], history


def params_without_token(params):
    return {k: v for k, v in params.items() if k != "token"}


def parse_entry(e):
    trend = e.get("direction")
    if not trend and isinstance(e.get("trend"), int):
        trend = TREND_NAMES.get(e["trend"])
    return {"mgdl": e["sgv"], "trend": trend, "time": e["date"] / 1000}
