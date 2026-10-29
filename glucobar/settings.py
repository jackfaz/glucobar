"""Finestra Impostazioni (clic destro → Impostazioni…), divisa in schede per argomento:
Generale, Valori, Avvisi e suoni, Aspetto, Elementi, Aggiornamenti. Ogni scelta si applica
subito a tutti gli elementi aperti (barra, icona, finestrella, pannello), così si vede
com'è prima di chiudere. Il menu col clic destro tiene solo le azioni rapide.

I colori del valore valgono con entrambi i temi; quelli di finestrella e pannello sono
del tema in uso (chiaro o scuro), così cambiare tema non li mescola."""

import os
import sys
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from . import __version__, autostart, credentials, sound, updates
from .config import ELEMENTS, save_config
from .alerts import ALARMS, REPEAT_CHOICES
from .i18n import LANGUAGES, element_name, refresh_label, t
from .theme import COLOR_KEYS, PALETTES, THEMES, UI_KEYS, is_light, palette
from .ui_common import FONT, TREND_STYLES, ask_range, fmt_value

# colore del valore -> esempio in mg/dL (dalle soglie dell'utente)
SAMPLES = {
    "in_range": lambda cfg: (cfg["low"] + cfg["high"]) // 2,
    "high": lambda cfg: (cfg["high"] + cfg["very_high"]) // 2,
    "very_high": lambda cfg: cfg["very_high"] + 30,
    "low": lambda cfg: max(40, cfg["low"] - 10),
    "stale": lambda cfg: (cfg["low"] + cfg["high"]) // 2,
}
TABS = ("general", "values", "alerts", "look", "elements", "connect", "updates")


