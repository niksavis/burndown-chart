# Burndown - AI Agent Guide

**Stack**: Python 3.13, Dash, Plotly, Waitress | **DB**: SQLite | **Platform**: Windows

## Core Axioms (Non-Negotiable)

1. **VENV**: Before any Python command, activate the virtual environment in the same shell.
2. **ZERO ERRORS**: `get_errors` must be clean after every change and before commit.
3. **ARCH GUIDES FIRST**: Consult docs/architecture before any code edit.
4. **LAYERING**: callbacks/ routes only; data/ holds logic; ui/ renders; visualization/ charts.
5. **NO CUSTOMER DATA**: Never commit real names, domains, IDs, or credentials.
6. **TEST ISOLATION**: Use tempfile.TemporaryDirectory() in tests.
7. **NO EMOJI**: Avoid emoji in code/logs/comments. Exception: emoji are allowed in documentation files (`.md`) only.
8. **TERMINAL STATE**: Each terminal run is isolated; activation does not persist.
9. **SELF-HEALING DOC**: If this file is wrong, inform → propose → update.
10. **COMMITS**: Conventional commit + bead ID required.

## Venv Rule (Formal)

If running any Python command:

- Required pattern (PowerShell): `.venv\Scripts\activate; <python command>`
- Required pattern (bash): `source .venv/bin/activate && <python command>`

Applies to: python scripts, pytest, pip install, release.py, regenerate_changelog.py, all .py.

## Architecture Guides (Required)

**Check before any code change**: docs/architecture/<language>\_guidelines.md

| Language   | Max File       | Max Function | Key Document                                                              |
| ---------- | -------------- | ------------ | ------------------------------------------------------------------------- |
| Python     | 500 lines      | 50 lines     | [python_guidelines.md](../docs/architecture/python_guidelines.md)         |
| JavaScript | 400 lines      | 40 lines     | [javascript_guidelines.md](../docs/architecture/javascript_guidelines.md) |
| HTML       | 300 lines      | N/A          | [html_guidelines.md](../docs/architecture/html_guidelines.md)             |
| CSS        | 500 lines      | N/A          | [css_guidelines.md](../docs/architecture/css_guidelines.md)               |
| SQL        | 50 lines/query | N/A          | [sql_guidelines.md](../docs/architecture/sql_guidelines.md)               |

**Discoverability**:

- Repository rules: [repo_rules.md](../repo_rules.md)
- Architecture index: [docs/architecture/readme.md](../docs/architecture/readme.md)
- Release process: [docs/release_process.md](../docs/release_process.md)

**Enforcement**: If file > 80% of limit → create a new file; do not append.

## Layered Architecture (Required)

- callbacks/ → event handling only; delegate to data/
- data/ → business logic, API calls, calculations, persistence orchestration
- ui/ → component builders and layout assembly
- visualization/ → plotting logic

## Code Standards (Required)

- **Type hints**: all functions must have annotations (except Dash callbacks and test fixtures).
- **Naming**: snake_case.py, PascalCase, snake_case(), UPPER_CASE.
- **Logging**: follow docs/LOGGING_STANDARDS.md; never log sensitive data.
- **Performance**: page < 2s, charts < 500ms, interactions < 100ms.
- **Windows**: PowerShell only; no bash utilities.

## Security and Data Safety

- Parameterized SQL only.
- Validate user input and external API responses.
- Use safe placeholders: Acme Corp, example.com, customfield_10001.

## Terminal Behavior (Critical)

- Each terminal run is a new shell; activation does not persist.
- Background process + new command in same terminal can terminate the process.

## Commit Rules (Mandatory)

- Format: type(scope): description (bd-XXX)
- Types: feat | fix | docs | style | refactor | perf | test | build | ci | chore
- Bead ID is required and must be at end of first line.

## Branch Strategy

Ask: "Create feature branch or work on main?" before implementing.

## Release Process (Required)

1. Activate venv.
2. Generate changelog draft: python regenerate_changelog.py --preview --json
3. Update changelog.md with release notes (flat bullets, user benefits, bold major features).
4. Commit changelog before release.py.
5. Run release.py patch|minor|major (preferred).

release.py updates version files, regenerates version info, updates agents.md metrics, commits, tags, and pushes.

## Beads Workflow (Required)

- Close bead before push.
- Beads metadata lives in separate worktree and must be pushed.
- Always include --description when creating beads.

## Testing

- Unit tests during implementation.
- Use Playwright, not Selenium.
- Run: pytest tests/unit/ -v
- Coverage: pytest --cov=data --cov=ui --cov-report=html

## Documentation Index

- Metrics: docs/dashboard_metrics.md, docs/dora_metrics.md, docs/flow_metrics.md
- Architecture: docs/caching_system.md, docs/namespace_syntax.md
- Guides: docs/defensive_refactoring_guide.md, docs/LOGGING_STANDARDS.md
- Index: docs/readme.md, docs/metrics_index.md

## Version

**Version**: 2.4.0 | **Condensed**: 2026-02-04 | Target: <1200 tokens
