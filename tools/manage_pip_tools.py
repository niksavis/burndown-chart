"""
Pip-Tools Dependency Management Utility

This script helps manage dependencies in a pip-tools workflow where:
- requirements.in contains high-level dependencies with flexible constraints
- requirements.txt is generated using pip-compile with pinned versions

It analyzes dependencies, suggests updates, and helps maintain clean requirements files.
"""

import os
import sys
import re
import subprocess
import json
from importlib.metadata import version, PackageNotFoundError
from datetime import datetime

# Remove any potential indirect imports related to pkg_resources
# importlib.metadata completely replaces pkg_resources functionality


def ensure_pip_tools():
    """Ensure pip-tools is installed."""
    try:
        # Using direct importlib.metadata function call
        version("pip-tools")
        return True
    except PackageNotFoundError:
        print("pip-tools is not installed. Installing now...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pip-tools"], check=True
        )
        return True


def parse_requirements_in(file_path):
    """Parse a requirements.in file and extract package information."""
    packages = []

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Extract package name and constraints
            match = re.match(r"^([a-zA-Z0-9_.-]+)([<>=!~].+)?(?:\s+#.*)?$", line)
            if match:
                package_name = match.group(1).lower()
                constraint = match.group(2) or ""

                packages.append(
                    {
                        "name": package_name,
                        "constraint": constraint.strip(),
                        "original_line": line,
                    }
                )

    return packages


def get_latest_versions(packages):
    """Get latest available versions for packages efficiently."""
    # Get all outdated packages at once rather than one by one
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )

        outdated_packages = json.loads(result.stdout)
        latest_versions = {
            pkg["name"].lower(): pkg["latest_version"] for pkg in outdated_packages
        }

        # Also add current versions of packages not reported as outdated
        package_names = [p["name"].lower() for p in packages]
        for pkg_name in package_names:
            if pkg_name not in latest_versions:
                try:
                    latest_versions[pkg_name] = version(pkg_name)
                except PackageNotFoundError:
                    pass

        return latest_versions
    except Exception as e:
        print(f"Error getting outdated packages: {e}")
        return {}


def check_outdated_packages(packages):
    """Check which packages in requirements.in have newer versions available."""
    latest_versions = get_latest_versions(packages)
    outdated = []

    # Get installed versions using imported version function
    installed_versions = {}
    for pkg_name in packages:
        try:
            version_value = version(
                pkg_name["name"]
            )  # Use directly imported version function
            installed_versions[pkg_name["name"]] = version_value
        except PackageNotFoundError:  # Use directly imported exception
            pass

    for package in packages:
        pkg_name = package["name"]
        if pkg_name in installed_versions and pkg_name in latest_versions:
            installed = installed_versions[pkg_name]
            latest = latest_versions[pkg_name]

            if installed != latest:
                outdated.append(
                    {
                        "name": pkg_name,
                        "current": installed,
                        "latest": latest,
                        "constraint": package["constraint"],
                    }
                )

    return outdated


def find_unused_packages_in_requirements(req_in_path, unused_packages_list):
    """Find which packages in requirements.in are in the unused_packages list."""
    packages = parse_requirements_in(req_in_path)
    unused = []

    unused_names = [p.lower() for p in unused_packages_list]

    for package in packages:
        if package["name"].lower() in unused_names:
            unused.append(package)

    return unused


def update_requirements_in(req_in_path, to_remove=None, to_update=None):
    """Update a requirements.in file by removing or updating packages."""
    to_remove = to_remove or []
    to_update = to_update or []

    # Read the original file
    with open(req_in_path, "r") as f:
        lines = f.readlines()

    # Create a backup
    backup_path = f"{req_in_path}.bak-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    with open(backup_path, "w") as f:
        f.writelines(lines)

    # Process each line
    updated_lines = []
    remove_names = [p["name"].lower() for p in to_remove]
    update_dict = {p["name"].lower(): p for p in to_update}

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            updated_lines.append(line)
            continue

        # Extract package name
        match = re.match(r"^([a-zA-Z0-9_.-]+)", stripped)
        if match:
            pkg_name = match.group(1).lower()

            # Skip if in remove list
            if pkg_name in remove_names:
                continue

            # Update if in update list
            if pkg_name in update_dict:
                updated = update_dict[pkg_name]
                new_line = f"{pkg_name}{updated['constraint']}"

                # Preserve inline comments if present
                comment_match = re.search(r"(#.+)$", stripped)
                if comment_match:
                    new_line += f" {comment_match.group(1)}"

                updated_lines.append(f"{new_line}\n")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Write updated file
    with open(req_in_path, "w") as f:
        f.writelines(updated_lines)

    return backup_path


def compile_requirements(req_in_path, req_txt_path=None):
    """Compile requirements.in to requirements.txt using pip-compile."""
    ensure_pip_tools()

    if not req_txt_path:
        req_txt_path = req_in_path.replace(".in", ".txt")

    cmd = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--output-file",
        req_txt_path,
        req_in_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Successfully compiled {req_in_path} to {req_txt_path}")
        return True
    else:
        print(f"Error compiling requirements: {result.stderr}")
        return False


