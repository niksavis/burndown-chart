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
6. RELEASE (Git + Beads sync)
```

---

## Phase 1: Planning with Spec-Kit

### Create Feature Branch

```powershell
# Create feature branch
git checkout -b 016-standalone-packaging
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

```powershell
# Run conversion script
.\.venv\Scripts\activate; python workflow/tasks_to_beads.py specs/<feature>/tasks.md tasks_import.jsonl

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
.\.venv\Scripts\activate; pytest tests/unit/ -v

# Check for errors
# GitHub Copilot: get_errors tool
```

### Complete Task

```powershell
# Commit your changes
git add <files>
git commit -m "feat(<scope>): <description>

Closes beads-<issue-id>"

# Mark task as complete
bd close <issue-id>

# Sync changes
bd sync
```

### Commit Message Format

```
type(scope): description

- type: feat|fix|refactor|docs|test|chore|perf
- scope: component affected (build, ui, data, etc.)
- description: what changed
- Footer: "Closes beads-<issue-id>" to link commit to task
```

**Examples**:
```
feat(build): add PyInstaller to requirements

Closes beads-t001

fix(app): resolve database path for frozen executable

Closes beads-t023

test(update): add version comparison unit tests

Closes beads-t104
```

---

## Phase 5: Release and Sync

### Push Changes

```powershell
# Pull and rebase
git pull --rebase

# Sync Beads with git
bd sync

# Push to remote
git push
```

### Create Release (MVP Complete)

```powershell
# Merge feature branch to main
git checkout main
git merge <feature-branch>

# Bump version (on main only)
.\.venv\Scripts\activate; python bump_version.py minor

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

## Example: Feature 016 Workflow

**Feature**: Standalone Executable Packaging

**Timeline**:
1. ✅ Planning (2026-01-14): Created research.md, plan.md, data-model.md, contracts/, quickstart.md
2. ✅ Tasks (2026-01-14): Generated tasks.md with 114 tasks across 8 user stories
3. ✅ Import (2026-01-14): Imported 114 tasks into Beads
4. 🚧 Development (in progress): Working through MVP tasks (Setup → Foundational → US3 → US1 → US2)
5. ⏳ Release: After MVP complete, merge to main and bump version

**MVP Scope** (50 tasks):
- Phase 1: Setup (T001-T005)
- Phase 2: Foundational (T006-T012)
- Phase 3: US3 - Build Process (T013-T022)
- Phase 4: US1 - Download & Run (T023-T035)
- Phase 9: US2 - GitHub Releases (T079-T093)

**Current Status**: Ready to start T001 (Add PyInstaller to requirements)

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-14  
**Maintainer**: Burndown Chart Project
