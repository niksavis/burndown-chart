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

logger = logging.getLogger(__name__)


def get_completed_items_by_week(
    issues: List[Dict],
    n_weeks: int = 2,
    flow_end_statuses: Optional[List[str]] = None,
) -> Dict[str, Dict]:
    """Bucket completed issues into current week and last week.

    Filters issues by completion status and resolutiondate, then groups them
    into ISO calendar weeks. Returns current week first, then last week.

    Args:
        issues: List of JIRA issue dictionaries
        n_weeks: Number of weeks to include (default: 2 for current + last week)
        flow_end_statuses: List of statuses indicating completion
            (default: ["Done", "Closed", "Resolved"])

    Returns:
        OrderedDict mapping week_label -> dict with:
        {
            "display_label": "Current Week (Feb 3-9)",
            "issues": [issue1, issue2, ...],
            "is_current": True/False,
            "total_issues": 5,
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
        f"[COMPLETED ITEMS] Filtering completed issues for last {n_weeks} weeks"
    )

    # Filter to only completed issues with resolutiondate
    completed_issues = []
    for issue in issues:
        # Access status from fields dict (JIRA format) or direct property
        status = (
            issue.get("fields", {})
            .get("status", {})
            .get("name", issue.get("status", ""))
        )
        resolutiondate = issue.get("fields", {}).get(
            "resolutiondate", issue.get("resolutiondate")
        )

        if status in flow_end_statuses and resolutiondate:
            completed_issues.append(issue)

    logger.info(
        f"[COMPLETED ITEMS] Found {len(completed_issues)} completed issues with resolutiondate"
    )

    if not completed_issues:
        # Return empty structure for consistency
        return _create_empty_week_structure(n_weeks)

    # Bucket issues by week using resolutiondate
    buckets = bucket_issues_by_week(
        issues=completed_issues, date_field="resolutiondate", n_weeks=n_weeks
    )

    # Get week definitions for formatting
    weeks = get_last_n_weeks(n_weeks)

    # Determine which week is current (last one in the list)
    current_week_label = weeks[-1][0] if weeks else None

    # Format result with ordered dict (current week first)
    result = OrderedDict()

    # Sort weeks in reverse order (current week first)
    for week_label, monday, sunday in reversed(weeks):
        week_issues = buckets.get(week_label, [])

        # Calculate totals
        total_issues = len(week_issues)
        total_points = sum(issue.get("points", 0.0) or 0.0 for issue in week_issues)

        # Format display label
        display_label = _format_week_label(
            week_label=week_label,
            monday=monday,
            sunday=sunday,
            is_current=(week_label == current_week_label),
        )

        result[week_label] = {
            "display_label": display_label,
            "issues": week_issues,
            "is_current": week_label == current_week_label,
            "total_issues": total_issues,
            "total_points": total_points,
        }

        logger.info(
            f"[COMPLETED ITEMS] {display_label}: {total_issues} issues, {total_points:.1f} points"
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
            "total_points": 0.0,
        }

    return result
