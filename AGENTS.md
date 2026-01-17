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
bd close <id>                         # Complete
bd sync                               # Sync with git
```

**FORBIDDEN**: `bd edit` (opens interactive editor - AI incompatible)
**Alternative**: `bd update <id> --description "text" --title "text" --notes "text"`

## Commit Format

```
type(scope): description

Closes burndown-chart-<id>
```

Types: See `.github/copilot-instructions.md` Rule 9

## Session End (Landing the Plane)

**AXIOM**: Work ≠ Complete until `git push` succeeds

**MANDATORY SEQUENCE**:

1. File remaining work → beads issues
2. Quality gates (if code changed) → `get_errors`, tests
3. Update beads → close/update status
4. **PUSH** (CRITICAL):
   ```bash
   git pull --rebase && bd sync && git push && git status
   # MUST show "up to date with origin"
   ```
5. Clean → stashes, remote branches
6. Hand off → Provide next prompt:
   ```
   Continue work on bd-X: [title]. [done, next]
   ```

**RULES**:
- ∄ completion before push (leaves work stranded)
- NEVER delegate push to user
- Push failure → resolve → retry until success
- ∀ session ends → ∃ handoff prompt

