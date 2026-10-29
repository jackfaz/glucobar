"""La scheda Avvisi e suoni su Windows vero (workflow ui-test.yml): GlucoBar completo
(collegato a un LibreLinkUp finto), un pacchetto importato, poi suoni, pacchetto e
ripetizione cambiati uno dopo l'altro come farebbe una persona, con ▶ e Applica (se c'è).
GlucoBar deve restare aperto e salvare le scelte.

Uso: python tools/win_sound_ui_test.py [--strict]
"""

import os
import shutil
import sys
import threading
import time
import traceback
import zipfile
from http.server import HTTPServer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_librelinkup import FakeLibreView  # noqa: E402

DATA = os.path.join(ROOT, "tests", "data")


def notice(title, text, level="notice"):
    print(f"::{level} title={title}::{text}", flush=True)


def main():
    FakeLibreView.state = {"logins": 0, "redirect": False, "redirected": False, "terms": False}
    server = HTTPServer(("127.0.0.1", 0), FakeLibreView)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.environ["LLU_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"
    from glucobar import config, credentials, sound
    shutil.rmtree(config.CONFIG_DIR, ignore_errors=True)
    cfg = config.load_config()
    cfg.update(source="libre", email="a@b.c", app_version="4.20.0", language="en",
               elements=["window"], update_check=False, alert_low=True, alert_high=True)
    config.save_config(cfg)
    credentials.set_password("a@b.c", "segreta", "libre")
    archive = os.path.join(os.environ.get("TEMP", "."), "UI pack.zip")
    with zipfile.ZipFile(archive, "w") as z:
        for name in os.listdir(DATA):
            z.write(os.path.join(DATA, name), name)
    pack, refs = sound.import_files([archive])
    from glucobar.i18n import set_language
    set_language("en")
    from glucobar.controller import Controller
    from glucobar.settings import SettingsWindow
    ctl = Controller(config.load_config())
    done = []
    errors = []

    def report(exc, val, tb):
        errors.append("".join(traceback.format_exception(exc, val, tb))[-600:])
    ctl.root.report_callback_exception = report

    def window():
        return SettingsWindow.current

    def pick(combo, value_index):
        combo.current(value_index)
        combo.event_generate("<<ComboboxSelected>>")

    steps = []

    def add(delay, fn):
        steps.append((delay, fn))

    def ref_index(ref):
        return window().sound_refs.index(ref)

    add(3000, lambda: SettingsWindow.open(ctl, "alerts"))
    for n, (kind, ref) in enumerate([("low", refs[0]), ("high", refs[1]), ("low", refs[2]),
                                     ("high", "builtin:siren"), ("other", refs[3])]):
        # due scelte di fila, a mezzo secondo l'una dall'altra, e ▶
        add(500, lambda k=kind, r=ref: pick(window().sound_boxes[k], ref_index(r)))
        add(300, lambda k=kind: window().win.update())
    add(500, lambda: pick(window().repeat_boxes["low"], 1))
    add(500, lambda: pick(window().repeat_boxes["high"], 3))
    add(500, lambda: pick(window().pack_box, window().pack_names.index(pack)))
    add(500, lambda: pick(window().sound_boxes["low"], ref_index(refs[1])))
    add(800, lambda: getattr(window(), "apply_sounds", lambda: None)())
    add(1500, lambda: (done.append(dict(ctl.cfg)), window().close(), ctl.quit()))

    def run(i=0):
        if i < len(steps):
            delay, fn = steps[i]
            try:
                fn()
            except Exception:
                errors.append(traceback.format_exc()[-600:])
            ctl.root.after(delay, run, i + 1)
    ctl.root.after(4000, run)
    ctl.run()
    server.shutdown()
    with open(config.LOG_PATH, encoding="utf-8") as f:
        log_lines = [line.strip() for line in f if "suono" in line or "ERRORE" in line]
    final = done[0] if done else {}
    ok = bool(done) and not errors and final.get("sound_low") == refs[1] \
        and final.get("repeat_low") == 15 and final.get("repeat_high") == 60
    notice("Scheda suoni", f"{'ok' if ok else 'NO'} | basso={final.get('sound_low')} "
           f"alto={final.get('sound_high')} altro={final.get('sound_other')} "
           f"ripeti={final.get('repeat_low')}/{final.get('repeat_high')} "
           f"pacchetto={final.get('sound_pack')} | errori: {' // '.join(errors) or 'nessuno'} "
           f"| log: {' | '.join(log_lines[-8:])}", "notice" if ok else "error")
    return 1 if not ok and "--strict" in sys.argv else 0


if __name__ == "__main__":
    sys.exit(main())
