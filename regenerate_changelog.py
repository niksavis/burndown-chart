"""
Regenerate changelog.md from git history.

This script is called automatically by bump_version.py during version bumps.
It can also be run standalone to regenerate the changelog without bumping version
(e.g., after adding new filtering rules or to clean up existing changelog).

Filters out technical commits (linting, formatting, tests, etc.) to keep
the changelog user-facing and readable.

Usage (standalone): python regenerate_changelog.py
Usage (imported): import regenerate_changelog; regenerate_changelog.main()
"""

import re
import subprocess
from pathlib import Path

# Configurable changelog types
# Format: 'type': (display_name, include_in_changelog)
CHANGELOG_TYPES = {
    "feat": ("Features", True),
    "fix": ("Bug Fixes", True),
    "perf": (
        "Performance Improvements",
        False,
    ),  # Can enable for performance-focused releases
    "docs": ("Documentation", False),  # Can enable for documentation releases
    "refactor": ("Refactoring", False),
    "style": ("Code Style", False),
    "test": ("Testing", False),
    "build": ("Build System", False),
    "ci": ("CI/CD", False),
    "chore": ("Maintenance", False),
}


def categorize_commit(commit_msg: str) -> tuple[str, str] | None:
    """Categorize commit by type and return (category, clean_message) or None if excluded.

    Returns:
        tuple[str, str] | None: (display_category, clean_message) if included, None otherwise
    """
    # Check for Conventional Commit format
    for commit_type, (display_name, include) in CHANGELOG_TYPES.items():
        # Pattern: type(scope)?: message or type: message
        pattern = rf"^{commit_type}(\(.*?\))?:\s*(.+)$"
        if match := re.match(pattern, commit_msg, re.IGNORECASE):
            clean_message = match.group(2).strip()
            return (display_name, clean_message) if include else None

    # For historical commits without conventional format:
    # Try to infer from content (fallback for old commits)
    commit_lower = commit_msg.lower()

    # Skip obvious noise patterns for legacy commits
    noise_patterns = [
        r"^bump version",
        r"^merge ",
        r"markdownlint|MD\d{3}",
        r"requirements\.txt|pip-compile",
        r"^beads|^bd-\d+|spec-kit",
    ]
    if any(re.search(pattern, commit_lower) for pattern in noise_patterns):
        return None

    # For non-conventional commits, categorize as "Other Changes" if substantial
    if len(commit_msg) > 20:
        return ("Other Changes", commit_msg)

    return None


def main():
    """Regenerate changelog from all tags."""
    # Get all tags
    result = subprocess.run(
        ["git", "tag", "--sort=-version:refname"],
        capture_output=True,
        text=True,
        check=True,
    )
    tags = result.stdout.strip().split("\n")

    if not tags or not tags[0]:
        print("No tags found")
        return

    changelog = "# Changelog\n\n"

    for i, tag in enumerate(tags):
        prev_tag = tags[i + 1] if i < len(tags) - 1 else None

        # Get tag date
        tag_date_result = subprocess.run(
            ["git", "log", "-1", "--format=%ai", tag],
            capture_output=True,
            text=True,
            check=True,
        )
        tag_date = tag_date_result.stdout.strip().split()[0]  # YYYY-MM-DD

        # Get commits between tags
        if prev_tag:
            range_spec = f"{prev_tag}..{tag}"
        else:
            range_spec = tag

        commits_result = subprocess.run(
            ["git", "log", range_spec, "--pretty=format:%s", "--no-merges"],
            capture_output=True,
            text=True,
            check=True,
        )

        commits = [c for c in commits_result.stdout.strip().split("\n") if c]

        # Categorize commits by type
        categorized = {}
        for commit in commits:
            result = categorize_commit(commit)
            if result:
                category, clean_message = result
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(f"- {clean_message}")

        # Build section
        changelog += f"## {tag}\n\n"
        changelog += f"*Released: {tag_date}*\n\n"

        # Output categories in preferred order
        preferred_order = [
            "Features",
            "Bug Fixes",
            "Performance Improvements",
            "Other Changes",
        ]
        has_content = False

        for category in preferred_order:
            if category in categorized:
                changelog += f"### {category}\n\n"
                changelog += "\n".join(categorized[category]) + "\n\n"
                has_content = True

        # Add any other categories not in preferred order
        for category, items in categorized.items():
            if category not in preferred_order:
                changelog += f"### {category}\n\n"
                changelog += "\n".join(items) + "\n\n"
                has_content = True

        if not has_content:
            changelog += "- Minor updates and improvements\n\n"

    # Write to file
    changelog_file = Path("changelog.md")
    changelog_file.write_text(changelog, encoding="utf-8")
    print(f"✓ Regenerated changelog.md from {len(tags)} tags")
    print(f"  Lines: {len(changelog.splitlines())}")


if __name__ == "__main__":
    main()
