# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Burndown Chart Updater.
Minimal executable to handle updating the main application.
"""

block_cipher = None

# Minimal hidden imports for updater
hiddenimports = [
    'zipfile',
    'shutil',
    'subprocess',
    'time',
    'pathlib',
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
    # Database (updater doesn't need it)
    'sqlite3',
]

a = Analysis(
    ['updater\\updater.py'],
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
    console=True,  # Show progress during update
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\icon.ico' if os.path.exists('assets\\icon.ico') else None,
)
