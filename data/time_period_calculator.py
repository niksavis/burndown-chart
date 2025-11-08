"""
Time Period Calculator for DORA & Flow Metrics

Provides ISO week-based time period bucketing for aggregating metrics over time.
Uses ISO 8601 week date system (Monday-Sunday weeks).

Key Features:
- ISO week calculation (Monday as first day of week)
- Year-week label generation (e.g., "2025-W43" in ISO format)
- Current week handling (include partial data up to today)
- Configurable display period via Data Points slider
- Support for historical data aggregation

Created: October 31, 2025
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def get_iso_week(dt: datetime) -> Tuple[int, int]:
    """
    Get ISO calendar year and week number for a datetime.

    ISO 8601 week date system:
    - Week starts on Monday
    - First week of the year contains the first Thursday
    - Week numbers range from 1-53

    Args:
        dt: Datetime to get ISO week for

    Returns:
        Tuple of (year, week_number)

    Example:
        >>> get_iso_week(datetime(2025, 10, 31))
        (2025, 44)
    """
    if not dt:
        logger.warning("get_iso_week called with None datetime, returning (0, 0)")
        return (0, 0)

    try:
        iso_calendar = dt.isocalendar()
        return (iso_calendar.year, iso_calendar.week)
    except AttributeError:
        logger.error(f"get_iso_week failed for {dt}, returning (0, 0)")
        return (0, 0)


def format_year_week(year: int, week: int) -> str:
    """
    Format year and week number as ISO week label.

    Args:
        year: ISO calendar year
        week: ISO week number (1-53)

    Returns:
        Formatted string "YYYY-Wxx" (ISO week format with W prefix)

    Example:
        >>> format_year_week(2025, 43)
        '2025-W43'
    """
    if not year or not week:
        logger.warning(
            f"format_year_week called with invalid values: year={year}, week={week}"
        )
        return "0000-W00"

    return f"{year}-W{week:02d}"


def get_year_week_label(dt: datetime) -> str:
    """
    Get year-week label for a datetime.

    Combines get_iso_week and format_year_week for convenience.

    Args:
        dt: Datetime to get label for

    Returns:
        Formatted year-week label "YYYY-Wxx" (ISO week format)

    Example:
        >>> get_year_week_label(datetime(2025, 10, 31))
        '2025-W44'
    """
    if not dt:
        logger.warning("get_year_week_label called with None datetime")
        return "0000-W00"

    year, week = get_iso_week(dt)
    return format_year_week(year, week)


def parse_year_week_label(label: str) -> Tuple[int, int]:
    """
    Parse year-week label back to year and week number.

    Handles both ISO format (YYYY-Wxx) and legacy format (YYYY-xx).

    Args:
        label: Year-week label in format "YYYY-Wxx" or "YYYY-xx"

    Returns:
        Tuple of (year, week_number)

    Example:
        >>> parse_year_week_label("2025-W43")
        (2025, 43)
        >>> parse_year_week_label("2025-43")  # Legacy format also supported
        (2025, 43)
    """
    if not label or "-" not in label:
        logger.warning(f"parse_year_week_label called with invalid label: {label}")
        return (0, 0)

    try:
        parts = label.split("-")
        year = int(parts[0])
        # Remove "W" prefix if present (ISO format: "2025-W43")
        week_str = parts[1].lstrip("W")
        week = int(week_str)
        return (year, week)
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse year-week label '{label}': {e}")
        return (0, 0)


def get_week_start_date(year: int, week: int) -> date:
    """
    Get the Monday start date for an ISO week.

    Args:
        year: ISO calendar year
        week: ISO week number (1-53)

    Returns:
        Date object for the Monday of that week

    Example:
        >>> get_week_start_date(2025, 44)
        date(2025, 10, 27)  # Monday, Oct 27, 2025
    """
    if not year or not week:
        logger.warning(
            f"get_week_start_date called with invalid values: year={year}, week={week}"
        )
        return date.today()

    try:
        # January 4th is always in week 1 (by ISO 8601 definition)
        jan_4 = date(year, 1, 4)
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())
        target_monday = week_1_monday + timedelta(weeks=week - 1)
        return target_monday
    except (ValueError, OverflowError) as e:
        logger.error(f"Failed to calculate week start date for {year}-W{week}: {e}")
        return date.today()


def get_week_end_date(year: int, week: int) -> date:
    """
    Get the Sunday end date for an ISO week.

    Args:
        year: ISO calendar year
        week: ISO week number (1-53)

    Returns:
        Date object for the Sunday of that week

    Example:
        >>> get_week_end_date(2025, 44)
        date(2025, 11, 2)  # Sunday, Nov 2, 2025
    """
    if not year or not week:
        logger.warning(
            f"get_week_end_date called with invalid values: year={year}, week={week}"
        )
        return date.today()

    try:
        monday = get_week_start_date(year, week)
        sunday = monday + timedelta(days=6)
        return sunday
    except (ValueError, OverflowError) as e:
        logger.error(f"Failed to calculate week end date for {year}-W{week}: {e}")
        return date.today()


def is_current_week(year: int, week: int) -> bool:
    """
    Check if the given ISO week is the current week.

    Args:
        year: ISO calendar year
        week: ISO week number

    Returns:
        True if the week is the current week, False otherwise

    Example:
        >>> is_current_week(2025, 44)
        True  # If today is Oct 31, 2025 (in week 44)
    """
    if not year or not week:
        return False

    current_year, current_week = get_iso_week(datetime.now())
    return year == current_year and week == current_week


def generate_week_range(
    start_date: date, end_date: date, include_partial_current: bool = True
) -> List[str]:
    """
    Generate list of year-week labels between start and end dates.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        include_partial_current: If True, include current week even if incomplete

    Returns:
        List of year-week labels in chronological order (ISO format with W prefix)

    Example:
        >>> generate_week_range(date(2025, 10, 1), date(2025, 10, 31))
        ['2025-W40', '2025-W41', '2025-W42', '2025-W43', '2025-W44']
    """
    if not start_date or not end_date:
        logger.warning("generate_week_range called with None dates")
        return []

    if start_date > end_date:
        logger.warning(
            f"generate_week_range: start_date {start_date} > end_date {end_date}"
        )
        return []

    try:
        week_labels = []
        current_date = start_date

        while current_date <= end_date:
            year, week = get_iso_week(
                datetime.combine(current_date, datetime.min.time())
            )
            label = format_year_week(year, week)

            # Add label if not already in list (avoid duplicates)
            if label not in week_labels:
                # Check if this is current week and we should include it
                if is_current_week(year, week):
                    if include_partial_current:
                        week_labels.append(label)
                else:
                    week_labels.append(label)

            # Move to next week
            current_date += timedelta(days=7)

        logger.info(
            f"Generated {len(week_labels)} weeks from {start_date} to {end_date}"
        )
        return week_labels

    except (ValueError, OverflowError) as e:
        logger.error(f"Failed to generate week range: {e}")
        return []


def get_recent_weeks(num_weeks: int, include_partial_current: bool = True) -> List[str]:
    """
    Get list of recent year-week labels, including current week.

    Used by Data Points slider to control display period.

    Args:
        num_weeks: Number of weeks to return (including current week)
        include_partial_current: If True, include current week even if incomplete

    Returns:
        List of year-week labels in chronological order (ISO format with W prefix)

    Example:
        >>> get_recent_weeks(4)
        ['2025-W41', '2025-W42', '2025-W43', '2025-W44']  # Last 4 weeks including current
    """
    if num_weeks <= 0:
        logger.warning(f"get_recent_weeks called with invalid num_weeks: {num_weeks}")
        return []

    try:
        today = date.today()
        # Start from num_weeks ago
        start_date = today - timedelta(weeks=num_weeks - 1)

        return generate_week_range(start_date, today, include_partial_current)

    except (ValueError, OverflowError) as e:
        logger.error(f"Failed to get recent weeks: {e}")
        return []


def filter_by_week_range(
    items: List[Dict], date_field: str, week_labels: List[str]
) -> List[Dict]:
    """
    Filter list of items to only include those within specified weeks.

    Args:
        items: List of dictionaries with date fields
        date_field: Name of the date field to filter by
        week_labels: List of year-week labels to include (ISO format with W prefix)

    Returns:
        Filtered list of items

    Example:
        >>> items = [
        ...     {"key": "A-1", "date": "2025-10-27T10:00:00"},
        ...     {"key": "A-2", "date": "2025-11-03T15:00:00"}
        ... ]
        >>> filter_by_week_range(items, "date", ["2025-W44"])
        [{"key": "A-1", "date": "2025-10-27T10:00:00"}]
    """
    if not items:
        return []

    if not week_labels:
        logger.warning("filter_by_week_range called with empty week_labels")
        return items

    try:
        filtered_items = []

        for item in items:
            date_value = item.get(date_field)
            if not date_value:
                logger.debug(
                    f"Item missing date field '{date_field}': {item.get('key', 'unknown')}"
                )
                continue

            # Parse date string to datetime
            if isinstance(date_value, str):
                try:
                    dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(
                        f"Failed to parse date '{date_value}' for item {item.get('key', 'unknown')}"
                    )
                    continue
            elif isinstance(date_value, datetime):
                dt = date_value
            elif isinstance(date_value, date):
                dt = datetime.combine(date_value, datetime.min.time())
            else:
                logger.warning(
                    f"Unsupported date type {type(date_value)} for item {item.get('key', 'unknown')}"
                )
                continue

            # Check if item's week is in target weeks
            item_week_label = get_year_week_label(dt)
            if item_week_label in week_labels:
                filtered_items.append(item)

        logger.info(
            f"Filtered {len(items)} items to {len(filtered_items)} items in {len(week_labels)} weeks"
        )
        return filtered_items

    except Exception as e:
        logger.error(f"Failed to filter by week range: {e}")
        return items


def group_by_week(items: List[Dict], date_field: str) -> Dict[str, List[Dict]]:
    """
    Group items by ISO week.

    Args:
        items: List of dictionaries with date fields
        date_field: Name of the date field to group by

    Returns:
        Dictionary mapping year-week labels (ISO format) to lists of items

    Example:
        >>> items = [
        ...     {"key": "A-1", "date": "2025-10-27T10:00:00"},
        ...     {"key": "A-2", "date": "2025-10-28T15:00:00"}
        ... ]
        >>> group_by_week(items, "date")
        {"2025-W44": [{"key": "A-1", ...}, {"key": "A-2", ...}]}
    """
    if not items:
        return {}

    try:
        grouped = {}

        for item in items:
            date_value = item.get(date_field)
            if not date_value:
                logger.debug(
                    f"Item missing date field '{date_field}': {item.get('key', 'unknown')}"
                )
                continue

            # Parse date string to datetime
            if isinstance(date_value, str):
                try:
                    dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(
                        f"Failed to parse date '{date_value}' for item {item.get('key', 'unknown')}"
                    )
                    continue
            elif isinstance(date_value, datetime):
                dt = date_value
            elif isinstance(date_value, date):
                dt = datetime.combine(date_value, datetime.min.time())
            else:
                logger.warning(
                    f"Unsupported date type {type(date_value)} for item {item.get('key', 'unknown')}"
                )
                continue

            # Get week label and add to group
            week_label = get_year_week_label(dt)
            if week_label not in grouped:
                grouped[week_label] = []
            grouped[week_label].append(item)

        logger.info(f"Grouped {len(items)} items into {len(grouped)} weeks")
        return grouped

    except Exception as e:
        logger.error(f"Failed to group by week: {e}")
        return {}


# Utility constants
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6
