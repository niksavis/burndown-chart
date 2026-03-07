---
agent: 'agent'
description: 'Run a strict self-review against burndown quality and safety rules before pushing to main'
---

This project uses trunk-based development — there are no PRs.  Perform a
self-review for the current working tree before pushing to `main`.  The
pre-push hook will run `python validate.py` automatically, but this prompt
checks the higher-level concerns that automated tools cannot catch.

Checklist:

- Zero diagnostics in changed files (`get_errors`).
- No architecture violations across `callbacks/`, `data/`, `ui/`, `visualization/`.
- No emoji in code/logs/comments.
- Type hints present where required.
- No secrets or customer data introduced.
- Tests run for touched behavior (or explicit reason why not).
- Commit message format readiness: `type(scope): description (bd-XXX)`.
- Changes are minimal and do not include unrelated refactors.
- Performance targets not regressed (page <2s, chart <500ms, interaction <100ms).

Return:

- PASS/FAIL per checklist item
- File-level findings
- Concrete remediation actions for all FAIL items
