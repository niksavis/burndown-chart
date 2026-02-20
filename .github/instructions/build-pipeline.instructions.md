---
applyTo: 'build/**/*,release.py,regenerate_changelog.py,pyproject.toml,build_config.yaml'
description: 'Enforce safe build pipeline and packaging changes'
---

# Build Pipeline Instructions

Apply these rules when changing build scripts, release automation, or packaging configuration.

## Core principles

- Build scripts must be idempotent (safe to run multiple times)
- Never modify version files manually (use release.py)
- Test build in clean environment before committing
- Keep build deterministic (no random/timestamp-based logic except version info)

## Key files

### Build scripts

- `build/build.ps1` - Main build orchestration
- `build/package.ps1` - Packaging logic
- `build/sign_executable.ps1` - Code signing
- `build/collect_licenses.ps1` - License aggregation
- `build/generate_version_info.py` - Windows PE version info
- `build/generate_icon.py` - Icon generation

### Specs

- `build/app.spec` - PyInstaller spec for main app
- `build/updater.spec` - PyInstaller spec for updater

### Config

- `build/build_config.yaml` - Build configuration
- `pyproject.toml` - Project metadata and versioning

### Release automation

- `release.py` - Version bumping and release flow
- `regenerate_changelog.py` - Changelog generation

## Guardrails

### Version management

- NEVER manually edit version in pyproject.toml or version files
- ALWAYS use `release.py patch|minor|major` to bump versions
- Release.py updates: pyproject.toml, changelog.md, version_info.txt, git tag
- Version format: semver (X.Y.Z)

### Build environment

- PowerShell only (no bash commands)
- Virtual environment must be activated (`.venv\Scripts\activate`)
- Clean build: remove dist/, build/ before building
- Signing: optional, skip if no certificate configured

### Testing builds

```powershell
# Clean build test
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
.venv\Scripts\activate
python -m PyInstaller build/app.spec
.\dist\Burndown.exe --version  # Verify
```

### Dependency management

- Add deps to requirements.in (not requirements.txt)
- Regenerate: `pip-compile requirements.in`
- Vendor deps tracked in vendor_dependencies.txt
- Report deps tracked in report_dependencies.txt

## Before completion

1. Verify build succeeds in clean environment
2. Check executable runs and shows correct version
3. Confirm no regression in app startup time
4. Run `get_errors` on changed files
5. If release.py changed, test version bump flow (dry-run mode if available)

## Related artifacts

- `.github/skills/release-management/SKILL.md` - Release workflow
- `.github/instructions/release-workflow.instructions.md` - Release standards
- `docs/release_process.md` - Full release documentation
- `build/signing.md` - Code signing setup
