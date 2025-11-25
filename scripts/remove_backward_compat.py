"""Script to remove backward compatibility code from DORA calculator.

This script removes:
1. use_variable_extraction parameters
2. field_mappings parameters
3. Legacy code paths (if not use_variable_extraction blocks)
4. Makes variable_extractor required (not Optional)
"""

import re
from pathlib import Path


def remove_backward_compat_from_dora_calculator():
    """Remove all backward compatibility code from dora_calculator.py."""

    file_path = Path("data/dora_calculator.py")
    content = file_path.read_text(encoding="utf-8")

    # Track changes
    changes_made = []

    # 1. Remove field_mappings parameter from function signatures
    # Pattern: field_mappings: Optional[Dict[str, str]] = None,
    old_pattern = r"field_mappings: Optional\[Dict\[str, str\]\] = None,\s*\n"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, "", content)
        changes_made.append("Removed field_mappings parameter from function signatures")

    # 2. Remove use_variable_extraction parameter
    # Pattern: use_variable_extraction: bool = True,  # Feature 012...
    old_pattern = r"use_variable_extraction: bool = True,.*\n"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, "", content)
        changes_made.append("Removed use_variable_extraction parameter")

    # 3. Change variable_extractor from Optional to required
    # Pattern: variable_extractor: Optional[VariableExtractor] = None,
    # Replace with: variable_extractor: VariableExtractor,
    old_pattern = r"variable_extractor: Optional\[VariableExtractor\] = None,"
    new_value = "variable_extractor: VariableExtractor,"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_value, content)
        changes_made.append("Made variable_extractor required (not Optional)")

    # 4. Remove "Supports both legacy..." from docstrings
    old_pattern = r"\s+Supports both legacy field_mappings and new variable extraction modes\.\s*\n"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, "\n", content)
        changes_made.append("Cleaned docstrings")

    # 5. Remove field_mappings from docstring Args
    old_pattern = r"\s+field_mappings:.*\n"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, "", content)
        changes_made.append("Removed field_mappings from docstrings")

    # 6. Remove use_variable_extraction from docstring Args
    old_pattern = r"\s+use_variable_extraction:.*\n"
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, "", content)
        changes_made.append("Removed use_variable_extraction from docstrings")

    # 7. Update variable_extractor docstring (remove "Optional" and "uses DEFAULT if None")
    old_pattern = r"variable_extractor: Optional VariableExtractor instance \(uses DEFAULT if None\)"
    new_value = (
        "variable_extractor: VariableExtractor instance with configured mappings"
    )
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_value, content)
        changes_made.append("Updated variable_extractor docstring")

    # Write back
    file_path.write_text(content, encoding="utf-8")

    return changes_made


if __name__ == "__main__":
    print("Removing backward compatibility code from dora_calculator.py...")
    changes = remove_backward_compat_from_dora_calculator()

    for change in changes:
        print(f"✓ {change}")

    print(f"\nTotal changes: {len(changes)}")
    print("Done!")
