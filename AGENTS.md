# Agent Instructions - Beads Workflow

**Issue Tracker**: bd (beads) | **Init**: `bd onboard`

## Session Start

**Preferred**: Use handoff prompt from previous agent: `Continue work on bd-123: [title]. [context]`
**Fallback**: `What beads tasks are ready?` → `bd ready`

## Beads Commands

```bash
bd ready                              # Find work
bd show <id>                          # View details
bd update <id> --status in_progress   # Claim
bd sync                               # Export→commit→pull→import→push (force immediate)
```

**FORBIDDEN**: `bd edit` (opens $EDITOR - AI incompatible)
**UPDATE**: `bd update <id> --description "text" --title "text" --notes "text" --status "status"`
**SYNC**: Run `bd sync` after batch changes (bypasses 30s debounce)

## Commit Format

```bash
type(scope): description (bd-XXX)

# Optional extended body
```

**MANDATORY**: Bead ID at END of first line (enables `bd doctor` orphan detection)
**WORKFLOW**: Close bead BEFORE commit (single commit = work + closed status)

Types: feat|fix|refactor|docs|test|chore|perf|style|build|ci

## Session End (Landing the Plane)

**AXIOM**: Work ≠ Complete until `git push` succeeds

**MANDATORY SEQUENCE**:

1. File remaining work → beads issues
2. Quality gates (if code) → `get_errors`, `pytest`
3. Close beads → stage → commit with bead ID → push
4. **PUSH** (NON-NEGOTIABLE):
   ```bash
   git pull --rebase
   # If .beads/issues.jsonl conflict:
   #   git checkout --theirs .beads/issues.jsonl
   #   bd import -i .beads/issues.jsonl
   bd sync        # Export→commit→pull→import→push
   git push       # PLANE STILL IN AIR UNTIL THIS SUCCEEDS
   git status     # MUST: "up to date with origin"
   ```
5. Clean → `git stash clear`, `git remote prune origin`
6. Verify → `git status` (nothing uncommitted/unpushed)
7. Hand off → `Continue work on bd-X: [title]. [context]`

**AXIOMS**:
- Plane NOT landed until `git push` succeeds
- NEVER "ready to push when you are" (YOU push)
- Push failure → resolve → retry → success
- Unpushed work breaks multi-agent coordination

