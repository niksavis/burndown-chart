import json
import re
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

CHANGELOG_TYPES = {
    "feat": ("Features", True),
    "fix": ("Bug Fixes", True),
    "perf": (
        "Performance Improvements",
        False,
    ),
    "docs": ("Documentation", False),
    "refactor": ("Refactoring", False),
    "style": ("Code Style", False),
    "test": ("Testing", False),
    "build": ("Build System", False),
    "ci": ("CI/CD", False),
    "chore": ("Maintenance", False),
}


def load_scope_descriptions() -> dict[str, str]:
    scopes_file = Path(".github/changelog-scopes.yml")
    if not scopes_file.exists():
        return {}

    try:
        content = scopes_file.read_text(encoding="utf-8")
        return yaml.safe_load(content) or {}
    except Exception:
        return {}


def is_noise_scope(scope: str) -> bool:
    noise_patterns = [
        r"^\d{3}$",
        r"^[tf]\d{3}$",
        r"^phase\d+$",
        r"^[a-z]+_[a-z]+$",
        r"^(cleanup|refactor|margins|visuals|modals|tabs|buttons|alerts|spec|test|script|polish|validation|ux)$",
    ]
    return any(re.match(pattern, scope.lower()) for pattern in noise_patterns)


def extract_scope(commit_msg: str) -> str | None:

    match = re.match(r"^[a-z]+\(([^)]+)\):", commit_msg)
    if match:
        scope = match.group(1)
        if is_noise_scope(scope):
            return None
        return scope
    return None


def extract_beads_issue(commit_msg: str) -> str | None:
    match = re.search(r"Closes burndown-chart-([a-z0-9]+)", commit_msg, re.IGNORECASE)
    return match.group(1).lower() if match else None


def get_beads_issue_title(issue_id: str) -> str | None:
    issues_file = Path(".beads/issues.jsonl")
    if not issues_file.exists():
        return None

    full_id = f"burndown-chart-{issue_id}"
    try:
        for line in issues_file.read_text(encoding="utf-8").splitlines():
            issue = json.loads(line)
            if issue["id"] == full_id:
                title = issue["title"]
                title = re.sub(r"^[A-Z]\d+:\s*", "", title)
                return title
    except json.JSONDecodeError, KeyError:
        pass
    return None


def group_commits_by_issue_and_scope(
    commits: list[str], scope_descriptions: dict[str, str]
) -> dict[str, list[tuple[str, str]]]:

    issue_groups = defaultdict(list)
    scope_groups = defaultdict(list)
    ungrouped = []

    for commit in commits:
        issue_id = extract_beads_issue(commit)
        if issue_id:
            issue_groups[issue_id].append(commit)
        else:
            scope = extract_scope(commit)
            if scope:
                scope_groups[scope].append(commit)
            else:
                ungrouped.append(commit)

    categorized = defaultdict(list)

    for issue_id, commit_list in issue_groups.items():
        issue_title = get_beads_issue_title(issue_id)
        if not issue_title:
            issue_title = re.sub(r"^[a-z]+(\([^)]+\))?:\s*", "", commit_list[0])

        first_commit = commit_list[0].lower()
        if first_commit.startswith("feat"):
            category = "Features"
        elif first_commit.startswith("fix"):
            category = "Bug Fixes"
        elif first_commit.startswith("docs"):
            category = "Documentation"
        else:
            category = "Other Changes"

        detail = f"{len(commit_list)} commits" if len(commit_list) > 1 else None
        categorized[category].append((issue_title, detail))

    for scope, commit_list in scope_groups.items():
        if scope not in scope_descriptions:
            continue

        title = scope_descriptions[scope]

        feat_count = sum(1 for c in commit_list if c.startswith("feat"))
        fix_count = sum(1 for c in commit_list if c.startswith("fix"))

        if feat_count > 0:
            category = "Features"
        elif fix_count > 0:
            category = "Bug Fixes"
        else:
            category = "Other Changes"

        categorized[category].append((title, None))

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

    for commit_type, (display_name, include) in CHANGELOG_TYPES.items():
        pattern = rf"^{commit_type}(\(.*?\))?:\s*(.+)$"
        if match := re.match(pattern, commit_msg, re.IGNORECASE):
            clean_message = match.group(2).strip()
            return (display_name, clean_message) if include else None

    commit_lower = commit_msg.lower()

    noise_patterns = [
        r"^bump version",
        r"^merge ",
        r"markdownlint|MD\d{3}",
        r"requirements\.txt|pip-compile",
        r"^beads|^bd-\d+",
    ]
    if any(re.search(pattern, commit_lower) for pattern in noise_patterns):
        return None

    if len(commit_msg) > 20:
        return ("Other Changes", commit_msg)

    return None


def parse_existing_versions(changelog_path: Path) -> set[str]:
    if not changelog_path.exists():
        return set()

    existing_versions = set()
    content = changelog_path.read_text(encoding="utf-8")

    for match in re.finditer(r"^## (v\d+\.\d+\.\d+)", content, re.MULTILINE):
        existing_versions.add(match.group(1))

    return existing_versions


