# Agent Instructions - Compatibility Shim

## Purpose

This file is a lightweight compatibility bootstrap for external agents (for example, Claude Code or Codex CLI) that may not automatically load `.github/copilot-instructions.md`.

## Source of Truth

- Canonical always-on policy: `.github/copilot-instructions.md`.
- Repository-specific coding/workflow rules: `repo_rules.md`.
- Architecture standards: `docs/architecture/readme.md` and language guideline files.

Do not duplicate policy text here. Keep this file concise and operational.

## Loading Strategy

- VS Code Copilot agents: rely on `.github/copilot-instructions.md` and conditional instructions under `.github/instructions/`.
- External agents: load this file first, then load `.github/copilot-instructions.md` for canonical policy.

## Orchestration Bootstrap (External Agents)

For non-trivial implementation tasks, external agents should follow the orchestration policy in `.github/copilot-instructions.md`:

1. Route to specialized subagents first.
2. Run read-only discovery in parallel only when independent.
3. Run edits/tests/validation in sequence.
4. End with quality gate checks.

If specialized patterns are discovered during implementation, run the self-evolving loop:

- Use `.github/agents/custom-agent-foundry.agent.md` to add/update subagents.
- Use `.github/instructions/agent-skills.instructions.md` + `.github/skills/make-skill-template/SKILL.md` to add/update skills.
- Update `.github/copilot_customization.md` and `.github/copilot_capability_map.md`.

## External Agent Quick Start

```powershell
bd daemon status
Push-Location .git\beads-worktrees\beads-metadata
git pull --rebase
Pop-Location
bd ready --json
git pull --rebase
```

## Beads Commands

```powershell
bd ready --json
bd show <id> --json
bd update <id> --status in_progress
bd create "Title" --description="Context" -p 0-4 -t bug|feature|task --json
bd close <id> --reason "Done" --json
```

Rules:

- Always include `--description` when creating beads.
- Never use `bd edit`.
- Beads metadata lives in `.git/beads-worktrees/beads-metadata/` and must be pushed.

## Dependency Onboarding Rule

For any new Python package, perform onboarding explicitly:

```powershell
# Runtime dependency
# 1) Edit requirements.in
pip-compile requirements.in
pip install -r requirements.txt

# Development dependency
# 1) Edit requirements-dev.in
pip-compile requirements-dev.in
pip install -r requirements-dev.txt
```

Never edit compiled requirement files directly.

## Non-Interactive Command Rule

Use `-Force` for file operations to avoid interactive hangs:

```powershell
Copy-Item -Force source dest
Move-Item -Force source dest
Remove-Item -Force file
Remove-Item -Recurse -Force dir
```

## Session End (External Agents)

Do not finish until both main and beads metadata are pushed:

```powershell
git pull --rebase
git push
Push-Location .git\beads-worktrees\beads-metadata
git pull --rebase
git push
Pop-Location
git status
```
