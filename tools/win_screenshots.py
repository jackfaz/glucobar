"""Screenshot di GlucoBar su Windows, in inglese, per README e post (workflow screenshots.yml).

Uso: python tools/win_screenshots.py cartella_di_uscita
Avvia GlucoBar da sorgente con tutti gli elementi, collegato a un sito Nightscout finto
con 12 ore di letture realistiche, e fotografa: barra, finestrella e pannello (tema
scuro, chiaro, colori per daltonici, colori scelti a mano), menu col clic destro,
finestra Impostazioni, messaggi (avviso, sensore, nuova versione).
"""

import ctypes
import math
import os
import shutil
import sys
import threading
import time
from http.server import HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_nightscout import FakeNightscout  # noqa: E402

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "screenshots")
user32 = ctypes.windll.user32


def readings():
    """12 ore di valori plausibili (una colazione, un pranzo), l'ultimo 142 in salita."""
    now = time.time()
    entries = []
    for i in range(0, 145):
        hours = i * 5 / 60
        value = (118 + 38 * math.exp(-((hours - 3.2) ** 2) / 0.8)
                 + 70 * math.exp(-((hours - 7.5) ** 2) / 1.1)
                 - 30 * math.exp(-((hours - 10.5) ** 2) / 0.5) + 6 * math.sin(i / 2.3))
        if i == 0:
            value = 142
        entries.append({"_id": f"id{i}", "type": "sgv", "sgv": int(value),
                        "direction": "FortyFiveUp" if i == 0 else "Flat",
                        "date": int((now - i * 300 - 60) * 1000)})
    return entries


def main():
    os.makedirs(OUT, exist_ok=True)
    FakeNightscout.state = {"auth": "public", "queries": [], "entries": readings()}
    server = HTTPServer(("127.0.0.1", 0), FakeNightscout)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    from glucobar.taskbar import all_taskbars, enable_dpi_awareness, window_rect
    enable_dpi_awareness()
    from glucobar import config
    shutil.rmtree(config.CONFIG_DIR, ignore_errors=True)
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    panel_w, panel_h = 540, 330
    cfg = config.load_config()
    cfg.update(source="nightscout", email=f"http://127.0.0.1:{server.server_port}",
               elements=["taskbar", "tray", "window", "desktop"], language="en",
               update_check=False, theme="dark", tray_promoted=True, tray_hint_shown=True,
               desktop_x=sw - panel_w - 280, desktop_y=60, desktop_w=panel_w, desktop_h=panel_h,
               window_x=sw - 240, window_y=60)
    config.save_config(cfg)
    from glucobar.i18n import set_language
    set_language("en")
    from glucobar.controller import Controller
    from PIL import ImageGrab

    ctl = Controller(config.load_config())
    bar = window_rect(all_taskbars()[0])

    def grab(name, box=None):
        img = ImageGrab.grab(bbox=box, all_screens=True, include_layered_windows=True)
        img.save(os.path.join(OUT, f"{name}.png"))
        print(f"::notice title=Screenshot::{name}.png {img.size}", flush=True)

    def frame(win):
        """Rettangolo della finestra con la cornice di Windows."""
        return window_rect(user32.GetParent(win.winfo_id()))

    elements_box = (sw - panel_w - 300, 40, sw - 20, 60 + panel_h + 20)
    taskbar_box = (max(0, bar[2] - 620), bar[1], bar[2], bar[3])

    def popup_menu(view, name, after):
        """tk_popup blocca il ciclo di Tk finché il menu è aperto: la foto la scatta un
        thread, che poi chiude il menu con Esc."""
        x, y = view.root.winfo_rootx() + 30, view.root.winfo_rooty() + 30

        def shoot():
            time.sleep(1.5)
            grab(name, (x - 20, y - 20, min(sw, x + 460), min(sh, y + 520)))
            user32.keybd_event(0x1B, 0, 0, 0)
            user32.keybd_event(0x1B, 0, 2, 0)
        threading.Thread(target=shoot, daemon=True).start()
        view.menu.tk_popup(x, y)
        ctl.root.after(800, after)

    def restyle(**changes):
        ctl.cfg.update(changes)
        config.save_config(ctl.cfg)
        ctl.restyle()

    def toasts():
        ctl.notify(ctl_t("alert_title"), ctl_t("alert_low", v="64 mg/dL", n=0), timeout=120)
        ctl.notify(ctl_t("sensor_msg_title"), ctl_t("sensor_stopped", sn="0M00A1B2C3D", d=0),
                   actions=[(ctl_t("replace_open"), lambda: None)])
        ctl.notify(ctl_t("update_title"), ctl_t("update_text", v="0.9.1"),
                   actions=[(ctl_t("update_install"), lambda: None),
                            (ctl_t("update_notes"), lambda: None)])

    from glucobar.i18n import t as ctl_t
    from glucobar.settings import SettingsWindow
    steps = [
        (8000, lambda: (grab("desktop-dark"), grab("elements-dark", elements_box),
                        grab("taskbar", taskbar_box))),
        (500, lambda: popup_menu(ctl.views["window"], "menu", next_step)),
        (None, lambda: ctl.open_settings()),
        (2000, lambda: grab("settings", frame(SettingsWindow.current.win))),
        (500, lambda: SettingsWindow.current.close()),
        (500, lambda: restyle(theme="light")),
        (2500, lambda: grab("elements-light", elements_box)),
        (500, lambda: restyle(theme="dark", palette="colorblind")),
        (2500, lambda: (grab("elements-colorblind", elements_box),
                        grab("taskbar-colorblind", taskbar_box))),
        (500, lambda: restyle(palette="standard", color_in_range="#b066ff",
                              color_high="#ffb000", ui_colors={"dark": {
                                  "bg": "#16213e", "panel": "#0f1629", "grid": "#26324f",
                                  "line": "#e0e6ff"}})),
        (500, lambda: ctl.open_settings()),
        (2500, lambda: (grab("elements-custom", elements_box),
                        grab("settings-custom", frame(SettingsWindow.current.win)))),
        (500, lambda: SettingsWindow.current.close()),
        (500, lambda: restyle(color_in_range=None, color_high=None, ui_colors={})),
        (1500, toasts),
        (2500, lambda: grab("messages", (sw - 400, max(0, bar[1] - 420), sw, bar[3]))),
        (500, lambda: ctl.quit()),
    ]
    position = [0]

    def next_step():
        while position[0] < len(steps):
            delay, action = steps[position[0]]
            position[0] += 1
            if delay is None:
                action()
                continue
            ctl.root.after(delay, run_step, action)
            return

    def run_step(action):
        try:
            result = action()
        except Exception as e:
            print(f"::warning title=Screenshot::step failed: {e!r}", flush=True)
            result = None
        # il menu richiama next_step da solo, quando si chiude
        if action is not steps[1][1]:
            next_step()
        return result

    next_step()
    ctl.run()
    server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
