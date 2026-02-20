# Layering Warn-Only Hooks

Warn-only hook pack that reminds contributors to preserve burndown layered architecture.

## Scope

- Trigger on changes under `callbacks/`, `data/`, `ui/`, `visualization/`.
- Emit guidance-only reminders; no automatic file modification.

## Messages

- Keep callbacks as routing delegates only.
- Keep business logic and persistence orchestration in data.
- Keep charts in visualization and layout/component assembly in ui.
