#!/usr/bin/env python3
"""
Automated Release Script for Burndown

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
    1. Preflight checks (clean working dir, on main branch, version sync)
    2. Calculate new version from last git tag (NOT configuration/__init__.py)
    3. Update configuration/__init__.py and readme.md
    4. Commit version changes
    5. Regenerate changelog from git history (amend if changed)
    6. Regenerate version_info.txt with new version
    7. Commit version_info.txt
    8. Update codebase context metrics artifacts
    9. Run pre-commit lint gate (auto-commit any formatter fixes)
    10. Create final release commit (tag points here)
    11. Create git tag
    12. Push everything to origin (main + tag)

Version Source of Truth:
    The current version is always read from the latest git tag (e.g. v2.15.2).
    configuration/__init__.py is a WRITE TARGET only — release.py writes the
    new version there, but never reads it as the base for bumping.

    If a previous partial release wrote a bumped version to
    configuration/__init__.py without completing (no tag), the preflight
    check_version_sync() will detect the mismatch and refuse to continue,
    printing recovery instructions.

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

# Bead ID used in all automated commit messages (set in main)
BEAD_ID: str = ""


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
    """Read current version from the last git tag (authoritative source).

    Using the tag rather than configuration/__init__.py prevents partial
    release runs from silently poisoning the base version: a failed run may
    have already written the bumped number to the file, causing the next
    invocation to skip a version.
    """
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v*"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        raise ValueError(
            "No version tags found. Cannot determine current version from git.\n"
            "If this is the first release, create an initial tag: "
            "git tag -a v0.1.0 -m 'Initial release'"
        )
    tag = result.stdout.strip().lstrip("v")
    parts = tag.split(".")
    if len(parts) != 3:
        raise ValueError(f"Unexpected tag format: {result.stdout.strip()!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def get_file_version() -> tuple[int, int, int]:
    """Read version from configuration/__init__.py (write target only)."""
    config_file = PROJECT_ROOT / "configuration" / "__init__.py"
    content = config_file.read_text(encoding="utf-8")

    match = re.search(r'__version__\s*=\s*["\'](\d+)\.(\d+)\.(\d+)["\']', content)
    if not match:
        raise ValueError("Could not find version in configuration/__init__.py")

    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def check_version_sync() -> bool:
    """Verify configuration/__init__.py matches the last git tag.

    A mismatch means a previous partial release wrote the bumped version to the
    file but did not complete (create the tag).  Proceeding without this check
    would skip a version number on the next run.

    Returns:
        True if versions are in sync, False otherwise.
    """
    print("\n  Checking version sync (file vs last tag)...")

    try:
        tag_version = get_current_version()
        file_version = get_file_version()
    except ValueError as e:
        print(f"  [WARNING] Could not compare versions: {e}")
        return True  # Can't check — allow release to proceed

    tag_str = ".".join(str(v) for v in tag_version)
    file_str = ".".join(str(v) for v in file_version)

    if tag_version == file_version:
        print(f"  [OK] File and last tag both at v{tag_str}")
        return True

    print("\n  VERSION MISMATCH DETECTED", file=sys.stderr)
    print(f"  Last git tag : v{tag_str}", file=sys.stderr)
    print(f"  File version : v{file_str}", file=sys.stderr)
    print(
        "\n  A previous partial release likely wrote the bumped version to",
        file=sys.stderr,
    )
    print(
        "  configuration/__init__.py without completing (no tag was created).",
        file=sys.stderr,
    )
    print("\n  To restore and retry:", file=sys.stderr)
    print(
        "    git checkout HEAD -- configuration/__init__.py readme.md",
        file=sys.stderr,
    )
    print(
        "    python release.py patch --bead-id <bead-id>",
        file=sys.stderr,
    )
    return False


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

    # Ensure the file passes ruff format so the pre-commit hook does not reject it
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", str(config_file)],
        check=False,
        capture_output=True,
    )

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
        import regenerate_changelog  # noqa: PLC0415

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

    bead_suffix = f" ({BEAD_ID})" if BEAD_ID else ""
    success, _ = run_command(
        [
            "git",
            "commit",
            "-m",
            f"chore(build): update version_info files for release{bead_suffix}",
        ],
        "Commit version_info files",
    )

    if not success:
        return False

    print("[OK] version_info files regenerated and committed")
    return True


def update_codebase_metrics() -> bool:
    """Update codebase context metrics artifacts."""
    print("\n" + "=" * 60)
    print("Updating Codebase Metrics")
    print("=" * 60)

    if not METRICS_SCRIPT.exists():
        print(f"WARNING: {METRICS_SCRIPT} not found", file=sys.stderr)
        print("[SKIP] Codebase metrics not updated")
        return True  # Non-critical, continue release

    cmd = [sys.executable, str(METRICS_SCRIPT)]
    if BEAD_ID:
        cmd += ["--bead-id", BEAD_ID]
    success, _ = run_command(cmd, "Calculate and update context metrics artifacts")

    if not success:
        print("[WARNING] Could not update metrics (non-critical)")
        return True  # Non-critical, continue release

    print("[OK] Codebase metrics updated")
    return True


def detect_stale_changelog_header(
    new_version: tuple[int, int, int],
    last_tag_version: tuple[int, int, int],
) -> bool:
    """Detect a stale changelog header left by a previous partial release.

    A stale header exists when changelog.md's first ## vX.Y.Z section is a
    version BETWEEN the last released tag and the new version we are about
    to create.  This happens when:
      1. A previous release run bumped to vA.B.C and wrote that header.
      2. That run failed before creating the tag.
      3. git reset --hard restored the commits but left the file on disk.
      4. The next run bumps to vA.B.D (skipping C) while the file shows vA.B.C.

    Returns:
        False (indicating a problem detected) when a stale header is found.
        True (clean) otherwise.
    """
    changelog_path = PROJECT_ROOT / "changelog.md"
    if not changelog_path.exists():
        return True

    content = changelog_path.read_text(encoding="utf-8")
    first_match = re.search(r"^## v(\d+)\.(\d+)\.(\d+)", content, re.MULTILINE)
    if not first_match:
        return True  # No header — nothing to flag

    first_header_version = (
        int(first_match.group(1)),
        int(first_match.group(2)),
        int(first_match.group(3)),
    )
    first_header_str = (
        f"v{first_match.group(1)}.{first_match.group(2)}.{first_match.group(3)}"
    )
    new_version_str = f"v{new_version[0]}.{new_version[1]}.{new_version[2]}"
    last_tag_str = f"v{last_tag_version[0]}.{last_tag_version[1]}.{last_tag_version[2]}"

    if last_tag_version < first_header_version < new_version:
        print("\n  STALE CHANGELOG HEADER DETECTED", file=sys.stderr)
        print(
            f"  changelog.md top entry : {first_header_str}",
            file=sys.stderr,
        )
        print(f"  Last released tag      : {last_tag_str}", file=sys.stderr)
        print(f"  New version            : {new_version_str}", file=sys.stderr)
        print(
            "\n  A previous partial release wrote this header without completing.",
            file=sys.stderr,
        )
        print("  To fix, rename the stale header to the new version:", file=sys.stderr)
        print(
            f"    (Get-Content changelog.md) -replace "
            f"'^## {first_header_str}$', '## {new_version_str}' "
            f"| Set-Content changelog.md",
            file=sys.stderr,
        )
        print(
            f"  Or edit changelog.md manually: change '## {first_header_str}'"
            f" to '## {new_version_str}'",
            file=sys.stderr,
        )
        return False

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

        bead_suffix = f" ({BEAD_ID})" if BEAD_ID else ""
        success, _ = run_command(
            [
                "git",
                "commit",
                "-m",
                f"chore(release): bump version to {new_version_str}{bead_suffix}",
            ],
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

        # Verify no stale header from a previous partial run was bundled
        if not detect_stale_changelog_header(new_version, current):
            return False, ""

        print(f"\n[OK] Version bumped to {new_version_str}")
        return True, new_version_str

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False, ""


def run_lint_gate() -> bool:
    """Run fast lint + type checks before tagging.

    Uses validate.py --fast (ruff + pyright) instead of
    pre-commit run --all-files.  The git pre-commit hook already
    runs validate.py on every automated commit in this script, so a
    second full pre-commit sweep is redundant and slow.  A targeted
    fast pass here catches any formatter drift introduced by the
    release steps themselves (version file writes, metrics updates).

    Returns:
        True when the lint gate passes, False on unrecoverable failure.
    """
    print("\n" + "=" * 60)
    print("Running Fast Lint Gate")
    print("=" * 60)

    validate_script = PROJECT_ROOT / "validate.py"
    if not validate_script.exists():
        print("[SKIP] validate.py not found; skipping lint gate")
        return True

    success, _ = run_command(
        [sys.executable, str(validate_script), "--fast"],
        "validate.py --fast (ruff + pyright)",
    )

    if success:
        print("[OK] Lint gate passed")
        return True

    # Check for auto-fixable drift (formatter rewrote files)
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    modified_files = status_result.stdout.strip()

    if not modified_files:
        print(
            "[FAILED] Lint gate failed with no auto-fixable changes.", file=sys.stderr
        )
        return False

    # Auto-fixes applied — commit them and re-verify
    print("[INFO] Formatter fixes applied; committing and re-verifying...")

    commit_ok, _ = run_command(["git", "add", "-A"], "Stage formatter fixes")
    if not commit_ok:
        return False

    bead_suffix = f" ({BEAD_ID})" if BEAD_ID else ""
    commit_ok, _ = run_command(
        [
            "git",
            "commit",
            "-m",
            f"style(format): apply formatter fixes for release{bead_suffix}",
        ],
        "Commit formatter fixes",
    )
    if not commit_ok:
        return False

    # Re-verify
    success, _ = run_command(
        [sys.executable, str(validate_script), "--fast"],
        "validate.py --fast (re-verify after fixes)",
    )
    if success:
        print("[OK] Lint gate passed after auto-fix")
        return True

    print("[FAILED] Lint gate still failing after auto-fix.", file=sys.stderr)
    return False


def create_release_commit(version: str) -> bool:
    """Create a final release commit that the tag will point to.

    This ensures the tagged commit has a clean message "Release vX.Y.Z"
    instead of implementation details like metrics updates.
    """
    print("\n" + "=" * 60)
    print("Creating Release Commit")
    print("=" * 60)

    bead_suffix = f" ({BEAD_ID})" if BEAD_ID else ""
    commit_message = f"chore(release): refresh release metadata artifacts{bead_suffix}"

    success, _ = run_command(
        ["git", "commit", "--allow-empty", "-m", commit_message],
        "Create release commit",
    )

    if not success:
        return False

    print(f"[OK] Release commit created: '{commit_message}'")
    return True


def create_tag(version: str) -> bool:
    """Create git tag after all commits are complete.

    This MUST be called after version bump, changelog, version_info, and metrics
    commits to prevent orphaned tags pointing to intermediate commits.
    """
    print("\n" + "=" * 60)
    print("Creating Git Tag")
    print("=" * 60)

    tag_name = f"v{version}"
    tag_message = f"Release {tag_name}"

    success, _ = run_command(
        ["git", "tag", "-a", tag_name, "-m", tag_message],
        f"Create tag {tag_name}",
    )

    if not success:
        return False

    print(f"[OK] Tag {tag_name} created with message: '{tag_message}'")
    return True


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
        description="Automated release script for Burndown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Version bump type (major: X.0.0, minor: 0.X.0, patch: 0.0.X)",
    )
    parser.add_argument(
        "--bead-id",
        default="",
        help="Beads issue ID to include in commit messages (e.g. burndown-chart-abc1)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Burndown - Automated Release")
    print("=" * 60)
    global BEAD_ID
    BEAD_ID = args.bead_id

    print(f"\nBump Type: {args.bump_type}")
    if BEAD_ID:
        print(f"Bead ID: {BEAD_ID}")

    # Preflight checks
    print("\n[PREFLIGHT CHECKS]")
    if not check_on_main():
        sys.exit(1)

    if not check_git_status():
        sys.exit(1)

    if not check_version_sync():
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

    # Step 3: Update codebase context metrics artifacts
    if not update_codebase_metrics():
        print("\n[FAILED] Codebase metrics update", file=sys.stderr)
        sys.exit(1)

    # Step 4: Run pre-commit lint gate — catch formatter drift before tagging
    if not run_lint_gate():
        print("\n[FAILED] Pre-commit lint gate", file=sys.stderr)
        sys.exit(1)

    # Step 5: Create final release commit (tag will point here)
    if not create_release_commit(new_version):
        print("\n[FAILED] Release commit creation", file=sys.stderr)
        sys.exit(1)

    # Step 6: Create tag pointing to release commit
    if not create_tag(new_version):
        print("\n[FAILED] Tag creation", file=sys.stderr)
        sys.exit(1)

    # Step 7: Push to origin
    if not push_release(f"v{new_version}"):
        print("\n[FAILED] Push to origin", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] RELEASE COMPLETE")
    print("=" * 60)
    print(f"\nVersion {new_version} released successfully!")


if __name__ == "__main__":
    main()
