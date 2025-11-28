"""Clean up remaining legacy code blocks from DORA calculator."""

import re
from pathlib import Path


def clean_legacy_blocks():
    """Remove broken legacy code blocks."""

    file_path = Path("data/dora_calculator.py")
    lines = file_path.read_text(encoding="utf-8").split("\n")

    cleaned_lines = []
    skip_until_else = False
    skip_until_end = False
    indent_level = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for broken "if not" blocks (incomplete conditionals from regex cleanup)
        if re.search(r"^\s+if not\s*#.*Legacy", line):
            # Found broken legacy block start, skip until matching else or end
            indent_level = len(line) - len(line.lstrip())
            skip_until_else = True
            i += 1
            continue

        if skip_until_else:
            current_indent = len(line) - len(line.lstrip())

            # Found else at same indent level
            if current_indent == indent_level and line.strip().startswith("else:"):
                skip_until_else = False
                skip_until_end = True  # Now skip the else block too
                i += 1
                continue

            # Still inside the broken if block
            if current_indent > indent_level or line.strip() == "":
                i += 1
                continue

            # Exited the block without finding else
            skip_until_else = False

        if skip_until_end:
            current_indent = len(line) - len(line.lstrip())

            # Still inside else block
            if current_indent > indent_level or line.strip() == "":
                i += 1
                continue

            # Exited else block
            skip_until_end = False

        # Remove lines that reference field_mappings in variable assignments
        if re.search(r"field_mappings\[|field_mappings\.get\(", line):
            i += 1
            continue

        # Remove broken incomplete conditionals
        if re.search(r"if field_mappings is None or.*not in\s*return", line):
            # This is a broken line, skip it
            i += 1
            continue

        cleaned_lines.append(line)
        i += 1

    # Write back
    content = "\n".join(cleaned_lines)
    file_path.write_text(content, encoding="utf-8")

    print(f"Cleaned up legacy blocks. Removed {len(lines) - len(cleaned_lines)} lines.")


if __name__ == "__main__":
    clean_legacy_blocks()
