"""Secondo sensore (es. Libre e Dexcom insieme): impostazioni separate, lettura insieme al
primo, nome di ciascuno."""

import os
import threading
import unittest
from http.server import HTTPServer
from unittest import mock

from glucobar import config, credentials, i18n, sources
from glucobar.config import DEFAULT_CONFIG
from tests.test_dexcom import FakeShare, reading
from tests.test_librelinkup import FakeLibreView


class SecondCfgTest(unittest.TestCase):
    def test_own_settings(self):
        cfg = dict(DEFAULT_CONFIG, source="libre", email="anna@x.it", region="eu",
                   patient_id="p1", people_shown=["p2"], second_source="dexcom",
                   second={"email": "anna_dex", "dexcom_region": "us", "junk": 1})
        sub = sources.second_cfg(cfg)
        self.assertEqual((sub["source"], sub["email"], sub["dexcom_region"]),
                         ("dexcom", "anna_dex", "us"))
        self.assertEqual((sub["patient_id"], sub["people_shown"]), (None, []))
        self.assertNotIn("junk", sub)

    def test_no_client_when_same_type_or_missing(self):
        base = dict(DEFAULT_CONFIG, source="libre", email="a")
        self.assertIsNone(sources.make_second_client(dict(base)))
        self.assertIsNone(sources.make_second_client(
            dict(base, second_source="libre", second={"email": "b"})))
        self.assertIsNone(sources.make_second_client(dict(base, second_source="dexcom")))
        client = sources.make_second_client(
            dict(base, second_source="dexcom", second={"email": "b"}))
        self.assertEqual(type(client).__name__, "DexcomShare")

    def test_client_saves_into_second(self):
        """Il client di LibreLinkUp salva regione e versione dell'app: nelle impostazioni
        del secondo sensore, non in quelle del primo."""
        cfg = dict(DEFAULT_CONFIG, source="dexcom", email="dex", region="eu",
                   second_source="libre", second={"email": "lib@x.it", "region": "eu"})
        with mock.patch.object(config, "save_config") as save:
            client = sources.make_second_client(cfg)
            client.cfg["region"] = "us"
            client.save(client.cfg)
        self.assertEqual(cfg["region"], "eu")                 # il primo non cambia
        self.assertEqual(cfg["second"]["region"], "us")
        self.assertEqual(cfg["second"]["email"], "lib@x.it")
        save.assert_called_once_with(cfg)


class BothSensorsTest(unittest.TestCase):
    """GlucoBar vero (senza finestre): LibreLinkUp e Dexcom finti, letti insieme."""

    @classmethod
    def setUpClass(cls):
        cls.servers = []
        for handler in (FakeLibreView, FakeShare):
            server = HTTPServer(("127.0.0.1", 0), handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            cls.servers.append(server)
        libre, dexcom = cls.servers
        cls.env = mock.patch.dict(os.environ, {
            "LLU_BASE_URL": f"http://127.0.0.1:{libre.server_port}",
            "DEXCOM_BASE_URL": f"http://127.0.0.1:{dexcom.server_port}"
                               "/ShareWebServices/Services"})
        cls.env.start()

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        for server in cls.servers:
            server.shutdown()
            server.server_close()

    def setUp(self):
        FakeLibreView.state = {"logins": 0, "redirect": False, "redirected": False,
                               "terms": False}
        FakeShare.state = {"logins": 0, "locked": False, "expire_once": False, "session": None,
                           "readings": [reading(2, 131, "FortyFiveUp"), reading(7, 125, 4)]}
        passwords = {"libre": "segreta", "dexcom": "segreta"}
        p = mock.patch.object(credentials, "get_password",
                              side_effect=lambda email, source="libre": passwords.get(source))
        p.start()
        self.addCleanup(p.stop)
        i18n.set_language("en")

    def test_fetch_both(self):
        from glucobar.controller import Controller
        cfg = dict(DEFAULT_CONFIG, source="libre", email="a@b.c", app_version="4.20.0",
                   second_source="dexcom", second={"email": "anna", "dexcom_region": "ous"})

        class Stub:
            on_second_data = Controller.on_second_data
            person_label = Controller.person_label
            person_key = Controller.person_key
            sensor_name = Controller.sensor_name

        ctl = Stub()
        ctl.cfg, ctl.second = cfg, None
        ctl.client = sources.make_client(cfg)
        ctl.second_client = sources.make_second_client(cfg)
        with mock.patch.object(config, "save_config"):
            first = sources.fetch_safely(ctl.client)
            ctl.on_second_data(*sources.fetch_safely(ctl.second_client))
        self.assertIsNone(first[2])
        self.assertEqual(ctl.second["current"]["mgdl"], 131)
        self.assertEqual(len(ctl.second["history"]), 2)
        # due sensori della stessa persona: si chiamano col nome del sensore
        self.assertEqual((ctl.person_label(), ctl.second["label"]), ("Libre", "Dexcom"))
        cfg["nicknames"] = {"second": "G7"}
        self.assertEqual(ctl.person_label("second"), "G7")


if __name__ == "__main__":
    unittest.main()
