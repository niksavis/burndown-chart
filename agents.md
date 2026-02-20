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
