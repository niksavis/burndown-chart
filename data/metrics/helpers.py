"""Utility helper functions for metrics calculation."""

from datetime import datetime


def get_current_iso_week() -> str:
    """
    Get current ISO week label in format YYYY-WW (without "W" prefix).

    Returns:
        str: ISO week label (e.g., "2025-44")
    """
    now = datetime.now()
    iso_calendar = now.isocalendar()
    # Format without "W" prefix to match dashboard format
    return f"{iso_calendar.year}-{iso_calendar.week:02d}"
