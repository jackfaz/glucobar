"""Suoni degli avvisi: ripetizione per basso e molto alto, pacchetti, importazione."""

import json
import os
import tempfile
import time
import unittest
import wave
import zipfile
from unittest import mock

from glucobar import alerts, config, sound
from glucobar.config import DEFAULT_CONFIG


def reading(mgdl, minutes_ago=0):
    return {"mgdl": mgdl, "trend": "Flat", "time": time.time() - minutes_ago * 60}


class RepeatAlarmTest(unittest.TestCase):
    """Il suono ripetuto finché il valore non torna nel range (o finché lo si zittisce),
    con un intervallo per il basso e uno per il molto alto."""

    def setUp(self):
        from glucobar.controller import Controller

        class Stub:
            alarms_active = Controller.alarms_active
            repeat_alarm = Controller.repeat_alarm
            repeat_seconds = Controller.repeat_seconds
            silence = Controller.silence

            def __init__(self):
                self.cfg = dict(DEFAULT_CONFIG, alert_low=True, alert_high=True,
                                repeat_low=15, repeat_high=60)
                self.alerts = alerts.AlertWatch()
                self.others, self.other_alerts = [], {}
                self.silenced, self._last_sound, self._alarm_sounding = set(), {}, False
                self.sounds = []

            def sound_now(self, kind="low"):
                self.sounds.append(kind)
                self._last_sound[kind] = time.time()

        self.ctl = Stub()
        self.stop = mock.patch.object(sound, "stop").start()
        self.addCleanup(mock.patch.stopall)

    def test_repeats_until_back_in_range(self):
        ctl = self.ctl
        ctl.alerts.check(ctl.cfg, reading(60))
        ctl.repeat_alarm()
        ctl.repeat_alarm()                       # non prima dell'intervallo
        self.assertEqual(ctl.sounds, ["low"])
        ctl._last_sound["low"] -= 16
        ctl.repeat_alarm()
        self.assertEqual(ctl.sounds, ["low", "low"])
        ctl.alerts.check(ctl.cfg, reading(110))  # di nuovo nel range: basta, e il suono si ferma
        ctl._last_sound["low"] -= 60
        ctl.repeat_alarm()
        self.assertEqual(len(ctl.sounds), 2)
        self.stop.assert_called_once()

    def test_own_interval_for_high(self):
        ctl = self.ctl
        ctl.alerts.check(ctl.cfg, reading(280))
        ctl.repeat_alarm()
        ctl._last_sound["high"] -= 30            # 30 s: per il basso basterebbe, per l'alto no
        ctl.repeat_alarm()
        self.assertEqual(ctl.sounds, ["high"])
        ctl._last_sound["high"] -= 31
        ctl.repeat_alarm()
        self.assertEqual(ctl.sounds, ["high", "high"])

    def test_silence_until_next_episode(self):
        ctl = self.ctl
        ctl.alerts.check(ctl.cfg, reading(280))
        ctl.silence(None, "high")
        ctl.repeat_alarm()
        self.assertEqual(ctl.sounds, [])
        ctl.alerts.check(ctl.cfg, reading(150))
        ctl.repeat_alarm()
        self.assertEqual(ctl.silenced, set())    # episodio finito
        ctl.alerts.check(ctl.cfg, reading(285))
        ctl.repeat_alarm()
        self.assertEqual(ctl.sounds, ["high"])

    def test_off_or_stale(self):
        ctl = self.ctl
        ctl.cfg["repeat_low"] = 0
        ctl.alerts.check(ctl.cfg, reading(60))
        ctl.repeat_alarm()
        self.assertEqual(ctl.sounds, [])
        ctl.cfg["repeat_low"] = 15
        ctl.alerts.check(ctl.cfg, reading(60, minutes_ago=30))   # dato vecchio: niente suono
        ctl.repeat_alarm()
        self.assertEqual(ctl.sounds, [])

    def test_setting_from_0_10_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            with open(path, "w") as f:
                json.dump({"alert_repeat": True, "alert_repeat_seconds": 30}, f)
            with mock.patch.object(config, "CONFIG_PATH", path):
                cfg = config.load_config()
        self.assertEqual((cfg["repeat_low"], cfg["repeat_high"]), (30, 30))
        self.assertNotIn("alert_repeat", cfg)


class SoundTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        for name in ("SOUNDS_DIR", "CACHE_DIR"):
            patch = mock.patch.object(sound, name, os.path.join(tmp.name, name))
            patch.start()
            self.addCleanup(patch.stop)

    def make(self, pack, *names, manifest=None):
        folder = os.path.join(sound.SOUNDS_DIR, pack)
        os.makedirs(folder, exist_ok=True)
        for name in names:
            open(os.path.join(folder, name), "wb").close()
        if manifest:
            with open(os.path.join(folder, "pack.json"), "w") as f:
                f.write(manifest)

    def test_builtin(self):
        for name in sound.BUILTIN:
            with wave.open(sound.builtin_path(name)) as f:
                self.assertGreater(f.getnframes() / f.getframerate(), 0.3, name)
        self.assertTrue(sound.resolve("builtin:falling").endswith("falling-1.wav"))
        # un file che non c'è più: un suono di GlucoBar, non il silenzio
        self.assertTrue(sound.resolve("Gone/x.mp3").endswith("beeps-1.wav"))

    def test_pack_guess_and_manifest(self):
        self.make("G7", "alerts_sounds_urgent_low_alarm.mp4", "alerts_sounds_low_alert.mp4",
                  "alerts_sounds_urgent_low_soon.mp4", "alerts_sounds_high_alert.mp4",
                  "alerts_sounds_signal_loss_alert.mp4", "readme.txt")
        self.make("Mine", "a.mp3", "b.wav", manifest='{"low": "b.wav", "high": "nope.mp3"}')
        self.assertEqual(list(sound.packs()), ["G7", "Mine"])
        self.assertNotIn("readme.txt", sound.packs()["G7"])
        self.assertEqual(sound.pack_sounds("G7"), {
            "low": "G7/alerts_sounds_urgent_low_alarm.mp4",
            "high": "G7/alerts_sounds_high_alert.mp4",
            "other": "G7/alerts_sounds_signal_loss_alert.mp4"})
        mine = sound.pack_sounds("Mine")
        self.assertEqual(mine["low"], "Mine/b.wav")
        self.assertEqual(mine["high"], sound.DEFAULTS["high"])   # file che non c'è
        self.assertEqual(sound.pack_sounds("GlucoBar"), sound.DEFAULTS)
        self.assertEqual(sound.label("G7/alerts_sounds_urgent_low_alarm.mp4"),
                         "Urgent low alarm (G7)")
        self.assertIn(("Mine/a.mp3", "A"), dict(sound.choices())["Mine"])

    def test_import(self):
        src = os.path.join(self.tmp, "Libre 3")
        os.makedirs(src)
        for name in ("low_alarm.mp3", "high_alarm.mp3", "notes.txt"):
            open(os.path.join(src, name), "wb").close()
        archive = os.path.join(self.tmp, "Libre 3.zip")
        with zipfile.ZipFile(archive, "w") as z:
            for name in os.listdir(src):
                z.write(os.path.join(src, name), f"Libre 3/{name}")
            z.writestr("../../evil.mp3", b"x")   # niente file fuori dalla cartella
        pack, refs = sound.import_files([archive])
        self.assertEqual(pack, "Libre 3")
        self.assertEqual(sorted(refs), ["Libre 3/evil.mp3", "Libre 3/high_alarm.mp3",
                                        "Libre 3/low_alarm.mp3"])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "evil.mp3")))
        self.assertEqual(sound.pack_sounds("Libre 3")["low"], "Libre 3/low_alarm.mp3")
        _pack, refs = sound.import_files([os.path.join(src, "low_alarm.mp3")])
        self.assertEqual(refs, ["My sounds/low_alarm.mp3"])
        _pack, refs = sound.import_files([os.path.join(src, "notes.txt")], pack="X")
        self.assertEqual(refs, [])

    def test_play_never_raises(self):
        with mock.patch("subprocess.Popen", side_effect=OSError("no player")), \
                mock.patch("sys.stdout"):
            self.assertTrue(sound.play("builtin:chime", 50))
        sound.stop()


if __name__ == "__main__":
    unittest.main()
