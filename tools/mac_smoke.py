"""Prova dal vivo dell'app per Mac (in GitHub Actions, su un Mac vero).

Uso: python tools/mac_smoke.py dist/GlucoBar.app
Avvia GlucoBar collegato a un sito Nightscout finto, aspetta che il valore compaia,
fotografa la barra dei menu e lo schermo, poi lo chiude con `glucobar stop` e
controlla che si sia chiuso davvero. Le foto finiscono anche negli avvisi del job
(in base64), così si vedono senza scaricare niente. Esce con 1 se qualcosa non va.
"""

import base64
import io
import json
import os
import subprocess
import sys
import threading
import time
from http.server import HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_nightscout import FakeNightscout, entry  # noqa: E402

CONFIG_DIR = os.path.expanduser("~/Library/Application Support/GlucoBar")


def notice(title, text):
    print(f"::notice title={title}::{text}", flush=True)


def photo(title, box_of, max_width):
    """Screenshot ritagliato (box_of: dimensioni -> rettangolo), in un avviso del job."""
    from PIL import Image
    path = "/tmp/glucobar-shot.png"
    if subprocess.run(["screencapture", "-x", path]).returncode != 0:
        print(f"{title}: screenshot non riuscito")
        return
    img = Image.open(path).convert("RGB")
    img = img.crop(box_of(*img.size))
    img.thumbnail((max_width, 900))
    for quality in (75, 55, 35):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=quality)
        if buf.tell() < 11_000:
            break
    # un avviso tiene al massimo 4096 caratteri: in più pezzi, da rimettere insieme
    data = base64.b64encode(buf.getvalue()).decode()
    chunks = [data[i:i + 4000] for i in range(0, len(data), 4000)]
    for n, chunk in enumerate(chunks, 1):
        notice(f"{title} {n}/{len(chunks)}", chunk)


def main(app):
    exe = os.path.join(app, "Contents", "MacOS", "GlucoBar")
    cli = os.path.join(app, "Contents", "MacOS", "glucobar-cli")
    FakeNightscout.state = {"auth": "public", "queries": [],
                            "entries": [entry(1 + 5 * i, 142 - i, "FortyFiveUp" if i == 0 else "Flat")
                                        for i in range(100)]}
    server = HTTPServer(("127.0.0.1", 0), FakeNightscout)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(os.path.join(CONFIG_DIR, "config.json"), "w") as f:
        json.dump({"source": "nightscout", "email": f"http://127.0.0.1:{server.server_port}",
                   "elements": ["tray", "window"], "language": "it"}, f)

    proc = subprocess.Popen([exe])
    time.sleep(12)
    ok = proc.poll() is None
    print("GlucoBar aperto:", ok)
    if ok:
        photo("barra dei menu", lambda w, h: (max(0, w - 900), 0, w, max(30, h // 25)), 900)
        photo("schermo", lambda w, h: (0, 0, w, h), 640)
        stop = subprocess.run([cli, "stop"], capture_output=True, text=True)
        print("glucobar stop:", stop.returncode, stop.stdout.strip(), stop.stderr.strip())
        time.sleep(2)
        closed = proc.poll() is not None
        print("GlucoBar chiuso:", closed)
        ok = stop.returncode == 0 and closed
        if not closed:
            proc.kill()
    try:
        with open(os.path.join(CONFIG_DIR, "glucobar.log"), encoding="utf-8") as f:
            print("--- log ---\n" + "".join(f.readlines()[-25:]))
    except OSError:
        print("(nessun log)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
