"""Finestra Impostazioni (clic destro → Impostazioni…): tema, colori del valore e soglie.
Ogni scelta si applica subito a tutti gli elementi aperti (barra, icona, finestrella,
pannello), così si vede com'è prima di chiudere."""

import tkinter as tk
from tkinter import colorchooser

from .config import save_config
from .i18n import t
from .theme import COLOR_KEYS, PALETTES, THEMES, palette
from .ui_common import FONT, ask_range, fmt_value

# colore -> valore di esempio in mg/dL (dalle soglie dell'utente)
SAMPLES = {
    "in_range": lambda cfg: (cfg["low"] + cfg["high"]) // 2,
    "high": lambda cfg: (cfg["high"] + cfg["very_high"]) // 2,
    "very_high": lambda cfg: cfg["very_high"] + 30,
    "low": lambda cfg: max(40, cfg["low"] - 10),
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
        pad = {"padx": 14, "pady": (10, 0)}

        box = tk.LabelFrame(win, text=t("settings_theme"), font=(FONT, 10), padx=10, pady=6)
        box.pack(fill="x", **pad)
        self.theme_var = tk.StringVar(master=win, value=cfg.get("theme", "auto"))
        for name in THEMES:
            tk.Radiobutton(box, text=t(f"theme_{name}"), value=name, variable=self.theme_var,
                           font=(FONT, 10), anchor="w", command=self.set_theme).pack(fill="x")

        box = tk.LabelFrame(win, text=t("settings_colors"), font=(FONT, 10), padx=10, pady=6)
        box.pack(fill="x", **pad)
        self.palette_var = tk.StringVar(master=win, value=cfg.get("palette", "standard"))
        for name in PALETTES:
            tk.Radiobutton(box, text=t(f"palette_{name}"), value=name, variable=self.palette_var,
                           font=(FONT, 10), anchor="w", command=self.set_palette).pack(fill="x")
        rows = tk.Frame(box)
        rows.pack(fill="x", pady=(8, 0))
        self.samples = {}
        for row, kind in enumerate(COLOR_KEYS):
            tk.Label(rows, text=t(f"color_{kind}"), font=(FONT, 10), anchor="w").grid(
                row=row, column=0, sticky="w", pady=2)
            sample = tk.Label(rows, width=6, font=(FONT, 12, "bold"), relief="flat")
            sample.grid(row=row, column=1, padx=10, pady=2)
            self.samples[kind] = sample
            tk.Button(rows, text=t("settings_change"), font=(FONT, 9),
                      command=lambda k=kind: self.pick(k)).grid(row=row, column=2, pady=2)
        rows.columnconfigure(0, weight=1)
        tk.Button(box, text=t("settings_reset_colors"), font=(FONT, 9),
                  command=self.reset_colors).pack(anchor="w", pady=(8, 0))

        box = tk.LabelFrame(win, text=t("settings_range"), font=(FONT, 10), padx=10, pady=6)
        box.pack(fill="x", **pad)
        self.range_lbl = tk.Label(box, font=(FONT, 10), anchor="w", justify="left")
        self.range_lbl.pack(side="left")
        tk.Button(box, text=t("settings_change"), font=(FONT, 9),
                  command=self.change_range).pack(side="right")

        tk.Label(win, text=t("settings_live"), font=(FONT, 9), fg="#6b6f76").pack(
            anchor="w", padx=14, pady=(8, 0))
        tk.Button(win, text=t("button_close"), width=10, command=self.close,
                  default="active").pack(anchor="e", padx=14, pady=(8, 14))
        win.bind("<Escape>", lambda _e: self.close())
        self.refresh()

        win.update_idletasks()
        win.geometry(f"+{(win.winfo_screenwidth() - win.winfo_reqwidth()) // 2}"
                     f"+{(win.winfo_screenheight() - win.winfo_reqheight()) // 4}")
        win.attributes("-topmost", True)
        win.focus_force()

    # ---- applicare subito ----
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
            sample.config(text=fmt_value(cfg, mgdl), fg=pal.value(cfg, mgdl), bg=pal.bg)
        unit = cfg["unit"]
        self.range_lbl.config(text=t("settings_range_now", low=fmt_value(cfg, cfg["low"]),
                                     high=fmt_value(cfg, cfg["high"]),
                                     very_high=fmt_value(cfg, cfg["very_high"]), unit=unit))

    def set_theme(self):
        self.cfg["theme"] = self.theme_var.get()
        self.apply()

    def set_palette(self):
        # una tavolozza nuova parte pulita: i colori scelti a mano tornano i suoi
        self.cfg["palette"] = self.palette_var.get()
        for key in COLOR_KEYS.values():
            self.cfg[key] = None
        self.apply()

    def pick(self, kind):
        cfg = self.cfg
        current = palette(cfg).value(cfg, SAMPLES[kind](cfg))
        _rgb, color = colorchooser.askcolor(color=current, title=t(f"color_{kind}"),
                                            parent=self.win)
        if color:
            cfg[COLOR_KEYS[kind]] = color.lower()
            self.apply()

    def reset_colors(self):
        for key in COLOR_KEYS.values():
            self.cfg[key] = None
        self.apply()

    def change_range(self):
        values = ask_range(self.cfg, self.win)
        if values:
            self.cfg.update(values)
            self.apply()

    def close(self):
        SettingsWindow.current = None
        self.win.destroy()
