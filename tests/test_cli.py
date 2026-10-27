import contextlib
import io
import json
import os
import tempfile
import time
import unittest
from unittest import mock

from glucobar import cli, config, credentials, i18n, tui
from glucobar.config import DEFAULT_CONFIG, load_config
from glucobar.librelinkup import LibreError
from tests.test_tui import FakeTerm


class IsolatedConfig(unittest.TestCase):
    """Impostazioni e password in una cartella temporanea."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.passwords = {}
        patches = [
            mock.patch.object(config, "CONFIG_DIR", tmp.name),
            mock.patch.object(config, "CONFIG_PATH", os.path.join(tmp.name, "config.json")),
            mock.patch.object(cli, "CONFIG_PATH", os.path.join(tmp.name, "config.json")),
            mock.patch.object(config, "LOG_PATH", os.path.join(tmp.name, "log.txt")),
            mock.patch.object(config, "LEGACY_CONFIG_PATH", os.path.join(tmp.name, "none.json")),
            # password per (sorgente, account), come le voci del Gestione credenziali
            mock.patch.object(credentials, "set_password",
                              side_effect=lambda e, p, s="libre":
                                  self.passwords.update({(s, e): p})),
            mock.patch.object(credentials, "get_password",
                              side_effect=lambda e, s="libre": self.passwords.get((s, e))),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        i18n.set_language("it")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class SetGetTest(IsolatedConfig):
    def test_parse_assignments(self):
        cfg = dict(DEFAULT_CONFIG)
        self.assertEqual(cli.parse_assignments(["unit=mmol/l", "low=80", "elements=desktop,tray",
                                                "desktop_hours=6", "taskbar_bg=auto"], cfg),
                         {"unit": "mmol/L", "low": 80, "elements": ["tray", "desktop"],
                          "desktop_hours": 6, "taskbar_bg": None})
        for wrong in (["colore=rosso"], ["low=abc"], ["low=10"], ["elements=orologio"],
                      ["low=190"], ["unit"]):
            with self.assertRaises(ValueError, msg=wrong):
                cli.parse_assignments(wrong, cfg)

    def test_set_then_get(self):
        code, out, _ = self.run_cli("set", "unit=mmol/L", "high=200", "language=de")
        self.assertEqual(code, 0)
        self.assertIn("unit = mmol/L", out)
        cfg = load_config()
        self.assertEqual((cfg["unit"], cfg["high"], cfg["language"]), ("mmol/L", 200, "de"))
        code, out, _ = self.run_cli("get", "high", "elements")
        self.assertEqual(out.split("\n")[:2],
                         ["high = 200", "elements = " + ",".join(DEFAULT_CONFIG["elements"])])

    def test_set_rejects_and_changes_nothing(self):
        code, _out, err = self.run_cli("set", "unit=mmol/L", "low=999")
        self.assertEqual(code, 2)
        self.assertIn("low", err)
        self.assertEqual(load_config()["unit"], "mg/dL")


class InstallerChoicesTest(IsolatedConfig):
    """GlucoBar.exe --set-... come lo chiama l'installer alla fine."""

    def test_set_source(self):
        from glucobar import app
        cli.main(["set", "language=it"])
        cfg = load_config()
        cfg["email"] = "a@b.c"
        config.save_config(cfg)
        self.assertEqual(app.main(["--set-elements", "desktop", "--set-language", "de",
                                   "--set-source", "libre"]), 0)
        cfg = load_config()
        self.assertEqual((cfg["elements"], cfg["language"], cfg["source"], cfg["email"]),
                         (["desktop"], "de", "libre", "a@b.c"))   # stesso sensore: account tenuto
        app.main(["--set-source", "dexcom"])
        cfg = load_config()
        self.assertEqual((cfg["source"], cfg["email"]), ("dexcom", ""))


class FakeClient:
    """Al posto di LibreLinkUp: accetta solo la password "giusta"."""

    def __init__(self, cfg, save=None, password=None):
        self.cfg, self.password = cfg, password

    def fetch(self):
        if self.password != "giusta":
            raise LibreError("Email o password errate")
        self.cfg["region"] = "de"
        return {"mgdl": 133, "trend": 2, "time": time.time()}, []


