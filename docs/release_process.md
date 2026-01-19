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
python release.py [patch|minor|major]  # Regenerates version_info.txt → bump → push → triggers CI
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
- [ ] `changelog.md` polished (v{X.Y.Z} section with release date)

**Version Bump** (Automated):

```powershell
python release.py [patch|minor|major]
```

**What it does**:
1. Preflight checks (clean working dir, on main)
2. Bump version in configuration/**init**.py and readme.md
3. Commit version changes
4. Create git tag ("Release v{X.Y.Z}")
5. Regenerate changelog from git history (requires PyYAML)
6. Commit changelog (amend)
7. Regenerate version_info.txt AND version_info_updater.txt (bundled in executables)
8. Commit version_info files
9. Push to origin → triggers GitHub Actions

**Post-Release**:
- [ ] GitHub release created with ZIP attached
- [ ] Release notes show polished changelog (not "Unreleased - In Development")
- [ ] Download ZIP → test executable → verify version in About dialog

---

## Changelog Generation

`release.py` automatically regenerates changelog from git commit history.

**Format rules**: Flat bullets only (no sub-bullets), bold major features, focus on user benefits

---

## Troubleshooting

**Build**: ModuleNotFoundError → `pip install -r requirements.txt pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0`

**Package**: ZIP wrong location → verify dist/BurndownChart.exe exists, check version in configuration/**init**.py

**GitHub Actions**: Workflow not triggering → verify tag format `v*` (not `2.6.0`), check .github/workflows/release.yml on main

**Runtime**: Missing deps → add to hiddenimports in build/app.spec, rebuild

**Version mismatch**: Tag ≠ executable version → release.py ensures correct order (bump → regenerate version_info.txt)

---

**Resources**: build/ (scripts), build/*.spec (PyInstaller), .github/workflows/release.yml, release.py
