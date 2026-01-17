"""
Generate changelog entries for NEW git tags (preserves existing content).

IMPORTANT: This generates DRAFT entries for new tags only.
Existing changelog entries are preserved and never overwritten.

FORMATTING RULE: FLAT BULLETS ONLY
The About dialog cannot render sub-bullet points (no indentation support).
All changelog entries MUST be flat single-line bullets with inline details:
  CORRECT:   - **Feature**: Description with details inline, comma-separated
  INCORRECT: - **Feature**: Description
               - Sub-point one
               - Sub-point two

BUG FIX vs DEVELOPMENT ITERATION:
When processing commits for a release, the script distinguishes between:
  - Bug Fixes: fix() commits for already-released features (scope has NO feat commits)
  - Development Iterations: fix() commits for NEW features being developed in same release
    (scope HAS feat commits) - these are rolled into the feature description, not listed
    as separate bug fixes

How it works:
1. Parses changelog.md to find which versions already have entries
2. Generates entries ONLY for new tags (not in changelog)
3. Prepends new entries to the TOP of existing changelog
4. Groups commits by scope/issue with user-friendly descriptions
5. Categorizes fix commits intelligently (bug vs development iteration)

Workflow Option A (Direct Markdown):
1. Run: python regenerate_changelog.py
2. Review generated entries in changelog.md
3. Manually refine for clarity and user-friendliness

Workflow Option B (LLM-Assisted):
1. Run: python regenerate_changelog.py --json
2. Creates changelog_draft.json with structured commit data
3. Use LLM to read JSON and write polished summaries
4. Copy LLM output to changelog.md

This script is called automatically by bump_version.py during version bumps.
It can also be run standalone to catch up on missing tags.

Usage (direct):  python regenerate_changelog.py
Usage (JSON):    python regenerate_changelog.py --json
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

        # IMPORTANT: If scope has BOTH feat and fix commits, the fixes are
        # development iterations (not bugs). Only categorize as "Bug Fixes"
        # if there are ONLY fix commits (meaning this is fixing released features).
        if feat_count > 0:
            # Has new features - all work (including fixes) is part of feature development
            category = "Features"
        elif fix_count > 0:
            # Only has fixes - these are real bug fixes for released features
            category = "Bug Fixes"
        else:
            # Other types (docs, refactor, etc.)
            category = "Other Changes"

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


def parse_existing_versions(changelog_path: Path) -> set[str]:
    """Parse existing changelog to find versions that already have entries."""
    if not changelog_path.exists():
        return set()

    existing_versions = set()
    content = changelog_path.read_text(encoding="utf-8")

    # Find all version headers (## vX.Y.Z)
    for match in re.finditer(r"^## (v\d+\.\d+\.\d+)", content, re.MULTILINE):
        existing_versions.add(match.group(1))

    return existing_versions


def export_to_json(tags_data: list[dict], output_path: Path):
    """Export tag data to JSON for LLM processing.

    Creates a structured JSON file that an LLM can easily read to generate
    high-quality changelog summaries.

    Args:
        tags_data: List of tag data dictionaries with commits and metadata
        output_path: Path to write JSON file
    """
    output_path.write_text(
        json.dumps(tags_data, indent=2, default=str), encoding="utf-8"
    )
    print(f"✓ Exported {len(tags_data)} tags to {output_path}")
    print("\n📝 LLM Prompt Suggestion:")
    print("─" * 60)
    print("Please review this changelog data and write user-friendly")
    print("summaries for each version. Focus on:")
    print("  • What users can DO with new features")
    print("  • Problems that bugs fixed")
    print("  • Group related commits into cohesive narratives")
    print("  • Use bold (**Feature**) for major features")
    print("  • Avoid technical jargon")
    print("─" * 60)


def main(export_json: bool = False):
    """Generate changelog entries for NEW tags only (preserves existing content)."""
    changelog_path = Path("changelog.md")

    # Load scope descriptions
    scope_descriptions = load_scope_descriptions()
    print(f"Loaded {len(scope_descriptions)} scope descriptions")

    # Parse existing changelog to find which versions are already documented
    existing_versions = parse_existing_versions(changelog_path)
    print(f"Found {len(existing_versions)} existing changelog entries")

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

    # Filter to only NEW tags (not in existing changelog)
    new_tags = [tag for tag in tags if tag not in existing_versions]

    if not new_tags:
        print("✓ No new tags to process - changelog is up to date")
        return

    print(f"Found {len(new_tags)} new tags to process: {', '.join(new_tags)}")

    # Collect data for all new tags
    tags_data = []
    new_entries = ""

    for i, tag in enumerate(new_tags):
        # Find previous tag for commit range
        tag_index = tags.index(tag)
        prev_tag = tags[tag_index + 1] if tag_index < len(tags) - 1 else None
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

        # Skip if no meaningful content
        if not categorized or (
            len(categorized) == 1
            and "Other Changes" in categorized
            and len(categorized["Other Changes"]) < 3
        ):
            continue

        # Store structured data for JSON export
        tags_data.append(
            {
                "version": tag,
                "date": tag_date,
                "commits": commits,
                "categorized": {
                    category: [(title, detail) for title, detail in items]
                    for category, items in categorized.items()
                },
                "commit_count": len(commits),
            }
        )

        # Build section for this NEW tag
        new_entries += f"## {tag}\n\n"
        new_entries += f"*Released: {tag_date}*\n\n"

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
                new_entries += f"### {category}\n\n"
                items = categorized[category]

                # Bold major features (5+ commits worth), plain text for others
                for title, detail in items:
                    # Check if this is a major feature by looking at original scope
                    # For now, just use plain text to match manual style
                    new_entries += f"- {title}\n"
                new_entries += "\n"
                has_content = True

        # Add any other categories not in preferred order
        for category, items in categorized.items():
            if category not in preferred_order:
                new_entries += f"### {category}\n\n"
                for title, detail in items:
                    new_entries += f"- {title}\n"
                new_entries += "\n"
                has_content = True

        if not has_content:
            new_entries += "- Minor updates and improvements\n\n"

    # Export JSON if requested (for LLM processing)
    if export_json and tags_data:
        json_path = Path("changelog_draft.json")
        export_to_json(tags_data, json_path)
        return

    # Prepend new entries to existing changelog (preserve curated content)
    if new_entries:
        if changelog_path.exists():
            existing_content = changelog_path.read_text(encoding="utf-8")
            # Remove "# Changelog" header if it exists
            if existing_content.startswith("# Changelog\n"):
                existing_content = existing_content[12:]  # Remove header

            full_changelog = f"# Changelog\n\n{new_entries}{existing_content}"
        else:
            full_changelog = f"# Changelog\n\n{new_entries}"

        changelog_path.write_text(full_changelog, encoding="utf-8")
        print(
            f"✓ Added {len(new_tags)} new changelog entries (preserving existing content)"
        )
        print(f"  New tags: {', '.join(new_tags)}")
        print("\n⚠️  MANUAL REFINEMENT RECOMMENDED:")
        print("  1. Review new entries for clarity and user-friendliness")
        print("  2. Add bold formatting (**Feature Name**) for major features")
        print("  3. Consolidate related items into cohesive narratives")
        print("  4. Polish language for non-technical users")
    else:
        print("✓ No new entries to add - all tags already in changelog")


if __name__ == "__main__":
    import sys

    # Check for --json flag
    export_json = "--json" in sys.argv
    main(export_json=export_json)
