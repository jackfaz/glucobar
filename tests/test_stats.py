import unittest

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


if __name__ == "__main__":
    unittest.main()
