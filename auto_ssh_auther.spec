# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys


project_root = Path(SPECPATH)
runtime_datas = [
    (str(project_root / "icon_ssh_auther.ico"), "."),
    (str(project_root / "icon_ssh_auther.png"), "."),
]
build_icon = project_root / ("icon_ssh_auther.ico" if sys.platform == "win32" else "icon_ssh_auther.png")

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=runtime_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='auto_ssh_auther',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=sys.platform == "darwin",
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(build_icon)],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='auto_ssh_auther',
)
app = BUNDLE(
    coll,
    name='auto_ssh_auther.app',
    icon=str(build_icon),
    bundle_identifier='com.gbworks.auto-ssh-auther',
)
