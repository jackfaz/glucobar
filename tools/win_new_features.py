"""Le novità della 0.10 su Windows vero (workflow screenshots.yml): più persone sulla
barra con il soprannome, stima della tendenza sul pannello, promemoria, ponte locale.

Uso: python tools/win_new_features.py cartella_di_uscita
Avvia GlucoBar da sorgente collegato a un LibreLinkUp finto con tre persone (due
mostrate insieme), controlla i risultati e salva le foto nella cartella. Esce con 1 se
qualcosa non va; i risultati sono negli avvisi del job.
"""

import ctypes
import json
import os
import shutil
import sys
import threading
import time
import urllib.request
from datetime import datetime, timedelta
from http.server import HTTPServer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_librelinkup import FakeLibreView  # noqa: E402

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "screenshots")
user32 = ctypes.windll.user32
PORT = 17581


def notice(title, text, level="notice"):
    print(f"::{level} title={title}::{text}", flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    FakeLibreView.state = {"logins": 0, "redirect": False, "redirected": False, "terms": False}
    server = HTTPServer(("127.0.0.1", 0), FakeLibreView)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.environ["LLU_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"

    from glucobar.taskbar import all_taskbars, enable_dpi_awareness, window_rect
    enable_dpi_awareness()
    from glucobar import config, credentials, reminders
    shutil.rmtree(config.CONFIG_DIR, ignore_errors=True)
    sw = user32.GetSystemMetrics(0)
    bar = window_rect(all_taskbars()[0])
    due = (datetime.now() - timedelta(minutes=1)).strftime("%H:%M")
    reminder = reminders.new("Pick up medicines at the pharmacy", "daily", at=due)
    reminder["created"] = time.time() - 86400
    later = reminders.new("Long-acting insulin", "weekly", at="22:00", days=[0, 3, 5])
    cfg = config.load_config()
    cfg.update(source="libre", email="a@b.c", app_version="4.20.0", language="en",
               elements=["taskbar", "window", "desktop"], update_check=False, theme="dark",
               people_shown=["p2"], nicknames={"p1": "Anna", "p2": "Luca"},
               predict=True, predict_ack=True, desktop_hours=3, desktop_alpha=1.0,
               desktop_x=sw - 560, desktop_y=bar[1] - 360, desktop_w=540, desktop_h=330,
               window_x=sw - 800, window_y=bar[1] - 200,
               bridge_http=True, bridge_port=PORT, reminders=[reminder, later])
    config.save_config(cfg)
    credentials.set_password("a@b.c", "segreta", "libre")
    from glucobar.i18n import set_language
    set_language("en")
    from glucobar.controller import Controller
    from glucobar.notify import Toast
    from PIL import ImageGrab

    ctl = Controller(config.load_config())
    problems = []

    def grab(name, box=None):
        img = ImageGrab.grab(bbox=box, all_screens=True, include_layered_windows=True)
        img.save(os.path.join(OUT, f"{name}.png"))
        notice("Screenshot", f"{name}.png {img.size}")

    def frame(win):
        x, y = win.winfo_rootx(), win.winfo_rooty()
        return x - 8, y - 32, x + win.winfo_width() + 8, y + win.winfo_height() + 8

    def check(name, ok, text):
        notice(f"Novità: {name}", f"{'ok' if ok else 'NO'} | {text}", "notice" if ok else "error")
        if not ok:
            problems.append(name)

    def step1():
        # due persone sulla barra
        tb = ctl.views["taskbar"]
        texts = [lbl.cget("text") for labels in tb.extra for lbl in labels]
        check("persone", len(ctl.others) == 1 and "Luca" in " ".join(texts),
              f"altre={[(o['label'], o['current']['mgdl']) for o in ctl.others]} barra={texts} "
              f"principale={tb.value_lbl.cget('text')} {tb.info_lbl.cget('text')}")
        x0, y0, x1, y1 = tb.value_rect()
        grab("taskbar-people", (max(0, x0 - 160), bar[1], min(sw, x1 + 160), bar[3]))
        # stima sul pannello
        panel = ctl.views["desktop"]
        pred = panel.prediction()
        check("stima", pred is not None,
              f"pendenza={pred and round(pred['slope'], 2)} punti={pred and pred['points'][-1]}")
        grab("panel-estimate", frame(panel.root))
        grab("elements-people", (sw - 820, bar[1] - 420, sw, bar[3]))
        # promemoria scaduto: il messaggio è arrivato
        titles = [toast.win.winfo_children() and toast for toast in Toast.open]
        check("promemoria", bool(Toast.open), f"messaggi aperti={len(titles)}")
        if Toast.open:
            boxes = [frame(toast.win) for toast in Toast.open]
            grab("reminder-toast", (min(b[0] for b in boxes) - 10, min(b[1] for b in boxes) - 10,
                                    sw, max(b[3] for b in boxes) + 10))
        # ponte: lo legge un altro programma, da un altro thread
        threading.Thread(target=read_bridge, daemon=True).start()
        ctl.root.after(2500, step2)

    def read_bridge():
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/v1/people", timeout=5) as r:
                people = json.loads(r.read())
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/v1/entries.json?count=2",
                                        timeout=5) as r:
                entries = json.loads(r.read())
            check("ponte", len(people) == 2 and entries and entries[0]["sgv"] == 142,
                  f"persone={[(p['name'], p['value'], p['state']) for p in people]} "
                  f"nightscout={[e['sgv'] for e in entries]}")
        except Exception as e:
            check("ponte", False, repr(e))

    def step2():
        for toast in list(Toast.open):
            toast.close()
        ctl.open_reminders()
        ctl.root.after(1500, step3)

    def step3():
        from glucobar.reminders_ui import RemindersWindow
        win = RemindersWindow.current.win
        grab("reminders", frame(win))
        RemindersWindow.current.close()
        from glucobar.settings import SettingsWindow
        SettingsWindow.open(ctl, "connect")
        ctl.root.after(1500, step4)

    def step4():
        from glucobar.settings import SettingsWindow
        win = SettingsWindow.current.win
        grab("settings-connect", frame(win))
        SettingsWindow.open(ctl, "values")
        ctl.root.after(800, lambda: (grab("settings-values", frame(win)), step5()))

    def step5():
        from glucobar.settings import SettingsWindow
        SettingsWindow.open(ctl, "general")
        win = SettingsWindow.current.win
        ctl.root.after(800, lambda: (grab("settings-general", frame(win)),
                                     ctl.root.after(500, ctl.quit)))

    ctl.root.after(8000, step1)
    ctl.run()
    with open(config.LOG_PATH, encoding="utf-8") as f:
        notice("Log di GlucoBar", " | ".join(line.strip() for line in f.readlines()[-12:]))
    server.shutdown()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
