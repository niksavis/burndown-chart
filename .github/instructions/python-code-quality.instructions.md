---
applyTo: '**/*.py'
description: 'Python coding conventions, readability, and reliability rules for burndown-chart'
---

# Python Code Quality Instructions

Apply these rules for Python changes.

## Core Rules

- Prioritize readability and clear intent over cleverness.
- Use descriptive names and explicit type hints for function parameters/returns.
- Keep docstrings concise and useful (PEP 257 style).
- Keep functions focused; split complex functions into smaller helpers.
- Handle edge cases explicitly (empty input, invalid types, missing keys, boundary values).

## Style and Structure

- Follow PEP 8 and repository architecture guidance.
- Use 4-space indentation and consistent import grouping.
- Prefer modern typing syntax (`list[str]`, `dict[str, Any]`, `X | None`) for Python 3.13.
- Prefer context managers for files/resources and deterministic cleanup.
- Use specific exceptions; avoid bare `except` and silent failure paths.

## Import Rules

- All imports must be at file top level, ordered: stdlib → third-party → local.
- Never import inside a function body. PLC0415 (`import` inside function) is enforced
  by ruff and is a blocking violation in all source files outside `tests/`.
- The ONLY exception: an approved circular-break wrapper function with `# noqa: PLC0415`
  on both the `def` line and the inner `from` line, plus a docstring naming the cycle.
- Never add `# noqa: PLC0415` to a plain function-body import without the wrapper
  structure. If you feel you need to, consult the `circular-import-safety` skill first.
- `data/jira/*.py` must use `import logging; logger = logging.getLogger(__name__)`
  instead of `from configuration import logger` to avoid a known startup cycle.

## Repository-Specific Constraints

- `callbacks/` should route only; business logic belongs in `data/`.
- Keep SQL parameterized in persistence and data layers.
- Do not log secrets, tokens, credentials, or customer-identifying data.
- No emoji in Python code, logging, or comments.

## Validation

1. Run `get_errors` on changed Python files.
2. Run targeted tests for changed behavior when available.
3. If tests are skipped, state why.
