"""I suoni degli avvisi.

Quelli di GlucoBar sono generati qui (file WAV creati la prima volta, nella cartella
delle impostazioni): uguali su ogni computer, anche dove i suoni di sistema sono muti.
Si possono aggiungere i propri: ogni cartella dentro `sounds` è un pacchetto, con i suoi
file audio (WAV, MP3, M4A...). Un file `pack.json` facoltativo dice quale usare per ogni
avviso, es. {"low": "basso.mp3", "high": "alto.mp3", "other": "segnale.mp3"};
senza, GlucoBar li sceglie dal nome.

Un suono si indica con "builtin:nome" (di GlucoBar) o "pacchetto/file.mp3".
"""

import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import wave
import zipfile

from .config import CONFIG_DIR, log

RATE = 22050
SOUNDS_DIR = os.path.join(CONFIG_DIR, "sounds")
CACHE_DIR = os.path.join(CONFIG_DIR, "sounds-builtin")
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".mp4", ".aac", ".wma", ".aif", ".aiff")
KINDS = ("low", "high", "other")   # other: nessun dato e stima della tendenza
MY_SOUNDS = "My sounds"            # dove finiscono i file scelti uno per uno
BUILTIN_PACK = "GlucoBar"


# ---- suoni di GlucoBar ----
def _tone(freqs, length, gap=0.0, decay=0.0, sweep=None):
    """Campioni di un bip (o di una glissata da freqs[0] a sweep)."""
    out = []
    n = int(RATE * length)
    for f in freqs:
        phase = 0.0
        for i in range(n):
            x = i / n
            freq = f if sweep is None else f + (sweep - f) * x
            phase += 2 * math.pi * freq / RATE
            fade = min(1.0, i / 200, (n - i) / 200)          # niente clic
            env = fade * (math.exp(-decay * x) if decay else 1.0)
            out.append(env * (math.sin(phase) + 0.25 * math.sin(2 * phase)) / 1.25)
        out += [0.0] * int(RATE * gap)
    return out


BUILTIN = {
    # nome: (campioni, chi lo usa di default)
    "falling": lambda: _tone([1175, 988, 784], 0.17, 0.07) * 2,     # basso: scende
    "rising": lambda: _tone([784, 988, 1175], 0.17, 0.07) * 2,      # alto: sale
    "beeps": lambda: _tone([880, 880, 1175], 0.16, 0.09),           # fino alla 0.10.1
    "chime": lambda: _tone([1319, 988], 0.5, 0.0, decay=5),
    "urgent": lambda: _tone([1568] * 6, 0.07, 0.05) * 2,
    "siren": lambda: _tone([700], 0.45, 0, sweep=1400) + _tone([1400], 0.45, 0.1, sweep=700),
    "soft": lambda: _tone([660, 880], 0.6, 0.1, decay=4),
}
DEFAULTS = {"low": "builtin:falling", "high": "builtin:rising", "other": "builtin:chime"}


