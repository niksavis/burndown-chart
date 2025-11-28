"""Remove broken if/else blocks from DORA calculator."""

from pathlib import Path


def fix_broken_conditionals():
    """Remove broken if statements and keep only the NEW variable extraction code."""

    file_path = Path("data/dora_calculator.py")
    lines = file_path.read_text(encoding="utf-8").split("\n")

    cleaned_lines = []
    in_broken_if = False
    in_else_block = False
    if_indent = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect broken if with comment "# NEW: Variable extraction mode"
        if stripped.startswith("if") and "# NEW: Variable extraction mode" in line:
            # This is a broken if - just remove it, keep the indented code that follows
            in_broken_if = True
            if_indent = len(line) - len(line.lstrip())
            i += 1
            continue

        # If we're in a broken if block
        if in_broken_if:
            current_indent = len(line) - len(line.lstrip())

            # Check if we hit the else block
            if current_indent == if_indent and stripped.startswith("else:"):
                # Start skipping the else block (legacy code)
                in_broken_if = False
                in_else_block = True
                i += 1
                continue

            # This is content of the broken if - keep it but dedent
            if current_indent > if_indent:
                # De-indent by removing the if-block's extra indentation
                dedented_line = " " * if_indent + line.lstrip()
                cleaned_lines.append(dedented_line)
                i += 1
                continue

            # We've exited the if block without hitting else
            in_broken_if = False

        # If we're in the else block (legacy code to skip)
        if in_else_block:
            current_indent = len(line) - len(line.lstrip())

            # Still inside the else block
            if current_indent > if_indent or stripped == "":
                i += 1
                continue

            # Exited the else block
            in_else_block = False

        # Normal line - keep it
        cleaned_lines.append(line)
        i += 1

    # Write back
    content = "\n".join(cleaned_lines)
    file_path.write_text(content, encoding="utf-8")

    removed = len(lines) - len(cleaned_lines)
    print(f"Removed {removed} lines from broken if/else blocks")
    return removed


if __name__ == "__main__":
    fix_broken_conditionals()
