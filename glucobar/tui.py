"""Mini interfaccia da terminale, senza librerie esterne: elenchi da scorrere con le
frecce, caselle da spuntare con la barra spaziatrice, testo e password.

Ogni widget ridisegna le proprie righe a ogni tasto (sequenze ANSI) e, confermato,
si riduce a una riga di riepilogo. I tasti arrivano da `Terminal.read_key()`,
che nei test si sostituisce con una sequenza finta.
"""

import os
import shutil
import sys

# colori ANSI
RESET, BOLD, DIM = "\x1b[0m", "\x1b[1m", "\x1b[2m"
GREEN, CYAN, RED, YELLOW = "\x1b[32m", "\x1b[36m", "\x1b[31m", "\x1b[33m"
POINTER, ON, OFF, CHECK = "›", "[x]", "[ ]", "√"


class Cancelled(Exception):
    """Ctrl+C o Esc: la procedura si interrompe senza salvare."""


class Terminal:
    """Tastiera in modalità "grezza" e output ANSI, su Windows e su Linux/macOS."""

    def __init__(self, out=None):
        self.out = out or sys.stdout
        self._restore = None
        self._pending = ""   # caratteri già letti ma non ancora consegnati

    @staticmethod
    def interactive():
        return sys.stdin.isatty() and sys.stdout.isatty()

    def __enter__(self):
        if os.name == "nt":
            import ctypes
            k32 = ctypes.windll.kernel32
            mode = ctypes.c_uint32()
            # output: abilita le sequenze ANSI (Windows 10+)
            out = k32.GetStdHandle(-11)
            if k32.GetConsoleMode(out, ctypes.byref(mode)):
                k32.SetConsoleMode(out, mode.value | 0x0004)
            # input: Ctrl+C come tasto, non come segnale (niente "Terminare il
            # processo batch?" dal file glucobar.cmd)
            inp = k32.GetStdHandle(-10)
            if k32.GetConsoleMode(inp, ctypes.byref(mode)):
                old = mode.value
                k32.SetConsoleMode(inp, old & ~0x0001)
                self._restore = lambda: k32.SetConsoleMode(inp, old)
        else:
            import termios
            import tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            self._restore = lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old)
        self.write("\x1b[?25l")   # nasconde il cursore
        return self

    def __exit__(self, *exc):
        self.write("\x1b[?25h" + RESET)
        if self._restore:
            self._restore()

    def write(self, text):
        # in modalità grezza "\n" non torna a inizio riga
        self.out.write(text.replace("\n", "\r\n") if os.name != "nt" else text)
        self.out.flush()

    def read_key(self):
        if os.name == "nt":
            import msvcrt
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(
                    msvcrt.getwch(), "")
        else:
            # direttamente dal terminale: con sys.stdin le frecce (ESC [ A) finivano
            # nel buffer di Python e venivano scambiate per Esc
            if not self._pending:
                self._pending = os.read(sys.stdin.fileno(), 64).decode("utf-8", "ignore")
            for seq, name in (("\x1b[A", "up"), ("\x1b[B", "down"), ("\x1b[D", "left"),
                              ("\x1b[C", "right"), ("\x1bOA", "up"), ("\x1bOB", "down")):
                if self._pending.startswith(seq):
                    self._pending = self._pending[len(seq):]
                    return name
            ch, self._pending = self._pending[:1], self._pending[1:]
        return {"\r": "enter", "\n": "enter", " ": "space", "\x08": "backspace",
                "\x7f": "backspace", "\x03": "ctrl-c", "\x1b": "esc"}.get(ch, ch)


class Block:
    """Righe ridisegnate al loro posto a ogni aggiornamento."""

    def __init__(self, term):
        self.term = term
        self.height = 0

    def draw(self, lines):
        up = f"\x1b[{self.height}F" if self.height else "\r"
        self.term.write(up + "\x1b[J" + "\n".join(lines) + "\n")
        self.height = len(lines)


