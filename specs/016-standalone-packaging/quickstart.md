# Quickstart: Building Standalone Executable

**Feature**: 016-standalone-packaging  
**Audience**: Developers building and releasing Windows executables

## Prerequisites

- Windows 10+ (64-bit)
- Python 3.13 installed
- Git installed
- Active virtual environment (`.venv`)
- All dependencies installed (`pip install -r requirements.txt`)

## Quick Commands

```powershell
# Build executables (app.exe + updater.exe)
.\build\build.ps1

# Build + test locally
.\build\build.ps1 -Test

# Build + create GitHub release (requires tag)
git tag v2.6.0
git push origin v2.6.0
# GitHub Actions workflow automatically builds and publishes
```

## Step-by-Step Build Process

### 1. Install Build Dependencies

```powershell
# Add PyInstaller to requirements.in
# Already added: pip-licenses>=5.0.0, pip-tools==7.4.1

# Install
.\.venv\Scripts\activate
pip install pyinstaller>=6.0.0
```

### 2. Generate License Files

```powershell
# Run license collection script
.\build\collect_licenses.ps1

# Generates:
# licenses/LICENSE.txt (app MIT license)
# licenses/NOTICE.txt (Apache 2.0 attributions)
# licenses/THIRD_PARTY_LICENSES.txt (all dependencies)
```

### 3. Build Main Executable

```powershell
# Run PyInstaller with app.spec
pyinstaller build/app.spec

# Output: dist/BurndownChart.exe
# Size: ~80-100MB (with dependencies bundled)
```

### 4. Build Updater Executable

```powershell
# Run PyInstaller with updater.spec
pyinstaller build/updater.spec

# Output: dist/BurndownChartUpdater.exe
# Size: ~10-15MB (minimal dependencies)
```

### 5. Test Locally

```powershell
# Navigate to dist/
cd dist

# Run app executable
.\BurndownChart.exe

# Expected behavior:
# - Terminal window appears
# - Server starts on http://127.0.0.1:8050
# - Browser opens automatically
# - App loads and functions normally

# Test updater (requires mock update file)
.\BurndownChartUpdater.exe --help
```

### 6. Package for Distribution

```powershell
# Create ZIP file for release
.\build\package.ps1

# Output: dist/burndown-chart-windows-v{version}.zip
# Contains:
# - BurndownChart.exe
# - BurndownChartUpdater.exe
# - README.txt (quick start)
# - licenses/ (all license files)
```

## Build Script Options

```powershell
# Show help
.\build\build.ps1 -Help

# Build without cleaning previous build
.\build\build.ps1 -NoClean

# Build with verbose output
.\build\build.ps1 -Verbose

# Build and run tests
.\build\build.ps1 -Test

# Sign executables (requires certificate)
.\build\build.ps1 -Sign -CertPath "path\to\cert.pfx"
```

## Configuration Files

### `build/build_config.yaml`

Main build configuration:

```yaml
app:
  name: "BurndownChart"
  version: "2.5.0"  # Read from bump_version.py
  entry_point: "app.py"
  icon: "assets/icon.ico"

dependencies:
  exclude_packages:
    - pytest
    - playwright
    - pip_tools
    - coverage
```

### `build/app.spec`

PyInstaller spec for main app:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../assets', 'assets'),
        ('../licenses', 'licenses'),
    ],
    hiddenimports=[
        'dash',
        'plotly',
        'waitress',
        'pydantic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'playwright',
        'pip_tools',
        'coverage',
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
    name='BurndownChart',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    console=True,  # Show terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/icon.ico',
)
```

### `build/updater.spec`

PyInstaller spec for updater:

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../updater/updater.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    excludes=[
        'dash', 'plotly', 'flask',  # Not needed in updater
    ],
    cipher=None,
)

exe = EXE(
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BurndownChartUpdater',
    console=True,  # Show progress messages
    icon='../assets/icon.ico',
)
```

## Testing the Build

### Manual Testing Checklist

