#!/usr/bin/env python3
"""
Convert tasks.md to Beads JSONL format for import.

Usage:
    python workflow/tasks_to_beads.py specs/<feature>/tasks.md output.jsonl
    python workflow/tasks_to_beads.py specs/<feature>/tasks.md | bd import -i -

ID Conventions:
    This script preserves the task ID prefix from tasks.md for type identification:
    - T001 → {prefix}-t001 (task from spec-kit planning)
    - B001 → {prefix}-b001 (bug)
    - E001 → {prefix}-e001 (epic/milestone)
    - F001 → {prefix}-f001 (feature)
    - C001 → {prefix}-c001 (chore)

    Examples:
    - burndown-chart-t001 (task from 016 spec)
    - burndown-chart-b042 (ad-hoc bug)

    Benefits:
    - Searchability: bd list --id "*-t*" finds all tasks
    - Human-readable: Type visible in ID
    - Batch operations: Can target types with glob patterns

    Note: The prefix is read from .beads/config.yaml (issue-prefix),
    defaulting to 'bd' if not configured.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime


def get_beads_prefix() -> str:
    """Get beads project prefix from config or default to 'bd'."""
    try:
        config_path = Path(".beads/config.yaml")
        if config_path.exists():
            import yaml

            with config_path.open() as f:
                config = yaml.safe_load(f)
                prefix = config.get("issue-prefix", "")
                if prefix:
                    return prefix
    except Exception:
        pass  # Fall back to bd
    return "bd"


def parse_tasks_md(file_path: Path) -> list[dict]:
    """Parse tasks.md and extract tasks in Beads JSONL format."""

    content = file_path.read_text(encoding="utf-8")
    tasks = []
    current_phase = None
    current_story = None

    # Extract phase headers
    phase_pattern = re.compile(r"^## (Phase \d+): (.+)$", re.MULTILINE)
    phases = {}
    for match in phase_pattern.finditer(content):
        phase_num = match.group(1)
        phase_name = match.group(2)
        phases[phase_num] = phase_name

    lines = content.split("\n")

    for i, line in enumerate(lines):
        # Track current phase
        if line.startswith("## Phase"):
            phase_match = re.match(r"^## (Phase \d+): (.+)", line)
            if phase_match:
                current_phase = phase_match.group(1)
                current_story = None

                # Extract story from phase name if present
                story_match = re.search(r"User Story (\d+)", phase_match.group(2))
                if story_match:
                    current_story = f"US{story_match.group(1)}"

        # Parse task line
        task_match = re.match(
            r"^- \[ \] (T\d+)(?: \[P\])?(?: \[(US\d+)\])? (.+)$", line
        )

        if task_match:
            task_id = task_match.group(1)
            story_label = task_match.group(2) or current_story
            description = task_match.group(3).strip()

            # Check if parallelizable
            is_parallel = "[P]" in line

            # Extract priority from phase (P1=1, P2=2, P3=3, setup/foundational=1)
            priority = 2  # Default
            if current_phase in ["Phase 1", "Phase 2"]:
                priority = 1  # Setup/Foundational = high priority
            elif "P1" in lines[max(0, i - 20) : i]:  # Check context for P1
                priority = 1
            elif "P3" in lines[max(0, i - 20) : i]:
                priority = 3

            # Build labels
            labels = []
            if story_label:
                labels.append(story_label)
            if is_parallel:
                labels.append("parallelizable")
            if current_phase:
                labels.append(current_phase.replace(" ", "-").lower())

            # Create Beads issue with enhanced description
            feature_dir = file_path.parent.name  # e.g., "016-standalone-packaging"
            prefix = get_beads_prefix()  # Dynamic prefix from config

            enhanced_description = f"""{description}

**Context**: {current_phase} - {phases.get(current_phase, "Unknown")}
**Story**: {story_label or "Setup/Infrastructure"}
**Parallel**: {"Yes - can run alongside other [P] tasks" if is_parallel else "No - sequential"}

**AI Guidance**:
- Reference specs/{feature_dir}/ for implementation details
- When closing: Include '({prefix}-{task_id.lower()})' at end of commit message first line
- Example: `git commit -m "feat(build): add feature ({prefix}-{task_id.lower()})"`
- Update notes field with implementation decisions or blockers encountered

**ID Convention**: This task uses '{task_id.lower()}' postfix for type identification.
When creating new issues manually, consider using:
- t### for tasks, b### for bugs, e### for epics, f### for features, c### for chores
"""

            issue = {
                "id": f"{prefix}-{task_id.lower()}",  # Use dynamic prefix + task ID
                "title": f"{task_id}: {description[:80]}",  # First 80 chars
                "description": enhanced_description,
                "status": "open",  # Beads uses 'open' not 'not_started'
                "priority": priority,
                "labels": labels,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }

            tasks.append(issue)

    return tasks


def main():
    parser = argparse.ArgumentParser(
        description="Convert tasks.md to Beads JSONL format for import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Write to file
  python workflow/tasks_to_beads.py specs/016/tasks.md output.jsonl
  
  # Pipe to beads import
  python workflow/tasks_to_beads.py specs/016/tasks.md | bd import -i -
  
  # Import with auto-rename
  python workflow/tasks_to_beads.py specs/016/tasks.md temp.jsonl
  bd import -i temp.jsonl --rename-on-import
        """,
    )
    parser.add_argument(
        "tasks_file",
        type=Path,
        help="Path to tasks.md file (e.g., specs/016-standalone-packaging/tasks.md)",
    )
    parser.add_argument(
        "output_file",
        type=Path,
        nargs="?",
        help="Output JSONL file (optional, defaults to stdout)",
    )

    args = parser.parse_args()

    tasks_file = args.tasks_file
    output_file = args.output_file

    if not tasks_file.exists():
        print(f"Error: {tasks_file} not found", file=sys.stderr)
        sys.exit(1)

    tasks = parse_tasks_md(tasks_file)

    if output_file:
        # Write to file
        with output_file.open("w", encoding="utf-8", newline="\n") as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
        print(f"✓ Converted {len(tasks)} tasks to {output_file}", file=sys.stderr)
    else:
        # Output to stdout
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
        for task in tasks:
            print(json.dumps(task, ensure_ascii=False))
        print(f"# Converted {len(tasks)} tasks", file=sys.stderr)


if __name__ == "__main__":
    main()
