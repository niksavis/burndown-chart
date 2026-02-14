"""Progressive Current Week Blending Algorithm.

Implements f(forecast, actual) weighted blending to eliminate Monday reliability drops
and provide smooth weekly progression for current week metrics.

The blending formula uses day-of-week weights to progressively transition from
forecast (100% on Monday) to actual (100% on Saturday-Sunday):

    blended = (actual × weight) + (forecast × (1 - weight))

Weights follow linear progression: weight = days_completed / 5

Where weight is determined by the current day of week:
- Monday (0): 0.0 (100% forecast, 0% actual) [0/5 days]
- Tuesday (1): 0.2 (80% forecast, 20% actual) [1/5 days]
- Wednesday (2): 0.4 (60% forecast, 40% actual) [2/5 days]
- Thursday (3): 0.6 (40% forecast, 60% actual) [3/5 days]
- Friday (4): 0.8 (20% forecast, 80% actual) [4/5 days]
- Saturday-Sunday (5-6): 1.0 (0% forecast, 100% actual) [work week complete]

Created: 2026-02-10
Related: Feature burndown-chart-a1vn
"""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Day-of-week weights for progressive blending
# Key: datetime.weekday() value (0=Monday, 6=Sunday)
# Value: Actual weight (forecast weight = 1.0 - actual_weight)
# Formula: weight = days_completed / 5 (linear progression)
WEEKDAY_WEIGHTS = {
    0: 0.0,  # Monday: 0% actual, 100% forecast (0/5)
    1: 0.2,  # Tuesday: 20% actual, 80% forecast (1/5)
    2: 0.4,  # Wednesday: 40% actual, 60% forecast (2/5)
    3: 0.6,  # Thursday: 60% actual, 40% forecast (3/5)
    4: 0.8,  # Friday: 80% actual, 20% forecast (4/5)
    5: 1.0,  # Saturday: 100% actual (work week complete)
    6: 1.0,  # Sunday: 100% actual (work week complete)
}

# Day names for display purposes
DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def get_weekday_weight(current_time: Optional[datetime] = None) -> float:
    """Get the actual weight for the current weekday.

    Args:
        current_time: Optional datetime for testing. Uses datetime.now() if None.

    Returns:
        Float between 0.0 and 1.0 representing the weight for actual value.
        Forecast weight = 1.0 - actual_weight.

    Example:
        >>> # On Monday
        >>> get_weekday_weight()  # Returns 0.0
        >>> # On Wednesday
        >>> get_weekday_weight()  # Returns 0.4
        >>> # On Friday
        >>> get_weekday_weight()  # Returns 0.8
    """
    if current_time is None:
        current_time = datetime.now()

    weekday = current_time.weekday()  # 0=Monday, 6=Sunday
    weight = WEEKDAY_WEIGHTS.get(weekday, 1.0)  # Default to 1.0 if invalid

    logger.debug(
        f"[BLENDING] Weekday={weekday} ({DAY_NAMES[weekday]}), actual_weight={weight}"
    )

    return weight


def calculate_current_week_blend(
    actual: float, forecast: float, current_time: Optional[datetime] = None
) -> float:
    """Calculate blended value for current week using progressive weighting.

    Combines forecast and actual values based on day of week, providing smooth
    transition from forecast-heavy (Monday) to actual-heavy (Friday).

    Args:
        actual: Current week actual value (e.g., items completed so far)
        forecast: Forecasted value for full week (from prior 4 weeks)
        current_time: Optional datetime for testing. Uses datetime.now() if None.

    Returns:
        Blended value: (actual × weight) + (forecast × (1 - weight))

    Example:
        >>> # Monday: Team has 0 items, forecast is 11.5
        >>> calculate_current_week_blend(0, 11.5)
        11.5  # 100% forecast
        >>> # Wednesday: Team has 5 items, forecast is 11.5
        >>> calculate_current_week_blend(5, 11.5)
        8.9  # 40% actual + 60% forecast
        >>> # Friday: Team has 10 items, forecast is 11.5
        >>> calculate_current_week_blend(10, 11.5)
        10.3  # 80% actual + 20% forecast
    """
    # Get day-of-week weight
    actual_weight = get_weekday_weight(current_time)
    forecast_weight = 1.0 - actual_weight

    # Calculate blended value
    blended = (actual * actual_weight) + (forecast * forecast_weight)

    logger.debug(
        f"[BLENDING] actual={actual:.2f}, forecast={forecast:.2f}, "
        f"weights=({actual_weight:.1%} actual, {forecast_weight:.1%} forecast), "
        f"blended={blended:.2f}"
    )

    return blended


