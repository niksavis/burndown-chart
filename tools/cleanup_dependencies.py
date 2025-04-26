"""
Dependency Cleanup Tool

This script identifies unused dependencies and generates commands to remove them.
It performs a more thorough analysis than the audit tool to minimize false positives.
"""

import os
import sys
import re
import pkg_resources
from pathlib import Path


def get_installed_packages():
    """Get all installed packages and their distributions."""
    installed = {}
    for dist in pkg_resources.working_set:
        installed[dist.key] = {
            "version": dist.version,
            "location": dist.location,
            "requires": [req.key for req in dist.requires()],
        }
    return installed


def find_import_mapping():
    """Create mapping between package names and their importable modules."""
    mapping = {}
    for dist in pkg_resources.working_set:
        if dist.has_metadata("top_level.txt"):
            for module in dist.get_metadata("top_level.txt").strip().split():
                mapping[module] = dist.key
    return mapping


def scan_python_files(project_dir):
    """Scan all Python files in the project for imports."""
    imports_by_file = {}
    import_pattern = re.compile(
        r"^(?:from\s+(\S+)\s+import|import\s+(\S+))", re.MULTILINE
    )

    for py_file in Path(project_dir).glob("**/*.py"):
        if ".git" in py_file.parts:
            continue

        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                imports = set()

                for match in import_pattern.finditer(content):
                    module = match.group(1) or match.group(2)
                    # Get the top-level module
                    top_module = module.split(".")[0]
                    imports.add(top_module)

                if imports:
                    imports_by_file[str(py_file)] = imports
        except Exception as e:
            print(f"Error reading {py_file}: {e}")

    return imports_by_file


def find_dependency_usages(project_dir, import_mapping):
    """Find which packages are being used based on imports."""
    imports_by_file = scan_python_files(project_dir)
    used_packages = set()

    for file_path, imports in imports_by_file.items():
        for import_name in imports:
            if import_name in import_mapping:
                used_packages.add(import_mapping[import_name])

    return used_packages, imports_by_file


def check_indirect_dependencies(used_packages, installed_packages):
    """Check which packages are needed as dependencies of directly used packages."""
    all_required = set(used_packages)

    # Find dependencies of dependencies
    def add_dependencies(package):
        if package in installed_packages:
            for req in installed_packages[package]["requires"]:
                if req not in all_required:
                    all_required.add(req)
                    add_dependencies(req)

    # Add dependencies for all directly used packages
    for package in list(used_packages):
        add_dependencies(package)

    return all_required


def identify_development_dependencies(project_dir):
    """Identify likely development dependencies from setup files."""
    dev_dependencies = set()

    # Check setup.py
    setup_file = Path(project_dir) / "setup.py"
    if setup_file.exists():
        with open(setup_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            # Look for development dependencies
            dev_match = re.search(
                r'(dev_requires|tests_require|extras_require\s*=\s*{[^}]*[\'"]dev[\'"]:)',
                content,
            )
            if dev_match:
                # Extract package names
                packages = re.findall(
                    r'[\'"]([a-zA-Z0-9_.-]+)[\'"]', content[dev_match.start() :]
                )
                dev_dependencies.update(packages)

    # Check requirements-dev.txt
    dev_req_file = Path(project_dir) / "requirements-dev.txt"
    if dev_req_file.exists():
        with open(dev_req_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (without version)
                    package = re.split(r"[<>=!~]", line)[0].strip().lower()
                    dev_dependencies.add(package)

    return dev_dependencies


def generate_cleanup_plan(installed_packages, used_packages, dev_dependencies):
    """Generate a plan for cleaning up unused dependencies."""
    all_required = check_indirect_dependencies(used_packages, installed_packages)

    # Find truly unused packages
    unused = []
    for package in installed_packages:
        if package not in all_required and package not in dev_dependencies:
            unused.append(
                {
                    "name": package,
                    "version": installed_packages[package]["version"],
                    "location": installed_packages[package]["location"],
                    "confidence": "high"
                    if not installed_packages[package]["requires"]
                    else "medium",
                }
            )

    return sorted(unused, key=lambda x: x["name"])


def export_cleanup_commands(unused_packages, output_file):
    """Generate shell commands to remove unused packages."""
    with open(output_file, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Generated dependency cleanup commands\n")
        f.write("# Review carefully before executing\n\n")

        for pkg in unused_packages:
            f.write(f"pip uninstall -y {pkg['name']}  # version {pkg['version']}\n")


def run_dependency_cleanup(project_dir, output_dir=None):
    """Run the full dependency cleanup analysis."""
    print(f"Analyzing dependencies in {project_dir}...")

    if not output_dir:
        output_dir = project_dir

    # Get installed packages
    print("Getting installed packages...")
    installed_packages = get_installed_packages()

    # Create import mapping
    print("Mapping imports to packages...")
    import_mapping = find_import_mapping()

    # Find package usages
    print("Scanning for package imports...")
    used_packages, imports_by_file = find_dependency_usages(project_dir, import_mapping)
    print(f"Found {len(used_packages)} directly used packages")

    # Identify dev dependencies
    print("Identifying development dependencies...")
    dev_dependencies = identify_development_dependencies(project_dir)
    print(f"Found {len(dev_dependencies)} development dependencies")

    # Generate cleanup plan
    print("Generating cleanup plan...")
    unused_packages = generate_cleanup_plan(
        installed_packages, used_packages, dev_dependencies
    )

    # Create reports
    unused_report_file = os.path.join(output_dir, "unused_dependencies.md")
    with open(unused_report_file, "w") as f:
        f.write("# Unused Dependencies Report\n\n")

        if unused_packages:
            f.write(f"Found {len(unused_packages)} potentially unused packages:\n\n")
            f.write("| Package | Version | Confidence |\n")
            f.write("| ------- | ------- | ---------- |\n")
            for pkg in unused_packages:
                f.write(f"| {pkg['name']} | {pkg['version']} | {pkg['confidence']} |\n")

            f.write("\n## Removal Commands\n\n")
            f.write("```bash\n")
            for pkg in unused_packages:
                f.write(f"pip uninstall -y {pkg['name']}\n")
            f.write("```\n\n")

            f.write(
                "**Note:** Before removing packages, verify they are truly unused. Some may be required indirectly or for non-standard imports.\n"
            )
        else:
            f.write(
                "No unused packages found. Your dependency list appears to be clean!\n"
            )

    # Export cleanup commands
    if unused_packages:
        cleanup_script = os.path.join(output_dir, "cleanup_dependencies.sh")
        export_cleanup_commands(unused_packages, cleanup_script)
        print(f"Cleanup script generated: {cleanup_script}")

    print(f"Report saved to: {unused_report_file}")
    return unused_report_file


if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()

    run_dependency_cleanup(project_dir)
