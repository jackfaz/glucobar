"""Finestra Impostazioni (clic destro → Impostazioni…): tema, tutti i colori e soglie.
Ogni scelta si applica subito a tutti gli elementi aperti (barra, icona, finestrella,
pannello), così si vede com'è prima di chiudere.

I colori del valore valgono con entrambi i temi; quelli di finestrella e pannello sono
del tema in uso (chiaro o scuro), così cambiare tema non li mescola."""

import sys
import tkinter as tk
from tkinter import colorchooser

from .config import save_config
from .i18n import t
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


class SettingsWindow:
    current = None   # una finestra sola: riaprendola torna in primo piano

    @classmethod
    def open(cls, ctl):
        if cls.current and cls.current.win.winfo_exists():
            cls.current.win.deiconify()
            cls.current.win.lift()
            cls.current.win.focus_force()
            return
        cls.current = cls(ctl)

    def __init__(self, ctl):
        self.ctl = ctl
        self.cfg = cfg = ctl.cfg
        self.win = win = tk.Toplevel(ctl.root)
        win.title(t("settings_title"))
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", self.close)
        left, right = tk.Frame(win), tk.Frame(win)
        left.grid(row=0, column=0, sticky="n", padx=(14, 7))
        right.grid(row=0, column=1, sticky="n", padx=(7, 14))

        box = self.section(left, t("settings_theme"))
        self.theme_var = tk.StringVar(master=win, value=cfg.get("theme", "auto"))
        for name in THEMES:
            tk.Radiobutton(box, text=t(f"theme_{name}"), value=name, variable=self.theme_var,
                           font=(FONT, 10), anchor="w", command=self.set_theme).pack(fill="x")

        box = self.section(left, t("settings_colors"))
        self.palette_var = tk.StringVar(master=win, value=cfg.get("palette", "standard"))
        for name in PALETTES:
            tk.Radiobutton(box, text=t(f"palette_{name}"), value=name, variable=self.palette_var,
                           font=(FONT, 10), anchor="w", command=self.set_palette).pack(fill="x")
        rows = tk.Frame(box)
        rows.pack(fill="x", pady=(8, 0))
        self.samples = {}
        for row, kind in enumerate(COLOR_KEYS):
            sample = tk.Label(rows, width=5, font=(FONT, 12, "bold"))
            self.samples[kind] = sample
            self.row(rows, row, t(f"color_{kind}"), sample, lambda k=kind: self.pick_value(k))
        tk.Button(box, text=t("settings_reset_colors"), font=(FONT, 9),
                  command=self.reset_value_colors).pack(anchor="w", pady=(8, 0))

        box = self.section(left, t("settings_range"))
        self.range_lbl = tk.Label(box, font=(FONT, 10), anchor="w", justify="left",
                                  wraplength=260)
        self.range_lbl.pack(side="left")
        tk.Button(box, text=t("settings_change"), font=(FONT, 9),
                  command=self.change_range).pack(side="right")

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
            self.transparent_var = tk.BooleanVar(master=win,
                                                 value=bool(cfg["taskbar_transparent"]))
            tk.Checkbutton(box, text=t("settings_transparent"), variable=self.transparent_var,
                           font=(FONT, 10), anchor="w",
                           command=self.set_transparent).pack(fill="x")
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

        bottom = tk.Frame(win)
        bottom.grid(row=1, column=0, columnspan=2, sticky="we", padx=14, pady=(10, 14))
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

    @staticmethod
    def section(parent, title):
        box = tk.LabelFrame(parent, text=title, font=(FONT, 10), padx=10, pady=6)
        box.pack(fill="x", pady=(10, 0))
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

    # ---- applicare subito ----
    def mode(self):
        return "light" if is_light(self.cfg) else "dark"

    def apply(self):
        save_config(self.cfg)
        self.ctl.restyle()   # ricrea gli elementi coi colori nuovi...
        self.refresh()
        self.win.lift()      # ...e questa finestra resta davanti a loro

    def refresh(self):
        """Esempi colorati come li si vedrà adesso, e le soglie nell'unità scelta."""
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
        self.range_lbl.config(text=t("settings_range_now", low=fmt_value(cfg, cfg["low"]),
                                     high=fmt_value(cfg, cfg["high"]),
                                     very_high=fmt_value(cfg, cfg["very_high"]),
                                     unit=cfg["unit"]))

    def choose(self, current, title):
        _rgb, color = colorchooser.askcolor(color=current, title=title, parent=self.win)
        return color.lower() if color else None

    def set_theme(self):
        self.cfg["theme"] = self.theme_var.get()
        self.apply()

    def set_palette(self):
        # una tavolozza nuova parte pulita: i colori del valore scelti a mano tornano i suoi
        self.cfg["palette"] = self.palette_var.get()
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

    def set_transparent(self):
        self.cfg["taskbar_transparent"] = self.transparent_var.get()
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

    def change_range(self):
        values = ask_range(self.cfg, self.win)
        if values:
            self.cfg.update(values)
            self.apply()

    def close(self):
        SettingsWindow.current = None
        self.win.destroy()
