"""Client per Dexcom Share, il servizio di condivisione di Dexcom (G6, G7, ONE+).

API non ufficiale, la stessa usata da Nightscout e pydexcom: può cambiare senza
preavviso. Si entra con l'account Dexcom di chi porta il sensore; nell'app Dexcom
deve essere attiva la condivisione (Share), con almeno un follower.
"""

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import credentials
from .config import save_config
from .i18n import t
from .sources import SourceError

SERVERS = {
    "ous": "https://shareous1.dexcom.com/ShareWebServices/Services",   # fuori dagli USA
    "us": "https://share2.dexcom.com/ShareWebServices/Services",
    "jp": "https://share.dexcom.jp/ShareWebServices/Services",
}
APPLICATION_IDS = {
    "ous": "d89443d2-327c-4a6f-89e5-496bbb0317db",
    "us": "d89443d2-327c-4a6f-89e5-496bbb0317db",
    "jp": "d8665ade-9673-4e27-9ff6-92db4ce13d13",
}
NULL_ID = "00000000-0000-0000-0000-000000000000"   # login non riuscito

# Le risposte più vecchie danno la tendenza come numero
TREND_NAMES = {1: "DoubleUp", 2: "SingleUp", 3: "FortyFiveUp", 4: "Flat",
               5: "FortyFiveDown", 6: "SingleDown", 7: "DoubleDown"}

BAD_CREDENTIALS = {"AccountPasswordInvalid", "SSO_AuthenticatePasswordInvalid",
                   "SSO_AuthenticateAccountNotFound"}
TOO_MANY_ATTEMPTS = {"SSO_AuthenticateMaxAttemptsExceeed", "SSO_AuthenticateMaxAttemptsExceeded"}
SESSION_EXPIRED = {"SessionIdNotFound", "SessionNotValid"}


class DexcomError(SourceError):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


class DexcomShare:
    def __init__(self, cfg, save=save_config, password=None):
        """`password`: per provare credenziali non ancora salvate (glucobar setup)."""
        self.cfg = cfg
        self.save = save
        self.password = password
        self.session_id = None
        self.connection = None   # Dexcom Share non dice quando è stato messo il sensore

    @property
    def region(self):
        return self.cfg.get("dexcom_region") if self.cfg.get("dexcom_region") in SERVERS \
            else "ous"

    @property
    def base_url(self):
        # Permette di puntare a un server di prova (vedi tests/)
        override = os.environ.get("DEXCOM_BASE_URL")
        return (override or SERVERS[self.region]).rstrip("/")

    def _post(self, endpoint, body=None, params=None):
        url = f"{self.base_url}/{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else b""
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                text = r.read().decode("utf-8")
                return json.loads(text) if text else None
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode("utf-8"))
            except Exception:
                payload = {}
            code = payload.get("Code") if isinstance(payload, dict) else None
            if code in BAD_CREDENTIALS:
                raise DexcomError(t("err_credentials"), code) from e
            if code in TOO_MANY_ATTEMPTS:
                raise DexcomError(t("err_dexcom_attempts"), code) from e
            if code in SESSION_EXPIRED:
                raise DexcomError(t("err_session"), code) from e
            if code:
                raise DexcomError(t("err_login", msg=payload.get("Message") or code), code) from e
            raise DexcomError(t("err_http", code=e.code)) from e
        except urllib.error.URLError as e:
            raise DexcomError(t("err_offline")) from e

    def login(self):
        self.session_id = None
        password = self.password or credentials.get_password(self.cfg["email"], "dexcom")
        if not password:
            raise DexcomError(t("err_no_password"))
        app_id = APPLICATION_IDS[self.region]
        account_id = self._post("General/AuthenticatePublisherAccount", {
            "accountName": self.cfg["email"], "password": password, "applicationId": app_id})
        if not account_id or account_id == NULL_ID:
            raise DexcomError(t("err_credentials"))
        session_id = self._post("General/LoginPublisherAccountById", {
            "accountId": account_id, "password": password, "applicationId": app_id})
        if not session_id or session_id == NULL_ID:
            raise DexcomError(t("err_credentials"))
        self.session_id = session_id

    def _readings(self):
        return self._post("Publisher/ReadPublisherLatestGlucoseValues", params={
            "sessionId": self.session_id, "minutes": 1440, "maxCount": 288})

    def fetch(self):
        """Ritorna (misura_corrente, storico): ogni misura è {mgdl, trend, time}."""
        if not self.session_id:
            self.login()
        try:
            raw = self._readings()
        except DexcomError as e:
            if e.code not in SESSION_EXPIRED:
                raise
            self.login()   # sessione scaduta: rifai il login una volta
            raw = self._readings()
        history = sorted((parse_reading(r) for r in raw or []), key=lambda m: m["time"])
        if not history:
            raise DexcomError(t("err_dexcom_no_data"))
        return history[-1], history


def parse_reading(r):
    # "WT": "Date(1691455258000)", millisecondi in UTC
    match = re.search(r"-?\d+", r.get("WT") or r.get("ST") or "")
    trend = r.get("Trend")
    if isinstance(trend, int):
        trend = TREND_NAMES.get(trend)
    return {
        "mgdl": r.get("Value"),
        "trend": trend,
        "time": int(match.group()) / 1000 if match else time.time(),
    }
