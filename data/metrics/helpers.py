"""Utility helper functions for metrics calculation."""

from datetime import datetime


def get_current_iso_week() -> str:
    """
    Get current ISO week label in format YYYY-Wxx.

    Returns:
        str: ISO week label (e.g., "2025-W44")
    """
    now = datetime.now()
    iso_calendar = now.isocalendar()
    return f"{iso_calendar.year}-W{iso_calendar.week:02d}"
