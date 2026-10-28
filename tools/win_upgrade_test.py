"""Prove di aggiornamento su Windows (nella build).

Uso: python tools/win_upgrade_test.py dist-installer\\GlucoBar-Setup-x.y.z.exe [precedente.exe]

1. Aggiornamento sopra l'ultima release (se `precedente.exe` c'è): installata e aperta,
   con impostazioni cambiate e una password salvata, poi la nuova si installa sopra in
   silenzio, come fa winget. Devono restare impostazioni, elementi, lingua, account e
   password, e GlucoBar deve riaprirsi una volta sola, aggiornato.
2. Aggiornamento da dentro GlucoBar: GlucoBar installato trova la versione 99.0.0 su un
   GitHub finto, scarica l'installer appena compilato, ne controlla l'impronta, lo avvia,
   si chiude e si riapre con le stesse impostazioni.

Ogni attesa ha un limite e l'output dei processi non resta collegato al job (GlucoBar
riaperto dall'installer terrebbe il passo aperto). Risultati negli avvisi del job.
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

# gli avvisi del job in UTF-8: la console di Windows (cp1252) non stampa frecce e simili
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONFIG_DIR = os.path.join(os.environ["APPDATA"], "GlucoBar")
CONFIG = os.path.join(CONFIG_DIR, "config.json")
LOG = os.path.join(CONFIG_DIR, "glucobar.log")
APP_DIR = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "GlucoBar")
EXE = os.path.join(APP_DIR, "GlucoBar.exe")
SILENT = ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/CURRENTUSER", "/NORESTART"]
QUIET = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
         "stderr": subprocess.DEVNULL}
TARGET = "GlucoBar:Nightscout"


def notice(title, text, level="notice"):
    print(f"::{level} title={title}::{text}", flush=True)


def run(args, timeout=300):
    """Codice di uscita, o "timeout"."""
    try:
        return subprocess.run(args, timeout=timeout, **QUIET).returncode
    except subprocess.TimeoutExpired:
        return "timeout"


def start(args, env=None):
    return subprocess.Popen(args, env=env, creationflags=0x00000008, **QUIET)   # DETACHED


def pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq GlucoBar.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return {int(row[1]) for row in csv.reader(io.StringIO(out))
            if len(row) > 1 and row[0].lower() == "glucobar.exe"}


def wait_for(condition, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(2)
    return condition()


def read_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def write_config(**changes):
    cfg = read_config()
    cfg.update(changes)
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f)


def exe_version():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          f"(Get-Item '{EXE}').VersionInfo.ProductVersion"],
                         capture_output=True, text=True, timeout=60).stdout
    return out.strip()


def credential_saved():
    out = subprocess.run(["cmdkey", f"/list:{TARGET}"], capture_output=True, text=True).stdout
    return "glucobar-test.invalid" in out


def log_tail(lines=10):
    try:
        with open(LOG, encoding="utf-8") as f:
            return " | ".join(line.strip() for line in f.readlines()[-lines:])
    except OSError:
        return "(nessun log)"


def clean():
    if os.path.exists(EXE):
        run([EXE, "--quit"], 30)
    for pid in pids():
        run(["taskkill", "/F", "/PID", str(pid)], 30)
    if os.path.exists(os.path.join(APP_DIR, "unins000.exe")):
        run([os.path.join(APP_DIR, "unins000.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES",
             "/NORESTART"], 120)
    run(["cmdkey", f"/delete:{TARGET}"], 30)
    time.sleep(2)
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)


def report(title, checks, extra=""):
    ok = all(passed for _name, passed in checks)
    text = " | ".join(f"{name}: {'ok' if passed else 'NO'}" for name, passed in checks)
    notice(title, text + (f" | {extra}" if extra else ""), "notice" if ok else "error")
    if not ok:
        notice(f"{title}: log di GlucoBar", log_tail())
    return ok


def upgrade_over_previous(new, previous, version):
    clean()
    code = run([previous] + SILENT + ["/ELEMENTS=taskbar,window", "/SENSOR=nightscout",
                                      "/LANG=it"])
    if code != 0:
        return report("Aggiornamento sopra la release precedente",
                      [(f"installazione della precedente (codice {code})", False)])
    old = exe_version()
    write_config(email="https://glucobar-test.invalid", unit="mmol/L", low=80,
                 elements=["window", "desktop"], language="fr")
    run(["cmdkey", f"/generic:{TARGET}", "/user:https://glucobar-test.invalid", "/pass:token"])
    start([EXE])
    started = wait_for(lambda: len(pids()) == 1, 30)
    before = pids()
    code = run([new] + SILENT)
    reopened = wait_for(lambda: len(pids()) == 1 and pids() != before, 60)
    after, cfg = pids(), read_config()
    checks = [
        ("precedente aperta", started),
        (f"installazione silenziosa (codice {code})", code == 0),
        (f"GlucoBar.exe aggiornato ({old} -> {exe_version()})", exe_version() == version),
        (f"riaperto una volta ({len(after)} processi)", reopened),
        ("impostazioni", cfg.get("unit") == "mmol/L" and cfg.get("low") == 80),
        (f"elementi {cfg.get('elements')}", cfg.get("elements") == ["window", "desktop"]),
        (f"lingua {cfg.get('language')}", cfg.get("language") == "fr"),
        ("account", cfg.get("source") == "nightscout"
         and cfg.get("email") == "https://glucobar-test.invalid"),
        ("password", credential_saved()),
    ]
    return report("Aggiornamento sopra la release precedente", checks)


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


def update_from_glucobar(new):
    clean()
    code = run([new] + SILENT + ["/ELEMENTS=window", "/SENSOR=nightscout", "/LANG=en"])
    write_config(email="https://glucobar-test.invalid", unit="mmol/L", auto_update=True,
                 update_check=True, update_checked_at=0)
    server, handler = serve(new)
    env = dict(os.environ, GLUCOBAR_UPDATE_API=f"http://127.0.0.1:{server.server_port}/latest")
    app = start([EXE], env)
    # il controllo parte un minuto dopo l'avvio; poi download, installazione, riapertura
    done = wait_for(lambda: app.poll() is not None and len(pids() - {app.pid}) == 1, 240)
    with open(LOG, encoding="utf-8") as f:
        log = f.read()
    cfg = read_config()
    server.shutdown()
    checks = [
        (f"installato (codice {code})", code == 0),
        ("installer scaricato dal GitHub finto", handler.downloads >= 1),
        ("installer avviato da GlucoBar", "avvio l'installer della versione 99.0.0" in log),
        ("vecchia copia chiusa e nuova aperta", done),
        ("impostazioni", cfg.get("unit") == "mmol/L" and cfg.get("elements") == ["window"]),
    ]
    return report("Aggiornamento da GlucoBar", checks)


def main(new, previous=None):
    version = os.path.basename(new)[len("GlucoBar-Setup-"):-len(".exe")]
    ok = True
    try:
        if previous and os.path.exists(previous):
            ok = upgrade_over_previous(new, previous, version) and ok
        else:
            notice("Aggiornamento sopra la release precedente", "nessuna release da scaricare")
        ok = update_from_glucobar(new) and ok
    finally:
        clean()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
