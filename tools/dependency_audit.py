"""
Dependency Audit Tool

This script analyzes project dependencies, checks for outdated packages,
identifies security vulnerabilities, and generates an update plan.
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime
import pkg_resources


def get_installed_packages():
    """Get all installed packages and their versions."""
    installed_packages = {}
    for package in pkg_resources.working_set:
        installed_packages[package.key] = package.version
    return installed_packages


def get_requirements_files(project_dir):
    """Find all requirements.txt files in the project."""
    return list(Path(project_dir).glob("**/requirements*.txt"))


def parse_requirements_file(req_file):
    """Parse a requirements.txt file and extract dependencies."""
    dependencies = []
    with open(req_file, "r") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Handle line continuation
            if line.endswith("\\"):
                line = line[:-1].strip()

            # Remove inline comments
            if "#" in line:
                line = line.split("#", 1)[0].strip()

            # Handle various formats: package==1.0.0, package>=1.0.0, etc.
            match = re.match(
                r"^([a-zA-Z0-9_.-]+)(?:[<>=!~]+([a-zA-Z0-9_.-]+))?.*$", line
            )
            if match:
                package_name = match.group(1).lower()
                dependencies.append(package_name)

    return dependencies


def find_imports_in_file(file_path):
    """Extract imports from a Python file."""
    imports = set()
    import_pattern = re.compile(
        r"^(?:from\s+(\S+)\s+import|import\s+(\S+))", re.MULTILINE
    )

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        try:
            content = f.read()
            for match in import_pattern.finditer(content):
                module = match.group(1) or match.group(2)
                # Get the top-level module
                top_module = module.split(".")[0]
                imports.add(top_module)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return imports


def find_all_imports(project_dir):
    """Find all import statements in Python files."""
    all_imports = set()
    python_files = Path(project_dir).glob("**/*.py")

    for py_file in python_files:
        if not any(
            part.startswith(".") for part in py_file.parts
        ):  # Skip hidden directories
            imports = find_imports_in_file(py_file)
            all_imports.update(imports)

    return all_imports


def check_outdated_packages():
    """Check for outdated packages using pip list --outdated."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error checking outdated packages: {e}")
        return []


def check_security_vulnerabilities():
    """Check for security vulnerabilities using safety check."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "safety"],
            capture_output=True,
            text=True,
            check=False,
        )

        result = subprocess.run(
            ["safety", "check", "--json"], capture_output=True, text=True
        )

        if result.returncode == 0:
            return {"vulnerabilities": []}
        else:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"vulnerabilities": [], "error": result.stderr}
    except Exception as e:
        print(f"Error checking security vulnerabilities: {e}")
        return {"vulnerabilities": [], "error": str(e)}


def generate_update_plan(outdated, vulnerabilities):
    """Generate a dependency update plan based on outdated packages and vulnerabilities."""
    update_plan = []

    # Process outdated packages
    for package in outdated:
        update_plan.append(
            {
                "package": package.get("name"),
                "current_version": package.get("version"),
                "latest_version": package.get("latest_version"),
                "reason": "outdated",
                "priority": "medium",
            }
        )

    # Process vulnerabilities
    for vuln in vulnerabilities.get("vulnerabilities", []):
        # Find if the vulnerable package is already in the update plan
        package_name = vuln.get("package_name")
        existing = next((p for p in update_plan if p["package"] == package_name), None)

        if existing:
            existing["reason"] = f"{existing['reason']}, security vulnerability"
            existing["priority"] = "high"
        else:
            update_plan.append(
                {
                    "package": package_name,
                    "current_version": vuln.get("installed_version"),
                    "latest_version": vuln.get("fixed_version") or "latest",
                    "reason": "security vulnerability",
                    "priority": "high",
                }
            )

    return sorted(update_plan, key=lambda x: 0 if x["priority"] == "high" else 1)


def identify_unused_dependencies(installed_packages, used_imports):
    """Identify installed packages that aren't being imported."""
    potentially_unused = []

    for package_name in installed_packages:
        # Skip standard library modules
        if package_name in sys.builtin_module_names:
            continue

        if package_name not in used_imports:
            potentially_unused.append(package_name)

    return potentially_unused


def run_dependency_audit(project_dir):
    """Run a full dependency audit."""
    print(f"Running dependency audit for {project_dir}...")

    # Get installed packages
    print("Checking installed packages...")
    installed_packages = get_installed_packages()
    print(f"Found {len(installed_packages)} installed packages")

    # Find requirements files
    req_files = get_requirements_files(project_dir)
    print(f"Found {len(req_files)} requirements files")

    # Parse requirements files
    print("Parsing requirements files...")
    req_dependencies = set()
    for req_file in req_files:
        deps = parse_requirements_file(req_file)
        req_dependencies.update(deps)
    print(f"Found {len(req_dependencies)} dependencies in requirements files")

    # Find imports
    print("Scanning Python files for imports...")
    used_imports = find_all_imports(project_dir)
    print(f"Found {len(used_imports)} unique imports in the project")

    # Check for outdated packages
    print("Checking for outdated packages...")
    outdated = check_outdated_packages()
    print(f"Found {len(outdated)} outdated packages")

    # Check for security vulnerabilities
    print("Checking for security vulnerabilities...")
    vulnerabilities = check_security_vulnerabilities()
    vuln_count = len(vulnerabilities.get("vulnerabilities", []))
    print(f"Found {vuln_count} security vulnerabilities")

    # Generate update plan
    update_plan = generate_update_plan(outdated, vulnerabilities)

    # Identify unused dependencies
    unused = identify_unused_dependencies(installed_packages, used_imports)

    # Generate report
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = os.path.join(project_dir, f"dependency_audit_{timestamp}.md")

    with open(report_file, "w") as f:
        f.write("# Dependency Audit Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Update plan
        f.write("## Package Update Plan\n\n")
        if update_plan:
            f.write(
                "| Package | Current Version | Latest Version | Reason | Priority |\n"
            )
            f.write(
                "| ------- | --------------- | -------------- | ------ | -------- |\n"
            )
            for pkg in update_plan:
                f.write(
                    f"| {pkg['package']} | {pkg['current_version']} | {pkg['latest_version']} | {pkg['reason']} | {pkg['priority']} |\n"
                )
        else:
            f.write("No updates required. All packages are up to date.\n")

        # Unused packages
        f.write("\n## Potentially Unused Dependencies\n\n")
        if unused:
            f.write(
                "The following packages are installed but don't appear to be imported in the project:\n\n"
            )
            f.write("| Package | Installed Version |\n")
            f.write("| ------- | ---------------- |\n")
            for pkg in unused:
                version = installed_packages.get(pkg, "unknown")
                f.write(f"| {pkg} | {version} |\n")

            f.write(
                "\n**Note:** This doesn't necessarily mean these packages should be removed. Some might be used indirectly or in non-Python files.\n"
            )
        else:
            f.write("All installed packages appear to be used in the project.\n")

    print(f"\nReport saved to {report_file}")
    return report_file


if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()

    run_dependency_audit(project_dir)
