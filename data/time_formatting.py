"""Time formatting utilities for displaying relative timestamps.

This module provides functions for converting ISO timestamps into human-readable
relative time strings (e.g., "2h ago", "3d ago", "Jan 28").

Used for displaying data freshness in query dropdowns and other UI elements.
"""

import logging
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)


def get_relative_time_string(timestamp_iso: str | None) -> str | None:
    """Convert ISO timestamp to compact relative format.

    Generates intuitive relative time strings that gracefully age:
    - Recent: "Just now", "5m ago", "2h ago"
    - This week: "3d ago"
    - This month: "2w ago"
    - Older: "Jan 28", "Dec '25"

    Args:
        timestamp_iso: ISO 8601 timestamp (e.g., "2025-01-28T14:30:00Z")
                      Returns None if timestamp is None or invalid

    Returns:
        Compact relative string (e.g., "2h ago", "Jan 28")
        Returns None if timestamp is None or cannot be parsed

    Examples:
        >>> get_relative_time_string("2026-01-29T12:00:00Z")  # 30 seconds ago
        "Just now"

        >>> get_relative_time_string("2026-01-29T11:55:00Z")  # 5 minutes ago
        "5m ago"

        >>> get_relative_time_string("2026-01-29T10:00:00Z")  # 2 hours ago
        "2h ago"

        >>> get_relative_time_string("2026-01-26T12:00:00Z")  # 3 days ago
        "3d ago"

        >>> get_relative_time_string("2026-01-15T12:00:00Z")  # 2 weeks ago
        "2w ago"

        >>> get_relative_time_string("2026-01-05T12:00:00Z")  # same year, >28 days
        "Jan 5"

        >>> get_relative_time_string("2025-12-20T12:00:00Z")  # previous year
        "Dec '25"
    """
    if not timestamp_iso:
        return None

    try:
        # Parse ISO timestamp - handle both with and without timezone
        # Common formats: "2026-01-29T14:30:00Z", "2026-01-29T14:30:00.123456Z"
        # Also handles: "2026-01-29T14:30:00+00:00"
        timestamp_str = timestamp_iso.replace("Z", "+00:00")
        then = datetime.fromisoformat(timestamp_str)

        # Ensure timezone-aware for comparison
        if then.tzinfo is None:
            then = then.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        delta = now - then

        # Future timestamps (clock skew, testing) - show "Just now"
        if delta.total_seconds() < 0:
            logger.debug(f"Future timestamp detected: {timestamp_iso}")
            return "Just now"

        # Less than 1 minute
        if delta < timedelta(minutes=1):
            return "Just now"

        # 1-59 minutes: "5m ago"
        if delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes}m ago"

        # 1-23 hours: "2h ago"
        if delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"

        # 1-6 days: "3d ago"
        if delta < timedelta(days=7):
            return f"{delta.days}d ago"

        # 7-28 days: "2w ago"
        if delta < timedelta(days=28):
            weeks = int(delta.days / 7)
            return f"{weeks}w ago"

        # Same year, >28 days: "Jan 28"
        if then.year == now.year:
            return then.strftime("%b %d")

        # Previous years: "Dec '25"
        return then.strftime("%b '%y")

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_iso}': {e}")
        return None


def format_datetime_for_display(timestamp_iso: str | None) -> str:
    """Format ISO timestamp for human-readable display.

    Converts ISO 8601 timestamp to localized display format.

    Args:
        timestamp_iso: ISO 8601 timestamp

    Returns:
        Formatted string (e.g., "Jan 29, 2026 2:30 PM")
        Returns "Never" if timestamp is None
        Returns "Invalid date" if parsing fails

    Example:
        >>> format_datetime_for_display("2026-01-29T14:30:00Z")
        "Jan 29, 2026 2:30 PM"
    """
    if not timestamp_iso:
        return "Never"

    try:
        timestamp_str = timestamp_iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(timestamp_str)

        # Format as: Jan 29, 2026 2:30 PM
        return dt.strftime("%b %d, %Y %I:%M %p")

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to format timestamp '{timestamp_iso}': {e}")
        return "Invalid date"
