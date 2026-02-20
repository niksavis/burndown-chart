---
name: "plotly-visualization-quality"
description: "Improve chart correctness and rendering performance"
---

# Skill: Plotly Visualization Quality

Use for `visualization/` chart updates and plot performance tuning.

## Objectives

- Preserve metric correctness.
- Improve chart render responsiveness.
- Keep visualization concerns isolated from data fetching logic.

## Workflow

1. Identify chart inputs and expected metrics.
2. Apply targeted chart logic changes in `visualization/` only.
3. Validate axis/series labels and data correctness.
4. Report performance implications and validation outcomes.

## Guardrails

- Do not move business calculations into callbacks or UI layers.
- Keep chart updates deterministic and testable.
- Avoid adding hard-coded customer-specific labels/data.
