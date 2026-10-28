"""Valore sulla barra con la barra nascosta automaticamente e in alto, a sinistra, a destra
(workflow edges-test.yml, su Windows 11 e Windows 10).

Uso: python tools/win_taskbar_edges_test.py run_glucobar.py|GlucoBar.exe [--strict]
- "Nascondi automaticamente la barra": con il mouse lontano il valore deve sparire, con
  il mouse sul bordo (barra di nuovo visibile) deve ricomparire sopra la barra.
- Barra in alto, a sinistra, a destra, in basso (StuckRects3 + riavvio di Esplora risorse;
  Windows 11 accetta solo il basso): il valore deve stare dentro la barra.
Per ogni caso scrive negli avvisi del job dove sono la barra e il valore.
"""

import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import winreg
from ctypes import wintypes
from http.server import HTTPServer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_nightscout import FakeNightscout, entry  # noqa: E402

ctypes.windll.shcore.SetProcessDpiAwareness(1)
user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
CONFIG_DIR = os.path.join(os.environ["APPDATA"], "GlucoBar")
LOG = os.path.join(CONFIG_DIR, "glucobar.log")
STUCK = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3"
EDGES = {0: "left", 1: "top", 2: "right", 3: "bottom"}


class APPBARDATA(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND),
                ("uCallbackMessage", wintypes.UINT), ("uEdge", wintypes.UINT),
                ("rc", wintypes.RECT), ("lParam", wintypes.LPARAM)]


def appbar(message, lparam=0):
    data = APPBARDATA(cbSize=ctypes.sizeof(APPBARDATA))
    data.hWnd = user32.FindWindowW("Shell_TrayWnd", None)
    data.lParam = lparam
    result = shell32.SHAppBarMessage(message, ctypes.byref(data))
    return result, data


def notice(title, text, level="notice"):
    print(f"::{level} title={title}::{text}", flush=True)


def rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def taskbar():
    """Rettangoli di barra, Start e area di notifica, e se la barra è visibile."""
    tb = user32.FindWindowW("Shell_TrayWnd", None)
    user32.FindWindowExW.restype = wintypes.HWND
    start = user32.FindWindowExW(tb, None, "Start", None)
    tray = user32.FindWindowExW(tb, None, "TrayNotifyWnd", None)
    _r, pos = appbar(5)   # ABM_GETTASKBARPOS
    return {"bar": rect(tb), "start": rect(start) if start else None,
            "tray": rect(tray) if tray else None, "visible": bool(user32.IsWindowVisible(tb)),
            "edge": EDGES.get(pos.uEdge, pos.uEdge),
            "autohide": bool(appbar(4)[0] & 1)}   # ABM_GETSTATE


def value_window(pid):
    """(rettangolo, visibile) della finestra del valore di GlucoBar (piccola)."""
    found = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def check(hwnd, _):
        owner = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(owner))
        name = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(ctypes.c_void_p(hwnd), name, 64)
        if owner.value == pid and name.value == "TkTopLevel":
            r = rect(ctypes.c_void_p(hwnd))
            if 0 < r[2] - r[0] <= 400 and 0 < r[3] - r[1] <= 200:
                found.append((r, bool(user32.IsWindowVisible(ctypes.c_void_p(hwnd)))))
        return True
    user32.EnumWindows(proc(check), 0)
    return found[0] if found else (None, False)


def inside(inner, outer, slack=2):
    return (inner and outer and inner[0] >= outer[0] - slack and inner[1] >= outer[1] - slack
            and inner[2] <= outer[2] + slack and inner[3] <= outer[3] + slack)


def set_autohide(on):
    appbar(10, 1 if on else 2)   # ABM_SETSTATE: ABS_AUTOHIDE / ABS_ALWAYSONTOP
    time.sleep(2)


def set_edge(edge):
    """Barra su un altro bordo: byte 12 di StuckRects3, poi Esplora risorse riavviato."""
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STUCK, 0,
                        winreg.KEY_READ | winreg.KEY_WRITE) as key:
        data = bytearray(winreg.QueryValueEx(key, "Settings")[0])
        data[12] = edge
        winreg.SetValueEx(key, "Settings", 0, winreg.REG_BINARY, bytes(data))
    subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen(["explorer.exe"])
    time.sleep(10)


def main(app_path, strict):
    FakeNightscout.state = {"auth": "public", "queries": [], "entries": [entry(1, 142, "Flat")]}
    server = HTTPServer(("127.0.0.1", 0), FakeNightscout)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(os.path.join(CONFIG_DIR, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "nightscout", "email": f"http://127.0.0.1:{server.server_port}",
                   "elements": ["taskbar"], "language": "en", "update_check": False}, f)
    app = subprocess.Popen([sys.executable, app_path] if app_path.endswith(".py") else [app_path])
    time.sleep(10)
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    problems = 0

    def case(name, ok, extra=""):
        nonlocal problems
        problems += not ok
        info = taskbar()
        value, visible = value_window(app.pid)
        notice(f"Bordo: {name}", f"{'ok' if ok else 'NO'} | barra {info} | valore {value} "
                                 f"visibile={visible} {extra}", "notice" if ok else "error")

    # --- nascondi automaticamente ---
    set_autohide(True)
    user32.SetCursorPos(sw // 2, sh // 2)
    time.sleep(3)
    value, visible = value_window(app.pid)
    case("auto-hide (barra nascosta)", not visible)
    # mouse sul bordo, con movimenti veri: SetCursorPos da solo non fa ricomparire la barra
    for y in range(sh - 40, sh, 4):
        user32.mouse_event(0x8001, (sw // 2) * 65535 // sw, y * 65535 // sh, 0, 0)
        time.sleep(0.05)
    time.sleep(2.5)
    value, visible = value_window(app.pid)
    bar = taskbar()["bar"]
    case("auto-hide (barra mostrata)", visible and inside(value, bar))
    user32.SetCursorPos(sw // 2, sh // 2)
    set_autohide(False)
    time.sleep(2)

    # --- bordi ---
    for edge in (1, 0, 2, 3):
        set_edge(edge)
        info = taskbar()
        if info["edge"] != EDGES[edge]:
            notice(f"Bordo: {EDGES[edge]}", f"Windows non lo permette (barra {info})")
            continue
        time.sleep(3)
        value, visible = value_window(app.pid)
        case(EDGES[edge], visible and inside(value, info["bar"]))
        if edge != 3:   # nascosta automaticamente anche su questo bordo
            set_autohide(True)
            user32.SetCursorPos(sw // 2, sh // 2)
            time.sleep(3)
            value, visible = value_window(app.pid)
            case(f"{EDGES[edge]} auto-hide", not visible)
            set_autohide(False)

    with open(LOG, encoding="utf-8") as f:
        notice("Log di GlucoBar", " | ".join(line.strip() for line in f.readlines()[-14:]))
    app.kill()
    server.shutdown()
    return 1 if strict and problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--strict" in sys.argv))
