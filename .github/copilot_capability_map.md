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

| Artifact                                                     | Scope (`applyTo`)                                                                                                        | Capability                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `.github/instructions/python-dash-layering.instructions.md`  | `callbacks/**/*.py,data/**/*.py,visualization/**/*.py,ui/**/*.py`                                                        | Enforces layered architecture boundaries                   |
| `.github/instructions/security-data-safety.instructions.md`  | `callbacks/**/*.py,data/**/*.py,ui/**/*.py,visualization/**/*.py,**/*.sql,assets/**/*.js`                                | Enforces no-secrets/no-customer-data and sanitized logging |
| `.github/instructions/testing-quality.instructions.md`       | `tests/**/*.py,data/**/*.py,callbacks/**/*.py`                                                                           | Requires targeted tests and isolation                      |
| `.github/instructions/powershell-python-env.instructions.md` | `**/*.py,tests/**/*.py,release.py,regenerate_changelog.py`                                                               | Enforces PowerShell + venv command pattern                 |
| `.github/instructions/release-workflow.instructions.md`      | `release.py,regenerate_changelog.py,changelog.md,docs/codebase_context_metrics.md,.github/codebase_context_metrics.json` | Standardizes changelog/release flow                        |
| `.github/instructions/review-gate.instructions.md`           | `**/*`                                                                                                                   | Final completion quality gate                              |
| `.github/instructions/review.instructions.md`                | Broad review policy document                                                                                             | Deep review checklist and coding standards                 |

## Skills

| Skill                                                  | Capability                                     | Best fit                             |
| ------------------------------------------------------ | ---------------------------------------------- | ------------------------------------ |
| `.github/skills/python-backend-quality/SKILL.md`       | Python backend quality and layered enforcement | General Python/backend changes       |
| `.github/skills/sqlite-persistence-safety/SKILL.md`    | Safe SQLite and persistence changes            | `data/persistence/`, SQL, migrations |
| `.github/skills/jira-integration-reliability/SKILL.md` | Reliable Jira fetch/cache/error handling       | Jira flows in `data/` + delegates    |
| `.github/skills/plotly-visualization-quality/SKILL.md` | Chart correctness and render performance       | `visualization/` chart work          |
| `.github/skills/release-management/SKILL.md`           | Release/changelog workflow safety              | Release prep and versioning          |

## Custom Agents (Subagents)

| Agent                                           | Capability                                | Best fit                           |
| ----------------------------------------------- | ----------------------------------------- | ---------------------------------- |
| `.github/agents/repo-quality-guardian.agent.md` | Quality/safety gatekeeper                 | End-of-task review and enforcement |
| `.github/agents/layering-enforcer.agent.md`     | Boundary checks and corrections           | Multi-layer Python changes         |
| `.github/agents/test-strategy.agent.md`         | Test planning and focused validation      | Behavior changes needing tests     |
| `.github/agents/release-readiness.agent.md`     | Release checklist and changelog readiness | Pre-release validation             |

## Prompts

| Prompt                                            | Capability                            | Best fit                              |
| ------------------------------------------------- | ------------------------------------- | ------------------------------------- |
| `.github/prompts/context-map-burndown.prompt.md`  | Minimal file context planning         | Start of non-trivial tasks            |
| `.github/prompts/bug-triage-burndown.prompt.md`   | Root-cause + focused bug fix flow     | Bug investigations                    |
| `.github/prompts/safe-refactor-python.prompt.md`  | Behavior-preserving refactor workflow | Python refactors                      |
| `.github/prompts/add-targeted-tests.prompt.md`    | Add isolated targeted tests           | Test additions after behavior changes |
| `.github/prompts/pre-merge-self-review.prompt.md` | PASS/FAIL self review checklist       | Final review before merge             |
| `.github/prompts/release-notes-draft.prompt.md`   | User-focused changelog bullets        | Release notes drafting                |

## Agent Metrics Artifacts

| Artifact                                | Type             | Purpose                                               |
| --------------------------------------- | ---------------- | ----------------------------------------------------- |
| `.github/codebase_context_metrics.json` | Machine-readable | Agent context sizing, chunking strategy, folder focus |
| `docs/codebase_context_metrics.md`      | Human-readable   | Quick operator view of codebase context size guidance |

## Hooks

| Hook pack                                  | Mode           | Capability                                      |
| ------------------------------------------ | -------------- | ----------------------------------------------- |
| `.github/hooks/governance-warn-only/`      | Warn-only      | Session reminders for governance and validation |
| `.github/hooks/governance-strict/`         | Strict profile | Stronger completion gate reminders              |
| `.github/hooks/layering-warn-only/`        | Warn-only      | Layering reminders                              |
| `.github/hooks/layering-strict/`           | Strict profile | Strict layering validation reminders            |
| `.github/hooks/release-hygiene-warn-only/` | Warn-only      | Release/changelog hygiene reminders             |
| `.github/hooks/release-hygiene-strict/`    | Strict profile | Strict release hygiene validation reminders     |

## Task-to-Artifact Routing

- Python feature/bug: `python-backend-quality` skill + `bug-triage-burndown` prompt + layering/testing/security instructions.
- Persistence change: `sqlite-persistence-safety` skill + testing/security instructions.
- Chart change: `plotly-visualization-quality` skill + layering instructions.
- Jira integration change: `jira-integration-reliability` skill + security/testing instructions.
- Refactor: `safe-refactor-python` prompt + `layering-enforcer` agent.
- Release prep: `release-management` skill + `release-readiness` agent + `release-notes-draft` prompt.

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
