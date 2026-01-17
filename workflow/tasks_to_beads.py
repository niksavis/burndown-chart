#!/usr/bin/env python3
"""
Convert tasks.md to Beads JSONL format for import.

Usage:
    python workflow/tasks_to_beads.py specs/<feature>/tasks.md output.jsonl
    python workflow/tasks_to_beads.py specs/<feature>/tasks.md | bd import -i -
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime


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

            # Create Beads issue
            issue = {
                "id": f"burndown-{task_id.lower()}",  # Use task ID as issue ID
                "title": f"{task_id}: {description[:80]}",  # First 80 chars
                "description": description,
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
