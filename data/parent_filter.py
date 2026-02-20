"""
Parent Issue Filter Module

This module provides functions to dynamically filter out parent issues
based on the configured parent field mapping (not hardcoded "Epic" type).

Architecture:
- Extracts all unique parent keys from issues' parent field
- Filters out any issue whose key appears as a parent (regardless of issue type)
- Works with any parent type: Epic, Feature, Initiative, Portfolio Epic, etc.
"""

import logging

logger = logging.getLogger(__name__)


def extract_parent_keys(issues: list[dict], parent_field: str) -> set[str]:
    """
    Extract unique parent keys from issues' parent field.

    This dynamically detects which issues are parents by checking what keys
    appear in the parent field across all issues.

    Args:
        issues: List of JIRA issues
        parent_field: Parent field name (e.g., "parent" or "customfield_10006")

    Returns:
        Set of parent keys (e.g., {"A942-3406", "A942-3408"})
    """
    if not parent_field:
        return set()

    parent_keys = set()

    for issue in issues:
        # Try top-level field first
        parent_value = issue.get(parent_field)

        # Try custom_fields dict if not found at top level
        if not parent_value and parent_field.startswith("customfield_"):
            custom_fields = issue.get("custom_fields", {})
            parent_value = custom_fields.get(parent_field)

        if not parent_value:
            continue

        # Extract key from parent value
        # Parent can be: string "A942-3406" or dict {"key": "A942-3406", ...}
        if isinstance(parent_value, dict):
            parent_key = parent_value.get("key")
        elif isinstance(parent_value, str):
            parent_key = parent_value.strip()
        else:
            parent_key = None

        if parent_key:
            parent_keys.add(parent_key)

    return parent_keys


def filter_parent_issues(
    issues: list[dict], parent_field: str, log_prefix: str = "FILTER"
) -> list[dict]:
    """
    Filter out parent issues from list.

    This removes any issue whose key appears as a parent in OTHER issues,
    regardless of the parent's issue type.

    Args:
        issues: List of JIRA issues
        parent_field: Parent field name from configuration
        log_prefix: Prefix for log messages

    Returns:
        Filtered list with parent issues removed
    """
    if not parent_field:
        logger.debug(f"[{log_prefix}] No parent field configured - no filtering")
        return issues

    # Extract all parent keys
    parent_keys = extract_parent_keys(issues, parent_field)

    if not parent_keys:
        logger.debug(f"[{log_prefix}] No parent keys found - no filtering")
        return issues

    # Filter out issues whose keys are parents
    issues_before = len(issues)
    filtered = [i for i in issues if i.get("issue_key") not in parent_keys]
    filtered_count = issues_before - len(filtered)

    if filtered_count > 0:
        logger.info(
            f"[{log_prefix}] Filtered out {filtered_count} parent issues "
            f"(found {len(parent_keys)} unique parent keys)"
        )

    return filtered
