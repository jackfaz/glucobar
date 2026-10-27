"""Client per LibreLinkUp, il servizio di condivisione di Abbott.

API non ufficiale: può cambiare senza preavviso.
"""

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from . import credentials
from .config import save_config
from .i18n import t

# TrendArrow di LibreLinkUp -> freccia
TREND_ARROWS = {1: "↓", 2: "↘", 3: "→", 4: "↗", 5: "↑"}


class LibreError(Exception):
    pass


class LibreLinkUp:
    def __init__(self, cfg, save=save_config):
        self.cfg = cfg
        self.save = save
        self.token = None
        self.account_id = None
        self.patient_id = None

    @property
    def base_url(self):
        # Permette di puntare a un server di prova (vedi tests/)
        override = os.environ.get("LLU_BASE_URL")
        if override:
            return override.rstrip("/")
        return f"https://api-{self.cfg['region']}.libreview.io"

    def _headers(self):
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "product": "llu.android",
            "version": self.cfg["app_version"],
            "cache-control": "no-cache",
            "User-Agent": "Mozilla/5.0",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
            h["Account-Id"] = self.account_id
        return h

    def _request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            self.base_url + path, data=data, method=method, headers=self._headers()
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode("utf-8"))
            except Exception:
                payload = None
            if e.code == 401:
                self.token = None
                raise LibreError(t("err_session")) from e
            if payload is not None:
                return payload
            raise LibreError(t("err_http", code=e.code)) from e
        except urllib.error.URLError as e:
            raise LibreError(t("err_offline")) from e

    def login(self):
        self.token = None
        password = credentials.get_password(self.cfg["email"])
        if not password:
            raise LibreError(t("err_no_password"))
        for _ in range(4):
            res = self._request(
                "POST", "/llu/auth/login",
                {"email": self.cfg["email"], "password": password},
            )
            data = res.get("data") or {}
            status = res.get("status")

            # Il server chiede una versione dell'app più recente
            if status == 920 and data.get("minimumVersion"):
                self.cfg["app_version"] = data["minimumVersion"]
                self.save(self.cfg)
                continue

            # Account di un'altra regione: ripeti sul server giusto
            if data.get("redirect") and data.get("region"):
                self.cfg["region"] = data["region"]
                self.save(self.cfg)
                continue

            if status == 2:
                raise LibreError(t("err_credentials"))
            if status == 4 or data.get("step"):
                raise LibreError(t("err_terms"))
            if status != 0 or "authTicket" not in data:
                msg = (res.get("error") or {}).get("message") or f"status {status}"
                raise LibreError(t("err_login", msg=msg))

            self.token = data["authTicket"]["token"]
            # Dalla versione 4.12 l'API vuole lo SHA-256 dell'id utente
            self.account_id = hashlib.sha256(data["user"]["id"].encode()).hexdigest()
            return
        raise LibreError(t("err_redirects"))

    def _get(self, path):
        if not self.token:
            self.login()
        try:
            res = self._request("GET", path)
        except LibreError:
            if self.token:
                raise
            self.login()  # token scaduto: rifai il login una volta
            res = self._request("GET", path)
        if res.get("status") != 0:
            raise LibreError(t("err_unexpected", status=res.get("status")))
        return res["data"]

    def fetch(self):
        """Ritorna (misura_corrente, storico): ogni misura è {mgdl, trend, time}."""
        if not self.patient_id:
            conns = self._get("/llu/connections")
            if not conns:
                raise LibreError(t("err_no_patient"))
            self.patient_id = conns[0]["patientId"]

        data = self._get(f"/llu/connections/{self.patient_id}/graph")
        current = parse_measurement(data["connection"]["glucoseMeasurement"])
        history = [parse_measurement(m) for m in data.get("graphData", [])]
        history.append(current)
        return current, history


def fetch_safely(client):
    """(misura, storico, errore): mai eccezioni, per i thread delle interfacce."""
    try:
        current, history = client.fetch()
        return current, history, None
    except LibreError as e:
        return None, None, str(e)
    except Exception as e:  # risposta in formato imprevisto, ecc.
        return None, None, t("err_generic", msg=e)


def parse_timestamp(m):
    # FactoryTimestamp è in UTC; Timestamp è nell'ora locale del telefono
    for key in ("FactoryTimestamp", "Timestamp"):
        ts = m.get(key)
        if not ts:
            continue
        try:
            dt = datetime.strptime(ts, "%m/%d/%Y %I:%M:%S %p")
        except ValueError:
            continue
        if key == "FactoryTimestamp":
            return dt.replace(tzinfo=timezone.utc).timestamp()
        return dt.timestamp()
    return time.time()


def parse_measurement(m):
    return {
        "mgdl": m.get("ValueInMgPerDl") or m.get("Value"),
        "trend": m.get("TrendArrow"),
        "time": parse_timestamp(m),
    }
