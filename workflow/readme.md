# Development Workflow: Spec-Kit + Beads + GitHub Copilot

**Goal**: Reproducible, structured development process for implementing features using design-first approach with private task tracking.

**Tools**: 
- **Spec-Kit**: Planning and task generation
- **Beads**: Private issue tracking with git integration
- **GitHub Copilot**: AI-assisted coding in VS Code

---

## Workflow Overview

```
1. SPECIFICATION (Spec-Kit: @speckit.specify)
   ↓
2. PLANNING (Spec-Kit: @speckit.plan)
   ↓
3. TASK GENERATION (Spec-Kit: @speckit.tasks)
   ↓
4. TASK IMPORT (Beads)
   ↓
5. ITERATIVE DEVELOPMENT (Code → Test → Commit)
   ↓
6. FEATURE COMPLETION (Update Spec-Kit docs, quality gates)
   ↓
7. RELEASE (Merge to main, version bump)
```

---

## Phase 1: Planning with Spec-Kit

### Create Feature Branch

```powershell
# Create feature branch
git checkout -b <feature-number>-<feature-name>
```

### Run Spec-Kit Planning

**Step 1: Create Specification** - In VS Code Chat (`Ctrl+Alt+I`):
```
@speckit.specify <feature description>
```

Example:
```
@speckit.specify Create standalone executable packaging for Windows using PyInstaller
```

This creates `specs/<feature>/spec.md` with user stories and acceptance criteria.

**Step 2: Create Implementation Plan** - In VS Code Chat:
```
@speckit.plan
```

This generates planning documents based on spec.md.

**Or check available templates first**:
```powershell
.\.specify\scripts\powershell\check-prerequisites.ps1 -Json
```

**Outputs**:
- `specs/<feature>/research.md` - Investigation findings and decisions
- `specs/<feature>/plan.md` - Technical implementation plan
- `specs/<feature>/spec.md` - User stories with priorities
- `specs/<feature>/data-model.md` - Entity definitions (if needed)
- `specs/<feature>/contracts/` - API contracts (if needed)
- `specs/<feature>/quickstart.md` - Developer guide

**Commit**: Planning documents
```powershell
git add specs/<feature>/
git commit -m "docs(spec-kit): complete Phase 0 & 1 planning for <feature>"
```

---

## Phase 2: Task Generation with Spec-Kit

### Generate tasks.md

**In VS Code Chat** (`Ctrl+Alt+I`):
```
@speckit.tasks
```

This generates tasks.md based on the planning documents (plan.md, spec.md, etc.) in your feature directory.

**Output**: `specs/<feature>/tasks.md` with:
- 100+ tasks in checklist format
- Organized by user stories (US1, US2, US3...)
- Clear dependencies and parallel opportunities
- MVP scope identified

**Format Example**:
```markdown
- [ ] T001 Add PyInstaller to requirements.in with version >=6.0.0
- [ ] T002 [P] [US3] Create build/ directory structure
- [ ] T023 [P] [US1] Modify app.py to detect PyInstaller executable
```

**Commit**: Task breakdown
```powershell
git add specs/<feature>/tasks.md
git commit -m "docs(spec-kit): generate task breakdown for <feature>"
```

---

## Phase 3: Import Tasks to Beads

### Convert tasks.md to Beads Format

```bash
# Activate virtual environment (if using Python project)
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

python workflow/tasks_to_beads.py specs/<feature>/tasks.md tasks_import.jsonl

# Import into Beads
bd import -i tasks_import.jsonl --rename-on-import

# Verify import
bd list --json | ConvertFrom-Json | Measure-Object
bd ready  # Show available tasks

# Sync to JSONL file
bd sync

# Clean up temporary file
Remove-Item tasks_import.jsonl
```

**Result**: All tasks now tracked in Beads with:
- Task IDs (T001, T002, ...)
- Priorities (P1, P2, P3)
- Story labels (US1, US2, ...)
- Parallelizable markers

---

## Phase 4: Iterative Development

### Find Work

```powershell
# See available tasks (no blockers)
bd ready

# See all open tasks
bd list

# View specific task details
bd show <issue-id>
```

### Claim and Work on Task

```powershell
# Start work on a task
bd update <issue-id> --status in_progress

# Implement the task
# Use GitHub Copilot for code generation

# Test your changes
.\# Test your changes (adapt to your project's test framework)
# Python: pytest tests/unit/ -v
# Node.js: npm test
# Go: go test ./...
```

### Complete Task

```bash
# Commit your changes (bead closes automatically via commit message)
git add <files>
git commit -m "feat(<scope>): <description> (bd-<id>)

Optional extended explanation of what was done and why.
Can include implementation details, decisions made, etc."

# Verify bead auto-closed
bd show <issue-id>  # Should show status: closed

# Sync changes
bd sync
```

**CRITICAL**: Never close beads manually. Always close via commit message with `(bd-<id>)` format. This ensures `bd doctor` can track orphaned issues and AI can trace work.

### Commit Message Format

