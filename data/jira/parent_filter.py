"""
Parent Issue Type Filter Module

This module filters out parent issue types (Epic, Initiative, Feature, etc.)
from metrics calculations while keeping them in the dataset for parent field population.

Parent types are:
1. Included in JQL queries (via query_builder.py) to fetch their data
2. Excluded from metrics (via this module) to prevent double-counting
3. Available for parent field lookups and Active Work Timeline display
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def filter_out_parent_types(
    issues: list[dict[str, Any]], parent_types: list[str]
) -> list[dict[str, Any]]:
    """
    Filter out parent issue types from a list of issues.

    Parent types (Epic, Initiative, Feature, etc.) are fetched to populate parent
    fields but should not be counted in project scope metrics to avoid double-counting
    (since their child stories/tasks are already counted).

    Args:
        issues: List of JIRA issue dictionaries
        parent_types: List of parent issue type names to exclude (case-insensitive)

    Returns:
        Filtered list with parent types removed

    Example:
        >>> issues = [
        ...     {"fields": {"issuetype": {"name": "Story"}}},
        ...     {"fields": {"issuetype": {"name": "Epic"}}},
        ...     {"fields": {"issuetype": {"name": "Task"}}}
        ... ]
        >>> filtered = filter_out_parent_types(issues, ["Epic"])
        >>> len(filtered)
        2
    """
    if not parent_types:
        return issues

    # Normalize parent types to lowercase for case-insensitive comparison
    parent_types_lower = {pt.lower() for pt in parent_types}

    filtered_issues = []
    excluded_count = 0

    for issue in issues:
        try:
            # Extract issue type - handle both nested (JIRA API) and flat (database) formats
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                # Nested format (JIRA API): issue.fields.issuetype.name
                issue_type = issue["fields"]["issuetype"]["name"]
            else:
                # Flat format (database): issue.issue_type
                issue_type = issue.get("issue_type", "")

            # Check if this issue type is a parent type
            if issue_type.lower() in parent_types_lower:
                excluded_count += 1
                logger.debug(
                    f"[ParentFilter] Excluding {issue_type} issue: "
                    f"{issue.get('key', 'UNKNOWN')}"
                )
                continue

            # Keep non-parent issues
            filtered_issues.append(issue)

        except (KeyError, TypeError) as e:
            # Log error but don't fail - include issue if we can't determine type
            logger.warning(
                f"[ParentFilter] Could not determine issue type for {issue.get('key', 'UNKNOWN')}: {e}"
            )
            filtered_issues.append(issue)

    logger.info(
        f"[ParentFilter] Filtered {len(issues)} issues → {len(filtered_issues)} "
        f"(excluded {excluded_count} parent issues)"
    )

    return filtered_issues


def extract_parent_types_from_issues(
    issues: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """
    Extract unique parent issue types found in a dataset.

    Useful for discovery and validation of parent type configuration.

    Args:
        issues: List of JIRA issue dictionaries

    Returns:
        List of dicts with 'name' and 'key' for each unique issue type

    Example:
        >>> issues = [...]
        >>> types = extract_parent_types_from_issues(issues)
        >>> print(types)
        [{'name': 'Epic', 'key': 'EPIC'}, {'name': 'Initiative', 'key': 'INIT'}]
    """
    issue_types = set()

    for issue in issues:
        try:
            # Extract issue type - handle both formats
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                issue_type = issue["fields"]["issuetype"]["name"]
            else:
                issue_type = issue.get("issue_type", "")

            if issue_type:
                issue_types.add(issue_type)

        except (KeyError, TypeError):
            continue

    # Return sorted list of dicts for consistency
    return sorted(
        [{"name": t, "key": t.upper()} for t in issue_types], key=lambda x: x["name"]
    )
