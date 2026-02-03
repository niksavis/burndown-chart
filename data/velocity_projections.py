"""Velocity Projection and Pace Health Calculations.

This module provides forward-looking metrics to answer:
- What pace do we need to meet our deadline?
- Are we on track?
- How much do we need to improve?

Automatically handles scope changes by using current remaining work,
not original project scope.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


def calculate_required_velocity(
    remaining_work: float,
    deadline: datetime,
    current_date: Optional[datetime] = None,
    time_unit: str = "week",
) -> float:
    """Calculate required velocity to meet deadline.

    Uses current remaining work (not original scope) to automatically
    handle scope changes during the project.

    Args:
        remaining_work: Items or points remaining to complete
        deadline: Target completion date
        current_date: Current date (defaults to now)
        time_unit: 'week' or 'day' for velocity calculation

    Returns:
        Required velocity (work units per time unit)
        Returns float('inf') if deadline has passed or is today

    Example:
        >>> from datetime import datetime, timedelta
        >>> deadline = datetime.now() + timedelta(days=28)
        >>> calculate_required_velocity(50, deadline, time_unit='week')
        12.5  # Need 12.5 items/week to complete 50 items in 4 weeks
    """
    if current_date is None:
        current_date = datetime.now()

    # Ensure both datetimes are naive or both are aware
    if current_date.tzinfo is not None and deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=current_date.tzinfo)
    elif current_date.tzinfo is None and deadline.tzinfo is not None:
        current_date = current_date.replace(tzinfo=deadline.tzinfo)

    # Calculate remaining time
    remaining_delta = deadline - current_date
    remaining_days = remaining_delta.days

    if remaining_days <= 0:
        logger.warning(
            f"Deadline has passed or is today (remaining days: {remaining_days})"
        )
        return float("inf")

    # Convert to requested time unit
    if time_unit == "week":
        remaining_periods = remaining_days / 7.0
    elif time_unit == "day":
        remaining_periods = float(remaining_days)
    else:
        raise ValueError(f"Invalid time_unit: {time_unit}. Use 'week' or 'day'.")

    if remaining_periods <= 0:
        return float("inf")

    # Required velocity = work / time
    required = remaining_work / remaining_periods

    logger.info(
        f"Required velocity: {required:.2f} units/{time_unit} "
        f"({remaining_work} work / {remaining_periods:.1f} {time_unit}s)"
    )

    return required


def calculate_velocity_gap(
    current_velocity: float, required_velocity: float
) -> Dict[str, float]:
    """Calculate gap between current and required velocity.

    Args:
        current_velocity: Team's current velocity (from recent data)
        required_velocity: Velocity needed to meet deadline

    Returns:
        Dictionary containing:
        - gap: Absolute difference (positive = need more velocity)
        - percent: Percentage difference relative to required
        - ratio: current/required ratio (1.0 = exactly on pace)

    Example:
        >>> calculate_velocity_gap(10.0, 12.5)
        {
            'gap': 2.5,      # Need 2.5 more items/week
            'percent': 20.0,  # 20% below required pace
            'ratio': 0.8      # Running at 80% of required pace
        }
    """
    if required_velocity == 0:
        logger.warning("Required velocity is 0 - no gap calculation possible")
        return {"gap": 0.0, "percent": 0.0, "ratio": 1.0}

    # Gap: positive means need to increase, negative means ahead of pace
    gap = required_velocity - current_velocity

    # Percentage difference
    percent = (gap / required_velocity) * 100

    # Ratio: 1.0 = on pace, <1.0 = behind, >1.0 = ahead
    ratio = current_velocity / required_velocity

    logger.info(
        f"Velocity gap: {gap:+.2f} ({percent:+.1f}%), ratio: {ratio:.2%} of required"
    )

    return {"gap": gap, "percent": percent, "ratio": ratio}


def assess_pace_health(
    current_velocity: float, required_velocity: float
) -> Dict[str, Any]:
    """Assess pace health status based on velocity comparison.

    Health thresholds:
    - Healthy: >= 100% of required velocity (on track or ahead)
    - At Risk: 80-99% of required velocity (close but need improvement)
    - Behind: < 80% of required velocity (significantly behind)

    Args:
        current_velocity: Team's current velocity
        required_velocity: Velocity needed to meet deadline

    Returns:
        Dictionary containing:
        - status: 'healthy'|'at_risk'|'behind'|'unknown'
        - indicator: Unicode symbol (✓|○|❄)
        - color: Hex color code for visual display
        - message: Human-readable status message
        - ratio: current/required ratio

    Example:
        >>> assess_pace_health(10.0, 12.5)
        {
            'status': 'at_risk',
            'indicator': '○',
            'color': '#ffc107',
            'message': 'Slightly below required pace',
            'ratio': 0.8
        }
    """
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

    # Determine health status based on ratio thresholds
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
    """Get visual indicator based on pace ratio.

    Quick helper for displaying status without full assessment.

    Args:
        ratio: current_velocity / required_velocity

    Returns:
        Unicode indicator: ✓ (>=1.0), ○ (0.8-0.99), ❄ (<0.8)

    Example:
        >>> get_pace_health_indicator(0.95)
        '○'
    """
    if ratio >= 1.0:
        return "✓"
    elif ratio >= 0.8:
        return "○"
    else:
        return "❄"


def calculate_completion_projection(
    remaining_work: float,
    current_velocity: float,
    current_date: Optional[datetime] = None,
    time_unit: str = "week",
) -> Dict[str, Any]:
    """Project completion date based on current velocity.

    Args:
        remaining_work: Items or points remaining
        current_velocity: Current team velocity
        current_date: Current date (defaults to now)
        time_unit: 'week' or 'day'

    Returns:
        Dictionary containing:
        - projected_date: Estimated completion date
        - days_from_now: Days until projected completion
        - periods_remaining: Number of time periods needed

    Example:
        >>> calculate_completion_projection(50, 10.0, time_unit='week')
        {
            'projected_date': datetime(...),  # 35 days from now
            'days_from_now': 35,
            'periods_remaining': 5.0
        }
    """
    if current_date is None:
        current_date = datetime.now()

    if current_velocity <= 0:
        logger.warning(f"Invalid current velocity: {current_velocity}")
        return {
            "projected_date": None,
            "days_from_now": None,
            "periods_remaining": None,
        }

    # Calculate periods needed
    periods_remaining = remaining_work / current_velocity

    # Convert to days
    if time_unit == "week":
        days_needed = periods_remaining * 7
    else:  # day
        days_needed = periods_remaining

    # Project completion date
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
