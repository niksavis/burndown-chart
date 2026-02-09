"""Completed Items Manager for Active Work Tab.

This module provides functions for displaying recently completed items in the
Active Work tab, grouped by ISO calendar weeks (Monday-Sunday).

Key Functions:
    get_completed_items_by_week() -> Dict: Get completed issues bucketed by week
    _format_week_label() -> str: Format week label for display
"""

import logging
from typing import Dict, List, Optional
from collections import OrderedDict

from data.iso_week_bucketing import get_last_n_weeks, bucket_issues_by_week
from data.parent_filter import extract_parent_keys, filter_parent_issues

logger = logging.getLogger(__name__)


def get_completed_items_by_week(
    issues: List[Dict],
    n_weeks: int = 2,
    flow_end_statuses: Optional[List[str]] = None,
    parent_field: Optional[str] = None,
) -> Dict[str, Dict]:
    """Bucket completed issues into current week and last week.

    Filters issues by completion status and resolutiondate, then groups them
    into ISO calendar weeks. Returns current week first, then last week.

    Args:
        issues: List of JIRA issue dictionaries
        n_weeks: Number of weeks to include (default: 2 for current + last week)
        flow_end_statuses: List of statuses indicating completion
            (default: ["Done", "Closed", "Resolved"])
        parent_field: Field name for parent/epic grouping (e.g., "parent")

    Returns:
        OrderedDict mapping week_label -> dict with:
        {
            "display_label": "Current Week (Feb 3-9)",
            "issues": [issue1, issue2, ...],
            "is_current": True/False,
            "total_issues": 5,
            "total_epics_closed": 1,
            "total_epics_linked": 2,
            "total_points": 12.0
        }

    Example:
        >>> issues = [...]  # Issues from database
        >>> result = get_completed_items_by_week(issues, n_weeks=2)
        >>> result["2026-W06"]["display_label"]
        "Current Week (Feb 3-9)"
        >>> len(result["2026-W06"]["issues"])
        5
    """
    # Default completion statuses
    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]

    logger.info(
        f"[COMPLETED ITEMS] Filtering completed issues for last {n_weeks} weeks, "
        f"using flow_end_statuses={flow_end_statuses}, parent_field={parent_field}"
    )

    # Filter to only completed issues with resolutiondate
    completed_issues = []
    for issue in issues:
        # Access status - try flat format first (database), then JIRA nested format
        status = issue.get("status")
        if not status:
            status = issue.get("fields", {}).get("status", {}).get("name", "")

        # Access resolutiondate - try flat format first (database), then JIRA nested format
        resolutiondate = issue.get("resolutiondate")
        if not resolutiondate:
            resolutiondate = issue.get("resolved")
        if not resolutiondate:
            resolutiondate = issue.get("fields", {}).get("resolutiondate")

        # Debug: Log first few issues details
        issue_key = issue.get("key", issue.get("issue_key", "unknown"))
        if len(completed_issues) < 3:  # Only log first few to avoid spam
            logger.info(
                f"[COMPLETED ITEMS DEBUG] Issue {issue_key}: status={status}, "
                f"resolutiondate={resolutiondate}, "
                f"in flow_end_statuses={status in flow_end_statuses}"
            )

        if status in flow_end_statuses and resolutiondate:
            completed_issues.append(issue)

    logger.info(
        f"[COMPLETED ITEMS] Found {len(completed_issues)} completed issues with resolutiondate (out of {len(issues)} total)"
    )

    if not completed_issues:
        # Return empty structure for consistency
        logger.warning(
            "[COMPLETED ITEMS] No completed issues found - returning empty structure"
        )
        return _create_empty_week_structure(n_weeks)

    # Bucket issues by week using resolutiondate
    logger.info(
        f"[COMPLETED ITEMS] Bucketing {len(completed_issues)} completed issues by week"
    )
    buckets = bucket_issues_by_week(
        issues=completed_issues, date_field="resolutiondate", n_weeks=n_weeks
    )

    # Log bucket results
    for week_label, week_issues in buckets.items():
        logger.info(f"[COMPLETED ITEMS] Week {week_label}: {len(week_issues)} issues")

    # Get week definitions for formatting
    weeks = get_last_n_weeks(n_weeks)

    # Determine which week is current (last one in the list)
    current_week_label = weeks[-1][0] if weeks else None

    # Format result with ordered dict (current week first)
    result = OrderedDict()

    # Sort weeks in reverse order (current week first)
    for week_label, monday, sunday in reversed(weeks):
        week_issues = buckets.get(week_label, [])

        parent_keys = set()
        closed_epic_keys = set()
        display_issues = week_issues
        epic_groups = []
        if parent_field:
            parent_keys = extract_parent_keys(week_issues, parent_field)
            closed_epic_keys = _get_closed_epic_keys(week_issues, parent_keys)
            display_issues = filter_parent_issues(
                week_issues, parent_field, log_prefix="COMPLETED ITEMS"
            )
            epic_groups = _group_issues_by_epic(display_issues, parent_field, issues)

        # Calculate totals
        total_issues = len(display_issues)
        total_epics_linked = len(parent_keys)
        total_epics_closed = len(closed_epic_keys)
        total_points = sum(issue.get("points", 0.0) or 0.0 for issue in display_issues)

        # Format display label
        display_label = _format_week_label(
            week_label=week_label,
            monday=monday,
            sunday=sunday,
            is_current=(week_label == current_week_label),
        )

        result[week_label] = {
            "display_label": display_label,
            "issues": display_issues,
            "is_current": week_label == current_week_label,
            "total_issues": total_issues,
            "total_epics_closed": total_epics_closed,
            "total_epics_linked": total_epics_linked,
            "total_points": total_points,
            "epic_groups": epic_groups,
        }

        logger.info(
            f"[COMPLETED ITEMS] {display_label}: {total_issues} issues, "
            f"{total_epics_closed} closed epics, {total_epics_linked} linked epics, "
            f"{total_points:.1f} points"
        )

    return result


