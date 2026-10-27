import json
import os
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock
from urllib.parse import parse_qs, urlparse

from glucobar import credentials, i18n
from glucobar.config import DEFAULT_CONFIG
from glucobar.dexcom import APPLICATION_IDS, NULL_ID, DexcomShare, parse_reading
from glucobar.sources import TREND_ARROWS, fetch_safely, make_client

ACCOUNT_ID = "11111111-2222-3333-4444-555555555555"


def reading(minutes_ago, value, trend="Flat"):
    ms = int((time.time() - minutes_ago * 60) * 1000)
    return {"WT": f"Date({ms})", "ST": f"Date({ms})", "DT": f"Date({ms}+0200)",
            "Value": value, "Trend": trend}


class FakeShare(BaseHTTPRequestHandler):
    """Imita Dexcom Share: account -> sessione -> letture, con gli errori veri."""
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
        url = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length)) if length else None
        if url.path.endswith("General/AuthenticatePublisherAccount"):
            s["logins"] += 1
            if s["locked"]:
                return self.send_json({"Code": "SSO_AuthenticateMaxAttemptsExceeed",
                                       "Message": "Maximum authentication attempts exceeded"},
                                      500)
            if body["password"] != "segreta" or body["applicationId"] != APPLICATION_IDS["ous"]:
                return self.send_json({"Code": "AccountPasswordInvalid",
                                       "Message": "Publisher account password failed"}, 500)
            return self.send_json(ACCOUNT_ID)
        if url.path.endswith("General/LoginPublisherAccountById"):
            if body["accountId"] != ACCOUNT_ID:
                return self.send_json(NULL_ID)
            s["session"] = f"session-{s['logins']}"
            return self.send_json(s["session"])
        if url.path.endswith("Publisher/ReadPublisherLatestGlucoseValues"):
            query = parse_qs(url.query)
            if s["expire_once"]:
                s["expire_once"] = False
                return self.send_json({"Code": "SessionIdNotFound", "Message": "not found"}, 500)
            if query["sessionId"] != [s["session"]]:
                return self.send_json({"Code": "SessionNotValid", "Message": "invalid"}, 500)
            self.send_json(s["readings"])   # dalla più recente, come Dexcom
            return
        self.send_json({"Code": "NotFound"}, 404)


class DexcomTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        i18n.set_language("it")
        cls.server = HTTPServer(("127.0.0.1", 0), FakeShare)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.env = mock.patch.dict(os.environ, {
            "DEXCOM_BASE_URL": f"http://127.0.0.1:{cls.server.server_port}/ShareWebServices/Services"})
        cls.env.start()

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        FakeShare.state = {"logins": 0, "locked": False, "expire_once": False, "session": None,
                           "readings": [reading(2, 142, "FortyFiveUp"), reading(7, 135, 4),
                                        reading(12, 128, "Flat")]}
        self.password = "segreta"
        p = mock.patch.object(credentials, "get_password",
                              side_effect=lambda email, source="libre":
                                  self.password if source == "dexcom" else None)
        p.start()
        self.addCleanup(p.stop)
        self.cfg = {**DEFAULT_CONFIG, "source": "dexcom", "email": "+391234567"}

    def test_fetch(self):
        client = make_client(self.cfg)
        self.assertIsInstance(client, DexcomShare)
        current, history, err = fetch_safely(client)
        self.assertIsNone(err)
        self.assertEqual(current["mgdl"], 142)
        self.assertEqual(TREND_ARROWS[current["trend"]], "↗")
        self.assertEqual([m["mgdl"] for m in history], [128, 135, 142])   # in ordine di tempo
        self.assertEqual(history[1]["trend"], "Flat")                     # numero 4 -> Flat
        self.assertAlmostEqual(current["time"], time.time() - 120, delta=5)
        self.assertIsNone(client.connection)                              # niente giorno sensore

    def test_wrong_password(self):
        self.password = "sbagliata"
        _c, _h, err = fetch_safely(make_client(self.cfg))
        self.assertEqual(err, "Email o password errate")

    def test_missing_password(self):
        self.password = None
        _c, _h, err = fetch_safely(make_client(self.cfg))
        self.assertIn("Password mancante", err)

    def test_too_many_attempts(self):
        FakeShare.state["locked"] = True
        _c, _h, err = fetch_safely(make_client(self.cfg))
        self.assertIn("Troppi tentativi", err)

    def test_expired_session_logs_in_again_once(self):
        client = make_client(self.cfg)
        fetch_safely(client)
        FakeShare.state["expire_once"] = True
        current, _h, err = fetch_safely(client)
        self.assertIsNone(err)
        self.assertEqual(current["mgdl"], 142)
        self.assertEqual(FakeShare.state["logins"], 2)

    def test_no_readings(self):
        FakeShare.state["readings"] = []
        _c, _h, err = fetch_safely(make_client(self.cfg))
        self.assertIn("Nessuna lettura nelle ultime 24 ore", err)

    def test_trial_password_without_saving(self):
        self.password = None
        client = DexcomShare(self.cfg, save=lambda cfg: None, password="segreta")
        current, _h, err = fetch_safely(client)
        self.assertIsNone(err)
        self.assertEqual(current["mgdl"], 142)

    def test_regions(self):
        with mock.patch.dict(os.environ, {"DEXCOM_BASE_URL": ""}):
            for region, host in (("ous", "shareous1.dexcom.com"), ("us", "share2.dexcom.com"),
                                 ("jp", "share.dexcom.jp"), ("zz", "shareous1.dexcom.com")):
                client = DexcomShare({**self.cfg, "dexcom_region": region})
                self.assertIn(host, client.base_url, region)

    def test_parse_reading(self):
        m = parse_reading({"WT": "Date(1691455258000)", "Value": 99, "Trend": "DoubleDown"})
        self.assertEqual((m["mgdl"], m["time"]), (99, 1691455258))
        self.assertEqual(TREND_ARROWS[m["trend"]], "↓↓")


if __name__ == "__main__":
    unittest.main()
