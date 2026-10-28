"""Prova dell'aggiornamento da dentro GlucoBar (nella build, su Windows).

Uso: python tools/win_update_test.py dist-installer\\GlucoBar-Setup-x.y.z.exe
Installa GlucoBar, lo avvia con "installa da solo le nuove versioni" e un GitHub finto
che annuncia la versione 99.0.0 (con l'installer appena compilato e la sua impronta
SHA-256). GlucoBar deve scaricarlo, avviarlo, chiudersi e riaprirsi aggiornato, con le
stesse impostazioni. I risultati finiscono negli avvisi del job; esce con 1 se no.
"""

import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG_DIR = os.path.join(os.environ["APPDATA"], "GlucoBar")
APP_DIR = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "GlucoBar")
LOG = os.path.join(CONFIG_DIR, "glucobar.log")
SILENT = ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/CURRENTUSER", "/NORESTART"]


def notice(title, text, level="notice"):
    print(f"::{level} title={title}::{text}", flush=True)


def glucobar_pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq GlucoBar.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return {int(row[1]) for row in csv.reader(io.StringIO(out)) if len(row) > 1
            and row[0].lower() == "glucobar.exe"}


def serve(installer):
    with open(installer, "rb") as f:
        body = f.read()
    sha = hashlib.sha256(body).hexdigest()

    class Handler(BaseHTTPRequestHandler):
        downloads = 0

        def log_message(self, *args):
            pass

        def do_GET(self):
            port = self.server.server_port
            if self.path == "/latest":
                data = json.dumps({"tag_name": "v99.0.0", "html_url": "https://example.org",
                                   "assets": [{"name": "GlucoBar-Setup-99.0.0.exe",
                                               "browser_download_url":
                                                   f"http://127.0.0.1:{port}/setup.exe",
                                               "digest": f"sha256:{sha}"}]}).encode()
            else:
                Handler.downloads += 1
                data = body
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, Handler


def main(installer):
    results, ok = [], True
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    code = subprocess.run([installer] + SILENT + ["/ELEMENTS=window", "/SENSOR=nightscout",
                                                  "/LANG=en"]).returncode
    results.append(f"installato (codice {code})")
    cfg_path = os.path.join(CONFIG_DIR, "config.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.update(email="https://glucobar-test.invalid", unit="mmol/L", auto_update=True,
               update_check=True, update_checked_at=0)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f)

    server, handler = serve(installer)
    env = dict(os.environ, GLUCOBAR_UPDATE_API=f"http://127.0.0.1:{server.server_port}/latest")
    app = subprocess.Popen([os.path.join(APP_DIR, "GlucoBar.exe")], env=env)
    # controllo dopo un minuto dall'avvio, poi download, installazione e riapertura
    deadline = time.time() + 240
    reopened = set()
    while time.time() < deadline:
        time.sleep(5)
        reopened = glucobar_pids() - {app.pid}
        if app.poll() is not None and reopened:
            break
    with open(LOG, encoding="utf-8") as f:
        log = f.read()
    with open(cfg_path, encoding="utf-8") as f:
        after = json.load(f)
    checks = [
        ("installer scaricato dal GitHub finto", handler.downloads >= 1),
        ("installer avviato da GlucoBar", "avvio l'installer della versione 99.0.0" in log),
        ("vecchia copia chiusa", app.poll() is not None),
        ("GlucoBar riaperto una volta", len(reopened) == 1),
        ("impostazioni rimaste", after.get("unit") == "mmol/L" and after.get("elements") == ["window"]),
    ]
    for name, passed in checks:
        results.append(f"{name}: {'ok' if passed else 'NO'}")
        ok = ok and passed
    notice("Aggiornamento da GlucoBar", " | ".join(results), "notice" if ok else "error")
    if not ok:
        notice("Log di GlucoBar", " | ".join(log.strip().splitlines()[-12:]))

    subprocess.run([os.path.join(APP_DIR, "GlucoBar.exe"), "--quit"])
    subprocess.run([os.path.join(APP_DIR, "unins000.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES",
                    "/NORESTART"])
    time.sleep(2)
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    server.shutdown()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
