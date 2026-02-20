---
name: 'refactor'
description: 'Behavior-preserving refactoring guidance for burndown-chart with layered architecture and safety gates'
---

# Skill: Refactor

Use this skill for targeted cleanup of existing code where behavior must remain the same.

## When to use

- A module/function exceeds architecture size limits.
- Callback modules contain business logic that should move to `data/`.
- Code duplication, nested conditionals, unclear naming, or dead code reduces maintainability.
- A user asks for "refactor", "clean up", "split this file", or "make this easier to maintain".

## Core principles

1. Preserve behavior first; improve structure second.
2. Prefer small, reviewable steps over large rewrites.
3. Keep changes minimal and focused on the requested scope.
4. Do not mix feature work with refactoring unless explicitly requested.
5. Validate after each significant step (`get_errors`, then targeted tests).

## Burndown-specific architecture rules

- `callbacks/`: route events only; delegate business logic.
- `data/`: calculations, orchestration, persistence-facing logic.
- `ui/`: component construction and layout assembly.
- `visualization/`: Plotly chart generation/transforms.

If refactoring crosses layers, move logic to the correct layer rather than adding cross-layer shortcuts.

## Safe refactor workflow

1. Map entry points and call sites before edits.
2. Extract one coherent unit at a time (helper, section, or feature group).
3. Keep public signatures stable unless required.
4. Update imports/usages immediately after each extraction.
5. Run validations:
   - `get_errors` on changed files (must be zero)
   - Targeted tests for touched behavior
6. Stop and report if refactor reveals unrelated regressions.

## High-value operations in this repo

- Extract method/function to reduce long functions (target <50 lines for Python functions).
- Split oversized files into focused modules under existing folders.
- Replace deep nesting with guard clauses and early returns.
- Consolidate duplicate logic into shared helpers.
- Rename symbols for clarity while preserving semantics.
- Move callback business logic to `data/` modules.

## Guardrails

- No emoji in code/logging/comments.
- No customer data, tokens, or credentials in code or examples.
- Keep SQL parameterized where applicable.
- Respect existing style and naming conventions.
- Avoid unrelated reformatting and broad churn.

## Validation checklist

- `get_errors` returns zero errors for changed files.
- Changed behavior has targeted test coverage or targeted test run evidence.
- Module boundaries are cleaner after refactor than before.
- Documentation/index artifacts are updated when reusable guidance changes.

## Recommended companions

- `.github/instructions/python-dash-layering.instructions.md`
- `.github/instructions/testing-quality.instructions.md`
- `.github/instructions/review-gate.instructions.md`
- `.github/prompts/safe-refactor-python.prompt.md`
- `.github/agents/layering-enforcer.agent.md`
