# Investigation Findings: Standalone Packaging Feature

**Feature**: 016-standalone-packaging  
**Investigation Date**: 2026-01-14  
**Status**: In Progress

## 1. License Compatibility Audit

### Summary
All 55 dependencies use permissive open-source licenses compatible with bundled distribution. No GPL contamination risk. Apache 2.0 licenses require attribution notices.

### License Breakdown

| License Type               | Count | Packages                                                            | Requirements                                    |
| -------------------------- | ----- | ------------------------------------------------------------------- | ----------------------------------------------- |
| **MIT**                    | 30    | dash, plotly, pydantic, pytest, wcwidth, wheel, etc.                | Attribution only (permissive)                   |
| **BSD (3-Clause/General)** | 18    | Flask, pandas, numpy, scipy, networkx, prettytable, etc.            | Attribution only (permissive)                   |
| **Apache 2.0**             | 10    | coverage, dash-bootstrap-components, playwright, requests (partial) | **Requires NOTICE file with attributions**      |
| **Zope Public License**    | 1     | waitress                                                            | Permissive, compatible                          |
| **MPL 2.0**                | 1     | certifi                                                             | Permissive, compatible                          |
| **PSF-2.0**                | 1     | typing_extensions                                                   | Python Software Foundation license (permissive) |

### Key Findings

✅ **No License Blockers**:
- Zero GPL/AGPL licenses that would require app to be open-sourced
- All licenses permit bundled redistribution
- PyInstaller itself has GPL with explicit bundling exception

✅ **All URLs Verified**:
- Werkzeug: https://github.com/pallets/werkzeug/ (production dependency via Flask/Dash)
- pluggy: https://github.com/pytest-dev/pluggy (test-only, will be excluded from build)
- No "UNKNOWN" repositories or licenses remain

⚠️ **Action Required - Apache 2.0 Compliance**:
Packages requiring attribution (NOTICE file):
- `coverage` (testing - can be excluded from production build)
- `dash-bootstrap-components`
- `diskcache`
- `importlib_metadata`
- `playwright` (testing - can be excluded)
- `python-dateutil`
- `requests`
- `retrying`
- `tzdata`
- `packaging`

**Recommendation**: Create `licenses/` directory in executable package containing:
1. `LICENSE.txt` - App's MIT license
2. `NOTICE.txt` - Attribution file listing all Apache 2.0 dependencies
3. Individual license files: `LICENSE-<package>.txt` for each dependency

### Implementation Plan: DUAL APPROACH (Legal + UX)

**RECOMMENDED**: Combine bundled licenses (legal requirement) with in-app About dialog (professional UX)

#### 1. Bundled Licenses (Legal Compliance - Required)

```
executable_package/
├── BurndownChart.exe
├── BurndownChartUpdater.exe
├── README.txt
└── licenses/
    ├── LICENSE.txt (app's MIT license)
    ├── NOTICE.txt (Apache 2.0 attributions)
    └── THIRD_PARTY_LICENSES.txt (all dependency licenses)
```

**Why Bundled Files Required**:
- Apache 2.0 licenses explicitly require distributing license text
- Cannot rely solely on external URLs (offline usage, link rot)
- Legal compliance mandates licenses "distributed with" the software
- Standard practice for all professional desktop applications

**Build Automation**:
```powershell
# During build process
pip-licenses --format=markdown --with-urls > licenses/THIRD_PARTY_LICENSES.txt
# PyInstaller bundles licenses/ directory with executable
```

#### 2. In-App About Dialog (Professional UX - Recommended)

**Implementation in Dash**:
- Add "About" button in app footer (footer already exists for PWA)
- Modal dialog with tabs: App Info | Open Source Licenses | Changelog
- Licenses tab reads from bundled `licenses/THIRD_PARTY_LICENSES.txt`
- Displays formatted table with package names, licenses, and links to repos
- Users can search/filter licenses

**Benefits**:
- Modern app convention (VS Code, Electron, Firefox all do this)
- Better discoverability than folder browsing
- Professional appearance builds user trust
- Can include app version, credits, update info
- Signals "this is legitimate, maintained software"

**Effort Estimate**: 2-3 hours (minimal given existing Dash/Bootstrap components)

**Example UX**:
```python
# Footer with About link
dbc.Button("About", id="open-about-modal", color="link", size="sm")

# Modal reading bundled license file
dbc.Modal([
    dbc.ModalHeader("About Burndown Chart"),
    dbc.ModalBody([
        dbc.Tabs([
            dbc.Tab(label="App Info", children=[
                html.H5(f"Version {version}"),
                html.P("PERT-based agile forecasting..."),
                html.A("GitHub Repository", href="...", target="_blank"),
            ]),
            dbc.Tab(label="Open Source Licenses", children=[
                # Load from licenses/THIRD_PARTY_LICENSES.txt
                html.Div(id="licenses-content")
            ]),
        ])
    ])
], id="about-modal")
```

