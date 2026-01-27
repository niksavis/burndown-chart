# Release Process

**Target**: Windows standalone executables | **Stack**: Python 3.13, PyInstaller, PowerShell

## Quick Reference

```powershell
# ALWAYS activate venv FIRST (MANDATORY)
.venv\Scripts\activate

# Local build (full sequence)
.\build\collect_licenses.ps1  # → licenses/THIRD_PARTY_LICENSES.txt
.\build\build.ps1             # → dist/BurndownChart.exe (~101 MB)
.\build\package.ps1           # → dist/BurndownChart-Windows-{version}.zip

# Automated release (venv must be active)
python release.py [patch|minor|major]  # Version bump → changelog → metrics → push → triggers CI

# Update codebase metrics (venv must be active)
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
- [ ] **Activate venv**: `.venv\Scripts\activate` (MANDATORY - do this FIRST)
- [ ] Dev dependencies installed (`pip install -r requirements-dev.txt` - needed for PyYAML)
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Feature branch merged to main
- [ ] All changes committed and pushed to main
- [ ] Working directory clean (`git status`)

**Changelog Creation** (BEFORE release.py):

```powershell
# Step 1: Preview unreleased commits and generate draft
python regenerate_changelog.py --preview --json

# This creates changelog_draft.json with:
# - All commits since last tag (v2.7.10..HEAD)
# - Grouped by scope/issue
# - Categorized (Features, Bug Fixes, etc.)

# Step 2: Use LLM to write polished changelog
# Prompt: "Read changelog_draft.json and write a user-friendly changelog 
#          section for v2.7.11. Focus on what users can DO, bold major
#          features (**Feature**), flat bullets only (no sub-bullets)."

# Step 3: Copy LLM output to TOP of changelog.md
# Format:
#   ## v2.7.11
#   *Released: 2026-01-26*
#   
#   ### Features
#   - **Major Feature**: Description inline with details
#   - Enhancement: Description
#   
#   ### Bug Fixes
#   - Fixed issue preventing X from Y

# Step 4: Commit changelog BEFORE running release.py
git add changelog.md
git commit -m "docs(changelog): add v2.7.11 release notes"
git push
```

**Version Bump** (Automated - venv must be active):

```powershell
python release.py [patch|minor|major]
```

**What release.py does**:
1. Preflight checks (clean working dir, on main branch)
2. Bump version in configuration/**init**.py and readme.md
3. Commit version changes: "chore: bump version to X.Y.Z"
4. Call regenerate_changelog() - **SKIPS** if vX.Y.Z already in changelog.md
5. Check if changelog.md changed - **NO AMEND** if changelog already committed
6. Regenerate version_info.txt and version_info_updater.txt (bundled in executables)
7. Commit version_info files: "chore(build): update version_info files for release"
8. Update codebase metrics in agents.md (auto-commits: "docs(metrics): update codebase metrics")
9. **Create final release commit**: "Release vX.Y.Z" (empty commit, tag points here)
10. **Create git tag** (points to release commit - GitHub Actions shows clean message)
11. Push main branch and tag to origin → **triggers GitHub Actions**

**Post-Release**:
- [ ] GitHub Actions workflow completes successfully
- [ ] GitHub release created with ZIP attached
- [ ] Release notes extracted from changelog.md (matching version section)
- [ ] Download ZIP → test executable → verify version in About dialog
- [ ] Verify success toast appears after update (if testing update flow)

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

**Purpose**: Generate changelog entries from git commit history

**Modes**:

1. **Preview Mode (RECOMMENDED for releases)**:
   ```powershell
   python regenerate_changelog.py --preview --json
   ```
   - Shows unreleased commits since last tag (v2.7.10..HEAD)
   - Creates `changelog_draft.json` for LLM processing
   - Use BEFORE running release.py
   - Enables manual polish before committing

2. **Post-Tag Mode (fallback)**:
   ```powershell
   python regenerate_changelog.py --json
   ```
   - Generates entries for NEW tags not in changelog.md
   - Use if you forgot to create changelog before release
   - Requires force-moving tag after editing

**Format rules**: 
- Flat bullets only (no sub-bullets - About dialog limitation)
- Bold major features: `**Feature Name**`
- Focus on user benefits, not technical details
- Inline details: `**Feature**: Description with all details inline, comma-separated`

**Recommended Workflow**:

```powershell
# Step 0: Activate venv (MANDATORY)
.venv\Scripts\activate

