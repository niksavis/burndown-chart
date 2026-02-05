# Beads ID Conventions

## Overview

This project uses **hierarchical IDs** for Spec-Kit generated work and **descriptive slugs** for ad-hoc work. Type classification is stored in beads' native `type` field, not in the ID.

## Convention

### Hierarchical Structure (Spec-Kit Generated)

```
{project-prefix}-{spec-number}          → Feature/Epic (parent)
{project-prefix}-{spec-number}.{N}      → Task (child)
{project-prefix}-{spec-number}.{N}.{M}  → Sub-task (optional)
```

**Examples:**
- `burndown-chart-016` - Feature: "Standalone Executable Packaging" (type: feature)
- `burndown-chart-016.1` - Task: "Add PyInstaller to requirements" (type: task)
- `burndown-chart-016.2` - Task: "Create build/ directory" (type: task)
- `burndown-chart-016.1.1` - Sub-task: "Configure PyInstaller settings" (type: task)

### Ad-Hoc Work (Manual Creation)

For non-hierarchical work, **beads generates hash IDs** automatically:

```
{project-prefix}-{hash}  # e.g., burndown-chart-6np, burndown-chart-abc
```

**Examples:**
- `burndown-chart-6np` - Bug fix (type: bug, title: "PyInstaller crashes with SQLite")
- `burndown-chart-abc` - Chore (type: chore, title: "Update dependencies")
- `burndown-chart-xyz` - Feature spike (type: feature, title: "Dark mode prototype")

**Note**: Beads does NOT support custom slugs like `burndown-chart-bug-crash`. Use descriptive titles and labels instead.

## Type Field Usage

**Use beads' native `-t` type field** instead of encoding type in ID:

| Type      | Usage                                  | Common Hierarchy Position |
| --------- | -------------------------------------- | ------------------------- |
| `feature` | Top-level specs, large initiatives     | Parent (e.g., `016`)      |
| `task`    | Work items from tasks.md               | Children (e.g., `016.1`)  |
| `bug`     | Defects found during development       | Anywhere                  |
| `chore`   | Maintenance, dependencies, refactoring | Anywhere                  |
| `epic`    | Multi-spec initiatives (if needed)     | Parent (rare)             |

## Labels for Metadata

Labels provide rich classification without cluttering IDs:

| Label Category | Examples                | Source                 |
| -------------- | ----------------------- | ---------------------- |
| Phase          | `phase-1`, `phase-2`    | tasks.md "## Phase N"  |
| User Story     | `us-1`, `us-3`, `us-5`  | tasks.md [US3] markers |
| Spec           | `spec-016`, `spec-017`  | Auto from parent ID    |
| Priority       | `mvp` (🎯 MVP marker)    | tasks.md annotations   |
| Parallelism    | `parallel` ([P] marker) | tasks.md [P] marker    |
| Domain         | `build`, `ui`, `data`   | Manual categorization  |

## Benefits

1. **Clean IDs**: `016.1` instead of redundant `t001`
2. **Native types**: Use beads' type field properly
3. **Rich metadata**: Labels for phase, story, domain tracking
4. **Flexible hierarchy**: Natural parent-child relationships
5. **Searchability**: `bd list --label us-3` finds all User Story 3 work
6. **Git clarity**: `(burndown-chart-016.1)` clearly shows feature and task

## Usage

### From Spec-Kit (Automated Workflow)

**Step 1: Create parent feature**
```bash
# Manual - one-time per spec directory
bd create "016: Standalone Executable Packaging" \
  -t feature \
  -p 0 \
  --id burndown-chart-016 \
  -l spec-016 -l build
```

**Step 2: Import tasks as children**
```bash
# Automated - converts tasks.md to hierarchical children
python workflow/tasks_to_beads.py \
  specs/016-standalone-packaging/tasks.md \
  tasks.jsonl \
  --parent burndown-chart-016

bd import -i tasks.jsonl --rename-on-import

# Creates:
# burndown-chart-016.1 (type: task, labels: [phase-1, spec-016])
# burndown-chart-016.2 (type: task, labels: [phase-1, parallel, spec-016])
# burndown-chart-016.3 (type: task, labels: [phase-2, us-3, spec-016])
```

