# Copilot Customization Inventory

This document indexes the repository Copilot customization artifacts and how to use them.

- Detailed capability map and gap review: [copilot_capability_map.md](./copilot_capability_map.md)

## Precedence

Apply artifacts in this order:

1. Always-on instructions (`.github/copilot-instructions.md`)
2. Conditional instructions (`.github/instructions/*.instructions.md`)
3. Skills (`.github/skills/**/SKILL.md`)
4. Prompts (`.github/prompts/*.prompt.md`)

## Instruction Loading Strategy

- VS Code Copilot: use `.github/copilot-instructions.md` as always-on canonical policy and apply conditional instructions automatically.
- External agents (Claude/Codex CLI): load `agents.md` as a bootstrap, then load `.github/copilot-instructions.md`.
- Keep `agents.md` concise to reduce duplicate context and token usage.

## Orchestration Defaults

- Non-trivial tasks should use orchestrated subagent workflow from `.github/copilot-instructions.md`.
- Parallel work is restricted to independent read-only discovery/research.
- Edits/tests/validation must run in sequence and finish with quality gate checks.
- Self-evolving specialization is required when recurring/novel task patterns are discovered.

## Package Onboarding Policy

- Canonical dependency onboarding workflow is defined in `.github/copilot-instructions.md` under `Dependency Onboarding (Required)`.
- Build/packaging-specific enforcement is defined in `.github/instructions/build-pipeline.instructions.md`.

## Conditional Instructions

- `.github/instructions/python-dash-layering.instructions.md`
- `.github/instructions/security-data-safety.instructions.md`
- `.github/instructions/testing-quality.instructions.md`
- `.github/instructions/context7-refresh.instructions.md`
- `.github/instructions/python-code-quality.instructions.md`
- `.github/instructions/html-css-style-color-guide.instructions.md`
- `.github/instructions/powershell-python-env.instructions.md`
- `.github/instructions/release-workflow.instructions.md`
- `.github/instructions/build-pipeline.instructions.md`
- `.github/instructions/cache-management.instructions.md`
- `.github/instructions/configuration-changes.instructions.md`
- `.github/instructions/review-gate.instructions.md`
- `.github/instructions/review.instructions.md`
- `.github/instructions/authoring.instructions.md`

## Agent Discoverability Artifacts

- `.github/codebase_context_metrics.json` (machine-readable context sizing and task routing)
- `docs/codebase_context_metrics.md` (human-readable companion summary)
- `.github/context-routing-map.md` (comprehensive task-type to file mapping guide)

## Skills

- `.github/skills/python-backend-quality/SKILL.md`
- `.github/skills/context7-retrieval-patterns/SKILL.md`
- `.github/skills/sqlite-persistence-safety/SKILL.md`
- `.github/skills/jira-integration-reliability/SKILL.md`
- `.github/skills/plotly-visualization-quality/SKILL.md`
- `.github/skills/frontend-javascript-quality/SKILL.md`
- `.github/skills/updater-reliability/SKILL.md`
- `.github/skills/release-management/SKILL.md`
- `.github/skills/refactor/SKILL.md`
- `.github/skills/circular-import-safety/SKILL.md` (detect, diagnose, and safely resolve circular Python import cycles)
- `.github/skills/cli-search-tools/SKILL.md` (repo-agnostic; rg, fd, jq, yq patterns for code exploration and structured data querying)
- `.github/skills/beads-schema-repair/SKILL.md` (diagnose and repair Dolt schema mismatches that prevent issue restoration after `bd backup fetch-git`)
- `.github/skills/make-skill-template/SKILL.md` (`disable-model-invocation: true` — invoke explicitly to scaffold new skills)
- `.github/skills/beads-workflow/SKILL.md` (full multi-developer beads lifecycle: fetch before starting, search for duplicates, create with description, export immediately on create/claim/block, auto-export on push)

## Prompts

- `.github/prompts/context-map-burndown.prompt.md`
- `.github/prompts/pre-push-self-review.prompt.md`
- `.github/prompts/bug-triage-burndown.prompt.md`
- `.github/prompts/safe-refactor-python.prompt.md`
- `.github/prompts/documentation-update.prompt.md`
- `.github/prompts/add-targeted-tests.prompt.md`
- `.github/prompts/release-notes-draft.prompt.md`

## Custom Agents

- `.github/agents/beast-mode-agnostic.agent.md`
- `.github/agents/custom-agent-foundry.agent.md`
- `.github/agents/repo-quality-guardian.agent.md`
- `.github/agents/layering-enforcer.agent.md`
- `.github/agents/context7-expert.agent.md`
- `.github/agents/refactor-execution.agent.md`
- `.github/agents/test-strategy.agent.md`
- `.github/agents/release-readiness.agent.md`
- `.github/agents/github-actions-expert.agent.md`
- `.github/agents/critical-thinking.agent.md`

## Agent Configuration Notes

- All agents use dual-model arrays (Codex + Sonnet 4.6). Priority order reflects task fit: Codex-first for execution-heavy tasks, Sonnet-first for reasoning-heavy tasks.
- `disable-model-invocation: true` is set on meta artifacts that should never be auto-spawned as subagents: `critical-thinking`, `custom-agent-foundry`, `make-skill-template`.
- Handoff chain: `refactor-execution` → `repo-quality-guardian` → `test-strategy` → `repo-quality-guardian`.

## Hook Packs

- `.github/hooks/governance-audit/`
- `.github/hooks/session-logger-lite/`
- `.github/hooks/governance-warn-only/`
- `.github/hooks/governance-strict/`
- `.github/hooks/layering-warn-only/`
- `.github/hooks/layering-strict/`
- `.github/hooks/release-hygiene-warn-only/`
- `.github/hooks/release-hygiene-strict/`

## Activation Toggle

Default profile:

- Use warn-only packs during normal development to avoid blocking workflows.
- Add `.github/hooks/governance-audit/hooks.json` for threat-pattern audit logging.
- Add `.github/hooks/session-logger-lite/hooks.json` for session lifecycle logs without prompt body capture.

Strict profile switch:

1. Set governance profile to `.github/hooks/governance-strict/hooks.json` in your local Copilot hook configuration.
2. Set layering profile to `.github/hooks/layering-strict/hooks.json`.
3. Set release hygiene profile to `.github/hooks/release-hygiene-strict/hooks.json`.
4. Keep `.github/hooks/governance-audit/hooks.json` enabled to retain auditable threat signals.
5. If strict enforcement causes false positives, switch back to corresponding warn-only packs and refine strict messages first.

Recommended rollout:

- Pilot strict mode in a small subset of sessions.
- Review outcomes and only then make strict mode your local default.

## Usage Notes

- Keep artifacts focused and non-overlapping.
- Prefer minimal changes and preserve existing behavior.
- Re-run diagnostics after customization updates.
- Update this inventory whenever files are added or removed.
