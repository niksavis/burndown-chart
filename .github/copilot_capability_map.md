# Copilot Capability Map

Purpose: one reviewable map of all Copilot customization artifacts, what each does, and when to use it.

## How to use this map

1. Start with always-on policy.
2. Apply matching conditional instructions by file scope.
3. Choose a skill or custom agent for the task shape.
4. Optionally use a prompt template for repeatable workflows.
5. Enable appropriate hook profile (warn-only or strict).

## Always-on Instructions

| Artifact                          | Role                                               | When to use                                                      |
| --------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------- |
| `.github/copilot-instructions.md` | Canonical always-on repository policy              | Every Copilot session                                            |
| `agents.md`                       | External-agent compatibility shim (bootstrap only) | Claude/Codex CLI sessions that do not auto-load always-on policy |

## Conditional Instructions

| Artifact                                                          | Scope (`applyTo`)                                                                                                        | Capability                                                 |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `.github/instructions/python-code-quality.instructions.md`        | `**/*.py`                                                                                                                | Enforces Python readability, typing, and reliability       |
| `.github/instructions/html-css-style-color-guide.instructions.md` | `**/*.html, **/*.css, assets/**/*.js`                                                                                    | Enforces accessible style and color guidance               |
| `.github/instructions/python-dash-layering.instructions.md`       | `callbacks/**/*.py,data/**/*.py,visualization/**/*.py,ui/**/*.py`                                                        | Enforces layered architecture boundaries                   |
| `.github/instructions/context7-refresh.instructions.md`           | `callbacks/**/*.py,data/**/*.py,ui/**/*.py,visualization/**/*.py,assets/**/*.js,**/*.ts,**/*.tsx,docs/**/*.md`           | Requires fresh Context7 retrieval for external APIs/docs   |
| `.github/instructions/security-data-safety.instructions.md`       | `callbacks/**/*.py,data/**/*.py,ui/**/*.py,visualization/**/*.py,**/*.sql,assets/**/*.js`                                | Enforces no-secrets/no-customer-data and sanitized logging |
| `.github/instructions/testing-quality.instructions.md`            | `tests/**/*.py,data/**/*.py,callbacks/**/*.py`                                                                           | Requires targeted tests and isolation                      |
| `.github/instructions/powershell-python-env.instructions.md`      | `**/*.py,tests/**/*.py,release.py,regenerate_changelog.py`                                                               | Enforces PowerShell + venv command pattern                 |
| `.github/instructions/release-workflow.instructions.md`           | `release.py,regenerate_changelog.py,changelog.md,docs/codebase_context_metrics.md,.github/codebase_context_metrics.json` | Standardizes changelog/release flow                        |
| `.github/instructions/build-pipeline.instructions.md`             | `build/**/*,release.py,regenerate_changelog.py,pyproject.toml,build_config.yaml`                                         | Enforces safe build and packaging changes                  |
| `.github/instructions/cache-management.instructions.md`           | `data/cache_manager.py,data/jira/cache_*.py,data/metrics_cache.py,data/persistence/sqlite/issues_cache.py`               | Enforces safe cache management patterns                    |
| `.github/instructions/configuration-changes.instructions.md`      | `configuration/**/*.py,data/config_validation.py,data/smart_defaults.py`                                                 | Enforces safe configuration management                     |
| `.github/instructions/review-gate.instructions.md`                | `**/*`                                                                                                                   | Final completion quality gate                              |
| `.github/instructions/review.instructions.md`                     | Broad review policy document                                                                                             | Deep review checklist and coding standards                 |

## Skills

| Skill                                                  | Capability                                     | Best fit                             |
| ------------------------------------------------------ | ---------------------------------------------- | ------------------------------------ |
| `.github/skills/context7-retrieval-patterns/SKILL.md`  | Up-to-date external API/doc retrieval workflow | Version-sensitive external libraries |
| `.github/skills/python-backend-quality/SKILL.md`       | Python backend quality and layered enforcement | General Python/backend changes       |
| `.github/skills/sqlite-persistence-safety/SKILL.md`    | Safe SQLite and persistence changes            | `data/persistence/`, SQL, migrations |
| `.github/skills/jira-integration-reliability/SKILL.md` | Reliable Jira fetch/cache/error handling       | Jira flows in `data/` + delegates    |
| `.github/skills/plotly-visualization-quality/SKILL.md` | Chart correctness and render performance       | `visualization/` chart work          |
| `.github/skills/release-management/SKILL.md`           | Release/changelog workflow safety              | Release prep and versioning          |
| `.github/skills/frontend-javascript-quality/SKILL.md`  | Reliable JavaScript/clientside callbacks       | `assets/` JS/CSS changes             |
| `.github/skills/updater-reliability/SKILL.md`          | Safe updater two-phase update flow             | `updater/` system changes            |
| `.github/skills/refactor/SKILL.md`                     | Behavior-preserving refactoring workflow       | Large-file splits and cleanup tasks  |

## Custom Agents (Subagents)

| Agent                                             | Capability                                | Best fit                             |
| ------------------------------------------------- | ----------------------------------------- | ------------------------------------ |
| `.github/agents/context7-bootstrap-sync.agent.md` | Context7 bootstrap and focused doc sync   | Tasks requiring current API truth    |
| `.github/agents/refactor-execution.agent.md`      | Behavior-preserving refactor execution    | Refactor tasks with validation gates |
| `.github/agents/repo-quality-guardian.agent.md`   | Quality/safety gatekeeper                 | End-of-task review and enforcement   |
| `.github/agents/layering-enforcer.agent.md`       | Boundary checks and corrections           | Multi-layer Python changes           |
| `.github/agents/test-strategy.agent.md`           | Test planning and focused validation      | Behavior changes needing tests       |
| `.github/agents/release-readiness.agent.md`       | Release checklist and changelog readiness | Pre-release validation               |