def _format_week_label(
    week_label: str, monday, sunday, is_current: bool = False
) -> str:
    """Format week label for display.

    Args:
        week_label: ISO week label (e.g., "2026-W06")
        monday: Monday date object for the week
        sunday: Sunday date object for the week
        is_current: Whether this is the current week

    Returns:
        Formatted label like "Current Week (Feb 3-9)" or "Last Week (Jan 27 - Feb 2)"

    Examples:
        >>> _format_week_label("2026-W06", date(2026, 2, 3), date(2026, 2, 9), True)
        "Current Week (Feb 3-9)"
        >>> _format_week_label("2026-W05", date(2026, 1, 27), date(2026, 2, 2), False)
        "Last Week (Jan 27 - Feb 2)"
    """
    # Format dates - strip leading zeros from day
    monday_str = f"{monday.strftime('%b')} {monday.day}"
    sunday_str = f"{sunday.strftime('%b')} {sunday.day}"

    # Handle month boundary
    if monday.month == sunday.month:
        date_range = f"{monday.strftime('%b')} {monday.day}-{sunday.day}"
    else:
        date_range = f"{monday_str} - {sunday_str}"

    # Add prefix
    prefix = "Current Week" if is_current else "Last Week"

    return f"{prefix} ({date_range})"


def _create_empty_week_structure(n_weeks: int = 2) -> Dict[str, Dict]:
    """Create empty week structure when no completed items exist.

    Args:
        n_weeks: Number of weeks to include

    Returns:
        OrderedDict with empty week data
    """
    weeks = get_last_n_weeks(n_weeks)
    current_week_label = weeks[-1][0] if weeks else None

    result = OrderedDict()

    for week_label, monday, sunday in reversed(weeks):
        display_label = _format_week_label(
            week_label=week_label,
            monday=monday,
            sunday=sunday,
            is_current=(week_label == current_week_label),
        )

        result[week_label] = {
            "display_label": display_label,
            "issues": [],
            "is_current": week_label == current_week_label,
            "total_issues": 0,
            "total_epics_closed": 0,
            "total_epics_linked": 0,
            "total_points": 0.0,
            "epic_groups": [],
        }

    return result


def _get_closed_epic_keys(issues: List[Dict], parent_keys: set[str]) -> set[str]:
    """Get parent keys that are also completed issues.

    Args:
        issues: Completed issues in the week
        parent_keys: Parent keys extracted from child issues

    Returns:
        Set of epic keys that are explicitly completed in this week
    """
    closed_epics = set()
    for issue in issues:
        issue_key = issue.get("issue_key", issue.get("key"))
        if issue_key and issue_key in parent_keys:
            closed_epics.add(issue_key)
    return closed_epics


def _group_issues_by_epic(
    issues: List[Dict], parent_field: str, all_issues: List[Dict]
) -> List[Dict]:
    """Group issues by parent epic for display.

    Args:
        issues: Issues to group (parents already filtered out)
        parent_field: Field name for parent/epic

    Returns:
        List of groups with epic_key, epic_summary, and issues
    """
    grouped = OrderedDict()

    for issue in issues:
        epic_key, epic_summary = _get_parent_info(issue, parent_field, all_issues)
        if not epic_key:
            epic_key = "No Parent"
            epic_summary = "Other"

        if epic_key not in grouped:
            grouped[epic_key] = {
                "epic_key": epic_key,
                "epic_summary": epic_summary,
                "issues": [],
            }

        grouped[epic_key]["issues"].append(issue)

    return list(grouped.values())


def _get_parent_info(
    issue: Dict, parent_field: str, all_issues: List[Dict]
) -> tuple[str | None, str | None]:
    """Extract parent epic key and summary from an issue.

    Args:
        issue: Issue dict
        parent_field: Parent field name

    Returns:
        Tuple of (parent_key, parent_summary)
    """
    parent = issue.get(parent_field)
    if not parent and parent_field.startswith("customfield_"):
        custom_fields = issue.get("custom_fields", {})
        parent = custom_fields.get(parent_field)

    if not parent:
        return None, None

    if isinstance(parent, dict):
        parent_key = parent.get("key")
        parent_summary = parent.get("summary") or parent.get("fields", {}).get(
            "summary"
        )
        return parent_key, parent_summary

    if isinstance(parent, str):
        parent_key = parent
        epic_issue = next(
            (
                item
                for item in all_issues
                if item.get("issue_key") == parent_key or item.get("key") == parent_key
            ),
            None,
        )
        if epic_issue:
            epic_summary = epic_issue.get("summary", parent_key)
            return parent_key, epic_summary
        return parent_key, parent_key

    return None, None
