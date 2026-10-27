"""Cuore di GlucoBar: un solo processo, un'icona vicino all'orologio che fa da
telecomando (modalità, lingua, account, esci) e una vista alla volta.

Tutto ciò che tocca Tkinter avviene nel thread principale: le richieste che
arrivano dal thread dell'icona o da quello dei dati passano per `post()`.
"""

import queue
import threading
import time
import tkinter as tk
import traceback

from . import i18n
from .config import log, save_config
from .i18n import LANGUAGES, t
from .librelinkup import LibreLinkUp, fetch_safely
from .ui_common import apply_icon, ask_credentials

MODES = ("taskbar", "window", "desktop", "tray")


class Controller:
    def __init__(self, cfg):
        self.cfg = cfg
        self.client = LibreLinkUp(cfg)
        self.current = None
        self.history = []
        self.error = None
        self.updated_at = None
        self.busy = False
        self._last_fetch = 0
        self.view = None
        self.tray = None
        self._calls = queue.Queue()

        self.root = tk.Tk()   # nascosta: le viste sono Toplevel figlie
        self.root.withdraw()
        apply_icon(self.root)

        self._start_tray()
        mode = cfg["mode"] if cfg["mode"] in MODES else "taskbar"
        if mode == "tray" and not self.tray:
            mode = "taskbar"  # senza icona non resterebbe nulla da vedere
        self.set_mode(mode)
        self.root.after(100, self._drain_calls)
        self._tick()

    # ---- da altri thread al thread di Tk ----
    def post(self, fn, *args):
        self._calls.put((fn, args))

    def _drain_calls(self):
        while True:
            try:
                fn, args = self._calls.get_nowait()
            except queue.Empty:
                break
            try:
                fn(*args)
            except Exception:
                log("comando non riuscito:\n" + traceback.format_exc())
        if self.root:
            self.root.after(100, self._drain_calls)

    # ---- icona nell'area di notifica ----
    def _start_tray(self):
        try:
            from .tray import TrayIcon
            self.tray = TrayIcon(self)
            self.tray.start()
        except Exception:
            log("icona nell'area di notifica non disponibile:\n" + traceback.format_exc())
            self.tray = None

    # ---- comandi (dall'icona o dai menu delle viste) ----
    def set_mode(self, mode):
        if self.view:
            self.view.destroy()
            self.view = None
        self.cfg["mode"] = mode
        save_config(self.cfg)
        log(f"modalità: {mode}")
        if mode == "taskbar":
            from .taskbar import TaskbarView
            self.view = TaskbarView(self)
        elif mode == "window":
            from .window import WindowView
            self.view = WindowView(self)
        elif mode == "desktop":
            from .desktop import DesktopView
            self.view = DesktopView(self)
        if self.tray:
            self.tray.update_menu()
        self.render()

    def set_language(self, lang):
        self.cfg["language"] = lang
        save_config(self.cfg)
        i18n.set_language(lang)
        self.set_mode(self.cfg["mode"])   # ricrea la vista con i testi nuovi

    def toggle_unit(self):
        self.cfg["unit"] = "mmol/L" if self.cfg["unit"] == "mg/dL" else "mg/dL"
        save_config(self.cfg)
        self.render()

    def change_account(self):
        if ask_credentials(self.cfg, self.root):
            self.client = LibreLinkUp(self.cfg)
            self.current, self.history, self.error = None, [], None
            self.refresh()

    def quit(self):
        log("uscita")
        if self.tray:
            self.tray.stop()
        if self.view:
            self.view.destroy()
            self.view = None
        root, self.root = self.root, None
        root.destroy()

    def add_common_menu(self, menu):
        """Voci comuni ai menu col clic destro delle viste."""
        modes = tk.Menu(menu, tearoff=0)
        mode_var = tk.StringVar(master=menu, value=self.cfg["mode"])
        for mode in MODES:
            if mode == "tray" and not self.tray:
                continue
            modes.add_radiobutton(label=t(f"mode_{mode}"), value=mode, variable=mode_var,
                                  command=lambda m=mode: self.post(self.set_mode, m))
        langs = tk.Menu(menu, tearoff=0)
        lang_var = tk.StringVar(master=menu, value=i18n.current_language())
        for code, name in LANGUAGES.items():
            langs.add_radiobutton(label=name, value=code, variable=lang_var,
                                  command=lambda c=code: self.post(self.set_language, c))
        menu.add_cascade(label=t("menu_mode"), menu=modes)
        menu.add_cascade(label=t("menu_language"), menu=langs)
        menu.add_command(label=t("menu_account"),
                         command=lambda: self.post(self.change_account))
        menu.add_separator()
        menu.add_command(label=t("menu_quit"), command=lambda: self.post(self.quit))
        menu._vars = (mode_var, lang_var)   # tenute vive insieme al menu

    # ---- dati ----
    def refresh(self):
        if self.busy:
            return
        self.busy = True
        self._last_fetch = time.time()
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        self.post(self._on_data, *fetch_safely(self.client))

    def _on_data(self, current, history, err):
        self.busy = False
        if err and err != self.error:
            log(f"dati: {err}")
        elif current and not self.current:
            log(f"primo dato ricevuto: {current['mgdl']} mg/dL")
        self.error = err
        if current:
            self.current, self.history = current, history
            self.updated_at = time.time()
        self.render()

    def _tick(self):
        if not self.root:
            return
        if time.time() - self._last_fetch >= self.cfg["refresh_seconds"]:
            self.refresh()
        else:
            self.render()   # aggiorna i "minuti fa"
        self.root.after(15000, self._tick)

    def render(self):
        if self.view:
            self.view.render()
        if self.tray:
            self.tray.render()

    def run(self):
        self.root.mainloop()
