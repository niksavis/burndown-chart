# Agent Instructions - Beads Workflow

## Purpose

Concise operational rules for multi-agent coordination and beads workflow. Repository-specific rules live in [repo_rules.md](repo_rules.md). Architecture rules live in [docs/architecture/readme.md](docs/architecture/readme.md).

## Codebase Metrics

**Last Updated**: 2026-02-09

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | 616 | 203.8K | **~1.8M** |
| Code (Python + JS/CSS) | 435 | 149.3K | ~1.3M |
| Python (no tests) | 353 | 136.4K | ~1.2M |
| Frontend (JS/CSS) | 82 | 12.9K | ~85.9K |
| Tests | 138 | 40.9K | ~359.6K |
| Documentation (MD) | 43 | 13.7K | ~106.8K |

**Agent Guidance**:
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 138 test files (20% of codebase)


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
bd create "Title" --description="Context" -p 0-4 -t bug|feature|task --json
bd close <id> --reason "Done" --json
```

Rules:

- **ALWAYS** include `--description` when creating beads (issues without descriptions lack context).
- **NEVER** use `bd edit` (opens interactive editor that agents cannot use).
- Use `bd update <id> --description "text"` for description changes.
- Beads metadata lives in `.git/beads-worktrees/beads-metadata/` and must be pushed.

## Priority System

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

## Non-Interactive Commands (Required)

ALWAYS use `-Force` flag to avoid interactive prompts that hang agents:

```powershell
Copy-Item -Force source dest    # NOT: Copy-Item source dest
Move-Item -Force source dest    # NOT: Move-Item source dest  
Remove-Item -Force file         # NOT: Remove-Item file
Remove-Item -Recurse -Force dir # For directories
```

## Beads Conflict Resolution (Required)

If `.beads/issues.jsonl` has conflicts:

```powershell
Push-Location .git\beads-worktrees\beads-metadata
git show :1:.beads\issues.jsonl > beads.base.jsonl
git show :2:.beads\issues.jsonl > beads.ours.jsonl
git show :3:.beads\issues.jsonl > beads.theirs.jsonl
bd merge beads.merged.jsonl beads.base.jsonl beads.ours.jsonl beads.theirs.jsonl --debug
Copy-Item -Force beads.merged.jsonl .beads\issues.jsonl
git add .beads\issues.jsonl
git merge --continue
Remove-Item -Force beads.*.jsonl
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

Work is NOT complete until `git push` succeeds. MANDATORY steps:

1. Create beads for unfinished work.
2. `get_errors` and tests pass (if code changed).
3. Close bead, commit.
4. **PUSH TO REMOTE** (this is mandatory):
   - Push main branch
   - Push beads-metadata worktree
   - Verify with `git status` (must show "up to date")
5. Hand off: `Continue work on bd-X: [title]. [context]`.

```powershell
git pull --rebase
git push  # If push fails, resolve and retry until success
Push-Location .git\beads-worktrees\beads-metadata
git pull --rebase
git push  # MANDATORY - work is not complete without this
Pop-Location
git status  # Verify: both branches up to date with remote
```

**CRITICAL**: NEVER stop before pushing. NEVER say "ready to push when you are" - YOU must push.
