"""Menu dell'icona vicino all'orologio (in GitHub Actions, su Windows).

Uso: python tools/win_tray_test.py run_glucobar.py|GlucoBar.exe [--strict]
Avvia GlucoBar con l'icona e la finestrella, collegato a un Nightscout finto che cambia
valore ogni 10 secondi (aggiornamento ogni 10 s). Apre il menu dell'icona come un clic
destro (il messaggio che Windows manda all'icona), sceglie Show → Small window con il
mouse e controlla che la finestrella sparisca. Lo fa due volte: subito, e restando sul menu
20 secondi prima di scegliere (nel frattempo arrivano letture nuove).
"""

import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from http.server import HTTPServer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_nightscout import FakeNightscout, entry  # noqa: E402
from tools.win_taskbar_test import (click, key, menu_item_center, menus_of,  # noqa: E402
                                    notice, read_config)

user32 = ctypes.windll.user32
CONFIG_DIR = os.path.join(os.environ["APPDATA"], "GlucoBar")
LOG = os.path.join(CONFIG_DIR, "glucobar.log")
WM_USER = 0x0400
WM_RBUTTONUP = 0x0205


def tray_windows(pid):
    """Le finestre nascoste dell'icona (pystray: classe "glucobar<numero>SystemTrayIcon")."""
    found = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def check(hwnd, _):
        owner = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(owner))
        name = ctypes.create_unicode_buffer(128)
        user32.GetClassNameW(ctypes.c_void_p(hwnd), name, 128)
        if owner.value == pid and re.fullmatch(r"glucobar\d+SystemTrayIcon", name.value):
            found.append(hwnd)
        return True
    user32.EnumWindows(proc(check), 0)
    return found


def feed(stop):
    n = 0
    while not stop.is_set():
        FakeNightscout.state["entries"] = [entry(0, 120 + n % 30, "Flat")] + [
            entry(5 * i, 120) for i in range(1, 40)]
        n += 1
        stop.wait(10)


def choose_small_window(app, wait):
    """Menu dell'icona, `wait` secondi fermi su Show, poi Small window. (ok, testo)."""
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    user32.SetCursorPos(sw - 60, sh - 20)
    before = read_config()["elements"]
    user32.AllowSetForegroundWindow(app.pid)
    for hwnd in tray_windows(app.pid):
        user32.PostMessageW(ctypes.c_void_p(hwnd), WM_USER + 11, 0, WM_RBUTTONUP)
    time.sleep(1.0)
    menus = menus_of(app.pid)
    if not menus:
        return False, f"menu non aperto (finestre dell'icona: {len(tray_windows(app.pid))})"
    show, texts = menu_item_center(menus[0], 0, cascade=True)
    if not show:
        key(0x1B, 2)
        return False, f"Show non trovato ({texts})"
    user32.SetCursorPos(*show)
    time.sleep(wait)
    still = bool(menus_of(app.pid))
    click(*show)
    time.sleep(1.0)
    sub = [m for m in menus_of(app.pid) if m not in menus]
    if not sub:
        key(0x1B, 2)
        return False, f"sottomenu non aperto (menu ancora aperto dopo {wait} s: {still})"
    # Show: barra, icona, finestrella, pannello
    where, texts = menu_item_center(sub[0], 2)
    if not where:
        key(0x1B, 3)
        return False, f"Small window non trovata ({texts})"
    click(*where)
    time.sleep(2.0)
    after = read_config()["elements"]
    ok = ("window" in before) != ("window" in after)
    return ok, f"elementi {before} -> {after}"


def main(app_path, strict):
    FakeNightscout.state = {"auth": "public", "queries": [], "entries": [entry(1, 142, "Flat")]}
    stop = threading.Event()
    threading.Thread(target=feed, args=(stop,), daemon=True).start()
    server = HTTPServer(("127.0.0.1", 0), FakeNightscout)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(os.path.join(CONFIG_DIR, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "nightscout", "email": f"http://127.0.0.1:{server.server_port}",
                   "elements": ["tray", "window"], "language": "en", "update_check": False,
                   "refresh_seconds": 10, "tray_hint_shown": True}, f)
    app = subprocess.Popen([sys.executable, app_path] if app_path.endswith(".py") else [app_path])
    time.sleep(10)
    results = []
    for wait in (0.5, 20):
        ok, text = choose_small_window(app, wait)
        results.append(ok)
        notice(f"Menu dell'icona (fermi {wait} s)", f"{'ok' if ok else 'NO'} | {text}")
        time.sleep(2)
    with open(LOG, encoding="utf-8") as f:
        log = f.readlines()
    notice("Log di GlucoBar", " | ".join(line.strip() for line in log[-12:]))
    app.kill()
    stop.set()
    server.shutdown()
    return 1 if strict and not all(results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--strict" in sys.argv))
