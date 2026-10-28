"""Controllo quotidiano dei servizi veri (workflow live-check.yml): legge un dato con gli
account salvati nei secret del repository e dice solo se funziona.

Secret (tutti facoltativi, si controlla solo ciò che c'è):
  LIBRE_EMAIL, LIBRE_PASSWORD              account LibreLinkUp
  DEXCOM_USER, DEXCOM_PASSWORD, DEXCOM_REGION (ous, us, jp; predefinita ous)
  NIGHTSCOUT_URL, NIGHTSCOUT_TOKEN         sito Nightscout (token facoltativo)

Il repository e i log sono pubblici: qui non si scrive mai un valore di glicemia, né
email, nomi o numeri di serie. Solo "ok" con l'età dell'ultima lettura, o l'errore.
Esce con 1 se un servizio non risponde come previsto: GitHub manda un'email.
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from glucobar import i18n  # noqa: E402
from glucobar.config import DEFAULT_CONFIG  # noqa: E402
from glucobar.report import redact  # noqa: E402
from glucobar.sources import make_client  # noqa: E402


def accounts(env):
    """[(nome, cfg, password)] per i servizi con i secret impostati."""
    found = []
    if env.get("LIBRE_EMAIL") and env.get("LIBRE_PASSWORD"):
        found.append(("LibreLinkUp", {"source": "libre", "email": env["LIBRE_EMAIL"]},
                      env["LIBRE_PASSWORD"]))
    if env.get("DEXCOM_USER") and env.get("DEXCOM_PASSWORD"):
        found.append(("Dexcom Share", {"source": "dexcom", "email": env["DEXCOM_USER"],
                                       "dexcom_region": env.get("DEXCOM_REGION") or "ous"},
                      env["DEXCOM_PASSWORD"]))
    if env.get("NIGHTSCOUT_URL"):
        found.append(("Nightscout", {"source": "nightscout", "email": env["NIGHTSCOUT_URL"]},
                      env.get("NIGHTSCOUT_TOKEN") or ""))
    return found


def check(name, cfg, password):
    """(ok, testo da mostrare)."""
    cfg = dict(DEFAULT_CONFIG, **cfg)
    client = make_client(cfg, save=lambda _cfg: None, password=password)
    try:
        current, history = client.fetch()
    except Exception as e:
        return False, f"{name}: errore: {redact(str(e), cfg)}"
    age = int((time.time() - current["time"]) // 60)
    text = f"{name}: ok, ultima lettura {age} min fa, {len(history)} letture di storico"
    if cfg["source"] == "libre" and cfg["app_version"] != DEFAULT_CONFIG["app_version"]:
        # LibreLinkUp ha chiesto una versione più recente dell'app: da aggiornare in config.py
        text += f"; LibreLinkUp chiede la versione {cfg['app_version']} " \
                f"(in config.py c'è {DEFAULT_CONFIG['app_version']})"
    if age > 60:
        text += " (dato vecchio: sensore o telefono spenti?)"
    return True, text


def main():
    i18n.set_language("en")
    found = accounts(os.environ)
    if not found:
        print("::notice title=Live check::nessun secret impostato, niente da controllare")
        return 0
    failed = 0
    for name, cfg, password in found:
        for secret in (cfg["email"], password):
            if secret:
                print(f"::add-mask::{secret}")
        ok, text = check(name, cfg, password)
        failed += not ok
        print(f"::{'notice' if ok else 'error'} title=Live check::{text}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
