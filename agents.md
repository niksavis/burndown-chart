# Agent Instructions - Beads Workflow

## Codebase Metrics

**Last Updated**: 2026-02-03

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | 732 | 251.2K | **~2.2M** |
| Code (Python + JS/CSS) | 414 | 144.4K | ~1.3M |
| Python (no tests) | 336 | 132.5K | ~1.2M |
| Frontend (JS/CSS) | 78 | 12.0K | ~81.6K |
| Tests | 127 | 38.3K | ~338.6K |
| Documentation (MD) | 191 | 68.4K | ~628.9K |

**Agent Guidance**:
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 127 test files (15% of codebase)


## Visual Design Anti-Patterns

**NEVER use emoji-style icons** (🔴🟠🟡🔵⚪) in CLI output or logs - they cause cognitive overload.

**ALWAYS use small Unicode symbols** with semantic colors:
- Status: `○ ◐ ● ✓ ❄`
- Priority: `● P1` (filled circle with text)
- Progress: `[====    ] 50%`

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

**CRITICAL**: This project uses **git worktrees** with separate branches:
- Code → `main` branch
- Beads DB → `beads-metadata` branch (in `.git/beads-worktrees/beads-metadata/`)
- **INVARIANT**: ∀ sessions: push(main) ∧ push(beads-metadata) (multi-agent coordination)

**MANDATORY SESSION START SEQUENCE**:
```powershell
# 1. Verify daemon auto-sync enabled
bd daemon status  # REQUIRED: "Sync: ✓ commit ✓ push"
# If NOT enabled: bd daemon start --auto-commit --auto-push

# 2. Sync beads-metadata branch
Push-Location .git/beads-worktrees/beads-metadata
git pull --rebase
Pop-Location

# 3. Find ready work
bd ready --json

# 4. (Optional) Sync main branch
git pull --rebase
```

## Beads Commands

```bash
bd ready --json                       # Find work (JSON for programmatic use)
bd show <id> --json                   # View details
bd update <id> --status in_progress   # Claim
bd create "Title" --description="Context" -p 1-4 -t bug|feature|task --json
bd close <id> --reason "Done" --json
# NO bd sync in worktree mode - daemon auto-commits to beads-metadata branch
```

**CRITICAL**: ALWAYS include `--description` when creating issues (context for future work)
**PATTERN**: Link discovered work: `--deps discovered-from:<parent-id>`
**FORBIDDEN**: `bd edit` (opens $EDITOR - AI incompatible), markdown TODO lists
**UPDATE**: `bd update <id> --description "text" --title "text" --notes "text" --status "status"`
**WORKTREE**: Beads changes auto-commit to `.git/beads-worktrees/beads-metadata/` - must push separately

**Priority Scale**:
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

## Beads Conflict Resolution

**CRITICAL**: If you encounter merge conflict in `.beads/issues.jsonl` (in beads-metadata branch):

```bash
# 1. Navigate to beads-metadata worktree
Push-Location .git/beads-worktrees/beads-metadata

# 2. Extract 3 versions (base, ours, theirs)
git show :1:.beads/issues.jsonl > beads.base.jsonl
git show :2:.beads/issues.jsonl > beads.ours.jsonl
git show :3:.beads/issues.jsonl > beads.theirs.jsonl

# 3. Run bd merge tool
bd merge beads.merged.jsonl beads.base.jsonl beads.ours.jsonl beads.theirs.jsonl --debug

# 4. Verify result (exit code 0 = success, 1 = manual edit needed)

# 5. Apply merged result
Copy-Item beads.merged.jsonl .beads/issues.jsonl

# 6. Complete merge
git add .beads/issues.jsonl
git merge --continue

# 7. Cleanup
Remove-Item beads.*.jsonl

# 8. Return to project root
Pop-Location
```

**Alternative (accept-remote)**: If conflict trivial (no data loss risk):
```powershell
Push-Location .git/beads-worktrees/beads-metadata
git checkout --theirs .beads/issues.jsonl
bd import -i .beads/issues.jsonl
git add .beads/issues.jsonl
git merge --continue
Pop-Location
```

**Decision criteria**:
- Use `bd merge` if: local changes must be preserved (default)
- Use `accept-remote` if: local changes irrelevant OR fresh clone
- **Frequency**: Rare with daemon auto-sync (∵ 5s push interval)

## Code Creation Prerequisite (MANDATORY)

**RULE**: ∀ code operations: read(architecture_guidelines) → validate(size_limits) → code

**BEFORE any file creation or modification**:
1. Check `docs/architecture/<language>_guidelines.md` for limits and patterns
2. If existing file: verify `wc -l <file>` < 80% of limit
3. If exceeding 80%: create NEW file (append forbidden)

These guidelines ensure:
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

**Agent workflow** (∀ file operations):
1. **Size check**: `lines(file) ≤ 0.8 × limit(language)` ?
   - TRUE → modify existing file
   - FALSE → create new file (partition by responsibility)
2. **Naming**: follow `<language>_guidelines.md` conventions
3. **Patterns**: verify compliance before commit
4. **Verification**: `get_errors` → fix → commit

## Anti-Patterns (DO NOT)

❌ **Never create markdown TODO lists** - use beads issues instead  
❌ **Never skip `--description`** - issues without context are useless  
❌ **Never commit without bead ID** - breaks traceability  
❌ **Never skip beads-metadata push** - breaks multi-agent coordination  
❌ **Never use `bd edit`** - opens $EDITOR (AI incompatible)  

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

**TRIGGER PHRASES**: {"let's land the plane", "wrap up", "end session"} → execute(landing_sequence)

**INVARIANT**: complete(session) ⟺ pushed(main) ∧ pushed(beads-metadata)

**MANDATORY SEQUENCE** (∀ steps required):

1. **Issue remaining work**: ∀ unfinished tasks → `bd create --description`
2. **Quality gates** (if ∃ code changes): `get_errors` ∧ `pytest` → all pass
3. **Close work**: `bd close <id>` → `git add -A` → `git commit -m "...(bd-XXX)"`
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
