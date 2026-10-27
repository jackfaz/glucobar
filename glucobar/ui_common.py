"""Parti comuni alle tre interfacce: colori, formati, finestra delle credenziali."""

import os
import sys
import time
import tkinter as tk
from tkinter import simpledialog

from . import credentials
from .config import save_config
from .i18n import t
from .nightscout import normalize_url
from .sources import region_options, source_options

# Carattere dell'interfaccia: Segoe UI su Windows (e per le anteprime generate su
# Linux), quello di sistema sul Mac
FONT = "Helvetica Neue" if sys.platform == "darwin" else "Segoe UI"

BG = "#1e1f22"
FG = "#f2f2f2"
DIM = "#8a8d93"
GREY = "#9a9da3"
GREEN = "#3ecf6e"
ORANGE = "#f5a524"
RED = "#ff4d4f"


def fmt_value(cfg, mgdl):
    if cfg["unit"] == "mmol/L":
        return f"{mgdl / 18.016:.1f}"
    return f"{mgdl:.0f}"


def color_for(cfg, mgdl):
    if mgdl < cfg["low"] or mgdl > cfg["very_high"]:
        return RED
    if mgdl > cfg["high"]:
        return ORANGE
    return GREEN


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


def bind_right_click(widget, callback):
    """Clic destro: Button-3 su Windows e Linux; sul Mac Button-2 e Ctrl+clic."""
    if sys.platform == "darwin":
        widget.bind("<Button-2>", callback)
        widget.bind("<Control-Button-1>", callback)
    else:
        widget.bind("<Button-3>", callback)


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