**Required Format** (per [Beads AGENT_INSTRUCTIONS.md](https://github.com/steveyegge/beads/blob/main/AGENT_INSTRUCTIONS.md)):

```
type(scope): description (bd-XXX)

Optional body with extended context, implementation details,
decisions made, or blockers encountered.
```

**Format Rules**:
- **type**: feat|fix|refactor|docs|test|chore|perf
- **scope**: component affected (build, ui, data, etc.)
- **description**: what changed (concise, < 50 chars)
- **(bd-XXX)**: bead ID at END of first line (enables bd doctor tracking)
- **body**: optional extended explanation (blank line separator)

**Examples**:
```bash
# Single task
git commit -m "feat(build): add PyInstaller to requirements (bd-t001)

Added PyInstaller>=6.0.0 to requirements.in per T001 specification.
Regenerated requirements.txt using pip-compile."

# Multiple related tasks
git commit -m "feat(build): create project structure (bd-t002, bd-t003, bd-t004)

Created build/, updater/, and licenses/ directories with
initial subdirectory structure per Phase 1 setup tasks."

# Bug fix
git commit -m "fix(app): resolve database path for frozen executable (bd-t023)

Closes beads-t023

test(update): add version comparison unit tests

Closes beads-t104
```

---

## Phase 5: Feature Completion

### Verify All Tasks Complete

**When all beads tasks are closed**, finalize the Spec-Kit workflow:

```powershell
# Verify no open tasks remain
bd list --status open  # Should show 0 open tasks
```

### Update Spec-Kit Documentation

1. **Update tasks.md** - Check off completed tasks in `specs/<feature>/tasks.md`:
   ```powershell
   # Edit specs/<feature>/tasks.md and mark tasks complete
   # Change [ ] to [x] for completed tasks
   ```

2. **Update spec.md** - Add completion date and final notes to `specs/<feature>/spec.md`:
   ```markdown
   ## Status
   - **Completed**: 2026-01-14
   - **Notes**: All MVP tasks completed, ready for merge
   ```

### Run Final Quality Gates

```bash
# Run your project's test suite
# Examples:
# Python: pytest tests/ -v
# Node.js: npm test
# Go: go test ./...
# Rust: cargo test

# Check for errors using your IDE/tooling
# VS Code: Problems panel (Ctrl+Shift+M)
# GitHub Copilot: get_errors tool
```

### Commit Documentation Updates

```powershell
# Add updated spec files
git add specs/<feature>/

# Commit with descriptive message
git commit -m "docs(spec-kit): mark <feature> as complete"
```

### Final Sync and Push

```powershell
# Sync beads to JSONL
bd sync

# Push to remote
git push
```

**Feature is now complete and ready for PR or merge to main.**

---

## Phase 6: Release and Merge

### Push Changes

```powershell
# Pull and rebase
git pull --rebase

# Sync Beads with git
bd sync

# Push to remote
git push
```

### Create Release (After Feature Branch Merge)

```bash
# Merge feature branch to main
git checkout main
git merge <feature-branch>

# Bump version using your project's version management
# Examples:
# Python: bump2version minor
# Node.js: npm version minor
# Semantic Release: npx semantic-release

# Push with tags
git push origin main --tags
```

**Automated**: GitHub Actions workflow creates release with built executables

---

## Beads Commands Reference

### Daily Workflow

```powershell
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

### Query and Filter

```powershell
bd list --status open              # Open tasks only
bd list --label US1                # User Story 1 tasks
bd list --label parallelizable     # Tasks that can run in parallel
bd list --priority 1               # High priority tasks
```

### Dependency Management

```powershell
bd link <id1> <id2>         # Create dependency (id1 blocks id2)
bd unlink <id1> <id2>       # Remove dependency
bd show <id> --deps         # Show dependencies
```

---

## Best Practices

### 1. Work in Small Batches
- Complete 1-3 tasks per commit
- Test after each task
- Commit frequently with clear messages

### 2. Follow Task Order
- Respect dependencies (Setup → Foundational → User Stories)
- Use `bd ready` to see unblocked tasks
- Parallelize when possible ([P] marker)

### 3. Keep Beads Synced
- Run `bd sync` after every few commits
- Sync before pushing to remote
- Resolve conflicts early

### 4. Update Status Actively
- Mark tasks `in_progress` when starting
- Close tasks immediately when done
- Add comments for blocked tasks: `bd comment <id> "Waiting for..."`

### 5. Test Before Closing
- Run tests: `pytest tests/unit/ -v`
- Check errors: GitHub Copilot `get_errors` tool
- Verify functionality manually

### 6. Document Decisions
- Add comments to complex tasks: `bd comment <id> "Decided to use..."`
- Update research.md if assumptions change
- Keep plan.md accurate

---

## Troubleshooting

### Beads Import Failed

```powershell
# Check JSONL format
python -m json.tool tasks_import.jsonl | head -n 20

# Verify status field (must be 'open', not 'not_started')
Select-String -Path tasks_import.jsonl -Pattern '"status"'

# Try import with dry-run
bd import -i tasks_import.jsonl --dry-run
```

### Task ID Prefix Mismatch

```powershell
# Use --rename-on-import to auto-fix
bd import -i tasks_import.jsonl --rename-on-import
```

### Beads Database Out of Sync

```powershell
# Force re-export from database
bd sync --force
```

### Git Merge Conflicts in .beads/issues.jsonl

```powershell
# Let Beads handle it
bd sync  # Auto-resolves using 3-way merge
```

---

## Tool Installation

See [SETUP.md](./SETUP.md) for detailed installation instructions for:
- Spec-Kit
- Beads
- Python environment
- VS Code extensions

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-17
