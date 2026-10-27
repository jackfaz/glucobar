import io
import unittest

from glucobar import tui


class FakeTerm:
    """Tasti finti al posto della tastiera; l'output va in una stringa."""

    def __init__(self, keys):
        self.keys = list(keys)
        self.out = io.StringIO()

    def read_key(self):
        return self.keys.pop(0)

    def write(self, text):
        self.out.write(text)


OPTIONS = [("a", "Alfa"), ("b", "Beta"), ("c", "Gamma")]


class WidgetsTest(unittest.TestCase):
    def test_select_with_arrows_wraps_around(self):
        self.assertEqual(tui.select(FakeTerm(["down", "down", "enter"]), "T", OPTIONS), "c")
        self.assertEqual(tui.select(FakeTerm(["up", "enter"]), "T", OPTIONS), "c")
        self.assertEqual(tui.select(FakeTerm(["enter"]), "T", OPTIONS, default=1), "b")

    def test_multiselect_space_toggles_and_needs_one(self):
        term = FakeTerm(["space", "enter", "space", "enter"])   # toglie, prova, rimette
        self.assertEqual(tui.multiselect(term, "T", OPTIONS, selected=["a"], need_one="Almeno uno"),
                         ["a"])
        self.assertIn("Almeno uno", term.out.getvalue())
        term = FakeTerm(["down", "space", "down", "space", "enter"])
        self.assertEqual(tui.multiselect(term, "T", OPTIONS, selected=["a"]), ["a", "b", "c"])

    def test_text_default_backspace_and_validation(self):
        self.assertEqual(tui.text(FakeTerm(["enter"]), "Email", default="a@b.c"), "a@b.c")
        keys = list("8x") + ["backspace", "0", "enter"]
        self.assertEqual(tui.text(FakeTerm(keys), "N"), "80")
        term = FakeTerm(list("9") + ["enter", "0", "enter"])
        check = lambda v: None if int(v) >= 40 else "Troppo basso"  # noqa: E731
        self.assertEqual(tui.text(term, "N", validate=check), "90")
        self.assertIn("Troppo basso", term.out.getvalue())

    def test_secret_is_never_printed(self):
        term = FakeTerm(list("segreta") + ["enter"])
        self.assertEqual(tui.text(term, "Password", secret=True), "segreta")
        self.assertNotIn("segreta", term.out.getvalue())

    def test_escape_cancels(self):
        with self.assertRaises(tui.Cancelled):
            tui.select(FakeTerm(["down", "esc"]), "T", OPTIONS)
        with self.assertRaises(tui.Cancelled):
            tui.text(FakeTerm(["ctrl-c"]), "T")


if __name__ == "__main__":
    unittest.main()
