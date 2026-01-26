#!/usr/bin/env python3
"""
Automated Release Script for Burndown Chart

Integrated release workflow that handles version bumping, changelog generation,
and executable metadata in a single atomic operation to prevent coordination bugs.

Usage:
    python release.py patch   # 2.6.0 → 2.6.1
    python release.py minor   # 2.6.0 → 2.7.0
    python release.py major   # 2.6.0 → 3.0.0

Prerequisites:
    - All changes committed and pushed to main
    - No uncommitted changes in working directory

Flow:
    1. Preflight checks (clean working dir, on main branch)
    2. Calculate new version from configuration/__init__.py
    3. Update configuration/__init__.py and readme.md
    4. Commit version changes
    5. Create git tag (once, with correct message)
    6. Regenerate changelog from git history
    7. Commit changelog (amend)
    8. Regenerate version_info.txt with new version
    9. Commit version_info.txt
    10. Push everything to origin (main + tag)

Note: bump_version.py is now deprecated. Use this script for releases.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
VERSION_INFO_SCRIPT = PROJECT_ROOT / "build" / "generate_version_info.py"
METRICS_SCRIPT = PROJECT_ROOT / "update_codebase_metrics.py"


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    print(f"\n[{description}]")
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.stdout:
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False, str(e)


def get_current_version() -> tuple[int, int, int]:
    """Read current version from configuration/__init__.py."""
    config_file = PROJECT_ROOT / "configuration" / "__init__.py"
    content = config_file.read_text(encoding="utf-8")

    match = re.search(r'__version__\s*=\s*["\'](\d+)\.(\d+)\.(\d+)["\']', content)
    if not match:
        raise ValueError("Could not find version in configuration/__init__.py")

    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def calculate_new_version(
    current: tuple[int, int, int], bump_type: str
) -> tuple[int, int, int]:
    """Calculate new version based on bump type."""
    major, minor, patch = current

    if bump_type == "major":
        return (major + 1, 0, 0)
    elif bump_type == "minor":
        return (major, minor + 1, 0)
    elif bump_type == "patch":
        return (major, minor, patch + 1)
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_configuration_file(new_version: tuple[int, int, int]) -> str:
    """Update version in configuration/__init__.py and return version string."""
    config_file = PROJECT_ROOT / "configuration" / "__init__.py"
    content = config_file.read_text(encoding="utf-8")

    version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
    updated = re.sub(
        r'(__version__\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
        rf"\g<1>{version_str}\g<2>",
        content,
    )

    config_file.write_text(updated, encoding="utf-8")
    print(f"[OK] Updated configuration/__init__.py to {version_str}")
    return version_str


def update_readme_file(version_str: str) -> None:
    """Update version badge and footer in readme.md."""
    readme_file = PROJECT_ROOT / "readme.md"
    content = readme_file.read_text(encoding="utf-8")

    # Update badge
    updated = re.sub(
        r"(badge/version-)\d+\.\d+\.\d+(-blue\.svg)",
        rf"\g<1>{version_str}\g<2>",
        content,
    )

    # Update footer version
    updated = re.sub(
        r"(\*\*Version:\*\* )\d+\.\d+\.\d+",
        rf"\g<1>{version_str}",
        updated,
    )

    readme_file.write_text(updated, encoding="utf-8")
    print(f"[OK] Updated readme.md badge and footer to {version_str}")


def regenerate_changelog() -> None:
    """Regenerate changelog.md from git tags using regenerate_changelog script."""
    try:
        print("\n[Regenerating changelog from git history]")
        import regenerate_changelog

        regenerate_changelog.main()
    except Exception as e:
        print(f"[WARNING] Could not regenerate changelog: {e}")
        print("  You can manually run: python regenerate_changelog.py")


def check_git_status() -> bool:
    """Verify git working directory is clean."""
    print("\n" + "=" * 60)
    print("Checking Git Status")
    print("=" * 60)

    success, output = run_command(
        ["git", "status", "--porcelain"], "Check for uncommitted changes"
    )

    if not success:
        return False

    if output.strip():
        print("\nERROR: Working directory has uncommitted changes:", file=sys.stderr)
        print(output)
        print("\nCommit or stash changes before releasing.", file=sys.stderr)
        return False

    print("[OK] Working directory is clean")
    return True


def check_on_main() -> bool:
    """Verify we're on the main branch."""
    success, output = run_command(
        ["git", "branch", "--show-current"], "Check current branch"
    )

    if not success:
        return False

    branch = output.strip()
    if branch != "main":
        print(f"\nERROR: Not on main branch (current: {branch})", file=sys.stderr)
        print("Checkout main before releasing.", file=sys.stderr)
        return False

    print("[OK] On main branch")
    return True


def regenerate_version_info() -> bool:
    """Regenerate version_info.txt for executable metadata."""
    print("\n" + "=" * 60)
    print("Regenerating version_info.txt")
    print("=" * 60)

    if not VERSION_INFO_SCRIPT.exists():
        print(f"ERROR: {VERSION_INFO_SCRIPT} not found", file=sys.stderr)
        return False

    success, _ = run_command(
        [sys.executable, str(VERSION_INFO_SCRIPT)],
        "Generate version_info.txt from configuration/__init__.py",
    )

    if not success:
        return False

    # Check if version_info files were modified
    success, output = run_command(
        [
            "git",
            "status",
            "--porcelain",
            "build/version_info.txt",
            "build/version_info_updater.txt",
        ],
        "Check if version_info files changed",
    )

    if not success:
        return False

    if not output.strip():
        print("[OK] version_info files are already up to date")
        return True

    # Commit the changes
    success, _ = run_command(
        ["git", "add", "build/version_info.txt", "build/version_info_updater.txt"],
        "Stage version_info files",
    )

    if not success:
        return False

    success, _ = run_command(
        ["git", "commit", "-m", "chore(build): update version_info files for release"],
        "Commit version_info files",
    )

    if not success:
        return False

    print("[OK] version_info files regenerated and committed")
    return True


