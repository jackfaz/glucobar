"""Gira davvero solo su Windows (in CI): usa una chiave di prova nel registro."""
import sys
import unittest

from glucobar import notifyicon

TEST_KEY = r"Software\GlucoBarTest\NotifyIconSettings"


@unittest.skipUnless(sys.platform == "win32", "registro di Windows")
class PromoteTest(unittest.TestCase):
    def setUp(self):
        import winreg
        self.winreg = winreg
        icons = {
            "111": r"{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}\Programs\GlucoBar\GlucoBar.exe",
            "222": r"C:\Program Files\Altro\altro.exe",
        }
        for name, path in icons.items():
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{TEST_KEY}\{name}") as key:
                winreg.SetValueEx(key, "ExecutablePath", 0, winreg.REG_SZ, path)
                winreg.SetValueEx(key, "IsPromoted", 0, winreg.REG_DWORD, 0)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        winreg = self.winreg
        for name in ("111", "222"):
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"{TEST_KEY}\{name}")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, TEST_KEY)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\GlucoBarTest")

    def promoted(self, name):
        winreg = self.winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"{TEST_KEY}\{name}") as key:
            return winreg.QueryValueEx(key, "IsPromoted")[0]

    def test_promotes_only_glucobar(self):
        self.assertTrue(notifyicon.promote("GlucoBar.exe", TEST_KEY))
        self.assertEqual(self.promoted("111"), 1)
        self.assertEqual(self.promoted("222"), 0)

    def test_not_found(self):
        self.assertFalse(notifyicon.promote("niente.exe", TEST_KEY))
        self.assertFalse(notifyicon.promote("GlucoBar.exe", r"Software\GlucoBarTest\Manca"))


class NotWindowsTest(unittest.TestCase):
    @unittest.skipIf(sys.platform == "win32", "solo fuori da Windows")
    def test_does_nothing(self):
        self.assertFalse(notifyicon.promote("GlucoBar.exe"))


if __name__ == "__main__":
    unittest.main()