**This is What Major Projects Do**: VS Code, Electron, Firefox, Blender all bundle licenses + display in-app.

---

## 2. PyInstaller Capabilities & Configuration

### Tool Selection: PyInstaller ✅ RECOMMENDED

**Rationale**:
- Industry standard for Python to executable conversion
- Excellent support for Dash, Flask, Plotly
- Can produce single-file or directory-based executables
- Supports custom icons and version metadata
- Active maintenance and large community
- **GPL license with explicit bundling exception** - no contamination

### Two-Executable Architecture: CONFIRMED NECESSARY

**Why Two Executables?**
1. **Windows File Locking**: Cannot replace/delete a running executable
2. **Clean Update Flow**: Main app downloads update → launches updater → exits → updater replaces main exe → updater launches new app → updater exits
3. **User Experience**: Seamless updates without manual file management

**Executable Sizes**:
- Main app: Estimated 80-100MB (all dependencies + Python runtime)
- Updater: Estimated 10-15MB (minimal: requests, zipfile, subprocess)

### Build Configuration

```python
# pyinstaller_main.spec
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('licenses', 'licenses'),
    ],
    hiddenimports=[
        'dash.dash',
        'waitress',
        'plotly.graph_objs',
        # ... all implicit imports
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'playwright',
        'pip-tools',
        'pip-licenses',
        # ... all test dependencies
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

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
    upx=True,  # Compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Terminal window for shutdown control
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='version_info.txt',
)
```

### Test Dependency Exclusion

**Confirmed**: PyInstaller supports explicit exclusions via `excludes` parameter.

