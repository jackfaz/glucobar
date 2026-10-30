"""Modalità "sfondo": pannello sul desktop, dietro le altre finestre (oppure, a scelta,
sempre in primo piano: si nasconde solo quando un'app è a schermo intero).

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
from .menus import Item, menu_open, popup, radio_items
from .theme import mix, palette
from .ui_common import FONT, age_minutes, beside_value, bind_right_click, fmt_value, is_stale
from .taskbar import IS_WIN

if IS_WIN:
    from ctypes import wintypes

    from .taskbar import DESKTOP_CLASSES, GWL_EXSTYLE, HWND_TOPMOST, SWP_NOACTIVATE, \
        SWP_NOMOVE, SWP_NOSIZE, WS_EX_TOOLWINDOW, class_name, monitor_rect, user32, \
        window_rect
    HWND_BOTTOM = wintypes.HWND(1)

HOURS_CHOICES = (3, 6, 12)  # LibreLinkUp fornisce circa 12 ore di storico, Dexcom 24


class DesktopView:
    MIN_W, MIN_H = 300, 200
    GRIP = 18   # zona dell'angolo per ridimensionare

    def __init__(self, ctl):
        self.ctl = ctl
        self.cfg = cfg = ctl.cfg
        self.c = palette(cfg)
        self.alive = True
        self.drag = None
        self.hidden = False   # nascosto perché un'app è a schermo intero

        self.root = tk.Toplevel(ctl.root)
        self.root.title("GlucoBar")
        self.root.overrideredirect(True)
        self.root.configure(bg=self.c.panel)
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

        self.canvas = tk.Canvas(self.root, bg=self.c.panel, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Motion>", self._hover)
        self.canvas.bind("<Double-Button-1>", lambda e: ctl.refresh())
        bind_right_click(self.canvas, lambda e: self.show_menu(e.x_root, e.y_root))


        self.root.update_idletasks()
        if IS_WIN:
            # Niente pulsante nella barra e niente Alt+Tab
            hwnd = self.own_hwnd()
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                                  user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_TOOLWINDOW)
        self.root.attributes("-topmost", self.on_top())
        self._keep_in_place()

    def destroy(self):
        self.alive = False
        self.root.destroy()

    # ---- finestra: sempre dietro, spostamento e ridimensionamento ----
    def own_hwnd(self):
        return user32.GetParent(self.root.winfo_id())

    def on_top(self):
        return bool(self.cfg.get("desktop_on_top"))

    def _keep_in_place(self):
        """Ogni secondo: dietro a tutto, oppure (sempre in primo piano) davanti a tutto
        tranne le app a schermo intero sullo stesso monitor, per cui si nasconde."""
        if not self.alive:
            return
        if IS_WIN and not self.drag and not menu_open():
            hwnd = self.own_hwnd()
            if not self.on_top():
                user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            else:
                fullscreen = self.fullscreen_app() and not self.cfg.get("desktop_over_fullscreen")
                if fullscreen and not self.hidden:
                    self.hidden = True
                    self.root.withdraw()
                elif not fullscreen and self.hidden:
                    self.hidden = False
                    self.root.deiconify()
                if not self.hidden:
                    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        self.root.after(1000, self._keep_in_place)

    def fullscreen_app(self):
        """C'è un'app a schermo intero (video, presentazione, gioco) sul nostro monitor?"""
        fg = user32.GetForegroundWindow()
        if not fg or fg == self.own_hwnd() or class_name(fg) in DESKTOP_CLASSES:
            return False
        left, top, right, bottom = window_rect(fg)
        ml, mt, mr, mb = monitor_rect(self.own_hwnd())
        return left <= ml and top <= mt and right >= mr and bottom >= mb

    def _in_grip(self, e):
        return (e.x >= self.canvas.winfo_width() - self.GRIP and
                e.y >= self.canvas.winfo_height() - self.GRIP)

    def _hover(self, e):
        resizable = self._in_grip(e) and not self.locked()
        self.canvas.configure(cursor="bottom_right_corner" if resizable else "")

    def _press(self, e):
        if self.locked():
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
    def show_menu(self, x, y):
        popup(self.root, self.ctl.menu_items(self.menu_items()), self.ctl.post, x, y)

    def menu_items(self):
        cfg = self.cfg
        return [
            Item(t("menu_hours"), children=radio_items(
                [(h, t("desk_hours", h=h)) for h in HOURS_CHOICES], int(cfg["desktop_hours"]),
                self.set_hours)),
            Item(t("menu_lock"), self.toggle_locked, checked=bool(cfg["desktop_locked"])),
            Item(t("menu_on_top"), self.toggle_on_top, checked=self.on_top()),
            Item(t("menu_over_fullscreen"), self.toggle_over_fullscreen,
                 checked=bool(cfg.get("desktop_over_fullscreen")), enabled=self.on_top()),
        ]

    def locked(self):
        return bool(self.cfg["desktop_locked"])

    def set_hours(self, hours):
        self.cfg["desktop_hours"] = hours
        save_config(self.cfg)
        self.draw()

    def toggle_on_top(self):
        self.cfg["desktop_on_top"] = not self.on_top()
        save_config(self.cfg)
        if self.hidden:
            self.hidden = False
            self.root.deiconify()
        self.root.attributes("-topmost", self.on_top())
        if not self.on_top():
            self.root.lower()

    def toggle_over_fullscreen(self):
        self.cfg["desktop_over_fullscreen"] = not self.cfg.get("desktop_over_fullscreen")
        save_config(self.cfg)

    def toggle_locked(self):
        self.cfg["desktop_locked"] = not self.cfg["desktop_locked"]
        save_config(self.cfg)
        self.draw()

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
        cfg, pal = self.cfg, self.c
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
            color = pal.stale if stale else pal.value(cfg, c["mgdl"])
            value = fmt_value(cfg, c["mgdl"])
            arrow = beside_value(cfg, self.ctl.readings, c)
            age = age_minutes(c)
            parts = [cfg["unit"], t("now") if age == 0 else t("min_ago", n=age)]
            if self.ctl.display_name():
                parts.insert(0, self.ctl.display_name())
            delta = stats.change(points, c)
            if delta is not None:
                parts.append(t("desk_change", delta=self.fmt_delta(delta)))
            estimate = None
            if self.prediction():
                end = self.prediction()["points"][-1]
                estimate = t("predict_sub", v=fmt_value(cfg, end[1]), n=end[0])
            sub_color = pal.error if stale else pal.dim
        else:
            color, value, arrow, parts, estimate = pal.dim, "--", "", [t("connecting")], None
            sub_color = pal.dim
        if error:
            parts, estimate, sub_color = ["⚠ " + error], None, pal.error

        vid = cv.create_text(pad, pad - head_h * 0.08, text=value, anchor="nw", fill=color,
                             font=(FONT, f_big, "bold"))
        value_right = cv.bbox(vid)[2]
        aid = cv.create_text(value_right + 8, pad + head_h * 0.02, text=arrow, anchor="nw",
                             fill=color, font=(FONT, int(f_big * 0.75), "bold"))
        value_end = max(value_right, cv.bbox(aid)[2] if arrow else 0)

        # --- tabella: a destra se c'è spazio accanto al valore, altrimenti sotto ---
        rows = []
        if summary:
            f = lambda v: fmt_value(cfg, v)  # noqa: E731
            rows = [
                (t("desk_mean"), f(summary["mean"]), pal.fg),
                (t("desk_in_range"), f"{summary['in_range']:.0f}%", pal.in_range),
                (t("desk_min"), f(summary["min"]), pal.value(cfg, summary["min"])),
                (t("desk_below"), f"{summary['below']:.0f}%", pal.low),
                (t("desk_max"), f(summary["max"]), pal.value(cfg, summary["max"])),
                (t("desk_above"), f"{summary['above']:.0f}%", pal.high),
            ]
        # colonne larghe quanto i testi veri (in tedesco sono più lunghi)
        normal = tkfont.Font(root=self.root, family=FONT, size=f_tiny)
        bold = tkfont.Font(root=self.root, family=FONT, size=f_tiny, weight="bold")
        col_w = (max((normal.measure(r[0]) for r in rows), default=0) + pad +
                 max((bold.measure(r[1]) for r in rows), default=0))
        table_w = 2 * col_w + pad
        beside = bool(rows) and W - value_end - 3 * pad >= table_w
        # il sottotitolo (con la stima è lungo) va a capo prima della tabella, invece di
        # spingerla sotto il valore
        sub_w = W - 3 * pad - table_w if beside else W - 2 * pad
        # la stima nel sottotitolo solo se ci sta su una riga (il grafico la mostra
        # comunque); a capo solo tra una parte e l'altra, non a metà di "2 min fa"
        small = tkfont.Font(root=self.root, family=FONT, size=f_small)
        if estimate and small.measure(" · ".join(parts + [estimate])) <= sub_w:
            parts = parts + [estimate]
        sub = " · ".join(p.replace(" ", "\u00a0") for p in parts)
        sid = cv.create_text(pad, pad + head_h * 0.74, text=sub, anchor="nw", fill=sub_color,
                             font=(FONT, f_small), width=sub_w)
        top = max(pad + head_h, cv.bbox(sid)[3] + 2)
        if beside:
            x0, y0, line_h = W - pad - table_w, pad + 2, head_h * 0.3
            for i, (label, val, col) in enumerate(rows):
                x = x0 + (i % 2) * (col_w + pad)
                y = y0 + (i // 2) * line_h
                cv.create_text(x, y, text=label, anchor="nw", fill=pal.dim,
                               font=(FONT, f_tiny))
                cv.create_text(x + col_w, y, text=val, anchor="ne", fill=col,
                               font=(FONT, f_tiny, "bold"))
        elif rows:
            # spazio indivisibile: si va a capo tra una voce e l'altra, non dentro
            text = "   ".join(f"{label} {val}" for label, val, _ in rows)
            tid = cv.create_text(pad, top, text=text, anchor="nw", fill=pal.dim,
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
        fid = cv.create_text(pad, H - pad, text=" · ".join(footer), anchor="sw", fill=pal.dim,
                             font=(FONT, f_tiny))
        second = self.second_points(hours)
        if second:   # legenda: quale linea è quale sensore
            x = W - pad - 14
            for label, col in ((self.ctl.person_label("second"), self.second_color()),
                               (self.ctl.person_label(), pal.line)):
                tid = cv.create_text(x, H - pad, text=label, anchor="se", fill=pal.dim,
                                     font=(FONT, f_tiny))
                x0 = cv.bbox(tid)[0]
                y0 = (cv.bbox(tid)[1] + cv.bbox(tid)[3]) / 2
                cv.create_line(x0 - 16, y0, x0 - 4, y0, fill=col, width=2)
                x = x0 - 26
            if x < cv.bbox(fid)[2]:   # niente spazio: la legenda sopra il piè di pagina
                foot_h += -f_tiny * 1.4
                cv.move(fid, 0, f_tiny * 1.4)
        self.draw_grip(W, H)

        # --- grafico ---
        axis_w = -f_tiny * 3
        self.draw_chart(points, pad + axis_w, top + pad * 0.5, W - pad,
                        H - pad - foot_h - (-f_tiny * 1.5), hours, f_tiny)

    def second_points(self, hours):
        """Le letture del secondo sensore (es. Dexcom insieme a Libre), se c'è."""
        second = getattr(self.ctl, "second", None)
        return stats.recent(second["history"], hours) if second else []

    def second_color(self):
        return "#2f6fd6" if self.c.light else "#5aa9ff"

    def prediction(self):
        """La stima della tendenza, se accesa (vedi stats.predict)."""
        if not self.cfg.get("predict") or not self.ctl.current:
            return None
        if is_stale(self.cfg, self.ctl.current):
            return None
        return stats.predict(self.ctl.history, self.ctl.current)

    def draw_chart(self, points, left, top, right, bottom, hours, f_tiny):
        cv, cfg, pal = self.canvas, self.cfg, self.c
        if right - left < 40 or bottom - top < 30:
            return
        now = time.time()
        pred = self.prediction()
        end = now + pred["points"][-1][0] * 60 if pred else now
        t0 = now - hours * 3600
        # la stima ha una sua zona a destra, larga almeno un ottavo del grafico: con 12 ore
        # i suoi 30 minuti sarebbero una striscia schiacciata contro il bordo
        split = right - max((end - now) / (end - t0), 0.125 if pred else 0) * (right - left)
        lo_v = 40
        second = self.second_points(hours)
        hi_v = max(300, min(400, max((p["mgdl"] for p in points + second), default=0) + 20))

        def y(v):
            v = min(max(v, lo_v), hi_v)
            return bottom - (v - lo_v) / (hi_v - lo_v) * (bottom - top)

        def x(ts):
            if ts <= now or end <= now:
                return left + (ts - t0) / (now - t0) * (split - left)
            return split + (ts - now) / (end - now) * (right - split)

        # fascia del range e soglie
        cv.create_rectangle(left, y(cfg["high"]), right, y(cfg["low"]), fill=pal.band, outline="")
        for v, col in ((cfg["low"], pal.low), (cfg["high"], pal.high)):
            cv.create_line(left, y(v), right, y(v), fill=col, dash=(3, 3))
            cv.create_text(left - 4, y(v), text=fmt_value(cfg, v), anchor="e", fill=col,
                           font=(FONT, f_tiny))
        cv.create_text(left - 4, y(hi_v), text=fmt_value(cfg, hi_v), anchor="ne", fill=pal.dim,
                       font=(FONT, f_tiny))

        # griglia oraria
        step = 1 if hours <= 3 else 2 if hours <= 6 else 3
        tick = datetime.fromtimestamp(t0).replace(minute=0, second=0, microsecond=0)
        ts = tick.timestamp() + 3600
        while ts < now:
            hour = datetime.fromtimestamp(ts)
            if hour.hour % step == 0:
                cv.create_line(x(ts), top, x(ts), bottom, fill=pal.grid)
                cv.create_text(x(ts), bottom + 3, text=hour.strftime("%H:%M"), anchor="n",
                               fill=pal.dim, font=(FONT, f_tiny))
            ts += 3600

        if pred:
            # la stima: una fascia tenue che si allarga e una linea tratteggiata, dopo
            # l'ultima lettura (vedi stats.predict: non è una previsione vera)
            t_now = pred["time"]
            upper = [(x(t_now), y(pred["from"]))] + [
                (x(t_now + m * 60), y(hi)) for m, _v, _lo, hi in pred["points"]]
            lower = [(x(t_now + m * 60), y(lo)) for m, _v, lo, _hi in reversed(pred["points"])]
            cv.create_polygon(*[c for xy in upper + lower for c in xy],
                              fill=mix(pal.line, pal.panel, 0.16), outline="")
            line = [(x(t_now), y(pred["from"]))] + [
                (x(t_now + m * 60), y(v)) for m, v, _lo, _hi in pred["points"]]
            cv.create_line(*[c for xy in line for c in xy], fill=pal.dim, width=1.5, dash=(4, 3))

        if len(second) >= 2:   # il secondo sensore: una linea di un altro colore, sotto
            coords = [c for p in second for c in (x(p["time"]), y(p["mgdl"]))]
            cv.create_line(*coords, fill=self.second_color(), width=1.5, smooth=True)
            last = second[-1]
            r2 = max(2, (bottom - top) / 70)
            cv.create_oval(x(last["time"]) - 1.6 * r2, y(last["mgdl"]) - 1.6 * r2,
                           x(last["time"]) + 1.6 * r2, y(last["mgdl"]) + 1.6 * r2,
                           fill=self.second_color(), outline="")
        if len(points) >= 2:
            coords = []
            for p in points:
                coords += [x(p["time"]), y(p["mgdl"])]
            cv.create_line(*coords, fill=pal.line, width=1.5, smooth=True)
        r = max(2, (bottom - top) / 70)
        for p in points:
            px, py = x(p["time"]), y(p["mgdl"])
            col = pal.value(cfg, p["mgdl"])
            cv.create_oval(px - r, py - r, px + r, py + r, fill=col, outline="")
        current = self.ctl.current
        if current and points:
            px, py = x(current["time"]), y(current["mgdl"])
            col = pal.value(cfg, current["mgdl"])
            cv.create_oval(px - 2.2 * r, py - 2.2 * r, px + 2.2 * r, py + 2.2 * r,
                           outline=col, width=2)

    def draw_grip(self, W, H):
        if self.locked():
            return
        for i in (4, 9, 14):
            self.canvas.create_line(W - i, H - 2, W - 2, H - i, fill=self.c.grid, width=2)
