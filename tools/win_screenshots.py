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
import subprocess
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

    # niente finestre della build in vista (la console del runner)
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "(New-Object -ComObject Shell.Application).MinimizeAll()"], timeout=60)
    for title in ("System Properties",):   # avvisi della macchina della build
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            user32.PostMessageW(hwnd, 0x0010, 0, 0)   # WM_CLOSE
    time.sleep(2)
    from glucobar.taskbar import all_taskbars, enable_dpi_awareness, window_rect
    enable_dpi_awareness()
    from glucobar import config
    shutil.rmtree(config.CONFIG_DIR, ignore_errors=True)
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    bar = window_rect(all_taskbars()[0])
    # pannello in basso a destra, sopra la scritta "Test Mode" di Windows Server
    panel_w, panel_h = 540, 330
    panel_x, panel_y = sw - panel_w - 4, bar[1] - panel_h - 4
    window_x, window_y = sw - 234, panel_y - 150
    cfg = config.load_config()
    cfg.update(source="nightscout", email=f"http://127.0.0.1:{server.server_port}",
               elements=["taskbar", "tray", "window", "desktop"], language="en",
               update_check=False, theme="dark", tray_promoted=True, tray_hint_shown=True,
               desktop_x=panel_x, desktop_y=panel_y, desktop_w=panel_w, desktop_h=panel_h,
               window_x=window_x, window_y=window_y, desktop_alpha=1.0)
    config.save_config(cfg)
    from glucobar.i18n import set_language
    set_language("en")
    from glucobar.controller import Controller
    from PIL import ImageGrab

    ctl = Controller(config.load_config())

    def promote():
        # l'icona di python.exe accanto all'orologio, come fa GlucoBar.exe per sé
        from glucobar import notifyicon
        for _ in range(10):   # la voce di Windows compare qualche secondo dopo l'icona
            if notifyicon.promote(os.path.basename(sys.executable)):
                print("::notice title=Screenshot::icon next to the clock", flush=True)
                return
            time.sleep(1)

    def grab(name, box=None):
        img = ImageGrab.grab(bbox=box, all_screens=True, include_layered_windows=True)
        img.save(os.path.join(OUT, f"{name}.png"))
        print(f"::notice title=Screenshot::{name}.png {img.size}", flush=True)

    def frame(win):
        """Rettangolo della finestra con la cornice di Windows."""
        return window_rect(user32.GetParent(win.winfo_id()))

    elements_box = (panel_x - 40, window_y - 30, sw, sh)
    taskbar_box = (max(0, bar[2] - 620), bar[1], bar[2], bar[3])

    def popup_menu(view, name, after):
        """tk_popup blocca il ciclo di Tk finché il menu è aperto: la foto la scatta un
        thread, che poi chiude il menu con Esc."""
        x, y = view.root.winfo_rootx() - 300, view.root.winfo_rooty() - 120

        def key(code, times=1):
            for _ in range(times):
                user32.keybd_event(code, 0, 0, 0)
                user32.keybd_event(code, 0, 2, 0)
                time.sleep(0.25)

        def shoot():
            time.sleep(1.2)
            key(0x28, 2)   # giù fino a "Show"...
            key(0x27)      # ...e si apre il sottomenu
            time.sleep(1.0)
            grab(name, (x - 20, y - 20, min(sw, x + 520), min(sh, y + 330)))
            key(0x1B, 2)
        threading.Thread(target=shoot, daemon=True).start()
        view.show_menu(x, y)
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

    def toast_box():
        from glucobar.notify import Toast
        boxes = [frame_of(toast.win) for toast in Toast.open]
        return (min(b[0] for b in boxes) - 16, min(b[1] for b in boxes) - 16, sw,
                max(b[3] for b in boxes) + 8)

    def frame_of(win):
        x, y = win.winfo_rootx(), win.winfo_rooty()
        return x, y, x + win.winfo_width(), y + win.winfo_height()

    def close_toasts():
        from glucobar.notify import Toast
        for toast in list(Toast.open):
            toast.close()

    def hover_value():
        x0, y0, x1, y1 = ctl.views["taskbar"].value_rect()
        user32.SetCursorPos(sw // 2, 200)
        time.sleep(0.3)
        user32.SetCursorPos((x0 + x1) // 2, (y0 + y1) // 2)

    def hover_box():
        x0, y0, x1, y1 = ctl.views["taskbar"].value_rect()
        peek = ctl.views["taskbar"].hover.peek
        if peek is None:
            return (max(0, x0 - 400), max(0, y0 - 400), min(sw, x1 + 400), sh)
        px, py = peek.root.winfo_rootx(), peek.root.winfo_rooty()
        return (max(0, px - 30), max(0, py - 30),
                min(sw, max(px + peek.root.winfo_width(), x1) + 30), sh)

    from glucobar.i18n import t as ctl_t
    from glucobar.settings import SettingsWindow
    steps = [
        (4000, promote),
        (6000, lambda: (grab("desktop-dark"), grab("elements-dark", elements_box),
                        grab("taskbar", taskbar_box))),
        (500, lambda: popup_menu(ctl.views["window"], "menu", next_step)),
        (None, lambda: ctl.open_settings()),
        (2000, lambda: grab("settings", frame(SettingsWindow.current.win))),
        *[step for n, name in enumerate(("general", "values", "look", "elements", "updates"))
          for step in ((300, lambda n=n: SettingsWindow.current.notebook.select(n)),
                       (900, lambda name=name: grab(f"settings-{name}",
                                                    frame(SettingsWindow.current.win))))],
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
        (500, lambda: SettingsWindow.open(ctl, "look")),
        (2500, lambda: (grab("elements-custom", elements_box),
                        grab("settings-custom", frame(SettingsWindow.current.win)))),
        (500, lambda: SettingsWindow.current.close()),
        (500, lambda: restyle(color_in_range=None, color_high=None, ui_colors={})),
        (1500, toasts),
        (2500, lambda: grab("messages", toast_box())),
        (500, close_toasts),
        (500, lambda: ctl.set_elements(["taskbar", "tray"])),
        (1500, hover_value),
        (2200, lambda: grab("hover-chart", hover_box())),
        (300, lambda: user32.SetCursorPos(sw // 2, 200)),
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
        if action is not steps[2][1]:
            next_step()
        return result

    next_step()
    ctl.run()
    server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
