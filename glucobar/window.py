"""Vista "finestrella": sempre in primo piano, con valore, freccia e grafico delle ultime ore."""

import time
import tkinter as tk

from .config import save_config
from .i18n import t
from .sources import TREND_ARROWS
from .ui_common import BG, DIM, FG, RED, age_minutes, color_for, fmt_value, is_stale


class WindowView:
    WIDTH, HEIGHT = 190, 112
    SPARK_HOURS = 3

    def __init__(self, ctl):
        self.ctl = ctl
        self.cfg = ctl.cfg

        self.root = tk.Toplevel(ctl.root)
        self.root.title("GlucoBar")
        self.root.overrideredirect(True)        # niente bordi
        self.root.attributes("-topmost", True)  # sempre in primo piano
        try:
            self.root.attributes("-alpha", 0.93)
        except tk.TclError:
            pass
        self.root.configure(bg=BG)

        # Il programma lavora in pixel reali: sugli schermi al 125-150% ingrandisce
        self.s = s = max(1.0, self.root.winfo_fpixels("1i") / 96)
        w, h = int(self.WIDTH * s), int(self.HEIGHT * s)
        x, y = self.cfg["window_x"], self.cfg["window_y"]
        if x is None or y is None:
            x, y = self.root.winfo_screenwidth() - w - 24, 24
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.value_lbl = tk.Label(self.root, text="…", font=("Segoe UI", 30, "bold"),
                                  bg=BG, fg=FG)
        self.value_lbl.place(x=12 * s, y=4 * s)
        self.arrow_lbl = tk.Label(self.root, text="", font=("Segoe UI", 26, "bold"),
                                  bg=BG, fg=FG)
        self.arrow_lbl.place(x=w - 46 * s, y=6 * s)
        self.info_lbl = tk.Label(self.root, text=t("connecting"), font=("Segoe UI", 9),
                                 bg=BG, fg=DIM, anchor="w")
        self.info_lbl.place(x=14 * s, y=52 * s, width=w - 20 * s)
        self.spark = tk.Canvas(self.root, width=w - 24 * s, height=34 * s, bg=BG,
                               highlightthickness=0)
        self.spark.place(x=12 * s, y=72 * s)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label=t("menu_refresh"), command=ctl.refresh)
        self.menu.add_command(label=t("menu_unit"), command=ctl.toggle_unit)
        self.menu.add_separator()
        ctl.add_common_menu(self.menu)

        for wdg in (self.root, self.value_lbl, self.arrow_lbl, self.info_lbl, self.spark):
            wdg.bind("<ButtonPress-1>", self._drag_start)
            wdg.bind("<B1-Motion>", self._drag_move)
            wdg.bind("<ButtonRelease-1>", self._drag_end)
            wdg.bind("<Button-3>", self._show_menu)
            wdg.bind("<Button-2>", self._show_menu)          # macOS
            wdg.bind("<Double-Button-1>", lambda e: ctl.refresh())

    def destroy(self):
        self.root.destroy()

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

    # ---- disegno ----
    def render(self):
        c, error = self.ctl.current, self.ctl.error
        if not c:
            self.value_lbl.config(text="--", fg=DIM)
            self.arrow_lbl.config(text="")
            self.info_lbl.config(text=error or t("connecting"), fg=RED if error else DIM)
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
        if error:
            info += " · ⚠ " + error
        self.info_lbl.config(text=info, fg=RED if (stale or error) else DIM)
        self.draw_sparkline()

    def draw_sparkline(self):
        cv = self.spark
        cv.delete("all")
        w, h = int(float(cv["width"])), int(float(cv["height"]))
        t1 = time.time()
        t0 = t1 - self.SPARK_HOURS * 3600
        pts = sorted((m for m in self.ctl.history if m["time"] >= t0 and m["mgdl"]),
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
        cv.create_line(*coords, fill="#c9ccd1", width=1.5 * self.s, smooth=True)
        lx, ly, r = coords[-2], coords[-1], 3 * self.s
        col = color_for(self.cfg, pts[-1]["mgdl"])
        cv.create_oval(lx - r, ly - r, lx + r, ly + r, fill=col, outline=col)
