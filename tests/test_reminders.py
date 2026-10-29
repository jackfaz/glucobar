import unittest
from datetime import datetime

from glucobar import reminders


def ts(*args):
    return datetime(*args).timestamp()


class ScheduleTest(unittest.TestCase):
    def setUp(self):
        self.created = ts(2026, 10, 1, 0, 0)

    def rem(self, kind, **fields):
        rem = reminders.new("Farmaci", kind, **fields)
        rem["created"] = self.created
        return rem

    def test_daily(self):
        rem = self.rem("daily", at="08:30")
        now = ts(2026, 10, 29, 9, 0)              # giovedì
        self.assertEqual(reminders.last_time(rem, now), ts(2026, 10, 29, 8, 30))
        self.assertEqual(reminders.next_time(rem, now), ts(2026, 10, 30, 8, 30))
        self.assertTrue(reminders.due(rem, now))
        reminders.fire(rem, now)
        self.assertFalse(reminders.due(rem, now))  # una volta per scadenza
        self.assertTrue(reminders.due(rem, ts(2026, 10, 30, 8, 31)))

    def test_too_late_and_before_creation(self):
        rem = self.rem("daily", at="08:30")
        self.assertFalse(reminders.due(rem, ts(2026, 10, 29, 21, 0)))   # oltre 12 ore dopo
        rem["created"] = ts(2026, 10, 29, 8, 45)
        self.assertFalse(reminders.due(rem, ts(2026, 10, 29, 9, 0)))    # creato dopo le 8:30

    def test_weekly(self):
        rem = self.rem("weekly", at="20:00", days=[0, 3])   # lunedì e giovedì
        now = ts(2026, 10, 30, 12, 0)                        # venerdì
        self.assertEqual(reminders.last_time(rem, now), ts(2026, 10, 29, 20, 0))
        self.assertEqual(reminders.next_time(rem, now), ts(2026, 11, 2, 20, 0))
        self.assertFalse(reminders.valid(self.rem("weekly", days=[])))

    def test_interval(self):
        rem = self.rem("interval", at="09:00", every=10, date="2026-10-20")
        self.assertEqual(reminders.next_time(rem, ts(2026, 10, 25)), ts(2026, 10, 30, 9, 0))
        self.assertIsNone(reminders.last_time(rem, ts(2026, 10, 19)))

    def test_once(self):
        rem = self.rem("once", at="10:00", date="2026-11-05")
        self.assertEqual(reminders.next_time(rem, ts(2026, 11, 1)), ts(2026, 11, 5, 10, 0))
        self.assertTrue(reminders.due(rem, ts(2026, 11, 5, 10, 5)))
        self.assertIsNone(reminders.next_time(rem, ts(2026, 11, 6)))

    def test_before_sensor_end(self):
        rem = self.rem("sensor", at="18:00", before=3)
        end = ts(2026, 11, 10, 7, 0)
        self.assertEqual(reminders.next_time(rem, ts(2026, 11, 1), end), ts(2026, 11, 7, 18, 0))
        self.assertIsNone(reminders.next_time(rem, ts(2026, 11, 1), None))   # sensore ignoto
        cfg = {"sensor_activated": ts(2026, 10, 27, 7, 0)}
        self.assertEqual(reminders.sensor_end(cfg, 14), end)

    def test_snooze_and_done(self):
        rem = self.rem("daily", at="08:30")
        now = ts(2026, 10, 29, 8, 31)
        reminders.fire(rem, now)
        reminders.snooze(rem, now, 15)
        self.assertFalse(reminders.due(rem, now + 14 * 60))
        self.assertTrue(reminders.due(rem, now + 15 * 60))
        self.assertEqual(reminders.next_time(rem, now), now + 15 * 60)
        reminders.done(rem, now + 16 * 60)
        self.assertFalse(reminders.due(rem, now + 20 * 60))
        self.assertTrue(reminders.due(rem, ts(2026, 10, 30, 8, 30)))

    def test_disabled_and_invalid(self):
        rem = self.rem("daily", at="08:30", enabled=False)
        self.assertFalse(reminders.due(rem, ts(2026, 10, 29, 9, 0)))
        for bad in (self.rem("daily", at="25:00"), self.rem("once", date="ieri"),
                    self.rem("interval", every=0, date="2026-10-01"), dict(self.rem("daily"), title=" ")):
            self.assertFalse(reminders.valid(bad))
            self.assertIsNone(reminders.next_time(bad, ts(2026, 10, 29)))


if __name__ == "__main__":
    unittest.main()
