import hashlib
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock
from urllib.parse import parse_qs, urlparse

from glucobar import credentials, i18n
from glucobar.config import DEFAULT_CONFIG
from glucobar.nightscout import Nightscout, normalize_url, parse_entry
from glucobar.sources import TREND_ARROWS, account_ready, fetch_safely, make_client

TOKEN = "readable-0123456789abcdef"
SECRET = "il-mio-api-secret"


def entry(minutes_ago, sgv, direction="Flat"):
    return {"_id": f"id{minutes_ago}", "type": "sgv", "sgv": sgv, "direction": direction,
            "date": int((time.time() - minutes_ago * 60) * 1000)}


class FakeNightscout(BaseHTTPRequestHandler):
    """Imita /api/v1/entries/sgv.json: pubblico, con token o con API_SECRET."""
    state = {}

    def log_message(self, *args):
        pass

    def send(self, body, code=200, kind="application/json"):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        s = self.state
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path != "/api/v1/entries/sgv.json":
            return self.send("<html>non è Nightscout</html>", 404, "text/html")
        s["queries"].append(query)
        token_ok = query.get("token") == [TOKEN]
        secret_ok = self.headers.get("api-secret") == hashlib.sha1(SECRET.encode()).hexdigest()
        if s["auth"] == "token" and not token_ok:
            return self.send({"status": 401, "message": "Unauthorized"}, 401)
        if s["auth"] == "secret" and not secret_ok:
            return self.send({"status": 401, "message": "Unauthorized"}, 401)
        self.send(s["entries"])   # dalla più recente, come Nightscout


class NightscoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        i18n.set_language("it")
        cls.server = HTTPServer(("127.0.0.1", 0), FakeNightscout)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        FakeNightscout.state = {"auth": "public", "queries": [], "entries": [
            entry(1, 151, "FortyFiveUp"), entry(6, 144, None) | {"trend": 4},
            {"type": "mbg", "mbg": 150, "date": entry(8, 0)["date"]},   # glucometro: ignorato
            entry(11, 139, "Flat")]}
        self.token = None
        p = mock.patch.object(credentials, "get_password",
                              side_effect=lambda account, source="libre":
                                  self.token if source == "nightscout" else None)
        p.start()
        self.addCleanup(p.stop)
        self.cfg = {**DEFAULT_CONFIG, "source": "nightscout", "email": self.url + "/"}

    def test_public_site(self):
        client = make_client(self.cfg)
        self.assertIsInstance(client, Nightscout)
        current, history, err = fetch_safely(client)
        self.assertIsNone(err)
        self.assertEqual(current["mgdl"], 151)
        self.assertEqual(TREND_ARROWS[current["trend"]], "↗")
        self.assertEqual([m["mgdl"] for m in history], [139, 144, 151])
        self.assertEqual(history[1]["trend"], "Flat")            # numero 4 -> Flat
        self.assertAlmostEqual(current["time"], time.time() - 60, delta=5)
        query = FakeNightscout.state["queries"][0]
        self.assertNotIn("token", query)
        self.assertIn("find[date][$gte]", query)                 # solo le ultime 24 ore

    def test_token(self):
        FakeNightscout.state["auth"] = "token"
        _c, _h, err = fetch_safely(make_client(self.cfg))
        self.assertIn("chiede un token", err)
        self.token = TOKEN
        current, _h, err = fetch_safely(make_client(self.cfg))
        self.assertIsNone(err)
        self.assertEqual(current["mgdl"], 151)

    def test_api_secret_instead_of_token(self):
        FakeNightscout.state["auth"] = "secret"
        self.token = SECRET
        client = make_client(self.cfg)
        current, _h, err = fetch_safely(client)
        self.assertIsNone(err)
        self.assertTrue(client.use_secret)

    def test_trial_token_without_saving(self):
        FakeNightscout.state["auth"] = "token"
        client = Nightscout(self.cfg, save=lambda cfg: None, password=TOKEN)
        current, _h, err = fetch_safely(client)
        self.assertIsNone(err)

    def test_wrong_address(self):
        # un'altra pagina dello stesso server: 404 con una pagina HTML
        _c, _h, err = fetch_safely(make_client({**self.cfg, "email": self.url + "/sito"}))
        self.assertIn("non risponde come un sito Nightscout", err)
        # risponde, ma non con un elenco di letture
        FakeNightscout.state["entries"] = {"status": "ok"}
        _c, _h, err = fetch_safely(make_client(self.cfg))
        self.assertIn("non risponde come un sito Nightscout", err)

    def test_no_readings(self):
        FakeNightscout.state["entries"] = []
        _c, _h, err = fetch_safely(make_client(self.cfg))
        self.assertIn("Nessuna lettura nelle ultime 24 ore", err)

    def test_account_ready_without_token(self):
        self.assertTrue(account_ready(self.cfg))                  # sito pubblico: basta l'indirizzo
        self.assertFalse(account_ready({**self.cfg, "email": ""}))
        self.assertFalse(account_ready({**self.cfg, "source": "libre"}))   # Libre: serve la password

    def test_normalize_url(self):
        self.assertEqual(normalize_url(" mionome.herokuapp.com/ "), "https://mionome.herokuapp.com")
        self.assertEqual(normalize_url("http://192.168.1.5:1337"), "http://192.168.1.5:1337")

    def test_parse_entry(self):
        m = parse_entry({"sgv": 99, "date": 1691455258000, "direction": "DoubleDown"})
        self.assertEqual((m["mgdl"], m["time"]), (99, 1691455258))
        self.assertEqual(TREND_ARROWS[m["trend"]], "↓↓")


if __name__ == "__main__":
    unittest.main()
