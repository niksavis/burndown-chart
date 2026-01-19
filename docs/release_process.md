# Release Process

**Target**: Windows standalone executables | **Stack**: Python 3.13, PyInstaller, PowerShell

## Quick Reference

```powershell
# Local build (full sequence)
.\.venv\Scripts\activate
.\build\collect_licenses.ps1  # → licenses/THIRD_PARTY_LICENSES.txt
.\build\build.ps1             # → dist/BurndownChart.exe (~101 MB)
.\build\package.ps1           # → dist/BurndownChart-Windows-{version}.zip

# Automated release
python release.py [patch|minor|major]  # Version bump → changelog → metrics → push → triggers CI

# Update codebase metrics (ad-hoc)
python update_codebase_metrics.py  # → agents.md (auto-commits)
```

---

## Local Build

**Prerequisites**: Windows 10/11, Python 3.13+, activated .venv

**Build commands**:
```powershell
.\build\collect_licenses.ps1   # Scan pip packages → licenses/THIRD_PARTY_LICENSES.txt
.\build\build.ps1 [-VerboseBuild]  # PyInstaller → dist/*.exe (bundles: runtime, deps, assets, licenses, changelog.md)
.\build\package.ps1 [-Version "X.Y.Z"]  # ZIP with: exes, LICENSE.txt, THIRD_PARTY_LICENSES.txt, README.txt
```

**Output**: `dist/BurndownChart-Windows-{version}.zip` (~109 MB)

**Test**:
```powershell
Expand-Archive dist\BurndownChart-Windows-*.zip -DestinationPath C:\Temp\Test
C:\Temp\Test\BurndownChart.exe  # Verify: starts, correct version in About, LICENSE.txt extracted
```

---

## GitHub Actions

**Workflow**: `.github/workflows/release.yml`

**Trigger**: `git push origin v*` (e.g., v2.6.1)

**Process**: Checkout → Python 3.13 setup → deps install → collect licenses → build → package → create release with ZIP

**Test without release**: Use test tag `v{version}-test` → workflow runs → manual cleanup:
```powershell
git tag v2.6.0-test && git push origin v2.6.0-test  # Trigger workflow
git tag -d v2.6.0-test && git push origin :refs/tags/v2.6.0-test  # Delete after verification
```

**Release notes**: Auto-generated from `changelog.md` section matching tag version

---

## CI/CD Integration

**Generic pattern** for GitLab CI/Azure Pipelines/Jenkins:

```yaml
# Windows runner, Python 3.13+
- Install: pip install -r requirements.txt pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0
- Build: .\build\collect_licenses.ps1 && .\build\build.ps1 && .\build\package.ps1
- Artifact: dist/BurndownChart-Windows-*.zip
```

**Environment override**: `$env:VERSION = "X.Y.Z"` before package.ps1

---

## Release Checklist

**Pre-Release**:
- [ ] Dev dependencies installed (`pip install -r requirements-dev.txt` - needed for PyYAML)
- [ ] Tests pass, no errors (`pytest`, `get_errors`)
- [ ] Feature branch merged to main
- [ ] Generate changelog draft: `python regenerate_changelog.py --json` (creates changelog_draft.json)
- [ ] Polish `changelog.md`: Create v{X.Y.Z} section with release date using JSON as reference

**Version Bump** (Automated):

```powershell
python release.py [patch|minor|major]
```

**What it does**:
1. Preflight checks (clean working dir, on main)
2. Bump version in configuration/**init**.py and readme.md
3. Commit version changes
4. Create git tag ("Release v{X.Y.Z}")
5. Regenerate changelog from git history (skips if v{X.Y.Z} already exists - requires PyYAML)
6. Commit changelog (if regenerated)
7. Regenerate version_info.txt AND version_info_updater.txt (bundled in executables)
8. Commit version_info files
9. Update codebase metrics in agents.md (auto-commits)
10. Push to origin → triggers GitHub Actions

**Post-Release**:
- [ ] GitHub release created with ZIP attached
- [ ] Release notes show polished changelog (not "Unreleased - In Development")
- [ ] Download ZIP → test executable → verify version in About dialog

---

## Codebase Metrics

**Script**: `update_codebase_metrics.py`

**Purpose**: Calculates token counts and updates agents.md with codebase statistics for AI agents

**Features**:
- **Dynamic calibration**: Tests 46 representative files to calculate chars-per-token ratio
- **Comprehensive breakdown**: Total, code, tests, docs, Python, frontend
- **Self-contained**: Updates agents.md and auto-commits changes

**Usage**:

```powershell
# Ad-hoc update (anytime)
python update_codebase_metrics.py

# Automatic (during release)
python release.py [patch|minor|major]  # Calls script internally
```

**Output**: Updates "Codebase Metrics" section in agents.md with current counts

---

## Changelog Generation

**Script**: `regenerate_changelog.py`

**Purpose**: Generate comprehensive changelog entries from git commit history

**Workflow**:

1. **Before release**: `python regenerate_changelog.py --json`
   - Creates `changelog_draft.json` with ALL commits since last tag
   - Includes commit message, scope, type, bead ID, description
   - Use as reference to write polished changelog section

2. **During release**: `release.py` calls `regenerate_changelog.py` automatically
   - **SKIPS** if v{X.Y.Z} section already exists in changelog.md
   - Only generates entries for NEW tags not found in changelog

**Format rules**: Flat bullets only (no sub-bullets), bold major features, focus on user benefits

**Example**:
```powershell
# Step 1: Generate draft with all commits
python regenerate_changelog.py --json

# Step 2: Read changelog_draft.json, write polished v2.7.0 section in changelog.md

# Step 3: Run release (changelog regeneration skipped since v2.7.0 exists)
python release.py minor
```

---

## Troubleshooting

**Build**: ModuleNotFoundError → `pip install -r requirements.txt pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0`

**Package**: ZIP wrong location → verify dist/BurndownChart.exe exists, check version in configuration/**init**.py

**GitHub Actions**: Workflow not triggering → verify tag format `v*` (not `2.6.0`), check .github/workflows/release.yml on main

**Runtime**: Missing deps → add to hiddenimports in build/app.spec, rebuild

**Version mismatch**: Tag ≠ executable version → release.py ensures correct order (bump → regenerate version_info.txt)

---

**Resources**: build/ (scripts), build/*.spec (PyInstaller), .github/workflows/release.yml, release.py
