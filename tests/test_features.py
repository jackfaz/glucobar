"""Temi, avvisi, sensore, sostituzione, nuove versioni, soglie dal menu."""

import time
import unittest

from glucobar import alerts, sensor, support, theme, updates
from glucobar.config import DEFAULT_CONFIG
from glucobar.ui_common import parse_range

DAY = 86400


def reading(mgdl, minutes_ago=0, now=None):
    return {"mgdl": mgdl, "trend": "Flat", "time": (now or time.time()) - minutes_ago * 60}


class ThemeTest(unittest.TestCase):
    def test_palettes(self):
        cfg = dict(DEFAULT_CONFIG, theme="dark")
        dark = theme.palette(cfg)
        self.assertFalse(dark.light)
        self.assertEqual([dark.value(cfg, v) for v in (60, 120, 200, 300)],
                         [dark.low, dark.in_range, dark.high, dark.very_high])
        light = theme.palette(dict(cfg, theme="light"))
        self.assertTrue(light.light)
        self.assertNotEqual(light.bg, dark.bg)
        blind = theme.palette(dict(cfg, palette="colorblind"))
        self.assertNotEqual(blind.in_range, dark.in_range)
        # sopra una barra chiara contano i colori della barra, non il tema scelto
        self.assertTrue(theme.palette(cfg, light=True).light)

    def test_custom_colors(self):
        cfg = dict(DEFAULT_CONFIG, theme="dark", color_in_range="#B066FF", color_low="#0000ff",
                   color_high="rosso")
        pal = theme.palette(cfg)
        self.assertEqual(pal.value(cfg, 120), "#b066ff")
        self.assertEqual(pal.value(cfg, 60), "#0000ff")
        standard = theme.palette(dict(DEFAULT_CONFIG, theme="dark"))
        self.assertEqual(pal.value(cfg, 200), standard.high)        # colore non valido: ignorato
        self.assertEqual(pal.value(cfg, 300), standard.very_high)
        self.assertNotEqual(pal.band, standard.band)                # la fascia segue il colore
        self.assertEqual(theme.mix("#ffffff", "#000000", 0.5), "#808080")
        # vale anche sopra la barra chiara
        self.assertEqual(theme.palette(cfg, light=True).value(cfg, 120), "#b066ff")

    def test_interface_colors_per_theme(self):
        cfg = dict(DEFAULT_CONFIG, theme="dark", color_stale="#777777",
                   ui_colors={"dark": {"bg": "#000000", "band": "#112233", "pippo": "#ffffff"},
                              "light": {"bg": "#fafafa"}})
        dark = theme.palette(cfg)
        self.assertEqual((dark.bg, dark.band, dark.stale), ("#000000", "#112233", "#777777"))
        self.assertFalse(hasattr(dark, "pippo"))
        self.assertEqual(theme.palette(dict(cfg, theme="light")).bg, "#fafafa")
        cfg["color_in_range"] = "#b066ff"   # la fascia scelta a mano non segue il colore
        self.assertEqual(theme.palette(cfg).band, "#112233")

    def test_unknown_palette_falls_back(self):
        cfg = dict(DEFAULT_CONFIG, theme="dark", palette="rainbow")
        self.assertEqual(theme.palette(cfg).in_range,
                         theme.palette(dict(cfg, palette="standard")).in_range)


