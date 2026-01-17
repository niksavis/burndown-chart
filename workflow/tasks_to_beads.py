#!/usr/bin/env python3
"""
Convert tasks.md to Beads JSONL format for import.

Usage:
    python workflow/tasks_to_beads.py specs/<feature>/tasks.md output.jsonl --parent burndown-chart-016
    python workflow/tasks_to_beads.py specs/<feature>/tasks.md | bd import -i -

Convention (Hierarchical Structure):
    Tasks.md entries become children of a parent feature:

    Parent (manual):  burndown-chart-016 (type: feature)
    Children (auto):  burndown-chart-016.1, 016.2, 016.3... (type: task)

    Example workflow:
    1. Create feature from spec directory:
       bd create "016: Standalone Packaging" -t feature -p 0 --id burndown-chart-016

    2. Import tasks as children:
       python workflow/tasks_to_beads.py specs/016/tasks.md tasks.jsonl --parent burndown-chart-016
       bd import -i tasks.jsonl --rename-on-import

    Result:
    - burndown-chart-016     (feature: parent epic)
    - burndown-chart-016.1   (task: Add PyInstaller...)
    - burndown-chart-016.2   (task: Create build/ directory...)

    Labels extracted from tasks.md:
    - phase-1, phase-2, phase-3 (from "## Phase N" headers)
    - us-1, us-3 (from [US3] markers)
    - parallel (from [P] marker)
    - mvp (from 🎯 MVP marker)

    Type field: Always "task" (beads native classification)
    Priority: p0 (MVP), p1 (Phase 1-2), p2 (Phase 3+), p3 (default)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime


def parse_tasks_md(file_path: Path, parent_id: str | None = None) -> list[dict]:
    """Parse tasks.md and extract tasks in Beads JSONL format.

    Args:
        file_path: Path to tasks.md
        parent_id: Optional parent issue ID (e.g., "burndown-chart-016")
                  If provided, creates hierarchical IDs: parent.1, parent.2, etc.
    """

    content = file_path.read_text(encoding="utf-8")
    tasks = []
    current_phase = None
    current_story = None
    task_counter = 0  # Sequential counter for hierarchical IDs

    # Extract phase headers and determine if MVP
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
                    current_story = f"us-{story_match.group(1)}"

        # Parse task line: - [ ] T001 [P] [US3] Description
        task_match = re.match(
            r"^- \[ \] (T\d+)(?: \[P\])?(?: \[(US\d+)\])? (.+)$", line
        )

        if task_match:
            task_counter += 1
            task_id_from_md = task_match.group(1)  # T001, T002, etc.
            story_label = task_match.group(2)
            if story_label:
                story_label = story_label.lower().replace("us", "us-")  # US3 → us-3
            else:
                story_label = current_story
            description = task_match.group(3).strip()

            # Check markers
            is_parallel = "[P]" in line
            is_mvp = "🎯 MVP" in " ".join(lines[max(0, i - 5) : i + 1])  # Look nearby

            # Build hierarchical ID
            if parent_id:
                issue_id = f"{parent_id}.{task_counter}"
            else:
                # Fallback: use old convention if no parent provided
                prefix = get_beads_prefix()
                issue_id = f"{prefix}-{task_id_from_md.lower()}"

            # Determine priority
            if is_mvp:
                priority = 0  # p0 - must have
            elif current_phase in ["Phase 1", "Phase 2"]:
                priority = 1  # p1 - foundational/setup
            elif current_phase == "Phase 3":
                priority = 2  # p2 - user stories
            else:
                priority = 3  # p3 - normal

            # Build labels
            labels = []
            if story_label:
                labels.append(story_label)
            if is_parallel:
                labels.append("parallel")
            if is_mvp:
                labels.append("mvp")
            if current_phase:
                phase_label = current_phase.lower().replace(
                    " ", "-"
                )  # "Phase 1" → "phase-1"
                labels.append(phase_label)

            # Add spec number from parent ID if hierarchical
            if parent_id:
                spec_match = re.search(r"-(\d+)$", parent_id)
                if spec_match:
                    labels.append(f"spec-{spec_match.group(1)}")

            # Extract feature directory name for context
            feature_dir = file_path.parent.name  # e.g., "016-standalone-packaging"

            # Build enhanced description
            enhanced_description = f"""{description}

**Context**: {current_phase or "Unassigned"} - {phases.get(current_phase, "See tasks.md")}
**Story**: {story_label or "Infrastructure/Setup"}
**Parallel**: {"Yes - can run alongside other [P] tasks" if is_parallel else "No - sequential execution"}

**AI Guidance**:
- Reference specs/{feature_dir}/ for implementation details
- When closing: Include '({issue_id})' at end of commit message first line
- Example: `git commit -m "feat(build): add feature ({issue_id})"`
- Use `bd update {issue_id} --notes "..."` to log implementation decisions

**Source**: {task_id_from_md} from {feature_dir}/tasks.md
"""

            issue = {
                "id": issue_id,
                "type": "task",  # Beads native type (all tasks from tasks.md are type:task)
                "title": f"{task_id_from_md}: {description[:80]}",  # Keep T001 prefix for readability
                "description": enhanced_description,
                "status": "open",
                "priority": priority,
                "labels": labels,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }

            tasks.append(issue)

    return tasks


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


def main():
    parser = argparse.ArgumentParser(
        description="Convert tasks.md to Beads JSONL format for import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Hierarchical structure (recommended)
  bd create "016: Standalone Packaging" -t feature -p 0 --id burndown-chart-016
  python workflow/tasks_to_beads.py specs/016/tasks.md tasks.jsonl --parent burndown-chart-016
  bd import -i tasks.jsonl --rename-on-import
  
  # Result: burndown-chart-016.1, 016.2, 016.3 (children of 016)
  
  # Flat structure (legacy)
  python workflow/tasks_to_beads.py specs/016/tasks.md tasks.jsonl
  bd import -i tasks.jsonl --rename-on-import
  
  # Pipe to beads
  python workflow/tasks_to_beads.py specs/016/tasks.md --parent burndown-chart-016 | bd import -i -
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
    parser.add_argument(
        "--parent",
        type=str,
        help="Parent issue ID for hierarchical structure (e.g., burndown-chart-016). "
        "Creates children as parent.1, parent.2, etc.",
    )

    args = parser.parse_args()

    tasks_file = args.tasks_file
    output_file = args.output_file
    parent_id = args.parent

    if not tasks_file.exists():
        print(f"Error: {tasks_file} not found", file=sys.stderr)
        sys.exit(1)

    tasks = parse_tasks_md(tasks_file, parent_id=parent_id)

    if output_file:
        # Write to file
        with output_file.open("w", encoding="utf-8", newline="\n") as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
        if parent_id:
            print(
                f"✓ Converted {len(tasks)} tasks to {output_file} (children of {parent_id})",
                file=sys.stderr,
            )
        else:
            print(f"✓ Converted {len(tasks)} tasks to {output_file}", file=sys.stderr)
    else:
        # Output to stdout
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
        for task in tasks:
            print(json.dumps(task, ensure_ascii=False))
        if parent_id:
            print(
                f"# Converted {len(tasks)} tasks (children of {parent_id})",
                file=sys.stderr,
            )
        else:
            print(f"# Converted {len(tasks)} tasks", file=sys.stderr)


if __name__ == "__main__":
    main()
