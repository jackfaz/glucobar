import hashlib
import json
import os
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from glucobar import credentials, i18n
from glucobar.librelinkup import (
    LibreError, LibreLinkUp, fetch_safely, parse_measurement,
)

USER_ID = "user-123"


def ts(dt):
    return dt.strftime("%m/%d/%Y %I:%M:%S %p")


def measurement(dt, value, trend=3):
    return {"FactoryTimestamp": ts(dt.astimezone(timezone.utc)),
            "Timestamp": ts(dt.astimezone()),
            "ValueInMgPerDl": value, "Value": value, "TrendArrow": trend}


class FakeLibreView(BaseHTTPRequestHandler):
    """Imita LibreLinkUp: versione minima, reindirizzamento di regione, login, dati."""
    state = {}

    def log_message(self, *args):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        s = self.state
        s["logins"] += 1
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.headers.get("version") < "4.20.0":
            return self.send_json({"status": 920, "data": {"minimumVersion": "4.20.0"}})
        if s["redirect"] and not s["redirected"]:
            s["redirected"] = True
            return self.send_json({"status": 0, "data": {"redirect": True, "region": "de"}})
        if s["terms"]:
            return self.send_json({"status": 4, "data": {"step": {"type": "tou"}}})
        if body["password"] != "segreta":
            return self.send_json({"status": 2, "error": {"message": "notAuthenticated"}})
        self.send_json({"status": 0, "data": {"user": {"id": USER_ID},
                                              "authTicket": {"token": "tok"}}})

    def do_GET(self):
        if self.headers.get("Account-Id") != hashlib.sha256(USER_ID.encode()).hexdigest():
            return self.send_json({"message": "unauthorized"}, 401)
        if self.path == "/llu/connections":
            return self.send_json({"status": 0, "data": [{"patientId": "p1"}]})
        now = datetime.now(timezone.utc) - timedelta(minutes=2)
        history = [measurement(now - timedelta(minutes=5 * i), 120 + i) for i in range(5, 0, -1)]
        self.send_json({"status": 0, "data": {
            "connection": {"glucoseMeasurement": measurement(now, 142, 4)},
            "graphData": history}})


class LibreLinkUpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        i18n.set_language("it")
        cls.server = HTTPServer(("127.0.0.1", 0), FakeLibreView)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.env = mock.patch.dict(os.environ, {
            "LLU_BASE_URL": f"http://127.0.0.1:{cls.server.server_port}"})
        cls.env.start()

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.server.shutdown()

    def setUp(self):
        FakeLibreView.state = {"logins": 0, "redirect": True, "redirected": False,
                               "terms": False}
        self.password = "segreta"
        patcher = mock.patch.object(credentials, "get_password",
                                    side_effect=lambda email: self.password)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cfg = {"email": "a@b.c", "region": "eu", "app_version": "4.16.0"}
        self.saved = []
        self.client = LibreLinkUp(self.cfg, save=lambda cfg: self.saved.append(dict(cfg)))

    def test_fetch_follows_version_and_region_redirects(self):
        current, history = self.client.fetch()
        self.assertEqual(current["mgdl"], 142)
        self.assertEqual(current["trend"], 4)
        self.assertEqual(len(history), 6)
        self.assertEqual(self.cfg["app_version"], "4.20.0")
        self.assertEqual(self.cfg["region"], "de")
        self.assertEqual(FakeLibreView.state["logins"], 3)
        self.assertTrue(self.saved)

    def test_wrong_password(self):
        self.password = "sbagliata"
        current, history, err = fetch_safely(self.client)
        self.assertIsNone(current)
        self.assertEqual(err, "Email o password errate")

    def test_terms_to_accept(self):
        FakeLibreView.state["terms"] = True
        with self.assertRaises(LibreError) as ctx:
            self.client.fetch()
        self.assertIn("termini", str(ctx.exception))

    def test_missing_password(self):
        self.password = None
        with self.assertRaises(LibreError):
            self.client.login()


class ParseTest(unittest.TestCase):
    def test_factory_timestamp_is_utc(self):
        m = parse_measurement({"FactoryTimestamp": "10/26/2026 6:30:00 PM",
                               "Timestamp": "10/26/2026 7:30:00 PM",
                               "ValueInMgPerDl": 133, "TrendArrow": 2})
        expected = datetime(2026, 10, 26, 18, 30, tzinfo=timezone.utc).timestamp()
        self.assertEqual(m["time"], expected)
        self.assertEqual((m["mgdl"], m["trend"]), (133, 2))

    def test_missing_timestamp_means_now(self):
        m = parse_measurement({"Value": 99})
        self.assertAlmostEqual(m["time"], time.time(), delta=5)


if __name__ == "__main__":
    unittest.main()
