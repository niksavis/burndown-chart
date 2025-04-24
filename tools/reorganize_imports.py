"""
Import Reorganization Tool

This script helps reorganize imports in Python modules according to project conventions.
It creates a backup before making any changes and operates in a safe, controlled manner.
"""

import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime


def backup_file(file_path):
    """Create a backup of the file before modifying it."""
    backup_path = str(file_path) + f".bak-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    return backup_path


def parse_imports(content):
    """
    Parse and categorize imports in the file content.
    Returns dict with keys: 'std_lib', 'third_party', 'application'.
    """
    import_pattern = re.compile(
        r"^(?:from\s+(\S+)\s+import\s+(.+?)$|import\s+(.+?)$)", re.MULTILINE
    )

    std_lib_imports = []
    third_party_imports = []
    application_imports = []

    # Standard library modules list (can be extended)
    std_libs = [
        "os",
        "sys",
        "io",
        "re",
        "datetime",
        "time",
        "math",
        "random",
        "json",
        "csv",
        "collections",
        "pathlib",
        "shutil",
        "logging",
        "traceback",
        "functools",
        "itertools",
        "typing",
        "abc",
        "copy",
        "warnings",
    ]

    # Third-party modules list (can be extended)
    third_party = [
        "dash",
        "pandas",
        "numpy",
        "plotly",
        "dash_bootstrap_components",
        "matplotlib",
        "networkx",
        "flask",
        "werkzeug",
        "scipy",
        "pytest",
    ]

    for match in import_pattern.finditer(content):
        if match.group(1):  # 'from X import Y' pattern
            module = match.group(1)
            # imports = match.group(2)

            if module in std_libs or module.split(".")[0] in std_libs:
                std_lib_imports.append(match.group(0))
            elif module in third_party or module.split(".")[0] in third_party:
                third_party_imports.append(match.group(0))
            else:
                application_imports.append(match.group(0))
        elif match.group(3):  # 'import X' pattern
            imports = match.group(3).split(",")
            for imp in imports:
                imp = imp.strip()
                if imp in std_libs or imp.split(".")[0] in std_libs:
                    std_lib_imports.append(f"import {imp}")
                elif imp in third_party or imp.split(".")[0] in third_party:
                    third_party_imports.append(f"import {imp}")
                else:
                    application_imports.append(f"import {imp}")

    return {
        "std_lib": std_lib_imports,
        "third_party": third_party_imports,
        "application": application_imports,
    }


def create_import_section(imports):
    """Create a properly formatted import section."""
    if not imports:
        return ""

    return "\n".join(sorted(imports)) + "\n"


def reorganize_file_imports(file_path, dry_run=True):
    """Reorganize imports in a file according to conventions."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract docstring if present
    docstring_pattern = re.compile(r'^"""(.+?)"""', re.DOTALL)
    docstring_match = docstring_pattern.search(content)
    docstring = f'"""{docstring_match.group(1)}"""\n\n' if docstring_match else ""

    # Remove existing imports
    content_without_imports = re.sub(
        r"^(?:from\s+\S+\s+import\s+.+?$|import\s+.+?$)",
        "",
        content,
        flags=re.MULTILINE,
    )

    # Analyze imports
    import_dict = parse_imports(content)

    # Create new import section
    import_section = (
        "#######################################################################\n"
    )
    import_section += "# IMPORTS\n"
    import_section += (
        "#######################################################################\n"
    )

    if import_dict["std_lib"]:
        import_section += "# Standard library imports\n"
        import_section += create_import_section(import_dict["std_lib"])
        if import_dict["third_party"] or import_dict["application"]:
            import_section += "\n"

    if import_dict["third_party"]:
        import_section += "# Third-party library imports\n"
        import_section += create_import_section(import_dict["third_party"])
        if import_dict["application"]:
            import_section += "\n"

    if import_dict["application"]:
        import_section += "# Application imports\n"
        import_section += create_import_section(import_dict["application"])

    # Construct new content
    new_content = docstring + import_section + "\n" + content_without_imports.lstrip()

    if dry_run:
        print(f"Dry run for {file_path}:")
        print("-" * 40)
        print(new_content[:500] + "..." if len(new_content) > 500 else new_content)
        print("-" * 40)
        return None

    # Create backup
    backup_path = backup_file(file_path)

    # Write changes
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return backup_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python reorganize_imports.py <file_path> [--dry-run]")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    if not file_path.exists():
        print(f"Error: File {file_path} not found")
        sys.exit(1)

    if dry_run:
        print("Running in DRY RUN mode - no changes will be made")

    backup_path = reorganize_file_imports(file_path, dry_run)

    if not dry_run:
        print(f"✓ Imports reorganized for {file_path}")
        print(f"✓ Backup created at {backup_path}")


if __name__ == "__main__":
    main()
