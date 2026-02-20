---
applyTo: "**/*"
description: "Final quality gate for implementation and review responses"
---

# Review Gate

Treat this as the final pass before declaring work complete.

## Required checks

- `get_errors` reports zero errors for changed files.
- Architecture boundaries are respected (`callbacks -> data`, `ui`, `visualization`).
- No emoji in code/logging/comments.
- No real customer data, secrets, tokens, or credentials.
- Changes are minimal, focused, and do not include unrelated refactors.
- If tests exist for touched behavior, run targeted tests first.

## Response expectations

- Report exactly what changed and where.
- Report what was validated and what could not be validated.
- If any check is skipped, clearly state why.
