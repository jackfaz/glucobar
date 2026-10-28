"""Messaggi di GlucoBar in un riquadro in basso a destra, sopra la barra delle
applicazioni (o in alto a destra sul Mac, sotto la barra dei menu), con pulsanti
facoltativi. Funziona anche quando l'icona vicino all'orologio è nascosta."""

import sys
import tkinter as tk

from .theme import palette
from .ui_common import FONT, bind_right_click

MARGIN = 12


def work_area(root):
    """(sinistra, alto, destra, basso) dello schermo principale senza barre."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom   # SPI_GETWORKAREA
    top = 30 if sys.platform == "darwin" else 0   # barra dei menu
    return 0, top, root.winfo_screenwidth(), root.winfo_screenheight() - 60


class Toast:
    open = []   # riquadri aperti, per impilarli

    def __init__(self, ctl, title, text, actions=(), timeout=15):
        """actions: [(testo, funzione)]; con dei pulsanti resta aperto finché non lo si
        chiude, altrimenti si chiude da solo dopo `timeout` secondi."""
        self.ctl = ctl
        pal = palette(ctl.cfg)
        s = max(1.0, ctl.root.winfo_fpixels("1i") / 96)
        self.win = win = tk.Toplevel(ctl.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=pal.grid, padx=1, pady=1)   # bordo sottile
        body = tk.Frame(win, bg=pal.bg, padx=int(14 * s), pady=int(10 * s))
        body.pack(fill="both", expand=True)
        width = int(340 * s)

        head = tk.Frame(body, bg=pal.bg)
        head.pack(fill="x")
        tk.Label(head, text=title, bg=pal.bg, fg=pal.fg, font=(FONT, 10, "bold"),
                 anchor="w").pack(side="left")
        close = tk.Label(head, text="✕", bg=pal.bg, fg=pal.dim, font=(FONT, 10), cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", lambda _e: self.close())
        message = tk.Label(body, text=text, bg=pal.bg, fg=pal.fg, font=(FONT, 9),
                           justify="left", anchor="w", wraplength=width - int(30 * s))
        message.pack(fill="x", pady=(int(4 * s), 0))
        if actions:
            row = tk.Frame(body, bg=pal.bg)
            row.pack(fill="x", pady=(int(8 * s), 0))
            for label, fn in actions:
                tk.Button(row, text=label, font=(FONT, 9), command=self._run(fn)).pack(
                    side="left", padx=(0, int(6 * s)))
        for widget in (body, message):
            bind_right_click(widget, lambda _e: self.close())

        win.update_idletasks()
        height = win.winfo_reqheight()
        left, top, right, bottom = work_area(ctl.root)
        below = sum(toast.win.winfo_height() + MARGIN for toast in Toast.open
                    if toast.win.winfo_exists())
        x = right - width - MARGIN
        y = top + MARGIN + below if sys.platform == "darwin" else bottom - height - MARGIN - below
        win.geometry(f"{width}x{height}+{x}+{y}")
        Toast.open.append(self)
        if not actions:
            win.after(timeout * 1000, self.close)

    def _run(self, fn):
        def run():
            self.close()
            self.ctl.post(fn)
        return run

    def close(self):
        if self in Toast.open:
            Toast.open.remove(self)
        try:
            self.win.destroy()
        except tk.TclError:
            pass