class WizardTest(IsolatedConfig):
    def test_full_wizard(self):
        term = FakeTerm(
            ["enter"]                                    # lingua: italiano (già scelta)
            + ["down", "down", "space", "enter"]         # aggiunge il terzo elemento
            + ["down", "enter"]                          # mmol/L
            + ["down", "enter"]                          # range personalizzato
            + list("80") + ["enter"]                     # soglia bassa (vuota -> cancello)
            + ["enter"]                                  # soglia alta: default
            + ["enter"]                                  # sensore: FreeStyle Libre
            + list("a@b.c") + ["enter"] + list("sbagliata") + ["enter"]
            + ["enter"]                                  # riprova
            + ["enter"] + list("giusta") + ["enter"])    # stessa email, password giusta
        cfg = load_config()
        cfg["low"] = 70
        with mock.patch.object(cli.autostart, "gui_exe", return_value=None):
            cli.wizard(term, cfg, client_class=FakeClient)
        saved = load_config()
        # Windows: finestrella (dopo barra e icona); Mac: pannello (dopo barra dei menu e finestrella)
        self.assertEqual(saved["elements"],
                         config.normalize_elements(DEFAULT_CONFIG["elements"] + [config.ELEMENTS[2]]))
        self.assertEqual(saved["unit"], "mmol/L")
        self.assertEqual((saved["low"], saved["high"]), (80, 180))
        self.assertEqual(saved["email"], "a@b.c")
        self.assertEqual(saved["region"], "de")          # suggerito dal server
        self.assertEqual(saved["source"], "libre")
        self.assertEqual(self.passwords, {("libre", "a@b.c"): "giusta"})
        screen = term.out.getvalue()
        self.assertIn("Connessione non riuscita: Email o password errate", screen)
        self.assertIn("Connesso: 7.4 ↘ mmol/L", screen)
        self.assertNotIn("giusta", screen)               # la password non si vede mai
        self.assertNotIn("sbagliata", screen)

    def test_dexcom_wizard(self):
        term = FakeTerm(
            ["enter"]                                    # lingua
            + ["enter"]                                  # cosa mostrare: come prima
            + ["enter"]                                  # mg/dL
            + ["enter"]                                  # range standard
            + ["down", "enter"]                          # sensore: Dexcom
            + ["down", "enter"]                          # regione: Stati Uniti
            + list("+391234567") + ["enter"]             # telefono: niente @
            + list("giusta") + ["enter"])
        cfg = load_config()
        cfg["email"] = "vecchio@libre.it"
        with mock.patch.object(cli.autostart, "gui_exe", return_value=None):
            cli.wizard(term, cfg, client_class=FakeClient)
        saved = load_config()
        self.assertEqual((saved["source"], saved["dexcom_region"]), ("dexcom", "us"))
        self.assertEqual(saved["email"], "+391234567")
        self.assertEqual(self.passwords, {("dexcom", "+391234567"): "giusta"})
        screen = term.out.getvalue()
        self.assertIn("Account Dexcom", screen)
        self.assertNotIn("vecchio@libre.it", screen)     # account Libre non riproposto

    def test_nightscout_wizard(self):
        term = FakeTerm(
            ["enter", "enter", "enter", "enter"]         # lingua, elementi, unità, range
            + ["down", "down", "enter"]                  # sensore: Nightscout
            + list("mionome") + ["enter"]                # niente punto: non è un indirizzo
            + list(".herokuapp.com/") + ["enter"]
            + list("giusta") + ["enter"])                # token
        with mock.patch.object(cli.autostart, "gui_exe", return_value=None):
            cli.wizard(term, load_config(), client_class=FakeClient)
        saved = load_config()
        self.assertEqual((saved["source"], saved["email"]),
                         ("nightscout", "https://mionome.herokuapp.com"))
        self.assertEqual(self.passwords, {("nightscout", "https://mionome.herokuapp.com"): "giusta"})
        screen = term.out.getvalue()
        self.assertIn("Sito Nightscout", screen)
        self.assertIn("Scrivi l'indirizzo del sito", screen)
        self.assertNotIn("giusta", screen)

    def test_set_source(self):
        code, out, _ = self.run_cli("set", "source=dexcom", "dexcom_region=jp")
        self.assertEqual(code, 0)
        cfg = load_config()
        self.assertEqual((cfg["source"], cfg["dexcom_region"]), ("dexcom", "jp"))
        code, _out, _err = self.run_cli("set", "source=medtronic")
        self.assertEqual(code, 2)

    def test_escape_saves_nothing(self):
        term = FakeTerm(["enter", "esc"])
        with self.assertRaises(tui.Cancelled):
            cli.wizard(term, load_config(), client_class=FakeClient)
        self.assertFalse(os.path.exists(config.CONFIG_PATH))


if __name__ == "__main__":
    unittest.main()
