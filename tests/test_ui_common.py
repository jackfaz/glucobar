import time
import unittest

from glucobar.config import DEFAULT_CONFIG
from glucobar.theme import palette
from glucobar.ui_common import beside_value, fmt_value, is_stale


class FormatTest(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(DEFAULT_CONFIG)

    def test_units(self):
        self.assertEqual(fmt_value(self.cfg, 133), "133")
        self.cfg["unit"] = "mmol/L"
        self.assertEqual(fmt_value(self.cfg, 180), "10.0")

    def test_colors(self):
        pal = palette(self.cfg, light=False)
        self.assertEqual(pal.value(self.cfg, 69), pal.low)
        self.assertEqual(pal.value(self.cfg, 70), pal.in_range)
        self.assertEqual(pal.value(self.cfg, 180), pal.in_range)
        self.assertEqual(pal.value(self.cfg, 181), pal.high)
        self.assertEqual(pal.value(self.cfg, 251), pal.very_high)

    def test_beside_value(self):
        now = time.time()
        current = {"mgdl": 150, "time": now, "trend": "FortyFiveUp"}
        history = [{"mgdl": 145, "time": now - 300}, current]
        self.assertEqual(beside_value(self.cfg, history, current), "↗")
        self.cfg["trend_style"] = "delta"
        self.assertEqual(beside_value(self.cfg, history, current), "+5")
        self.assertEqual(beside_value(self.cfg, [current], current), "↗")   # niente delta
        self.cfg["trend_style"] = "both"
        self.assertEqual(beside_value(self.cfg, history, current), "↗ +5")
        self.cfg["unit"] = "mmol/L"
        self.assertEqual(beside_value(self.cfg, history, current), "↗ +0.3")
        old = dict(current, time=now - 20 * 60)
        self.assertEqual(beside_value(self.cfg, history, old), "")

    def test_stale(self):
        self.assertFalse(is_stale(self.cfg, {"time": time.time() - 60}))
        self.assertTrue(is_stale(self.cfg, {"time": time.time() - 16 * 60}))


if __name__ == "__main__":
    unittest.main()