### Manual Creation (Ad-Hoc Work)

```bash
# Bug discovered during 016 work (hash ID auto-generated)
bd create "PyInstaller crashes with SQLite" \
  -t bug \
  -p 0 \
  -l spec-016 -l blocker
# Result: burndown-chart-6np (hash ID)

# Chore work (hash ID auto-generated)
bd create "Update all dependencies to latest" \
  -t chore \
  -p 2 \
  -l maintenance -l q1-2026
# Result: burndown-chart-abc (hash ID)

# Feature as child of existing feature (hierarchical ID supported!)
bd create "Add export to CSV" \
  -t feature \
  -p 1 \
  --id burndown-chart-016.99 \
  -l spec-016 -l enhancement
# Result: burndown-chart-016.99 (hierarchical child of 016)
```

## Rationale

Steve Yegge's beads uses **hash-based IDs** (`bd-a3f8e9`) for collision-free concurrent multi-developer work. This project uses **semantic IDs** because:

1. **Single-developer context**: No concurrent branch collisions
2. **Strong planning workflow**: Spec-Kit generates well-defined task lists
3. **Hierarchy from specs**: Each spec directory naturally maps to a feature parent
4. **Human readability**: `016.3` is clearer than `a3f8e9` in commit history

### Two Orthogonal Systems

1. **Hierarchy (structure)**: Dot notation for parent-child relationships
   - `016` → `016.1` → `016.1.1`
   - Beads native feature, creates automatic dependencies
   
2. **Type (classification)**: Beads' native type field
   - `type: feature|task|bug|chore|epic`
   - Independent of position in hierarchy
   - A bug can be anywhere: top-level, child, or sub-child

### Type Can Appear at Any Level

```
burndown-chart-016 (type: feature) - Top-level parent
├─ burndown-chart-016.1 (type: task) - Standard task
├─ burndown-chart-016.2 (type: bug) - Bug as direct child!
│  ├─ burndown-chart-016.2.1 (type: task) - Investigation task
│  └─ burndown-chart-016.2.2 (type: chore) - Cleanup after fix
└─ burndown-chart-016.3 (type: task) - Another task
   └─ burndown-chart-016.3.1 (type: bug) - Bug found during task

burndown-chart-6np (type: bug) - Standalone bug, no parent (hash ID)
```

This is a **project-level convention**, not a beads requirement. Multi-developer projects should prefer hash IDs for collision-free merges.

## Commit Format

Always include bead ID in commits for traceability and orphan detection:

```bash
# Feature work (hierarchical)
git commit -m "feat(build): add PyInstaller spec (burndown-chart-016.1)"

# Bug fix (hash ID)
git commit -m "fix(app): resolve SQLite crash (burndown-chart-6np)"

# Close bead BEFORE commit
bd close burndown-chart-016.1 --reason "Completed"
git add .
git commit -m "feat(build): add PyInstaller spec (burndown-chart-016.1)"
git push
```

The `(burndown-chart-XXX)` at the end enables `bd doctor` orphan detection (warns if bead is referenced but still open).

## Future Evolution

If the project grows to multi-developer with concurrent feature work, consider:
- **Hash IDs for concurrent work**: Use beads default hash generation for collision-free branch merges
- **Semantic IDs for planned work**: Keep spec number hierarchy for Spec-Kit generated tasks
- **Hybrid approach**: `burndown-chart-016.1` (planned) vs `burndown-chart-a3f8e9` (ad-hoc)
- **Labels over prefixes**: Use labels extensively instead of encoding metadata in IDs

---

**Last Updated**: 2026-01-17  
**Beads Version**: v0.47.1  
**Project**: Burndown  
**Convention**: Hierarchical semantic IDs with native type classification