def _key(term):
    key = term.read_key()
    if key in ("ctrl-c", "esc"):
        raise Cancelled()
    return key


def width():
    return shutil.get_terminal_size((100, 24)).columns


def fit(text_, room):
    """Accorcia con … : una riga che va a capo rovinerebbe il ridisegno."""
    return text_ if len(text_) <= room else text_[:max(1, room - 1)] + "…"


def header(title, hint):
    """Titolo e, sotto, il suggerimento sui tasti (righe corte: niente a capo)."""
    lines = [f"{BOLD}{fit(title, width() - 1)}{RESET}"]
    if hint:
        lines.append(f"  {DIM}{fit(hint, width() - 3)}{RESET}")
    return lines


def _done(block, title, answer):
    answer = fit(answer, width() - len(title) - 5)
    block.draw([f"{GREEN}{CHECK}{RESET} {title}: {BOLD}{answer}{RESET}"])


def select(term, title, options, default=0, hint=""):
    """Una scelta tra `options` [(valore, etichetta)], con le frecce. Ritorna il valore."""
    block, pos = Block(term), default
    while True:
        lines = header(title, hint)
        for i, (_value, label) in enumerate(options):
            if i == pos:
                lines.append(f"  {CYAN}{POINTER} {label}{RESET}")
            else:
                lines.append(f"    {label}")
        block.draw(lines)
        key = _key(term)
        if key == "up":
            pos = (pos - 1) % len(options)
        elif key == "down":
            pos = (pos + 1) % len(options)
        elif key == "enter":
            _done(block, title, options[pos][1])
            return options[pos][0]


def multiselect(term, title, options, selected=(), hint="", need_one=""):
    """Caselle da spuntare con lo spazio; Invio conferma. Ritorna i valori spuntati."""
    block, pos = Block(term), 0
    chosen = {v for v, _ in options if v in selected}
    warning = ""
    while True:
        lines = header(title, hint)
        for i, (value, label) in enumerate(options):
            box = f"{GREEN}{ON}{RESET}" if value in chosen else OFF
            if i == pos:
                lines.append(f"  {CYAN}{POINTER}{RESET} {box} {CYAN}{label}{RESET}")
            else:
                lines.append(f"    {box} {label}")
        if warning:
            lines.append(f"  {YELLOW}{warning}{RESET}")
        block.draw(lines)
        key = _key(term)
        warning = ""
        if key == "up":
            pos = (pos - 1) % len(options)
        elif key == "down":
            pos = (pos + 1) % len(options)
        elif key == "space":
            value = options[pos][0]
            chosen ^= {value}
        elif key == "enter":
            if need_one and not chosen:
                warning = need_one
                continue
            result = [v for v, _ in options if v in chosen]
            _done(block, title, ", ".join(label for v, label in options if v in chosen))
            return result


def text(term, title, default="", secret=False, validate=None, hint=""):
    """Riga di testo; con `secret` mostra asterischi. `validate(valore)` ritorna un
    messaggio d'errore oppure None."""
    block, value, error = Block(term), "", ""
    while True:
        shown = "*" * len(value) if secret else value
        placeholder = f"{DIM}{default}{RESET}" if not value and default and not secret else ""
        lines = header(title, hint) + [
            f"  {CYAN}{POINTER}{RESET} {shown}{placeholder}{CYAN}▏{RESET}"]
        if error:
            lines.append(f"  {RED}{error}{RESET}")
        block.draw(lines)
        key = _key(term)
        error = ""
        if key == "enter":
            result = value or default
            error = validate(result) if validate else None
            if error:
                continue
            _done(block, title, "*" * 8 if secret and result else result)
            return result
        if key == "backspace":
            value = value[:-1]
        elif len(key) == 1 and key.isprintable():
            value += key


def confirm(term, title, default=True, yes="Yes", no="No", hint=""):
    options = [(True, yes), (False, no)]
    return select(term, title, options, default=0 if default else 1, hint=hint)


def message(term, text_, color=""):
    term.write(f"{color}{text_}{RESET}\n")