def analyze_requirements_in(req_in_path, unused_packages_file=None):
    """Analyze requirements.in for outdated and unused packages."""
    packages = parse_requirements_in(req_in_path)
    print(f"Found {len(packages)} packages in {req_in_path}")

    print("\nChecking for outdated packages...")
    outdated = check_outdated_packages(packages)

    unused = []
    if unused_packages_file and os.path.exists(unused_packages_file):
        print("\nChecking for unused packages...")
        with open(unused_packages_file, "r") as f:
            content = f.read()
            # Extract package names from the markdown table
            matches = re.findall(r"\|\s*([a-zA-Z0-9_.-]+)\s*\|", content)
            if matches:
                # First match is the header, so skip it
                unused_names = matches[1:]
                unused = find_unused_packages_in_requirements(req_in_path, unused_names)

    # Generate report
    report_path = f"{os.path.dirname(req_in_path)}/requirements_analysis.md"
    with open(report_path, "w") as f:
        f.write("# Requirements Analysis Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**File Analyzed:** {os.path.basename(req_in_path)}\n\n")

        # Outdated packages
        f.write("## Outdated Packages\n\n")
        if outdated:
            f.write("| Package | Current Version | Latest Version | Constraint |\n")
            f.write("| ------- | --------------- | -------------- | ---------- |\n")
            for pkg in outdated:
                f.write(
                    f"| {pkg['name']} | {pkg['current']} | {pkg['latest']} | {pkg['constraint']} |\n"
                )
        else:
            f.write("No outdated packages found.\n")

        # Unused packages
        f.write("\n## Potentially Unused Packages\n\n")
        if unused:
            f.write("| Package | Constraint | Original Line |\n")
            f.write("| ------- | ---------- | ------------- |\n")
            for pkg in unused:
                f.write(
                    f"| {pkg['name']} | {pkg['constraint']} | `{pkg['original_line']}` |\n"
                )

            f.write(
                "\n**Note:** Verify that these packages are truly unused before removal.\n"
            )
        else:
            f.write("No unused packages found in requirements.in.\n")

        # Suggested actions
        f.write("\n## Suggested Actions\n\n")

        if outdated:
            f.write("### Update outdated packages:\n\n```bash\n")
            for pkg in outdated:
                f.write(
                    f"# Update {pkg['name']} from {pkg['current']} to {pkg['latest']}\n"
                )
            f.write("```\n\n")

        if unused:
            f.write("### Consider removing unused packages:\n\n```bash\n")
            for pkg in unused:
                f.write(f"# Remove {pkg['name']}\n")
            f.write("```\n\n")

    print(f"\nAnalysis report saved to {report_path}")
    return report_path


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python manage_pip_tools.py [command] [args]")
        print("Commands:")
        print(
            "  analyze <requirements.in> [unused_packages.md] - Analyze for outdated and unused packages"
        )
        print(
            "  compile <requirements.in> [requirements.txt] - Compile requirements.in to requirements.txt"
        )
        print(
            "  clean <requirements.in> <unused_packages.md> - Remove unused packages from requirements.in"
        )
        print("  update <requirements.in> - Update all packages to latest versions")
        sys.exit(1)

    command = sys.argv[1]

    if command == "analyze" and len(sys.argv) >= 3:
        req_in_path = sys.argv[2]
        unused_file = sys.argv[3] if len(sys.argv) > 3 else None
        analyze_requirements_in(req_in_path, unused_file)

    elif command == "compile" and len(sys.argv) >= 3:
        req_in_path = sys.argv[2]
        req_txt_path = sys.argv[3] if len(sys.argv) > 3 else None
        compile_requirements(req_in_path, req_txt_path)

    elif command == "clean" and len(sys.argv) >= 4:
        req_in_path = sys.argv[2]
        unused_file = sys.argv[3]

        with open(unused_file, "r") as f:
            content = f.read()
            # Extract package names from the markdown table
            matches = re.findall(r"\|\s*([a-zA-Z0-9_.-]+)\s*\|", content)
            if matches:
                # First match is the header, so skip it
                unused_names = matches[1:]
                unused = find_unused_packages_in_requirements(req_in_path, unused_names)

                if unused:
                    backup = update_requirements_in(req_in_path, to_remove=unused)
                    print(f"Removed {len(unused)} unused packages from {req_in_path}")
                    print(f"Backup saved to {backup}")

                    # Compile updated requirements
                    compile_requirements(req_in_path)
                else:
                    print("No unused packages found in requirements.in")

    elif command == "update" and len(sys.argv) >= 3:
        req_in_path = sys.argv[2]
        packages = parse_requirements_in(req_in_path)
        outdated = check_outdated_packages(packages)

        if outdated:
            backup = update_requirements_in(req_in_path, to_update=outdated)
            print(f"Updated {len(outdated)} packages in {req_in_path}")
            print(f"Backup saved to {backup}")

            # Compile updated requirements
            compile_requirements(req_in_path)
        else:
            print("No outdated packages found in requirements.in")

    else:
        print("Invalid command or missing arguments.")
        sys.exit(1)


if __name__ == "__main__":
    main()
