"""Prova visiva del valore sulla barra delle applicazioni (in GitHub Actions, su Windows).

Uso: python tools/win_taskbar_test.py dist\\GlucoBar\\GlucoBar.exe [--strict]
Avvia GlucoBar con il solo valore sulla barra, collegato a un sito Nightscout finto
(valore 142, verde), poi ripete le azioni che lo facevano lampeggiare o sparire: aprire e
chiudere un'app, aprire una cartella, cliccare su uno spazio vuoto della barra. Intanto
fotografa il punto del valore ogni ~10-20 ms e conta in quante foto le cifre verdi ci sono.
Risultati e una foto del primo momento in cui manca finiscono negli avvisi del job.
Con --strict esce con 1 se GlucoBar si chiude o se in uno scenario il valore manca in
più del 10% delle foto (qualche fotogramma perso può dipendere dalla macchina della build).
"""

import base64
import ctypes
from ctypes import wintypes
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

from glucobar.config import DEFAULT_CONFIG  # noqa: E402
from glucobar.theme import palette, taskbar_light  # noqa: E402

CONFIG_DIR = os.path.join(os.environ["APPDATA"], "GlucoBar")
LOG = os.path.join(CONFIG_DIR, "glucobar.log")
# il verde "nel range" che GlucoBar usa sopra questa barra (più scuro se la barra è chiara;
# fino alla 0.8.4 era sempre quello chiaro: valgono tutti e due, per provare le vecchie)
_green = palette(DEFAULT_CONFIG, light=taskbar_light()).in_range
GREENS = {tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
          for c in (_green, palette(DEFAULT_CONFIG, light=False).in_range)}


def is_green(pixel):
    return any(all(abs(a - b) < 40 for a, b in zip(pixel, green)) for green in GREENS)
user32 = ctypes.windll.user32


def notice(title, text):
    print(f"::notice title={title}::{text}", flush=True)


def photo_notice(title, img, size=(480, 120)):
    img = img.convert("RGB")
    img.thumbnail(size)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
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
    return sum(is_green(pixel) for pixel in img.getdata())


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
            time.sleep(0.01)

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


def key(code, times=1):
    for _ in range(times):
        user32.keybd_event(code, 0, 0, 0)
        user32.keybd_event(code, 0, 2, 0)
        time.sleep(0.2)


def right_click(x, y):
    user32.SetCursorPos(x, y)
    user32.mouse_event(0x0008, 0, 0, 0, 0)   # destro giù
    user32.mouse_event(0x0010, 0, 0, 0, 0)   # destro su


def menus_of(pid):
    """Menu a comparsa aperti (classe #32768) che appartengono al processo `pid`."""
    found = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def check(hwnd, _):
        name = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(ctypes.c_void_p(hwnd), name, 64)
        owner = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(owner))
        if name.value == "#32768" and owner.value == pid and \
                user32.IsWindowVisible(ctypes.c_void_p(hwnd)):
            found.append(hwnd)
        return True
    user32.EnumWindows(proc(check), 0)
    return found


def windows_of(pid):
    """Finestre visibili di `pid` dall'alto in basso, con la barra come riferimento."""
    found = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def check(hwnd, _):
        owner = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(owner))
        name = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(ctypes.c_void_p(hwnd), name, 64)
        if name.value == "Shell_TrayWnd":
            found.append("BARRA")
        elif owner.value == pid and user32.IsWindowVisible(ctypes.c_void_p(hwnd)):
            rect = wintypes.RECT()
            user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
            style = user32.GetWindowLongW(ctypes.c_void_p(hwnd), -20)
            found.append(f"{name.value} {rect.left},{rect.top},{rect.right},{rect.bottom} "
                         f"ex={style & 0xFFFFFFFF:#x}")
        return True
    user32.EnumWindows(proc(check), 0)
    return found


