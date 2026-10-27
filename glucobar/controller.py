"""Cuore di GlucoBar: un solo processo che mostra gli elementi scelti, anche insieme:
valore sulla barra, icona col numero vicino all'orologio, finestrella, pannello sullo
sfondo. Il menu (clic destro sull'icona o su qualsiasi elemento) sceglie cosa
mostrare, lingua, account, esci.

Tutto ciò che tocca Tkinter avviene nel thread principale: le richieste che
arrivano dal thread dell'icona o da quello dei dati passano per `post()`.
"""

import queue
import threading
import time
import tkinter as tk
import traceback

from . import i18n
from .config import ELEMENTS, log, normalize_elements, peek_config, save_config
from .i18n import LANGUAGES, t
from .sources import fetch_safely, make_client
from .ui_common import apply_icon, ask_credentials


# Impostazioni che si possono cambiare da terminale mentre GlucoBar è aperto
LIVE_KEYS = ("elements", "language", "unit", "low", "high", "very_high", "stale_minutes",
             "refresh_seconds", "source", "dexcom_region", "email", "taskbar_monitor", "taskbar_side", "taskbar_offset",
             "taskbar_bg", "taskbar_transparent", "desktop_hours", "desktop_alpha",
             "desktop_locked")
REBUILD_KEYS = {"taskbar_bg", "taskbar_transparent", "desktop_alpha", "desktop_locked"}
ACCOUNT_KEYS = {"source", "dexcom_region", "email"}


def _view_class(element):
    if element == "taskbar":
        from .taskbar import TaskbarView
        return TaskbarView
    if element == "window":
        from .window import WindowView
        return WindowView
    from .desktop import DesktopView
    return DesktopView


class Controller:
    def __init__(self, cfg):
        self.cfg = cfg
        self.client = make_client(cfg)
        self.current = None
        self.history = []
        self.error = None
        self.updated_at = None
        self.busy = False
        self._last_fetch = 0
        self.views = {}      # elemento -> vista aperta (taskbar, window, desktop)
        self.tray = None
        self._calls = queue.Queue()

        self.root = tk.Tk()   # nascosta: le viste sono Toplevel figlie
        self.root.withdraw()
        apply_icon(self.root)

        self._start_tray()
        elements = normalize_elements(cfg["elements"])
        if elements == ["tray"] and not self.tray:
            elements = ["taskbar"]   # senza icona non resterebbe nulla da vedere
        self.set_elements(elements)
        self.root.after(100, self._drain_calls)
        self._tick()
        self.root.after(2000, self._watch_config)

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

    def available(self, element):
        return element != "tray" or self.tray is not None

    # ---- cosa mostrare ----
    def shown(self, element):
        return element in self.cfg["elements"]

    def set_elements(self, elements):
        elements = normalize_elements(elements)
        # prima di toccare l'icona: il suo thread legge cfg["elements"] quando è pronta
        self.cfg["elements"] = elements
        for element in list(self.views):
            if element not in elements:
                self.views.pop(element).destroy()
        for element in elements:
            if element != "tray" and element not in self.views:
                self.views[element] = _view_class(element)(self)
        if self.tray:
            # nascosta, non fermata: si può riaccendere dal menu degli altri elementi
            self.tray.set_visible("tray" in elements)
            self.tray.update_menu()
        save_config(self.cfg)
        log(f"elementi mostrati: {', '.join(elements)}")
        self.render()

    def toggle_element(self, element):
        elements = list(self.cfg["elements"])
        if element in elements:
            if len(elements) == 1:
                return   # almeno un elemento deve restare visibile
            elements.remove(element)
        else:
            elements.append(element)
        self.set_elements(elements)

    def rebuild_views(self):
        """Ricrea le viste aperte (per esempio dopo un cambio di lingua)."""
        for element in list(self.views):
            self.views.pop(element).destroy()
        self.set_elements(self.cfg["elements"])

    # ---- comandi (dall'icona o dai menu delle viste) ----
    def set_language(self, lang):
        self.cfg["language"] = lang
        save_config(self.cfg)
        i18n.set_language(lang)
        self.rebuild_views()

    def toggle_unit(self):
        self.cfg["unit"] = "mmol/L" if self.cfg["unit"] == "mg/dL" else "mg/dL"
        save_config(self.cfg)
        self.render()

    def change_account(self):
        if ask_credentials(self.cfg, self.root):
            self.client = make_client(self.cfg)
            self.current, self.history, self.error = None, [], None
            self.refresh()

    def quit(self):
        log("uscita")
        if self.tray:
            self.tray.stop()
        for element in list(self.views):
            self.views.pop(element).destroy()
        root, self.root = self.root, None
        root.destroy()

    def add_common_menu(self, menu):
        """Voci comuni ai menu col clic destro delle viste."""
        show = tk.Menu(menu, tearoff=0)
        show_vars = []
        for element in ELEMENTS:
            if not self.available(element):
                continue
            var = tk.BooleanVar(master=menu, value=self.shown(element))
            show_vars.append(var)
            show.add_checkbutton(label=t(f"mode_{element}"), variable=var,
                                 command=lambda e=element: self.post(self.toggle_element, e))
        langs = tk.Menu(menu, tearoff=0)
        lang_var = tk.StringVar(master=menu, value=i18n.current_language())
        for code, name in LANGUAGES.items():
            langs.add_radiobutton(label=name, value=code, variable=lang_var,
                                  command=lambda c=code: self.post(self.set_language, c))
        menu.add_cascade(label=t("menu_show"), menu=show)
        menu.add_cascade(label=t("menu_language"), menu=langs)
        menu.add_command(label=t("menu_account"),
                         command=lambda: self.post(self.change_account))
        menu.add_separator()
        menu.add_command(label=t("menu_quit"), command=lambda: self.post(self.quit))

        def sync():
            # le spunte seguono i cambi fatti da altri menu (per esempio dall'icona)
            visible = [e for e in ELEMENTS if self.available(e)]
            for var, element in zip(show_vars, visible):
                var.set(self.shown(element))
            lang_var.set(i18n.current_language())
        menu.configure(postcommand=sync)
        menu._vars = (show_vars, lang_var)   # tenute vive insieme al menu

    # ---- modifiche da terminale (glucobar set / setup) ----
    def _watch_config(self):
        if not self.root:
            return
        try:
            saved = peek_config()
            changed = [k for k in LIVE_KEYS if saved and saved.get(k) != self.cfg.get(k)]
            if changed:
                self.apply_external(saved, changed)
        except Exception:
            log("rilettura impostazioni:\n" + traceback.format_exc())
        self.root.after(2000, self._watch_config)

    def apply_external(self, saved, changed):
        log(f"impostazioni cambiate da fuori: {', '.join(changed)}")
        for key in changed:
            self.cfg[key] = saved[key]
        if "language" in changed:
            i18n.set_language(self.cfg["language"])
        if ACCOUNT_KEYS & set(changed):
            self.client = make_client(self.cfg)
            self.current, self.history, self.error = None, [], None
            self.refresh()
        if "language" in changed or REBUILD_KEYS & set(changed):
            self.rebuild_views()
        elif "elements" in changed:
            self.set_elements(self.cfg["elements"])
        else:
            for view in self.views.values():
                if hasattr(view, "reposition"):
                    view.reposition()
            self.render()

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
        for view in self.views.values():
            view.render()
        if self.tray:
            self.tray.render()

    def run(self):
        self.root.mainloop()
