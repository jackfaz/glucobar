"""Gira anche su Windows in CI: lì usa il vero Gestione credenziali."""
import os
import tempfile
import unittest
from unittest import mock

from glucobar import credentials


class CredentialsTest(unittest.TestCase):
    def setUp(self):
        # voce di prova, per non toccare la password vera
        patches = [mock.patch.object(credentials, "TARGET", "GlucoBar:Test-unittest")]
        if hasattr(credentials, "_PATH"):
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            patches.append(mock.patch.object(credentials, "_PATH",
                                             os.path.join(tmp.name, "credentials.json")))
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(credentials.delete_password)

    def test_save_read_delete(self):
        credentials.set_password("a@b.c", "segreta è")
        self.assertEqual(credentials.get_password("A@B.C"), "segreta è")
        self.assertIsNone(credentials.get_password("altro@b.c"))
        self.assertTrue(credentials.delete_password())
        self.assertIsNone(credentials.get_password("a@b.c"))
        self.assertFalse(credentials.delete_password())


if __name__ == "__main__":
    unittest.main()
