"""Istanza unica e richiesta di chiusura con i file (Mac e Linux).
Su Windows (mutex ed evento) li prova la build, con GlucoBar aperto davvero."""
import os
import sys
import tempfile
import unittest
from unittest import mock

from glucobar import config, instance


@unittest.skipIf(sys.platform == "win32", "su Windows usa mutex ed evento")
class FileInstanceTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = mock.patch.object(config, "CONFIG_DIR", tmp.name)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self.release)

    def release(self):
        if instance._lock is not None:
            instance._lock.close()
            instance._lock = None

    def test_single_instance_and_quit_request(self):
        self.assertFalse(instance.is_running())
        self.assertFalse(instance.already_running())       # siamo la copia aperta
        self.assertTrue(instance.is_running())
        event = instance.quit_event()
        self.assertFalse(instance.quit_requested(event))
        # un'altra copia chiede di chiudere: qui nessuno chiude, quindi scade
        self.assertFalse(instance.request_quit(timeout=0.3))
        self.assertTrue(instance.quit_requested(event))
        self.assertFalse(instance.quit_requested(event))   # la richiesta vale una volta

    def test_old_request_is_ignored(self):
        os.makedirs(config.CONFIG_DIR, exist_ok=True)
        with open(os.path.join(config.CONFIG_DIR, "quit.request"), "w") as f:
            f.write("quit\n")
        instance.already_running()
        self.assertFalse(instance.quit_requested(instance.quit_event()))


if __name__ == "__main__":
    unittest.main()
