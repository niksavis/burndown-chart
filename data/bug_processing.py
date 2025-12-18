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
        raise ValueError(f"date_from ({date_from}) must be before date_to ({date_to})")

    # Initialize weekly statistics for all weeks in range
    weekly_stats = {}

    # Get ISO week range (this is the proper way to handle date ranges)
    start_week = get_iso_week(date_from)
    end_week = get_iso_week(date_to)

    # Fill any missing weeks
    year_start, week_start = map(int, start_week.split("-W"))
    year_end, week_end = map(int, end_week.split("-W"))

    for year in range(year_start, year_end + 1):
        start = week_start if year == year_start else 1
        # FIX: Determine actual number of weeks in the year (52 or 53)
        # ISO 8601: Week 53 only exists in years that start on Thursday or leap years starting on Wednesday
        # Most years have 52 weeks, some have 53
        max_week_in_year = get_max_iso_week_for_year(year)
        end = min(week_end if year == year_end else max_week_in_year, max_week_in_year)

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
                resolved_date = datetime.strptime(
                    resolved_str[:19], "%Y-%m-%dT%H:%M:%S"
                )
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
    all_bug_issues: List[Dict],
    timeline_filtered_bugs: List[Dict],
    weekly_stats: List[Dict],
    date_from=None,
    date_to=None,
    all_project_issues: List[Dict] = None,
) -> Dict:
    """Calculate overall bug metrics summary.

    Args:
        all_bug_issues: List of all bug issues (for current state metrics like open bugs count)
        timeline_filtered_bugs: List of bugs filtered by timeline (for historical metrics like resolution rate)
        weekly_stats: List of weekly bug statistics
        date_from: Start date for timeline filter (for display purposes)
        date_to: End date for timeline filter (for display purposes)
        all_project_issues: List of ALL project issues (bugs + non-bugs) for capacity calculation

    Returns:
        Bug metrics summary dictionary with resolution rate, trends, etc.
    """
    if not all_bug_issues and not timeline_filtered_bugs:
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

    # Count current state metrics from ALL bugs (not filtered by timeline)
    # This gives the true current state of open/closed bugs
    open_bugs = 0
    open_bug_points = 0

    for issue in all_bug_issues:
        fields = issue.get("fields", {})
        resolution_date = fields.get("resolutiondate")
        points = fields.get("customfield_10016") or 0

        if not resolution_date:
            open_bugs += 1
            open_bug_points += points

    # Count historical metrics from timeline-filtered bugs
    # This gives resolution rate and trends for the selected period
    total_bugs = len(timeline_filtered_bugs)
    closed_bugs = 0
    total_bug_points = 0
    resolution_times = []

    for issue in timeline_filtered_bugs:
        fields = issue.get("fields", {})
        resolution_date = fields.get("resolutiondate")
        points = fields.get("customfield_10016") or 0

        total_bug_points += points

        # Count closed bugs and calculate resolution time
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

    # Calculate resolution rate from timeline-filtered bugs
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

    # Calculate capacity consumed by bugs (open bug points / total project points)
    capacity_consumed_by_bugs = 0.0
    if all_project_issues:
        # Calculate total project points from ALL issues (bugs and non-bugs)
        total_project_points = 0
        for issue in all_project_issues:
            fields = issue.get("fields", {})
            points = fields.get("customfield_10016") or 0
            total_project_points += points

        # Calculate capacity: open bug points / total points
        if total_project_points > 0:
            capacity_consumed_by_bugs = open_bug_points / total_project_points

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
        "capacity_consumed_by_bugs": capacity_consumed_by_bugs,
        "date_from": date_from,  # Timeline filter start date
        "date_to": date_to,  # Timeline filter end date
    }


