# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Burndown Chart Updater.
Minimal executable to handle updating the main application.
"""

import os
from pathlib import Path

# Get project root - when running with pyinstaller from project root,
# spec file paths are relative to spec file location (build/)
# So we need to go up one level
SPEC_DIR = Path(os.path.abspath(SPECPATH))
PROJECT_ROOT = SPEC_DIR.parent

block_cipher = None

# Minimal hidden imports for updater
hiddenimports = [
    'zipfile',
    'shutil',
    'subprocess',
    'time',
    'pathlib',
    'sqlite3',  # Needed for database flag updates
]

# Exclude everything not needed for updater
excludes = [
    # Heavy application dependencies
    'dash',
    'plotly',
    'pandas',
    'numpy',
    'scipy',
    'matplotlib',
    'networkx',
    'pydantic',
    # Test frameworks
    'pytest',
    'pytest_cov',
    'playwright',
    'selenium',
    # Development tools
    'pip_tools',
    'pip_licenses',
    # GUI frameworks
    'tkinter',
    'wx',
    'PyQt5',
    'PyQt6',
]

a = Analysis(
    [str(PROJECT_ROOT / 'updater' / 'updater.py')],  # Use absolute path
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='BurndownChartUpdater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Silent update - no terminal window, user sees browser toast only
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'assets' / 'icon.ico') if (PROJECT_ROOT / 'assets' / 'icon.ico').exists() else None,
)
