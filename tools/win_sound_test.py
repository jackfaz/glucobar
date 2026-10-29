"""I suoni degli avvisi su Windows vero (workflow ui-test.yml): i suoni di GlucoBar e i
file dei pacchetti (WAV, MP3, M4A, MP4) si aprono e partono con MCI, e si fermano.

Uso: python tools/win_sound_test.py [--strict]
I risultati sono negli avvisi del job; con --strict esce con 1 se qualcosa non va.
"""

import os
import shutil
import sys
import time
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DATA = os.path.join(ROOT, "tests", "data")


def notice(title, text, level="notice"):
    print(f"::{level} title={title}::{text}", flush=True)


def mci_error(code):
    import ctypes
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.winmm.mciGetErrorStringW(code, buf, 255)
    return buf.value


def main():
    from glucobar import sound
    shutil.rmtree(sound.SOUNDS_DIR, ignore_errors=True)
    # un pacchetto da zip, come lo importa la finestra Impostazioni
    archive = os.path.join(os.environ.get("TEMP", "."), "Test pack.zip")
    with zipfile.ZipFile(archive, "w") as z:
        for name in os.listdir(DATA):
            z.write(os.path.join(DATA, name), f"inside/{name}")
    pack, refs = sound.import_files([archive])
    problems = []
    notice("Suoni: importati", f"{pack}: {refs}")
    for ref in [f"builtin:{n}" for n in sound.BUILTIN] + refs:
        path = sound.resolve(ref)
        err, _ = sound._mci(f'open "{path}" type mpegvideo alias probe')
        length = sound._mci("status probe length")[1] if not err else ""
        sound._mci("close probe")
        ok = sound.play(ref, 30)
        time.sleep(0.3)
        mode = sound._mci(f"status {sound._ALIAS} mode")[1]
        sound.stop()
        good = not err and ok and length not in ("", "0")
        notice(f"Suono {ref}", f"{'ok' if good else 'NO'} | apertura={err} {mci_error(err) if err else ''}"
               f" | durata={length} ms | play={ok} | stato={mode}",
               "notice" if good else "error")
        if not good:
            problems.append(ref)
    return 1 if problems and "--strict" in sys.argv else 0


if __name__ == "__main__":
    sys.exit(main())
