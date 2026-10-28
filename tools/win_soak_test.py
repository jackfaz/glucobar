"""Prova di lunga durata su Windows (workflow soak.yml): GlucoBar resta aperto per giorni,
quindi memoria, handle e oggetti grafici non devono crescere col tempo.

Uso: python tools/win_soak_test.py dist\\GlucoBar\\GlucoBar.exe [minuti]
Avvia GlucoBar con tutti gli elementi, collegato a un sito Nightscout finto che cambia
valore a ogni lettura (anche bassi e molto alti, per far scattare gli avvisi), con
aggiornamento ogni 10 secondi. Ogni 5 minuti cambia tema da terminale, così le finestre
vengono ricreate. Ogni 30 secondi misura il processo; alla fine confronta l'inizio (dopo
due minuti di assestamento) con la fine e scrive i risultati negli avvisi del job.
Esce con 1 se GlucoBar si chiude o se qualcosa cresce oltre i limiti.
"""

import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from http.server import HTTPServer

import psutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_nightscout import FakeNightscout, entry  # noqa: E402

CONFIG_DIR = os.path.join(os.environ["APPDATA"], "GlucoBar")
CONFIG = os.path.join(CONFIG_DIR, "config.json")
LOG = os.path.join(CONFIG_DIR, "glucobar.log")
VALUES = (142, 156, 171, 188, 210, 245, 268, 230, 190, 150, 118, 92, 74, 63, 58, 66, 85, 110)
# crescita massima tra l'inizio (dopo l'assestamento) e la fine
LIMITS = {"memoria privata (MB)": 40, "handle": 300, "oggetti GDI": 150, "oggetti USER": 150}
WARMUP = 120


def notice(title, text, level="notice"):
    print(f"::{level} title={title}::{text}", flush=True)


def gui_objects(pid):
    """(GDI, USER) del processo."""
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)   # QUERY_LIMITED
    try:
        get = ctypes.windll.user32.GetGuiResources
        return get(handle, 0), get(handle, 1)
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def measure(proc):
    gdi, user = gui_objects(proc.pid)
    return {"memoria privata (MB)": proc.memory_info().private / 2 ** 20,
            "handle": proc.num_handles(), "oggetti GDI": gdi, "oggetti USER": user}


def feed(stop):
    """Un valore nuovo ogni 10 secondi, come un sensore molto veloce."""
    n = 0
    while not stop.is_set():
        value = VALUES[n % len(VALUES)]
        trend = "SingleUp" if VALUES[(n + 1) % len(VALUES)] > value else "SingleDown"
        FakeNightscout.state["entries"] = [entry(0, value, trend)] + [
            entry(5 * i, VALUES[(n - i) % len(VALUES)]) for i in range(1, 140)]
        n += 1
        stop.wait(10)


def set_theme(name):
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["theme"] = name
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f)


def main(exe, minutes):
    FakeNightscout.state = {"auth": "public", "queries": [], "entries": []}
    stop = threading.Event()
    threading.Thread(target=feed, args=(stop,), daemon=True).start()
    server = HTTPServer(("127.0.0.1", 0), FakeNightscout)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump({"source": "nightscout", "email": f"http://127.0.0.1:{server.server_port}",
                   "elements": ["taskbar", "tray", "window", "desktop"], "language": "en",
                   "refresh_seconds": 10, "alert_low": True, "alert_high": True,
                   "alerts_note_shown": True, "update_check": False, "theme": "dark"}, f)
    if os.path.exists(LOG):
        os.remove(LOG)

    app = subprocess.Popen([exe])
    proc = psutil.Process(app.pid)
    start = time.monotonic()
    samples, themes = [], 0
    while time.monotonic() - start < minutes * 60:
        time.sleep(30)
        if app.poll() is not None:
            break
        elapsed = time.monotonic() - start
        samples.append((elapsed, measure(proc)))
        if int(elapsed // 300) > themes:   # ogni 5 minuti
            themes += 1
            set_theme("light" if themes % 2 else "dark")
    alive = app.poll() is None
    stop.set()

    with open(LOG, encoding="utf-8") as f:
        log = f.readlines()
    errors = [line.strip() for line in log if "Traceback" in line or "non riuscit" in line]
    alerts = sum("avviso:" in line for line in log)
    data = sum("primo dato" in line for line in log)
    base = next((m for t, m in samples if t >= WARMUP), samples[0][1] if samples else None)
    end = samples[-1][1] if samples else None
    problems = []
    rows = []
    if base and end:
        for key, limit in LIMITS.items():
            growth = end[key] - base[key]
            rows.append(f"{key}: {base[key]:.0f} -> {end[key]:.0f} ({growth:+.0f}, limite +{limit})")
            if growth > limit:
                problems.append(key)
    if not alive:
        problems.append("GlucoBar si è chiuso")
    summary = (f"{minutes} min, {len(samples)} misure, cambi di tema {themes}, avvisi {alerts}, "
               f"letture ok {data > 0}" + " | " + " | ".join(rows))
    notice("Lunga durata", summary, "error" if problems else "notice")
    series = " ".join(f"{t / 60:.0f}m:{m['memoria privata (MB)']:.0f}MB/{m['oggetti GDI']}gdi"
                      for t, m in samples[::4])
    notice("Andamento", series)
    if errors:
        notice("Errori nel log", " | ".join(errors[-8:]), "warning")
    if alive:
        app.kill()
    time.sleep(1)
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60))