def forecast_bug_resolution(
    open_bugs: int, weekly_stats: List[Dict], use_last_n_weeks: int = 8
) -> Dict:
    """Forecast when open bugs will be resolved based on historical closure rates.

    Calculates optimistic, most likely, and pessimistic forecasts using
    average closure rate and standard deviation from recent history.

    Args:
        open_bugs: Number of currently open bugs
        weekly_stats: List of weekly bug statistics with bugs_resolved counts
        use_last_n_weeks: Number of recent weeks to analyze (default: 8)

    Returns:
        Dict with forecast data:
            - optimistic_weeks: Best case weeks to resolution (avg + 1 std dev)
            - most_likely_weeks: Expected weeks to resolution (avg rate)
            - pessimistic_weeks: Worst case weeks to resolution (avg - 1 std dev)
            - optimistic_date: Best case completion date (ISO format)
            - most_likely_date: Expected completion date (ISO format)
            - pessimistic_date: Worst case completion date (ISO format)
            - avg_closure_rate: Average bugs resolved per week
            - insufficient_data: True if forecast cannot be calculated

    Example:
        >>> weekly_stats = [
        ...     {"week_start": "2025-01-01", "bugs_resolved": 5},
        ...     {"week_start": "2025-01-08", "bugs_resolved": 6},
        ...     {"week_start": "2025-01-15", "bugs_resolved": 4},
        ...     {"week_start": "2025-01-22", "bugs_resolved": 5},
        ... ]
        >>> forecast = forecast_bug_resolution(10, weekly_stats)
        >>> forecast["most_likely_weeks"]  # ~2 weeks with 5 bugs/week rate
        2
    """
    # Handle zero open bugs - immediate completion
    if open_bugs == 0:
        return {
            "optimistic_weeks": 0,
            "most_likely_weeks": 0,
            "pessimistic_weeks": 0,
            "optimistic_date": calculate_future_date(0),
            "most_likely_date": calculate_future_date(0),
            "pessimistic_date": calculate_future_date(0),
            "avg_closure_rate": 0,
            "insufficient_data": False,
        }

    # Need at least 4 weeks of data for meaningful forecast
    if len(weekly_stats) < 4:
        return {
            "optimistic_weeks": 0,
            "most_likely_weeks": 0,
            "pessimistic_weeks": 0,
            "optimistic_date": "",
            "most_likely_date": "",
            "pessimistic_date": "",
            "avg_closure_rate": 0,
            "insufficient_data": True,
        }

    # Extract closure rates from recent weeks
    recent_stats = weekly_stats[-use_last_n_weeks:]
    closure_rates = [week.get("bugs_resolved", 0) for week in recent_stats]

    # Extract date range of analysis
    analysis_start = recent_stats[0].get("week_start") if recent_stats else None
    analysis_end = recent_stats[-1].get("week_start") if recent_stats else None

    # Calculate average closure rate
    avg_closure_rate = sum(closure_rates) / len(closure_rates)

    # Check for zero closure rate (no progress)
    if avg_closure_rate == 0:
        return {
            "optimistic_weeks": 0,
            "most_likely_weeks": 0,
            "pessimistic_weeks": 0,
            "optimistic_date": "",
            "most_likely_date": "",
            "pessimistic_date": "",
            "avg_closure_rate": 0,
            "insufficient_data": True,
        }

    # Calculate standard deviation for confidence intervals
    std_dev = calculate_standard_deviation(closure_rates)

    # Calculate optimistic rate (avg + 1 std dev)
    optimistic_rate = avg_closure_rate + std_dev
    optimistic_rate = max(optimistic_rate, avg_closure_rate)  # At least avg

    # Calculate pessimistic rate (avg - 1 std dev, minimum 0.1)
    pessimistic_rate = avg_closure_rate - std_dev
    pessimistic_rate = max(pessimistic_rate, 0.1)  # Avoid division by zero

    # Calculate weeks to complete
    optimistic_weeks = int(open_bugs / optimistic_rate) + (
        1 if open_bugs % optimistic_rate > 0 else 0
    )
    most_likely_weeks = int(open_bugs / avg_closure_rate) + (
        1 if open_bugs % avg_closure_rate > 0 else 0
    )
    pessimistic_weeks = int(open_bugs / pessimistic_rate) + (
        1 if open_bugs % pessimistic_rate > 0 else 0
    )

    # Ensure ordering: optimistic <= likely <= pessimistic
    optimistic_weeks = min(optimistic_weeks, most_likely_weeks)
    pessimistic_weeks = max(pessimistic_weeks, most_likely_weeks)

    return {
        "optimistic_weeks": optimistic_weeks,
        "most_likely_weeks": most_likely_weeks,
        "pessimistic_weeks": pessimistic_weeks,
        "optimistic_date": calculate_future_date(optimistic_weeks),
        "most_likely_date": calculate_future_date(most_likely_weeks),
        "pessimistic_date": calculate_future_date(pessimistic_weeks),
        "avg_closure_rate": round(avg_closure_rate, 2),
        "insufficient_data": False,
        "analysis_start": analysis_start,  # First week of analysis period
        "analysis_end": analysis_end,  # Last week of analysis period
        "weeks_analyzed": len(recent_stats),  # Number of weeks analyzed
    }


def get_iso_week(date: datetime) -> str:
    """Convert date to ISO week format (YYYY-Www).

    Args:
        date: Date to convert

    Returns:
        ISO week string (e.g., "2025-W03")
    """
    iso_calendar = date.isocalendar()
    return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"


def get_max_iso_week_for_year(year: int) -> int:
    """Get the maximum ISO week number for a given year.

    Most years have 52 weeks, but some years have 53 weeks according to ISO 8601.
    A year has 53 weeks if:
    - It starts on a Thursday (e.g., 2015, 2020, 2026)
    - It's a leap year that starts on a Wednesday (e.g., 2004, 2032)

    Args:
        year: Year to check

    Returns:
        Maximum week number (52 or 53)

    Example:
        >>> get_max_iso_week_for_year(2024)
        52
        >>> get_max_iso_week_for_year(2015)  # Started on Thursday
        53
    """
    # December 28th is always in the last week of the year (ISO 8601 rule)
    # because the last week must contain at least 4 days of the year
    last_day_of_year_week = datetime(year, 12, 28)
    return last_day_of_year_week.isocalendar()[1]


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
    if not values or len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance**0.5


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
    from datetime import timedelta

    if base_date is None:
        base_date = datetime.now()

    future_date = base_date + timedelta(weeks=weeks_ahead)
    return future_date.date().isoformat()


