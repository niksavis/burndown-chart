"""
Unified dependency management script for updating and auditing dependencies.
"""

import argparse
import subprocess
import os
import sys
from pathlib import Path


def get_project_root():
    """
    Get the project root directory.

    Since this script is in the tools folder, the project root is one level up.
    """
    return Path(__file__).parent.parent.absolute()


def update_dependencies(sync=False, clean=False):
    """
    Update requirements.txt from requirements.in and refresh packages in venv.

    Args:
        sync: If True, remove packages not in requirements.txt
        clean: If True, recreate the environment from scratch
    """
    # Get project root and path to requirements files
    project_root = get_project_root()
    os.chdir(project_root)  # Change to project root for relative paths

    print("Updating requirements.txt from requirements.in...")

    # Generate requirements.txt from requirements.in using relative paths
    try:
        subprocess.run(
            [
                "pip-compile",
                "requirements.in",  # Use relative path
                "--output-file",
                "requirements.txt",  # Use relative path
                "--upgrade",
                "--no-header",  # Omit header that might contain sensitive path info
                "--no-annotate",  # Optionally remove annotations with paths
            ],
            check=True,
        )
        print("Successfully generated requirements.txt")
    except subprocess.CalledProcessError as e:
        print(f"Error generating requirements.txt: {e}")
        return False

    # Handle clean reinstall if requested
    if clean:
        print("Performing clean reinstall of all dependencies...")
        try:
            # Uninstall all packages (except pip and setuptools)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "freeze",
                    "--exclude-editable",
                    "|",
                    "grep",
                    "-v",
                    "^\\-e",
                    "|",
                    "xargs",
                    "pip",
                    "uninstall",
                    "-y",
                ],
                shell=True,
                check=True,
            )
            print("Successfully cleaned environment")
        except subprocess.CalledProcessError as e:
            print(f"Error cleaning environment: {e}")
            return False

    # Install/update package options
    pip_args = ["pip", "install", "-r", "requirements.txt"]

    # Add sync flag if requested
    if sync:
        print("Synchronizing environment with requirements.txt...")
        pip_args.append("--no-deps")
    else:
        print("Updating packages in virtual environment...")
        pip_args.append("--upgrade")

    try:
        subprocess.run(pip_args, check=True)
        print("Successfully updated packages in virtual environment")

        # If syncing, now add dependencies
        if sync:
            subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error updating packages: {e}")
        return False

    return True


def main():
    # Set working directory to project root for better compatibility
    os.chdir(get_project_root())

    parser = argparse.ArgumentParser(description="Manage project dependencies")
    parser.add_argument(
        "--audit", action="store_true", help="Run a full dependency audit"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Synchronize environment with requirements.txt (remove unlisted packages)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Perform a clean reinstall of all dependencies",
    )
    args = parser.parse_args()

    if args.audit:
        # Import and run the audit functionality
        from tools.dependency_audit import run_dependency_audit

        run_dependency_audit(os.getcwd())
    else:
        # Run the standard update with optional sync/clean flags
        update_dependencies(sync=args.sync, clean=args.clean)


if __name__ == "__main__":
    main()
