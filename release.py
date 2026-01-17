#!/usr/bin/env python3
"""
Automated Release Script for Burndown Chart

This script automates the release process to prevent common mistakes:
1. Regenerates version_info.txt (bundled in executable)
2. Runs bump_version.py (updates version in code)
3. Pushes changes and tags to trigger GitHub Actions

Usage:
    python release.py patch   # 2.6.0 → 2.6.1
    python release.py minor   # 2.6.0 → 2.7.0
    python release.py major   # 2.6.0 → 3.0.0

Prerequisites:
    - Changelog already polished (contains new version section with release date)
    - All changes committed and pushed to main
    - No uncommitted changes in working directory
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
VERSION_INFO_SCRIPT = PROJECT_ROOT / "build" / "generate_version_info.py"
BUMP_VERSION_SCRIPT = PROJECT_ROOT / "bump_version.py"


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

    # Check if version_info.txt was modified
    success, output = run_command(
        ["git", "status", "--porcelain", "build/version_info.txt"],
        "Check if version_info.txt changed",
    )

    if not success:
        return False

    if not output.strip():
        print("[OK] version_info.txt is already up to date")
        return True

    # Commit the change
    success, _ = run_command(
        ["git", "add", "build/version_info.txt"], "Stage version_info.txt"
    )

    if not success:
        return False

    success, _ = run_command(
        ["git", "commit", "-m", "chore(build): update version_info.txt for release"],
        "Commit version_info.txt",
    )

    if not success:
        return False

    print("[OK] version_info.txt regenerated and committed")
    return True


def bump_version(bump_type: str) -> tuple[bool, str]:
    """Run bump_version.py to update version and recreate tag with consistent message."""
    print("\n" + "=" * 60)
    print(f"Bumping Version ({bump_type})")
    print("=" * 60)

    if not BUMP_VERSION_SCRIPT.exists():
        print(f"ERROR: {BUMP_VERSION_SCRIPT} not found", file=sys.stderr)
        return False, ""

    # Run bump_version.py with --yes flag to skip confirmation
    print(f"\nRunning: python bump_version.py {bump_type} --yes")

    try:
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), bump_type, "--yes"],
            cwd=PROJECT_ROOT,
            text=True,
        )

        if result.returncode != 0:
            print(
                f"\nERROR: bump_version.py failed with code {result.returncode}",
                file=sys.stderr,
            )
            return False, ""

        # Extract new version from git tags
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            check=True,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        new_version = result.stdout.strip()

        # Recreate tag with consistent message format
        print(f"\nRecreating tag {new_version} with consistent message...")

        # Delete the tag created by bump_version.py
        subprocess.run(
            ["git", "tag", "-d", new_version],
            check=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
        )

        # Create new tag with standard message format
        tag_message = f"Release {new_version}"
        subprocess.run(
            ["git", "tag", "-a", new_version, "-m", tag_message],
            check=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
        )

        print(f"\n[OK] Version bumped to {new_version}")
        print(f"[OK] Tag created with message: '{tag_message}'")
        return True, new_version

    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False, ""


def push_release(version: str) -> bool:
    """Push commits and tags to origin."""
    print("\n" + "=" * 60)
    print("Pushing to Origin")
    print("=" * 60)

    success, _ = run_command(
        ["git", "push", "origin", "main", "--tags"],
        f"Push main branch and {version} tag",
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

    # Step 1: Regenerate version_info.txt
    if not regenerate_version_info():
        print("\n[FAILED] version_info.txt regeneration", file=sys.stderr)
        sys.exit(1)

    # Step 2: Bump version (interactive)
    success, new_version = bump_version(args.bump_type)
    if not success:
        print("\n[FAILED] Version bump", file=sys.stderr)
        sys.exit(1)

    # Step 3: Push to origin
    if not push_release(new_version):
        print("\n[FAILED] Push to origin", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] RELEASE COMPLETE")
    print("=" * 60)
    print(f"\nVersion {new_version} released successfully!")


if __name__ == "__main__":
    main()
