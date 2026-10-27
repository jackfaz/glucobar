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
