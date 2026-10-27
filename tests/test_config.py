import argparse
import json
import os
import tempfile
import unittest
from unittest import mock

from glucobar import app, config
from glucobar.config import load_config, normalize_elements


class ElementsTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_elements(["desktop", "tray", "tray", "boh"]),
                         ["tray", "desktop"])
        self.assertEqual(normalize_elements([]), ["taskbar"])
        self.assertEqual(normalize_elements(None), ["taskbar"])

    def test_command_line(self):
        self.assertEqual(app.elements_arg("window, taskbar"), ["taskbar", "window"])
        with self.assertRaises(argparse.ArgumentTypeError):
            app.elements_arg("taskbar,orologio")


class LoadConfigTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, "config.json")
        for name, value in (("CONFIG_PATH", self.path),
                            ("LEGACY_CONFIG_PATH", os.path.join(tmp.name, "nessuno.json"))):
            patcher = mock.patch.object(config, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_defaults(self):
        self.assertEqual(load_config()["elements"], ["taskbar", "tray"])

    def test_mode_of_version_020_becomes_elements(self):
        self.write({"mode": "desktop"})
        cfg = load_config()
        self.assertEqual(cfg["elements"], ["tray", "desktop"])
        self.assertNotIn("mode", cfg)

    def test_saved_elements_win(self):
        self.write({"mode": "desktop", "elements": ["window"]})
        self.assertEqual(load_config()["elements"], ["window"])


if __name__ == "__main__":
    unittest.main()


class LegacyImportTest(unittest.TestCase):
    """La prima versione salvava la password in chiaro in .glicemia_widget.json."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.legacy = os.path.join(tmp.name, ".glicemia_widget.json")
        self.saved_passwords = {}
        patches = [
            mock.patch.object(config, "CONFIG_DIR", os.path.join(tmp.name, "GlucoBar")),
            mock.patch.object(config, "CONFIG_PATH", os.path.join(tmp.name, "GlucoBar", "c.json")),
            mock.patch.object(config, "LOG_PATH", os.path.join(tmp.name, "GlucoBar", "log.txt")),
            mock.patch.object(config, "LEGACY_CONFIG_PATH", self.legacy),
            mock.patch("glucobar.credentials.set_password",
                       side_effect=lambda e, p, s="libre": self.saved_passwords.update({e: p})),
            mock.patch("glucobar.credentials.delete_password",
                       side_effect=lambda s=None: self.saved_passwords.clear()),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        with open(self.legacy, "w", encoding="utf-8") as f:
            json.dump({"email": "a@b.c", "password": "in-chiaro", "taskbar_monitor": 2}, f)

    def test_import_removes_plaintext_password(self):
        cfg = load_config()
        self.assertEqual((cfg["email"], cfg["taskbar_monitor"]), ("a@b.c", 2))
        self.assertEqual(self.saved_passwords, {"a@b.c": "in-chiaro"})
        with open(self.legacy, encoding="utf-8") as f:
            legacy = json.load(f)
        self.assertNotIn("password", legacy)
        self.assertTrue(legacy["imported_to_glucobar"])

    def test_forget_everything_does_not_come_back(self):
        load_config()
        config.forget_everything()
        self.assertEqual(self.saved_passwords, {})
        self.assertFalse(os.path.exists(config.CONFIG_DIR))
        self.assertFalse(os.path.exists(self.legacy))
        self.assertEqual(load_config()["email"], "")   # niente reimportazione

    def test_already_imported_file_is_ignored(self):
        load_config()
        os.remove(config.CONFIG_PATH)   # come dopo una disinstallazione vecchia
        self.saved_passwords.clear()
        self.assertEqual(load_config()["email"], "")
        self.assertEqual(self.saved_passwords, {})


class ScrubLegacyTest(LegacyImportTest):
    def test_existing_install_cleans_old_file(self):
        # come dopo la 0.3.0: impostazioni già importate, password ancora nel vecchio file
        os.makedirs(config.CONFIG_DIR)
        with open(config.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"email": "a@b.c"}, f)
        load_config()
        with open(self.legacy, encoding="utf-8") as f:
            self.assertNotIn("password", json.load(f))
