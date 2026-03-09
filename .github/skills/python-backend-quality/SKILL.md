---
name: python-backend-quality
description: 'Improve quality and reliability of Python backend changes in burndown-chart'
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
- All imports at module top level. PLC0415 violations are blocking defects.
- Never add `# noqa: PLC0415` without either a wrapper function docstring or a
  `# circular import guard` comment naming the specific cycle being broken.
- Before any cross-module import change, run:
  `.venv\Scripts\python.exe -c "from callbacks import register_all_callbacks; print('OK')"`
  A startup crash means a new circular import was introduced.
- If you need a lazy import, load the `circular-import-safety` skill first.

## Suggested validations

- `get_errors` for changed files.
- `pytest tests/unit/ -v` when unit-level behavior changes.
