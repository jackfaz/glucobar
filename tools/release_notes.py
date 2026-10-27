"""Stampa la sezione di CHANGELOG.md di una versione, per il testo della release.

Uso: python tools/release_notes.py 0.4.0 [release-notes.md]
(senza file stampa a schermo; il file è scritto in UTF-8 anche su Windows)
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def section(changelog, version):
    match = re.search(rf"^## \[{re.escape(version)}\].*?$(.*?)(?=^## \[|^\[)",
                      changelog, re.M | re.S)
    if not match:
        raise SystemExit(f"Versione {version} non trovata in CHANGELOG.md")
    return match.group(1).strip()


def notes(version):
    with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
        text = section(f.read(), version)
    repo = os.environ.get("GITHUB_REPOSITORY", "jackfaz/glucobar")
    return (f"{text}\n\n---\n"
            f"GlucoBar is not a medical device. Download `GlucoBar-Setup-{version}.exe` "
            f"below. Full history: "
            f"[CHANGELOG.md](https://github.com/{repo}/blob/main/CHANGELOG.md)\n")


if __name__ == "__main__":
    result = notes(sys.argv[1])
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(result)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(result)
