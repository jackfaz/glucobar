import unittest

from glucobar import stats
from glucobar.config import DEFAULT_CONFIG
from glucobar.stats import change, recent, sensor_days, summary

NOW = 1_800_000_000


def m(minutes_ago, value):
    return {"mgdl": value, "trend": 3, "time": NOW - minutes_ago * 60}


class StatsTest(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(DEFAULT_CONFIG)

    def test_recent_filters_and_sorts(self):
        history = [m(10, 120), m(800, 90), m(30, 110), m(5, None)]
        self.assertEqual([p["mgdl"] for p in recent(history, 12, NOW)], [110, 120])

    def test_summary(self):
        points = [m(t, v) for t, v in [(60, 60), (45, 100), (30, 150), (15, 200)]]
        s = summary(points, self.cfg)
        self.assertEqual((s["min"], s["max"], s["mean"]), (60, 200, 127.5))
        self.assertEqual((s["below"], s["in_range"], s["above"]), (25, 50, 25))
        self.assertIsNone(summary([], self.cfg))

    def test_change(self):
        points = [m(30, 100), m(15, 110), m(0, 130)]
        self.assertEqual(change(points, points[-1]), 20)
        self.assertIsNone(change([m(40, 100), m(0, 130)], m(0, 130)))

    def test_sensor_days(self):
        self.assertAlmostEqual(sensor_days({"sensor": {"a": NOW - 3 * 86400}}, NOW), 3)
        self.assertIsNone(sensor_days({"sensor": {}}, NOW))
        self.assertIsNone(sensor_days(None, NOW))



class DeltaTest(unittest.TestCase):
    def test_delta_is_per_five_minutes(self):
        now = 1_800_000_000
        current = {"mgdl": 150, "time": now}
        dexcom = [{"mgdl": 145, "time": now - 300}, {"mgdl": 140, "time": now - 600}, current]
        self.assertEqual(stats.delta(dexcom, current), 5)
        libre = [{"mgdl": 120, "time": now - 900}, current]   # storico ogni 15 minuti
        self.assertEqual(stats.delta(libre, current), 10)
        self.assertIsNone(stats.delta([{"mgdl": 120, "time": now - 3600}, current], current))
        self.assertIsNone(stats.delta([current], current))

    def test_format(self):
        from glucobar.config import DEFAULT_CONFIG
        from glucobar.ui_common import fmt_delta
        cfg = dict(DEFAULT_CONFIG)
        self.assertEqual([fmt_delta(cfg, d) for d in (5, -12.4, 0)], ["+5", "-12", "+0"])
        cfg["unit"] = "mmol/L"
        self.assertEqual(fmt_delta(cfg, 5.4), "+0.3")


if __name__ == "__main__":
    unittest.main()


class PredictTest(unittest.TestCase):
    def test_straight_line(self):
        now = 1_800_000_000
        history = [{"mgdl": 200 - 2 * m, "time": now - (30 - m) * 60} for m in range(0, 31, 5)]
        current = history[-1]                                         # 140, -2 al minuto
        pred = stats.predict(history, current, now=now)
        self.assertAlmostEqual(pred["slope"], -2, places=5)
        minutes, value, low, high = pred["points"][-1]
        self.assertEqual((minutes, round(value)), (30, 80))
        self.assertTrue(low < value < high)
        first = pred["points"][0]                                     # la fascia si allarga
        self.assertLess(first[3] - first[2], high - low)
        self.assertAlmostEqual(stats.minutes_to(pred, 100), 20)
        self.assertIsNone(stats.minutes_to(pred, 70))                 # oltre i 30 minuti
        clamped = stats.predict([dict(m, mgdl=m["mgdl"] - 100) for m in history],
                                dict(current, mgdl=40), now=now)
        self.assertEqual(clamped["points"][-1][1], 40)                # mai sotto 40

    def test_not_enough_data(self):
        now = 1_800_000_000
        current = {"mgdl": 120, "time": now}
        self.assertIsNone(stats.predict([current], current, now=now))
        close = [{"mgdl": 118, "time": now - 120}, current]       # 2 minuti: solo rumore
        self.assertIsNone(stats.predict(close, current, now=now))
        old = {"mgdl": 120, "time": now - 20 * 60}                  # dato vecchio
        self.assertIsNone(stats.predict([dict(old, time=old["time"] - 600), old], old, now=now))

    def test_rising_and_limits(self):
        now = 1_800_000_000
        history = [{"mgdl": 100 + 10 * m, "time": now - (15 - m) * 60} for m in (0, 15)]
        pred = stats.predict(history, history[-1], now=now)
        self.assertEqual(pred["slope"], 4.0)                        # limitata a 4 mg/dL/min
        self.assertEqual(pred["points"][-1][1], 250 + 120)
        self.assertIsNone(stats.minutes_to(pred, 70))
