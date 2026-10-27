# PyInstaller: pyinstaller --noconfirm --clean glucobar.spec
# Crea dist/GlucoBar/ con due eseguibili che condividono le librerie in _internal:
#   GlucoBar.exe      il programma (senza console)
#   glucobar-cli.exe  il comando da terminale (glucobar setup, status, set, ...)
# Cartella e non file unico: parte più in fretta e dà meno falsi positivi agli antivirus.

import os
import re
import sys

with open(os.path.join(SPECPATH, "glucobar", "__init__.py"), encoding="utf-8") as f:
    VERSION = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)


def version_info(name, description):
    # Nome, descrizione e versione nelle Proprietà del file: gli eseguibili senza
    # questi dati sono guardati con più sospetto dagli antivirus
    if sys.platform != "win32":
        return None  # il modulo versioninfo esiste solo su Windows
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct,
        VSVersionInfo)
    numbers = tuple(int(n) for n in re.findall(r"\d+", VERSION)[:3]) + (0,)
    strings = [("CompanyName", "GlucoBar contributors"),
               ("FileDescription", description),
               ("FileVersion", VERSION),
               ("InternalName", name),
               ("LegalCopyright", "MIT License, GlucoBar contributors"),
               ("OriginalFilename", name + ".exe"),
               ("ProductName", "GlucoBar"),
               ("ProductVersion", VERSION)]
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=numbers, prodvers=numbers),
        kids=[StringFileInfo([StringTable("040904B0",
                                          [StringStruct(k, v) for k, v in strings])]),
              VarFileInfo([VarStruct("Translation", [0x0409, 1200])])])


common = dict(
    datas=[("assets/glucobar.ico", "assets"), ("assets/glucobar.png", "assets")],
    hiddenimports=["pystray._win32"],  # pystray sceglie il backend a runtime
    excludes=["unittest", "pydoc", "pytest"],
)
app = Analysis(["run_glucobar.py"], **common)
cli = Analysis(["run_cli.py"], **common)

app_exe = EXE(PYZ(app.pure), app.scripts, [], exclude_binaries=True, name="GlucoBar",
              icon="assets/glucobar.ico", console=False, upx=False,
              version=version_info("GlucoBar", "GlucoBar"))
cli_exe = EXE(PYZ(cli.pure), cli.scripts, [], exclude_binaries=True, name="glucobar-cli",
              icon="assets/glucobar.ico", console=True, upx=False,
              version=version_info("glucobar-cli", "GlucoBar command line"))

coll = COLLECT(app_exe, cli_exe, app.binaries, app.datas, cli.binaries, cli.datas,
               name="GlucoBar", upx=False)
