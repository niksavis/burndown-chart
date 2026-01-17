# Research: Standalone Packaging

**Feature**: 016-standalone-packaging  
**Date**: 2026-01-14  
**Status**: Complete - All investigations resolved

## Executive Summary

All 11 investigation items completed and documented in [research/findings.md](research/findings.md). Key decisions:
- **Tool**: PyInstaller (industry standard, GPL with bundling exception)
- **Architecture**: Two-executable approach (app.exe + updater.exe) - CONFIRMED NECESSARY
- **Browser Launch**: Hybrid approach (auto-launch with terminal fallback)
- **License Compliance**: Dual approach (bundled licenses/ + in-app About dialog)
- **GitHub Releases**: Automated via GitHub Actions with conventional commit changelog

## 1. Packaging Tool Selection

### Decision: PyInstaller

**Rationale**:
- Industry standard (used by VS Code, Electron alternatives)
- GPL with explicit bundling exception (no license contamination)
- Cross-platform support (Windows primary, Linux/macOS possible)
- Mature ecosystem with extensive documentation
- Supports Python 3.13

**Alternatives Considered**:
- `py2exe`: Windows-only, less active development
- `cx_Freeze`: More complex configuration
- `Nuitka`: Compilation approach (slower builds, higher complexity)

**Implementation**: PyInstaller .spec file configuration with custom hooks for Dash/Plotly

## 2. Two-Executable Architecture

### Decision: REQUIRED for Windows

**Problem**: Windows file locking prevents executable from replacing itself while running.

**Solution**: 
1. Main app (app.exe) - Dash application
2. Updater (updater.exe) - Minimal updater that:
   - Waits for app.exe to terminate
   - Downloads new version from GitHub
   - Replaces app.exe
   - Relaunches updated app.exe

**Flow**:
```
User clicks "Update Now" 
→ app.exe downloads new version
→ app.exe launches updater.exe with args (download_path, app_path)
→ app.exe exits
→ updater.exe replaces app.exe
→ updater.exe launches new app.exe
→ updater.exe exits
```

**Evidence**: Standard pattern in Electron (app-asar.js + updater), Chrome (GoogleUpdate.exe), Firefox (updater.exe)

## 3. Browser Launching Strategy

### Decision: Hybrid Approach

**Implementation**:
1. **Primary**: Auto-launch browser using `webbrowser.open()` on startup
2. **Fallback**: Display terminal window with clickable URL if auto-launch fails
3. **Terminal**: Remains visible for shutdown control and status messages

**Benefits**:
- Best UX for 95% of users (auto-open "just works")
- Graceful degradation for edge cases (corporate policies, headless systems)
- Terminal provides shutdown control (Ctrl+C or close window)
- User can bookmark URL for subsequent sessions

**Configuration**:
- Environment variable `BURNDOWN_NO_BROWSER=1` to disable auto-launch
- URL displayed in terminal always (even if browser opens)

## 4. GitHub Release Automation

### Decision: GitHub Actions Workflow

**Approach**: Two-stage workflow
1. **Tag Push** → triggers build workflow
2. **Build Workflow** → compiles executables, creates release, uploads assets

**Workflow Structure**:
```yaml
name: Release
on:
  push:
    tags:
      - 'v*'
jobs:
  build:
    runs-on: windows-latest
    steps:
      - Checkout code
      - Setup Python 3.13
      - Install dependencies + pyinstaller
      - Run build script (build/build.ps1)
      - Generate changelog (conventional commits)
      - Create GitHub release
      - Upload assets (Windows ZIP)
```

**Release Structure**:
- Title: "Burndown Chart v{version}"
- Body: Automated changelog + installation instructions
- Assets: `burndown-chart-windows-v{version}.zip`
- Tags: Semver (`v2.5.0`)

**Changelog Generation**: Use `github.event.commits` or GitHub GraphQL API for PR titles

## 5. License Compliance

### Decision: Dual Approach (Legal + UX)

**1. Bundled Licenses (Required)**:
```
licenses/
├── LICENSE.txt (app MIT)
├── NOTICE.txt (Apache 2.0 attributions)
└── THIRD_PARTY_LICENSES.txt (all 55 dependencies)
```

**2. In-App About Dialog (Recommended)**:
- Modal accessible from footer
- Tabs: App Info | Licenses | Changelog
- Displays licenses from bundled files
- Links to package repositories

**License Audit Results**:
- 55 total dependencies
- 30 MIT, 18 BSD, 10 Apache 2.0, 1 Zope, 1 MPL, 1 PSF
- Zero GPL conflicts
- All Apache 2.0 packages documented in NOTICE.txt

**Build Integration**:
```powershell
# Generate during build
pip-licenses --format=markdown --with-urls > licenses/THIRD_PARTY_LICENSES.txt
# PyInstaller bundles entire licenses/ directory
```

## 6. Dependency Exclusion

### Decision: Exclude Test/Dev Dependencies

**Excluded from Production Build**:
- `pytest` + plugins (~15MB)
- `playwright` (~30MB)
- `pip-tools`, `pip-licenses` (~5MB)
- Total savings: **~50MB** (50% size reduction)

**PyInstaller Configuration**:
```python
# app.spec
excludes = ['pytest', 'playwright', 'pluggy', 'pip_tools', 'coverage']
```

