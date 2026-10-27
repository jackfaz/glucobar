"""Crea il manifesto winget (3 file YAML) per una versione pubblicata su GitHub.

Uso: python tools/winget_manifest.py 0.5.0 dist-installer/GlucoBar-Setup-0.5.0.exe [cartella]

Il risultato va inviato a https://github.com/microsoft/winget-pkgs, per esempio con
    wingetcreate submit <cartella>\\manifests\\j\\jackfaz\\GlucoBar\\0.5.0
"""

import datetime
import hashlib
import os
import sys

PACKAGE = "jackfaz.GlucoBar"
REPO = os.environ.get("GITHUB_REPOSITORY", "jackfaz/glucobar")
APP_ID = "{08BF5F70-5160-4B58-BCA3-99FF0D35CACC}"   # AppId in installer/glucobar.iss
SCHEMA = "1.9.0"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def manifests(version, installer):
    url = f"https://github.com/{REPO}/releases/download/v{version}/{os.path.basename(installer)}"
    head = (f"PackageIdentifier: {PACKAGE}\n"
            f"PackageVersion: {version}\n")
    tail = f"ManifestVersion: {SCHEMA}\n"
    schema = f"# yaml-language-server: $schema=https://aka.ms/winget-manifest.{{}}.{SCHEMA}.schema.json\n\n"
    product_code = f"'{APP_ID}_is1'"
    return {
        f"{PACKAGE}.yaml": schema.format("version") + head + (
            "DefaultLocale: en-US\n"
            "ManifestType: version\n") + tail,
        f"{PACKAGE}.installer.yaml": schema.format("installer") + head + (
            "InstallerType: inno\n"
            "Scope: user\n"
            "InstallModes:\n- interactive\n- silent\n- silentWithProgress\n"
            "UpgradeBehavior: install\n"
            "Commands:\n- glucobar\n"
            f"ProductCode: {product_code}\n"
            f"ReleaseDate: {datetime.date.today().isoformat()}\n"
            "AppsAndFeaturesEntries:\n"
            "- DisplayName: GlucoBar\n"
            "  Publisher: GlucoBar contributors\n"
            f"  ProductCode: {product_code}\n"
            "Installers:\n"
            "- Architecture: x64\n"
            f"  InstallerUrl: {url}\n"
            f"  InstallerSha256: {sha256(installer)}\n"
            "ManifestType: installer\n") + tail,
        f"{PACKAGE}.locale.en-US.yaml": schema.format("defaultLocale") + head + (
            "PackageLocale: en-US\n"
            "Publisher: GlucoBar contributors\n"
            f"PublisherUrl: https://github.com/{REPO}\n"
            f"PublisherSupportUrl: https://github.com/{REPO}/issues\n"
            "PackageName: GlucoBar\n"
            f"PackageUrl: https://github.com/{REPO}\n"
            "License: MIT\n"
            f"LicenseUrl: https://github.com/{REPO}/blob/main/LICENSE\n"
            "ShortDescription: Your FreeStyle Libre glucose on the Windows taskbar.\n"
            "Description: |-\n"
            "  GlucoBar reads your latest FreeStyle Libre reading from LibreLinkUp and shows it\n"
            "  on the taskbar next to the clock, in a small window, in a desktop panel with a\n"
            "  chart and statistics, or as a tray icon. Not a medical device.\n"
            "Moniker: glucobar\n"
            "Tags:\n- diabetes\n- freestyle-libre\n- librelinkup\n- cgm\n- glucose\n- taskbar\n"
            f"ReleaseNotesUrl: https://github.com/{REPO}/blob/main/CHANGELOG.md\n"
            "ManifestType: defaultLocale\n") + tail,
    }


def main(version, installer, out="winget"):
    folder = os.path.join(out, "manifests", "j", "jackfaz", "GlucoBar", version)
    os.makedirs(folder, exist_ok=True)
    for name, content in manifests(version, installer).items():
        with open(os.path.join(folder, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    print(f"manifesto winget in {folder}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
