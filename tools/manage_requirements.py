"""
Requirements Management Tool

This script helps maintain clean and up-to-date requirements files.
It can consolidate multiple requirements files, detect and remove duplicates,
and update version numbers.
"""

import os
import sys
import re
import subprocess
import pkg_resources
from pathlib import Path
from datetime import datetime


class RequirementEntry:
    """Represents a requirement entry with full parsing capabilities."""

    def __init__(self, line):
        self.original_line = line.strip()
        self.package_name = None
        self.version_spec = None
        self.comment = None
        self.is_valid = False
        self.parse()

    def parse(self):
        """Parse a requirements line into components."""
        line = self.original_line

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return

        # Extract inline comment
        if "#" in line:
            line, self.comment = line.split("#", 1)
            line = line.strip()
            self.comment = self.comment.strip()

        # Handle various formats: package==1.0.0, package>=1.0.0, etc.
        match = re.match(r"^([a-zA-Z0-9_.-]+)(?:([<>=!~]+)([a-zA-Z0-9_.-]+))?", line)
        if match:
            self.package_name = match.group(1).lower()
            if match.group(2) and match.group(3):
                self.version_spec = {
                    "operator": match.group(2),
                    "version": match.group(3),
                }
            self.is_valid = True

    def __str__(self):
        """Convert back to string format."""
        if not self.is_valid:
            return self.original_line

        result = self.package_name
        if self.version_spec:
            result += f"{self.version_spec['operator']}{self.version_spec['version']}"
        if self.comment:
            result += f" # {self.comment}"
        return result


def parse_requirements_file(path):
    """Parse a requirements file into a structured format."""
    requirements = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Create entry
            entry = RequirementEntry(line)
            requirements.append(entry)

    return requirements


def get_installed_versions():
    """Get versions of all installed packages."""
    versions = {}
    for pkg in pkg_resources.working_set:
        versions[pkg.key] = pkg.version
    return versions


def update_versions(requirements, installed_versions=None):
    """Update version specifications to match currently installed versions."""
    if installed_versions is None:
        installed_versions = get_installed_versions()

    for req in requirements:
        if req.is_valid and req.package_name in installed_versions:
            current_version = installed_versions[req.package_name]
            req.version_spec = {"operator": "==", "version": current_version}

    return requirements


def remove_duplicates(requirements):
    """Remove duplicate package entries, keeping the last occurrence."""
    unique_reqs = []
    seen_packages = set()

    # Process in reverse to keep last occurrence
    for req in reversed(requirements):
        if req.is_valid and req.package_name not in seen_packages:
            seen_packages.add(req.package_name)
            unique_reqs.insert(0, req)  # Add to front to restore order
        elif not req.is_valid:
            unique_reqs.insert(0, req)  # Keep comments and invalid lines

    return unique_reqs


def consolidate_requirements(req_files):
    """Consolidate multiple requirements files into a single list."""
    all_reqs = []

    for req_file in req_files:
        reqs = parse_requirements_file(req_file)
        all_reqs.extend(reqs)

    return all_reqs


def generate_requirements_file(requirements, output_file):
    """Generate a requirements file from the structured requirements."""
    with open(output_file, "w") as f:
        f.write("# Generated requirements file\n")
        f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for req in requirements:
            f.write(f"{str(req)}\n")


def run_pip_freeze():
    """Run pip freeze to get a current snapshot of the environment."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()


def create_fresh_requirements(project_dir=None):
    """Create a fresh requirements.txt based on the current environment."""
    if not project_dir:
        project_dir = os.getcwd()

    # Get current frozen requirements
    frozen_reqs = []
    for line in run_pip_freeze():
        frozen_reqs.append(RequirementEntry(line))

    # Output file
    output_file = os.path.join(project_dir, "requirements-new.txt")
    generate_requirements_file(frozen_reqs, output_file)

    print(f"Generated fresh requirements file: {output_file}")
    return output_file


def update_requirements_file(req_file, project_dir=None):
    """Update versions in a requirements file."""
    if not project_dir:
        project_dir = os.getcwd()

    # Parse requirements
    reqs = parse_requirements_file(req_file)

    # Get installed versions
    installed_versions = get_installed_versions()

    # Update versions
    updated_reqs = update_versions(reqs, installed_versions)

    # Remove duplicates
    cleaned_reqs = remove_duplicates(updated_reqs)

    # Create backup
    backup_file = f"{req_file}.bak-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    os.rename(req_file, backup_file)

    # Write updated file
    generate_requirements_file(cleaned_reqs, req_file)

    print(f"Updated requirements file: {req_file}")
    print(f"Backup created: {backup_file}")
    return req_file


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python manage_requirements.py [command] [args]")
        print("Commands:")
        print("  update <file> - Update versions in a requirements file")
        print("  fresh - Generate fresh requirements.txt from current environment")
        print(
            "  consolidate <file1> <file2> [output] - Consolidate multiple requirements files"
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "update" and len(sys.argv) >= 3:
        update_requirements_file(sys.argv[2])
    elif command == "fresh":
        create_fresh_requirements()
    elif command == "consolidate" and len(sys.argv) >= 4:
        req_files = sys.argv[2:-1] if len(sys.argv) > 4 else sys.argv[2:]
        output_file = (
            sys.argv[-1] if len(sys.argv) > 4 else "requirements-consolidated.txt"
        )

        all_reqs = consolidate_requirements(req_files)
        cleaned_reqs = remove_duplicates(all_reqs)
        generate_requirements_file(cleaned_reqs, output_file)

        print(f"Consolidated {len(req_files)} requirements files into: {output_file}")
    else:
        print("Invalid command or missing arguments.")
        sys.exit(1)


if __name__ == "__main__":
    main()
