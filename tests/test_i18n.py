import string
import unittest

from glucobar.i18n import LANGUAGES, STRINGS, refresh_label


def placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


class TranslationsTest(unittest.TestCase):
    def test_every_language_has_every_key(self):
        keys = set(STRINGS["en"])
        self.assertEqual(set(LANGUAGES), set(STRINGS))
        for lang, texts in STRINGS.items():
            self.assertEqual(set(texts), keys, f"chiavi diverse in {lang}")

    def test_placeholders_match_english(self):
        for lang, texts in STRINGS.items():
            for key, text in texts.items():
                self.assertEqual(placeholders(text), placeholders(STRINGS["en"][key]),
                                 f"{lang}.{key}")

    def test_refresh_label(self):
        self.assertEqual([refresh_label(s) for s in (10, 30, 60, 90, 120, 300)],
                         ["10 s", "30 s", "1 min", "90 s", "2 min", "5 min"])


if __name__ == "__main__":
    unittest.main()