def update_codebase_metrics() -> bool:
    """Update codebase metrics in agents.md."""
    print("\n" + "=" * 60)
    print("Updating Codebase Metrics")
    print("=" * 60)

    if not METRICS_SCRIPT.exists():
        print(f"WARNING: {METRICS_SCRIPT} not found", file=sys.stderr)
        print("[SKIP] Codebase metrics not updated")
        return True  # Non-critical, continue release

    success, _ = run_command(
        [sys.executable, str(METRICS_SCRIPT)],
        "Calculate and update metrics in agents.md",
    )

    if not success:
        print("[WARNING] Could not update metrics (non-critical)")
        return True  # Non-critical, continue release

    print("[OK] Codebase metrics updated")
    return True


def bump_version(bump_type: str) -> tuple[bool, str]:
    """Bump version, update files, create tag, and regenerate changelog.

    Returns:
        tuple[bool, str]: (success, new_version_tag)
    """
    print("\n" + "=" * 60)
    print(f"Bumping Version ({bump_type})")
    print("=" * 60)

    try:
        # Get current version
        current = get_current_version()
        current_str = f"{current[0]}.{current[1]}.{current[2]}"
        print(f"\nCurrent version: {current_str}")

        # Calculate new version
        new_version = calculate_new_version(current, bump_type)
        new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
        print(f"{bump_type.upper()} bump: {current_str} → {new_version_str}")

        # Update files
        version_str = update_configuration_file(new_version)
        update_readme_file(version_str)

        # Commit version changes
        success, _ = run_command(
            ["git", "add", "configuration/__init__.py", "readme.md"],
            "Stage version changes",
        )
        if not success:
            return False, ""

        success, _ = run_command(
            ["git", "commit", "-m", f"chore: bump version to {new_version_str}"],
            "Commit version changes",
        )
        if not success:
            return False, ""

        # Regenerate changelog from git history (skips if version section exists)
        regenerate_changelog()

        # Check if changelog.md was modified (only amend if it changed)
        success, status_output = run_command(
            ["git", "status", "--porcelain", "changelog.md"],
            "Check if changelog changed",
        )

        if status_output.strip():
            # Changelog was regenerated, amend to include it
            success, _ = run_command(
                ["git", "add", "changelog.md"],
                "Stage changelog",
            )
            if not success:
                print("[WARNING] Could not stage changelog")

            success, _ = run_command(
                ["git", "commit", "--amend", "--no-edit"],
                "Commit changelog (amend)",
            )
            if not success:
                print("[WARNING] Could not commit changelog")
        else:
            print(
                "[OK] Changelog already contains version section (skipped regeneration)"
            )

        # Create git tag AFTER all amends (prevents orphaned tag)
        tag_name = f"v{new_version_str}"
        tag_message = f"Release {tag_name}"
        success, _ = run_command(
            ["git", "tag", "-a", tag_name, "-m", tag_message],
            f"Create tag {tag_name}",
        )
        if not success:
            return False, ""

        print(f"\n[OK] Version bumped to {tag_name}")
        print(f"[OK] Tag created with message: '{tag_message}'")
        return True, tag_name

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False, ""


def push_release(version: str) -> bool:
    """Push commits and tags to origin."""
    print("\n" + "=" * 60)
    print("Pushing to Origin")
    print("=" * 60)

    # Push main branch first
    success, _ = run_command(
        ["git", "push", "origin", "main"],
        "Push main branch",
    )

    if not success:
        return False

    # Push only the new tag (not --tags which pushes all local tags)
    success, _ = run_command(
        ["git", "push", "origin", version],
        f"Push {version} tag",
    )

    if not success:
        return False

    print(f"\n[OK] Release {version} pushed to origin")
    print("\nGitHub Actions will now build the release.")
    print("Monitor: https://github.com/niksavis/burndown-chart/actions")
    return True


def main():
    """Main release workflow."""
    parser = argparse.ArgumentParser(
        description="Automated release script for Burndown Chart",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Version bump type (major: X.0.0, minor: 0.X.0, patch: 0.0.X)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Burndown Chart - Automated Release")
    print("=" * 60)
    print(f"\nBump Type: {args.bump_type}")

    # Preflight checks
    print("\n[PREFLIGHT CHECKS]")
    if not check_on_main():
        sys.exit(1)

    if not check_git_status():
        sys.exit(1)

    # Step 1: Bump version first (updates configuration/__init__.py)
    success, new_version = bump_version(args.bump_type)
    if not success:
        print("\n[FAILED] Version bump", file=sys.stderr)
        sys.exit(1)

    # Step 2: Regenerate version_info.txt with NEW version
    if not regenerate_version_info():
        print("\n[FAILED] version_info.txt regeneration", file=sys.stderr)
        sys.exit(1)

    # Step 3: Update codebase metrics in agents.md
    if not update_codebase_metrics():
        print("\n[FAILED] Codebase metrics update", file=sys.stderr)
        sys.exit(1)

    # Step 4: Push to origin
    if not push_release(new_version):
        print("\n[FAILED] Push to origin", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] RELEASE COMPLETE")
    print("=" * 60)
    print(f"\nVersion {new_version} released successfully!")


if __name__ == "__main__":
    main()
