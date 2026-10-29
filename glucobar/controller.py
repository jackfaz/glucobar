"""Cuore di GlucoBar: un solo processo che mostra gli elementi scelti, anche insieme:
valore sulla barra, icona col numero vicino all'orologio, finestrella, pannello sullo
sfondo. Il menu (clic destro sull'icona o su qualsiasi elemento) sceglie cosa
mostrare, lingua, account, esci.

Tutto ciò che tocca Tkinter avviene nel thread principale: le richieste che
arrivano dal thread dell'icona o da quello dei dati passano per `post()`.
"""

import json
import queue
import sys
import threading
import time
import tkinter as tk
import traceback
import webbrowser

from . import alerts, i18n, instance, reminders, sensor, support, theme, updates
from .alerts import AlertWatch

ALARMS = ("low", "high")   # gli avvisi il cui suono si può ripetere
from .config import (ELEMENTS, MIN_REFRESH, REFRESH_CHOICES, log, normalize_elements,
                     peek_config, save_config)
from .i18n import element_name, refresh_label, t
from .menus import SEPARATOR, Item, menu_open, radio_items
from .sources import fetch_safely, make_client
from .theme import COLOR_KEYS
from .ui_common import apply_icon, ask_credentials, fmt_value


# Impostazioni che si possono cambiare da terminale mentre GlucoBar è aperto
LIVE_KEYS = ("elements", "language", "unit", "low", "high", "very_high", "stale_minutes",
             "refresh_seconds", "source", "dexcom_region", "email", "taskbar_monitor",
             "taskbar_side", "taskbar_offset", "taskbar_bg", "taskbar_transparent",
             "taskbar_scale", "window_scale", "desktop_hours", "desktop_alpha", "desktop_locked",
             "theme", "palette", "alert_low", "alert_high", "alert_stale", "update_check",
             "auto_update", "sensor_life_days", "ui_colors", "taskbar_text", "show_delta",
             "trend_style", "predict", "alert_soon", "nicknames", "people_shown",
             "alert_sound", "alert_repeat", "alert_repeat_seconds",
             "hover_chart", "desktop_on_top", "desktop_over_fullscreen",
             *COLOR_KEYS.values())
