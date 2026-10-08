import logging
from datetime import datetime

logger = logging.getLogger(__name__)

WEEKDAY_WEIGHTS = {
    0: 0.0,
    1: 0.2,
    2: 0.4,
    3: 0.6,
    4: 0.8,
    5: 1.0,
    6: 1.0,
}

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def get_weekday_weight(current_time: datetime | None = None) -> float:

    if current_time is None:
        current_time = datetime.now()

    weekday = current_time.weekday()
    weight = WEEKDAY_WEIGHTS.get(weekday, 1.0)

    logger.debug(
        f"[BLENDING] Weekday={weekday} ({DAY_NAMES[weekday]}), actual_weight={weight}"
    )

    return weight


def calculate_current_week_blend(
    actual: float, forecast: float, current_time: datetime | None = None
) -> float:

    actual_weight = get_weekday_weight(current_time)
    forecast_weight = 1.0 - actual_weight

    blended = (actual * actual_weight) + (forecast * forecast_weight)

    logger.debug(
        f"[BLENDING] actual={actual:.2f}, forecast={forecast:.2f}, "
        f"weights=({actual_weight:.1%} actual, {forecast_weight:.1%} forecast), "
        f"blended={blended:.2f}"
    )

    return blended


def get_blend_metadata(
    actual: float, forecast: float, current_time: datetime | None = None
) -> dict:

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
        "is_blended": actual_weight < 1.0,
    }

    logger.debug(
        f"[BLENDING] Metadata: f={blended:.2f}, x={forecast:.2f}, y={actual:.2f}, "
        f"ratio={metadata['actual_percent']}%/{metadata['forecast_percent']}%, "
        f"day={metadata['day_name']}"
    )

    return metadata


def format_blend_description(metadata: dict) -> str:

    if not metadata.get("is_blended", False):
        return f"Current week actual ({metadata.get('day_name', 'Today')})"

    return (
        f"Based on {metadata['actual_percent']}% actual, "
        f"{metadata['forecast_percent']}% forecast ({metadata['day_name']})"
    )
