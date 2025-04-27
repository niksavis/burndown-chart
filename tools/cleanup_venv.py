"""
Script to clean up packages not listed in requirements.txt from a virtual environment
"""

import subprocess
import sys
from pathlib import Path


def get_installed_packages():
    """Get a list of all installed packages in the current environment"""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )
    packages = result.stdout.strip().split("\n")
    # Parse package names (ignore version numbers)
    return [p.split("==")[0].lower() for p in packages if p]


def get_required_packages(requirements_file=None):
    """Get a list of all packages listed in requirements.txt"""
    # If no requirements file specified, determine the location based on script location
    if requirements_file is None:
        # Get the project root directory (parent of the tools directory)
        project_root = Path(__file__).parent.parent
        requirements_file = project_root / "requirements.txt"

    try:
        with open(requirements_file, "r") as f:
            packages = f.readlines()
        # Parse package names (ignore version numbers)
        return [
            p.strip().split("==")[0].lower()
            for p in packages
            if p.strip() and not p.startswith("#")
        ]
    except FileNotFoundError:
        print(f"Error: {requirements_file} not found.")
        sys.exit(1)


def main():
    installed = get_installed_packages()
    required = get_required_packages()

    # Find packages to remove (installed but not required)
    to_remove = [
        pkg
        for pkg in installed
        if pkg not in required and pkg != "pip" and pkg != "setuptools"
    ]

    if not to_remove:
        print("No packages to remove. All installed packages are in requirements.txt")
        return

    print(f"Found {len(to_remove)} packages to remove:")
    for pkg in to_remove:
        print(f"  - {pkg}")

    # Ask for confirmation
    confirm = input("\nDo you want to remove these packages? (yes/no): ")
    if confirm.lower() != "yes":
        print("Operation cancelled.")
        return

    # Remove packages
    print("\nRemoving packages...")
    for pkg in to_remove:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", pkg], check=True
            )
            print(f"Removed: {pkg}")
        except subprocess.CalledProcessError as e:
            print(f"Error removing {pkg}: {e}")

    print("\nCleanup complete!")


if __name__ == "__main__":
    main()
