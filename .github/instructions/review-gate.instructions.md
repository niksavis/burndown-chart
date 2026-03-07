---
applyTo: '**/*'
description: 'Final quality gate for implementation and review responses'
---

# Review Gate Instructions

Treat this as the final pass before declaring work complete.

## Required checks

- `get_errors` reports zero errors for changed files.
- Architecture boundaries are respected (`callbacks -> data`, `ui`, `visualization`).
- No emoji in code/logging/comments.
- No real customer data, secrets, tokens, or credentials.
- Changes are minimal, focused, and do not include unrelated refactors.
- If tests exist for touched behavior, run targeted tests first.

## Pre-commit lint gate (required before every commit)

Run in the same shell as venv activation. If any tool is missing, install dev dependencies first.

```powershell
# Ensure Python tools are available (safe to re-run; no-ops if already installed)
pip install -r requirements-dev.txt

# Ensure Node tools are available
npm install

# Lint gate — must all exit 0 before committing
ruff check .
djlint --check report_assets/**/*.html
pyright data/ callbacks/ ui/ visualization/
npx markdownlint-cli2 "**/*.md" "#node_modules" "#.venv" "#build" "#cache" "#logs" "#profiles"
```

If `ruff check` fails, fix violations then re-run before committing.
If `djlint --check` fails, run `djlint --reformat report_assets/**/*.html` then re-run check.
If `pyright` reports errors, fix type annotation issues before committing.
If `markdownlint-cli2` reports errors, fix markdown formatting before committing.

## Response expectations

- Report exactly what changed and where.
- Report what was validated and what could not be validated.
- If any check is skipped, clearly state why.