def builtin_path(name):
    path = os.path.join(CACHE_DIR, f"{name}-1.wav")   # -1: cambia se cambia il suono
    if not os.path.exists(path):
        os.makedirs(CACHE_DIR, exist_ok=True)
        frames = b"".join(struct.pack("<h", int(12000 * s)) for s in BUILTIN[name]())
        with wave.open(path + ".tmp", "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(RATE)
            f.writeframes(frames)
        os.replace(path + ".tmp", path)
    return path


# ---- pacchetti ----
def is_audio(name):
    return name.lower().endswith(AUDIO_EXT) and not name.startswith(".")


def packs():
    """{nome del pacchetto: [file audio]}, in ordine alfabetico."""
    out = {}
    try:
        names = sorted(os.listdir(SOUNDS_DIR), key=str.lower)
    except OSError:
        return out
    for name in names:
        folder = os.path.join(SOUNDS_DIR, name)
        if name.startswith(".") or not os.path.isdir(folder):
            continue
        files = sorted((f for f in os.listdir(folder) if is_audio(f)), key=str.lower)
        if files:
            out[name] = files
    return out


def nice_name(filename):
    """"alerts_sounds_urgent_low.mp4" -> "Urgent low"."""
    stem = os.path.splitext(filename)[0]
    stem = re.sub(r"^(alerts?_sounds?|sounds?|alarms?)_", "", stem, flags=re.I)
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    return stem[:1].upper() + stem[1:]


def label(ref):
    if not ref or ref.startswith("builtin:"):
        name = (ref or DEFAULTS["low"]).split(":", 1)[1]
        from .i18n import t
        return t(f"sound_{name}")
    pack, _, filename = ref.partition("/")
    return f"{nice_name(filename)} ({pack})"


def choices():
    """[(gruppo, [(ref, testo)])]: prima i suoni di GlucoBar, poi un gruppo per pacchetto."""
    out = [(BUILTIN_PACK, [(f"builtin:{n}", label(f"builtin:{n}")) for n in BUILTIN])]
    for pack, files in packs().items():
        out.append((pack, [(f"{pack}/{f}", nice_name(f)) for f in files]))
    return out


def resolve(ref):
    """Percorso del file di un suono; quello di default se il file non c'è più."""
    if ref and not ref.startswith("builtin:"):
        pack, _, filename = ref.partition("/")
        path = os.path.join(SOUNDS_DIR, pack, filename)
        if pack and filename and os.path.isfile(path):
            return path
        ref = None
    name = (ref or "").split(":", 1)[-1]
    return builtin_path(name if name in BUILTIN else "beeps")


_WORDS = {   # parole nel nome del file, con il loro peso, per avviso
    "low": {"urgent": 3, "low": 4, "hypo": 4, "alarm": 1, "soon": -3, "fall": -2,
            "high": -9, "rise": -9, "rising": -9, "signal": -9, "loss": -9},
    "high": {"high": 4, "hyper": 4, "alarm": 1, "intense": 1, "low": -9, "urgent": -2,
             "rise": -2, "rising": -2, "signal": -9, "loss": -9},
    "other": {"signal": 4, "loss": 4, "error": 3, "system": 2, "technical": 2, "stale": 4,
              "low": -9, "high": -9, "success": -9},
}


def guess(files, kind):
    """Il file del pacchetto più adatto a un avviso, dal nome; None se nessuno."""
    best, best_score = None, 0
    for f in files:
        words = re.findall(r"[a-z]+", os.path.splitext(f)[0].lower())
        score = sum(_WORDS[kind].get(w, 0) for w in words)
        if score > best_score:
            best, best_score = f, score
    return best


def pack_sounds(pack):
    """{avviso: ref} per un pacchetto: da pack.json se c'è, altrimenti dal nome dei file."""
    if pack == BUILTIN_PACK:
        return dict(DEFAULTS)
    files = packs().get(pack, [])
    try:
        with open(os.path.join(SOUNDS_DIR, pack, "pack.json"), encoding="utf-8") as f:
            chosen = json.load(f)
    except (OSError, ValueError):
        chosen = {}
    out = {}
    for kind in KINDS:
        name = chosen.get(kind) if isinstance(chosen, dict) else None
        name = name if name in files else guess(files, kind)
        out[kind] = f"{pack}/{name}" if name else DEFAULTS[kind]
    return out


def safe_name(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", os.path.basename(name)).strip(" .")
    return name[:80] or "sound"


def import_files(paths):
    """Copia file audio (o un .zip) tra i pacchetti. Restituisce (pacchetto, [ref])."""
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    refs, pack = [], None
    for path in paths:
        if path.lower().endswith(".zip"):
            pack = safe_name(os.path.splitext(os.path.basename(path))[0])
            refs += _import_zip(path, pack)
            continue
        if not is_audio(os.path.basename(path)):
            continue
        pack = pack or MY_SOUNDS
        folder = os.path.join(SOUNDS_DIR, pack)
        os.makedirs(folder, exist_ok=True)
        name = safe_name(os.path.basename(path))
        target = os.path.join(folder, name)
        if os.path.abspath(path) != os.path.abspath(target):
            shutil.copyfile(path, target)
        refs.append(f"{pack}/{name}")
    return pack, refs


def _import_zip(path, pack):
    folder = os.path.join(SOUNDS_DIR, pack)
    os.makedirs(folder, exist_ok=True)
    refs = []
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            base = os.path.basename(info.filename)
            if info.is_dir() or info.file_size > 20_000_000:
                continue
            if base == "pack.json" or is_audio(base):
                name = "pack.json" if base == "pack.json" else safe_name(base)
                with z.open(info) as src, open(os.path.join(folder, name), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                if name != "pack.json":
                    refs.append(f"{pack}/{name}")
    return refs


def open_folder():
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(SOUNDS_DIR)
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", SOUNDS_DIR])


# ---- riproduzione ----
_ALIAS = "glucobar_alert"
_proc = None
_mci_open = False


def _mci(command):
    import ctypes
    buf = ctypes.create_unicode_buffer(256)
    err = ctypes.windll.winmm.mciSendStringW(command, buf, 255, 0)
    return err, buf.value


def stop():
    """Ferma il suono in corso (i suoni lunghi, quando si torna nel range o si zittisce)."""
    global _proc, _mci_open
    try:
        if _mci_open:
            _mci(f"close {_ALIAS}")
            _mci_open = False
        if _proc and _proc.poll() is None:
            _proc.terminate()
        _proc = None
    except Exception as e:
        log(f"suono non fermato: {e}")


def play(ref=None, volume=100):
    """Suona senza aspettare la fine (fermando quello di prima); mai un errore che
    fermi GlucoBar. Restituisce False se il file non si può riprodurre."""
    global _proc, _mci_open
    stop()
    try:
        path = resolve(ref)
        volume = max(0, min(100, int(volume)))
        if sys.platform == "win32":
            # MCI (Windows Media): WAV, MP3, M4A e gli altri formati di Windows
            err, _ = _mci(f'open "{path}" type mpegvideo alias {_ALIAS}')
            if err:
                log(f"suono non aperto ({err}): {os.path.basename(path)}")
                if path.lower().endswith(".wav"):
                    import winsound
                    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return True
                return False
            _mci_open = True
            _mci(f"setaudio {_ALIAS} volume to {volume * 10}")
            err, _ = _mci(f"play {_ALIAS}")
            return not err
        if sys.platform == "darwin":
            _proc = subprocess.Popen(["afplay", "-v", str(volume / 100), path])
            return True
        for cmd in (["paplay", f"--volume={volume * 655}", path],
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                     "-volume", str(volume), path],
                    ["aplay", "-q", path]):
            try:
                _proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
                return True
            except OSError:
                continue
        print("\a", end="", flush=True)
        return True
    except Exception as e:
        log(f"suono non riprodotto: {e}")
        return False


def playing():
    """Il suono è ancora in corso? (Per i test.)"""
    try:
        if sys.platform == "win32":
            return _mci_open and _mci(f"status {_ALIAS} mode")[1] == "playing"
        return bool(_proc and _proc.poll() is None)
    except Exception:
        return False
