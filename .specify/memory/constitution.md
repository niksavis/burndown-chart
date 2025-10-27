<!--
Sync Impact Report:
- Version: N/A → 1.0.0 (Initial ratification - streamlined to essentials only)
- Principles: 3 core architectural principles (removed environment setup and UX guidelines)
- Removed: Windows PowerShell setup (→ README), Mobile-First specifics (→ design docs), tool choices
- Rationale: Constitution should contain ONLY blocking architectural constraints, not setup guides or preferences
- Templates requiring updates: None (initial constitution creation)
- Follow-up: Monitor layered architecture and test isolation in code reviews
-->

# Burndown Chart Generator Constitution

## Core Principles

### I. Layered Architecture (NON-NEGOTIABLE)

**Rule**: Business logic MUST reside in the `data/` layer. Callbacks in `callbacks/` MUST only handle events and delegate to data layer functions.

**Rationale**: Dash callbacks become untestable when they contain logic. Separation enables unit testing, reusability, and clear responsibility boundaries.

**Verification**: Code review MUST reject callbacks with calculations, API calls, or data transformations. All logic functions MUST have corresponding unit tests in `tests/unit/data/`.

### II. Test Isolation (NON-NEGOTIABLE)

**Rule**: Tests MUST NOT create files in project root directory. All file operations MUST use `tempfile.TemporaryDirectory()` or `tempfile.NamedTemporaryFile()` with proper cleanup via pytest fixtures.

**Rationale**: File pollution causes test interdependencies, race conditions in parallel execution, and workspace contamination.

**Verification**: All test files creating `app_settings.json`, `project_data.json`, or `jira_cache.json` MUST be flagged in code review. Use `pytest --random-order` to detect isolation violations.

### III. Performance Budgets (NON-NEGOTIABLE)

**Rule**: Initial page load < 2 seconds. Chart rendering < 500ms. User interactions < 100ms response time.

**Rationale**: Performance budgets prevent regressions and impact architectural decisions (caching, lazy loading, data structure choices).

**Verification**: Performance tests in `tests/` MUST validate these targets. Violations require profiling data and justification before merge.

## Data Architecture

**Persistence**: Application state persists to JSON files (`app_settings.json`, `project_data.json`, `jira_cache.json`).

**Code Organization**:
- `callbacks/` - Event handlers only (delegate to data layer)
- `data/` - Business logic, API calls, persistence, calculations
- `ui/` - Component rendering
- `visualization/` - Chart generation
- `configuration/` - Constants and settings

## Testing Requirements

Unit tests MUST be written during implementation. Integration and performance tests MAY be written after feature completion.

## Governance

This constitution supersedes conflicting guidance. All code changes MUST comply with Core Principles I-III.

Amendments MUST increment version per semantic versioning: MAJOR (principle removal/redefinition), MINOR (new principle), PATCH (clarifications).

Reference `.github/copilot-instructions.md` for detailed implementation patterns, environment setup, tool choices, and troubleshooting.

**Version**: 1.0.0 | **Ratified**: 2025-10-27 | **Last Amended**: 2025-10-27
