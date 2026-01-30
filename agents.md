# Agent Instructions - Beads Workflow

## Codebase Metrics

**Last Updated**: 2026-01-29

| Category               | Files | Lines  | Tokens    |
| ---------------------- | ----- | ------ | --------- |
| **Total**              | 551   | 236.9K | **~2.1M** |
| Code (Python + JS/CSS) | 242   | 136.8K | ~1.2M     |
| Python (no tests)      | 219   | 125.6K | ~1.1M     |
| Frontend (JS/CSS)      | 23    | 11.2K  | ~72.9K    |
| Tests                  | 122   | 35.7K  | ~310.6K   |
| Documentation (MD)     | 187   | 64.5K  | ~597.0K   |

**Agent Guidance**:
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 122 test files (15% of codebase)


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
# 1. Ensure daemon running with auto-sync (CRITICAL for multi-machine coordination)
bd daemon status  # Check if "Sync: ✓ commit ✓ push" present
# If daemon not running OR Sync shows "none", restart with:
bd daemon start --auto-commit --auto-push

# 2. Pull latest beads state
cd .git/beads-worktrees/beads-metadata
git pull --rebase
cd ../../..

# 3. Check for ready work
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

## Architectural Guidelines (MANDATORY)

**BEFORE creating/editing code**: Check architectural guidelines for file size limits and patterns

These guidelines are **agent skills** that ensure quality code by enforcing:
- **Cognitive clarity**: Files sized for comprehension and AI context windows
- **Single responsibility**: Each module/class/function has one clear purpose
- **Maintainability**: Safe modifications without cascading failures
- **Testability**: Focused components easy to test in isolation
- **Discoverability**: Intuitive structure and naming patterns

```
docs/architecture/
├── readme.md              # Index and quick reference
├── python_guidelines.md   # Python: 500 line limit, type hints, layered architecture
├── javascript_guidelines.md  # JavaScript: 400 line limit, ES6 modules, clientside patterns
├── html_guidelines.md     # HTML: 300 line limit, semantic HTML5, ARIA mandatory
├── css_guidelines.md      # CSS: 500 line limit, BEM naming, variables
└── sql_guidelines.md      # SQL: 50 line queries, foreign keys, indexes
```

**Quick limits**:
- Python: 500 lines/file, 50 lines/function → [python_guidelines.md](../docs/architecture/python_guidelines.md)
- JavaScript: 400 lines/file, 40 lines/function → [javascript_guidelines.md](../docs/architecture/javascript_guidelines.md)
- HTML: 300 lines/component → [html_guidelines.md](../docs/architecture/html_guidelines.md)
- CSS: 500 lines/file, BEM naming → [css_guidelines.md](../docs/architecture/css_guidelines.md)
- SQL: 50 lines/query, indexes mandatory → [sql_guidelines.md](../docs/architecture/sql_guidelines.md)

**Agent workflow**:
1. Check existing file size: `wc -l path/to/file`
2. If file > 80% of limit → create NEW file (don't append)
3. Follow naming conventions from guidelines
4. Verify patterns match guidelines before committing

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
   # All commands from PROJECT ROOT only
   # Navigate, sync, and return in one command sequence
   Push-Location .git/beads-worktrees/beads-metadata
   git pull --rebase
   git status  # Check for uncommitted changes
   # If changes: git add .beads/issues.jsonl && git commit -m "chore(beads): sync" && git push
   git push  # Push any daemon-committed changes
   Pop-Location
   
   # Verify you're back in project root
   pwd  # Should show project root
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

