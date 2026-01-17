# Release Process

Comprehensive guide for building and releasing standalone executables for the Burndown Chart application.

## Table of Contents

- [Local Build Process](#local-build-process)
- [GitHub Actions (Automated)](#github-actions-automated)
- [CI/CD Integration](#cicd-integration)
- [Release Checklist](#release-checklist)
- [Troubleshooting](#troubleshooting)

---

## Local Build Process

Build standalone Windows executables locally for testing or manual distribution.

### Prerequisites

- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.13+ ([Download](https://www.python.org/downloads/))
- **Git**: For cloning and version control
- **Virtual Environment**: Activated (.venv)

### Step 1: Environment Setup

```powershell
# Clone repository (if not already done)
git clone https://github.com/niksavis/burndown-chart.git
cd burndown-chart

# Activate virtual environment
.\.venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.13.x

# Install dependencies
pip install -r requirements.txt

# Install build tools
pip install pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0
```

### Step 2: Collect Third-Party Licenses

Generates `licenses/THIRD_PARTY_LICENSES.txt` with all dependency licenses.

```powershell
.\build\collect_licenses.ps1
```

**Output:**
- `licenses/THIRD_PARTY_LICENSES.txt` - Consolidated license list
- `licenses/NOTICE.txt` - Apache 2.0 attribution

**What it does:**
- Scans installed packages with `pip-licenses`
- Generates plain-vertical format with URLs and descriptions
- Creates NOTICE file for Apache 2.0 compliance

### Step 3: Build Executables

Compiles Python code into standalone executables using PyInstaller.

```powershell
.\build\build.ps1
```

**Optional flags:**
- `-VerboseBuild` - Show detailed PyInstaller output

**Output:**
- `dist/BurndownChart.exe` (~101 MB) - Main application
- `dist/BurndownChartUpdater.exe` (~8 MB) - Update utility

**What it does:**
- Runs PyInstaller with `build/app.spec` and `build/updater.spec`
- Bundles Python interpreter, dependencies, assets, licenses
- Creates single-file executables (onefile mode)
- Includes hidden imports, data files (assets/, licenses/, changelog.md)

**Build artifacts bundled:**
- Python 3.13 runtime
- All dependencies from requirements.txt
- `assets/` folder (CSS, JS, images, manifest)
- `licenses/` folder (THIRD_PARTY_LICENSES.txt, NOTICE.txt)
- `LICENSE` (project license - extracted on first run)
- `changelog.md` (for About dialog)

### Step 4: Package Distribution

Creates ZIP file with executables and documentation.

```powershell
.\build\package.ps1
```

**Optional parameters:**
- `-Version "2.5.0"` - Override version (default: reads from configuration/**init**.py)

**Output:**
- `dist/BurndownChart-Windows-{version}.zip` (~109 MB)

**ZIP Contents:**
```
BurndownChart-Windows-2.5.0.zip
├── BurndownChart.exe          # Main application
├── BurndownChartUpdater.exe   # Update utility (optional)
├── LICENSE.txt                # MIT license
├── THIRD_PARTY_LICENSES.txt   # Dependency licenses
└── README.txt                 # Quick start guide
```

**What it does:**
- Verifies build artifacts exist
- Creates staging directory
- Copies executables, licenses, documentation
- Renames LICENSE → LICENSE.txt (Windows convention)
- Compresses to ZIP with optimal compression
- Cleans up staging directory

### Step 5: Test Locally

```powershell
# Extract ZIP to test directory
Expand-Archive -Path dist\BurndownChart-Windows-2.5.0.zip -DestinationPath C:\Temp\BurndownTest

# Run executable
cd C:\Temp\BurndownTest
.\BurndownChart.exe

# Open browser to http://127.0.0.1:8050
# Verify:
# - App starts without errors
# - About dialog shows correct version and changelog
# - LICENSE.txt extracted to exe directory (after first run)
# - JIRA connection works
```

### Complete Build Command Sequence

```powershell
# One-liner for full build
.\.venv\Scripts\activate; .\build\collect_licenses.ps1; .\build\build.ps1; .\build\package.ps1

# Result: dist/BurndownChart-Windows-{version}.zip ready for distribution
```

---

## GitHub Actions (Automated)

Automated build and release workflow triggered by version tags.

### Workflow Overview

**File**: `.github/workflows/release.yml`

**Triggers:**
1. **Tag push**: `git push origin v*` (e.g., v2.5.0)
2. **Manual**: Workflow dispatch (for testing without release)

**Environment:**
- Runner: `windows-latest` (Windows Server 2022)
- Python: 3.13 (cached)
- Build time: ~5-10 minutes

**Steps:**
1. Checkout code (full history for changelog)
2. Setup Python 3.13 with pip cache
3. Install dependencies (requirements.txt + build tools)
4. Collect licenses (`collect_licenses.ps1`)
5. Build executables (`build.ps1`)
6. Verify artifacts
7. Package ZIP (`package.ps1`)
8. Extract version from tag
9. Read changelog for release notes
10. Create GitHub release with ZIP asset

### Testing Workflow Without Publishing

Use a test tag to trigger workflow without creating official release:

```powershell
# Create and push test tag
git tag v2.5.0-test
git push origin v2.5.0-test

# Monitor workflow at:
# https://github.com/niksavis/burndown-chart/actions

# Workflow runs but SKIPS release creation (only creates artifacts)

# Delete test tag after verification
git tag -d v2.5.0-test
git push origin :refs/tags/v2.5.0-test
```

### Creating Official Release

```powershell
# 1. Ensure you're on main branch with latest changes
git checkout main
git pull

# 2. Update version (creates commit + tag)
python bump_version.py patch  # or minor/major

# 3. Push changes AND tag
git push origin main --tags

# 4. GitHub Actions automatically:
#    - Builds executables
#    - Creates release v{version}
#    - Uploads BurndownChart-Windows-{version}.zip
#    - Generates release notes from changelog.md
```

### Release Notes Generation

Workflow automatically creates release notes from `changelog.md`:

**Template structure:**
- Installation instructions (Windows standalone + source)
- First-time setup (JIRA connection)
- What's Changed (extracted from changelog.md for this version)
- Requirements (OS, network, disk space)
- Support links (GitHub Issues)
- License information

**Changelog extraction:**
- Searches for `## v{version}` section in changelog.md
- Extracts content until next version or end of file
- Falls back to full changelog if version section not found

### Workflow Variables

Set in workflow at runtime:
- `VERSION` - Extracted from tag (v2.5.0 → 2.5.0)
- `ZIP_PATH` - Relative path to ZIP (dist/BurndownChart-Windows-{version}.zip)
- `ZIP_NAME` - Filename only
- `CHANGELOG` - Version-specific changelog section

### Manual Trigger (Workflow Dispatch)

For testing without tagging:

1. Go to Actions → Release Build → Run workflow
2. Select branch (016-standalone-packaging for testing)
3. Check "Test mode" (skips release creation)
4. Click "Run workflow"

**Test mode behavior:**
- Runs all build steps
- Generates release notes (saved as artifact)
- SKIPS actual release creation
- Shows summary of what would be released

---

## CI/CD Integration

Integrate into other CI/CD systems (GitLab CI, Azure Pipelines, Jenkins, etc.).

### Generic CI/CD Requirements

**Environment:**
- Windows agent/runner
- Python 3.13+ installed
- PowerShell 5.1+
- Git for cloning

**Build Dependencies:**
```bash
pip install -r requirements.txt
pip install pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0
```

### GitLab CI Example

`.gitlab-ci.yml`:
```yaml
build-windows:
  stage: build
  tags:
    - windows
  script:
    - python -m venv .venv
    - .\.venv\Scripts\activate
    - pip install -r requirements.txt
    - pip install pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0
    - .\build\collect_licenses.ps1
    - .\build\build.ps1
    - .\build\package.ps1
  artifacts:
    paths:
      - dist/BurndownChart-Windows-*.zip
    expire_in: 30 days
  only:
    - tags
```

### Azure Pipelines Example

`azure-pipelines.yml`:
```yaml
trigger:
  tags:
    include:
      - v*

pool:
  vmImage: 'windows-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.13'
    
- script: |
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    pip install pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0
  displayName: 'Install dependencies'

- powershell: |
    .\.venv\Scripts\activate
    .\build\collect_licenses.ps1
    .\build\build.ps1
    .\build\package.ps1
  displayName: 'Build release'

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: 'dist'
    artifactName: 'windows-release'
```

### Jenkins Pipeline Example

`Jenkinsfile`:
```groovy
pipeline {
    agent { label 'windows' }
    
    stages {
        stage('Setup') {
            steps {
                bat '''
                    python -m venv .venv
                    .venv\\Scripts\\activate
                    pip install -r requirements.txt
                    pip install pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0
                '''
            }
        }
        
        stage('Build') {
            steps {
                bat '''
                    .venv\\Scripts\\activate
                    .\\build\\collect_licenses.ps1
                    .\\build\\build.ps1
                    .\\build\\package.ps1
                '''
            }
        }
        
        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'dist/BurndownChart-Windows-*.zip', fingerprint: true
            }
        }
    }
}
```

### Environment Variables

Build scripts respect these environment variables:

- `VERSION` - Override version detection (default: read from configuration/**init**.py)
- `VIRTUAL_ENV` - Virtual environment path (scripts check for venv, fall back to global Python)

Example:
```powershell
$env:VERSION = "2.5.1"
.\build\package.ps1  # Uses 2.5.1 instead of auto-detected version
```

---

## Release Checklist

### Pre-Release

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No type errors (`get_errors` tool in VS Code)
- [ ] Feature branch merged to main
- [ ] `changelog.md` updated with release notes
- [ ] Version in `configuration/__init__.py` matches changelog
- [ ] All beads for release closed

### Local Build Test

- [ ] Build locally: `.\build\collect_licenses.ps1; .\build\build.ps1; .\build\package.ps1`
- [ ] Extract ZIP to temp directory
- [ ] Run `BurndownChart.exe` - starts without errors
- [ ] Check About dialog - version and changelog correct
- [ ] Test JIRA connection
- [ ] Verify LICENSE.txt extracted on first run

### Version Bump

```powershell
# From main branch
git checkout main
git pull

# Bump version (creates commit + tag)
python bump_version.py patch   # 2.5.0 → 2.5.1
python bump_version.py minor   # 2.5.0 → 2.6.0
python bump_version.py major   # 2.5.0 → 3.0.0

# Push to trigger GitHub Actions
git push origin main --tags
```

**What bump_version.py does:**
1. Updates `configuration/__init__.py` (**version** = "X.Y.Z")
2. Creates git commit: "chore(release): bump version to X.Y.Z"
3. Creates annotated git tag: vX.Y.Z
4. Does NOT push (you must push manually)

### GitHub Release Verification

After workflow completes, verify at https://github.com/niksavis/burndown-chart/releases:

- [ ] Release created with correct version tag
- [ ] Release notes show correct changelog section
- [ ] BurndownChart-Windows-{version}.zip attached
- [ ] ZIP size ~109 MB
- [ ] All links work (GitHub Issues, no 404s)
- [ ] JIRA setup instructions correct (no email, generic token instructions)
- [ ] License shows MIT (not Apache 2.0)
- [ ] Requirements mention "Network Access" (not "Internet Connection")

### Distribution Verification

Download and test the released ZIP:

- [ ] Extract to fresh directory
- [ ] ZIP contains: BurndownChart.exe, BurndownChartUpdater.exe, LICENSE.txt, THIRD_PARTY_LICENSES.txt, README.txt
- [ ] ZIP does NOT contain: README.md, LICENSE (without .txt), licenses/ folder
- [ ] Double-click BurndownChart.exe starts app
- [ ] About → App Info shows correct version
- [ ] About → Changelog shows full version history
- [ ] About → Licenses shows all dependencies
- [ ] LICENSE.txt created in exe directory after first run (only one file)

### Post-Release

- [ ] Update release announcement (GitHub Discussions, Discord, etc.)
- [ ] Archive old test releases (delete v*-test tags)
- [ ] Close release milestone in project tracker

---

## Troubleshooting

### Build Failures

**"Virtual environment not activated"**
- Solution: `.\.venv\Scripts\activate` before building
- Build scripts check for venv, fall back to global Python if not found

**"ModuleNotFoundError: No module named 'X'"**
- Solution: `pip install -r requirements.txt` (production) + build tools
- Build tools: `pip install pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0`

**"LICENSE file not found in bundle"**
- Build includes LICENSE at root via app.spec
- Check: `(str(PROJECT_ROOT / 'LICENSE'), '.')` in app.spec datas

**"changelog.md not found in About dialog"**
- Build includes changelog.md via app.spec
- Check: `(str(PROJECT_ROOT / 'changelog.md'), '.')` in app.spec datas
- About dialog reads from sys._MEIPASS in frozen mode

### Package Issues

**"Package not created at: dist/..."**
- Verify build.ps1 succeeded (dist/BurndownChart.exe exists)
- Check version extracted from configuration/**init**.py
- Run with `-Verbose` flag for detailed output

**"ZIP contains wrong files"**
- Check package.ps1 staging logic (lines 100-135)
- Expected: LICENSE.txt (renamed from LICENSE), THIRD_PARTY_LICENSES.txt (copied from licenses/), README.txt (from build/)
- Should NOT include: README.md, LICENSE (no extension), licenses/ folder

### GitHub Actions

**Workflow not triggering**
- Verify tag format: `v*` (e.g., v2.5.0, not 2.5.0)
- Check workflow file: `.github/workflows/release.yml` on main branch
- View Actions tab for workflow runs

**Release not created**
- Check workflow condition: `if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')`
- Manual workflow_dispatch skips release creation (test mode)
- Verify secrets.GITHUB_TOKEN permissions (contents: write)

**ZIP not uploaded**
- Check ZIP_PATH uses relative path (not absolute Windows path)
- Verify ZIP exists at expected location: `dist/BurndownChart-Windows-{version}.zip`
- Check workflow logs for packaging step errors

### Runtime Issues

**"LICENSE.txt not extracted on first run"**
- License extractor runs on app startup (app.py)
- Check frozen detection: `getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")`
- Verify LICENSE bundled: should be at `sys._MEIPASS / "LICENSE"`

**"Changelog not showing in About dialog"**
- Changelog reads from sys._MEIPASS in frozen mode
- Check: `ui/about_dialog.py` lines 668-680 and 725-733
- Verify changelog.md bundled in executable

**"Missing dependencies at runtime"**
- Check hiddenimports in app.spec (line 30+)
- PyInstaller might miss dynamic imports
- Add to hiddenimports list and rebuild

### Version Management

**"Version mismatch between tag and build"**
- Ensure bump_version.py ran successfully
- Verify configuration/**init**.py updated: `__version__ = "X.Y.Z"`
- Check git tag matches: `git tag -l`

**"Old version showing in About dialog"**
- Version read from configuration/**init**.py at build time
- Rebuild with updated version file
- Clear browser cache if testing locally


---

## Changelog Generation Workflow

Burndown Chart uses an incremental changelog system to ensure release notes are accurate and never overwritten. The changelog is generated and updated using the `regenerate_changelog.py` script.

### How to Generate/Update changelog.md

1. **Incremental Update:**
- Run: `python regenerate_changelog.py`
- This will scan all conventional commits since the last tag and append new entries to `changelog.md`.
- Existing release notes are preserved; only new changes are added.

2. **LLM-Assisted Summaries (Optional):**
- Run: `python regenerate_changelog.py --json`
- This creates `changelog_draft.json` with structured commit data for the new version.
- Feed the JSON to an LLM (e.g., Copilot Chat): "Write user-friendly summaries for these versions."
- Copy the LLM output into `changelog.md` for polished release notes.
- Delete `changelog_draft.json` after use (auto-ignored by git).

3. **Best Practices:**
- Always update `changelog.md` before bumping the version and creating a release.
- Never overwrite previous release notes; only add new entries for the current version.
- Use bold formatting for major features and focus on user benefits.

### Changelog in Release Automation

- The GitHub Actions workflow extracts the correct version section from `changelog.md` for release notes.
- If the section is missing, it falls back to the full changelog.
- See `.github/copilot-instructions.md` for detailed changelog workflow.

---

## Additional Resources

- **Build Scripts**: `build/` directory (collect_licenses.ps1, build.ps1, package.ps1)
- **PyInstaller Specs**: `build/app.spec`, `build/updater.spec`
- **GitHub Workflow**: `.github/workflows/release.yml`
- **Version Management**: `bump_version.py`
- **Documentation**: `docs/` directory

---

For questions or issues, see [GitHub Issues](https://github.com/niksavis/burndown-chart/issues).
