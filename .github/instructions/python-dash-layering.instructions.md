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

Before finishing:

1. Confirm changed code follows the folder responsibility rules above.
2. Confirm no emoji in code/logs/comments.
3. Run error checks and resolve diagnostics before completion.
