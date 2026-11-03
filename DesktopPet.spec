# Build from the repository root: python -m PyInstaller DesktopPet.spec --noconfirm
from pathlib import Path

ROOT = Path(SPECPATH)
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(path), str(path.parent.relative_to(ROOT)))
           for path in sorted((ROOT / 'assets').rglob('*'))
           if path.is_file() and path.suffix.lower() in ('.png', '.ico')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PySide2', 'PySide6', 'PyQt6.QtWebEngineCore',
              'PyQt6.QtWebEngineWidgets', 'PyQt6.QtQml', 'PyQt6.QtQuick'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    [], name="DesktopPet", debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, icon=str(ROOT / "assets" / "icons" / "fox_ico.ico"),
    uac_admin=False, uac_uiaccess=False,
)