def get_blend_metadata(
    actual: float, forecast: float, current_time: Optional[datetime] = None
) -> Dict:
    """Get detailed metadata about the current blending calculation.

    Provides all components needed for transparent UI display: f(x,y), x, y,
    blend ratio, and day of week.

    Args:
        actual: Current week actual value
        forecast: Forecasted value for full week
        current_time: Optional datetime for testing. Uses datetime.now() if None.

    Returns:
        Dictionary with keys:
        - 'blended' (f): Blended result
        - 'forecast' (x): Forecast value
        - 'actual' (y): Current week actual
        - 'actual_weight': Percentage weight for actual (0.0-1.0)
        - 'forecast_weight': Percentage weight for forecast (0.0-1.0)
        - 'actual_percent': Display percentage for actual (0-100)
        - 'forecast_percent': Display percentage for forecast (0-100)
        - 'weekday': Day of week index (0-6)
        - 'day_name': Day name (e.g., "Monday")
        - 'is_blended': True if blending is active (weight < 1.0)

    Example:
        >>> # Wednesday: 5 actual, 11.5 forecast
        >>> meta = get_blend_metadata(5, 11.5)
        >>> meta['blended']  # 8.9
        >>> meta['day_name']  # "Wednesday"
        >>> meta['actual_percent']  # 40
        >>> meta['forecast_percent']  # 60
    """
    if current_time is None:
        current_time = datetime.now()

    weekday = current_time.weekday()
    actual_weight = get_weekday_weight(current_time)
    forecast_weight = 1.0 - actual_weight
    blended = calculate_current_week_blend(actual, forecast, current_time)

    metadata = {
        "blended": blended,
        "forecast": forecast,
        "actual": actual,
        "actual_weight": actual_weight,
        "forecast_weight": forecast_weight,
        "actual_percent": round(actual_weight * 100),
        "forecast_percent": round(forecast_weight * 100),
        "weekday": weekday,
        "day_name": DAY_NAMES[weekday],
        "is_blended": actual_weight < 1.0,  # Blending active Mon-Fri
    }

    logger.debug(
        f"[BLENDING] Metadata: f={blended:.2f}, x={forecast:.2f}, y={actual:.2f}, "
        f"ratio={metadata['actual_percent']}%/{metadata['forecast_percent']}%, "
        f"day={metadata['day_name']}"
    )

    return metadata


def format_blend_description(metadata: Dict) -> str:
    """Format blend metadata as human-readable description.

    Args:
        metadata: Dictionary from get_blend_metadata()

    Returns:
        Formatted string like "Based on 50% actual, 50% forecast (Wednesday)"

    Example:
        >>> meta = get_blend_metadata(5, 11.5)
        >>> format_blend_description(meta)
        "Based on 40% actual, 60% forecast (Wednesday)"
    """
    if not metadata.get("is_blended", False):
        # No blending active (Sat-Sun, or weight=1.0)
        return f"Current week actual ({metadata.get('day_name', 'Today')})"

    return (
        f"Based on {metadata['actual_percent']}% actual, "
        f"{metadata['forecast_percent']}% forecast ({metadata['day_name']})"
    )
