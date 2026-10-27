"""Modalità "barra": il valore appoggiato sulla barra delle applicazioni di Windows.

Una finestrella senza bordi, con sfondo trasparente, sta sopra la barra a sinistra
delle icone vicino all'orologio ed è tenuta sempre in primo piano.

Perché non "dentro" la barra: su Windows 11 25H2 una finestra agganciata alla barra
(SetParent, come fa TrafficMonitor) viene disegnata SOTTO lo sfondo semitrasparente
della barra e non si vede.

Si nasconde quando un programma è a schermo intero sullo stesso monitor.
"""

import sys
import tkinter as tk
import traceback

from .config import log, save_config
from .i18n import t
from .sources import TREND_ARROWS
from .ui_common import FONT, RED, age_minutes, bind_right_click, color_for, fmt_value, is_stale

IS_WIN = sys.platform == "win32"

if IS_WIN:
    import ctypes
    import winreg
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    user32.FindWindowW.restype = wintypes.HWND
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowExW.restype = wintypes.HWND
    user32.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND,
                                     wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.GetParent.restype = wintypes.HWND
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_uint]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

    user32.MonitorFromWindow.restype = wintypes.HMONITOR
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]

    MONITOR_DEFAULTTONEAREST = 2
    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_TOPMOST = 0x00000008
    GW_HWNDPREV = 3
    user32.GetWindow.argtypes = [wintypes.HWND, ctypes.c_uint]
    user32.GetWindow.restype = wintypes.HWND
    HWND_TOPMOST = wintypes.HWND(-1)
    SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x1, 0x2, 0x10

# Finestre del desktop: se sono in primo piano non è "schermo intero"
DESKTOP_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"}


def enable_dpi_awareness():
    """Coordinate in pixel reali, così combaciano con quelle della barra.
    Va chiamata prima di creare qualsiasi finestra."""
    if not IS_WIN:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def window_rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def monitor_rect(hwnd):
    """Rettangolo del monitor su cui si trova la finestra."""
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST),
                           ctypes.byref(info))
    r = info.rcMonitor
    return r.left, r.top, r.right, r.bottom


def all_taskbars():
    """Barra del monitor principale seguita da quelle degli altri monitor
    (da sinistra a destra). Le altre esistono solo se in Windows è attivo
    "Mostra la barra delle applicazioni su tutti gli schermi"."""
    bars = []
    main = user32.FindWindowW("Shell_TrayWnd", None)
    if main:
        bars.append(main)
    others, h = [], None
    while True:
        h = user32.FindWindowExW(None, h, "Shell_SecondaryTrayWnd", None)
        if not h:
            break
        others.append(h)
    others.sort(key=lambda w: window_rect(w)[0])
    return bars + others