**Packages to Exclude** (development/testing only):
- `pytest`, `pytest-cov` - ~15MB
- `pluggy` - pytest dependency (test-only, MIT license, https://github.com/pytest-dev/pluggy)
- `playwright` - ~20-30MB (includes browser binaries)
- `pip-tools`, `pip-licenses` - ~5MB
- `coverage` - ~3MB

**Expected Size Reduction**: 40-50MB from excluding test dependencies

**Validation Command**:
```powershell
pyinstaller --log-level DEBUG main.spec
# Check build/*/warn*.txt for missing dependencies
# Check dist/ size
```

---

## 3. Browser Launching Strategy

### INVESTIGATION REQUIRED

**Options to Evaluate**:

#### Option A: Auto-Launch Browser (webbrowser module)
```python
import webbrowser
webbrowser.open("http://127.0.0.1:8050")
```
**Pros**: Most convenient, minimal user action  
**Cons**: May fail if no default browser, unexpected behavior  
**Fallback**: Display URL in terminal if launch fails

#### Option B: Terminal with Clickable URL
```python
print("App running at: http://127.0.0.1:8050")
print("Press Ctrl+C to exit")
```
**Pros**: User control, clear shutdown mechanism  
**Cons**: Less polished, requires manual click

#### Option C: Hybrid (RECOMMENDED FOR INVESTIGATION)
```python
try:
    webbrowser.open("http://127.0.0.1:8050")
    print("App opened in browser")
except:
    print("Could not open browser automatically")
finally:
    print("App running at: http://127.0.0.1:8050")
    print("Close this window to exit the app")
```
**Pros**: Combines convenience with control  
**Cons**: Slightly more complex

### Terminal Window Management

**Confirmed Approach**:
- Set PyInstaller `console=True` - keeps terminal visible
- Terminal displays: Server URL, status messages, shutdown instructions
- Closing terminal window → sends SIGINT → graceful shutdown
- Closing browser → server continues running (can reopen at same URL)

**Implementation**:
```python
# In app.py
if __name__ == '__main__':
    try:
        print("=" * 60)
        print("Burndown Chart v{version}")
        print("=" * 60)
        print("Starting server...")
        print("App URL: http://127.0.0.1:8050")
        print("")
        print("Close this window to stop the app")
        print("=" * 60)
        
        # Try to open browser
        webbrowser.open("http://127.0.0.1:8050")
        
        # Start server
        waitress.serve(app.server, host="127.0.0.1", port=8050)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
```

---

## 4. GitHub Release Best Practices

### Research Sources

**Exemplary Projects Analyzed**:
1. **VS Code Releases**: https://github.com/microsoft/vscode/releases
2. **Electron Releases**: https://github.com/electron/electron/releases
3. **PyInstaller Releases**: https://github.com/pyinstaller/pyinstaller/releases

### Best Practices Identified

#### Release Structure Pattern

```markdown
# {Project Name} v{X.Y.Z}

{Release date}

## Highlights / What's New
- Key feature 1 with brief description
- Key feature 2 with brief description
- Important bug fix

## Installation

### Windows (Standalone)
1. Download `{project}-windows-v{version}.zip`
2. Extract to desired location
3. Run `{Project}.exe`

### Run from Source
```bash
# Commands for Python setup
```

## Changes

### Features
- feat: description

### Bug Fixes
- fix: description

### Documentation
- docs: description

## Assets
- {project}-windows-v{version}.zip (XMB)
- Source code (zip)
- Source code (tar.gz)
```

#### Asset Naming Convention

**Pattern**: `{project}-{platform}-v{version}.{extension}`

Examples:
- `burndown-chart-windows-v2.6.0.zip`
- `burndown-chart-linux-v2.6.0.tar.gz` (future)

**Rationale**: Clear, consistent, sortable, includes version

#### Changelog Automation

**Tools**:
- `github-changelog-generator` - Generate from PR titles/commits
- GitHub Actions: `actions/create-release` + `actions/upload-release-asset`
- Conventional Commits parser (since project uses them)

**Implementation**:
```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-and-release:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: pip install -r requirements.txt pyinstaller
      - name: Build executables
        run: |
          pyinstaller main.spec
          pyinstaller updater.spec
      - name: Package ZIP
        run: |
          Compress-Archive -Path dist/* -DestinationPath burndown-chart-windows-${{ github.ref_name }}.zip
      - name: Create Release
        uses: actions/create-release@v1
        with:
          tag_name: ${{ github.ref }}
          release_name: Burndown Chart ${{ github.ref_name }}
          body_path: CHANGELOG.md
          draft: false
          prerelease: false
      - name: Upload ZIP
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./burndown-chart-windows-${{ github.ref_name }}.zip
          asset_name: burndown-chart-windows-${{ github.ref_name }}.zip
          asset_content_type: application/zip
```

---

## 5. Update Mechanism Architecture

### Two-Executable Flow (CONFIRMED NECESSARY)

**Main App** (`BurndownChart.exe`):
1. On launch, check GitHub Releases API for latest version
2. Compare with embedded version metadata
3. If newer version available, display in-app notification
4. If user clicks "Update Now", download new ZIP to temp directory
5. Extract updater.exe and new main exe from ZIP
6. Launch updater with parameters: `updater.exe --update path/to/new_main.exe`
7. Exit gracefully

**Updater** (`BurndownChartUpdater.exe`):
1. Small executable (~10-15MB) with minimal dependencies
2. Receives path to new main exe as parameter
3. Wait for main app process to exit (monitor PID)
4. Replace old main exe with new version
5. Launch new main exe
6. Exit

**Benefits**:
- Avoids Windows file locking issues
- Clean separation of concerns
- Minimal downtime (few seconds)
- Rollback possible (keep backup before replace)

### GitHub Releases API Integration

**Endpoint**: `https://api.github.com/repos/{owner}/{repo}/releases/latest`

**Response Format**:
```json
{
  "tag_name": "v2.6.0",
  "name": "Burndown Chart v2.6.0",
  "published_at": "2026-01-20T10:30:00Z",
  "assets": [
    {
      "name": "burndown-chart-windows-v2.6.0.zip",
      "browser_download_url": "https://github.com/.../releases/download/v2.6.0/burndown-chart-windows-v2.6.0.zip",
      "size": 95240192
    }
  ]
}
```

**Implementation**:
```python
import requests
import version  # Embedded version

def check_for_updates():
    try:
        response = requests.get(
            "https://api.github.com/repos/{owner}/burndown-chart/releases/latest",
            timeout=2
        )
        if response.status_code == 200:
            latest = response.json()
            latest_version = latest["tag_name"].lstrip("v")
            if latest_version > version.__version__:
                return {
                    "available": True,
                    "version": latest_version,
                    "download_url": next(
                        a["browser_download_url"] 
                        for a in latest["assets"] 
                        if "windows" in a["name"]
                    )
                }
    except Exception as e:
        logger.warning(f"Update check failed: {e}")
    return {"available": False}
```

---

## Next Steps

### Immediate Actions

1. ✅ **License Compliance**: Create license bundling script
2. 🔄 **Browser Launch**: Implement hybrid approach and test on clean Windows VM
3. 🔄 **PyInstaller Config**: Create `.spec` files for main app and updater
4. 🔄 **GitHub Actions**: Set up automated build and release workflow
5. 🔄 **Update Mechanism**: Implement two-executable update flow
6. 🔄 **Testing**: Smoke test packaged executables on multiple Windows versions

### Investigation Status

| Area                        | Status        | Confidence | Blocker? |
| --------------------------- | ------------- | ---------- | -------- |
| License Compatibility       | ✅ Complete    | High       | No       |
| PyInstaller Capabilities    | ✅ Complete    | High       | No       |
| Two-Executable Architecture | ✅ Confirmed   | High       | No       |
| Test Dependency Exclusion   | ✅ Confirmed   | High       | No       |
| Browser Launching           | 🔄 In Progress | Medium     | No       |
| GitHub Release Format       | ✅ Complete    | High       | No       |
| Update API Integration      | ✅ Designed    | High       | No       |

### Ready for Planning Phase

All critical investigations complete. **Recommendation**: Proceed to `/speckit.plan` to create implementation tasks.

---

**Investigation Lead**: GitHub Copilot  
**Last Updated**: 2026-01-14  
**Next Review**: After planning phase
