# Beads ID Conventions

## Overview

This project uses **postfix conventions** in beads IDs to make issue types easily identifiable and searchable.

## Convention

```
{project-prefix}-{type}{number}
```

**Examples:**
- `burndown-chart-t001` - Task from Spec-Kit planning
- `burndown-chart-b042` - Bug found during development
- `burndown-chart-e005` - Epic/milestone
- `burndown-chart-f012` - Feature work
- `burndown-chart-c008` - Chore/maintenance

## Type Prefixes

| Prefix | Type    | Source            | Usage                                         |
| ------ | ------- | ----------------- | --------------------------------------------- |
| `t###` | task    | Spec-Kit tasks.md | Sequential work items from planning           |
| `b###` | bug     | Manual creation   | Defects found during development              |
| `e###` | epic    | Manual creation   | Large features spanning multiple issues       |
| `f###` | feature | Manual creation   | New functionality                             |
| `c###` | chore   | Manual creation   | Maintenance work (deps, tooling, refactoring) |

## Benefits

1. **Searchability**: `bd list --id "*-t*"` finds all tasks
2. **Human-readable**: Type visible at a glance in commit history
3. **Batch operations**: Can target types with glob patterns
4. **Git history**: Easy to see what type of work was done
5. **Filtering**: `git log --grep="(.*-b[0-9]"` finds all bug fixes

## Usage

### From Spec-Kit (Automated)

```bash
# tasks.md contains: - [ ] T001 [P] Implement feature X
python workflow/tasks_to_beads.py specs/feature/tasks.md tasks.jsonl
bd import -i tasks.jsonl --rename-on-import

# Creates: burndown-chart-t001
```

### Manual Creation

```bash
# Bug found during development
bd create "Fix null pointer in auth" -t bug -p 1
# Manually note the ID (e.g., bd-a3f8e9)
# Rename to follow convention:
bd update bd-a3f8e9 --id burndown-chart-b042

# Or use explicit ID (if supported in future beads versions):
bd create "Fix auth bug" -t bug -p 1 --id burndown-chart-b042
```

**Note**: Current beads (v0.47.1) generates hash-based IDs by default. Manual renaming or scripted generation may be needed for strict convention adherence.

## Rationale

Steve Yegge's beads doesn't enforce postfix conventions - it uses **hash-based IDs** (`bd-a3f8e9`) for collision-free concurrent work. However, for **single-developer projects with strong planning workflows**, human-readable postfixes provide:

- Clear type identification in commit messages
- Better grep-ability in git history
- Natural mapping from Spec-Kit task IDs

This is a **project-level convention**, not a beads requirement. Other projects may prefer pure hash IDs.

## Commit Format

Always include bead ID in commits:

```bash
git commit -m "fix(auth): resolve null pointer (burndown-chart-b042)"
```

The `(burndown-chart-b042)` at the end enables `bd doctor` orphan detection.

## Future Evolution

If the project grows to multi-developer with concurrent feature work, consider:
- **Hybrid approach**: Use hash IDs (`bd-a3f8e9`) for concurrent work, postfix IDs (`bd-t001`) for planned tasks
- **Labels instead**: Use beads labels `type:task`, `type:bug` for filtering instead of ID postfixes
- **Automatic conversion**: Enhance `tasks_to_beads.py` to check for ID collisions and fall back to hash generation

---

**Last Updated**: 2026-01-17  
**Beads Version**: v0.47.1  
**Project**: Burndown Chart
