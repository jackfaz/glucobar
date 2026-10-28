"""Finestra Impostazioni (clic destro → Impostazioni…), divisa in schede per argomento:
Generale, Valori e avvisi, Aspetto, Elementi, Aggiornamenti. Ogni scelta si applica
subito a tutti gli elementi aperti (barra, icona, finestrella, pannello), così si vede
com'è prima di chiudere. Il menu col clic destro tiene solo le azioni rapide.

I colori del valore valgono con entrambi i temi; quelli di finestrella e pannello sono
del tema in uso (chiaro o scuro), così cambiare tema non li mescola."""

import sys
import tkinter as tk
from tkinter import colorchooser, ttk

from . import __version__, autostart, updates
from .config import ELEMENTS, save_config
from .i18n import LANGUAGES, element_name, refresh_label, t
from .theme import COLOR_KEYS, PALETTES, THEMES, UI_KEYS, is_light, palette
from .ui_common import FONT, ask_range, fmt_value

# colore del valore -> esempio in mg/dL (dalle soglie dell'utente)
SAMPLES = {
    "in_range": lambda cfg: (cfg["low"] + cfg["high"]) // 2,
    "high": lambda cfg: (cfg["high"] + cfg["very_high"]) // 2,
    "very_high": lambda cfg: cfg["very_high"] + 30,
    "low": lambda cfg: max(40, cfg["low"] - 10),
    "stale": lambda cfg: (cfg["low"] + cfg["high"]) // 2,
}
TABS = ("general", "values", "look", "elements", "updates")


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
        self.tab_look(self.tab("look"))
        self.tab_elements(self.tab("elements"))
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
        box = tk.LabelFrame(parent, text=title, font=(FONT, 10), padx=10, pady=6)
        box.pack(fill="x", pady=(10, 0), **pack)
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

        box = self.section(frame, t("menu_alerts"))
        self.alert_boxes = {}
        for kind in ("low", "high", "stale"):
            v = self.var(tk.BooleanVar, bool(cfg.get(f"alert_{kind}")))
            box_ = tk.Checkbutton(box, variable=v, font=(FONT, 10), anchor="w",
                                  command=lambda k=kind: ctl.toggle_alert(k))
            box_.pack(fill="x")
            self.alert_boxes[kind] = box_
        tk.Label(box, text=t("alert_menu_note"), font=(FONT, 9), fg="#6b6f76",
                 anchor="w").pack(fill="x", pady=(4, 0))

        box = self.section(frame, t("settings_show_values"))
        self.check(box, t("menu_delta"), cfg.get("show_delta"),
                   lambda on: ctl.set_options(show_delta=on))

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
        self.check(box, t("menu_lock"), cfg.get("desktop_locked"),
                   lambda on: self.set_and_lift(desktop_locked=on))

    def toggle_element(self, element):
        self.ctl.toggle_element(element)
        for name, v in self.element_vars.items():   # almeno uno resta acceso
            v.set(self.ctl.shown(name))
        self.win.lift()

    def set_and_lift(self, **changes):
        self.ctl.set_options(**changes)   # ricrea gli elementi: questa finestra resta davanti
        self.win.lift()

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
        alert_labels = {
            "low": t("alert_menu_low", v=f"{fmt_value(cfg, cfg['low'])} {unit}"),
            "high": t("alert_menu_high", v=f"{fmt_value(cfg, cfg['very_high'])} {unit}"),
            "stale": t("alert_menu_stale", n=cfg["stale_minutes"]),
        }
        for kind, box in self.alert_boxes.items():
            box.config(text=alert_labels[kind])
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
        SettingsWindow.current = None
        self.win.destroy()
