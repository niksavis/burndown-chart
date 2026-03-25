---
applyTo: 'callbacks/**/*.py,data/**/*.py,visualization/**/*.py,ui/**/*.py'
description: 'Enforce burndown layered architecture for Python/Dash changes'
---

# Python Dash Layering Instructions

Apply these rules when editing Python files in this repository:

- `callbacks/` is routing only; delegate all business logic and persistence to `data/`.
- `data/` contains calculations, orchestration, API access, and persistence coordination.
- `visualization/` contains chart generation only.
- `ui/` contains component builders and layout assembly only.
- Keep functions small (target <= 50 lines) and extract shared helpers for repeated logic.
- Add type hints to all functions except Dash callbacks and test fixtures.
- Use parameterized SQL only; never concatenate SQL with user input.
- Never introduce real customer identifiers, domains, tokens, or credentials.

## Import Rules

- All imports MUST be at module top level, ordered: stdlib → third-party → local.
- Importing inside a function body is forbidden unless it is an approved circular-break
  wrapper (PLC0415 is enforced by ruff; any new violation is a blocking defect).
- Never suppress `# noqa: PLC0415` without a wrapper function docstring or
  `# circular import guard` comment that names the specific cycle.

### Forbidden module-level imports (will cause circular import at startup)

These specific cross-module imports MUST remain lazy (wrapper pattern) forever
until the underlying cycle is structurally dissolved:

| File pattern        | Must NOT import at module level              | Use instead                                      |
| ------------------- | -------------------------------------------- | ------------------------------------------------ |
| `data/jira/*.py`    | `from data.persistence import ...`           | Lazy wrapper function                            |
| `data/jira/*.py`    | `from data.persistence.factory import ...`   | Lazy wrapper function                            |
| `data/jira/*.py`    | `from configuration import logger`           | `import logging; logger = logging.getLogger(...)` |
| `data/metrics_snapshots.py` | `from data.metrics_calculator import ...` | Lazy wrapper function                        |
| `ui/metric_cards/_helpers.py` | `from ui.flow_metrics_dashboard import ...` | Lazy wrapper function                      |

### Pre-edit smoke test

Run before and after any change that adds, moves, or removes an import:

```bash
.venv/Scripts/python.exe -c "from callbacks import register_all_callbacks; print('OK')"
.venv/Scripts/python.exe -m ruff check . --select PLC0415
```

Both must pass. A startup crash is a circular import; a new PLC0415 is an
unapproved lazy import. Consult the `circular-import-safety` skill before proceeding.

Before finishing:

1. Confirm changed code follows the folder responsibility rules above.
2. Confirm no emoji in code/logs/comments.
3. Confirm imports are at module top and no new PLC0415 violations exist.
4. Run error checks and resolve diagnostics before completion.
