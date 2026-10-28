import time
import unittest

from glucobar.config import DEFAULT_CONFIG
from glucobar.theme import palette
from glucobar.ui_common import fmt_value, is_stale


class FormatTest(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(DEFAULT_CONFIG)

    def test_units(self):
        self.assertEqual(fmt_value(self.cfg, 133), "133")
        self.cfg["unit"] = "mmol/L"
        self.assertEqual(fmt_value(self.cfg, 180), "10.0")

    def test_colors(self):
        pal = palette(self.cfg, light=False)
        self.assertEqual(pal.value(self.cfg, 69), pal.danger)
        self.assertEqual(pal.value(self.cfg, 70), pal.in_range)
        self.assertEqual(pal.value(self.cfg, 180), pal.in_range)
        self.assertEqual(pal.value(self.cfg, 181), pal.high)
        self.assertEqual(pal.value(self.cfg, 251), pal.danger)

    def test_stale(self):
        self.assertFalse(is_stale(self.cfg, {"time": time.time() - 60}))
        self.assertTrue(is_stale(self.cfg, {"time": time.time() - 16 * 60}))


if __name__ == "__main__":
    unittest.main()
