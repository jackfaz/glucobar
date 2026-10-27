"""Gira anche su Windows in CI: lì usa il vero Gestione credenziali."""
import tempfile
import unittest
from unittest import mock

from glucobar import credentials


class CredentialsTest(unittest.TestCase):
    def setUp(self):
        # voci di prova, per non toccare le password vere
        patches = [mock.patch.dict(credentials.TARGETS,
                                   {"libre": "GlucoBar:Test-unittest-libre",
                                    "dexcom": "GlucoBar:Test-unittest-dexcom"})]
        if hasattr(credentials, "_DIR"):
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            patches.append(mock.patch.object(credentials, "_DIR", tmp.name))
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

    def test_one_password_per_source(self):
        credentials.set_password("a@b.c", "libre", "libre")
        credentials.set_password("a@b.c", "dexcom", "dexcom")
        self.assertEqual(credentials.get_password("a@b.c", "libre"), "libre")
        self.assertEqual(credentials.get_password("a@b.c", "dexcom"), "dexcom")
        self.assertTrue(credentials.delete_password("dexcom"))
        self.assertIsNone(credentials.get_password("a@b.c", "dexcom"))
        self.assertEqual(credentials.get_password("a@b.c", "libre"), "libre")
        self.assertTrue(credentials.delete_password())   # tutte
        self.assertIsNone(credentials.get_password("a@b.c", "libre"))


if __name__ == "__main__":
    unittest.main()
