"""I suoni degli avvisi su Windows vero (workflow ui-test.yml): un pacchetto importato
da zip, i file MP3, M4A e MP4 convertiti in WAV da Media Foundation (con la durata
giusta) e i suoni di GlucoBar. I computer di GitHub non hanno l'audio: qui si controlla
che i file si leggano e che suonarli non dia errori, non che si sentano.

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


def main():
    from glucobar import sound
    shutil.rmtree(sound.SOUNDS_DIR, ignore_errors=True)
    shutil.rmtree(sound.CACHE_DIR, ignore_errors=True)
    archive = os.path.join(os.environ.get("TEMP", "."), "Test pack.zip")
    with zipfile.ZipFile(archive, "w") as z:
        for name in os.listdir(DATA):
            z.write(os.path.join(DATA, name), f"inside/{name}")
    pack, refs = sound.import_files([archive])
    notice("Suoni: importati", f"{pack}: {refs}")
    problems = []
    for ref in [f"builtin:{n}" for n in sound.BUILTIN] + refs:
        start = time.time()
        try:
            wav = sound.decoded(sound.resolve(ref))
            length, error = sound.duration(wav), ""
        except Exception as e:
            length, error = 0, repr(e)
        took = time.time() - start
        played = sound.play(ref, 40)
        sound.stop()
        # chime: un secondo; i suoni di GlucoBar almeno 0.3 s
        good = (0.9 < length < 1.2) if not ref.startswith("builtin:") else length > 0.3
        notice(f"Suono {ref}", f"{'ok' if good else 'NO'} | durata={length:.2f} s | "
               f"conversione {took:.2f} s | play={played} {error}",
               "notice" if good else "error")
        if not good:
            problems.append(ref)
    # un file che non è audio: errore chiaro, e play() suona quello di GlucoBar
    bad = os.path.join(sound.SOUNDS_DIR, pack, "broken.mp3")
    with open(bad, "wb") as f:
        f.write(b"not audio" * 100)
    ok = not sound.check(f"{pack}/broken.mp3")
    notice("Suono rovinato", f"{'ok' if ok else 'NO'} | riconosciuto come non leggibile",
           "notice" if ok else "error")
    if not ok:
        problems.append("broken")
    return 1 if problems and "--strict" in sys.argv else 0


if __name__ == "__main__":
    sys.exit(main())
