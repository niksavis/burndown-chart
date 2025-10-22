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
    # Validate inputs
    if not isinstance(bug_issues, list) or len(bug_issues) == 0:
        raise ValueError("Cannot calculate statistics from empty bug list")

    if not isinstance(date_from, datetime) or not isinstance(date_to, datetime):
        raise ValueError("date_from and date_to must be datetime objects")

    if date_from >= date_to:
        raise ValueError(
            f"date_from ({date_from}) must be before date_to ({date_to})"
        )

    # Initialize weekly statistics for all weeks in range
    weekly_stats = {}
    current_date = date_from

    while current_date < date_to:
        week_key = get_iso_week(current_date)
        if week_key not in weekly_stats:
            weekly_stats[week_key] = {
                "week": week_key,
                "week_start_date": get_week_start_date(week_key),
                "bugs_created": 0,
                "bugs_resolved": 0,
                "bugs_points_created": 0,
                "bugs_points_resolved": 0,
                "net_bugs": 0,
                "net_points": 0,
                "cumulative_open_bugs": 0,
            }
        # Move to next day
        current_date = current_date.replace(day=current_date.day + 1)
        if current_date.day == 1:  # Handle month rollover
            break
        if current_date > date_to:
            break

    # Ensure we have the complete range by using ISO week range
    start_week = get_iso_week(date_from)
    end_week = get_iso_week(date_to)

    # Fill any missing weeks
    year_start, week_start = map(int, start_week.split("-W"))
    year_end, week_end = map(int, end_week.split("-W"))

    for year in range(year_start, year_end + 1):
        start = week_start if year == year_start else 1
        end = week_end if year == year_end else 53
        for week in range(start, end + 1):
            week_key = f"{year}-W{week:02d}"
            if week_key not in weekly_stats:
                weekly_stats[week_key] = {
                    "week": week_key,
                    "week_start_date": get_week_start_date(week_key),
                    "bugs_created": 0,
                    "bugs_resolved": 0,
                    "bugs_points_created": 0,
                    "bugs_points_resolved": 0,
                    "net_bugs": 0,
                    "net_points": 0,
                    "cumulative_open_bugs": 0,
                }

    # Aggregate bugs into weekly bins
    for bug in bug_issues:
        fields = bug.get("fields", {})

        # Parse created date
        created_str = fields.get("created", "")
        if created_str:
            try:
                created_date = datetime.strptime(created_str[:19], "%Y-%m-%dT%H:%M:%S")
                created_week = get_iso_week(created_date)

                # Only count bugs created within the analysis period
                if created_week in weekly_stats:
                    weekly_stats[created_week]["bugs_created"] += 1

                    # Add story points
                    points = fields.get(story_points_field) or 0
                    weekly_stats[created_week]["bugs_points_created"] += points

            except ValueError:
                # Skip bugs with invalid date format
                continue

        # Parse resolved date
        resolved_str = fields.get("resolutiondate")
        if resolved_str:
            try:
                resolved_date = datetime.strptime(resolved_str[:19], "%Y-%m-%dT%H:%M:%S")
                resolved_week = get_iso_week(resolved_date)

                # Count bugs resolved within the analysis period
                if resolved_week in weekly_stats:
                    weekly_stats[resolved_week]["bugs_resolved"] += 1

                    # Add story points
                    points = fields.get(story_points_field) or 0
                    weekly_stats[resolved_week]["bugs_points_resolved"] += points

            except ValueError:
                # Skip bugs with invalid date format
                continue

    # Calculate derived fields and cumulative totals
    cumulative_bugs = 0
    sorted_weeks = sorted(weekly_stats.keys())

    for week_key in sorted_weeks:
        stat = weekly_stats[week_key]

        # Calculate net changes
        stat["net_bugs"] = stat["bugs_created"] - stat["bugs_resolved"]
        stat["net_points"] = stat["bugs_points_created"] - stat["bugs_points_resolved"]

        # Calculate cumulative open bugs
        cumulative_bugs += stat["net_bugs"]
        stat["cumulative_open_bugs"] = cumulative_bugs

    # Return as ordered list
    return [weekly_stats[week] for week in sorted_weeks]


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
    iso_calendar = date.isocalendar()
    return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"


def get_week_start_date(iso_week: str) -> str:
    """Get start date (Monday) of an ISO week.

    Args:
        iso_week: ISO week string (e.g., "2025-W03")

    Returns:
        ISO date string of week start
    """
    year, week = iso_week.split("-W")
    # ISO week format: %G (ISO year), %V (ISO week number), %u (ISO weekday, 1=Monday)
    week_start = datetime.strptime(f"{year}-W{week}-1", "%G-W%V-%u")
    return week_start.date().isoformat()


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