def class_name(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def taskbar_colors():
    """Colori di sfondo/testo simili a quelli della barra (tema chiaro o scuro)."""
    light = False
    if IS_WIN:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            light = winreg.QueryValueEx(key, "SystemUsesLightTheme")[0] == 1
        except OSError:
            pass
    return ("#eeeeee", "#5f6368") if light else ("#1f1f1f", "#a0a0a0")


def windows_above(hwnd, limit=400):
    """Classi delle finestre sopra `hwnd` nell'ordine di Windows (dalla più vicina)."""
    above, h = [], hwnd
    for _ in range(limit):
        h = user32.GetWindow(h, GW_HWNDPREV)
        if not h:
            break
        above.append(h)
    return above


SIZES = ((0.85, "size_small"), (1.0, "size_normal"), (1.12, "size_large"), (1.25, "size_xlarge"))
MAX_SCALE = 1.25


class TaskbarView:
    def __init__(self, ctl):
        self.ctl = ctl
        self.cfg = ctl.cfg
        self.alive = True
        self.hidden = False
        self.last_geometry = None
        self.screen = None   # rettangolo del monitor della barra usata
        self._last_bars = None
        self._last_state = None   # per annotare nel log solo i cambiamenti
        self._checks = 0

        bg, dim = taskbar_colors()
        self.bg = self.cfg["taskbar_bg"] or bg
        self.dim = dim

        self.root = tk.Toplevel(ctl.root)
        self.root.title("GlucoBar")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=self.bg)
        if self.cfg["taskbar_transparent"]:
            try:
                self.root.attributes("-transparentcolor", self.bg)
            except tk.TclError:
                pass  # solo Windows

        self.box = tk.Frame(self.root, bg=self.bg)
        self.box.place(relx=0.5, rely=0.5, anchor="center")
        self.value_lbl = tk.Label(self.box, text="…", bg=self.bg, fg=self.dim)
        self.value_lbl.grid(row=0, column=0, sticky="e")
        self.arrow_lbl = tk.Label(self.box, text="", bg=self.bg, fg=self.dim)
        self.arrow_lbl.grid(row=0, column=1, sticky="w")
        self.info_lbl = tk.Label(self.box, text="", bg=self.bg, fg=self.dim)
        self.info_lbl.grid(row=1, column=0, columnspan=2)
        for lbl in (self.value_lbl, self.arrow_lbl, self.info_lbl):
            lbl.configure(padx=0, pady=0, bd=0)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label=t("menu_refresh"), command=ctl.refresh)
        self.menu.add_command(label=t("menu_unit"), command=ctl.toggle_unit)
        self.menu.add_command(label=t("menu_side"), command=self.toggle_side)
        self.menu.add_command(label=t("menu_monitor"), command=self.next_monitor)
        sizes = tk.Menu(self.menu, tearoff=0)
        self.scale_var = tk.DoubleVar(master=self.menu, value=float(self.cfg["taskbar_scale"]))
        for scale, key in SIZES:
            sizes.add_radiobutton(label=t(key), value=scale, variable=self.scale_var,
                                  command=lambda v=scale: self.set_scale(v))
        self.menu.add_cascade(label=t("menu_size"), menu=sizes)
        self.menu.add_separator()
        ctl.add_common_menu(self.menu)

        for w in (self.root, self.box, self.value_lbl, self.arrow_lbl, self.info_lbl):
            bind_right_click(w, lambda e: self.menu.tk_popup(e.x_root, e.y_root))
            w.bind("<Double-Button-1>", lambda e: ctl.refresh())

        self.root.update_idletasks()
        if IS_WIN:
            # Niente pulsante nella barra e niente Alt+Tab per questa finestra
            hwnd = self.own_hwnd()
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                                  user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_TOOLWINDOW)
        self.reposition()
        self._keep_on_taskbar()

    def destroy(self):
        self.alive = False
        self.root.destroy()

    # ---- posizione sopra la barra ----
    def own_hwnd(self):
        return user32.GetParent(self.root.winfo_id())

    def layout_for(self, height):
        """Caratteri e dimensioni in proporzione all'altezza della barra e alla
        dimensione scelta. Crescono valore e freccia; i minuti al massimo restano
        normali, così le due righe stanno sempre nell'altezza della barra."""
        k = min(max(float(self.cfg.get("taskbar_scale") or 1.0), 0.7), MAX_SCALE)
        self.value_lbl.configure(font=(FONT, -int(height * 0.42 * k), "bold"))
        self.arrow_lbl.configure(font=(FONT, -int(height * 0.36 * k), "bold"))
        self.info_lbl.configure(font=(FONT, -int(height * 0.21 * min(k, 1.0))))
        return int(height * 1.75 * k), height

    def set_scale(self, scale):
        self.cfg["taskbar_scale"] = scale
        save_config(self.cfg)
        self.reposition()

    def taskbar_geometry(self):
        """(left, top, right, bottom) della parte visibile della barra scelta,
        bordo sinistro dell'area delle icone/orologio e se la barra è visibile."""
        if not IS_WIN:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.screen = (0, 0, sw, sh)
            return (0, sh - 48, sw, sh), sw - 200, True
        bars = all_taskbars()
        if not bars:
            return None, 0, False
        wanted = int(self.cfg["taskbar_monitor"])
        index = wanted - 1 if 1 <= wanted <= len(bars) else 0  # non c'è: principale
        tb = bars[index]
        secondary = index > 0
        left, top, right, bottom = window_rect(tb)
        # Sui PC touch con Windows 11 la finestra della barra è più alta di
        # quella visibile: come TrafficMonitor, si misura il pulsante Start
        start = user32.FindWindowExW(tb, None, "Start", None)
        if start:
            s_top, s_bottom = window_rect(start)[1::2]
            if 0 < s_bottom - s_top <= bottom - top:
                top = bottom - (s_bottom - s_top)
        h = bottom - top
        tray = user32.FindWindowExW(tb, None, "TrayNotifyWnd", None)
        tray_left = window_rect(tray)[0] if tray else 0
        if not left < tray_left < right:
            # Le barre secondarie hanno solo l'orologio (~88 px a 100%, come
            # TrafficMonitor); sulla principale lascia ~280 px per icone e orologio
            tray_left = right - int(h * (100 if secondary else 280) / 48)
        self.screen = monitor_rect(tb)
        # barra nascosta (nascondi automaticamente) o non visibile
        visible = bool(user32.IsWindowVisible(tb)) and top < self.screen[3] - 4
        if (index, len(bars)) != self._last_bars:
            self._last_bars = (index, len(bars))
            log(f"barre trovate: {len(bars)} (monitor scelto {wanted}, uso il n. {index + 1})")
        return (left, top, right, bottom), tray_left, visible

    def reposition(self):
        bar, tray_left, visible = self.taskbar_geometry()
        if bar is None:
            return False
        left, top, right, bottom = bar
        w, h = self.layout_for(bottom - top)
        if self.cfg["taskbar_side"] == "right":
            x = tray_left - w - int(h * 0.1)
        else:
            x = left + int(h * 0.25)
        x += int(self.cfg["taskbar_offset"])
        geometry = f"{w}x{h}+{x}+{top}"
        if geometry != self.last_geometry:
            self.root.geometry(geometry)
            self.last_geometry = geometry
            log(f"barra={bar} icone_da_x={tray_left} -> valore in {geometry}")
            self._checks = 0   # ricontrolla subito dove è finita davvero
        return visible

    def state(self):
        """Dove è davvero la finestra del valore e cosa le sta sopra (per il log)."""
        hwnd = self.own_hwnd()
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        bars = set(all_taskbars())
        bar_above = any(h in bars for h in windows_above(hwnd))
        return (f"finestra reale={window_rect(hwnd)} visibile={bool(user32.IsWindowVisible(hwnd))} "
                f"topmost={bool(style & WS_EX_TOPMOST)} barra_sopra={bar_above}")

    def fullscreen_app_active(self):
        """Classe della finestra a schermo intero sul monitor della barra, o None."""
        if not IS_WIN:
            return None
        fg = user32.GetForegroundWindow()
        if not fg or fg == self.own_hwnd() or class_name(fg) in DESKTOP_CLASSES:
            return None
        # Schermo intero sullo stesso monitor della barra usata
        l, t_, r, b = window_rect(fg)
        ml, mt, mr, mb = self.screen or monitor_rect(fg)
        if l <= ml and t_ <= mt and r >= mr and b >= mb:
            return class_name(fg) or "?"
        return None

    def _keep_on_taskbar(self):
        if not self.alive:
            return
        try:
            visible = self.reposition()
            fullscreen = self.fullscreen_app_active()
            hide = not visible or fullscreen
            if hide and not self.hidden:
                self.root.withdraw()
                self.hidden = True
                log("valore nascosto: " + ("barra non visibile" if not visible
                                           else f"app a schermo intero ({fullscreen})"))
            elif not hide and self.hidden:
                self.root.deiconify()
                self.hidden = False
                log("valore di nuovo visibile")
            if IS_WIN and not self.hidden:
                # Se clicchi sulla barra, Windows la porta davanti: torna sopra
                user32.SetWindowPos(self.own_hwnd(), HWND_TOPMOST, 0, 0, 0, 0,
                                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
                # ogni 30 s (e dopo ogni spostamento) annota se qualcosa è cambiato
                if self._checks % 60 == 1:
                    state = self.state()
                    if state != self._last_state:
                        self._last_state = state
                        log("valore sulla barra: " + state)
                self._checks += 1
        except Exception:
            log("controllo posizione:\n" + traceback.format_exc())
        self.root.after(500, self._keep_on_taskbar)

    def toggle_side(self):
        self.cfg["taskbar_side"] = "left" if self.cfg["taskbar_side"] == "right" else "right"
        save_config(self.cfg)
        self.reposition()

    def next_monitor(self):
        count = len(all_taskbars()) if IS_WIN else 1
        current = int(self.cfg["taskbar_monitor"])
        if not 1 <= current <= count:
            current = 1
        self.cfg["taskbar_monitor"] = current % max(count, 1) + 1
        save_config(self.cfg)
        self.reposition()

    def render(self):
        c, error = self.ctl.current, self.ctl.error
        if not c:
            self.value_lbl.config(text="--", fg=self.dim)
            self.arrow_lbl.config(text="")
            self.info_lbl.config(text=t("error_short") if error else "…",
                                 fg=RED if error else self.dim)
            return
        age = age_minutes(c)
        stale = is_stale(self.cfg, c)
        color = self.dim if stale else color_for(self.cfg, c["mgdl"])
        self.value_lbl.config(text=fmt_value(self.cfg, c["mgdl"]), fg=color)
        self.arrow_lbl.config(text="" if stale else " " + TREND_ARROWS.get(c["trend"], ""),
                              fg=color)
        info = t("now") if age == 0 else t("min_short", n=age)
        if error:
            info = "⚠ " + info
        self.info_lbl.config(text=info, fg=RED if (stale or error) else self.dim)
