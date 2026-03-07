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

## Quality Gate (required before every push to main)

This project uses trunk-based development — `main` is the only branch and
there are no PRs.  The pre-push hook runs `python validate.py` automatically.
For ad-hoc manual runs:

```powershell
# Fast check during development (ruff + djlint + pyright)
python validate.py --fast

# Full gate before pushing (adds markdownlint + pytest)
python validate.py

# Auto-fix lint violations, then re-run
python validate.py --fix
```

If any tool is missing, install dev dependencies first:

```powershell
pip install -r requirements-dev.txt
npm install
```

If `ruff` fails, fix violations then re-run.
If `djlint` fails, run `python validate.py --fix` then re-run.
If `pyright` reports errors, fix type issues before committing.
If `markdownlint` reports errors, fix markdown formatting before committing.
If `prettier` fails, run `python validate.py --fix` then re-stage any reformatted files and re-commit before pushing.

## Prettier rule (agent-critical)

Any time `.js`, `.css`, `.json`, `.yml`, or `.yaml` files are created or edited,
run `python validate.py --fix` immediately afterward to auto-apply prettier formatting.
Re-stage and commit the formatted result before pushing.  Skipping this step causes
the GHA `lint.yml` pre-commit hook to fail with "files were modified by this hook".

## Response expectations

- Report exactly what changed and where.
- Report what was validated and what could not be validated.
- If any check is skipped, clearly state why.
