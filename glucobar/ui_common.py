"""Parti comuni alle interfacce: formati, finestre di dialogo, credenziali."""

import os
import sys
import time
import tkinter as tk
from tkinter import simpledialog

from . import credentials, stats
from .config import save_config
from .i18n import t
from .nightscout import normalize_url
from .sources import TREND_ARROWS, region_options, source_options

# Carattere dell'interfaccia: Segoe UI su Windows (e per le anteprime generate su
# Linux), quello di sistema sul Mac
FONT = "Helvetica Neue" if sys.platform == "darwin" else "Segoe UI"

GREY = "#9a9da3"   # valore vecchio, su qualsiasi sfondo


def fmt_value(cfg, mgdl):
    if cfg["unit"] == "mmol/L":
        return f"{mgdl / 18.016:.1f}"
    return f"{mgdl:.0f}"


def fmt_delta(cfg, delta):
    """Variazione con il segno, nell'unità scelta: "+5", "-12", "+0.3"."""
    if cfg["unit"] == "mmol/L":
        return f"{delta / 18.016:+.1f}"
    return f"{delta:+.0f}"


TREND_STYLES = ("arrow", "delta", "both")


def beside_value(cfg, history, c):
    """Cosa scrivere accanto al valore (trend_style): la freccia, la variazione (delta) al
    suo posto, o tutte e due. Senza una lettura precedente da cui calcolare il delta resta
    la freccia; con il valore vecchio niente."""
    if is_stale(cfg, c):
        return ""
    arrow = TREND_ARROWS.get(c["trend"], "")
    style = cfg.get("trend_style", "arrow")
    delta = stats.delta(history, c) if style in ("delta", "both") else None
    if delta is None:
        return arrow
    delta = fmt_delta(cfg, delta)
    return delta if style == "delta" else f"{arrow} {delta}".strip()


def delta_beside(cfg):
    """Il delta è già accanto al valore: sotto non va ripetuto."""
    return cfg.get("trend_style", "arrow") in ("delta", "both")


def age_minutes(measurement):
    return max(0, int((time.time() - measurement["time"]) // 60))


def is_stale(cfg, measurement):
    return age_minutes(measurement) >= cfg["stale_minutes"]


def asset_path(name):
    # Nell'exe di PyInstaller i file stanno in sys._MEIPASS
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "assets", name)


def apply_icon(root):
    try:
        root.iconbitmap(default=asset_path("glucobar.ico"))
    except tk.TclError:
        pass  # .ico supportato solo su Windows


def choose(parent, title, prompt, options, default):
    """Finestrella con una scelta tra `options` [(valore, testo)]; None se annullata."""
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.resizable(False, False)
    var = tk.StringVar(master=dlg, value=default)
    tk.Label(dlg, text=prompt, justify="left", font=(FONT, 10)).pack(
        anchor="w", padx=16, pady=(14, 6))
    for value, label in options:
        tk.Radiobutton(dlg, text=label, value=value, variable=var, anchor="w",
                       font=(FONT, 10)).pack(fill="x", padx=24)
    result = []

    def ok(_event=None):
        result.append(var.get())
        dlg.destroy()

    buttons = tk.Frame(dlg)
    buttons.pack(fill="x", padx=16, pady=(12, 14))
    tk.Button(buttons, text=t("button_cancel"), width=10, command=dlg.destroy).pack(side="right")
    tk.Button(buttons, text=t("button_ok"), width=10, command=ok, default="active").pack(
        side="right", padx=(0, 6))
    dlg.bind("<Return>", ok)
    dlg.bind("<Escape>", lambda _event: dlg.destroy())
    if parent.winfo_viewable():
        dlg.transient(parent)
    dlg.update_idletasks()
    dlg.geometry(f"+{(dlg.winfo_screenwidth() - dlg.winfo_reqwidth()) // 2}"
                 f"+{(dlg.winfo_screenheight() - dlg.winfo_reqheight()) // 3}")
    dlg.attributes("-topmost", True)
    dlg.focus_force()
    dlg.grab_set()
    parent.wait_window(dlg)
    return result[0] if result else None


RANGE_LIMITS = {"low": (40, 200), "high": (100, 400), "very_high": (150, 500)}   # mg/dL


def parse_range(cfg, texts):
    """{"low": "3.9", ...} nell'unità scelta -> soglie in mg/dL; ValueError se non vanno."""
    values = {}
    for key, (lo, hi) in RANGE_LIMITS.items():
        number = float(texts[key].replace(",", ".").strip())
        mgdl = round(number * 18.016) if cfg["unit"] == "mmol/L" else round(number)
        if not lo <= mgdl <= hi:
            raise ValueError(key)
        values[key] = mgdl
    if not values["low"] < values["high"] < values["very_high"]:
        raise ValueError("order")
    return values


def ask_range(cfg, parent):
    """Finestrella per le soglie (basso, alto, molto alto); None se annullata."""
    dlg = tk.Toplevel(parent)
    dlg.title(t("range_title"))
    dlg.resizable(False, False)
    tk.Label(dlg, text=t("range_prompt", unit=cfg["unit"]), justify="left",
             font=(FONT, 10)).grid(row=0, column=0, columnspan=2, sticky="w",
                                   padx=16, pady=(14, 8))
    entries = {}
    for row, key in enumerate(RANGE_LIMITS, 1):
        tk.Label(dlg, text=t(f"range_{key}"), font=(FONT, 10)).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=3)
        entry = tk.Entry(dlg, width=8, font=(FONT, 10), justify="right")
        entry.insert(0, fmt_value(cfg, cfg[key]))
        entry.grid(row=row, column=1, sticky="w", padx=(0, 16), pady=3)
        entries[key] = entry
    error = tk.Label(dlg, text="", fg="#c62828", font=(FONT, 9), justify="left")
    error.grid(row=4, column=0, columnspan=2, sticky="w", padx=16)
    result = []

    def ok(_event=None):
        try:
            result.append(parse_range(cfg, {k: e.get() for k, e in entries.items()}))
        except ValueError:
            error.config(text=t("range_invalid"))
            return
        dlg.destroy()

    buttons = tk.Frame(dlg)
    buttons.grid(row=5, column=0, columnspan=2, sticky="e", padx=16, pady=(8, 14))
    tk.Button(buttons, text=t("button_cancel"), width=10, command=dlg.destroy).pack(side="right")
    tk.Button(buttons, text=t("button_ok"), width=10, command=ok, default="active").pack(
        side="right", padx=(0, 6))
    dlg.bind("<Return>", ok)
    dlg.bind("<Escape>", lambda _event: dlg.destroy())
    dlg.update_idletasks()
    dlg.geometry(f"+{(dlg.winfo_screenwidth() - dlg.winfo_reqwidth()) // 2}"
                 f"+{(dlg.winfo_screenheight() - dlg.winfo_reqheight()) // 3}")
    dlg.attributes("-topmost", True)
    dlg.focus_force()
    entries["low"].focus_set()
    dlg.grab_set()
    parent.wait_window(dlg)
    return result[0] if result else None


