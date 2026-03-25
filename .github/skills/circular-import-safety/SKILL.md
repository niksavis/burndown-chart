---
name: circular-import-safety
description: 'Detect, diagnose, and safely resolve circular Python import cycles in burndown-chart. Use when you see ImportError at startup, are about to add a new cross-module import, are refactoring module structure, get a PLC0415 ruff violation, or need to decide whether a lazy import is justified. Covers known cycle map, decision tree, approved wrapper pattern, structural fix protocol, and validation commands.'
---

# Skill: Circular Import Safety

Use this skill before adding any new import that crosses architectural layers, when
restructuring modules, or whenever a PLC0415 lint violation appears in source code.

---

## Decision Tree: Should I use a lazy import?

```
Q: I need to import X from module Y inside a function or at module level.
       |
       v
Does moving the import to module top cause an ImportError or startup crash?
   NO  --> Move it to module top. Done. (PLC0415 rule enforced by ruff.)
   YES --> You have a circular import. Do NOT suppress it silently.
              |
              v
       Can the cycle be broken by restructuring? (Extract shared interface,
       move shared logic to a third module, apply dependency inversion.)
            YES --> Do the structural fix. This is the preferred solution.
            NO  --> Use the approved lazy wrapper pattern (see below).
                    DOCUMENT the cycle in the wrapper docstring.
                    Add # noqa: PLC0415 ONLY to that wrapper.
```

**If you are considering `# noqa: PLC0415` anywhere in source code**: stop and
re-read this decision tree. The lint rule exists precisely to force this decision.

---

## Known Import Cycles in This Codebase

These cycles are real, documented, and intentionally guarded. Do not re-introduce
module-level imports across these boundaries.

### Cycle 1: persistence ↔ jira (primary cycle)

```
data.persistence.__init__
  → data.persistence.adapters.__init__
    → data.persistence.adapters.legacy_data
      → data.jira.*              ← any data/jira/*.py
          → data.persistence.*   ← CYCLE back to persistence
```

**Consequence**: any `data/jira/*.py` file that imports from `data.persistence`
at module top will crash the interpreter with a partial-init ImportError.

**Guard**: `data/jira/*.py` files that need `get_backend`, `load_app_settings`, or
`save_app_settings` MUST use the lazy wrapper function pattern.

### Cycle 2: configuration ↔ jira

```
configuration.*
  → data.persistence.*
    → data.jira.*
      → configuration.*    ← CYCLE
```

**Consequence**: `from configuration import logger` inside `data/jira/*.py` creates
a startup cycle.

**Guard**: All `data/jira/*.py` files MUST use `import logging; logger =
logging.getLogger(__name__)` instead of `from configuration import logger`.
This is not a lazy import workaround — it is the structurally correct approach.

### Cycle 3: metrics ↔ metrics_calculator (internal metrics cycle)

```
data.metrics.__init__
  → data.metrics._weekly_flow
    → data.metrics_snapshots
      → data.metrics_calculator
        → data.metrics.*     ← CYCLE
```

**Guard**: `data/metrics_snapshots.py` uses lazy wrapper functions for
`calculate_forecast`, `calculate_trend_vs_forecast`, `calculate_flow_load_range`.

### Cycle 4: ui.metric_cards ↔ flow_metrics_dashboard

```
ui.metric_cards.__init__
  → ui.metric_cards._helpers
    → ui.flow_metrics_dashboard
      → ui.metric_cards.*    ← CYCLE
```

**Guard**: `ui/metric_cards/_helpers.py` uses a lazy wrapper for
`_get_flow_performance_tier`.

---

### Cycle 5: configuration.metrics_config ↔ data.metrics

```
configuration.metrics_config
  → data.persistence.factory       (if imported at module level)
    → data.__init__
      → data.metrics.weekly_calculator
        → configuration.metrics_config  ← CYCLE (partial init)
```

**Consequence**: `from data.persistence.factory import get_backend` at
module level in `configuration/metrics_config.py` crashes collection of
any test that imports through the `configuration` or `data` package chain.

**Guard**: Use the lazy wrapper function pattern for `get_backend` in
`configuration/metrics_config.py`. Never promote this import to module level.

---

## Approved Lazy Wrapper Pattern

When a structural fix is deferred, use this exact pattern. Never use bare
`from X import Y` inside a function without the wrapper structure.

```python
def get_backend():  # noqa: PLC0415
    """Lazy wrapper: breaks circular data.jira -> data.persistence."""
    from data.persistence.factory import (  # noqa: PLC0415
        get_backend as _get_backend,
    )
    return _get_backend()
```

Rules for the wrapper:
- Function must be at module top level (not nested).
- The `# noqa: PLC0415` comment belongs on the `def` line AND the `from` line.
- Docstring must name the specific cycle being broken.
- The function name must match the imported name (or be clearly aliased).
- Callers use `get_backend()` identically to the original import.

---

## Forbidden Patterns

```python
# FORBIDDEN: Bare lazy import inside a function body (no structural reason)
def some_function():
    from data.foo import bar   # PLC0415 violation with no justification

# FORBIDDEN: noqa without explanation
from data.persistence import load_app_settings  # noqa: PLC0415

# FORBIDDEN: Suppressing the cycle symptom without documenting it
import importlib
bar = importlib.import_module("data.foo").bar
```

---

## Detection Commands

### Fast startup smoke test (catches circular imports at interpreter init)

```bash
.venv/Scripts/python.exe -c "from callbacks import register_all_callbacks; print('OK')"
```

If this raises `ImportError: cannot import name 'X' from partially initialized
module 'Y'` — you have a new circular import cycle.

### Lint enforcement check (catches lazy imports missed by review)

```bash
.venv/Scripts/python.exe -m ruff check . --select PLC0415
```

Source files outside `tests/` must report zero violations (all existing guards
already have `# noqa: PLC0415`). A new violation means a new unapproved lazy import.

### Combined pre-edit safety check

Run both before touching any cross-module import:

```bash
.venv/Scripts/python.exe -m ruff check . --select PLC0415
.venv/Scripts/python.exe -c "from callbacks import register_all_callbacks; print('OK')"
```

Run both again after the edit. Both must still pass.

---

## Structural Fix Protocol (Preferred over wrappers)

When the codebase evolves to the point where a cycle can be broken cleanly:

1. Identify the shared dependency causing the cycle.
2. Extract it to a third module with no upstream imports (`data/shared/`, or a
   `_types.py` / `_constants.py` file).
3. Both sides of the cycle import from the new neutral module.
4. Remove the lazy wrapper function.
5. Remove the `# noqa: PLC0415` suppressions.
6. Run smoke test + lint check to confirm clean state.

Example: If `data.jira` and `data.persistence` both need `AppSettings`, extract
`AppSettings` to `data.settings_types` (imports nothing from either module).

---

## Pre-edit Checklist

Before adding any new import between modules in different layers:

- [ ] Did I check if the target module is in a known cycle boundary above?
- [ ] Did I try moving the import to module top first?
- [ ] If that causes ImportError: did I document the cycle before suppressing?
- [ ] Did I run the smoke test after the edit?
- [ ] Did I run `ruff check --select PLC0415` and see zero new violations?
- [ ] Is the `# noqa: PLC0415` justified by a wrapper docstring or guard comment?
