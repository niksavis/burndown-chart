"""Datetime parsing utilities."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 string to datetime.

    Args:
        value: ISO 8601 datetime string.

    Returns:
        Parsed datetime or None if value is missing or invalid.
    """
    if not value:
        return None

    candidate = value
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"

    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        logger.warning(f"[Datetime] Failed to parse datetime: {value}")
        return None
