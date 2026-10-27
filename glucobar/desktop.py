"""Modalità "sfondo": pannello sul desktop, dietro le altre finestre.

Valore grande con freccia e variazione, tabella con media/minimo/massimo e tempo
nel range, grafico delle ultime ore. Si sposta trascinandolo e si ridimensiona
dall'angolo in basso a destra; posizione e dimensioni vengono ricordate.
"""

import time
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

from . import stats
from .config import save_config
from .i18n import t
from .sources import TREND_ARROWS
from .ui_common import DIM, FG, FONT, ORANGE, RED, age_minutes, bind_right_click, color_for, \
    fmt_value, is_stale
from .taskbar import IS_WIN

if IS_WIN:
    from ctypes import wintypes

    from .taskbar import GWL_EXSTYLE, SWP_NOACTIVATE, SWP_NOMOVE, SWP_NOSIZE, \
        WS_EX_TOOLWINDOW, user32
    HWND_BOTTOM = wintypes.HWND(1)

PANEL = "#15171c"
GRID = "#2a2d35"
BAND = "#1b3325"
LINE = "#c9ccd1"
HOURS_CHOICES = (3, 6, 12)  # LibreLinkUp fornisce circa 12 ore di storico, Dexcom 24


class DesktopView:
    MIN_W, MIN_H = 300, 200
    GRIP = 18   # zona dell'angolo per ridimensionare

    def __init__(self, ctl):
        self.ctl = ctl
        self.cfg = cfg = ctl.cfg
        self.alive = True
        self.drag = None

        self.root = tk.Toplevel(ctl.root)
        self.root.title("GlucoBar")
        self.root.overrideredirect(True)
        self.root.configure(bg=PANEL)
        try:
            self.root.attributes("-alpha", float(cfg["desktop_alpha"]))
        except tk.TclError:
            pass

        w = max(self.MIN_W, int(cfg["desktop_w"]))
        h = max(self.MIN_H, int(cfg["desktop_h"]))
        x, y = cfg["desktop_x"], cfg["desktop_y"]
        if x is None or y is None:
            x, y = self.root.winfo_screenwidth() - w - 40, 60
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.canvas = tk.Canvas(self.root, bg=PANEL, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Motion>", self._hover)
        self.canvas.bind("<Double-Button-1>", lambda e: ctl.refresh())
        bind_right_click(self.canvas, lambda e: self.menu.tk_popup(e.x_root, e.y_root))

        self.hours_var = tk.IntVar(value=int(cfg["desktop_hours"]))
        self.locked_var = tk.BooleanVar(value=bool(cfg["desktop_locked"]))
        hours_menu = tk.Menu(self.root, tearoff=0)
        for hours in HOURS_CHOICES:
            hours_menu.add_radiobutton(label=t("desk_hours", h=hours), value=hours,
                                       variable=self.hours_var, command=self.set_hours)
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label=t("menu_refresh"), command=ctl.refresh)
        self.menu.add_command(label=t("menu_unit"), command=ctl.toggle_unit)
        self.menu.add_cascade(label=t("menu_hours"), menu=hours_menu)
        self.menu.add_checkbutton(label=t("menu_lock"), variable=self.locked_var,
                                  command=self.set_locked)
        self.menu.add_separator()
        ctl.add_common_menu(self.menu)

        self.root.update_idletasks()
        if IS_WIN:
            # Niente pulsante nella barra e niente Alt+Tab
            hwnd = self.own_hwnd()
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                                  user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_TOOLWINDOW)
        self._keep_at_bottom()

    def destroy(self):
        self.alive = False
        self.root.destroy()

    # ---- finestra: sempre dietro, spostamento e ridimensionamento ----
    def own_hwnd(self):
        return user32.GetParent(self.root.winfo_id())

    def _keep_at_bottom(self):
        if not self.alive:
            return
        if IS_WIN and not self.drag:
            user32.SetWindowPos(self.own_hwnd(), HWND_BOTTOM, 0, 0, 0, 0,
                                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        self.root.after(1000, self._keep_at_bottom)

    def _in_grip(self, e):
        return (e.x >= self.canvas.winfo_width() - self.GRIP and
                e.y >= self.canvas.winfo_height() - self.GRIP)

    def _hover(self, e):
        resizable = self._in_grip(e) and not self.locked_var.get()
        self.canvas.configure(cursor="bottom_right_corner" if resizable else "")

    def _press(self, e):
        if self.locked_var.get():
            return
        self.drag = {
            "mode": "resize" if self._in_grip(e) else "move",
            "x": e.x_root, "y": e.y_root,
            "w": self.root.winfo_width(), "h": self.root.winfo_height(),
            "left": self.root.winfo_x(), "top": self.root.winfo_y(),
        }

    def _motion(self, e):
        d = self.drag
        if not d:
            return
        dx, dy = e.x_root - d["x"], e.y_root - d["y"]
        if d["mode"] == "resize":
            w = max(self.MIN_W, d["w"] + dx)
            h = max(self.MIN_H, d["h"] + dy)
            self.root.geometry(f"{w}x{h}")
        else:
            self.root.geometry(f"+{d['left'] + dx}+{d['top'] + dy}")

    def _release(self, _e):
        if not self.drag:
            return
        self.drag = None
        self.cfg.update(desktop_x=self.root.winfo_x(), desktop_y=self.root.winfo_y(),
                        desktop_w=self.root.winfo_width(), desktop_h=self.root.winfo_height())
        save_config(self.cfg)

    # ---- menu ----
    def set_hours(self):
        self.cfg["desktop_hours"] = self.hours_var.get()
        save_config(self.cfg)
        self.draw()

    def set_locked(self):
        self.cfg["desktop_locked"] = self.locked_var.get()
        save_config(self.cfg)

    # ---- disegno ----
    def fmt_delta(self, delta):
        if self.cfg["unit"] == "mmol/L":
            return f"{delta / 18.016:+.1f}"
        return f"{delta:+.0f}"

    def render(self):
        self.draw()

    def draw(self):
        if not self.alive:
            return
        cv = self.canvas
        cv.delete("all")
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 50 or H < 50:
            return
        cfg = self.cfg
        hours = int(cfg["desktop_hours"])
        pad = max(10, int(min(W, H) * 0.04))
        head_h = max(56, int(H * 0.24))
        f_big = -int(head_h * 0.66)
        f_small = -max(11, int(head_h * 0.2))
        f_tiny = -max(10, int(head_h * 0.17))

        points = stats.recent(self.ctl.history, hours)
        summary = stats.summary(points, cfg)
        c, error = self.ctl.current, self.ctl.error

        # --- valore grande, freccia, sottotitolo ---
        if c:
            stale = is_stale(cfg, c)
            color = DIM if stale else color_for(cfg, c["mgdl"])
            value = fmt_value(cfg, c["mgdl"])
            arrow = "" if stale else TREND_ARROWS.get(c["trend"], "")
            age = age_minutes(c)
            parts = [cfg["unit"], t("now") if age == 0 else t("min_ago", n=age)]
            delta = stats.change(points, c)
            if delta is not None:
                parts.append(t("desk_change", delta=self.fmt_delta(delta)))
            sub, sub_color = " · ".join(parts), RED if stale else DIM
        else:
            color, value, arrow = DIM, "--", ""
            sub, sub_color = t("connecting"), DIM
        if error:
            sub, sub_color = "⚠ " + error, RED

        vid = cv.create_text(pad, pad - head_h * 0.08, text=value, anchor="nw", fill=color,
                             font=(FONT, f_big, "bold"))
        value_right = cv.bbox(vid)[2]
        aid = cv.create_text(value_right + 8, pad + head_h * 0.02, text=arrow, anchor="nw",
                             fill=color, font=(FONT, int(f_big * 0.75), "bold"))
        sid = cv.create_text(pad, pad + head_h * 0.74, text=sub, anchor="nw", fill=sub_color,
                             font=(FONT, f_small), width=W - 2 * pad)
        head_right = max(value_right, cv.bbox(aid)[2] if arrow else 0, cv.bbox(sid)[2])

        # --- tabella: a destra se c'è spazio, altrimenti sotto il valore ---
        rows = []
        if summary:
            f = lambda v: fmt_value(cfg, v)  # noqa: E731
            rows = [
                (t("desk_mean"), f(summary["mean"]), FG),
                (t("desk_in_range"), f"{summary['in_range']:.0f}%", color_for(cfg, cfg["low"])),
                (t("desk_min"), f(summary["min"]), color_for(cfg, summary["min"])),
                (t("desk_below"), f"{summary['below']:.0f}%", RED),
                (t("desk_max"), f(summary["max"]), color_for(cfg, summary["max"])),
                (t("desk_above"), f"{summary['above']:.0f}%", ORANGE),
            ]
        # colonne larghe quanto i testi veri (in tedesco sono più lunghi)
        normal = tkfont.Font(root=self.root, family=FONT, size=f_tiny)
        bold = tkfont.Font(root=self.root, family=FONT, size=f_tiny, weight="bold")
        col_w = (max((normal.measure(r[0]) for r in rows), default=0) + pad +
                 max((bold.measure(r[1]) for r in rows), default=0))
        table_w = 2 * col_w + pad
        top = pad + head_h
        if rows and W - head_right - 3 * pad >= table_w:
            x0, y0, line_h = W - pad - table_w, pad + 2, head_h * 0.3
            for i, (label, val, col) in enumerate(rows):
                x = x0 + (i % 2) * (col_w + pad)
                y = y0 + (i // 2) * line_h
                cv.create_text(x, y, text=label, anchor="nw", fill=DIM,
                               font=(FONT, f_tiny))
                cv.create_text(x + col_w, y, text=val, anchor="ne", fill=col,
                               font=(FONT, f_tiny, "bold"))
        elif rows:
            # spazio indivisibile: si va a capo tra una voce e l'altra, non dentro
            text = "   ".join(f"{label} {val}" for label, val, _ in rows)
            tid = cv.create_text(pad, top, text=text, anchor="nw", fill=DIM,
                                 font=(FONT, f_tiny), width=W - 2 * pad)
            top = cv.bbox(tid)[3] + 2

        # --- piè di pagina ---
        footer = [t("desk_hours", h=hours)]
        days = stats.sensor_days(self.ctl.client.connection)
        if days is not None:
            footer.append(t("desk_sensor", d=int(days) + 1))
        if self.ctl.updated_at:
            footer.append(t("desk_updated", time=datetime.fromtimestamp(self.ctl.updated_at)
                                                  .strftime("%H:%M")))
        foot_h = -f_tiny * 1.6
        cv.create_text(pad, H - pad, text=" · ".join(footer), anchor="sw", fill=DIM,
                       font=(FONT, f_tiny))
        self.draw_grip(W, H)

        # --- grafico ---
        axis_w = -f_tiny * 3
        self.draw_chart(points, pad + axis_w, top + pad * 0.5, W - pad,
                        H - pad - foot_h - (-f_tiny * 1.5), hours, f_tiny)

    def draw_chart(self, points, left, top, right, bottom, hours, f_tiny):
        cv, cfg = self.canvas, self.cfg
        if right - left < 40 or bottom - top < 30:
            return
        now = time.time()
        t0 = now - hours * 3600
        lo_v = 40
        hi_v = max(300, min(400, max((p["mgdl"] for p in points), default=0) + 20))

        def y(v):
            v = min(max(v, lo_v), hi_v)
            return bottom - (v - lo_v) / (hi_v - lo_v) * (bottom - top)

        def x(ts):
            return left + (ts - t0) / (now - t0) * (right - left)

        # fascia del range e soglie
        cv.create_rectangle(left, y(cfg["high"]), right, y(cfg["low"]), fill=BAND, outline="")
        for v, col in ((cfg["low"], RED), (cfg["high"], ORANGE)):
            cv.create_line(left, y(v), right, y(v), fill=col, dash=(3, 3))
            cv.create_text(left - 4, y(v), text=fmt_value(cfg, v), anchor="e", fill=col,
                           font=(FONT, f_tiny))
        cv.create_text(left - 4, y(hi_v), text=fmt_value(cfg, hi_v), anchor="ne", fill=DIM,
                       font=(FONT, f_tiny))

        # griglia oraria
        step = 1 if hours <= 3 else 2 if hours <= 6 else 3
        tick = datetime.fromtimestamp(t0).replace(minute=0, second=0, microsecond=0)
        ts = tick.timestamp() + 3600
        while ts < now:
            hour = datetime.fromtimestamp(ts)
            if hour.hour % step == 0:
                cv.create_line(x(ts), top, x(ts), bottom, fill=GRID)
                cv.create_text(x(ts), bottom + 3, text=hour.strftime("%H:%M"), anchor="n",
                               fill=DIM, font=(FONT, f_tiny))
            ts += 3600

        if len(points) >= 2:
            coords = []
            for p in points:
                coords += [x(p["time"]), y(p["mgdl"])]
            cv.create_line(*coords, fill=LINE, width=1.5, smooth=True)
        r = max(2, (bottom - top) / 70)
        for p in points:
            px, py = x(p["time"]), y(p["mgdl"])
            col = color_for(cfg, p["mgdl"])
            cv.create_oval(px - r, py - r, px + r, py + r, fill=col, outline="")
        current = self.ctl.current
        if current and points:
            px, py = x(current["time"]), y(current["mgdl"])
            col = color_for(cfg, current["mgdl"])
            cv.create_oval(px - 2.2 * r, py - 2.2 * r, px + 2.2 * r, py + 2.2 * r,
                           outline=col, width=2)

    def draw_grip(self, W, H):
        if self.locked_var.get():
            return
        for i in (4, 9, 14):
            self.canvas.create_line(W - i, H - 2, W - 2, H - i, fill=GRID, width=2)