def bind_right_click(widget, callback):
    """Clic destro: Button-3 su Windows e Linux; sul Mac Button-2 e Ctrl+clic.

    Il clic si ferma qui ("break"): Tk lo passa anche alla finestra che contiene il
    widget, e se anche lei ha il menu se ne aprivano due di fila. Il secondo distruggeva
    il primo prima che Windows ne eseguisse la scelta: la prima scelta andava persa
    (Mostra → Finestrella, e nella 0.8.4 "Aggiorna ogni" sul valore della barra)."""
    def handler(event):
        callback(event)
        return "break"
    if sys.platform == "darwin":
        widget.bind("<Button-2>", handler)
        widget.bind("<Control-Button-1>", handler)
    else:
        widget.bind("<Button-3>", handler)


def ask_credentials(cfg, parent=None):
    """Chiede sensore e account (per Dexcom anche la regione, per Nightscout indirizzo
    e token facoltativo). La password va nel Gestione credenziali, in una voce
    diversa per ogni sensore."""
    owns_root = parent is None
    if owns_root:
        parent = tk.Tk()
        parent.withdraw()
        apply_icon(parent)
    try:
        source = choose(parent, t("sensor_title"), t("sensor_prompt"), source_options(),
                        cfg.get("source", "libre"))
        if not source:
            return False
        dexcom = source == "dexcom"
        region = cfg.get("dexcom_region", "ous")
        if dexcom:
            region = choose(parent, t("cred_title_dexcom"), t("dexcom_region"),
                            region_options(), region)
            if not region:
                return False
        nightscout = source == "nightscout"
        title = t("cred_title_dexcom" if dexcom else
                  "cred_title_nightscout" if nightscout else "cred_title")
        prompt = t("cred_email_dexcom" if dexcom else
                   "cred_url_nightscout" if nightscout else "cred_email")
        same_source = source == cfg.get("source", "libre")
        email = simpledialog.askstring(title, prompt,
                                       initialvalue=cfg.get("email", "") if same_source else "",
                                       parent=parent)
        if not email or not email.strip():
            return False
        if nightscout:
            email = normalize_url(email)
            password = simpledialog.askstring(title, t("cred_token_nightscout"), show="•",
                                              parent=parent)
            if password is None:   # Annulla; vuoto = sito pubblico
                return False
            password = password.strip()
        else:
            password = simpledialog.askstring(title, t("cred_password"), show="•", parent=parent)
            if not password:
                return False
    finally:
        if owns_root:
            parent.destroy()
    cfg.update(source=source, dexcom_region=region, email=email.strip())
    if password:
        credentials.set_password(cfg["email"], password, source)
    else:
        credentials.delete_password(source)   # Nightscout pubblico: niente token vecchi
    save_config(cfg)
    return True
