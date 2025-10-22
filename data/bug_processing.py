"""Bug data processing and analysis.

Provides functions for filtering bug issues, calculating bug statistics,
aggregating metrics, and forecasting bug resolution timelines.
"""

from datetime import datetime
from typing import Dict, List, Optional


def filter_bug_issues(
    issues: List[Dict],
    bug_type_mappings: Dict[str, str],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[Dict]:
    """Filter issues to include only bugs based on type mappings.

    Args:
        issues: List of JIRA issues
        bug_type_mappings: Dict mapping JIRA type names to "bug" category
        date_from: Optional start date filter (filters by created_date)
        date_to: Optional end date filter (filters by created_date)

    Returns:
        List of issues classified as bugs within date range

    See: contracts/bug_filtering.contract.md for detailed specification
    """
    filtered_bugs = []

    for issue in issues:
        # Extract issue type name
        issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "")

        # Check if issue type is mapped to "bug"
        if issue_type not in bug_type_mappings:
            continue

        # Apply date range filter if specified
        if date_from or date_to:
            created_str = issue.get("fields", {}).get("created", "")
            if created_str:
                try:
                    # Parse JIRA datetime format
                    created_date = datetime.strptime(
                        created_str[:19], "%Y-%m-%dT%H:%M:%S"
                    )

                    # Check date range
                    if date_from and created_date < date_from:
                        continue
                    if date_to and created_date > date_to:
                        continue
                except ValueError:
                    # Skip issues with invalid date format
                    continue

        filtered_bugs.append(issue)

    return filtered_bugs


def calculate_bug_statistics(
    bug_issues: List[Dict],
    date_from: datetime,
    date_to: datetime,
    story_points_field: str = "customfield_10016",
) -> List[Dict]:
    """Calculate weekly bug statistics from bug issues.

    Args:
        bug_issues: List of filtered bug issues
        date_from: Start date of analysis period
        date_to: End date of analysis period
        story_points_field: JIRA custom field for story points

    Returns:
        List of weekly bug statistics dictionaries

    See: contracts/bug_statistics.contract.md for detailed specification
    """
    # TODO: Implement weekly statistics calculation per contract
    return []


def calculate_bug_metrics_summary(
    bug_issues: List[Dict], weekly_stats: List[Dict]
) -> Dict:
    """Calculate overall bug metrics summary.

    Args:
        bug_issues: List of all bug issues
        weekly_stats: List of weekly bug statistics

    Returns:
        Bug metrics summary dictionary with resolution rate, trends, etc.
    """
    if not bug_issues:
        return {
            "total_bugs": 0,
            "open_bugs": 0,
            "closed_bugs": 0,
            "resolution_rate": 0.0,
            "avg_resolution_time_days": 0.0,
            "bugs_created_last_4_weeks": 0,
            "bugs_resolved_last_4_weeks": 0,
            "trend_direction": "stable",
            "total_bug_points": 0,
            "open_bug_points": 0,
            "capacity_consumed_by_bugs": 0.0,
        }

    # Count total, open, and closed bugs
    total_bugs = len(bug_issues)
    open_bugs = 0
    closed_bugs = 0
    total_bug_points = 0
    open_bug_points = 0
    resolution_times = []

    for issue in bug_issues:
        fields = issue.get("fields", {})
        resolution_date = fields.get("resolutiondate")
        points = fields.get("customfield_10016") or 0

        # Count open vs closed
        if resolution_date:
            closed_bugs += 1

            # Calculate resolution time
            created_str = fields.get("created", "")
            if created_str:
                try:
                    created = datetime.strptime(created_str[:19], "%Y-%m-%dT%H:%M:%S")
                    resolved = datetime.strptime(
                        resolution_date[:19], "%Y-%m-%dT%H:%M:%S"
                    )
                    resolution_time = (resolved - created).days
                    resolution_times.append(resolution_time)
                except ValueError:
                    pass
        else:
            open_bugs += 1
            open_bug_points += points

        total_bug_points += points

    # Calculate resolution rate
    resolution_rate = closed_bugs / total_bugs if total_bugs > 0 else 0.0

    # Calculate average resolution time
    avg_resolution_time_days = (
        sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
    )

    # Calculate recent trends (last 4 weeks) from weekly_stats
    bugs_created_last_4_weeks = 0
    bugs_resolved_last_4_weeks = 0

    if weekly_stats and len(weekly_stats) >= 4:
        recent_stats = weekly_stats[-4:]
        bugs_created_last_4_weeks = sum(
            week.get("bugs_created", 0) for week in recent_stats
        )
        bugs_resolved_last_4_weeks = sum(
            week.get("bugs_resolved", 0) for week in recent_stats
        )

    # Determine trend direction
    trend_direction = "stable"
    if bugs_created_last_4_weeks > 0 or bugs_resolved_last_4_weeks > 0:
        if bugs_resolved_last_4_weeks > bugs_created_last_4_weeks * 1.1:
            trend_direction = "improving"
        elif bugs_created_last_4_weeks > bugs_resolved_last_4_weeks * 1.1:
            trend_direction = "degrading"

    return {
        "total_bugs": total_bugs,
        "open_bugs": open_bugs,
        "closed_bugs": closed_bugs,
        "resolution_rate": resolution_rate,
        "avg_resolution_time_days": avg_resolution_time_days,
        "bugs_created_last_4_weeks": bugs_created_last_4_weeks,
        "bugs_resolved_last_4_weeks": bugs_resolved_last_4_weeks,
        "trend_direction": trend_direction,
        "total_bug_points": total_bug_points,
        "open_bug_points": open_bug_points,
        "capacity_consumed_by_bugs": 0.0,  # Will be calculated when total capacity is known
    }


def forecast_bug_resolution(
    open_bugs: int, weekly_stats: List[Dict], confidence_level: float = 0.95
) -> Dict:
    """Forecast bug resolution timeline with confidence intervals.

    Args:
        open_bugs: Current count of open bugs
        weekly_stats: Historical weekly bug statistics
        confidence_level: Statistical confidence level (0.0-1.0)

    Returns:
        Bug forecast dictionary with optimistic/pessimistic estimates

    See: contracts/bug_forecasting.contract.md for detailed specification
    """
    # TODO: Implement forecasting per contract
    return {}


def get_iso_week(date: datetime) -> str:
    """Convert date to ISO week format (YYYY-Www).

    Args:
        date: Date to convert

    Returns:
        ISO week string (e.g., "2025-W03")
    """
    # TODO: Implement ISO week conversion
    return ""


def get_week_start_date(iso_week: str) -> str:
    """Get start date (Monday) of an ISO week.

    Args:
        iso_week: ISO week string (e.g., "2025-W03")

    Returns:
        ISO date string of week start
    """
    # TODO: Implement week start date calculation
    return ""


def calculate_standard_deviation(values: List[float]) -> float:
    """Calculate standard deviation of a list of values.

    Args:
        values: List of numeric values

    Returns:
        Standard deviation
    """
    # TODO: Implement standard deviation calculation
    return 0.0


def calculate_future_date(
    weeks_ahead: int, base_date: Optional[datetime] = None
) -> str:
    """Calculate a future date given weeks ahead.

    Args:
        weeks_ahead: Number of weeks in the future
        base_date: Base date (defaults to now)

    Returns:
        ISO date string
    """
    # TODO: Implement future date calculation
    return ""
