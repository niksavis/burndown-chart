"""
Regenerate changelog.md from git history.

IMPORTANT: This generates a DRAFT changelog that requires manual refinement.
The automated output groups commits by scope and filters noise, but human
curation is needed to achieve production-quality release notes.

Workflow:
1. Run during version bump (automatic via bump_version.py)
2. Review generated changelog.md
3. Manually refine:
   - Consolidate related scopes into feature narratives
   - Add context about user benefits
   - Remove any remaining technical noise
   - Polish language for clarity

This script is called automatically by bump_version.py during version bumps.
It can also be run standalone to regenerate the changelog without bumping version.

Usage (standalone): python regenerate_changelog.py
Usage (imported): import regenerate_changelog; regenerate_changelog.main()
"""

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import yaml

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


def load_scope_descriptions() -> dict[str, str]:
    """Load scope descriptions from .github/changelog-scopes.yml."""
    scopes_file = Path(".github/changelog-scopes.yml")
    if not scopes_file.exists():
        return {}

    try:
        content = scopes_file.read_text(encoding="utf-8")
        return yaml.safe_load(content) or {}
    except Exception:
        return {}


def is_noise_scope(scope: str) -> bool:
    """Check if scope is technical noise (task IDs, phase numbers, etc.)."""
    noise_patterns = [
        r"^\d{3}$",  # 012, 001, etc.
        r"^[tf]\d{3}$",  # t007, f012, etc.
        r"^phase\d+$",  # phase2, phase8, etc.
        r"^[a-z]+_[a-z]+$",  # variable_mapping, profile_management (keep dashes)
        r"^(cleanup|refactor|margins|visuals|modals|tabs|buttons|alerts|spec|test|script|polish|validation|ux)$",
    ]
    return any(re.match(pattern, scope.lower()) for pattern in noise_patterns)


def extract_scope(commit_msg: str) -> str | None:
    """Extract scope from conventional commit (e.g., 'budget' from 'feat(budget): ...')."""
    match = re.match(r"^[a-z]+\(([^)]+)\):", commit_msg)
    if match:
        scope = match.group(1)
        # Filter out noise scopes
        if is_noise_scope(scope):
            return None
        return scope
    return None


def extract_beads_issue(commit_msg: str) -> str | None:
    """Extract Beads issue ID from commit message."""
    match = re.search(r"Closes burndown-chart-([a-z0-9]+)", commit_msg, re.IGNORECASE)
    return match.group(1).lower() if match else None


def get_beads_issue_title(issue_id: str) -> str | None:
    """Fetch issue title from .beads/issues.jsonl."""
    issues_file = Path(".beads/issues.jsonl")
    if not issues_file.exists():
        return None

    full_id = f"burndown-chart-{issue_id}"
    try:
        for line in issues_file.read_text(encoding="utf-8").splitlines():
            issue = json.loads(line)
            if issue["id"] == full_id:
                # Clean up title - remove task ID prefix if present
                title = issue["title"]
                title = re.sub(r"^[A-Z]\d+:\s*", "", title)
                return title
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def group_commits_by_issue_and_scope(
    commits: list[str], scope_descriptions: dict[str, str]
) -> dict[str, list[tuple[str, str]]]:
    """Group commits by issue (if linked) or scope, return categorized groups.

    Returns:
        dict[category, list[(title, detail_or_none)]]
    """
    # First pass: group by issue or scope
    issue_groups = defaultdict(list)  # issue_id -> commits
    scope_groups = defaultdict(list)  # scope -> commits
    ungrouped = []

    for commit in commits:
        # Check for Beads issue link
        issue_id = extract_beads_issue(commit)
        if issue_id:
            issue_groups[issue_id].append(commit)
        else:
            # Group by scope
            scope = extract_scope(commit)
            if scope:
                scope_groups[scope].append(commit)
            else:
                ungrouped.append(commit)

    # Second pass: categorize into Features/Fixes/etc
    categorized = defaultdict(list)

    # Process issue groups (highest priority)
    for issue_id, commit_list in issue_groups.items():
        issue_title = get_beads_issue_title(issue_id)
        if not issue_title:
            # Fallback to first commit message
            issue_title = re.sub(r"^[a-z]+(\([^)]+\))?:\s*", "", commit_list[0])

        # Determine category from first commit type
        first_commit = commit_list[0].lower()
        if first_commit.startswith("feat"):
            category = "Features"
        elif first_commit.startswith("fix"):
            category = "Bug Fixes"
        elif first_commit.startswith("docs"):
            category = "Documentation"
        else:
            category = "Other Changes"

        # Add detail if multiple commits
        detail = f"{len(commit_list)} commits" if len(commit_list) > 1 else None
        categorized[category].append((issue_title, detail))

    # Process scope groups
    for scope, commit_list in scope_groups.items():
        # Skip if no description available (means it's not user-facing)
        if scope not in scope_descriptions:
            continue

        # Get description from config
        title = scope_descriptions[scope]

        # Count commit types
        feat_count = sum(1 for c in commit_list if c.startswith("feat"))
        fix_count = sum(1 for c in commit_list if c.startswith("fix"))

        # Determine category by dominant type
        if feat_count >= fix_count:
            category = "Features"
        else:
            category = "Bug Fixes"

        # Don't show commit counts - cleaner output like manual curation
        categorized[category].append((title, None))

    # Process ungrouped commits (limit verbosity)
    MAX_UNGROUPED = 5
    for commit in ungrouped[:MAX_UNGROUPED]:
        result = categorize_commit(commit)
        if result:
            cat, msg = result
            categorized[cat].append((msg, None))

    if len(ungrouped) > MAX_UNGROUPED:
        categorized["Other Changes"].append(
            (f"...and {len(ungrouped) - MAX_UNGROUPED} more changes", None)
        )

    return dict(categorized)


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
    # Load scope descriptions
    scope_descriptions = load_scope_descriptions()
    print(f"Loaded {len(scope_descriptions)} scope descriptions")

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

        # Group commits by issue/scope and categorize
        categorized = group_commits_by_issue_and_scope(commits, scope_descriptions)

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
                items = categorized[category]

                # Bold major features (5+ commits worth), plain text for others
                for title, detail in items:
                    # Check if this is a major feature by looking at original scope
                    # For now, just use plain text to match manual style
                    changelog += f"- {title}\n"
                changelog += "\n"
                has_content = True

        # Add any other categories not in preferred order
        for category, items in categorized.items():
            if category not in preferred_order:
                changelog += f"### {category}\n\n"
                for title, detail in items:
                    changelog += f"- {title}\n"
                changelog += "\n"
                has_content = True

        if not has_content:
            changelog += "- Minor updates and improvements\n\n"

    # Write to file
    changelog_file = Path("changelog.md")
    changelog_file.write_text(changelog, encoding="utf-8")
    print(f"✓ Regenerated changelog.md from {len(tags)} tags")
    print(f"  Lines: {len(changelog.splitlines())}")
    print("\n⚠️  MANUAL REFINEMENT REQUIRED:")
    print("  1. Review generated entries for clarity and accuracy")
    print("  2. Consolidate related items into feature narratives")
    print("  3. Add bold formatting for major features")
    print("  4. Remove any remaining technical noise")
    print("  5. Polish language for user-facing communication")


if __name__ == "__main__":
    main()
