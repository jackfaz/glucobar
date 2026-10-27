import time
import unittest

from glucobar.config import DEFAULT_CONFIG
from glucobar.ui_common import GREEN, ORANGE, RED, color_for, fmt_value, is_stale


class FormatTest(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(DEFAULT_CONFIG)

    def test_units(self):
        self.assertEqual(fmt_value(self.cfg, 133), "133")
        self.cfg["unit"] = "mmol/L"
        self.assertEqual(fmt_value(self.cfg, 180), "10.0")

    def test_colors(self):
        self.assertEqual(color_for(self.cfg, 69), RED)
        self.assertEqual(color_for(self.cfg, 70), GREEN)
        self.assertEqual(color_for(self.cfg, 180), GREEN)
        self.assertEqual(color_for(self.cfg, 181), ORANGE)
        self.assertEqual(color_for(self.cfg, 251), RED)

    def test_stale(self):
        self.assertFalse(is_stale(self.cfg, {"time": time.time() - 60}))
        self.assertTrue(is_stale(self.cfg, {"time": time.time() - 16 * 60}))


if __name__ == "__main__":
    unittest.main()
