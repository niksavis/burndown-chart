"""ISO Week Bucketing Utilities.

Provides utilities for grouping JIRA issues into ISO calendar weeks (Monday-Sunday)
and calculating metrics per week. Used by DORA and Flow metrics dashboards.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def get_iso_week_bounds(dt: datetime) -> Tuple[date, date]:
    """Get Monday and Sunday dates for the ISO week containing the given date.

    Args:
        dt: A datetime object

    Returns:
        Tuple of (monday_date, sunday_date) for the week containing dt
    """
    # Get ISO calendar info
    year, week, weekday = dt.isocalendar()

    # Monday is weekday 1, Sunday is weekday 7
    # Calculate Monday of this week
    monday = dt.date() - timedelta(days=weekday - 1)
    sunday = monday + timedelta(days=6)

    return monday, sunday


def get_week_label(dt: datetime) -> str:
    """Get ISO week label (YYYY-Wxx) for the given date.

    Args:
        dt: A datetime object

    Returns:
        String like "2025-W44" representing the ISO week
    """
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def get_last_n_weeks(
    n: int, end_date: Optional[datetime] = None
) -> List[Tuple[str, date, date]]:
    """Get list of last N ISO weeks (including current week).

    Args:
        n: Number of weeks to retrieve (including current week)
        end_date: End date (defaults to today)

    Returns:
        List of tuples: (week_label, monday_date, sunday_date)
        Sorted oldest to newest
    """
    if end_date is None:
        end_date = datetime.now()

    weeks = []
    current_date = end_date

    for i in range(n):
        monday, sunday = get_iso_week_bounds(current_date)
        week_label = get_week_label(current_date)

        weeks.append((week_label, monday, sunday))

        # Move to previous week
        current_date = current_date - timedelta(days=7)

    # Return oldest to newest
    return list(reversed(weeks))


def get_weeks_from_date_range(
    start_date: datetime, end_date: datetime
) -> List[Tuple[str, date, date]]:
    """Get list of ISO weeks covering the date range from start to end.

    Args:
        start_date: Earliest date in range
        end_date: Latest date in range

    Returns:
        List of tuples: (week_label, monday_date, sunday_date)
        Sorted oldest to newest, no duplicates
    """
    weeks = []
    seen_labels = set()

    current = start_date
    while current <= end_date:
        monday, sunday = get_iso_week_bounds(current)
        week_label = get_week_label(current)

        # Only add unique weeks
        if week_label not in seen_labels:
            seen_labels.add(week_label)
            weeks.append((week_label, monday, sunday))

        # Move to next week
        current = current + timedelta(days=7)

    return weeks


def bucket_issues_by_week(
    issues: List[Dict[str, Any]], date_field: str, n_weeks: int = 12
) -> Dict[str, List[Dict[str, Any]]]:
    """Bucket JIRA issues into ISO weeks based on a date field.

    Args:
        issues: List of JIRA issue dictionaries
        date_field: Field name to use for bucketing (e.g., "resolutiondate", "created")
        n_weeks: Number of weeks to include (default: 12)

    Returns:
        Dictionary mapping week_label -> list of issues
        Only includes weeks that have at least one issue
    """
    # Get the week definitions
    weeks = get_last_n_weeks(n_weeks)
    week_ranges = {label: (monday, sunday) for label, monday, sunday in weeks}

    # Initialize buckets
    buckets: Dict[str, List[Dict[str, Any]]] = {
        label: [] for label in week_ranges.keys()
    }

    # Bucket issues
    for issue in issues:
        # Get the date value from the issue - try flat format first (database), then JIRA nested format
        date_value = issue.get(date_field)
        if not date_value and date_field == "resolutiondate":
            date_value = issue.get("resolved")
        if not date_value:
            date_value = issue.get("fields", {}).get(date_field)

        if not date_value:
            continue

        # Parse date (handle both date and datetime strings)
        try:
            if "T" in date_value:
                # DateTime format: 2025-01-15T10:30:00.000+0000
                issue_date = datetime.fromisoformat(
                    date_value.replace("Z", "+00:00")
                ).date()
            else:
                # Date format: 2025-01-15
                issue_date = datetime.fromisoformat(date_value).date()
        except (ValueError, AttributeError) as e:
            logger.warning(
                f"Could not parse date {date_value} for issue {issue.get('key', 'unknown')}: {e}"
            )
            continue

        # Find which week this issue belongs to
        for week_label, (monday, sunday) in week_ranges.items():
            if monday <= issue_date <= sunday:
                buckets[week_label].append(issue)
                break

    return buckets


def get_week_range_description(n_weeks: int) -> str:
    """Get human-readable description of week range.

    Args:
        n_weeks: Number of weeks

    Returns:
        String like "Last 12 weeks (2025-W32 to 2025-W43)"
    """
    weeks = get_last_n_weeks(n_weeks)
    if not weeks:
        return "No weeks"

    first_week = weeks[0][0]
    last_week = weeks[-1][0]

    return f"Last {n_weeks} weeks ({first_week} to {last_week})"