```powershell
# 1. Clean system test
# - Copy dist/*.exe to clean Windows VM (no Python installed)
# - Double-click BurndownChart.exe
# - Verify: terminal appears, browser opens, app loads

# 2. Database persistence
# - Run app, configure JIRA settings
# - Close app, reopen
# - Verify: settings persisted

# 3. Portable installation
# - Copy app.exe and profiles/ to USB drive
# - Run from USB drive
# - Verify: app loads data correctly

# 4. Update mechanism
# - Modify current version to be older
# - Run app
# - Verify: update notification appears

# 5. License display
# - Open app, click About in footer
# - Verify: licenses tab shows all dependencies
```

### Automated Tests

```powershell
# Run build validation tests
pytest tests/integration/test_executable_launch.py -v

# Test updater logic
pytest tests/unit/updater/test_updater.py -v

# Smoke test executable
.\dist\BurndownChart.exe --version
.\dist\BurndownChart.exe --test-database
```

## Troubleshooting

### Build Fails: "Module not found"

**Solution**: Add missing module to `hiddenimports` in app.spec

```python
hiddenimports=[
    'dash',
    'plotly',
    'missing_module_name',  # Add here
],
```

### Executable Size >100MB

**Solution**: 
1. Verify test dependencies excluded
2. Enable UPX compression (`upx=True`)
3. Check for unnecessary data files

```powershell
# Analyze executable size
pyinstaller --log-level=DEBUG build/app.spec
# Check build/BurndownChart/warn-BurndownChart.txt for included files
```

### Antivirus False Positive

**Solution**: Code sign executable

```powershell
# Sign with certificate
.\build\sign_executable.ps1 -CertPath "cert.pfx" -Password "pwd"
```

### Browser Doesn't Auto-Open

**Check**:
1. `webbrowser` module included (should be standard library)
2. User has default browser configured
3. Corporate policies not blocking auto-launch

**Fallback**: Terminal displays clickable URL

### Database File Not Created

**Check**:
1. Executable directory is writable
2. Running with admin rights (if in Program Files)
3. Check logs in `profiles/logs/` for permissions errors

## GitHub Release Workflow

### Automated Release (Recommended)

```powershell
# 1. Bump version
python bump_version.py minor  # or major/patch

# 2. Commit and push
git add .
git commit -m "chore: bump version to 2.6.0"
git push origin main

# 3. Create and push tag
git tag v2.6.0
git push origin v2.6.0

# 4. GitHub Actions automatically:
# - Builds executables
# - Collects licenses
# - Packages ZIP
# - Creates GitHub release
# - Uploads assets
# - Generates changelog
```

### Manual Release (Fallback)

```powershell
# 1. Build locally
.\build\build.ps1

# 2. Package
.\build\package.ps1

# 3. Create release on GitHub
# - Go to Releases → Draft a new release
# - Tag: v2.6.0
# - Title: "Burndown Chart v2.6.0"
# - Upload: dist/burndown-chart-windows-v2.6.0.zip
# - Publish release
```

## Performance Benchmarks

| Metric          | Target  | Typical |
| --------------- | ------- | ------- |
| Build time      | <10 min | ~7 min  |
| Executable size | <100 MB | ~85 MB  |
| Launch time     | <5 sec  | ~3 sec  |
| Browser open    | <3 sec  | ~1 sec  |
| Update check    | <2 sec  | <1 sec  |

## Next Steps

1. **Implement Build Scripts**: Create `build/build.ps1`, `collect_licenses.ps1`, `package.ps1`
2. **Create .spec Files**: Configure PyInstaller for app and updater
3. **Update app.py**: Add update check on launch
4. **Implement Update Manager**: Create `data/update_manager.py`
5. **Add About Dialog**: Create `ui/about_dialog.py` with license display
6. **Setup GitHub Actions**: Create `.github/workflows/release.yml`
7. **Test on Clean Systems**: VM testing without Python installed

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [GitHub Releases API](https://docs.github.com/en/rest/releases)
- [Python webbrowser module](https://docs.python.org/3/library/webbrowser.html)
- [Code Signing Guide](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)

---

**Status**: Ready for implementation. All prerequisites documented, configuration examples provided, testing procedures defined.