def generate_bug_weekly_forecast(
    weekly_stats: List[Dict], use_last_n_weeks: int = 8
) -> Dict:
    """Generate next week forecast for bugs created and resolved.

    Uses PERT 3-point estimation (optimistic, most likely, pessimistic) based on
    historical weekly statistics.

    Args:
        weekly_stats: List of weekly bug statistics from calculate_bug_statistics()
        use_last_n_weeks: Number of recent weeks to use for forecast (default: 8)

    Returns:
        Dictionary with forecast for created and resolved bugs:
        {
            "created": {
                "most_likely": float,
                "optimistic": float,
                "pessimistic": float,
                "next_week": str  # ISO week format like "2025-W44"
            },
            "resolved": {
                "most_likely": float,
                "optimistic": float,
                "pessimistic": float,
                "next_week": str
            },
            "created_points": {...},  # If story points available
            "resolved_points": {...}
        }
    """
    if not weekly_stats or len(weekly_stats) < 2:
        # Not enough data for forecast
        return {
            "created": {
                "most_likely": 0,
                "optimistic": 0,
                "pessimistic": 0,
                "next_week": "",
            },
            "resolved": {
                "most_likely": 0,
                "optimistic": 0,
                "pessimistic": 0,
                "next_week": "",
            },
            "insufficient_data": True,
        }

    # Use last N weeks for forecast
    recent_stats = (
        weekly_stats[-use_last_n_weeks:]
        if len(weekly_stats) > use_last_n_weeks
        else weekly_stats
    )

    # Extract bugs created and resolved per week
    bugs_created = [s["bugs_created"] for s in recent_stats]
    bugs_resolved = [s["bugs_resolved"] for s in recent_stats]

    # Calculate PERT estimates for bugs created
    avg_created = sum(bugs_created) / len(bugs_created)
    max_created = max(bugs_created) if bugs_created else 0
    min_created = min(bugs_created) if bugs_created else 0
    optimistic_created = max_created  # Best week performance
    pessimistic_created = min_created  # Worst week performance
    most_likely_created = avg_created  # Average performance

    # Calculate PERT estimates for bugs resolved
    avg_resolved = sum(bugs_resolved) / len(bugs_resolved)
    max_resolved = max(bugs_resolved) if bugs_resolved else 0
    min_resolved = min(bugs_resolved) if bugs_resolved else 0
    optimistic_resolved = max_resolved
    pessimistic_resolved = min_resolved
    most_likely_resolved = avg_resolved

    # Calculate next week date
    from datetime import timedelta

    last_week = recent_stats[-1]["week"]
    # Parse ISO week format (e.g., "2025-W43")
    year, week_num = last_week.split("-W")
    # Calculate next week
    from datetime import datetime as dt

    last_week_date = dt.strptime(f"{year}-W{week_num}-1", "%Y-W%W-%w")
    next_week_date = last_week_date + timedelta(weeks=1)
    next_week_str = next_week_date.strftime("%Y-W%W")

    result = {
        "created": {
            "most_likely": round(most_likely_created, 1),
            "optimistic": round(optimistic_created, 1),
            "pessimistic": round(pessimistic_created, 1),
            "next_week": next_week_str,
        },
        "resolved": {
            "most_likely": round(most_likely_resolved, 1),
            "optimistic": round(optimistic_resolved, 1),
            "pessimistic": round(pessimistic_resolved, 1),
            "next_week": next_week_str,
        },
        "insufficient_data": False,
    }

    # Add story points forecasts if available
    has_points = any(
        s.get("bugs_points_created", 0) > 0 or s.get("bugs_points_resolved", 0) > 0
        for s in recent_stats
    )
    if has_points:
        points_created = [s.get("bugs_points_created", 0) for s in recent_stats]
        points_resolved = [s.get("bugs_points_resolved", 0) for s in recent_stats]

        avg_points_created = sum(points_created) / len(points_created)
        max_points_created = max(points_created) if points_created else 0
        min_points_created = min(points_created) if points_created else 0

        avg_points_resolved = sum(points_resolved) / len(points_resolved)
        max_points_resolved = max(points_resolved) if points_resolved else 0
        min_points_resolved = min(points_resolved) if points_resolved else 0

        result["created_points"] = {
            "most_likely": round(avg_points_created, 1),
            "optimistic": round(max_points_created, 1),
            "pessimistic": round(min_points_created, 1),
            "next_week": next_week_str,
        }
        result["resolved_points"] = {
            "most_likely": round(avg_points_resolved, 1),
            "optimistic": round(max_points_resolved, 1),
            "pessimistic": round(min_points_resolved, 1),
            "next_week": next_week_str,
        }

    return result
