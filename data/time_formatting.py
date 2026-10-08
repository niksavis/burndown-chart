import logging
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)


def get_relative_time_string(timestamp_iso: str | None) -> str | None:

    if not timestamp_iso:
        return None

    try:
        timestamp_str = timestamp_iso.replace("Z", "+00:00")
        then = datetime.fromisoformat(timestamp_str)

        if then.tzinfo is None:
            then = then.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        delta = now - then

        if delta.total_seconds() < 0:
            logger.debug(f"Future timestamp detected: {timestamp_iso}")
            return "Just now"

        if delta < timedelta(minutes=1):
            return "Just now"

        if delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes}m ago"

        if delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"

        if delta < timedelta(days=7):
            return f"{delta.days}d ago"

        if delta < timedelta(days=28):
            weeks = int(delta.days / 7)
            return f"{weeks}w ago"

        if then.year == now.year:
            return then.strftime("%b %d")

        return then.strftime("%b '%y")

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_iso}': {e}")
        return None


def format_datetime_for_display(timestamp_iso: str | None) -> str:

    if not timestamp_iso:
        return "Never"

    try:
        timestamp_str = timestamp_iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(timestamp_str)

        return dt.strftime("%b %d, %Y %I:%M %p")

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to format timestamp '{timestamp_iso}': {e}")
        return "Invalid date"
