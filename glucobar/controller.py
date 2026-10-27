"""Cuore di GlucoBar: un solo processo che mostra gli elementi scelti, anche insieme:
valore sulla barra, icona col numero vicino all'orologio, finestrella, pannello sullo
sfondo. Il menu (clic destro sull'icona o su qualsiasi elemento) sceglie cosa
mostrare, lingua, account, esci.

Tutto ciò che tocca Tkinter avviene nel thread principale: le richieste che
arrivano dal thread dell'icona o da quello dei dati passano per `post()`.
"""

import queue
import sys
import threading
import time
import tkinter as tk
import traceback

from . import i18n, instance
from .config import ELEMENTS, log, normalize_elements, peek_config, save_config
from .i18n import LANGUAGES, element_name, t
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
        self._promoting = False   # tentativi in corso di mettere l'icona accanto all'orologio
        self._calls = queue.Queue()

        self.root = tk.Tk()   # nascosta: le viste sono Toplevel figlie
        self.root.withdraw()
        apply_icon(self.root)
        if sys.platform == "darwin":
            self._mac_accessory()

        self._start_tray()
        elements = normalize_elements(cfg["elements"])
        if elements == ["tray"] and not self.tray:
            # senza icona non resterebbe nulla da vedere: barra (Windows) o finestrella (Mac)
            elements = [e for e in ELEMENTS if e != "tray"][:1]
        self.set_elements(elements)
        self.root.after(100, self._drain_calls)
        self._tick()
        self.root.after(2000, self._watch_config)
        # installer, disinstallazione o `glucobar stop` possono chiedere di chiudere
        self._quit_event = instance.quit_event()
        self.root.after(500, self._watch_quit)

    def _mac_accessory(self):
        """Mac: app "accessoria", come tutte quelle della barra dei menu: niente icona
        nel Dock e niente menu File/Modifica in alto (Tkinter la renderebbe un'app
        normale anche con LSUIElement)."""
        try:
            from AppKit import NSApplication
            NSApplication.sharedApplication().setActivationPolicy_(1)   # Accessory
        except Exception:
            log("modalità accessoria non impostata:\n" + traceback.format_exc())

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
            if sys.platform == "darwin":
                from .macbar import MacMenuBar   # valore nella barra dei menu
                self.tray = MacMenuBar(self)
            else:
                from .tray import TrayIcon
                self.tray = TrayIcon(self)
            self.tray.start()
        except Exception:
            log("icona nell'area di notifica non disponibile:\n" + traceback.format_exc())
            self.tray = None

    PROMOTE_DELAYS = (2, 3, 5, 10, 20, 30)   # secondi tra un tentativo e l'altro

    def promote_tray(self, attempt=0):
        """Mette l'icona accanto all'orologio, una volta sola (vedi notifyicon.py).
        La voce di Windows compare qualche secondo dopo l'icona: riprova per un po'."""
        from . import notifyicon
        if sys.platform != "win32":
            return   # solo Windows 11 nasconde le icone nuove sotto la freccetta
        if attempt == 0:
            if self._promoting:
                return   # c'è già una serie di tentativi in corso
            self._promoting = True
        if self.cfg.get("tray_promoted") or not self.tray or not self.root:
            self._promoting = False
            return
        if notifyicon.promote("GlucoBar.exe"):
            self.cfg["tray_promoted"] = True
            save_config(self.cfg)
            self._promoting = False
            log("icona resa visibile accanto all'orologio")
        elif attempt < len(self.PROMOTE_DELAYS):
            self.root.after(self.PROMOTE_DELAYS[attempt] * 1000, self.promote_tray, attempt + 1)
        else:
            self._promoting = False
            log("icona non trovata nelle impostazioni di Windows: resta sotto la freccetta ^")
            self.tray.show_hint()

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
            if "tray" in elements and self.tray.ready:
                self.promote_tray()
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
            show.add_checkbutton(label=element_name(element), variable=var,
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

    def _watch_quit(self):
        if not self.root:
            return
        if instance.quit_requested(self._quit_event):
            log("chiusura richiesta da fuori (installer o glucobar stop)")
            self.quit()
            return
        self.root.after(500, self._watch_quit)

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
