<!--
Sync Impact Report:
- Version: 1.4.2 → 1.5.0 (Optimized for conciseness and token efficiency)
- Principles: 6 core architectural principles (unchanged in semantics, condensed in form)
- Updated: Removed redundant details now in copilot-instructions.md, kept governance focus
- Rationale: Constitution is for spec-kit governance, not agent execution. Agent uses copilot-instructions.md
- Templates requiring updates: None
- Follow-up: None
-->

# Burndown Constitution

## Core Principles

### 0. Zero Errors Policy (NON-NEGOTIABLE)

ALL code MUST be error-free before committing. Type errors, linting errors, and runtime errors are prohibited.

**Rationale**: Errors compound technical debt and break builds. Prevention is cheaper than remediation.

**Verification**: Before ANY commit:
1. Run `get_errors` on all modified files
2. Fix ALL errors (zero tolerance)
3. Re-verify with `get_errors`
4. Commit ONLY after zero errors confirmed

**Enforcement**: Commits with errors are FORBIDDEN. No exceptions.

### I. Layered Architecture (NON-NEGOTIABLE)

Business logic MUST reside in `data/` layer. Callbacks in `callbacks/` MUST only delegate to data layer.

**Rationale**: Dash callbacks become untestable when they contain logic. Separation enables unit testing and reusability.

**Verification**: Code review MUST reject callbacks with calculations/API calls/transformations. All logic functions MUST have unit tests in `tests/unit/data/`.

### II. Test Isolation (NON-NEGOTIABLE)

Tests MUST NOT create files in project root. All file operations MUST use `tempfile.TemporaryDirectory()` or `tempfile.NamedTemporaryFile()`.

**Rationale**: File pollution causes test interdependencies and workspace contamination.

**Verification**: Tests MUST use `tempfile` for all file operations. Use `pytest --random-order` to detect violations.

### III. Performance Budgets (NON-NEGOTIABLE)

Page load <2s, chart rendering <500ms, user interactions <100ms.

**Rationale**: Performance budgets prevent regressions and impact architectural decisions.

**Verification**: Performance tests in `tests/` MUST validate these targets.

### IV. Simplicity & Reusability (KISS + DRY)

Keep implementations simple (KISS). Avoid duplication - extract shared logic to reusable functions (DRY).

**Rationale**: Complex code is harder to test and maintain. Duplication creates multiple sources of truth.

**Verification**: Code review MUST reject over-engineered solutions or copy-pasted logic.

### V. Data Privacy & Security (NON-NEGOTIABLE)

Customer-identifying information MUST NEVER be committed. Use placeholder data only.

**Rationale**: Public repositories expose sensitive information.

**Verification**: Code review MUST reject commits containing real company names, production domains, customer JIRA field IDs, credentials, or user data.

**Placeholders**: "Acme Corp", "example.com", "customfield_10001"

### VI. Defensive Refactoring (NON-NEGOTIABLE)

Unused code MUST be removed systematically. All refactoring MUST follow defensive practices with verification.

**Rationale**: Dead code increases maintenance burden and creates false positives.

**Verification**: Before removing any function:
1. Verify zero references across codebase
2. Confirm no callback decorators
3. Check no unit tests reference it
4. Ensure not exported in `__init__.py`
5. Run full test suite before AND after removal
6. Create backup branch
7. Commit incrementally

**Protected Code** (NEVER remove without justification):
- Functions with callback decorators
- Functions registered in `callbacks/__init__.py`
- Public API exports in `__init__.py`
- Functions with unit tests in `tests/unit/`
- Entry point functions in `app.py`, `server.py`

See `docs/defensive_refactoring_guide.md` for procedures.

---

## Data Architecture

**Persistence**: SQLite database at `profiles/burndown.db`

**Tables** (12): profiles, queries, jira_cache, jira_issues, jira_changelog_entries, project_statistics, project_scope, metrics_data_points, budget_revisions, budget_settings, app_state, task_progress

**JSON usage**: Export/import/reports only (not primary storage)

**Code Organization**:
- `callbacks/` - Event handlers only (delegate to data layer)
- `data/` - Business logic, JIRA API, metrics, persistence
- `ui/` - Component rendering (dashboards, cards)
- `visualization/` - Chart generation
- `configuration/` - Constants, settings

**User Data Protection**: All user data in `profiles/` (excluded via `.gitignore`)

---

## Testing Requirements

Unit tests MUST be written during implementation. Integration/performance tests MAY be written after feature completion.

---

## Development Workflow

**Branch Strategy**: AI agent MUST ask before creating feature branch vs main commit.

**Version Management** (CRITICAL sequence):
1. `git checkout main && git merge <feature-branch>`
2. `python bump_version.py [major|minor|patch]` (on main only)
3. `git push origin main --tags`

AI agent MUST verify current branch is main before running bump script.

---

## Governance

This constitution supersedes conflicting guidance. All code changes MUST comply with Core Principles I-VI.

**Amendments**: MAJOR (principle removal/redefinition), MINOR (new principle), PATCH (clarifications).

**Operational Details**: See `docs/` folder. Development standards in `.github/copilot-instructions.md`.

**Version**: 1.5.0 | **Ratified**: 2025-10-27 | **Optimized**: 2026-01-14
