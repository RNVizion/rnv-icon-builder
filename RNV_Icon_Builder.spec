# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build specification for RNV Icon Builder.

Build with:
    pyinstaller RNV_Icon_Builder.spec

Output:
    dist/RNV_Icon_Builder.exe  (Windows, single-file)
    dist/RNV_Icon_Builder      (macOS/Linux, single-file)

Note: For the Windows .exe icon, place an `icon.ico` file at
resources/icons/icon.ico. If only icon.png exists, you can build
the app first, then use the app itself to generate the .ico and
rebuild.
"""

from pathlib import Path

block_cipher = None

# Resource folders to bundle (screenshots excluded — those are for the README only)
RESOURCE_DATAS = [
    ('resources/button_images',     'resources/button_images'),
    ('resources/background_images', 'resources/background_images'),
    ('resources/fonts',             'resources/fonts'),
    ('resources/icons',             'resources/icons'),
]

# Windows .exe icon (falls back gracefully if missing)
ICON_PATH = 'resources/icons/icon.ico'
if not Path(ICON_PATH).exists():
    ICON_PATH = None


a = Analysis(
    ['RNV_Icon_Builder.py'],
    pathex=[],
    binaries=[],
    datas=RESOURCE_DATAS,
    hiddenimports=[
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
        'pytest',
        'test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RNV_Icon_Builder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
)