def export_to_json(tags_data: list[dict], output_path: Path):

    output_path.write_text(
        json.dumps(tags_data, indent=2, default=str), encoding="utf-8"
    )
    print(f"Exported {len(tags_data)} tags to {output_path}")
    print("\nLLM Prompt Suggestion:")
    print("-" * 60)
    print("Please review this changelog data and write user-friendly")
    print("summaries for each version. Focus on:")
    print("  - What users can DO with new features")
    print("  - Problems that bugs fixed")
    print("  - Group related commits into cohesive narratives")
    print("  - Use bold (**Feature**) for major features")
    print("  - Avoid technical jargon")
    print("-" * 60)


def main(export_json: bool = False, preview: bool = False):

    changelog_path = Path("changelog.md")

    scope_descriptions = load_scope_descriptions()
    print(f"Loaded {len(scope_descriptions)} scope descriptions")

    existing_versions = parse_existing_versions(changelog_path)
    print(f"Found {len(existing_versions)} existing changelog entries")

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

    if preview:
        latest_tag = tags[0]
        print(f"Preview of unreleased commits since {latest_tag}:\n")

        commits_result = subprocess.run(
            ["git", "log", f"{latest_tag}..HEAD", "--pretty=format:%s", "--no-merges"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [c for c in commits_result.stdout.strip().split("\n") if c]

        if not commits:
            print("No unreleased commits")
            return

        categorized = group_commits_by_issue_and_scope(commits, scope_descriptions)

        if export_json:
            tags_data = [
                {
                    "version": "vX.Y.Z (UNRELEASED)",
                    "date": date.today().isoformat(),
                    "commits": commits,
                    "categorized": {
                        category: [(title, detail) for title, detail in items]
                        for category, items in categorized.items()
                    },
                    "commit_count": len(commits),
                }
            ]
            json_path = Path("changelog_draft.json")
            export_to_json(tags_data, json_path)
        else:
            for category, items in categorized.items():
                print(f"### {category}\n")
                for title, _detail in items:
                    print(f"- {title}")
                print()
        return

    new_tags = [tag for tag in tags if tag not in existing_versions]

    if not new_tags:
        print("No new tags to process - changelog is up to date")
        return

    print(f"Found {len(new_tags)} new tags to process: {', '.join(new_tags)}")

    tags_data = []
    new_entries = ""

    for i, tag in enumerate(new_tags):
        tag_index = tags.index(tag)
        prev_tag = tags[tag_index + 1] if tag_index < len(tags) - 1 else None
        prev_tag = tags[i + 1] if i < len(tags) - 1 else None

        tag_date_result = subprocess.run(
            ["git", "log", "-1", "--format=%ai", tag],
            capture_output=True,
            text=True,
            check=True,
        )
        tag_date = tag_date_result.stdout.strip().split()[0]

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

        categorized = group_commits_by_issue_and_scope(commits, scope_descriptions)

        if not categorized or (
            len(categorized) == 1
            and "Other Changes" in categorized
            and len(categorized["Other Changes"]) < 3
        ):
            continue

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

        new_entries += f"## {tag}\n\n"
        new_entries += f"_Released: {tag_date}_\n\n"

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

                for title, _detail in items:
                    new_entries += f"- {title}\n"
                new_entries += "\n"
                has_content = True

        for category, items in categorized.items():
            if category not in preferred_order:
                new_entries += f"### {category}\n\n"
                for title, _detail in items:
                    new_entries += f"- {title}\n"
                new_entries += "\n"
                has_content = True

        if not has_content:
            new_entries += "- Minor updates and improvements\n\n"

    if export_json and tags_data:
        json_path = Path("changelog_draft.json")
        export_to_json(tags_data, json_path)
        return

    if new_entries:
        if changelog_path.exists():
            existing_content = changelog_path.read_text(encoding="utf-8")
            if existing_content.startswith("# Changelog\n"):
                existing_content = existing_content[12:]

            full_changelog = f"# Changelog\n\n{new_entries}{existing_content}"
        else:
            full_changelog = f"# Changelog\n\n{new_entries}"

        changelog_path.write_text(full_changelog, encoding="utf-8")
        print(
            f"Added {len(new_tags)} new changelog entries (preserving existing content)"
        )
        print(f"  New tags: {', '.join(new_tags)}")
        print("\nMANUAL REFINEMENT RECOMMENDED:")
        print("  1. Review new entries for clarity and user-friendliness")
        print("  2. Add bold formatting (**Feature Name**) for major features")
        print("  3. Consolidate related items into cohesive narratives")
        print("  4. Polish language for non-technical users")
    else:
        print("No new entries to add - all tags already in changelog")


if __name__ == "__main__":
    import sys

    export_json = "--json" in sys.argv
    preview = "--preview" in sys.argv
    main(export_json=export_json, preview=preview)
