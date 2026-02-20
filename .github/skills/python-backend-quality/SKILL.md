---
name: "python-backend-quality"
description: "Improve quality and reliability of Python backend changes in burndown-chart"
---

# Skill: Python Backend Quality

Use this skill when working in `callbacks/`, `data/`, `visualization/`, or related Python backend code.

## Goals

- Reduce defects and regressions.
- Keep implementation aligned with repository architecture.
- Deliver minimal, validated changes quickly.

## Workflow

1. Build a file context map for the requested change.
2. Apply minimal edits that preserve architecture boundaries.
3. Verify diagnostics with `get_errors`.
4. Run targeted tests for modified behavior where available.
5. Report concrete outcomes and any residual risk.

## Enforcement points

- `callbacks/` may route only; business logic lives in `data/`.
- Type hints required (except Dash callbacks/test fixtures).
- Parameterized SQL only.
- No emoji in code/logging/comments.
- No customer data or credentials in code, logs, or tests.

## Suggested validations

- `get_errors` for changed files.
- `pytest tests/unit/ -v` when unit-level behavior changes.
