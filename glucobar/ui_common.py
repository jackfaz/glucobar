"""Parti comuni alle tre interfacce: colori, formati, finestra delle credenziali."""

import os
import sys
import time
import tkinter as tk
from tkinter import simpledialog

from . import credentials
from .config import save_config
from .i18n import t

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


def ask_credentials(cfg, parent=None):
    """Chiede email e password LibreLinkUp. La password va nel Gestione credenziali."""
    owns_root = parent is None
    if owns_root:
        parent = tk.Tk()
        parent.withdraw()
        apply_icon(parent)
    try:
        email = simpledialog.askstring(t("cred_title"), t("cred_email"),
                                       initialvalue=cfg.get("email", ""), parent=parent)
        if not email:
            return False
        password = simpledialog.askstring(t("cred_title"), t("cred_password"),
                                          show="•", parent=parent)
        if not password:
            return False
    finally:
        if owns_root:
            parent.destroy()
    cfg["email"] = email.strip()
    credentials.set_password(cfg["email"], password)
    save_config(cfg)
    return True
