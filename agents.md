# Agent Instructions - Beads Workflow

## Codebase Metrics

**Last Updated**: 2026-01-26

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | 551 | 236.1K | **~2.1M** |
| Code (Python + JS/CSS) | 240 | 136.2K | ~1.2M |
| Python (no tests) | 219 | 125.6K | ~1.1M |
| Frontend (JS/CSS) | 21 | 10.7K | ~68.6K |
| Tests | 125 | 35.9K | ~312.3K |
| Documentation (MD) | 186 | 63.9K | ~592.5K |

**Agent Guidance**:
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 125 test files (15% of codebase)


## Session Start

**RULE 0 - VENV ACTIVATION (MANDATORY FIRST STEP)**:
```powershell
.venv\Scripts\activate  # PowerShell (Windows)
# Verify: prompt shows (.venv)
```
**CHECKPOINT**: STOP. Is venv activated? If NO → activate NOW. If YES → proceed.

**AXIOM**: Check beads state FIRST (multi-machine coordination)
**Handoff**: `Continue work on bd-123: [title]. [context]`
**Cold Start**: Sync beads-metadata → check state → claim work

**CRITICAL**: This project uses **git worktrees** for beads with separate `beads-metadata` branch:
- Code changes → `main` branch
- Beads database → `beads-metadata` branch (in `.git/beads-worktrees/beads-metadata/`)
- **MUST sync BOTH branches** for multi-agent coordination

**MANDATORY SESSION START SEQUENCE**:
```bash
# 1. Pull latest beads state (CRITICAL for multi-agent)
cd .git/beads-worktrees/beads-metadata
git pull --rebase
cd ../../..

# 2. Check for ready work
bd ready

# 3. (Optional) Check main branch updates
git pull --rebase
```
- Beads database → `beads-metadata` branch (in `.git/beads-worktrees/beads-metadata/`)
- **MUST push BOTH branches** or multi-agent coordination breaks

## Beads Commands

```bash
bd ready                              # Find work
bd show <id>                          # View details
bd update <id> --status in_progress   # Claim
# NO bd sync in worktree mode - daemon auto-commits to beads-metadata branch
```

**FORBIDDEN**: `bd edit` (opens $EDITOR - AI incompatible)
**UPDATE**: `bd update <id> --description "text" --title "text" --notes "text" --status "status"`
**WORKTREE**: Beads changes auto-commit to `.git/beads-worktrees/beads-metadata/` - must push separately

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

**AXIOM**: Work ≠ Complete until `git push` succeeds (BOTH main AND beads-metadata branches)

**MANDATORY SEQUENCE**:

1. File remaining work → beads issues
2. Quality gates (if code) → `get_errors`, `pytest`
3. Close beads → stage → commit with bead ID → push **main branch**
4. **PUSH MAIN** (NON-NEGOTIABLE):
   ```bash
   git pull --rebase
   git push       # Push main branch
   git status     # MUST: "up to date with origin"
   ```
5. **SYNC BEADS METADATA** (CRITICAL for multi-agent):
   ```bash
   # Navigate to beads-metadata worktree
   cd .git/beads-worktrees/beads-metadata
   
   # Pull latest changes (other agents may have updated)
   git pull --rebase
   
   # Check for uncommitted beads changes
   git status
   
   # If changes exist, commit and push
   git add .beads/issues.jsonl
   git commit -m "chore(beads): sync metadata - closed [bead-ids]"
   git push
   
   # Verify push succeeded
   git status  # MUST: "up to date with origin"
   
   # Return to project root
   cd ../../..
   ```
6. Clean → `git stash clear`, `git remote prune origin`
7. Verify → Both branches pushed successfully
8. Hand off → `Continue work on bd-X: [title]. [context]`

**AXIOMS**:
- Plane NOT landed until BOTH `main` AND `beads-metadata` pushed
- ALWAYS pull beads-metadata BEFORE committing (prevents merge conflicts)
- NEVER skip beads-metadata push (breaks multi-agent coordination)
- NEVER "ready to push when you are" (YOU push)
- Push failure → resolve → retry → success
- Unpushed beads breaks team synchronization

