<!--
Sync Impact Report:
- Version: 1.2.1 → 1.3.0 (Added Core Principle V: Data Privacy & Security)
- Principles: 4 → 5 core architectural principles
- Updated: Added comprehensive data privacy requirements
- Updated: Added verification criteria for sensitive data
- Rationale: Formalize data protection practices to prevent customer data exposure
- Templates requiring updates: None
- Follow-up: Review all existing code for compliance with new privacy principle
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

**Verification**: All test files creating `app_settings.json`, `project_data.json`, `jira_cache.json`, `jira_changelog_cache.json`, `jira_query_profiles.json`, `metrics_snapshots.json`, or `task_progress.json` MUST be flagged in code review. Use `pytest --random-order` to detect isolation violations.

### III. Performance Budgets (NON-NEGOTIABLE)

**Rule**: Initial page load < 2 seconds. Chart rendering < 500ms. User interactions < 100ms response time.

**Rationale**: Performance budgets prevent regressions and impact architectural decisions (caching, lazy loading, data structure choices).

**Verification**: Performance tests in `tests/` MUST validate these targets. Violations require profiling data and justification before merge.

### IV. Simplicity & Reusability (KISS + DRY)

**Rule**: Keep implementations simple (KISS). Avoid duplication - extract shared logic to reusable functions (DRY).

**Rationale**: Complex code is harder to test and maintain. Duplication creates multiple sources of truth and increases bug surface area.

**Verification**: Code review MUST reject over-engineered solutions or copy-pasted logic. Shared utilities MUST be extracted to appropriate modules with unit tests.

### V. Data Privacy & Security (NON-NEGOTIABLE)

**Rule**: Customer-identifying information MUST NEVER be committed to the repository. All examples, documentation, and configuration MUST use generic placeholder data.

**Rationale**: Public repositories expose sensitive information. Data breaches damage trust, violate privacy obligations, and can have legal consequences.

**Verification**: Code review MUST reject commits containing:
- Real company or organization names
- Production domain names or URLs
- Customer-specific JIRA field IDs (e.g., customfield_XXXXX with actual production values)
- Production environment identifiers
- Real user data, credentials, or API tokens
- Comments referencing specific customer implementations

**Required Practices**:
- Use placeholder names: "Acme Corp", "Example Organization"
- Use placeholder domains: "example.com", "example.org"
- Use generic field IDs: "customfield_10001", "customfield_10002"
- Document patterns, not specific customer configurations
- Review git history before pushing to ensure no sensitive data exposure

## Data Architecture

**Persistence**: Application state persists to JSON files:
- `app_settings.json` - PERT config, deadline, JIRA config, field_mappings (DORA/Flow)
- `project_data.json` - Statistics, scope, metrics_history (snapshots)
- `jira_cache.json` - JIRA API responses (24hr TTL)
- `jira_changelog_cache.json` - JIRA changelog data cache
- `jira_query_profiles.json` - Saved JQL queries
- `metrics_snapshots.json` - Weekly DORA/Flow metric snapshots
- `task_progress.json` - Runtime task progress tracking

**Code Organization**:
- `callbacks/` - Event handlers only (delegate to data layer)
- `data/` - Business logic, JIRA API, metrics calculators (DORA/Flow), persistence
- `ui/` - Component rendering (dashboards, modals, metric cards)
- `visualization/` - Chart generation (burndown, DORA/Flow trends)
- `configuration/` - Constants, settings, metric definitions

## Testing Requirements

Unit tests MUST be written during implementation. Integration and performance tests MAY be written after feature completion.

## Governance

This constitution supersedes conflicting guidance. All code changes MUST comply with Core Principles I-V.

Amendments MUST increment version per semantic versioning: MAJOR (principle removal/redefinition), MINOR (new principle), PATCH (clarifications).

Reference `.github/copilot-instructions.md` for detailed implementation patterns, environment setup, tool choices, and troubleshooting.

**Version**: 1.3.0 | **Ratified**: 2025-10-27 | **Last Amended**: 2025-11-09