# Step 1: Ensure all work committed and pushed
git status                              # Should be clean
git pull --rebase                       # Get latest

# Step 2: Preview unreleased commits
python regenerate_changelog.py --preview --json

# Step 3: Use LLM to write changelog
# Prompt: "Read changelog_draft.json and write v2.7.11 changelog.
#          Bold major features, flat bullets only, user-friendly."

# Step 4: Add LLM output to TOP of changelog.md
# Format:
#   ## v2.7.11
#   *Released: 2026-01-26*
#   
#   ### Features
#   - **Major Feature**: Complete description inline
#   
#   ### Bug Fixes
#   - Fixed specific issue

# Step 5: Commit changelog BEFORE release.py
git add changelog.md
git commit -m "docs(changelog): add v2.7.11 release notes"
git push

# Step 6: Run automated release
python release.py patch

# What happens:
# - release.py calls regenerate_changelog()
# - Script checks changelog.md for "## v2.7.11"
# - Found → SKIPS regeneration
# - No amend needed
# - Creates tag pointing to correct commit
# - Pushes everything
```

**Fallback Workflow** (if forgot to create changelog):

```powershell
# After running release.py (tag already exists):

# Step 1: Generate from existing tag
python regenerate_changelog.py --json

# Step 2: Polish generated entries in changelog.md

# Step 3: Amend commit
git add changelog.md
git commit --amend --no-edit

# Step 4: Force-move tag to amended commit
git tag -f v2.7.11

# Step 5: Force push
git push origin main v2.7.11 --force
```

---

## Troubleshooting

**Build**: ModuleNotFoundError → `pip install -r requirements.txt pyinstaller>=6.0.0 pip-licenses>=5.0.0 pillow>=10.0.0`

**Package**: ZIP wrong location → verify dist/BurndownChart.exe exists, check version in configuration/**init**.py

**GitHub Actions**: Workflow not triggering → verify tag format `v*` (not `2.6.0`), check .github/workflows/release.yml on main

**Runtime**: Missing deps → add to hiddenimports in build/app.spec, rebuild

**Version mismatch**: Tag ≠ executable version → release.py ensures correct order (bump → regenerate version_info.txt)

**Orphaned tag** (tag points to wrong commit):
```powershell
# Symptoms: GitHub Actions builds wrong code, executable has old bugs

# Fix:
git push origin :refs/tags/v2.7.11           # Delete remote tag
git tag -d v2.7.11                           # Delete local tag
git tag v2.7.11 <correct-commit-hash>        # Recreate on correct commit
git push origin v2.7.11                      # Push corrected tag
```

**Forgot to write changelog before release**:
```powershell
# Tag already exists but changelog missing/incomplete

# Option 1: Force-move tag (if release not yet downloaded by users)
python regenerate_changelog.py --json        # Generate from tag
# Edit changelog.md to polish
git add changelog.md
git commit --amend --no-edit                 # Amend into version bump
git tag -f v2.7.11                           # Force-move tag
git push origin main v2.7.11 --force         # Force push

# Option 2: Skip to next version (if release already public)
# - Leave v2.7.11 as-is
# - Create v2.7.12 with proper changelog
```

**Success toast not appearing after update**:
```powershell
# Check app.log for errors in /api/version endpoint
# Check JavaScript console for fetch errors
# Verify post_update_relaunch flag in database:
sqlite3 "D:\Utilities\Burndown Chart\profiles\burndown.db" "SELECT * FROM app_state WHERE key='post_update_relaunch';"
# Should be empty or "True" after update, cleared after toast shown
```

---

**Resources**: build/ (scripts), build/*.spec (PyInstaller), .github/workflows/release.yml, release.py
