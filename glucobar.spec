# PyInstaller: pyinstaller --noconfirm --clean glucobar.spec
# Crea dist/GlucoBar/ con due eseguibili che condividono le librerie in _internal:
#   GlucoBar.exe      il programma (senza console)
#   glucobar-cli.exe  il comando da terminale (glucobar setup, status, set, ...)
# Cartella e non file unico: parte più in fretta e dà meno falsi positivi agli antivirus.

common = dict(
    datas=[("assets/glucobar.ico", "assets"), ("assets/glucobar.png", "assets")],
    hiddenimports=["pystray._win32"],  # pystray sceglie il backend a runtime
    excludes=["unittest", "pydoc", "pytest"],
)
app = Analysis(["run_glucobar.py"], **common)
cli = Analysis(["run_cli.py"], **common)

app_exe = EXE(PYZ(app.pure), app.scripts, [], exclude_binaries=True, name="GlucoBar",
              icon="assets/glucobar.ico", console=False, upx=False)
cli_exe = EXE(PYZ(cli.pure), cli.scripts, [], exclude_binaries=True, name="glucobar-cli",
              icon="assets/glucobar.ico", console=True, upx=False)

coll = COLLECT(app_exe, cli_exe, app.binaries, app.datas, cli.binaries, cli.datas,
               name="GlucoBar", upx=False)
