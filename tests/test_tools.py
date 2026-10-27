import hashlib
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools"))
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

    def test_release_notes(self):
        version = glucobar.__version__
        plain = release_notes.notes(version)
        self.assertNotIn("SHA-256", plain)
        full = release_notes.notes(version, self.path, "https://vt.example/x")
        self.assertIn(self.digest, full)
        self.assertIn("[VirusTotal](https://vt.example/x)", full)
        self.assertNotIn("VirusTotal", release_notes.notes(version, self.path))


if __name__ == "__main__":
    unittest.main()
