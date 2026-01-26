---
description: Convert tasks.md to Beads issues with hierarchical structure
handoffs:
  - label: Ready Tasks
    agent: speckit.implement
    prompt: Start implementing the imported tasks
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Detect feature context**:
   - Check current git branch name (e.g., `feature/016-standalone-packaging`)
   - Extract spec number from branch name (e.g., `016`)
   - Or prompt user for spec directory if not on feature branch
   - Determine spec directory: `specs/<number>-<feature-name>/`

2. **Verify tasks.md exists**:
   - Check for `specs/<spec-dir>/tasks.md`
   - If not found, suggest running `/speckit.tasks` first
   - Exit if tasks.md doesn't exist

3. **Check for existing parent feature**:
   - Run `bd list` and grep for parent ID pattern (e.g., `burndown-chart-016`)
   - If exists: Use existing parent ID
   - If not exists: Create parent feature bead:
     ```
     bd create "<spec-number>: <Feature Title from spec.md>" -t feature -p 0 --id burndown-chart-<spec-number>
     ```

4. **Convert tasks to beads**:
   - Run the conversion script with parent ID:
     ```powershell
     python workflow/tasks_to_beads.py specs/<spec-dir>/tasks.md tasks.jsonl --parent burndown-chart-<spec-number>
     ```
   - This creates hierarchical IDs: `burndown-chart-016.1`, `016.2`, `016.3`, etc.

5. **Import into beads**:
   - Run: `bd import -i tasks.jsonl --rename-on-import`
   - The `--rename-on-import` flag preserves hierarchical IDs
   - Run: `bd sync` to commit changes immediately (bypass 30s debounce)

6. **Display summary**:
   - Show created parent feature ID (e.g., `burndown-chart-016`)
   - List all child task IDs (e.g., `burndown-chart-016.1` through `016.N`)
   - Show total task count
   - Display next steps:
     ```
     Next: Run 'bd ready' to find available tasks
     Then: 'bd update <id> --status in_progress' to claim a task
     ```

7. **Cleanup**:
   - Remove temporary `tasks.jsonl` file
   - Suggest user run `bd ready` to see available work

## Error Handling

- **No git repository**: Prompt user for spec directory path
- **No tasks.md**: Show error and suggest `/speckit.tasks` command
- **Parent ID conflict**: If `burndown-chart-<spec-number>` already exists but isn't type:feature, prompt user to resolve manually
- **Import failure**: Show beads error output and suggest manual import

## Implementation Notes

- Always use PowerShell syntax for Windows compatibility
- Use absolute paths when referencing files
- The hierarchical structure (`parent.1`, `parent.2`) enables tracking feature completion
- Labels from tasks.md (phase-1, us-1, parallel, mvp) are automatically preserved
- Task priorities (p0-p3) are set based on MVP markers and phase numbers

## Example Workflow

For feature branch `feature/016-standalone-packaging`:

1. Extract spec number: `016`
2. Check parent: `bd list | Select-String "burndown-chart-016"`
3. If not exists: `bd create "016: Standalone Packaging" -t feature -p 0 --id burndown-chart-016`
4. Convert: `python workflow/tasks_to_beads.py specs/016-standalone-packaging/tasks.md tasks.jsonl --parent burndown-chart-016`
5. Import: `bd import -i tasks.jsonl --rename-on-import`
6. Sync: `bd sync`
7. Display: "Created burndown-chart-016 with 15 child tasks (016.1 through 016.15)"
8. Cleanup: `Remove-Item tasks.jsonl`

Context for conversion: $ARGUMENTS
