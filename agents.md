# Agent Instructions - Beads Workflow

## Codebase Metrics

**Last Updated**: 2026-01-26

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | 551 | 236.0K | **~2.1M** |
| Code (Python + JS/CSS) | 240 | 136.2K | ~1.2M |
| Python (no tests) | 219 | 125.5K | ~1.1M |
| Frontend (JS/CSS) | 21 | 10.7K | ~68.6K |
| Tests | 125 | 35.9K | ~312.3K |
| Documentation (MD) | 186 | 63.8K | ~591.4K |

**Agent Guidance**:
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 125 test files (15% of codebase)


## Session Start

**AXIOM**: `bd sync` FIRST (multi-machine coordination)
**Handoff**: `Continue work on bd-123: [title]. [context]`
**Cold Start**: `bd sync` → `bd ready`

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
**WORKFLOW**: Close bead BEFORE push (NOT after release)
```
Work → Close bead → Sync → Push → Create release
       └─ Close here, NOT after release!
```

Types: feat|fix|refactor|docs|test|chore|perf|style|build|ci

## File Naming Convention

**RULE**: Use lowercase letters with underscores for all file names

**Correct**:
- `readme.md`, `bd_guide.md`, `advanced_features.md`
- `agent_automation.py`, `simple_agent.py`
- `config.yaml`, `tasks.jsonl`

**Incorrect**:
- `README.md`, `BD_GUIDE.md`, `ADVANCED_FEATURES.md`
- `AgentAutomation.py`, `SimpleAgent.py`

**Why**: Consistent naming, better cross-platform compatibility, easier grep/search

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

