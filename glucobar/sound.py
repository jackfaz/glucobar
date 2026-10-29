"""Il suono degli avvisi: tre bip brevi, uguali su ogni computer (i suoni di sistema
possono essere muti nello schema audio di Windows). Il file WAV lo crea GlucoBar la
prima volta, nella cartella delle impostazioni."""

import math
import os
import struct
import subprocess
import sys
import wave

from .config import CONFIG_DIR, log

RATE = 22050


def alarm_wav():
    """Percorso del suono (creato se manca)."""
    path = os.path.join(CONFIG_DIR, "alert.wav")
    if not os.path.exists(path):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        frames = bytearray()
        for beep in range(3):
            for i in range(int(RATE * 0.16)):
                fade = min(1.0, i / 200, (RATE * 0.16 - i) / 200)   # niente clic
                tone = math.sin(2 * math.pi * (880 if beep < 2 else 1175) * i / RATE)
                frames += struct.pack("<h", int(12000 * fade * tone))
            frames += b"\x00\x00" * int(RATE * 0.09)
        with wave.open(path, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(RATE)
            f.writeframes(bytes(frames))
    return path


def play():
    """Suona senza aspettare la fine; mai un errore che fermi GlucoBar."""
    try:
        path = alarm_wav()
        if sys.platform == "win32":
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif sys.platform == "darwin":
            subprocess.Popen(["afplay", path])
        else:
            for player in ("paplay", "aplay"):
                try:
                    subprocess.Popen([player, path], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    return
                except OSError:
                    continue
            print("\a", end="", flush=True)
    except Exception as e:
        log(f"suono non riprodotto: {e}")
