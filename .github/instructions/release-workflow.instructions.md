---
applyTo: 'release.py,regenerate_changelog.py,changelog.md,docs/codebase_context_metrics.md,.github/codebase_context_metrics.json'
description: 'Standardize changelog and release workflow behavior'
---

# Release Workflow Instructions

For release-related tasks:

- Activate venv in the same command before Python execution.
- Generate changelog draft first: `python regenerate_changelog.py --preview --json`.
- Update `changelog.md` with flat bullets and user-facing benefits.
- Commit changelog updates before invoking `release.py`.
- Use `release.py patch|minor|major` for version workflow.

Safety checks:

1. Never include credentials/tokens in release notes.
2. Keep release notes concise and user-focused.
3. Preserve existing release process unless explicitly requested.
