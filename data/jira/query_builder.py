"""
JIRA Query Builder Module

This module handles JQL query construction and modification to ensure
parent issue types are included in queries while being excluded from calculations.

Architecture:
- Parse user's JQL query for issuetype clause
- Add configured parent types (Epic, Initiative, etc.) to the clause
- Maintain backward compatibility (empty list = no modification)
- Handle edge cases (already includes types, no type filter, etc.)
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


def build_jql_with_parent_types(user_jql: str, parent_types: List[str]) -> str:
    """
    Ensure parent types are included in JQL query.

    This modifies the user's JQL query to include parent issue types
    in the issuetype clause, enabling parent issues to be fetched
    while still being filtered from calculations later.

    Logic:
    1. Parse user's JQL for "issuetype in (...)" clause
    2. If found: Add parent types to the type list
    3. If not found: User query has no type restriction (already includes all)
    4. If parent types already present: No modification needed

    Args:
        user_jql: User's JQL query string
        parent_types: List of parent type names (e.g., ["Epic", "Initiative"])

    Returns:
        Modified JQL query with parent types included

    Examples:
        >>> build_jql_with_parent_types(
        ...     'project = PROJ AND issuetype in (Story, Bug)',
        ...     ['Epic']
        ... )
        'project = PROJ AND issuetype in (Story, Bug, Epic)'

        >>> build_jql_with_parent_types(
        ...     'project = PROJ',  # No type restriction
        ...     ['Epic']
        ... )
        'project = PROJ'  # No modification needed

        >>> build_jql_with_parent_types(
        ...     'issuetype in (Story, Bug, Epic)',
        ...     ['Epic']
        ... )
        'issuetype in (Story, Bug, Epic)'  # Already includes Epic
    """
    if not parent_types:
        logger.debug("[Query Builder] No parent types configured - query unchanged")
        return user_jql

    if not user_jql or not user_jql.strip():
        logger.warning("[Query Builder] Empty JQL query provided")
        return user_jql

    # Pattern to match: issuetype in (Type1, Type2, "Type with spaces", ...)
    # Handles:
    # - Case insensitive "issuetype"
    # - Optional whitespace around operators
    # - Quoted types with spaces
    # - Comma-separated list
    pattern = r"\bissuetype\s+in\s*\(([^)]+)\)"

    match = re.search(pattern, user_jql, re.IGNORECASE)

    if not match:
        # No issuetype restriction - query includes all types by default
        logger.info(
            "[Query Builder] No issuetype filter in JQL - "
            "parent types already included (no modification needed)"
        )
        return user_jql

    # Extract the types list: "Story, Bug, Task" or "Story", "Bug", Task
    types_str = match.group(1)

    # Parse types from string, handling quotes and whitespace
    existing_types = _parse_issue_types(types_str)

    # Check if parent types already present
    existing_types_lower = {t.lower() for t in existing_types}
    types_to_add = [pt for pt in parent_types if pt.lower() not in existing_types_lower]

    if not types_to_add:
        logger.info(
            "[Query Builder] Parent types already in JQL - no modification needed"
        )
        logger.debug(f"[Query Builder] Existing types: {existing_types}")
        return user_jql

    # Add parent types to list
    modified_types = existing_types + types_to_add

    # Rebuild issuetype clause with proper quoting
    new_clause = _build_issuetype_clause(modified_types)

    # Replace in original JQL
    modified_jql = user_jql[: match.start()] + new_clause + user_jql[match.end() :]

    logger.info(
        f"[Query Builder] Added {len(types_to_add)} parent type(s) to JQL: "
        f"{', '.join(types_to_add)}"
    )
    logger.debug(f"[Query Builder] Original JQL: {user_jql}")
    logger.debug(f"[Query Builder] Modified JQL: {modified_jql}")

    return modified_jql


def _parse_issue_types(types_str: str) -> List[str]:
    """
    Parse issue types from JQL issuetype clause.

    Handles:
    - Quoted types: "Story", 'Bug'
    - Unquoted types: Story, Bug
    - Mixed: "Story with spaces", Bug, Task
    - Whitespace: " Story ", Bug

    Args:
        types_str: Types string from JQL (e.g., '"Story", Bug, "New Feature"')

    Returns:
        List of cleaned type names

    Examples:
        >>> _parse_issue_types('"Story", Bug, Task')
        ['Story', 'Bug', 'Task']

        >>> _parse_issue_types('Story, "New Feature", Task')
        ['Story', 'New Feature', 'Task']
    """
    if not types_str:
        return []

    # Split by comma
    parts = types_str.split(",")

    types = []
    for part in parts:
        # Strip whitespace
        cleaned = part.strip()

        # Remove quotes if present
        if cleaned.startswith(('"', "'")):
            cleaned = cleaned[1:]
        if cleaned.endswith(('"', "'")):
            cleaned = cleaned[:-1]

        cleaned = cleaned.strip()

        if cleaned:
            types.append(cleaned)

    return types


def _build_issuetype_clause(types: List[str]) -> str:
    """
    Build issuetype clause with proper quoting.

    Rules:
    - Types with spaces or special chars: Quote with double quotes
    - Simple types (alphanumeric + hyphen): No quotes needed

    Args:
        types: List of issue type names

    Returns:
        JQL issuetype clause (e.g., 'issuetype in (Story, "New Feature", Bug)')

    Examples:
        >>> _build_issuetype_clause(['Story', 'Bug', 'Task'])
        'issuetype in (Story, Bug, Task)'

        >>> _build_issuetype_clause(['Story', 'New Feature', 'Bug'])
        'issuetype in (Story, "New Feature", Bug)'
    """
    if not types:
        return "issuetype in ()"

    # Quote types that contain spaces or special characters
    quoted_types = []
    for t in types:
        if " " in t or "," in t or '"' in t or "'" in t:
            # Escape double quotes inside type name
            escaped = t.replace('"', '\\"')
            quoted_types.append(f'"{escaped}"')
        else:
            # Simple type - no quotes needed
            quoted_types.append(t)

    types_list = ", ".join(quoted_types)
    return f"issuetype in ({types_list})"


def extract_parent_types_from_config(config: dict) -> List[str]:
    """
    Extract parent issue types from configuration.

    Args:
        config: Configuration dictionary with field_mappings

    Returns:
        List of parent type names (e.g., ["Epic", "Initiative"])

    Example:
        >>> config = {
        ...     "field_mappings": {
        ...         "general": {
        ...             "parent_issue_types": ["Epic", "Initiative"]
        ...         }
        ...     }
        ... }
        >>> extract_parent_types_from_config(config)
        ['Epic', 'Initiative']
    """
    parent_types = (
        config.get("field_mappings", {})
        .get("general", {})
        .get("parent_issue_types", [])
    )

    # Ensure it's a list and filter empty strings
    if not isinstance(parent_types, list):
        logger.warning(
            f"[Query Builder] parent_issue_types is not a list: {type(parent_types)}"
        )
        return []

    # Filter None and empty strings
    cleaned_types = [t for t in parent_types if t and isinstance(t, str)]

    if len(cleaned_types) != len(parent_types):
        logger.warning(
            f"[Query Builder] Filtered {len(parent_types) - len(cleaned_types)} "
            "invalid parent type entries"
        )

    return cleaned_types
