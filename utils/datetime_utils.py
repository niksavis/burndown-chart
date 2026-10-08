from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_iso_datetime(value: str | None) -> datetime | None:

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
