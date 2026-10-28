"""Vista "finestrella": sempre in primo piano, con valore, freccia e grafico delle ultime ore.
Si sposta trascinandola e si ridimensiona dall'angolo in basso a destra: testo e grafico
crescono insieme, nelle stesse proporzioni."""

import time
import tkinter as tk

from .config import save_config
from .i18n import t
from .menus import fill_tk
from .sources import TREND_ARROWS
from .theme import palette
from .ui_common import FONT, age_minutes, bind_right_click, fmt_value, is_stale


class WindowView:
    WIDTH, HEIGHT = 190, 112
    SPARK_HOURS = 3
    MIN_SCALE, MAX_SCALE = 0.8, 2.5

    def __init__(self, ctl):
        self.ctl = ctl
        self.cfg = ctl.cfg
        self.c = c = palette(self.cfg)

        self.root = tk.Toplevel(ctl.root)
        self.root.title("GlucoBar")
        self.root.overrideredirect(True)        # niente bordi
        self.root.attributes("-topmost", True)  # sempre in primo piano
        try:
            self.root.attributes("-alpha", 0.93)
        except tk.TclError:
            pass
        self.root.configure(bg=c.bg)

        # Il programma lavora in pixel reali: sugli schermi al 125-150% ingrandisce
        self.s = max(1.0, self.root.winfo_fpixels("1i") / 96)
        self.k = self._clamp(self.cfg.get("window_scale") or 1.0)

        self.value_lbl = tk.Label(self.root, text="…", bg=c.bg, fg=c.fg)
        self.arrow_lbl = tk.Label(self.root, text="", bg=c.bg, fg=c.fg)
        self.info_lbl = tk.Label(self.root, text=t("connecting"), bg=c.bg, fg=c.dim, anchor="w")
        self.spark = tk.Canvas(self.root, bg=c.bg, highlightthickness=0)
        # angolo per ridimensionare
        self.grip = tk.Canvas(self.root, bg=c.bg, highlightthickness=0,
                              cursor="bottom_right_corner")

        w, h = self.size()
        x, y = self.cfg["window_x"], self.cfg["window_y"]
        if x is None or y is None:
            x, y = self.root.winfo_screenwidth() - w - 24, 24
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.layout()

        self.menu = tk.Menu(self.root, tearoff=0,
                            postcommand=lambda: fill_tk(self.menu, ctl.menu_items(), ctl.post))

        for wdg in (self.root, self.value_lbl, self.arrow_lbl, self.info_lbl, self.spark):
            wdg.bind("<ButtonPress-1>", self._drag_start)
            wdg.bind("<B1-Motion>", self._drag_move)
            wdg.bind("<ButtonRelease-1>", self._drag_end)
            bind_right_click(wdg, self._show_menu)
            wdg.bind("<Double-Button-1>", lambda e: ctl.refresh())
        self.grip.bind("<ButtonPress-1>", self._resize_start)
        self.grip.bind("<B1-Motion>", self._resize_move)
        self.grip.bind("<ButtonRelease-1>", self._resize_end)

    def destroy(self):
        self.root.destroy()

    # ---- dimensioni ----
    def _clamp(self, k):
        return min(max(float(k), self.MIN_SCALE), self.MAX_SCALE)

    def size(self):
        f = self.s * self.k
        return int(self.WIDTH * f), int(self.HEIGHT * f)

    def layout(self):
        """Posizioni e caratteri per la dimensione attuale (self.k)."""
        f, k = self.s * self.k, self.k
        w, h = self.size()
        self.value_lbl.configure(font=(FONT, round(30 * k), "bold"))
        self.value_lbl.place(x=12 * f, y=4 * f)
        self.arrow_lbl.configure(font=(FONT, round(26 * k), "bold"))
        self.arrow_lbl.place(x=w - 46 * f, y=6 * f)
        self.info_lbl.configure(font=(FONT, max(7, round(9 * k))))
        self.info_lbl.place(x=14 * f, y=52 * f, width=w - 20 * f)
        self.spark.configure(width=w - 24 * f, height=34 * f)
        self.spark.place(x=12 * f, y=72 * f)
        g = int(11 * self.s)
        self.grip.configure(width=g, height=g)
        self.grip.place(x=w - g, y=h - g)
        self.grip.delete("all")
        for i in (3, 6, 9):   # tre trattini diagonali, come il pannello
            d = i * self.s
            self.grip.create_line(g - d, g - 1, g - 1, g - d, fill=self.c.grip)
        self.render()

    # ---- trascinamento / ridimensionamento / menu ----
    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _drag_end(self, _e):
        self.cfg["window_x"], self.cfg["window_y"] = self.root.winfo_x(), self.root.winfo_y()
        save_config(self.cfg)

    def _resize_start(self, _e):
        self._origin = (self.root.winfo_rootx(), self.root.winfo_rooty())

    def _resize_move(self, e):
        # la larghezza decide la scala; l'altezza segue, per non deformare il grafico
        left, top = self._origin
        k = self._clamp((e.x_root - left) / (self.WIDTH * self.s))
        if abs(k - self.k) < 0.02:
            return
        self.k = k
        w, h = self.size()
        self.root.geometry(f"{w}x{h}+{left}+{top}")
        self.layout()

    def _resize_end(self, _e):
        self.cfg["window_scale"] = round(self.k, 2)
        save_config(self.cfg)

    def _show_menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    # ---- disegno ----
    def render(self):
        c, error, pal = self.ctl.current, self.ctl.error, self.c
        if not c:
            self.value_lbl.config(text="--", fg=pal.dim)
            self.arrow_lbl.config(text="")
            self.info_lbl.config(text=error or t("connecting"),
                                 fg=pal.error if error else pal.dim)
            return

        age = age_minutes(c)
        stale = is_stale(self.cfg, c)
        color = pal.dim if stale else pal.value(self.cfg, c["mgdl"])
        value = fmt_value(self.cfg, c["mgdl"])
        arrow = TREND_ARROWS.get(c["trend"], "")

        self.value_lbl.config(text=value, fg=color)
        self.arrow_lbl.config(text="" if stale else arrow, fg=color)
        when = t("now") if age == 0 else t("min_ago", n=age)
        info = f"{self.cfg['unit']} · {when}"
        if error:
            info += " · ⚠ " + error
        self.info_lbl.config(text=info, fg=pal.error if (stale or error) else pal.dim)
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
        f = self.s * self.k

        def y(v):
            v = min(max(v, lo_v), hi_v)
            return h - 2 - (v - lo_v) / (hi_v - lo_v) * (h - 4)

        def x(ts):
            return (ts - t0) / (t1 - t0) * (w - 4) + 2

        # fascia del range obiettivo
        cv.create_rectangle(0, y(self.cfg["high"]), w, y(self.cfg["low"]),
                            fill=self.c.band, outline="")
        if len(pts) < 2:
            return
        coords = []
        for m in pts:
            coords += [x(m["time"]), y(m["mgdl"])]
        cv.create_line(*coords, fill=self.c.line, width=1.5 * f, smooth=True)
        lx, ly, r = coords[-2], coords[-1], 3 * f
        col = self.c.value(self.cfg, pts[-1]["mgdl"])
        cv.create_oval(lx - r, ly - r, lx + r, ly + r, fill=col, outline=col)