## Prompts

| Prompt                                            | Capability                            | Best fit                              |
| ------------------------------------------------- | ------------------------------------- | ------------------------------------- |
| `.github/prompts/context-map-burndown.prompt.md`  | Minimal file context planning         | Start of non-trivial tasks            |
| `.github/prompts/bug-triage-burndown.prompt.md`   | Root-cause + focused bug fix flow     | Bug investigations                    |
| `.github/prompts/safe-refactor-python.prompt.md`  | Behavior-preserving refactor workflow | Python refactors                      |
| `.github/prompts/add-targeted-tests.prompt.md`    | Add isolated targeted tests           | Test additions after behavior changes |
| `.github/prompts/documentation-update.prompt.md`  | Documentation updates and accuracy    | Documentation changes                 |
| `.github/prompts/pre-merge-self-review.prompt.md` | PASS/FAIL self review checklist       | Final review before merge             |
| `.github/prompts/release-notes-draft.prompt.md`   | User-focused changelog bullets        | Release notes drafting                |

## Agent Metrics Artifacts

| Artifact                                | Type             | Purpose                                               |
| --------------------------------------- | ---------------- | ----------------------------------------------------- |
| `.github/codebase_context_metrics.json` | Machine-readable | Agent context sizing, chunking strategy, task routing |
| `docs/codebase_context_metrics.md`      | Human-readable   | Context size guidance and task-to-folder routing      |
| `.github/context-routing-map.md`        | Agent guide      | Comprehensive task-type to file mapping guide         |

## Hooks

| Hook pack                                  | Mode           | Capability                                      |
| ------------------------------------------ | -------------- | ----------------------------------------------- |
| `.github/hooks/governance-audit/`          | Audit          | Threat-pattern scanning + local governance log  |
| `.github/hooks/session-logger-lite/`       | Lite logger    | Session start/end local JSONL logging           |
| `.github/hooks/governance-warn-only/`      | Warn-only      | Session reminders for governance and validation |
| `.github/hooks/governance-strict/`         | Strict profile | Stronger completion gate reminders              |
| `.github/hooks/layering-warn-only/`        | Warn-only      | Layering reminders                              |
| `.github/hooks/layering-strict/`           | Strict profile | Strict layering validation reminders            |
| `.github/hooks/release-hygiene-warn-only/` | Warn-only      | Release/changelog hygiene reminders             |
| `.github/hooks/release-hygiene-strict/`    | Strict profile | Strict release hygiene validation reminders     |

Recommended baseline composition:

- `governance-warn-only` + `layering-warn-only` + `release-hygiene-warn-only`
- plus `governance-audit` and `session-logger-lite` for local auditability

## Task-to-Artifact Routing

- **Python backend**: `python-backend-quality` skill + `python-code-quality` instruction + `python-dash-layering` instruction + `testing-quality` instruction
- **External API freshness**: `context7-retrieval-patterns` skill + `context7-refresh` instruction + `context7-bootstrap-sync` agent
- **Frontend/JavaScript**: `frontend-javascript-quality` skill + `html-css-style-color-guide` instruction + `security-data-safety` instruction
- **Persistence/Database**: `sqlite-persistence-safety` skill + `cache-management` instruction + `testing-quality` instruction
- **Chart/Visualization**: `plotly-visualization-quality` skill + `python-dash-layering` instruction
- **JIRA integration**: `jira-integration-reliability` skill + `cache-management` instruction + `security-data-safety` instruction
- **Build/Packaging**: `build-pipeline` instruction + `release-management` skill (if release-related)
- **Updater system**: `updater-reliability` skill + `build-pipeline` instruction
- **Configuration**: `configuration-changes` instruction + `security-data-safety` instruction
- **Refactor**: `refactor` skill + `safe-refactor-python` prompt + `refactor-execution` agent + `layering-enforcer` agent + `testing-quality` instruction
- **Release prep**: `release-management` skill + `release-readiness` agent + `release-notes-draft` prompt
- **Documentation (latest guidelines)**: `documentation-update` prompt + `context7-retrieval-patterns` skill + `context7-refresh` instruction + `context7-bootstrap-sync` agent

## Context Loading Optimization

For any non-trivial task:

1. Start with `context-map-burndown` prompt to plan file loading
2. Reference `.github/context-routing-map.md` for task-specific file paths
3. Check `docs/codebase_context_metrics.md` for folder guidance
4. Load files in priority order (critical → helpful → optional)
5. Use `semantic_search` for unknown/exploratory searches

## Gap Review (Current)

### Filled

- All requested artifact categories exist: always-on, conditional instructions, skills, custom agents, prompts, hooks.
- Compatibility split is in place: canonical `.github/copilot-instructions.md` and lean `agents.md` shim.

### Gaps resolved in current pass

1. Hook schema consistency:
   - All hook packs now use the executable `event/run` schema.

2. Missing strict variants:
   - Added strict counterparts for layering and release hygiene.

3. Review instruction metadata:
   - Added frontmatter (`applyTo`, `description`) to `.github/instructions/review.instructions.md`.

### Open optimization opportunity

1. Capability ownership review cadence:
   - Add a recurring checklist for stale artifacts and overlap control.

## Quarterly review checklist

- Verify each artifact still has a clear owner and unique purpose.
- Remove or merge overlapping prompts/skills/agents.
- Validate hook messages still match active governance rules.
- Confirm instruction `applyTo` scopes match current repo structure.
- Run `get_errors` on changed customization files and update this map.

## Maintenance checklist

- Keep this map updated when adding/removing customization artifacts.
- Keep `.github/copilot-instructions.md` canonical and `agents.md` minimal.
- Run `get_errors` on changed docs after updates.
