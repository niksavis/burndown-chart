---
applyTo: "tests/**/*.py,data/**/*.py,callbacks/**/*.py"
description: "Require targeted tests and isolation for behavior changes"
---

# Testing Quality

When behavior changes, apply these testing rules:

- Prefer targeted tests first, then broader suite only if needed.
- Use `tempfile.TemporaryDirectory()` for filesystem isolation in tests.
- Do not write test artifacts to project root, `profiles/`, `logs/`, or `cache/`.
- Keep tests deterministic (no real network or external customer data).
- If no test is added for changed behavior, state explicit reason.

Validation checklist:

1. Run targeted tests for touched modules.
2. Ensure diagnostics are clean with `get_errors`.
3. Report what was validated and what was not.
