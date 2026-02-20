---
agent: "agent"
description: "Run a strict self-review against burndown quality and safety rules"
---

Perform a self-review for the current working tree before merge.

Checklist:

- Zero diagnostics in changed files (`get_errors`).
- No architecture violations across `callbacks/`, `data/`, `ui/`, `visualization/`.
- No emoji in code/logs/comments.
- Type hints present where required.
- No secrets or customer data introduced.
- Tests run for touched behavior (or explicit reason why not).
- Commit message format readiness: `type(scope): description (bd-XXX)`.

Return:

- PASS/FAIL per checklist item
- File-level findings
- Concrete remediation actions for all FAIL items
