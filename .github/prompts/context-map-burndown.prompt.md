---
agent: 'agent'
description: 'Map the smallest set of files needed before implementing a change in burndown-chart'
---

Create a context map for this task in `burndown-chart` before editing code.

Task: ${input:task}

## Output format

1. **Goal summary** (1-2 lines): What is the objective?
2. **Task type** (choose one): bug-fix | feature | refactor | documentation | build | test | config
3. **Candidate files to inspect** (max 10):
   - File path
   - Reason to load
   - Priority (critical | helpful | optional)
4. **Primary edit files** (ordered by edit sequence)
5. **Related artifacts**:
   - Skills to apply (from `.github/skills/`)
   - Instructions to follow (from `.github/instructions/`)
   - Docs to reference (from `docs/`)
6. **Validation strategy**:
   - Commands to run (`get_errors`, `pytest`, etc.)
   - Manual checks (UI verification, browser console, etc.)
7. **Risks and assumptions**

## Context loading strategy

Use the **context routing map** to guide file selection:

- **Python backend**: Load module + `__init__.py` + related callback + tests
- **Frontend/JS**: Load JS file + related CSS + Python callback + UI component
- **Database/persistence**: Load backend + schema + migration + docs
- **JIRA integration**: Load adapter + cache + delegates + docs
- **Charts**: Load chart module + config + data preparation + callback
- **Build/release**: Load build scripts + release.py + docs
- **Updater**: Load updater module + update manager + docs
- **Config**: Load config module + validation + persistence + UI form
- **Tests**: Load test file + source being tested + fixtures
- **Docs**: Load doc + related code for accuracy

Refer to `.github/context-routing-map.md` for detailed file paths.

## Folder-specific guidance

### `callbacks/` changes

- Purpose: Event routing only (no business logic)
- Load: Callback file + delegate in `data/` + UI component in `ui/`
- Validation: Verify delegation pattern, test UI interaction

### `data/` changes

- Purpose: Business logic, API calls, calculations
- Load: Module + `data/__init__.py` + callers (callbacks) + tests
- Validation: Unit tests, `get_errors`, edge cases

### `ui/` changes

- Purpose: Component builders and layout
- Load: Component + styles + callbacks + clientside JS
- Validation: Visual check (desktop + mobile), a11y

### `visualization/` changes

- Purpose: Plotly chart generation
- Load: Chart module + config + data prep + callback
- Validation: Visual check, performance (<500ms), `get_errors`

### `assets/` changes

- Purpose: Clientside callbacks, JS, CSS
- Load: JS/CSS + related UI component + Python callback
- Validation: Browser console, keyboard nav, mobile viewport

### `data/persistence/` changes

- Purpose: Database operations
- Load: Backend + schema + migration + repository pattern
- Validation: Test with clean DB, test with existing data, transactions

### `data/jira/` changes

- Purpose: JIRA API integration
- Load: Adapter + cache ops + delegates + field mapping
- Validation: Test with JIRA API, verify error handling, check logs

### `build/` or `release.py` changes

- Purpose: Build pipeline, versioning, packaging
- Load: Build script + release.py + config + docs
- Validation: Clean build test, version verification

### `updater/` changes

- Purpose: Two-phase update mechanism
- Load: Updater module + update manager + file ops + docs
- Validation: Test update flow, check both success and failure cases

### `configuration/` changes

- Purpose: Config management, defaults, validation
- Load: Config module + validation + persistence + help text
- Validation: Test defaults, test validation, test persistence

### `tests/` changes

- Purpose: Adding or updating tests
- Load: Test file + source being tested + fixtures + conftest
- Validation: Run tests, verify isolation, check coverage

### `docs/` changes

- Purpose: Documentation updates
- Load: Doc file + related code for accuracy + doc index
- Validation: Verify accuracy against code, check links

## Constraints

- Prefer minimal file set and targeted changes
- Respect architecture layers (callbacks → data, ui, visualization)
- Include `get_errors` in validation checks
- Reference `.github/context-routing-map.md` for detailed routing
- Use codebase context metrics for strategy (strict-chunking recommended)
- Load <500 lines per file when possible