class AlertTest(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(DEFAULT_CONFIG, alert_low=True, alert_high=True, alert_stale=True)
        self.watch = alerts.AlertWatch()

    def test_once_per_episode(self):
        self.assertEqual(self.watch.check(self.cfg, reading(65)), ["low"])
        self.assertEqual(self.watch.check(self.cfg, reading(60)), [])
        self.assertEqual(self.watch.check(self.cfg, reading(110)), [])
        self.assertEqual(self.watch.check(self.cfg, reading(64)), ["low"])
        self.assertEqual(self.watch.check(self.cfg, reading(280)), ["high"])

    def test_stale_and_off(self):
        self.assertEqual(self.watch.check(self.cfg, reading(65, minutes_ago=20)), ["stale"])
        self.cfg["alert_low"] = False
        self.assertEqual(alerts.AlertWatch().check(self.cfg, reading(65)), [])
        self.assertEqual(alerts.AlertWatch().check(self.cfg, None), [])

    def test_enabling_during_episode_alerts_now(self):
        self.cfg["alert_low"] = False
        self.assertEqual(self.watch.check(self.cfg, reading(65)), [])
        self.cfg["alert_low"] = True
        self.assertEqual(self.watch.check(self.cfg, reading(65)), ["low"])

    def test_trend_estimate_going_low(self):
        now = time.time()
        falling = [reading(150 - 2 * m, minutes_ago=30 - m, now=now) for m in range(0, 31, 5)]
        current = falling[-1]                                   # 90, -2 al minuto: 70 tra 10 min
        cfg = dict(self.cfg, alert_soon=True)
        self.assertAlmostEqual(alerts.soon_minutes(cfg, falling, current, now), 10)
        self.assertIn("soon", alerts.AlertWatch().check(cfg, current, now, falling))
        self.assertNotIn("soon", alerts.AlertWatch().check(dict(cfg, alert_soon=False),
                                                            current, now, falling))
        flat = [reading(120, minutes_ago=30 - m, now=now) for m in range(0, 31, 5)]
        self.assertEqual(alerts.AlertWatch().check(cfg, flat[-1], now, flat), [])
        # già sotto la soglia: c'è l'avviso "basso", non quello della stima
        low = [reading(80 - 2 * m, minutes_ago=30 - m, now=now) for m in range(0, 31, 5)]
        self.assertEqual(alerts.AlertWatch().check(cfg, low[-1], now, low), ["low"])


def connection(sn, activated):
    return {"sensor": {"sn": sn, "a": activated, "pt": 4}}


class SensorTest(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(DEFAULT_CONFIG, sensor_notified=[])
        self.watch = sensor.SensorWatch()
        self.start = 1_800_000_000

    def check(self, conn, now, minutes_ago=1, error=None):
        return self.watch.check(self.cfg, conn, reading(120, minutes_ago, now), error, now)

    def test_reminders_before_the_end(self):
        conn = connection("A1", self.start)
        events, dirty = self.check(conn, self.start + 2 * DAY)
        self.assertEqual((events, dirty), ([], True))   # sensore nuovo da ricordare
        self.assertEqual(self.check(conn, self.start + 3 * DAY), ([], False))
        events, _ = self.check(conn, self.start + 13.5 * DAY)
        self.assertEqual([e[0] for e in events], ["ending"])
        self.assertAlmostEqual(events[0][1]["hours"], 12)
        self.assertEqual(self.check(conn, self.start + 13.6 * DAY)[0], [])
        events, _ = self.check(conn, self.start + 13.95 * DAY)
        self.assertEqual([e[0] for e in events], ["ending"])
        self.assertEqual(self.check(conn, self.start + 13.97 * DAY)[0], [])

    def test_plus_sensor_lasts_15_days(self):
        self.cfg["sensor_life_days"] = 15
        conn = connection("A1", self.start)
        self.check(conn, self.start)
        self.assertEqual(self.check(conn, self.start + 13.5 * DAY)[0], [])

    def test_stopped_early(self):
        conn = connection("A1", self.start)
        self.check(conn, self.start + 3 * DAY)
        # un'ora senza dati ma con un errore di rete: non è il sensore
        self.assertEqual(self.check(conn, self.start + 4 * DAY, 70, error="offline")[0], [])
        events, _ = self.check(conn, self.start + 4 * DAY, 70)
        self.assertEqual(events, [("stopped", {"sn": "A1"})])
        self.assertEqual(self.check(conn, self.start + 4 * DAY, 90)[0], [])

    def test_replaced_early(self):
        self.check(connection("A1", self.start), self.start + DAY)
        events, dirty = self.check(connection("B2", self.start + 6 * DAY), self.start + 6.1 * DAY)
        self.assertEqual(events, [("replaced_early", {"sn": "A1", "days": 6})])
        self.assertTrue(dirty)
        self.assertEqual(self.cfg["sensor_sn"], "B2")
        # cambiato alla fine: niente avviso
        events, _ = self.check(connection("C3", self.start + 20 * DAY), self.start + 20 * DAY)
        self.assertEqual(events, [])

    def test_no_sensor_data(self):
        self.assertEqual(self.watch.check(self.cfg, {}, None, None), ([], False))
        self.assertIsNone(sensor.info({"sensor": {"sn": "A1", "a": 0}}))


class SupportTest(unittest.TestCase):
    def test_urls_by_country(self):
        self.assertIn("/it-it/", support.replacement_url("libre", ("it", "IT")))
        self.assertIn("/ch-it/", support.replacement_url("libre", ("it", "CH")))
        self.assertIn("/ch-de/", support.replacement_url("libre", ("de", "CH")))
        self.assertEqual(support.replacement_url("libre", ("ja", "JP")), support.LIBRE_FALLBACK)
        self.assertIn("/de-de/", support.replacement_url("dexcom", ("de", "DE")))
        self.assertEqual(support.replacement_url("dexcom", ("it", "IT")),
                         support.DEXCOM_FALLBACK)
        for url in list(support.LIBRE_FORMS.values()) + list(support.DEXCOM_PAGES.values()):
            self.assertTrue(url.startswith("https://"), url)


class UpdateTest(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(updates.parse_version("v0.10.2"), (0, 10, 2))
        self.assertTrue(updates.is_newer("0.10.0", "0.9.3"))
        self.assertFalse(updates.is_newer("v0.9.0", "0.9.0"))
        self.assertFalse(updates.is_newer("nightly", "0.9.0"))


class InstallUpdateTest(unittest.TestCase):
    """Download dell'installer da un server finto, come lo farebbe GlucoBar."""

    def setUp(self):
        import hashlib
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        self.body = b"MZ" + b"x" * 5000

        body = self.body

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_port}/GlucoBar-Setup-9.9.9.exe"
        self.sha = hashlib.sha256(body).hexdigest()

    def test_parse_release_prefers_versioned_installer(self):
        data = {"tag_name": "v9.9.9", "html_url": "https://example.org/r", "assets": [
            {"name": "GlucoBar-Setup.exe", "browser_download_url": "fixed"},
            {"name": "GlucoBar-Setup-9.9.9.exe", "browser_download_url": self.url,
             "digest": "sha256:" + self.sha.upper()},
            {"name": "GlucoBar-mac.dmg", "browser_download_url": "dmg"}]}
        release = updates.parse_release(data)
        self.assertEqual((release["version"], release["installer"], release["sha256"]),
                         ("9.9.9", self.url, self.sha))
        self.assertIsNone(updates.parse_release({"tag_name": "v1.0.0"})["installer"])

    def test_download_checks_the_fingerprint(self):
        import tempfile
        folder = tempfile.mkdtemp()
        release = {"version": "9.9.9", "installer": self.url, "sha256": self.sha}
        path = updates.download(release, folder)
        with open(path, "rb") as f:
            self.assertEqual(f.read(), self.body)
        with self.assertRaises(ValueError):
            updates.download(dict(release, sha256="0" * 64), folder)

    def test_installer_scope(self):
        import os
        import tempfile
        from unittest import mock
        local = tempfile.mkdtemp()
        with mock.patch.dict(os.environ, {"LOCALAPPDATA": local}):
            self.assertIn("/CURRENTUSER", updates.installer_args(
                os.path.join(local, "Programs", "GlucoBar", "GlucoBar.exe")))
            self.assertIn("/ALLUSERS", updates.installer_args(
                os.path.join(tempfile.gettempdir(), "Program Files", "GlucoBar.exe")))


class RangeTest(unittest.TestCase):
    def test_parse(self):
        cfg = dict(DEFAULT_CONFIG)
        self.assertEqual(parse_range(cfg, {"low": "75", "high": "160", "very_high": "220"}),
                         {"low": 75, "high": 160, "very_high": 220})
        cfg["unit"] = "mmol/L"
        self.assertEqual(parse_range(cfg, {"low": "3,9", "high": "10", "very_high": "13.9"}),
                         {"low": 70, "high": 180, "very_high": 250})
        for wrong in ({"low": "190", "high": "160", "very_high": "220"},
                      {"low": "x", "high": "10", "very_high": "13"},
                      {"low": "1", "high": "10", "very_high": "13"}):
            with self.assertRaises(ValueError):
                parse_range(cfg, wrong)



class TaskbarEdgeTest(unittest.TestCase):
    """Su quale bordo è la barra e quanta ne resta in vista (nascosta automaticamente)."""

    def test_edges(self):
        from glucobar.taskbar import on_screen, taskbar_edge
        screen = (0, 0, 1024, 768)
        self.assertEqual(taskbar_edge((0, 728, 1024, 768), screen), "bottom")
        self.assertEqual(taskbar_edge((0, 0, 1024, 40), screen), "top")
        self.assertEqual(taskbar_edge((0, 0, 62, 768), screen), "left")
        self.assertEqual(taskbar_edge((962, 0, 1024, 768), screen), "right")
        # nascoste: quasi tutte fuori dallo schermo, ma sempre sullo stesso bordo
        self.assertEqual(taskbar_edge((0, 766, 1024, 806), screen), "bottom")
        self.assertEqual(taskbar_edge((0, -38, 1024, 2), screen), "top")
        self.assertEqual(taskbar_edge((-60, 0, 2, 768), screen), "left")
        self.assertEqual(on_screen((0, 728, 1024, 768), screen), 40)
        self.assertEqual(on_screen((0, 766, 1024, 806), screen), 2)
        self.assertEqual(on_screen((-60, 0, 2, 768), screen), 2)
        self.assertEqual(on_screen((0, 900, 1024, 940), screen), 0)


if __name__ == "__main__":
    unittest.main()
