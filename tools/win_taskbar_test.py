"""Prova visiva del valore sulla barra delle applicazioni (in GitHub Actions, su Windows).

Uso: python tools/win_taskbar_test.py dist\\GlucoBar\\GlucoBar.exe [--strict]
Avvia GlucoBar con il solo valore sulla barra, collegato a un sito Nightscout finto
(valore 142, verde), poi ripete le azioni che lo facevano lampeggiare o sparire: aprire e
chiudere un'app, aprire una cartella, cliccare su uno spazio vuoto della barra. Intanto
fotografa il punto del valore ogni ~50 ms e conta in quante foto le cifre verdi ci sono.
Risultati e una foto del primo momento in cui manca finiscono negli avvisi del job.
Con --strict esce con 1 se in qualche foto il valore non c'è.
"""

import base64
import ctypes
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from http.server import HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_nightscout import FakeNightscout, entry  # noqa: E402

ctypes.windll.shcore.SetProcessDpiAwareness(1)   # pixel reali, come GlucoBar
from PIL import ImageGrab  # noqa: E402  (dopo la DPI awareness)

CONFIG_DIR = os.path.join(os.environ["APPDATA"], "GlucoBar")
LOG = os.path.join(CONFIG_DIR, "glucobar.log")
GREEN = (62, 207, 110)
user32 = ctypes.windll.user32


def notice(title, text):
    print(f"::notice title={title}::{text}", flush=True)


def photo_notice(title, img):
    img = img.copy()
    img.thumbnail((600, 300))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    data = base64.b64encode(buf.getvalue()).decode()
    chunks = [data[i:i + 4000] for i in range(0, len(data), 4000)]
    for n, chunk in enumerate(chunks, 1):
        notice(f"{title} {n}/{len(chunks)}", chunk)


def value_rect():
    """Dove GlucoBar ha messo il valore: l'ultima riga "-> valore in WxH+X+Y" del log."""
    with open(LOG, encoding="utf-8") as f:
        found = re.findall(r"valore in (\d+)x(\d+)\+(-?\d+)\+(-?\d+)", f.read())
    w, h, x, y = map(int, found[-1])
    return x, y, x + w, y + h


def green_pixels(img):
    count = 0
    for r, g, b in img.getdata():
        if abs(r - GREEN[0]) < 40 and abs(g - GREEN[1]) < 40 and abs(b - GREEN[2]) < 40:
            count += 1
    return count


class Watcher:
    """Fotografa il valore di continuo mentre si fanno le azioni."""

    def __init__(self, rect, threshold):
        self.rect, self.threshold = rect, threshold
        self.samples = []      # (secondi, visibile)
        self.first_missing = None
        self._stop = threading.Event()

    def run(self):
        start = time.monotonic()
        while not self._stop.is_set():
            img = ImageGrab.grab(bbox=self.rect, include_layered_windows=True, all_screens=True)
            visible = green_pixels(img) >= self.threshold
            self.samples.append((time.monotonic() - start, visible))
            if not visible and self.first_missing is None:
                # più contesto: un po' di barra intorno al valore
                x0, y0, x1, y1 = self.rect
                self.first_missing = ImageGrab.grab(
                    bbox=(x0 - 200, y0 - 40, x1 + 200, y1), include_layered_windows=True,
                    all_screens=True)
            time.sleep(0.03)

    def during(self, action, seconds):
        self.samples, self.first_missing = [], None
        self._stop.clear()
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        try:
            action()
            time.sleep(seconds)
        finally:
            self._stop.set()
            thread.join()
        seen = sum(v for _, v in self.samples)
        return seen, len(self.samples), self.first_missing


def click(x, y):
    user32.SetCursorPos(x, y)
    user32.mouse_event(0x0002, 0, 0, 0, 0)   # sinistro giù
    user32.mouse_event(0x0004, 0, 0, 0, 0)   # sinistro su


def main(exe, strict):
    FakeNightscout.state = {"auth": "public", "queries": [], "entries": [entry(1, 142, "Flat")]}
    server = HTTPServer(("127.0.0.1", 0), FakeNightscout)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(os.path.join(CONFIG_DIR, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "nightscout", "email": f"http://127.0.0.1:{server.server_port}",
                   "elements": ["taskbar"], "language": "en"}, f)
    if os.path.exists(LOG):
        os.remove(LOG)

    app = subprocess.Popen([exe])
    time.sleep(10)
    if app.poll() is not None:
        notice("Barra", "GlucoBar si è chiuso all'avvio")
        return 1
    rect = value_rect()
    baseline = green_pixels(ImageGrab.grab(bbox=rect, include_layered_windows=True,
                                           all_screens=True))
    notice("Barra", f"valore in {rect}, pixel verdi all'inizio: {baseline}")
    photo_notice("Valore all'inizio", ImageGrab.grab(
        bbox=(rect[0] - 200, rect[1] - 40, rect[2] + 200, rect[3]),
        include_layered_windows=True, all_screens=True))
    if baseline < 20:
        notice("Barra", "valore non visibile già all'inizio: prova non significativa")
        app.kill()
        return 1 if strict else 0

    watcher = Watcher(rect, max(10, baseline // 3))
    problems = 0
    apps = []

    def open_notepad():
        apps.append(subprocess.Popen(["notepad.exe"]))

    def close_notepad():
        apps.pop().kill()

    def open_folder():
        subprocess.Popen(["explorer.exe", os.environ.get("USERPROFILE", "C:\\")])

    def close_folder():
        # solo la finestra della cartella: explorer.exe è anche la barra delle applicazioni
        hwnd = user32.FindWindowW("CabinetWClass", None)
        if hwnd:
            user32.PostMessageW(hwnd, 0x0010, 0, 0)   # WM_CLOSE

    def click_taskbar():
        # uno spazio vuoto della barra: a metà tra l'inizio e il valore
        x0, y0, x1, y1 = rect
        click(x0 // 2, (y0 + y1) // 2)

    for name, action in (("apri app", open_notepad), ("chiudi app", close_notepad),
                         ("apri cartella", open_folder), ("chiudi cartella", close_folder),
                         ("clic sulla barra", click_taskbar),
                         ("clic sulla barra 2", click_taskbar)):
        seen, total, missing = watcher.during(action, 2.0)
        ok = seen == total
        problems += not ok
        alive = app.poll() is None
        notice("Barra", f"{name}: visibile in {seen}/{total} foto"
                        + ("" if alive else " · GLUCOBAR CHIUSO"))
        if missing is not None:
            photo_notice(f"Manca ({name})", missing)
        if not alive:
            problems += 1
            break

    with open(LOG, encoding="utf-8") as f:
        tail = [line.strip() for line in f.readlines()[-12:]]
    notice("Log di GlucoBar", " | ".join(tail))
    if app.poll() is None:
        app.kill()
    time.sleep(1)
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)   # i test dopo partono da zero
    return 1 if (strict and problems) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--strict" in sys.argv))