class SettingsWindow:
    current = None   # una finestra sola: riaprendola torna in primo piano

    @classmethod
    def open(cls, ctl, tab=None):
        if cls.current and cls.current.win.winfo_exists():
            cls.current.win.deiconify()
            cls.current.win.lift()
            cls.current.win.focus_force()
        else:
            cls.current = cls(ctl)
        if tab:
            cls.current.notebook.select(TABS.index(tab))

    def __init__(self, ctl):
        self.ctl = ctl
        self.cfg = ctl.cfg
        self.win = win = tk.Toplevel(ctl.root)
        win.title(t("settings_title"))
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", self.close)
        self.notebook = ttk.Notebook(win)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(12, 0))
        self.vars = []   # le variabili Tk devono vivere quanto la finestra
        self.tab_general(self.tab("general"))
        self.tab_values(self.tab("values"))
        self.tab_alerts(self.tab("alerts"))
        self.tab_look(self.tab("look"))
        self.tab_elements(self.tab("elements"))
        self.tab_connect(self.tab("connect"))
        self.tab_updates(self.tab("updates"))

        bottom = tk.Frame(win)
        bottom.pack(fill="x", padx=14, pady=(10, 14))
        tk.Label(bottom, text=t("settings_live"), font=(FONT, 9), fg="#6b6f76").pack(side="left")
        tk.Button(bottom, text=t("button_close"), width=10, command=self.close,
                  default="active").pack(side="right")
        win.bind("<Escape>", lambda _e: self.close())
        self.refresh()

        win.update_idletasks()
        win.geometry(f"+{(win.winfo_screenwidth() - win.winfo_reqwidth()) // 2}"
                     f"+{max(0, (win.winfo_screenheight() - win.winfo_reqheight()) // 4)}")
        win.attributes("-topmost", True)
        win.focus_force()

    # ---- mattoni ----
    def tab(self, name):
        frame = tk.Frame(self.notebook, padx=12, pady=4)
        self.notebook.add(frame, text=t(f"tab_{name}"))
        return frame

    @staticmethod
    def section(parent, title, **pack):
        # spazi stretti: la scheda più lunga deve stare anche su uno schermo da 768 pixel
        box = tk.LabelFrame(parent, text=title, font=(FONT, 10), padx=10, pady=3)
        box.pack(fill="x", pady=(6, 0), **pack)
        return box

    @staticmethod
    def row(parent, row, label, sample, command):
        tk.Label(parent, text=label, font=(FONT, 10), anchor="w").grid(
            row=row, column=0, sticky="w", pady=2)
        sample.grid(row=row, column=1, padx=10, pady=2)
        button = tk.Button(parent, text=t("settings_change"), font=(FONT, 9), command=command)
        button.grid(row=row, column=2, pady=2)
        parent.columnconfigure(0, weight=1)
        return button

    def var(self, kind, value):
        v = kind(master=self.win, value=value)
        self.vars.append(v)
        return v

    def check(self, parent, text, value, command):
        v = self.var(tk.BooleanVar, bool(value))
        tk.Checkbutton(parent, text=text, variable=v, font=(FONT, 10), anchor="w",
                       command=lambda: command(v.get())).pack(fill="x")
        return v

    def radios(self, parent, choices, value, command, side="top"):
        v = self.var(tk.StringVar, str(value))
        for key, label in choices:
            tk.Radiobutton(parent, text=label, value=str(key), variable=v, font=(FONT, 10),
                           anchor="w", command=lambda k=key: command(k)).pack(
                side=side, fill="x" if side == "top" else None, padx=(0, 8))
        return v

    # ---- Generale ----
    def tab_general(self, frame):
        cfg, ctl = self.cfg, self.ctl
        box = self.section(frame, t("settings_account"))
        self.account_lbl = tk.Label(box, font=(FONT, 10), anchor="w", justify="left",
                                    wraplength=330)
        self.account_lbl.pack(side="left")
        tk.Button(box, text=t("menu_account"), font=(FONT, 9),
                  command=self.change_account).pack(side="right")

        self.people_section(frame)

        box = self.section(frame, t("menu_language"))
        names = ["Auto"] + list(LANGUAGES.values())
        codes = ["auto"] + list(LANGUAGES)
        current = cfg.get("language", "auto")
        lang = ttk.Combobox(box, values=names, state="readonly", width=24)
        lang.current(codes.index(current) if current in codes else 0)
        lang.pack(anchor="w")
        lang.bind("<<ComboboxSelected>>",
                  lambda _e: self.set_language(codes[lang.current()]))

        box = self.section(frame, t("settings_unit"))
        self.radios(box, [("mg/dL", "mg/dL"), ("mmol/L", "mmol/L")], cfg["unit"],
                    lambda unit: ctl.set_options(unit=unit) or self.refresh(), side="left")

        box = self.section(frame, t("menu_refresh_every"))
        self.radios(box, [(s, refresh_label(s)) for s in ctl.refresh_choices()],
                    ctl.refresh_seconds(), ctl.set_refresh, side="left")

        if autostart.gui_exe():   # solo nell'app installata
            box = self.section(frame, t("settings_startup"))
            label = t("menu_autostart" if sys.platform == "darwin" else "menu_autostart_win")
            self.check(box, label, autostart.is_enabled(), autostart.set_enabled)

    def people_section(self, frame):
        """Soprannome di ogni persona seguita e, con LibreLinkUp, chi mostrare insieme
        sulla barra."""
        ctl = self.ctl
        box = self.section(frame, t("settings_people"))
        patients = getattr(ctl.client, "patients", None) or []
        primary = getattr(ctl.client, "patient_id", None)
        shown = self.cfg.get("people_shown") or []
        grid = tk.Frame(box)
        grid.pack(fill="x")
        tk.Label(grid, text=t("settings_people_nickname"), font=(FONT, 9), fg="#6b6f76").grid(
            row=0, column=1, sticky="w")
        for row, (pid, name) in enumerate(patients or [(None, t("settings_people_you"))], 1):
            label = name + (f"  ({t('settings_people_main')})"
                            if len(patients) > 1 and pid == primary else "")
            tk.Label(grid, text=label, font=(FONT, 10), anchor="w").grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=2)
            entry = tk.Entry(grid, width=14, font=(FONT, 10))
            entry.insert(0, (self.cfg.get("nicknames") or {}).get(ctl.person_key(pid), ""))
            entry.grid(row=row, column=1, sticky="w", pady=2)
            for event in ("<FocusOut>", "<Return>"):
                entry.bind(event, lambda _e, p=pid, en=entry: ctl.set_nickname(p, en.get()))
            if len(patients) > 1 and pid != primary:
                self.var(tk.BooleanVar, False)
                v = self.vars[-1]
                v.set(pid in shown)
                tk.Checkbutton(grid, text=t("settings_people_also"), variable=v, font=(FONT, 9),
                               command=lambda p=pid: ctl.toggle_person_shown(p)).grid(
                    row=row, column=2, sticky="w", padx=(10, 0))
        tk.Label(box, text=t("settings_people_note"), font=(FONT, 9), fg="#6b6f76", anchor="w",
                 justify="left", wraplength=380).pack(fill="x", pady=(4, 0))

    def change_account(self):
        self.win.attributes("-topmost", False)   # la finestra dell'account deve stare sopra
        self.ctl.change_account()
        self.win.attributes("-topmost", True)
        self.refresh()

    def set_language(self, code):
        """Cambia la lingua e riapre la finestra già tradotta, sulla stessa scheda."""
        tab = self.notebook.index("current")
        self.ctl.set_language(code)
        self.close()
        SettingsWindow.open(self.ctl, TABS[tab])

    # ---- Valori e avvisi ----
    def tab_values(self, frame):
        cfg, ctl = self.cfg, self.ctl
        box = self.section(frame, t("settings_range"))
        self.range_lbl = tk.Label(box, font=(FONT, 10), anchor="w", justify="left",
                                  wraplength=300)
        self.range_lbl.pack(side="left")
        tk.Button(box, text=t("settings_change"), font=(FONT, 9),
                  command=self.change_range).pack(side="right")

        box = self.section(frame, t("settings_beside"))
        self.radios(box, [(n, t(f"beside_{n}")) for n in TREND_STYLES],
                    cfg.get("trend_style", "arrow"), lambda n: ctl.set_options(trend_style=n))

        # "sotto il valore" nella stessa sezione: la scheda resta abbastanza bassa per
        # gli schermi piccoli
        tk.Label(box, text=t("settings_show_values"), font=(FONT, 9), fg="#6b6f76",
                 anchor="w").pack(fill="x", pady=(6, 0))
        self.check(box, t("menu_delta"), cfg.get("show_delta"),
                   lambda on: ctl.set_options(show_delta=on))

        box = self.section(frame, t("predict_title"))
        self.predict_vars = {}
        for key, label in (("predict", t("predict_show")), ("alert_soon", t("predict_alert"))):
            self.predict_vars[key] = self.check(box, label, cfg.get(key),
                                                lambda on, k=key: self.set_predict(k, on))
        tk.Label(box, text=t("predict_note"), font=(FONT, 9), fg="#6b6f76", anchor="w",
                 justify="left", wraplength=520).pack(fill="x", pady=(4, 0))

    # ---- Avvisi e suoni ----
    def tab_alerts(self, frame):
        cfg, ctl = self.cfg, self.ctl
        box = self.section(frame, t("menu_alerts"))
        self.alert_boxes, self.alert_vars = {}, {}
        for kind in ("low", "high", "stale"):
            v = self.alert_vars[kind] = self.var(tk.BooleanVar, bool(cfg.get(f"alert_{kind}")))
            box_ = tk.Checkbutton(box, variable=v, font=(FONT, 10), anchor="w",
                                  command=lambda k=kind: ctl.toggle_alert(k))
            box_.pack(fill="x")
            self.alert_boxes[kind] = box_
        tk.Label(box, text=t("alert_menu_note"), font=(FONT, 9), fg="#6b6f76",
                 anchor="w").pack(fill="x", pady=(2, 0))

        box = self.section(frame, t("settings_sounds"))
        # le scelte dei suoni restano in sospeso (▶ le fa sentire) finché non si preme
        # Applica: si possono provare tutti senza cambiare niente
        self.pending = {}
        row = tk.Frame(box)
        row.pack(fill="x")
        self.sound_on = self.var(tk.BooleanVar, cfg.get("alert_sound", True))
        tk.Checkbutton(row, text=t("alert_sound_on"), variable=self.sound_on, font=(FONT, 10),
                       command=lambda: self.change(alert_sound=self.sound_on.get())).pack(
            side="left")
        self.volume = tk.Scale(row, from_=0, to=100, orient="horizontal", length=130,
                               showvalue=False)
        self.volume.set(cfg.get("alert_volume", 100))
        self.volume.config(command=lambda v: self.change(alert_volume=int(float(v))))
        self.volume.pack(side="right")
        self.volume.bind("<ButtonRelease-1>", lambda _e: self.preview("low"))
        tk.Label(row, text=t("sound_volume"), font=(FONT, 10)).pack(side="right", padx=(0, 6))

        row = tk.Frame(box)
        row.pack(fill="x", pady=(6, 2))
        tk.Label(row, text=t("sound_pack"), font=(FONT, 10)).pack(side="left")
        self.pack_box = ttk.Combobox(row, state="readonly", width=26)
        self.pack_box.pack(side="left", padx=6)
        self.pack_box.bind("<<ComboboxSelected>>", lambda _e: self.choose_pack())
        tk.Button(row, text=t("sound_import"), font=(FONT, 9),
                  command=self.import_pack).pack(side="left")
        tk.Button(row, text=t("sound_folder"), font=(FONT, 9),
                  command=sound.open_folder).pack(side="left", padx=(4, 0))

        grid = tk.Frame(box)
        grid.pack(fill="x", pady=(2, 0))
        tk.Label(grid, text=t("sound_repeat_head"), font=(FONT, 9), fg="#6b6f76").grid(
            row=0, column=4, sticky="w")
        self.sound_boxes, self.repeat_boxes = {}, {}
        self.repeats = repeats = [0, *REPEAT_CHOICES]
        for row_, kind in enumerate(sound.KINDS, 1):
            tk.Label(grid, text=t(f"sound_kind_{kind}"), font=(FONT, 10), anchor="w").grid(
                row=row_, column=0, sticky="w", padx=(0, 8), pady=2)
            combo = ttk.Combobox(grid, state="readonly", width=30)
            combo.grid(row=row_, column=1, pady=2)
            combo.bind("<<ComboboxSelected>>", lambda _e, k=kind: self.choose_sound(k))
            self.sound_boxes[kind] = combo
            tk.Button(grid, text=t("sound_browse"), font=(FONT, 9),
                      command=lambda k=kind: self.browse_sound(k)).grid(row=row_, column=2, padx=4)
            tk.Button(grid, text="\u25b6", font=(FONT, 9), width=2,
                      command=lambda k=kind: self.preview(k)).grid(row=row_, column=3)
            if kind in ALARMS:
                every = ttk.Combobox(grid, state="readonly", width=8, values=[
                    refresh_label(s) if s else t("repeat_off") for s in repeats])
                every.grid(row=row_, column=4, padx=(8, 0), sticky="w")
                every.bind("<<ComboboxSelected>>", lambda _e, k=kind, c=every: self.change(
                    **{f"repeat_{k}": repeats[c.current()]}))
                self.repeat_boxes[kind] = every
        row = tk.Frame(box)
        row.pack(fill="x", pady=(4, 0))
        self.apply_button = tk.Button(row, text=t("sound_apply"), width=10, state="disabled",
                                      command=self.apply_sounds)
        self.apply_button.pack(side="right", anchor="n", padx=(8, 0))
        tk.Label(row, text=t("sound_note"), font=(FONT, 9), fg="#6b6f76", anchor="w",
                 justify="left", wraplength=470).pack(side="left", fill="x")
        self.refresh_sounds()

    def chosen(self, key):
        """Il valore scelto adesso: quello in sospeso, o quello in uso."""
        return self.pending.get(key, self.cfg.get(key))

    def change(self, **values):
        self.pending.update(values)
        self.apply_button.config(state="normal")

    def preview(self, kind):
        ref = self.chosen(f"sound_{kind}")
        sound.play(ref, self.chosen("alert_volume"))

    def apply_sounds(self):
        if not self.pending:
            return
        changes, self.pending = self.pending, {}
        self.apply_button.config(state="disabled")
        self.ctl.set_options(**changes)
        if not self.cfg.get("alert_sound", True):
            self.ctl.silence_all()
        self.refresh_sounds()

    def refresh_sounds(self):
        """Elenchi di suoni e pacchetti (cambiano importando o aggiungendo cartelle) e le
        scelte di adesso: quelle in sospeso, o quelle in uso (anche se cambiate dal menu
        col clic destro)."""
        for kind, v in self.alert_vars.items():
            v.set(bool(self.cfg.get(f"alert_{kind}")))
        self.sound_on.set(self.chosen("alert_sound") is not False)
        if "alert_volume" not in self.pending:
            self.volume.config(command="")   # .set() lo chiamerebbe
            self.volume.set(self.cfg.get("alert_volume", 100))
            self.volume.config(command=lambda v: self.change(alert_volume=int(float(v))))
        for kind, combo in self.repeat_boxes.items():
            try:
                seconds = max(0, int(self.chosen(f"repeat_{kind}") or 0))
            except (TypeError, ValueError):
                seconds = 0
            seconds = max(10, seconds) if seconds else 0
            combo.current(self.repeats.index(seconds) if seconds in self.repeats else 1)
        groups = sound.choices()
        self.sound_refs = [ref for _group, refs in groups for ref, _label in refs]
        labels = [sound.label(ref) for ref in self.sound_refs]
        for kind, combo in self.sound_boxes.items():
            combo.config(values=labels)
            ref = self.chosen(f"sound_{kind}")
            if ref not in self.sound_refs:
                ref = sound.DEFAULTS[kind]
            combo.current(self.sound_refs.index(ref))
        self.pack_names = [group for group, _refs in groups]
        self.pack_box.config(values=self.pack_names)
        current = self.chosen("sound_pack")
        self.pack_box.current(self.pack_names.index(current) if current in self.pack_names else 0)

    def choose_sound(self, kind):
        self.change(**{f"sound_{kind}": self.sound_refs[self.sound_boxes[kind].current()]})
        self.preview(kind)

    def choose_pack(self):
        self.use_pack(self.pack_names[self.pack_box.current()])

    def use_pack(self, pack):
        """Un pacchetto: un suono per ogni avviso (in sospeso, come le altre scelte)."""
        self.change(sound_pack=pack, **{f"sound_{k}": ref
                                        for k, ref in sound.pack_sounds(pack).items()})
        self.refresh_sounds()
        self.preview("low")

    def ask_files(self, multiple):
        types = [(t("sound_files"), " ".join(f"*{e}" for e in sound.AUDIO_EXT + (".zip",)))]
        self.win.attributes("-topmost", False)   # la finestra per scegliere deve stare sopra
        ask = filedialog.askopenfilenames if multiple else filedialog.askopenfilename
        paths = ask(parent=self.win, title=t("sound_browse"), filetypes=types)
        self.win.attributes("-topmost", True)
        return list(paths) if multiple else ([paths] if paths else [])

    def import_pack(self):
        """Un .zip o dei file audio diventano un pacchetto (dal nome dello zip o della
        cartella), scelto subito (da applicare)."""
        paths = self.ask_files(multiple=True)
        if not paths:
            return
        try:
            pack, refs = sound.import_files(paths, pack=sound.safe_name(
                os.path.basename(os.path.dirname(paths[0]))))
        except (OSError, ValueError) as e:
            messagebox.showerror(t("settings_sounds"), str(e), parent=self.win)
            return
        if self.readable(refs):
            self.use_pack(pack)
        else:
            self.refresh_sounds()

    def readable(self, refs):
        """Prova a leggere i file importati (su Windows li converte già adesso, tutti
        insieme) e dice quali non si possono suonare. Vero se almeno uno va bene."""
        if not refs:
            return False
        self.win.config(cursor="watch")
        self.win.update_idletasks()
        sound.decode_all([sound.resolve(ref) for ref in refs])
        bad = [ref for ref in refs if not sound.check(ref)]
        self.win.config(cursor="")
        if bad:
            messagebox.showwarning(t("settings_sounds"), t("sound_unreadable", names=", ".join(
                ref.partition("/")[2] for ref in bad[:8])), parent=self.win)
        return len(bad) < len(refs)

    def browse_sound(self, kind):
        paths = self.ask_files(multiple=False)
        if not paths:
            return
        try:
            pack, refs = sound.import_files(paths)
        except (OSError, ValueError) as e:
            messagebox.showerror(t("settings_sounds"), str(e), parent=self.win)
            return
        if not self.readable(refs):
            self.refresh_sounds()
        elif paths[0].lower().endswith(".zip"):
            self.use_pack(pack)
        else:
            self.change(**{f"sound_{kind}": refs[0]})
            self.refresh_sounds()
            self.preview(kind)

    def set_predict(self, key, on):
        """La stima della tendenza si accende solo dopo aver letto (una volta) cosa è e
        cosa non è."""
        if on and not self.cfg.get("predict_ack"):
            if not messagebox.askokcancel(t("predict_title"), t("predict_disclaimer"),
                                          icon="warning", parent=self.win):
                self.predict_vars[key].set(False)
                return
            self.cfg["predict_ack"] = True
        self.ctl.set_options(**{key: on})
        self.win.lift()

    def change_range(self):
        values = ask_range(self.cfg, self.win)
        if values:
            self.cfg.update(values)
            self.apply()

    # ---- Aspetto ----
    def tab_look(self, frame):
        cfg = self.cfg
        left, right = tk.Frame(frame), tk.Frame(frame)
        left.grid(row=0, column=0, sticky="n", padx=(0, 7))
        right.grid(row=0, column=1, sticky="n", padx=(7, 0))

        box = self.section(left, t("settings_theme"))
        self.theme_var = self.radios(box, [(n, t(f"theme_{n}")) for n in THEMES],
                                     cfg.get("theme", "auto"), self.set_theme)

        box = self.section(left, t("settings_colors"))
        self.palette_var = self.radios(box, [(n, t(f"palette_{n}")) for n in PALETTES],
                                       cfg.get("palette", "standard"), self.set_palette)
        rows = tk.Frame(box)
        rows.pack(fill="x", pady=(8, 0))
        self.samples = {}
        for row, kind in enumerate(COLOR_KEYS):
            sample = tk.Label(rows, width=5, font=(FONT, 12, "bold"))
            self.samples[kind] = sample
            self.row(rows, row, t(f"color_{kind}"), sample, lambda k=kind: self.pick_value(k))
        tk.Button(box, text=t("settings_reset_colors"), font=(FONT, 9),
                  command=self.reset_value_colors).pack(anchor="w", pady=(8, 0))

        self.ui_box = box = self.section(right, "")
        rows = tk.Frame(box)
        rows.pack(fill="x")
        self.swatches = {}
        for row, key in enumerate(UI_KEYS):
            swatch = tk.Label(rows, width=5, relief="solid", bd=1)
            self.swatches[key] = swatch
            self.row(rows, row, t(f"ui_{key}"), swatch, lambda k=key: self.pick_ui(k))
        tk.Button(box, text=t("settings_reset_colors"), font=(FONT, 9),
                  command=self.reset_ui_colors).pack(anchor="w", pady=(8, 0))

        if sys.platform == "win32":   # il valore sulla barra c'è solo su Windows
            box = self.section(right, t("settings_taskbar"))
            self.transparent_var = self.check(box, t("settings_transparent"),
                                              cfg["taskbar_transparent"], self.set_transparent)
            rows = tk.Frame(box)
            rows.pack(fill="x", pady=(4, 0))
            self.taskbar_swatches, self.taskbar_buttons = {}, {}
            for row, key in enumerate(("taskbar_bg", "taskbar_text")):
                swatch = tk.Label(rows, width=5, relief="solid", bd=1)
                self.taskbar_swatches[key] = swatch
                self.taskbar_buttons[key] = self.row(rows, row, t(f"settings_{key}"), swatch,
                                                     lambda k=key: self.pick_taskbar(k))
            tk.Button(box, text=t("settings_reset_colors"), font=(FONT, 9),
                      command=self.reset_taskbar).pack(anchor="w", pady=(8, 0))

    # ---- Elementi ----
    def tab_elements(self, frame):
        cfg, ctl = self.cfg, self.ctl
        box = self.section(frame, t("menu_show"))
        self.element_vars = {}
        for element in ELEMENTS:
            if ctl.available(element):
                v = self.var(tk.BooleanVar, ctl.shown(element))
                self.element_vars[element] = v
                tk.Checkbutton(box, text=element_name(element), variable=v, font=(FONT, 10),
                               anchor="w", command=lambda e=element: self.toggle_element(e)
                               ).pack(fill="x")

        if sys.platform == "win32":
            from .taskbar import SIZES
            box = self.section(frame, t("settings_taskbar"))
            tk.Label(box, text=t("menu_size"), font=(FONT, 10), anchor="w").pack(fill="x")
            row = tk.Frame(box)
            row.pack(fill="x")
            self.radios(row, [(scale, t(key)) for scale, key in SIZES],
                        float(cfg["taskbar_scale"]),
                        lambda scale: ctl.set_options(taskbar_scale=scale), side="left")
            self.check(box, t("menu_hover_chart"), cfg.get("hover_chart", True),
                       lambda on: ctl.set_options(hover_chart=on))

        from .desktop import HOURS_CHOICES
        box = self.section(frame, t("mode_desktop"))
        tk.Label(box, text=t("menu_hours"), font=(FONT, 10), anchor="w").pack(fill="x")
        row = tk.Frame(box)
        row.pack(fill="x")
        self.radios(row, [(h, t("desk_hours", h=h)) for h in HOURS_CHOICES],
                    int(cfg["desktop_hours"]),
                    lambda h: ctl.set_options(desktop_hours=h), side="left")
        self.check(box, t("menu_on_top"), cfg.get("desktop_on_top"),
                   lambda on: self.set_and_lift(desktop_on_top=on))
        self.check(box, t("menu_over_fullscreen"), cfg.get("desktop_over_fullscreen"),
                   lambda on: self.ctl.set_options(desktop_over_fullscreen=on))
        self.check(box, t("menu_lock"), cfg.get("desktop_locked"),
                   lambda on: self.set_and_lift(desktop_locked=on))
        row = tk.Frame(box)
        row.pack(fill="x", pady=(4, 0))
        tk.Label(row, text=t("settings_opacity"), font=(FONT, 10)).pack(side="left")
        # si vede subito sul pannello; si salva quando si lascia il cursore
        opacity = tk.Scale(row, from_=30, to=100, orient="horizontal", length=200,
                           showvalue=True, command=self.preview_opacity)
        opacity.set(round(float(cfg.get("desktop_alpha") or 0.92) * 100))
        opacity.pack(side="left", padx=(10, 0))
        opacity.bind("<ButtonRelease-1>", lambda _e: self.save_opacity(opacity.get()))

    def toggle_element(self, element):
        self.ctl.toggle_element(element)
        for name, v in self.element_vars.items():   # almeno uno resta acceso
            v.set(self.ctl.shown(name))
        self.win.lift()

    def preview_opacity(self, value):
        panel = self.ctl.views.get("desktop")
        if panel is not None:
            try:
                panel.root.attributes("-alpha", int(value) / 100)
            except tk.TclError:
                pass

    def save_opacity(self, value):
        self.cfg["desktop_alpha"] = int(value) / 100
        save_config(self.cfg)

    def set_and_lift(self, **changes):
        self.ctl.set_options(**changes)   # ricrea gli elementi: questa finestra resta davanti
        self.win.lift()

    # ---- Connessioni (ponte locale, vedi bridge.py) ----
    def tab_connect(self, frame):
        cfg = self.cfg
        note = {"font": (FONT, 9), "fg": "#6b6f76", "anchor": "w", "justify": "left",
                "wraplength": 420}

        box = self.section(frame, t("bridge_http"))
        tk.Label(box, text=t("bridge_http_note"), **note).pack(fill="x")
        self.check(box, t("bridge_http_on"), cfg.get("bridge_http"),
                   lambda on: self.set_bridge(bridge_http=on))
        self.check(box, t("bridge_lan"), cfg.get("bridge_lan"),
                   lambda on: self.set_bridge(bridge_lan=on))
        grid = tk.Frame(box)
        grid.pack(fill="x", pady=(4, 0))
        self.http_fields = {
            "bridge_port": self.field(grid, 0, t("bridge_port"), cfg.get("bridge_port"), 7),
            "bridge_token": self.field(grid, 1, t("bridge_token"), cfg.get("bridge_token"), 20),
        }
        tk.Button(grid, text=t("bridge_apply"), font=(FONT, 9), command=self.apply_http).grid(
            row=1, column=2, padx=(8, 0))
        row = tk.Frame(box)
        row.pack(fill="x", pady=(6, 0))
        self.http_lbl = tk.Label(row, font=(FONT, 10), anchor="w", justify="left")
        self.http_lbl.pack(side="left")
        self.http_copy = tk.Button(row, text=t("bridge_copy"), font=(FONT, 9), command=self.copy_url)
        self.http_open = tk.Button(row, text=t("bridge_open"), font=(FONT, 9), command=self.open_url)

        box = self.section(frame, t("bridge_mqtt"))
        tk.Label(box, text=t("bridge_mqtt_note"), **note).pack(fill="x")
        self.check(box, t("bridge_mqtt_on"), cfg.get("mqtt"), lambda on: self.set_bridge(mqtt=on))
        grid = tk.Frame(box)
        grid.pack(fill="x", pady=(4, 0))
        self.mqtt_fields = {
            "mqtt_host": self.field(grid, 0, t("bridge_host"), cfg.get("mqtt_host"), 20),
            "mqtt_port": self.field(grid, 1, t("bridge_port"), cfg.get("mqtt_port"), 7),
            "mqtt_user": self.field(grid, 2, t("bridge_user"), cfg.get("mqtt_user"), 20),
            "mqtt_password": self.field(grid, 3, t("bridge_password"), "", 20, show="•"),
            "mqtt_topic": self.field(grid, 4, t("bridge_topic"), cfg.get("mqtt_topic"), 20),
        }
        self.check(box, t("bridge_discovery"), cfg.get("mqtt_discovery", True),
                   lambda on: self.set_bridge(mqtt_discovery=on))
        row = tk.Frame(box)
        row.pack(fill="x", pady=(4, 0))
        tk.Button(row, text=t("bridge_apply"), font=(FONT, 9), command=self.apply_mqtt).pack(side="left")
        self.mqtt_lbl = tk.Label(row, font=(FONT, 10), anchor="w")
        self.mqtt_lbl.pack(side="left", padx=(10, 0))
        self.bridge_status()

    @staticmethod
    def field(grid, row, label, value, width, show=""):
        tk.Label(grid, text=label, font=(FONT, 10), anchor="w").grid(row=row, column=0, sticky="w", pady=1)
        entry = tk.Entry(grid, width=width, font=(FONT, 10), show=show)
        entry.insert(0, "" if value is None else str(value))
        entry.grid(row=row, column=1, sticky="w", padx=(8, 0), pady=1)
        return entry

    def set_bridge(self, **changes):
        self.cfg.update(changes)
        save_config(self.cfg)
        if self.ctl.bridge:
            self.ctl.bridge.reconfigure()
            self.ctl.bridge.update()
        self.win.after(300, self.bridge_status)

    def apply_http(self):
        try:
            port = int(self.http_fields["bridge_port"].get())
            if not 1024 <= port <= 65535:
                raise ValueError
        except ValueError:
            self.http_lbl.config(text=t("bridge_bad_port"), fg="#c62828")
            return
        self.set_bridge(bridge_port=port, bridge_token=self.http_fields["bridge_token"].get().strip())

    def apply_mqtt(self):
        fields = self.mqtt_fields
        try:
            port = int(fields["mqtt_port"].get())
        except ValueError:
            port = 1883
        user = fields["mqtt_user"].get().strip()
        password = fields["mqtt_password"].get()
        if password:
            credentials.set_password(user or "mqtt", password, "mqtt")
            fields["mqtt_password"].delete(0, "end")
        if self.ctl.bridge:
            self.ctl.bridge._mqtt_conf = None   # riconnette anche se cambia solo la password
        self.set_bridge(mqtt_host=fields["mqtt_host"].get().strip(), mqtt_port=port,
                        mqtt_user=user, mqtt_topic=fields["mqtt_topic"].get().strip() or "glucobar")

    def bridge_status(self):
        """Indirizzi e stato del collegamento, aggiornati finché la finestra è aperta."""
        if not self.win.winfo_exists() or not hasattr(self, "http_lbl"):
            return
        bridge = self.ctl.bridge
        urls = bridge.addresses() if bridge else []
        self.http_copy.pack_forget()
        self.http_open.pack_forget()
        if not self.cfg.get("bridge_http"):
            self.http_lbl.config(text=t("bridge_off"), fg="#6b6f76")
        elif bridge and bridge.http_error:
            self.http_lbl.config(text=t("bridge_error", e=bridge.http_error), fg="#c62828")
        elif urls:
            self.http_lbl.config(text=t("bridge_running", url=urls[0]), fg="#1e9e4a")
            self.http_copy.pack(side="left", padx=(10, 0))
            self.http_open.pack(side="left", padx=(6, 0))
        mqtt = bridge.mqtt if bridge else None
        if not self.cfg.get("mqtt"):
            self.mqtt_lbl.config(text=t("bridge_off"), fg="#6b6f76")
        elif mqtt and mqtt.status == "ok":
            self.mqtt_lbl.config(text=t("bridge_mqtt_ok"), fg="#1e9e4a")
        elif mqtt and mqtt.status.startswith("error"):
            self.mqtt_lbl.config(text=t("bridge_mqtt_error", e=mqtt.status[7:]), fg="#c62828")
        else:
            self.mqtt_lbl.config(text=t("bridge_mqtt_wait"), fg="#6b6f76")
        self.win.after(2000, self.bridge_status)

    def bridge_url(self):
        urls = self.ctl.bridge.addresses() if self.ctl.bridge else []
        token = (self.cfg.get("bridge_token") or "").strip()
        return (urls[0] + (f"/?token={token}" if token else "")) if urls else None

    def copy_url(self):
        url = self.bridge_url()
        if url:
            self.win.clipboard_clear()
            self.win.clipboard_append(url)

    def open_url(self):
        import webbrowser
        url = self.bridge_url()
        if url:
            webbrowser.open(url)

    # ---- Aggiornamenti ----
    def tab_updates(self, frame):
        cfg, ctl = self.cfg, self.ctl
        box = self.section(frame, t("tab_updates"))
        tk.Label(box, text=t("settings_version", v=__version__), font=(FONT, 10),
                 anchor="w").pack(fill="x")
        row = tk.Frame(box)
        row.pack(fill="x", pady=(8, 4))
        self.check_button = tk.Button(row, text=t("settings_updates_now"), font=(FONT, 9),
                                      command=self.check_now)
        self.check_button.pack(side="left")
        self.install_button = tk.Button(row, font=(FONT, 9), command=self.install)
        self.update_lbl = tk.Label(box, font=(FONT, 10), anchor="w", justify="left",
                                   wraplength=360)
        self.update_lbl.pack(fill="x")
        self.check(box, t("menu_update_check"), cfg.get("update_check", True),
                   lambda _on: ctl.toggle_update_check())
        if updates.can_install():
            self.check(box, t("menu_auto_update"), cfg.get("auto_update"),
                       lambda _on: ctl.toggle_auto_update())
        if ctl.update:
            self.show_update(ctl.update, None)

    def check_now(self):
        self.check_button.config(state="disabled")
        self.install_button.pack_forget()
        self.update_lbl.config(text=t("update_checking"))
        self.ctl.check_updates(force=True, done=self.show_update)

    def show_update(self, release, error):
        if not self.win.winfo_exists():
            return
        self.check_button.config(state="normal")
        if error:
            self.update_lbl.config(text=t("update_check_failed", e=error))
        elif release and updates.is_newer(release["version"]):
            self.update_lbl.config(text=t("update_found", v=release["version"]))
            label = t("update_install" if self.ctl.can_install_update() else "update_open")
            self.install_button.config(text=label)
            self.install_button.pack(side="left", padx=(8, 0))
        else:
            self.update_lbl.config(text=t("update_latest"))

    def install(self):
        if self.ctl.can_install_update():
            self.ctl.install_update()
        else:
            self.ctl.open_update()

    # ---- applicare subito ----
    def mode(self):
        return "light" if is_light(self.cfg) else "dark"

    def apply(self):
        save_config(self.cfg)
        self.ctl.restyle()   # ricrea gli elementi coi colori nuovi...
        self.refresh()
        self.win.lift()      # ...e questa finestra resta davanti a loro

    def refresh(self):
        """Esempi colorati come li si vedrà adesso, soglie, avvisi e account."""
        cfg = self.cfg
        pal = palette(cfg)
        for kind, sample in self.samples.items():
            mgdl = SAMPLES[kind](cfg)
            color = pal.stale if kind == "stale" else pal.value(cfg, mgdl)
            sample.config(text=fmt_value(cfg, mgdl), fg=color, bg=pal.bg)
        for key, swatch in self.swatches.items():
            swatch.config(bg=getattr(pal, key))
        self.ui_box.config(text=t(f"settings_ui_{self.mode()}"))
        if sys.platform == "win32":
            from .taskbar import taskbar_colors
            bg, dim = taskbar_colors()
            colors = {"taskbar_bg": cfg["taskbar_bg"] or bg,
                      "taskbar_text": cfg.get("taskbar_text") or dim}
            for key, swatch in self.taskbar_swatches.items():
                swatch.config(bg=colors[key])
            # con lo sfondo trasparente il colore dello sfondo non si vede
            self.taskbar_buttons["taskbar_bg"].config(
                state="disabled" if cfg["taskbar_transparent"] else "normal")
        unit = cfg["unit"]
        self.range_lbl.config(text=t("settings_range_now", low=fmt_value(cfg, cfg["low"]),
                                     high=fmt_value(cfg, cfg["high"]),
                                     very_high=fmt_value(cfg, cfg["very_high"]), unit=unit))
        for kind, box in self.alert_boxes.items():
            box.config(text=self.ctl.alert_label(kind))
        sensor = t(f"sensor_{cfg.get('source', 'libre')}").split(" · ")[0]
        self.account_lbl.config(text=f"{sensor}\n{cfg.get('email') or '-'}")

    def choose(self, current, title):
        _rgb, color = colorchooser.askcolor(color=current, title=title, parent=self.win)
        return color.lower() if color else None

    def set_theme(self, name):
        self.cfg["theme"] = name
        self.apply()

    def set_palette(self, name):
        # una tavolozza nuova parte pulita: i colori del valore scelti a mano tornano i suoi
        self.cfg["palette"] = name
        for key in COLOR_KEYS.values():
            self.cfg[key] = None
        self.apply()

    def pick_value(self, kind):
        cfg = self.cfg
        pal = palette(cfg)
        current = pal.stale if kind == "stale" else pal.value(cfg, SAMPLES[kind](cfg))
        color = self.choose(current, t(f"color_{kind}"))
        if color:
            cfg[COLOR_KEYS[kind]] = color
            self.apply()

    def pick_ui(self, key):
        color = self.choose(getattr(palette(self.cfg), key), t(f"ui_{key}"))
        if color:
            colors = dict(self.cfg.get("ui_colors") or {})
            colors[self.mode()] = dict(colors.get(self.mode()) or {}, **{key: color})
            self.cfg["ui_colors"] = colors
            self.apply()

    def pick_taskbar(self, key):
        swatch = self.taskbar_swatches[key]
        color = self.choose(swatch.cget("bg"), t(f"settings_{key}"))
        if color:
            self.cfg[key] = color
            self.apply()

    def set_transparent(self, on):
        self.cfg["taskbar_transparent"] = on
        self.apply()

    def reset_value_colors(self):
        for key in COLOR_KEYS.values():
            self.cfg[key] = None
        self.apply()

    def reset_ui_colors(self):
        colors = dict(self.cfg.get("ui_colors") or {})
        colors.pop(self.mode(), None)
        self.cfg["ui_colors"] = colors
        self.apply()

    def reset_taskbar(self):
        self.cfg.update(taskbar_bg=None, taskbar_text=None, taskbar_transparent=True)
        self.transparent_var.set(True)
        self.apply()

    def close(self):
        if getattr(self, "pending", None):
            answer = messagebox.askyesnocancel(t("settings_sounds"), t("sound_pending"),
                                               parent=self.win)
            if answer is None:
                return
            if answer:
                self.apply_sounds()
        SettingsWindow.current = None
        self.win.destroy()
