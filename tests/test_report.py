import os
import unittest
from unittest import mock

from glucobar import report
from glucobar.config import DEFAULT_CONFIG


class RedactTest(unittest.TestCase):
    def test_hides_personal_data(self):
        home = os.path.expanduser("~")
        text = (f"log in {home}/GlucoBar/glucobar.log\n"
                "primo dato ricevuto: 140 mg/dL, poi 7.8 mmol/L e 7,8 mmol/L\n"
                "login di Mario.Rossi+cgm@example.co.uk fallito")
        out = report.redact(text, {"email": "mario.rossi+cgm@example.co.uk"})
        self.assertNotIn(home, out)
        self.assertIn("%USERPROFILE%", out)
        self.assertNotIn("140", out)
        self.assertNotIn("7.8", out)
        self.assertNotIn("7,8", out)
        self.assertIn("<value> mg/dL", out)
        self.assertNotIn("example", out)
        self.assertIn("<email>", out)

    def test_keeps_useful_numbers(self):
        out = report.redact("barra=(0, 1032, 1920, 1080) build 26200 GlucoBar 0.5.0")
        self.assertEqual(out, "barra=(0, 1032, 1920, 1080) build 26200 GlucoBar 0.5.0")


class ReportTest(unittest.TestCase):
    def test_report_has_no_email_and_is_a_code_block(self):
        cfg = dict(DEFAULT_CONFIG, email="a@b.c")
        with mock.patch("glucobar.credentials.get_password", return_value="x"):
            text = report.build_report(cfg, running=False)
        self.assertTrue(text.startswith("```text") and text.endswith("```"))
        self.assertIn("email and password saved", text)
        self.assertNotIn("a@b.c", text)
        self.assertIn("Shown:", text)


class ThresholdsTest(unittest.TestCase):
    def test_thresholds_are_not_hidden(self):
        cfg = dict(DEFAULT_CONFIG)
        with mock.patch("glucobar.credentials.get_password", return_value=None):
            text = report.build_report(cfg, running=False)
        self.assertIn("low 70, high 180, very high 250", text)


if __name__ == "__main__":
    unittest.main()
