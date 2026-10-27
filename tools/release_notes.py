"""Stampa la sezione di CHANGELOG.md di una versione, per il testo della release.

Uso: python tools/release_notes.py 0.4.0 [release-notes.md] [installer.exe] [link VirusTotal]
                                     [true se Windows Defender segnala l'installer]
(senza file stampa a schermo; il file è scritto in UTF-8 anche su Windows).
Con l'installer aggiunge la sua impronta SHA-256, con il link anche la scansione.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from virustotal import sha256  # noqa: E402


def section(changelog, version):
    match = re.search(rf"^## \[{re.escape(version)}\].*?$(.*?)(?=^## \[|^\[)",
                      changelog, re.M | re.S)
    if not match:
        raise SystemExit(f"Versione {version} non trovata in CHANGELOG.md")
    return match.group(1).strip()


def notes(version, installer=None, scan_url=None, defender_flag=False):
    with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
        text = section(f.read(), version)
    repo = os.environ.get("GITHUB_REPOSITORY", "jackfaz/glucobar")
    result = (f"{text}\n\n---\n"
              f"GlucoBar is not a medical device. Download `GlucoBar-Setup-{version}.exe` "
              f"below (`GlucoBar-Setup.exe` is the same file, under a name that stays the same "
              f"in every release). Full history: "
              f"[CHANGELOG.md](https://github.com/{repo}/blob/main/CHANGELOG.md)\n")
    if installer:
        result += (f"\nSHA-256 of `{os.path.basename(installer)}`: "
                   f"`{sha256(installer)}`\n")
    if scan_url:
        result += f"Antivirus scan of this exact file: [VirusTotal]({scan_url})\n"
    if defender_flag:
        result += ("\n**Pre-release:** Microsoft Defender's automatic (machine-learning) check "
                   "flags this installer, a false positive common for Python apps packaged as "
                   "an .exe. It stays a pre-release until Microsoft clears it; the latest "
                   "release is the recommended download meanwhile.\n")
    return result


if __name__ == "__main__":
    extra = [a or None for a in sys.argv[3:5]]
    result = notes(sys.argv[1], *extra, defender_flag=sys.argv[5:6] == ["true"])
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(result)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(result)
