"""Anteprima col grafico: tenendo il mouse un secondo sul valore della barra compare
sopra di lui, con dissolvenza e un piccolo scorrimento, lo stesso contenuto del pannello
sullo sfondo (valore, statistiche, grafico delle ultime ore); spostando il mouse sparisce
allo stesso modo. Non prende il focus e non si sposta: è solo da guardare."""

import tkinter as tk

from .desktop import DesktopView
from .taskbar import IS_WIN
from .theme import palette

DELAY_MS = 1000     # quanto tenere il mouse sul valore
POLL_MS = 100       # ogni quanto si guarda dov'è il mouse
STEPS = 8           # fotogrammi dell'animazione...
STEP_MS = 18        # ...uno ogni 18 ms (circa 150 ms in tutto)
ALPHA = 1.0
SLIDE = 12          # pixel di scorrimento verso l'alto mentre compare
WIDTH, HEIGHT = 500, 310

if IS_WIN:
    from .taskbar import GWL_EXSTYLE, WS_EX_TOOLWINDOW, user32
    WS_EX_NOACTIVATE = 0x08000000


def ease(x):
    """Rallenta alla fine (ease-out cubica)."""
    return 1 - (1 - x) ** 3


class PeekView(DesktopView):
    """Il disegno è quello del pannello (DesktopView.draw); cambia solo la finestra."""

    def __init__(self, ctl):   # niente DesktopView.__init__: posizione e trascinamento no
        self.ctl = ctl
        self.cfg = ctl.cfg
        self.c = palette(self.cfg)
        self.alive = True
        self.drag = None
        self.shown = False
        self.progress = 0.0   # 0 = nascosta, 1 = del tutto visibile
        self._anim = None
        self._target = (0, 0)
        self._slide = SLIDE
        self.s = 1.0

        self.root = tk.Toplevel(ctl.root)
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=self.c.grid)   # bordo sottile
        self.canvas = tk.Canvas(self.root, bg=self.c.panel, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)
        # su Windows la dimensione vera arriva dopo: si ridisegna quando arriva
        self.canvas.bind("<Configure>", lambda _e: self.render())
        self.s = max(1.0, self.root.winfo_fpixels("1i") / 96)
        self._styled = False

    def locked(self):
        return True   # niente angolo per ridimensionare

    def draw_grip(self, W, H):
        pass

    def render(self):
        if self.shown:
            self.draw()

    # ---- comparsa e scomparsa ----
    def show(self, anchor, screen):
        """anchor: rettangolo del valore; screen: monitor (sinistra, alto, destra, basso)."""
        if self.shown or not self.alive:
            return
        self.shown = True
        w, h = int(WIDTH * self.s), int(HEIGHT * self.s)
        left, top, right, bottom = screen
        x = min(max((anchor[0] + anchor[2]) // 2 - w // 2, left + 8), right - w - 8)
        gap = int(10 * self.s)
        if anchor[1] - h - gap >= top:          # barra in basso: sopra il valore
            y, self._slide = anchor[1] - h - gap, int(SLIDE * self.s)
        else:                                   # barra in alto: sotto
            y, self._slide = anchor[3] + gap, -int(SLIDE * self.s)
        self._target = (x, y)
        if self.progress == 0:
            self.root.geometry(f"{w}x{h}+{x}+{y + self._slide}")
            self._set_alpha(0.0)
            self.root.deiconify()
            self._no_focus()
            self.root.update_idletasks()
        self.draw()
        self._animate()

    def hide(self):
        if not self.shown:
            return
        self.shown = False
        self._animate()

    def _no_focus(self):
        """Niente pulsante nella barra, niente Alt+Tab e niente focus (Windows)."""
        if not IS_WIN or self._styled:
            return
        self._styled = True
        self.root.update_idletasks()
        hwnd = user32.GetParent(self.root.winfo_id())
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                              | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)

    def _set_alpha(self, alpha):
        try:
            self.root.attributes("-alpha", alpha)
        except tk.TclError:
            pass

    def _animate(self):
        if self._anim is None:
            self._step()

    def _step(self):
        self._anim = None
        if not self.alive:
            return
        goal = 1.0 if self.shown else 0.0
        if self.progress < goal:
            self.progress = min(goal, self.progress + 1 / STEPS)
        elif self.progress > goal:
            self.progress = max(goal, self.progress - 1 / STEPS)
        k = ease(self.progress)
        x, y = self._target
        self._set_alpha(ALPHA * k)
        self.root.geometry(f"+{x}+{int(y + self._slide * (1 - k))}")
        if self.progress == goal:
            if goal == 0:
                self.root.withdraw()
            else:
                self.draw()
            return
        self._anim = self.root.after(STEP_MS, self._step)

    def destroy(self):
        self.alive = False
        self.root.destroy()


class HoverWatch:
    """Quando il mouse entra nel valore, guarda ogni 100 ms dov'è: dopo un secondo
    fermo lì mostra l'anteprima, appena esce la nasconde. Guardare la posizione (invece
    di contare gli eventi di entrata e uscita) evita falsi segnali tra una cifra e
    l'altra."""

    def __init__(self, view):
        self.view = view
        self.peek = None
        self.since = None
        self._poll = None

    def enter(self, _event=None):
        if self._poll is None and self.view.cfg.get("hover_chart", True):
            self.since = None
            self._poll = self.view.root.after(POLL_MS, self.check)

    def check(self):
        self._poll = None
        view = self.view
        if not view.alive:
            return
        rect = view.value_rect()
        x, y = view.root.winfo_pointerxy()
        inside = rect[0] <= x < rect[2] and rect[1] <= y < rect[3] and not view.hidden
        if not inside:
            self.stop()
            return
        self.since = self.since or 0
        self.since += POLL_MS
        if self.since >= DELAY_MS and (self.peek is None or not self.peek.shown):
            if self.peek is None:
                self.peek = PeekView(view.ctl)
            self.peek.show(rect, view.screen or (0, 0, view.root.winfo_screenwidth(),
                                                 view.root.winfo_screenheight()))
        self._poll = view.root.after(POLL_MS, self.check)

    def stop(self):
        """Mouse uscito, menu aperto o elemento chiuso: via l'anteprima."""
        if self._poll is not None:
            try:
                self.view.root.after_cancel(self._poll)
            except tk.TclError:
                pass
            self._poll = None
        self.since = None
        if self.peek is not None:
            self.peek.hide()

    def render(self):
        if self.peek is not None:
            self.peek.render()

    def destroy(self):
        if self.peek is not None:
            self.peek.destroy()
            self.peek = None
