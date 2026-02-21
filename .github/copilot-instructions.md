# Burndown - AI Agent Guide

**Stack**: Python 3.13, Dash, Plotly, Waitress | **DB**: SQLite | **Platform**: Windows

## Copilot Customization Precedence (Canonical)

Apply Copilot customization artifacts in this order:

1. Always-on instructions (`.github/copilot-instructions.md`)
2. Conditional instructions (`.github/instructions/*.instructions.md`)
3. Skills (`.github/skills/**/SKILL.md`)
4. Prompts (`.github/prompts/*.prompt.md`)

When guidance conflicts, higher-precedence artifacts win.

## Canonical Source Policy

- This file is the canonical source for always-on Copilot behavior in this repository.
- `agents.md` is a lightweight cross-tool compatibility shim for environments that do not auto-load this file.
- To avoid context overload, keep policy details here and keep `agents.md` concise with links and operational bootstrap only.
- If behavior changes here, update `agents.md` only when compatibility bootstrap behavior must change.

## Customization Inventory

- Index and usage map: [copilot_customization.md](./copilot_customization.md)

## Context Metrics Source

- Machine-readable: `.github/codebase_context_metrics.json`
- Human-readable: `docs/codebase_context_metrics.md`
- Use these artifacts to choose context strategy (`single-pass`, `targeted-chunking`, `strict-chunking`) before broad file reads.

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

**Check before any code change**: `docs/architecture/*_guidelines.md`

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
- **Simplicity**: Keep implementations simple (KISS). Avoid over-engineering.
- **Reusability**: Extract shared logic to reusable functions (DRY). No duplication.
- **Boy Scout Rule**: Leave touched code and customization artifacts clearer than you found them.

## File Naming (Required)

- Do not use uppercase letters in repository filenames.
- For customization docs under `.github/`, use lowercase names.

## Customization Self-Healing (Required)

When important, reusable guidance is discovered during implementation or review:

1. Update the most specific artifact first (`instructions`/`skills`/`prompts`/`agents`/`hooks`).
2. If guidance affects global behavior, also update this file.
3. Reflect additions/changes in `.github/copilot_customization.md` and `.github/copilot_capability_map.md`.
4. Keep changes minimal and avoid duplicating policy text across files.

## Orchestration Workflow (Required for Non-Trivial Tasks)

For non-trivial implementation tasks (multi-file, refactor, migration, release, cross-layer changes), use an orchestrated workflow instead of ad-hoc execution.

1. **Route first**: Choose specialized agents/skills/instructions before editing.
2. **Parallel phase (read-only only)**: Run independent analysis/research in parallel when safe.
3. **Sequence phase (edits/validation)**: Execute code-editing and validation steps in strict sequence.
4. **Quality gate**: End with repository quality checks (`get_errors`, targeted tests when applicable).

### Parallel vs Sequence Rules

- **Parallel allowed** only for read-only discovery/research (context mapping, doc retrieval, architecture checks).
- **Sequence required** for edits, refactors, tests, and release changes.
- If any parallel branch returns conflicting guidance, resolve conflict in sequence before editing.

### Default Subagent Routing

- External API/version-sensitive tasks: `context7-expert`.
- Layer boundary risks: `layering-enforcer`.
- Behavior-preserving structure work: `refactor-execution`.
- Test planning/updates: `test-strategy`.
- Final completion gate: `repo-quality-guardian`.
- Release readiness: `release-readiness`.

## Self-Evolving Specialization Loop (Required)

When implementation reveals recurring or novel specialized task patterns, evolve the customization set in-session:

1. Detect specialization candidate (repeated workflow, recurring edge cases, repeated manual steps).
2. Decide artifact type:

- New/updated **agent** for workflow orchestration or role behavior.
- New/updated **skill** for reusable domain procedure/resources.
- New/updated **instruction** for scoped policy enforcement.

3. Use `custom-agent-foundry` to create/update specialized subagents.
4. Use `agent-skills.instructions.md` and `make-skill-template` to create/update skills.
5. Wire discoverability updates in `.github/copilot_customization.md` and `.github/copilot_capability_map.md`.
6. Validate with `get_errors` and report what was added and why.

## Security and Data Safety

- Parameterized SQL only.
- Validate user input and external API responses.
- Use safe placeholders: Acme Corp, example.com, customfield_10001.

## Terminal Behavior (Critical)

- Each terminal run is a new shell; activation does not persist.
- Background process + new command in same terminal can terminate the process.

## Dependency Onboarding (Required)

- Treat new packages as explicit onboarding work.
- Runtime package workflow:
  1.  Add to `requirements.in`
  2.  Regenerate `requirements.txt`
  3.  Install with `pip install -r requirements.txt`
- Development package workflow:
  1.  Add to `requirements-dev.in`
  2.  Regenerate `requirements-dev.txt`
  3.  Install with `pip install -r requirements-dev.txt`
- Never edit compiled `requirements.txt` or `requirements-dev.txt` by hand.

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

release.py updates version files, regenerates version info, updates codebase context metrics artifacts, commits, tags, and pushes.

## Beads Workflow (Required)

- **ALWAYS** include `--description` when creating beads (issues without descriptions lack context).
- **NEVER** use `bd edit` (opens interactive editor that agents cannot use).
- Close bead before push.
- Beads metadata lives in separate worktree and must be pushed.

## Priority System

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

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
