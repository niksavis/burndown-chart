"""
Version Bump Script

Updates application version across all project files before merging to main.
Run this script before merging feature branches to ensure version consistency.

Usage:
    python bump_version.py [major|minor|patch]

If no argument provided, prompts interactively.
"""

import re
import subprocess
import sys
from pathlib import Path


def get_current_version() -> tuple[int, int, int]:
    """Read current version from configuration/__init__.py."""
    config_file = Path(__file__).parent / "configuration" / "__init__.py"
    content = config_file.read_text(encoding="utf-8")

    match = re.search(r'__version__\s*=\s*["\'](\d+)\.(\d+)\.(\d+)["\']', content)
    if not match:
        raise ValueError("Could not find version in configuration/__init__.py")

    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(current: tuple[int, int, int], bump_type: str) -> tuple[int, int, int]:
    """Calculate new version based on bump type."""
    major, minor, patch = current

    if bump_type == "major":
        return (major + 1, 0, 0)
    elif bump_type == "minor":
        return (major, minor + 1, 0)
    elif bump_type == "patch":
        return (major, minor, patch + 1)
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use major, minor, or patch.")


def update_configuration_file(new_version: tuple[int, int, int]) -> None:
    """Update version in configuration/__init__.py."""
    config_file = Path(__file__).parent / "configuration" / "__init__.py"
    content = config_file.read_text(encoding="utf-8")

    version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
    updated = re.sub(
        r'(__version__\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
        rf"\g<1>{version_str}\g<2>",
        content,
    )

    config_file.write_text(updated, encoding="utf-8")
    print(f"[OK] Updated configuration/__init__.py to {version_str}")


def update_readme_file(new_version: tuple[int, int, int]) -> None:
    """Update version badge in readme.md."""
    readme_file = Path(__file__).parent / "readme.md"
    content = readme_file.read_text(encoding="utf-8")

    version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
    updated = re.sub(
        r"(badge/version-)\d+\.\d+\.\d+(-blue\.svg)",
        rf"\g<1>{version_str}\g<2>",
        content,
    )

    readme_file.write_text(updated, encoding="utf-8")
    print(f"[OK] Updated readme.md badge to {version_str}")


def generate_changelog() -> None:
    """Regenerate changelog.md from all git tags using regenerate_changelog script."""
    try:
        # Import and run the changelog regeneration
        import regenerate_changelog

        regenerate_changelog.main()
    except Exception as e:
        print(f"[WARNING] Could not regenerate changelog: {e}")
        print("  You can manually run: python regenerate_changelog.py")


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("Burndown Chart Version Bump Utility")
    print("=" * 60)

    # Get current version
    try:
        current = get_current_version()
        current_str = f"{current[0]}.{current[1]}.{current[2]}"
        print(f"\nCurrent version: {current_str}")
    except Exception as e:
        print(f"Error reading current version: {e}")
        sys.exit(1)

    # Determine bump type
    if len(sys.argv) > 1:
        bump_type = sys.argv[1].lower()
    else:
        print("\nSelect version bump type:")
        print("  1. major - Breaking changes (X.0.0)")
        print("  2. minor - New features (0.X.0)")
        print("  3. patch - Bug fixes (0.0.X)")

        choice = input("\nEnter choice (1/2/3 or major/minor/patch): ").strip().lower()

        # Map numeric choices to bump types
        choice_map = {"1": "major", "2": "minor", "3": "patch"}
        bump_type = choice_map.get(choice, choice)

    # Validate bump type
    if bump_type not in ("major", "minor", "patch"):
        print(f"Error: Invalid bump type '{bump_type}'")
        print("Use: major, minor, or patch")
        sys.exit(1)

    # Calculate new version
    new_version = bump_version(current, bump_type)
    new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"

    print(f"\n{bump_type.upper()} bump: {current_str} → {new_version_str}")

    # Confirm action
    confirm = input("\nProceed with version update? (y/N): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        sys.exit(0)

    # Update files
    try:
        update_configuration_file(new_version)
        update_readme_file(new_version)
    except Exception as e:
        print(f"\n[ERROR] Error updating files: {e}")
        sys.exit(1)

    # Create git tag automatically
    try:
        # Commit version changes
        subprocess.run(
            ["git", "add", "configuration/__init__.py", "readme.md"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"chore: bump version to {new_version_str}"],
            check=True,
            capture_output=True,
        )
        print("[OK] Committed version changes")

        # Create annotated tag
        subprocess.run(
            [
                "git",
                "tag",
                "-a",
                f"v{new_version_str}",
                "-m",
                f"Release v{new_version_str}",
            ],
            check=True,
            capture_output=True,
        )
        print(f"[OK] Created tag v{new_version_str}")

        # Now regenerate changelog from all tags (including the new one)
        print("\nRegenerating changelog from git history...")
        generate_changelog()

        # Commit the regenerated changelog
        subprocess.run(
            ["git", "add", "changelog.md"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--amend", "--no-edit"],
            check=True,
            capture_output=True,
        )
        print("[OK] Updated changelog.md")

    except subprocess.CalledProcessError as e:
        print(f"\n[WARNING] Could not create git tag automatically: {e}")
        print("  You may need to commit and tag manually.")
    except Exception as e:
        print(f"\n[WARNING] Unexpected error during git operations: {e}")

    # Success message
    print(f"\n{'=' * 60}")
    print(f"[SUCCESS] Version bumped to {new_version_str}")
    print(f"{'=' * 60}")
    print("\nNext steps:")
    print("  1. Review changes: git log -1 --stat")
    print("  2. Verify tag: git tag -l v{}".format(new_version_str))
    print("  3. Merge to main: git checkout main && git merge <branch-name>")
    print("  4. Push changes: git push origin main --tags")
    print()


if __name__ == "__main__":
    main()
