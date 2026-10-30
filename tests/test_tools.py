import hashlib
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools"))
import live_check  # noqa: E402
import release_notes  # noqa: E402
import virustotal  # noqa: E402

import glucobar  # noqa: E402


class ToolsTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".exe")
        with os.fdopen(fd, "wb") as f:
            f.write(b"MZ installer")
        self.digest = hashlib.sha256(b"MZ installer").hexdigest()

    def tearDown(self):
        os.remove(self.path)

    def test_report_url_uses_sha256(self):
        self.assertEqual(virustotal.report_url(self.path),
                         f"https://www.virustotal.com/gui/file/{self.digest}")

    def test_multipart_contains_file(self):
        body, content_type = virustotal.multipart(self.path)
        boundary = content_type.split("boundary=")[1]
        self.assertIn(b"MZ installer", body)
        self.assertTrue(body.endswith(f"--{boundary}--\r\n".encode()))
        self.assertIn(os.path.basename(self.path).encode(), body)

    def test_upload_without_key_does_nothing(self):
        with mock.patch.dict(os.environ, {"VT_API_KEY": ""}), \
                mock.patch.object(sys, "argv", ["virustotal.py", self.path]), \
                mock.patch("urllib.request.urlopen") as urlopen:
            with self.assertRaises(SystemExit) as done:
                exec(compile(open(virustotal.__file__, encoding="utf-8").read(),
                             virustotal.__file__, "exec"), {"__name__": "__main__"})
        self.assertEqual(done.exception.code, 0)
        urlopen.assert_not_called()

    def test_request_retries_when_busy(self):
        import io
        import urllib.error
        busy = urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)
        ok = mock.MagicMock()
        ok.__enter__.return_value = io.BytesIO(b'{"data": 1}')
        with mock.patch("urllib.request.urlopen", side_effect=[busy, ok]), \
                mock.patch("time.sleep") as sleep:
            self.assertEqual(virustotal.request("https://x/u", "key"), {"data": 1})
        sleep.assert_called_once()
        denied = urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=denied), \
                self.assertRaises(urllib.error.HTTPError):
            virustotal.request("https://x/u", "key")

    def test_wait_reports_flagging_engines(self):
        analysis = {"data": {"attributes": {
            "status": "completed",
            "stats": {"malicious": 1, "suspicious": 0, "undetected": 70},
            "results": {"Microsoft": {"category": "malicious",
                                      "result": "Trojan:Win32/Wacatac.B!ml"},
                        "ESET-NOD32": {"category": "undetected", "result": None}}}}}
        with mock.patch.object(virustotal, "request", return_value=analysis):
            lines = virustotal.summary(*virustotal.wait("id", "key"))
        self.assertEqual(lines, ["1 malicious, 0 suspicious, 70 undetected",
                                 "Microsoft: Trojan:Win32/Wacatac.B!ml"])

    def test_release_notes(self):
        version = glucobar.__version__
        plain = release_notes.notes(version)
        self.assertNotIn("SHA-256 of", plain)
        self.assertNotIn("[VirusTotal]", plain)
        full = release_notes.notes(version, self.path, "https://vt.example/x")
        self.assertIn(self.digest, full)
        self.assertIn("[VirusTotal](https://vt.example/x)", full)
        self.assertNotIn("[VirusTotal]", release_notes.notes(version, self.path))
        self.assertNotIn("Pre-release", full)
        self.assertIn("**Pre-release:**", release_notes.notes(version, self.path, "u", True))



class LiveCheckTest(unittest.TestCase):
    """Il controllo quotidiano, contro il LibreLinkUp finto dei test."""

    def test_accounts_from_secrets(self):
        self.assertEqual(live_check.accounts({}), [])
        found = live_check.accounts({"LIBRE_EMAIL": "a@b.c", "LIBRE_PASSWORD": "x",
                                     "DEXCOM_USER": "u", "NIGHTSCOUT_URL": "https://ns.example"})
        self.assertEqual([name for name, _cfg, _pw in found], ["LibreLinkUp", "Nightscout"])

    def test_check_never_prints_values_or_email(self):
        from http.server import HTTPServer
        import threading
        from test_librelinkup import FakeLibreView
        FakeLibreView.state = {"logins": 0, "redirect": False, "redirected": False,
                               "terms": False}
        server = HTTPServer(("127.0.0.1", 0), FakeLibreView)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        with mock.patch.dict(os.environ, {"LLU_BASE_URL": f"http://127.0.0.1:{server.server_port}"}):
            ok, text = live_check.check("LibreLinkUp", {"source": "libre", "email": "a@b.c"},
                                        "segreta")
            self.assertTrue(ok, text)
            self.assertIn("ok, ultima lettura 2 min fa", text)
            self.assertIn("chiede la versione 4.20.0", text)
            self.assertNotIn("142", text)
            ok, text = live_check.check("LibreLinkUp", {"source": "libre", "email": "a@b.c"},
                                        "sbagliata")
            self.assertFalse(ok)
            self.assertNotIn("a@b.c", text)


if __name__ == "__main__":
    unittest.main()
