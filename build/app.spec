# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Burndown Chart main application.
Defines how to bundle the application and all its dependencies.
"""

block_cipher = None

# Data files to bundle (assets, licenses)
datas = [
    ('assets', 'assets'),
    ('licenses', 'licenses'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'dash',
    'dash.dependencies',
    'dash_bootstrap_components',
    'plotly',
    'pandas',
    'numpy',
    'scipy',
    'scipy.special',
    'scipy.special._cdflib',
    'requests',
    'waitress',
    'pyperclip',
    'dotenv',
    'networkx',
    'pydantic',
    'sqlite3',
    'logging.handlers',
]

# Packages to exclude from the bundle
excludes = [
    'pytest',
    'pytest_cov',
    'playwright',
    'pip_tools',
    'pip_licenses',
    'pyinstaller',
    'tkinter',
    'test',
    'unittest',
    '_pytest',
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
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
    name='BurndownChart',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disabled to avoid false positives with antivirus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show terminal window for status messages
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\icon.ico' if os.path.exists('assets\\icon.ico') else None,
)
