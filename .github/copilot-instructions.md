# Burndown Chart - AI Agent Guide

**Stack**: Python 3.13, Dash, Plotly, Waitress | **DB**: SQLite | **Platform**: Windows

## NON-NEGOTIABLE RULES

### 1. Zero Errors Policy

- Run `get_errors` after every change
- Fix ALL errors before commit (zero tolerance)
- Pre-commit: `get_errors` → fix → verify → commit

### 2. Layered Architecture

- `callbacks/` → event handling ONLY, delegate to `data/`
- Never implement logic in callbacks
- `data/` → business logic, API calls, calculations

### 3. KISS + DRY + Boy Scout

- KISS: Simplify, early returns, break functions >50 lines
- DRY: Extract duplicates (3+ blocks) → helpers
- Boy Scout: Every change improves codebase (remove dead code, add type hints, fix smells)

### 4. No Customer Data

- NEVER commit: real company names, domains, JIRA field IDs, credentials
- Use: "Acme Corp", "example.com", "customfield_10001"

### 5. Test Isolation

- Tests MUST use `tempfile.TemporaryDirectory()`, never project root

### 6. No Emoji

- NEVER use emoji (encoding issues, breaks grep)

### 7. Terminal Management

- If app running, open NEW terminal for other commands

### 8. Self-Healing Documentation

- On discovering errors in `copilot-instructions.md`: INFORM → PROPOSE → UPDATE
- Mathematically condense rules: minimum context, maximum clarity
- Remove redundancy, preserve all rules

### 9. Conventional Commits with Beads Tracking (MANDATORY)

- Format: `type(scope): description (bd-XXX)`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
- **MUST include bead ID** in parentheses at end of first line
- Enables `bd doctor` to detect orphaned issues and provides AI traceability

**Examples**:

```bash
# Single task (hierarchical)
git commit -m "feat(build): add PyInstaller to requirements (burndown-chart-016.1)"

# Multiple related tasks (list all in first line)
git commit -m "feat(build): create project structure (burndown-chart-016.2, 016.3, 016.4)"

# Bug fix (hash ID)
git commit -m "fix(data): resolve circular import in frozen exe (burndown-chart-6np)"

# Extended body for context
git commit -m "feat(update): add auto-reconnect overlay (bd-xmc)

Implemented WebSocket reconnection overlay that polls server every 2s
during app restart/update. Shows 'Reconnecting...' message until app
available. Prevents duplicate browser tabs after updates."
```

**Why Both**:

- Conventional commits → changelog generation
- Bead ID in parentheses → `bd doctor` tracking and AI traceability
- Footer body (optional) → detailed context for complex changes

---

## Architecture

- `callbacks/` Event handling → delegate to data/
- `data/` Business logic, JIRA API, persistence
- `ui/` Component rendering (Dash Bootstrap)
- `visualization/` Plotly charts
- `configuration/` Constants, settings
- **DB**: `profiles/burndown.db` (12 tables)

## Key Entry Points

- `app.py` - Entry, initialization, migration
- `ui/layout.py` - Main layout
- `callbacks/__init__.py` - Callback hub
- `data/persistence/` - SQLite backend
- `data/jira_query_manager.py` - JIRA API (not jira_simple.py)

## Code Standards

- **Naming**: `snake_case.py`, `PascalCase`, `snake_case()`, `UPPER_CASE`
- **Type Hints**: All functions MUST have annotations
- **Logging**: Follow `docs/LOGGING_STANDARDS.md`, never log customer data/credentials
- **Performance**: Page <2s, charts <500ms, interactions <100ms
- **Windows**: PowerShell only (no `grep`, `find`, `cat`)

---

## Version Control

**Branch Strategy**: Ask user "Create feature branch or work on main?" before implementing.

**Release Process** (CRITICAL):

1. **Polish changelog FIRST** (create v{X.Y.Z} section with release date in `changelog.md`)
2. **Automated** (recommended): `python release.py [patch|minor|major]`
3. **Manual**: `python build/generate_version_info.py` → commit → `python bump_version.py` → push with tags

**release.py automates**:

- Regenerates `build/version_info.txt` (bundled in executable)
- Calls `bump_version.py` (which calls `regenerate_changelog.py`)
- Recreates tag with consistent message: "Release v{X.Y.Z}"
- Pushes to trigger GitHub Actions

**Changelog Rules**:

- FLAT BULLETS ONLY (no sub-bullets - About dialog cannot render)
- Focus on user benefits, not technical details
- Bold major features: `**Feature Name**`

**Self-Review Checklist**:

- [ ] Code conventions followed
- [ ] No debug code
- [ ] `pytest tests/ -v` passes
- [ ] `get_errors` returns zero errors
- [ ] No sensitive data

---

## Development Workflow (Spec-Kit + Beads)

1. Specification: `@speckit.specify <feature>` → `specs/<feature>/spec.md`
2. Planning: `@speckit.plan` → research.md, plan.md, contracts/
3. Tasks: `@speckit.tasks` → `specs/<feature>/tasks.md`
4. Import: Create parent feature → `python workflow/tasks_to_beads.py specs/<feature>/tasks.md tasks.jsonl --parent burndown-chart-016; bd import -i tasks.jsonl --rename-on-import; bd sync`
5. Work: `bd ready` → claim → do work → `bd close burndown-chart-016.X --reason "Completed"` → stage all → commit with `(burndown-chart-016.X)` → push
6. Complete: All beads closed → update spec.md → `pytest` → push

**Workflow**: Close bead BEFORE commit (single commit = work + closed status)  
**Commit format**: `feat(scope): description (burndown-chart-XXX)` (traceability, orphan detection)  
**After batch**: `bd sync` (bypass 30s debounce, force immediate export/commit/push)

---

## Testing

- Unit tests during implementation
- Use Playwright (not Selenium)
- Run: `pytest tests/unit/ -v`
- Coverage: `pytest --cov=data --cov=ui --cov-report=html`

---

## Documentation

- **Metrics**: `docs/dashboard_metrics.md`, `docs/dora_metrics.md`, `docs/flow_metrics.md`
- **Architecture**: `docs/caching_system.md`, `docs/namespace_syntax.md`
- **Guides**: `docs/defensive_refactoring_guide.md`, `docs/LOGGING_STANDARDS.md`
- **Index**: `docs/readme.md`, `docs/metrics_index.md`

---

**Version**: 2.3.0 | **Condensed**: 2026-01-17 | Target: <1500 tokens