def read_config():
    with open(os.path.join(CONFIG_DIR, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def menu_item_center(menu_hwnd, index, cascade=False):
    """Centro di una voce del menu a comparsa aperto `menu_hwnd`: la voce `index`, o con
    cascade=True il sottomenu numero `index`. Tk disegna da sé le voci e Windows non ne
    conosce il testo: si contano le posizioni."""
    user32.SendMessageW.restype = ctypes.c_void_p
    user32.GetSubMenu.restype = ctypes.c_void_p
    hmenu = user32.SendMessageW(wintypes.HWND(menu_hwnd), 0x01E1, 0, 0)   # MN_GETHMENU
    count = user32.GetMenuItemCount(ctypes.c_void_p(hmenu))
    if cascade:
        items = [i for i in range(count) if user32.GetSubMenu(ctypes.c_void_p(hmenu), i)]
    else:
        items = list(range(count))
    if index >= len(items):
        return None, f"{count} voci, {len(items)} adatte"
    rect = wintypes.RECT()
    user32.GetMenuItemRect(None, ctypes.c_void_p(hmenu), items[index], ctypes.byref(rect))
    return ((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2), ""


def choose_from_menu(app, rect):
    """Clic destro sul valore, clic su "Size", clic su "Small": come una persona.
    Ritorna il taskbar_scale salvato (0.85 se la scelta ha funzionato)."""
    x0, y0, x1, y1 = rect
    # su una cifra: così vale anche per le versioni in cui il fondo non prende i clic
    img = ImageGrab.grab(bbox=rect, all_screens=True)
    digit = next(((x0 + i % img.width, y0 + i // img.width)
                  for i, pixel in enumerate(img.getdata()) if is_green(pixel)),
                 ((x0 + x1) // 2, (y0 + y1) // 2))
    right_click(*digit)
    time.sleep(1.0)
    menus = menus_of(app.pid)
    if not menus:
        return "menu non aperto"
    # il primo sottomenu del valore sulla barra è Size
    where, texts = menu_item_center(menus[0], 0, cascade=True)
    if not where:
        key(0x1B, 2)
        return f"voce non trovata tra {texts}"
    click(*where)
    time.sleep(1.0)
    first_click = where
    sub = [m for m in menus_of(app.pid) if m not in menus]
    where, texts = menu_item_center(sub[0], 0) if sub else (None, "nessun sottomenu")
    if not where:
        key(0x1B, 3)
        return f"sottomenu senza voci ({texts})"
    click(*where)
    time.sleep(1.5)
    return f"{read_config().get('taskbar_scale')} (clic a {first_click} e {where})"


def big_windows(pid):
    """Finestre visibili di `pid` alte almeno 200 pixel (l'anteprima col grafico)."""
    found = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def check(hwnd, _):
        owner = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(ctypes.c_void_p(hwnd)):
            r = wintypes.RECT()
            user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(r))
            if r.bottom - r.top >= 200:
                found.append((r.left, r.top, r.right, r.bottom))
        return True
    user32.EnumWindows(proc(check), 0)
    return found


def hover_check(app, rect):
    """Un secondo col mouse sul valore: compare il grafico; mouse via: sparisce."""
    x0, y0, x1, y1 = rect
    user32.SetCursorPos(user32.GetSystemMetrics(0) // 2, 200)
    time.sleep(0.8)
    before = set(big_windows(app.pid))   # il pannello sullo sfondo, se c'è
    user32.SetCursorPos((x0 + x1) // 2, (y0 + y1) // 2)
    time.sleep(0.4)
    early = [w for w in big_windows(app.pid) if w not in before]
    time.sleep(1.4)
    shown = [w for w in big_windows(app.pid) if w not in before]
    drawn = green_pixels(ImageGrab.grab(bbox=shown[0], all_screens=True)) if shown else 0
    user32.SetCursorPos(user32.GetSystemMetrics(0) // 2, 200)
    time.sleep(0.8)
    gone = not [w for w in big_windows(app.pid) if w not in before]
    above = bool(shown) and shown[0][3] <= y0
    ok = not early and bool(shown) and above and gone and drawn >= 300
    return (f"grafico col mouse: dopo 0,4 s {'NO' if not early else 'già visibile'}, "
            f"dopo 1,8 s {shown[0] if shown else 'NO'}{' sopra il valore' if above else ''} "
            f"con {drawn} pixel verdi disegnati, "
            f"mouse via: {'sparito' if gone else 'ANCORA LÌ'}"), ok


def window_order():
    order = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(proc(lambda hwnd, _: order.append(hwnd) or True), 0)
    return order


def panel_hwnd(pid):
    """Il pannello sullo sfondo: la finestra di GlucoBar larga almeno 400 pixel."""
    for hwnd in window_order():
        owner = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(owner))
        if owner.value != pid:
            continue
        r = wintypes.RECT()
        user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(r))
        if r.right - r.left >= 400 and r.bottom - r.top >= 250:
            return hwnd
    return None


def panel_on_top_check(app):
    """Pannello "sempre in primo piano": sopra un'app aperta dopo di lui, nascosto con
    un'app a schermo intero, di nuovo visibile quando questa si chiude."""
    panel = panel_hwnd(app.pid)
    if not panel:
        return "pannello: non trovato", False
    subprocess.Popen(["notepad.exe"])
    time.sleep(2.5)
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    other = user32.GetForegroundWindow()
    order = window_order()
    above = panel in order and other in order and order.index(panel) < order.index(other)
    # la stessa app a schermo intero: senza bordi e grande quanto il monitor
    user32.SetWindowLongW(ctypes.c_void_p(other), -16, 0x90000000 - 2 ** 32)   # WS_POPUP|VISIBLE
    user32.SetWindowPos(ctypes.c_void_p(other), None, 0, 0, user32.GetSystemMetrics(0),
                        user32.GetSystemMetrics(1), 0x0020 | 0x0040)
    time.sleep(2.5)
    hidden = not user32.IsWindowVisible(ctypes.c_void_p(panel))
    user32.PostMessageW(ctypes.c_void_p(other), 0x0010, 0, 0)   # WM_CLOSE
    time.sleep(2.5)
    back = bool(user32.IsWindowVisible(ctypes.c_void_p(panel)))
    return (f"pannello in primo piano: sopra l'app {'sì' if above else 'NO'}, "
            f"nascosto a schermo intero {'sì' if hidden else 'NO'}, "
            f"di nuovo visibile {'sì' if back else 'NO'}"), above and hidden and back


def menu_checks(app, rect):
    """Clic destro sulle parti trasparenti del valore: deve aprirsi il menu di GlucoBar,
    non quello della barra. Poi "Update every → 10 s" scelto una volta sola deve bastare."""
    x0, y0, x1, y1 = rect
    points = [(x0 + 3, y0 + 3), (x1 - 3, y0 + 3), (x0 + 3, y1 - 3), (x1 - 3, y1 - 3),
              ((x0 + x1) // 2, y0 + 2)]
    ours = 0
    under = []
    user32.WindowFromPoint.restype = wintypes.HWND
    for x, y in points:
        hwnd = user32.WindowFromPoint(wintypes.POINT(x, y))
        name = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, name, 64)
        owner = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        under.append(f"{name.value}{'*' if owner.value == app.pid else ''}")
        right_click(x, y)
        time.sleep(1.0)
        ours += bool(menus_of(app.pid))
        key(0x1B, 2)   # chiude il menu, qualunque sia
        time.sleep(0.5)
    results = [f"clic destro sul fondo trasparente: menu di GlucoBar {ours}/{len(points)} "
               f"(sotto il mouse: {', '.join(under)}; * = GlucoBar)",
               "finestre dall'alto: " + " / ".join(windows_of(app.pid))]
    first = choose_from_menu(app, rect)
    results.append(f"Size → Small al primo colpo: {first}")
    second = None
    if not str(first).startswith("0.85 "):   # e la seconda volta? (il problema segnalato con la 0.8.4)
        second = choose_from_menu(app, rect)
        results.append(f"al secondo colpo: {second}")
    return results, ours == len(points) and str(first).startswith("0.85 ")


def main(exe, strict):
    FakeNightscout.state = {"auth": "public", "queries": [], "entries": [entry(1, 142, "Flat")]}
    server = HTTPServer(("127.0.0.1", 0), FakeNightscout)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(os.path.join(CONFIG_DIR, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "nightscout", "email": f"http://127.0.0.1:{server.server_port}",
                   "elements": ["taskbar", "desktop"], "desktop_on_top": True,
                   "language": "en"}, f)
    if os.path.exists(LOG):
        os.remove(LOG)

    # anche da sorgente (run_glucobar.py), per provare in fretta senza compilare
    app = subprocess.Popen([sys.executable, exe] if exe.endswith(".py") else [exe])
    time.sleep(10)
    if app.poll() is not None:
        notice("Barra", "GlucoBar si è chiuso all'avvio")
        return 1
    rect = value_rect()
    baseline = green_pixels(ImageGrab.grab(bbox=rect, include_layered_windows=True,
                                           all_screens=True))
    results = [f"valore in {rect}, barra {'chiara' if taskbar_light() else 'scura'}, "
               f"pixel verdi all'inizio: {baseline}"]
    if baseline < 20:
        notice("Barra", f"valore non visibile già all'inizio ({baseline} pixel {_green})")
        with open(LOG, encoding="utf-8") as f:
            notice("Log di GlucoBar", " | ".join(line.strip() for line in f.readlines()[-12:]))
        app.kill()
        return 1 if strict else 0

    watcher = Watcher(rect, max(10, baseline // 3))
    problems = 0
    photos = []   # foto dei momenti in cui il valore manca: dopo il riepilogo, al massimo una
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
        # uno spazio vuoto della barra: un quinto dello schermo da sinistra (prima delle
        # icone, che sulla barra centrata stanno nel mezzo)
        x0, y0, x1, y1 = rect
        click(user32.GetSystemMetrics(0) // 5, (y0 + y1) // 2)

    for name, action in (("apri app", open_notepad), ("chiudi app", close_notepad),
                         ("apri cartella", open_folder), ("chiudi cartella", close_folder),
                         *[(f"clic sulla barra {n}", click_taskbar) for n in range(1, 6)]):
        seen, total, missing = watcher.during(action, 1.5)
        problems += seen < 0.9 * total
        alive = app.poll() is None
        results.append(f"{name}: visibile in {seen}/{total} foto"
                       + ("" if alive else " · GLUCOBAR CHIUSO"))
        if missing is not None and not photos:
            photos.append((f"Manca ({name})", missing))
        if not alive:
            problems += 1
            break

    if app.poll() is None:
        menu_results, menus_ok = menu_checks(app, rect)
        results += menu_results
        problems += not menus_ok
        hover_result, hover_ok = hover_check(app, rect)
        results.append(hover_result)
        problems += not hover_ok
        panel_result, panel_ok = panel_on_top_check(app)
        results.append(panel_result)
        problems += not panel_ok
    notice("Valore sulla barra", " | ".join(results))
    for title, img in photos:
        photo_notice(title, img)
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