REBUILD_KEYS = {"taskbar_bg", "taskbar_transparent", "taskbar_text", "desktop_alpha", "trend_style",
                "desktop_locked", "desktop_on_top", "window_scale", "theme", "palette", "ui_colors",
                *COLOR_KEYS.values()}
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
        self.others = []     # altre persone mostrate insieme: [{"id", "label", "current"}]
        self.other_alerts = {}   # id -> AlertWatch delle altre persone
        self.silenced = set()    # (persona, avviso) zittiti fino alla fine dell'episodio
        self._last_sound = 0
        self.error = None
        self.updated_at = None
        self.busy = False
        self._last_fetch = 0
        self._last_render = 0
        self._started = time.time()
        self.alerts = AlertWatch()
        self.sensors = sensor.SensorWatch()
        self.update = None          # ultima release, se più nuova (vedi updates.py)
        self._installing = False
        self._checking_update = False
        self._logged_sensor = None
        self._theme_key = self.theme_key()
        self.views = {}      # elemento -> vista aperta (taskbar, window, desktop)
        self.tray = None
        self._promoting = False   # tentativi in corso di mettere l'icona accanto all'orologio
        self._calls = queue.Queue()
        self.bridge = None

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
        try:
            from .bridge import Bridge
            self.bridge = Bridge(self)
        except Exception:
            log("ponte locale non avviato:\n" + traceback.format_exc())
        self.root.after(100, self._drain_calls)
        self._tick()
        self.root.after(3000, self.announce_version)
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
        # Su Windows Tk continua a girare mentre un menu col clic destro è aperto: i
        # comandi aspettano che si chiuda, così non distruggono la finestra del menu
        # mentre è ancora aperto
        while not menu_open():
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

    def toggle_hover_chart(self):
        self.cfg["hover_chart"] = not self.cfg.get("hover_chart", True)
        save_config(self.cfg)

    def toggle_delta(self):
        self.cfg["show_delta"] = not self.cfg.get("show_delta")
        save_config(self.cfg)
        self.render()

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
        if self.bridge:
            self.bridge.stop()
        if self.tray:
            self.tray.stop()
        for element in list(self.views):
            self.views.pop(element).destroy()
        root, self.root = self.root, None
        root.destroy()

    # ---- menu (uguale per clic destro, icona e barra dei menu del Mac) ----
    def menu_items(self, view_items=()):
        items = []
        if self.update:
            version = self.update["version"]
            if self.can_install_update():
                items.append(Item(t("menu_update_install", v=version), self.install_update))
            else:
                items.append(Item(t("menu_update", v=version), self.open_update))
            items.append(SEPARATOR)
        items.append(Item(t("menu_refresh"), self.refresh, default=True))
        items += list(view_items)
        items.append(Item(t("menu_show"), children=[
            Item(element_name(e), self.toggle_element, e, checked=self.shown(e))
            for e in ELEMENTS if self.available(e)]))
        patients = getattr(self.client, "patients", None) or []
        if len(patients) > 1:
            shown = self.cfg.get("people_shown") or []
            choices = [(pid, self.person_label(pid, full=True)) for pid, _name in patients]
            items.append(Item(t("menu_person"), children=radio_items(
                choices, self.client.patient_id, self.set_patient) + [SEPARATOR] + [
                Item(t("menu_person_also", name=label), self.toggle_person_shown, pid,
                     checked=pid in shown)
                for pid, label in choices if pid != self.client.patient_id]))
        # il resto (unità, aggiornamento, avvisi, lingua, account, avvio, nuove versioni)
        # sta nella finestra Impostazioni, divisa per argomento
        items += [
            Item(t("menu_sensor"), children=self.sensor_items()),
            Item(t("menu_settings"), self.open_settings),
            Item(t("menu_reminders"), self.open_reminders),
            SEPARATOR,
            Item(t("menu_quit"), self.quit),
        ]
        return items

    def sensor_items(self):
        items = []
        info = self.sensor_info()
        if info:
            items += [Item(t("sensor_day", d=sensor.day_of(info), n=sensor.life_days(self.cfg)),
                           enabled=False),
                      Item(t("sensor_serial", sn=info["sn"]), self.copy_serial, info["sn"]),
                      SEPARATOR]
        source = self.cfg.get("source", "libre")
        if source == "nightscout":   # il sensore può essere di chiunque
            items += [Item(t("replace_libre"), self.request_replacement, "libre"),
                      Item(t("replace_dexcom"), self.request_replacement, "dexcom")]
        else:
            items.append(Item(t("replace"), self.request_replacement, source))
        return items

    def sensor_info(self):
        if self.cfg.get("source", "libre") != "libre":
            return None
        return sensor.info(getattr(self.client, "connection", None))

    # ---- comandi del menu ----
    def open_settings(self):
        from .settings import SettingsWindow
        SettingsWindow.open(self)

    def open_reminders(self):
        from .reminders_ui import RemindersWindow
        RemindersWindow.open(self)

    # ---- promemoria (reminders.py) ----
    def sensor_end(self):
        """Fine prevista del sensore in uso (solo FreeStyle Libre), per i promemoria."""
        if self.cfg.get("source", "libre") != "libre":
            return None
        return reminders.sensor_end(self.cfg, sensor.life_days(self.cfg))

    def find_reminder(self, rem_id):
        return next((r for r in self.cfg.get("reminders") or [] if r.get("id") == rem_id), None)

    def check_reminders(self):
        now, end = time.time(), self.sensor_end()
        for rem in self.cfg.get("reminders") or []:
            if not reminders.due(rem, now, end):
                continue
            reminders.fire(rem, now, end)
            save_config(self.cfg)
            log(f"promemoria: {rem['id']}")
            rem_id = rem["id"]
            self.notify(t("rem_toast_title"), rem["title"], actions=[
                (t("rem_done"), lambda: self.reminder_done(rem_id)),
                (t("rem_later", n=refresh_label(15 * 60)), lambda: self.reminder_snooze(rem_id, 15)),
                (t("rem_later", n=refresh_label(60 * 60)), lambda: self.reminder_snooze(rem_id, 60)),
            ])

    def reminder_done(self, rem_id):
        rem = self.find_reminder(rem_id)
        if rem:
            reminders.done(rem, time.time())
            save_config(self.cfg)
            self.refresh_reminders_window()

    def reminder_snooze(self, rem_id, minutes):
        rem = self.find_reminder(rem_id)
        if rem:
            reminders.snooze(rem, time.time(), minutes)
            save_config(self.cfg)
            self.refresh_reminders_window()

    def refresh_reminders_window(self):
        from .reminders_ui import RemindersWindow
        window = RemindersWindow.current
        if window and window.win.winfo_exists():
            window.refresh()

    def restyle(self):
        self._theme_key = self.theme_key()
        self.rebuild_views()
        if self.tray:
            self.tray.render()

    def theme_key(self):
        return (theme.is_light(self.cfg), theme.taskbar_light(), self.cfg.get("palette"),
                json.dumps(self.cfg.get("ui_colors"), sort_keys=True),
                *(self.cfg.get(key) for key in COLOR_KEYS.values()))

    def toggle_alert(self, kind):
        key = f"alert_{kind}"
        self.cfg[key] = not self.cfg.get(key)
        if self.cfg[key] and not self.cfg.get("alerts_note_shown"):
            # una volta sola: cosa sono (e non sono) questi avvisi
            self.cfg["alerts_note_shown"] = True
            self.notify(t("alert_title"), t("alerts_note"), timeout=30)
        save_config(self.cfg)
        self.check_alerts()

    def set_patient(self, patient_id):
        self.cfg["patient_id"] = patient_id
        self.others = [o for o in self.others if o["id"] != patient_id]
        # il sensore è di un'altra persona: niente avvisi di "sensore cambiato"
        self.cfg.update(sensor_sn=None, sensor_activated=None, sensor_notified=[])
        save_config(self.cfg)
        self.client.patient_id = patient_id
        self.current, self.history, self.error = None, [], None
        self.render()
        self.refresh()

    # ---- persone seguite (LibreLinkUp: più persone con lo stesso account) ----
    def person_key(self, pid=None):
        """Chiave dei soprannomi: l'id della persona (LibreLinkUp) o "self"."""
        return str(pid or getattr(self.client, "patient_id", None) or "self")

    def person_label(self, pid=None, full=False):
        """Il soprannome scelto o il nome; full=True: "Soprannome (Nome Cognome)"."""
        key = self.person_key(pid)
        nickname = ((self.cfg.get("nicknames") or {}).get(key) or "").strip()
        names = dict(getattr(self.client, "patients", None) or [])
        name = names.get(pid or getattr(self.client, "patient_id", None), "")
        if full:
            return f"{nickname} ({name})" if nickname and name else nickname or name
        return nickname or name.split(" ")[0]

    def display_name(self):
        """Il nome da scrivere accanto al valore principale: il soprannome se c'è,
        altrimenti il nome solo quando si vedono più persone insieme."""
        nickname = (self.cfg.get("nicknames") or {}).get(self.person_key(), "").strip()
        return nickname or (self.person_label() if self.others else "")

    def set_nickname(self, pid, nickname):
        nicknames = dict(self.cfg.get("nicknames") or {})
        nickname = nickname.strip()[:20]
        if nickname:
            nicknames[self.person_key(pid)] = nickname
        else:
            nicknames.pop(self.person_key(pid), None)
        self.cfg["nicknames"] = nicknames
        save_config(self.cfg)
        self.relabel_others()
        self.render()

    def toggle_person_shown(self, pid):
        shown = list(self.cfg.get("people_shown") or [])
        if pid in shown:
            shown.remove(pid)
        else:
            shown.append(pid)
        self.cfg["people_shown"] = shown
        save_config(self.cfg)
        self.others = [o for o in self.others if o["id"] in shown]
        self.render()
        self.refresh()

    def relabel_others(self):
        for other in self.others:
            other["label"] = self.person_label(other["id"])

    def copy_serial(self, sn):
        self.root.clipboard_clear()
        self.root.clipboard_append(sn)
        self.notify(t("menu_sensor"), t("sensor_copied", sn=sn), timeout=8)

    def request_replacement(self, maker, sn=None):
        """Apre la pagina del produttore e copia il numero di serie (se si conosce)."""
        url = support.replacement_url(maker)
        log(f"pagina di sostituzione aperta: {url}")
        webbrowser.open(url)
        info = self.sensor_info()
        sn = sn or (info["sn"] if info and maker == "libre" else None)
        if sn:
            self.root.clipboard_clear()
            self.root.clipboard_append(sn)
            self.notify(t("menu_sensor"), t("replace_copied", sn=sn), timeout=20)

    def toggle_update_check(self):
        self.cfg["update_check"] = not self.cfg.get("update_check", True)
        if not self.cfg["update_check"]:
            self.update = None
        save_config(self.cfg)
        self.render()

    def toggle_auto_update(self):
        self.cfg["auto_update"] = not self.cfg.get("auto_update")
        if self.cfg["auto_update"]:
            self.cfg["update_check"] = True
        save_config(self.cfg)
        if self.cfg["auto_update"] and self.can_install_update():
            self.install_update()
        self.render()

    def open_update(self):
        webbrowser.open(self.update["page"] if self.update else updates.RELEASES)

    def can_install_update(self):
        return bool(self.update and self.update.get("installer") and updates.can_install())

    def install_update(self):
        """Scarica l'installer della nuova versione e lo avvia in silenzio: chiude
        GlucoBar, lo aggiorna e lo riapre con le stesse impostazioni."""
        if self._installing or not self.can_install_update():
            return
        self._installing = True
        release = self.update
        log(f"scarico la versione {release['version']}")
        self.notify(t("update_title"), t("update_downloading", v=release["version"]), timeout=20)
        threading.Thread(target=self._download_worker, args=(release,), daemon=True).start()

    def _download_worker(self, release):
        try:
            path = updates.download(release)
        except Exception as e:
            log(f"aggiornamento non scaricato: {e}")
            self.post(self._update_failed, str(e))
            return
        self.post(self._start_installer, path, release["version"])

    def _update_failed(self, error):
        self._installing = False
        self.notify(t("update_title"), t("update_failed", e=error),
                    actions=[(t("update_notes"), self.open_update)])

    def _start_installer(self, path, version):
        log(f"avvio l'installer della versione {version}")
        try:
            updates.run_installer(path)
        except OSError as e:
            log(f"installer non avviato: {e}")
            self._update_failed(str(e))
        # l'installer chiede a GlucoBar di chiudersi (vedi instance.py) e lo riapre

    def notify(self, title, text, actions=(), timeout=15):
        from .notify import Toast
        log(f"messaggio: {title}")
        try:
            Toast(self, title, text, actions, timeout)
        except tk.TclError:
            log("messaggio non mostrato:\n" + traceback.format_exc())

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

    def set_options(self, **changes):
        """Impostazioni cambiate dalla finestra Impostazioni: si applicano subito."""
        self.apply_external(dict(self.cfg, **changes), list(changes), quiet=True)
        save_config(self.cfg)

    def apply_external(self, saved, changed, quiet=False):
        if not quiet:
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
            self._theme_key = self.theme_key()
            self.rebuild_views()
        elif "elements" in changed:
            self.set_elements(self.cfg["elements"])
        else:
            for view in self.views.values():
                if hasattr(view, "reposition"):
                    view.reposition()
            self.render()

    # ---- dati ----
    def refresh_seconds(self):
        try:
            return max(MIN_REFRESH, int(self.cfg["refresh_seconds"]))
        except (TypeError, ValueError):
            return 60

    def refresh_choices(self):
        """Le scelte del menu, più il valore attuale se scelto da terminale (es. 45 s)."""
        return sorted(set(REFRESH_CHOICES) | {self.refresh_seconds()})

    def set_refresh(self, seconds):
        self.cfg["refresh_seconds"] = int(seconds)
        save_config(self.cfg)
        log(f"aggiornamento ogni {refresh_label(seconds)}")
        self.render()

    def refresh(self):
        if self.busy:
            return
        self.busy = True
        self._last_fetch = time.time()
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        current, history, err = fetch_safely(self.client)
        extras = dict(getattr(self.client, "extras", None) or {})
        self.post(self._on_data, current, history, err, extras)

    def _on_data(self, current, history, err, extras=None):
        self.busy = False
        if extras is not None:
            primary = getattr(self.client, "patient_id", None)
            self.others = [{"id": pid, "label": self.person_label(pid), "current": extras[pid]}
                           for pid in self.cfg.get("people_shown") or []
                           if pid in extras and pid != primary]
        if err and err != self.error:
            log(f"dati: {err}")
        elif current and not self.current:
            log(f"primo dato ricevuto: {current['mgdl']} mg/dL")
        self.error = err
        if current:
            self.current, self.history = current, history
            self.updated_at = time.time()
        self.render()
        self.check_alerts()
        self.check_sensor()

    def check_alerts(self):
        cfg = self.cfg
        people = [(None, self.alerts, self.current, self.history)] + [
            (o["id"], self.other_alerts.setdefault(o["id"], AlertWatch()), o["current"], None)
            for o in self.others]
        for pid, watch, c, history in people:
            for kind in watch.check(cfg, c, history=history):
                value = f"{fmt_value(cfg, c['mgdl'])} {cfg['unit']}" if c else ""
                minutes = int((time.time() - c["time"]) // 60) if c else 0
                if kind == "soon":
                    minutes = round(alerts.soon_minutes(cfg, history, c) or 0)
                    value = f"{fmt_value(cfg, cfg['low'])} {cfg['unit']}"
                title = t("alert_title")
                if self.others or pid:   # più persone: di chi è l'avviso
                    title += " – " + self.person_label(pid)
                log(f"avviso: {kind}")
                actions = []
                if kind in ALARMS and cfg.get("alert_repeat"):
                    # il suono si ripete: il messaggio resta finché non lo si zittisce
                    actions = [(t("alert_silence"), lambda p=pid, k=kind: self.silence(p, k))]
                self.notify(title, t(f"alert_{kind}", v=value, n=minutes), actions=actions,
                            timeout=60)
                if cfg.get("alert_sound", True):
                    self.sound_now()

    # ---- suono degli avvisi (basso e molto alto), anche ripetuto ----
    def alarms_active(self):
        """(persona, avviso) di valore basso o molto alto in corso, tra quelli accesi."""
        watches = [(None, self.alerts)] + [(o["id"], self.other_alerts.get(o["id"]))
                                          for o in self.others]
        return {(pid, kind) for pid, watch in watches if watch
                for kind in watch.active if kind in ALARMS}

    def repeat_alarm(self):
        """Ogni secondo: con "ripeti il suono", suona di nuovo finché il valore non torna
        nel range o finché non si preme Zittisci."""
        active = self.alarms_active()
        self.silenced &= active   # episodio finito: la prossima volta suona di nuovo
        if not (self.cfg.get("alert_repeat") and self.cfg.get("alert_sound", True)):
            return
        if active - self.silenced and time.time() - self._last_sound >= self.repeat_seconds():
            self.sound_now()

    def repeat_seconds(self):
        try:
            return max(10, int(self.cfg.get("alert_repeat_seconds") or 15))
        except (TypeError, ValueError):
            return 15

    def sound_now(self):
        from . import sound
        self._last_sound = time.time()
        sound.play()

    def silence(self, pid, kind):
        self.silenced.add((pid, kind))
        log(f"suono zittito: {kind}")

    def check_sensor(self):
        if self.cfg.get("source", "libre") != "libre":
            return
        events, dirty = self.sensors.check(self.cfg, getattr(self.client, "connection", None),
                                           self.current, self.error)
        if dirty:
            save_config(self.cfg)
        info = self.sensor_info()
        if info and info["sn"] != self._logged_sensor:
            # il tipo serve a capire quanto dura ogni modello (14 o 15 giorni)
            self._logged_sensor = info["sn"]
            log(f"sensore LibreLinkUp: tipo {info['type']}, giorno {sensor.day_of(info)}")
        for name, data in events:
            log(f"sensore: {name}")
            if name == "ending":
                hours = data["hours"]
                text = (t("sensor_ending_h", h=round(hours)) if hours >= 1.5
                        else t("sensor_ending_soon"))
                self.notify(t("sensor_msg_title"), text, timeout=60)
            else:   # stopped / replaced_early: si può chiedere la sostituzione
                text = t(f"sensor_{name}", sn=data["sn"], d=data.get("days", 0))
                self.notify(t("sensor_msg_title"), text, actions=[
                    (t("replace_open"), lambda sn=data["sn"]: self.request_replacement("libre", sn))])

    def check_updates(self, force=False, done=None):
        """Una volta al giorno; con force=True subito (Impostazioni → Cerca aggiornamenti),
        e alla fine done(release o None, errore o None)."""
        now = time.time()
        if self._checking_update or (not force and (
                not self.cfg.get("update_check", True) or now - self._started < 60
                or now - float(self.cfg.get("update_checked_at") or 0) < updates.INTERVAL)):
            return
        self._checking_update = True
        threading.Thread(target=self._update_worker, args=(done,), daemon=True).start()

    def _update_worker(self, done):
        try:
            result, error = updates.latest_release(), None
        except Exception as e:
            log(f"controllo nuova versione non riuscito: {e}")
            result, error = None, str(e)
        self.post(self._on_update, result, done, error)

    def _on_update(self, result, done=None, error=None):
        self._checking_update = False
        now = time.time()
        # se GitHub non risponde riprova tra un'ora, non tra un minuto
        self.cfg["update_checked_at"] = now if result else now - updates.INTERVAL + 3600
        if result and updates.is_newer(result["version"]):
            self.update = result
            version = result["version"]
            if self.cfg.get("auto_update") and self.can_install_update():
                save_config(self.cfg)
                self.install_update()
            elif done is None and self.cfg.get("update_notified") != version:
                self.cfg["update_notified"] = version
                log(f"nuova versione disponibile: {version}")
                if self.can_install_update():
                    actions = [(t("update_install"), self.install_update),
                               (t("update_notes"), self.open_update)]
                else:
                    actions = [(t("update_open"), self.open_update)]
                self.notify(t("update_title"), t("update_text", v=version), actions=actions)
        save_config(self.cfg)
        self.render()
        if done:   # controllo chiesto dalle Impostazioni: risponde lì
            done(result, error)

    def announce_version(self):
        """Primo avvio dopo un aggiornamento: lo dice, con le novità a un clic."""
        from . import __version__
        previous = self.cfg.get("last_version")
        if previous == __version__:
            return
        self.cfg["last_version"] = __version__
        save_config(self.cfg)
        if previous and updates.is_newer(__version__, previous):
            log(f"aggiornato da {previous} a {__version__}")
            page = f"https://github.com/jackfaz/glucobar/releases/tag/v{__version__}"
            self.notify(t("update_title"), t("updated_to", v=__version__),
                        actions=[(t("update_notes"), lambda: webbrowser.open(page))])

    def _tick(self):
        if not self.root:
            return
        now = time.time()
        wait = self.refresh_seconds()
        if self.error:
            wait = max(wait, 60)   # dopo un errore (password, rete) non insistere troppo
        self.repeat_alarm()
        if now - self._last_fetch >= wait:
            self.refresh()
        elif now - self._last_render >= 15:
            self._last_render = now
            if self.theme_key() != self._theme_key:   # tema di Windows o macOS cambiato
                log("tema cambiato")
                self.restyle()
            self.render()   # aggiorna i "minuti fa"
            self.check_alerts()   # "nessun dato" scatta anche senza letture nuove
            self.check_sensor()
            self.check_reminders()
            self.check_updates()
        self.root.after(1000, self._tick)

    def render(self):
        for view in self.views.values():
            view.render()
        if self.bridge:
            self.bridge.update()
        if self.tray:
            self.tray.render()
            self.tray.update_menu()

    def run(self):
        self.root.mainloop()