**Verification**: Build script MUST verify excluded packages not imported at runtime

## 7. Update Mechanism Technical Details

### Architecture

**Update Check** (non-blocking, <2s):
```python
# On app launch
threading.Thread(target=check_for_updates, daemon=True).start()
# Queries: https://api.github.com/repos/owner/repo/releases/latest
```

**Update Download**:
```python
# User clicks "Update Now"
1. Download ZIP from release asset URL
2. Extract to temp directory
3. Verify checksums (if provided)
4. Launch updater.exe with paths
5. Exit app.exe
```

**Updater Logic**:
```python
# updater.exe (minimal dependencies)
1. Wait for app.exe process to exit (timeout 10s)
2. Backup old app.exe → app.exe.bak
3. Move new app.exe from temp → install dir
4. Launch new app.exe
5. Clean up temp files
6. Exit
```

**Error Handling**:
- Network failures → silent fail, retry next launch
- Download corruption → keep current version, show error
- Updater failure → restore from .bak file

## 8. Browser Auto-Launch Implementation

### Technical Approach

**Module**: Python `webbrowser` standard library

**Code**:
```python
import webbrowser
import socket

def launch_app():
    # Get free port
    port = get_free_port()
    
    # Start Waitress server (non-blocking)
    server = threading.Thread(target=start_server, args=(port,), daemon=True)
    server.start()
    
    # Wait for server ready (max 3s)
    wait_for_server(port, timeout=3)
    
    # Open browser
    url = f"http://127.0.0.1:{port}"
    try:
        webbrowser.open(url)
        print(f"✓ Browser opened: {url}")
    except Exception as e:
        print(f"⚠ Auto-launch failed: {e}")
    
    # Always display URL
    print(f"\nApp running at: {url}")
    print("Press Ctrl+C to stop")
```

**Terminal Behavior**:
- Remains visible throughout app lifecycle
- Displays status messages (server started, URL)
- Captures Ctrl+C for graceful shutdown
- Closing terminal → kills app process

## 9. Code Signing

### Decision: Optional Initially, Required for Production

**Certificate**: Windows Authenticode (EV certificate recommended)

**Tool**: `signtool.exe` (Windows SDK)

**Command**:
```powershell
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com /fd SHA256 app.exe
```

**Benefits**:
- Reduces Windows SmartScreen warnings
- Builds user trust
- Required for automatic updates (some systems)

**Phase 1**: Build without signing (testing)
**Phase 2**: Acquire certificate and integrate into CI/CD

## 10. Portable Installation

### Implementation

**Database Path Resolution**:
```python
# data/database.py
import os

def get_db_path():
    # Detect if running from executable
    if getattr(sys, 'frozen', False):
        # PyInstaller executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running from source
        app_dir = os.path.dirname(__file__)
    
    return os.path.join(app_dir, 'profiles', 'burndown.db')
```

**Behavior**:
- First run: Creates `profiles/` directory next to executable
- Subsequent runs: Loads from same `profiles/` directory
- Move executable → database moves with it
- Multiple installations → separate databases (no conflicts)

**User Data Structure**:
```
BurndownChart_v2.5.0/
├── app.exe
├── updater.exe
├── licenses/
│   └── [license files]
└── profiles/
    └── burndown.db (created on first run)
```

## 11. Splash Screen & Initialization

### Decision: Minimal Loading Screen

**Implementation**: Dash `loading_state` component

**Display**:
- Logo or "Burndown Chart" text
- Progress spinner
- "Initializing database..." message
- Max duration: 3 seconds

**Why Not Native Splash**:
- PyInstaller splash support is basic (static images only)
- Dash provides better control over loading UX
- Can show actual progress (database migration, etc.)
- Consistent with web app experience

**Code**:
```python
# ui/splash.py
def render_splash():
    return dbc.Container([
        html.Div([
            html.H1("Burndown Chart"),
            dbc.Spinner(),
            html.P("Initializing...")
        ])
    ], className="splash-screen")
```

## Dependencies Added

**Build Tools**:
- `pyinstaller>=6.0.0` (latest stable)
- Already have: `pip-licenses>=5.0.0`, `pip-tools==7.4.1`

**Runtime** (no new dependencies):
- All required dependencies already in requirements.txt
- Updater uses standard library only (no additional deps)

## Risk Assessment

| Risk                           | Mitigation                             |
| ------------------------------ | -------------------------------------- |
| Antivirus false positives      | Code signing certificate               |
| Large executable size (>100MB) | Exclude test deps, use UPX compression |
| Update failures                | Rollback mechanism (.bak file)         |
| License compliance errors      | Automated verification in build script |
| Browser launch failures        | Hybrid approach with terminal fallback |
| Windows version compatibility  | Target Windows 10+ (95% coverage)      |

## Next Steps (Phase 1)

1. Generate data-model.md (minimal - mostly build config entities)
2. Generate contracts/ (GitHub Release API schema)
3. Generate quickstart.md (developer build guide)
4. Update agent context with PyInstaller, packaging patterns
5. Re-evaluate Constitution Check (should still pass)

---

**Research Status**: ✅ Complete - All 11 investigations documented above. Ready for Phase 1 (Design & Contracts).
