# PyInstaller: pyinstaller --noconfirm --clean glucobar.spec
# Crea dist/GlucoBar/GlucoBar.exe (cartella, non file unico: parte più in fretta
# e dà meno falsi positivi agli antivirus).

a = Analysis(
    ["run_glucobar.py"],
    datas=[("assets/glucobar.ico", "assets"), ("assets/glucobar.png", "assets")],
    hiddenimports=["pystray._win32"],  # pystray sceglie il backend a runtime
    excludes=["unittest", "pydoc", "pytest"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GlucoBar",
    icon="assets/glucobar.ico",
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="GlucoBar", upx=False)
