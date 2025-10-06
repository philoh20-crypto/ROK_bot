# -*- mode: python ; coding: utf-8 -*-

# PyInstaller build specification for Rise of Kingdoms Bot
# Compatible with Windows
# Output: dist/RoK_Bot/RoK_Bot.exe

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ---- MAIN ENTRY ----
main_script = 'bot_core.py'  # main bot controller (entry point)
project_name = 'RoK_Bot'

# ---- HIDDEN IMPORTS ----
hiddenimports = []
hiddenimports += collect_submodules('cv2')
hiddenimports += collect_submodules('PyQt5')
hiddenimports += collect_submodules('numpy')

# ---- DATA FILES (TEMPLATES, IMAGES, ETC.) ----
datas = []
if os.path.isdir('templates'):
    datas.append(('templates', 'templates'))
if os.path.isdir('assets'):
    datas.append(('assets', 'assets'))
if os.path.isdir('icons'):
    datas.append(('icons', 'icons'))

# Add additional data like .ui files or image references
datas += collect_data_files('cv2')
datas += collect_data_files('PyQt5')

# ---- BUILD SETTINGS ----
a = Analysis(
    [main_script],
    pathex=[os.getcwd()],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# ---- PYQT5 GUI SETTINGS ----
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=project_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # set to True if you want a console window
    icon='icons/app.ico' if os.path.exists('icons/app.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=project_name,
)
