---
applyTo: '**/*.py,tests/**/*.py,release.py,regenerate_changelog.py'
description: 'Enforce PowerShell + venv command patterns for Python tasks'
---

# PowerShell + Python Environment Instructions

When executing Python commands in this repository:

- Use PowerShell command syntax only.
- Activate venv in the same command invocation.
- Preferred pattern: `.venv\\Scripts\\activate; <python command>`.
- Do not assume terminal state persists between commands.
- Avoid bash-only utilities and shell syntax.

If commands fail:

1. Re-check venv activation pattern.
2. Re-run with explicit command and concise diagnostics.
3. Avoid introducing workaround scripts unless requested.
