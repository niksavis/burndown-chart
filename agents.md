# Agent Instructions - Beads Workflow

## Purpose

Concise operational rules for multi-agent coordination and beads workflow. Repository-specific rules live in [repo_rules.md](repo_rules.md). Architecture rules live in [docs/architecture/readme.md](docs/architecture/readme.md).

## Codebase Metrics

**Last Updated**: 2026-02-05

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | 633 | 203.8K | **~1.8M** |
| Code (Python + JS/CSS) | 427 | 147.3K | ~1.3M |
| Python (no tests) | 346 | 135.0K | ~1.2M |
| Frontend (JS/CSS) | 81 | 12.3K | ~83.3K |
| Tests | 134 | 39.6K | ~348.3K |
| Documentation (MD) | 72 | 17.0K | ~137.4K |

**Agent Guidance**:
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 134 test files (20% of codebase)


## Visual Design (Required)

- Never use emoji-style icons in CLI output or logs.
- Use small Unicode symbols: ○ ◐ ● ✓ ❄.

## Session Start (Mandatory)

1. Confirm venv activation in the shell before Python commands.
2. Sync beads-metadata worktree.
3. Find ready work.
4. Optionally sync main.

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
bd create "Title" --description="Context" -p 1-4 -t bug|feature|task --json
bd close <id> --reason "Done" --json
```

Rules:

- Always include `--description` when creating beads.
- Do not use `bd edit`.
- Beads metadata lives in `.git/beads-worktrees/beads-metadata/` and must be pushed.

## Beads Conflict Resolution (Required)

If `.beads/issues.jsonl` has conflicts:

```powershell
Push-Location .git\beads-worktrees\beads-metadata
git show :1:.beads\issues.jsonl > beads.base.jsonl
git show :2:.beads\issues.jsonl > beads.ours.jsonl
git show :3:.beads\issues.jsonl > beads.theirs.jsonl
bd merge beads.merged.jsonl beads.base.jsonl beads.ours.jsonl beads.theirs.jsonl --debug
Copy-Item beads.merged.jsonl .beads\issues.jsonl
git add .beads\issues.jsonl
git merge --continue
Remove-Item beads.*.jsonl
Pop-Location
```

## Code Creation Prerequisite

Before any file change:

1. Read architecture guidelines for the language.
2. Check file size threshold (80% rule).
3. If threshold exceeded, create a new file.
4. Run `get_errors` after changes.

## Commit Rules (Mandatory)

- Format: `type(scope): description (bd-XXX)`
- Close bead before push.

## Session End (Landing Sequence)

Complete only when both main and beads-metadata are pushed.

1. Create beads for unfinished work.
2. `get_errors` and tests pass (if code changed).
3. Close bead, commit.
4. Push main.
5. Push beads-metadata.
6. Hand off: `Continue work on bd-X: [title]. [context]`.

```powershell
git pull --rebase
git push
Push-Location .git\beads-worktrees\beads-metadata
git pull --rebase
git push
Pop-Location
```
