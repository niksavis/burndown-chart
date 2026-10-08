from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def calculate_required_velocity(
    remaining_work: float,
    deadline: datetime,
    current_date: datetime | None = None,
    time_unit: str = "week",
) -> float:

    if current_date is None:
        current_date = datetime.now()

    if current_date.tzinfo is not None and deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=current_date.tzinfo)
    elif current_date.tzinfo is None and deadline.tzinfo is not None:
        current_date = current_date.replace(tzinfo=deadline.tzinfo)

    remaining_delta = deadline - current_date
    remaining_days = remaining_delta.days

    if remaining_days <= 0:
        logger.warning(
            f"Deadline has passed or is today (remaining days: {remaining_days})"
        )
        return float("inf")

    if time_unit == "week":
        remaining_periods = remaining_days / 7.0
    elif time_unit == "day":
        remaining_periods = float(remaining_days)
    else:
        raise ValueError(f"Invalid time_unit: {time_unit}. Use 'week' or 'day'.")

    if remaining_periods <= 0:
        return float("inf")

    required = remaining_work / remaining_periods

    logger.info(
        f"Required velocity: {required:.2f} units/{time_unit} "
        f"({remaining_work} work / {remaining_periods:.1f} {time_unit}s)"
    )

    return required


def calculate_velocity_gap(
    current_velocity: float, required_velocity: float
) -> dict[str, float]:

    if required_velocity == 0:
        logger.warning("Required velocity is 0 - no gap calculation possible")
        return {"gap": 0.0, "percent": 0.0, "ratio": 1.0}

    gap = required_velocity - current_velocity

    percent = (gap / required_velocity) * 100

    ratio = current_velocity / required_velocity

    logger.info(
        f"Velocity gap: {gap:+.2f} ({percent:+.1f}%), ratio: {ratio:.2%} of required"
    )

    return {"gap": gap, "percent": percent, "ratio": ratio}


def assess_pace_health(
    current_velocity: float, required_velocity: float
) -> dict[str, Any]:

    if required_velocity == 0:
        logger.warning("Required velocity is 0 - cannot assess health")
        return {
            "status": "unknown",
            "indicator": "○",
            "color": "#6c757d",
            "message": "No deadline set or no remaining work",
            "ratio": 0.0,
        }

    if required_velocity == float("inf"):
        return {
            "status": "deadline_passed",
            "indicator": "❄",
            "color": "#dc3545",
            "message": "Deadline has passed",
            "ratio": 0.0,
        }

    ratio = current_velocity / required_velocity

    if ratio >= 1.0:
        return {
            "status": "on_pace",
            "indicator": "✓",
            "color": "#28a745",
            "message": "On track or ahead of required pace",
            "ratio": ratio,
        }
    elif ratio >= 0.8:
        return {
            "status": "at_risk",
            "indicator": "○",
            "color": "#ffc107",
            "message": "Slightly below required pace",
            "ratio": ratio,
        }
    else:
        return {
            "status": "behind_pace",
            "indicator": "❄",
            "color": "#dc3545",
            "message": "Significantly behind required pace",
            "ratio": ratio,
        }


def get_pace_health_indicator(ratio: float) -> str:

    if ratio >= 1.0:
        return "✓"
    elif ratio >= 0.8:
        return "○"
    else:
        return "❄"


def calculate_completion_projection(
    remaining_work: float,
    current_velocity: float,
    current_date: datetime | None = None,
    time_unit: str = "week",
) -> dict[str, Any]:

    if current_date is None:
        current_date = datetime.now()

    if current_velocity <= 0:
        logger.warning(f"Invalid current velocity: {current_velocity}")
        return {
            "projected_date": None,
            "days_from_now": None,
            "periods_remaining": None,
        }

    periods_remaining = remaining_work / current_velocity

    if time_unit == "week":
        days_needed = periods_remaining * 7
    else:
        days_needed = periods_remaining

    projected_date = current_date + timedelta(days=days_needed)

    logger.info(
        f"Projected completion: {projected_date.strftime('%Y-%m-%d')} "
        f"({days_needed:.1f} days from now)"
    )

    return {
        "projected_date": projected_date,
        "days_from_now": int(days_needed),
        "periods_remaining": periods_remaining,
    }
