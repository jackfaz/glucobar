"""Modalità "finestra": finestrella sempre in primo piano con valore, freccia e grafico."""

import threading
import time
import tkinter as tk

from .config import save_config
from .i18n import t
from .librelinkup import TREND_ARROWS, LibreLinkUp, fetch_safely
from .ui_common import (
    BG, DIM, FG, RED, age_minutes, apply_icon, ask_credentials, color_for,
    fmt_value, is_stale,
)


class GlucoseWindow:
    WIDTH, HEIGHT = 190, 112
    SPARK_HOURS = 3

    def __init__(self, cfg):
        self.cfg = cfg
        self.client = LibreLinkUp(cfg)
        self.current = None
        self.history = []
        self.error = None
        self.busy = False
        self._last_fetch = 0

        self.root = tk.Tk()
        self.root.title("GlucoBar")
        apply_icon(self.root)
        self.root.overrideredirect(True)        # niente bordi
        self.root.attributes("-topmost", True)  # sempre in primo piano
        try:
            self.root.attributes("-alpha", 0.93)
        except tk.TclError:
            pass
        self.root.configure(bg=BG)

        x, y = cfg["window_x"], cfg["window_y"]
        if x is None or y is None:
            x = self.root.winfo_screenwidth() - self.WIDTH - 24
            y = 24
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self.value_lbl = tk.Label(self.root, text="…", font=("Segoe UI", 30, "bold"),
                                  bg=BG, fg=FG)
        self.value_lbl.place(x=12, y=4)
        self.arrow_lbl = tk.Label(self.root, text="", font=("Segoe UI", 26, "bold"),
                                  bg=BG, fg=FG)
        self.arrow_lbl.place(x=self.WIDTH - 46, y=6)
        self.info_lbl = tk.Label(self.root, text=t("connecting"), font=("Segoe UI", 9),
                                 bg=BG, fg=DIM, anchor="w")
        self.info_lbl.place(x=14, y=52, width=self.WIDTH - 20)
        self.spark = tk.Canvas(self.root, width=self.WIDTH - 24, height=34, bg=BG,
                               highlightthickness=0)
        self.spark.place(x=12, y=72)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label=t("menu_refresh"), command=self.refresh)
        self.menu.add_command(label=t("menu_unit"), command=self.toggle_unit)
        self.menu.add_command(label=t("menu_account"), command=self.change_account)
        self.menu.add_separator()
        self.menu.add_command(label=t("menu_quit"), command=self.root.destroy)

        for w in (self.root, self.value_lbl, self.arrow_lbl, self.info_lbl, self.spark):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<ButtonRelease-1>", self._drag_end)
            w.bind("<Button-3>", self._show_menu)
            w.bind("<Button-2>", self._show_menu)          # macOS
            w.bind("<Double-Button-1>", lambda e: self.refresh())

        self._tick()

    # ---- trascinamento / menu ----
    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _drag_end(self, _e):
        self.cfg["window_x"], self.cfg["window_y"] = self.root.winfo_x(), self.root.winfo_y()
        save_config(self.cfg)

    def _show_menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def toggle_unit(self):
        self.cfg["unit"] = "mmol/L" if self.cfg["unit"] == "mg/dL" else "mg/dL"
        save_config(self.cfg)
        self.render()

    def change_account(self):
        if ask_credentials(self.cfg, self.root):
            self.client = LibreLinkUp(self.cfg)
            self.refresh()

    # ---- dati ----
    def refresh(self):
        if self.busy:
            return
        self.busy = True
        self._last_fetch = time.time()
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        result = fetch_safely(self.client)
        self.root.after(0, self._on_data, *result)

    def _on_data(self, current, history, err):
        self.busy = False
        self.error = err
        if current:
            self.current, self.history = current, history
        self.render()

    def _tick(self):
        # aggiorna "x min fa" ogni 15 s e i dati ogni refresh_seconds
        if time.time() - self._last_fetch >= self.cfg["refresh_seconds"]:
            self.refresh()
        else:
            self.render()
        self.root.after(15000, self._tick)

    # ---- disegno ----
    def render(self):
        c = self.current
        if not c:
            self.value_lbl.config(text="--", fg=DIM)
            self.arrow_lbl.config(text="")
            self.info_lbl.config(text=self.error or t("connecting"),
                                 fg=RED if self.error else DIM)
            return

        age = age_minutes(c)
        stale = is_stale(self.cfg, c)
        color = DIM if stale else color_for(self.cfg, c["mgdl"])
        value = fmt_value(self.cfg, c["mgdl"])
        arrow = TREND_ARROWS.get(c["trend"], "")

        self.value_lbl.config(text=value, fg=color)
        self.arrow_lbl.config(text="" if stale else arrow, fg=color)
        when = t("now") if age == 0 else t("min_ago", n=age)
        info = f"{self.cfg['unit']} · {when}"
        if self.error:
            info += " · ⚠ " + self.error
        self.info_lbl.config(text=info, fg=RED if (stale or self.error) else DIM)
        self.root.title(f"{value} {arrow}")
        self.draw_sparkline()

    def draw_sparkline(self):
        cv = self.spark
        cv.delete("all")
        w, h = int(cv["width"]), int(cv["height"])
        t1 = time.time()
        t0 = t1 - self.SPARK_HOURS * 3600
        pts = sorted((m for m in self.history if m["time"] >= t0 and m["mgdl"]),
                     key=lambda m: m["time"])
        lo_v, hi_v = 40, 300

        def y(v):
            v = min(max(v, lo_v), hi_v)
            return h - 2 - (v - lo_v) / (hi_v - lo_v) * (h - 4)

        def x(ts):
            return (ts - t0) / (t1 - t0) * (w - 4) + 2

        # fascia del range obiettivo
        cv.create_rectangle(0, y(self.cfg["high"]), w, y(self.cfg["low"]),
                            fill="#24352b", outline="")
        if len(pts) < 2:
            return
        coords = []
        for m in pts:
            coords += [x(m["time"]), y(m["mgdl"])]
        cv.create_line(*coords, fill="#c9ccd1", width=1.5, smooth=True)
        lx, ly = coords[-2], coords[-1]
        col = color_for(self.cfg, pts[-1]["mgdl"])
        cv.create_oval(lx - 3, ly - 3, lx + 3, ly + 3, fill=col, outline=col)

    def run(self):
        self.root.mainloop()
