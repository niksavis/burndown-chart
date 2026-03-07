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

- Index and usage map: `.github/copilot_customization.md`

## Context Metrics Source

- Machine-readable: `.github/codebase_context_metrics.json`
- Human-readable: `docs/codebase_context_metrics.md`
- Use these artifacts to choose context strategy (`single-pass`, `targeted-chunking`, `strict-chunking`) before broad file reads.

## Core Axioms (Non-Negotiable)

1. **VENV**: Before any Python command, activate the virtual environment in the same shell.
2. **ZERO ERRORS**: `get_errors` must be clean after every change and before commit.
3. **ARCH GUIDES FIRST**: Consult docs/architecture before any code edit.
4. **CONTEXT7**: For any code generation, library/API question, setup, or configuration task — auto-invoke `resolve-library-id` then `query-docs` before implementation. Do not answer from memory. Route to `context7-expert` for version migration, deprecation, or upgrade-impact analysis.
5. **LAYERING**: callbacks/ routes only; data/ holds logic; ui/ renders; visualization/ charts.
6. **NO CUSTOMER DATA**: Never commit real names, domains, IDs, or credentials.
7. **TEST ISOLATION**: Use tempfile.TemporaryDirectory() in tests.
8. **NO EMOJI**: Avoid emoji in code/logs/comments. Exception: emoji are allowed in documentation files (`.md`) only.
9. **TERMINAL STATE**: Each terminal run is isolated; activation does not persist.
10. **SELF-HEALING DOC**: If this file is wrong, inform → propose → update.
11. **COMMITS**: Conventional commit + bead ID required.

## Venv Rule (Formal)

If running any Python command, activate the venv first using the platform-appropriate pattern:

| Platform | Activation pattern |
|---|---|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1; <python command>` |
| macOS / Linux (bash/zsh) | `source .venv/bin/activate && <python command>` |

Alternatively, call the venv interpreter directly (no activation needed):

| Platform | Direct call |
|---|---|
| Windows | `.venv\Scripts\python.exe <args>` |
| macOS / Linux | `.venv/bin/python <args>` |

Applies to: python scripts, pytest, pip install, release.py, regenerate_changelog.py, all .py.

## Architecture Guides (Required)

**Check before any code change**: `docs/architecture/*_guidelines.md`

| Language   | Max File       | Max Function | Key Document                                                              |
| ---------- | -------------- | ------------ | ------------------------------------------------------------------------- |
| Python     | 500 lines      | 50 lines     | `docs/architecture/python_guidelines.md`         |
| JavaScript | 400 lines      | 40 lines     | `docs/architecture/javascript_guidelines.md` |
| HTML       | 300 lines      | N/A          | `docs/architecture/html_guidelines.md`             |
| CSS        | 500 lines      | N/A          | `docs/architecture/css_guidelines.md`               |
| SQL        | 50 lines/query | N/A          | `docs/architecture/sql_guidelines.md`               |

**Discoverability**:

- Repository rules: `repo_rules.md`
- Architecture index: `docs/architecture/readme.md`
- Release process: `docs/release_process.md`

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
- **Platform awareness**: Detect the OS before issuing terminal commands. Windows uses PowerShell (`Get-ChildItem`, `Select-String`, `Copy-Item -Force`). macOS/Linux uses bash/zsh native tools. `validate.py` works on all platforms.
- **Windows local dev**: PowerShell only for local development. No bash utilities.
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
- Architecture/decision trade-offs: `critical-thinking`.
- Creating/updating agent files: `custom-agent-foundry`.

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
- Run `python validate.py` before pushing to catch ruff, djlint, pyright, markdownlint, and test failures in one pass.

## Dependency Onboarding (Required)

- Treat new packages as explicit onboarding work.
- Runtime package workflow:
  1. Add to `requirements.in`
  2. Regenerate `requirements.txt`
  3. Install with `pip install -r requirements.txt`
- Development package workflow:
  1. Add to `requirements-dev.in`
  2. Regenerate `requirements-dev.txt`
  3. Install with `pip install -r requirements-dev.txt`
- Never edit compiled `requirements.txt` or `requirements-dev.txt` by hand.

## Commit Rules (Mandatory)

- Format: type(scope): description (bd-XXX)
- Types: feat | fix | docs | style | refactor | perf | test | build | ci | chore
- Bead ID is required and must be at end of first line.

## Branch Strategy

This project uses **trunk-based development** — `main` is the only long-lived branch
and the primary protection against broken code reaching other developers.

- Local feature or bugfix branches are fine and encouraged for in-progress work.
- Feature branches may be pushed to remote for collaboration.
- Integrate by rebasing onto `main` locally, then push `main` to remote.
- **No remote PRs** between branches — all code review happens locally before push.
- Remote PRs are extremely rare exceptions, not the normal workflow.
- The pre-commit and pre-push git hooks are the primary quality gate before code
  reaches `main` on the remote.

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
