"""Forecast calculation functions for metrics trending and predictions."""

import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


def calculate_forecast(
    historical_values: List[float],
    weights: Optional[List[float]] = None,
    min_weeks: int = 2,
    decimal_precision: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Calculate weighted forecast from historical metric values.

    Uses weighted average of most recent weeks, with more weight on recent data.
    Handles building baseline scenarios when fewer than 4 weeks of data available.

    Args:
        historical_values: List of metric values from recent weeks (oldest to newest)
        weights: Optional custom weights (must sum to 1.0). Defaults to [0.1, 0.2, 0.3, 0.4]
        min_weeks: Minimum weeks required for forecast (default: 2)
        decimal_precision: Number of decimal places to round forecast (default: 1)

    Returns:
        Dictionary with forecast data:
        {
            "forecast_value": float,           # Forecasted metric value
            "forecast_range": None,            # Reserved for Flow Load
            "historical_values": List[float],  # Echo of input
            "weights_applied": List[float],    # Actual weights used
            "weeks_available": int,            # Number of weeks used
            "confidence": str                  # "building" or "established"
        }

        Returns None if insufficient data (< min_weeks)

    Raises:
        ValueError: If negative values provided or weights invalid
        TypeError: If historical_values is not a list of numbers

    Examples:
        >>> calculate_forecast([10, 12, 15, 18])
        {"forecast_value": 15.2, "confidence": "established", "weeks_available": 4, ...}

        >>> calculate_forecast([10, 12])  # Building baseline
        {"forecast_value": 11.0, "confidence": "building", "weeks_available": 2, ...}

        >>> calculate_forecast([10])  # Insufficient data
        None
    """
    # Input validation
    if not isinstance(historical_values, list):
        raise TypeError("historical_values must be a list")

    if not historical_values:  # Empty list
        return None

    # Type check all values
    for v in historical_values:
        if not isinstance(v, (int, float)):
            raise TypeError(f"All historical values must be numbers, got {type(v)}")

    # Check for negative values
    if any(v < 0 for v in historical_values):
        negative_val = min(historical_values)
        raise ValueError(f"Historical values cannot be negative: {negative_val}")

    # Check minimum weeks requirement
    if len(historical_values) < min_weeks:
        return None  # Insufficient data

    # Determine weights to use
    if weights is not None:
        # Validate custom weights
        if len(weights) != len(historical_values):
            raise ValueError(
                f"Weights length ({len(weights)}) must match "
                f"historical_values length ({len(historical_values)})"
            )

        # Check weights sum to 1.0 (with tolerance for floating point)
        weight_sum = sum(weights)
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0 (got {weight_sum})")

        weights_to_use = weights
    else:
        # Auto-select weights based on data availability
        if len(historical_values) == 4:
            # Standard 4-week weighted average
            weights_to_use = [0.1, 0.2, 0.3, 0.4]
        else:
            # Equal weighting for 2-3 weeks (building baseline)
            equal_weight = 1.0 / len(historical_values)
            weights_to_use = [equal_weight] * len(historical_values)

    # Calculate weighted average
    forecast_value = sum(v * w for v, w in zip(historical_values, weights_to_use))

    # Round to specified precision
    forecast_value = round(forecast_value, decimal_precision)

    # Determine confidence level
    confidence = "established" if len(historical_values) == 4 else "building"

    return {
        "forecast_value": forecast_value,
        "forecast_range": None,  # Reserved for Flow Load
        "historical_values": historical_values.copy(),  # Defensive copy
        "weights_applied": weights_to_use.copy()
        if isinstance(weights_to_use, list)
        else list(weights_to_use),
        "weeks_available": len(historical_values),
        "confidence": confidence,
    }


def calculate_trend_vs_forecast(
    current_value: float,
    forecast_value: float,
    metric_type: str,
    threshold: float = 0.10,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate trend direction and deviation percentage vs forecast.

    Determines if current performance is on track, above, or below forecast based
    on metric type (higher_better vs lower_better) and threshold.

    Args:
        current_value: Current week's metric value
        forecast_value: Forecasted benchmark value
        metric_type: "higher_better" or "lower_better"
        threshold: Neutral zone percentage (default: 0.10 = ±10%)
        previous_period_value: Optional W-1 value for Monday morning scenario

    Returns:
        Dictionary with trend analysis:
        {
            "direction": str,         # "↗" (up), "→" (neutral), "↘" (down)
            "deviation_percent": float, # Percentage deviation from forecast
            "status_text": str,       # Human-readable status message
            "color_class": str,       # CSS class: "text-success", "text-secondary", "text-danger"
            "is_good": bool           # Directional interpretation
        }

    Examples:
        >>> calculate_trend_vs_forecast(16, 13, "higher_better")
        {"direction": "↗", "deviation_percent": 23.1, "status_text": "+23% above forecast", "color_class": "text-success", ...}

        >>> calculate_trend_vs_forecast(5, 13, "higher_better")
        {"direction": "↘", "deviation_percent": -61.5, "status_text": "-62% vs forecast", "color_class": "text-danger", ...}
    """
    # Input validation
    if not isinstance(current_value, (int, float)):
        raise TypeError(f"current_value must be numeric, got {type(current_value)}")

    if not isinstance(forecast_value, (int, float)):
        raise TypeError(f"forecast_value must be numeric, got {type(forecast_value)}")

    if forecast_value < 0:
        raise ValueError(f"forecast_value must be non-negative, got {forecast_value}")

    valid_types = ["higher_better", "lower_better"]
    if metric_type not in valid_types:
        raise ValueError(
            f"metric_type must be one of {valid_types}, got '{metric_type}'"
        )

    # Special case: Zero forecast value (perfect score for lower_better metrics like CFR, MTTR)
    # For metrics like Change Failure Rate or MTTR, a forecast of 0 means "no failures expected"
    if forecast_value == 0:
        if current_value == 0:
            # Both zero - perfect performance maintained
            direction = "→"
            status_text = "On track"
            color_class = "text-success"  # Zero failures/incidents is good!
            is_good = True
            deviation_percent = 0.0
        elif metric_type == "lower_better":
            # Forecast was 0 (perfect) but current > 0 (degradation)
            # Can't calculate percentage (division by zero), so use fixed messaging
            direction = "↗"
            status_text = "Above forecast"
            color_class = "text-danger"
            is_good = False
            deviation_percent = 100.0  # Arbitrary large value to indicate increase
        else:  # higher_better
            # Forecast was 0 but current > 0 (improvement)
            direction = "↗"
            status_text = "Above forecast"
            color_class = "text-success"
            is_good = True
            deviation_percent = 100.0  # Arbitrary large value to indicate increase

        return {
            "direction": direction,
            "deviation_percent": deviation_percent,
            "status_text": status_text,
            "color_class": color_class,
            "is_good": is_good,
        }

    # Calculate deviation percentage (forecast > 0 guaranteed here)
    deviation_percent = ((current_value - forecast_value) / forecast_value) * 100

    # Determine direction and status based on metric type
    abs_deviation = abs(deviation_percent)

    # Special case: Monday morning (week just started, no completions yet)
    # Feature 009 US2 T046
    if current_value == 0 and deviation_percent == -100.0:
        direction = "↘"
        status_text = "Week starting..."
        color_class = "text-secondary"
        is_good = True  # Week starting is not "bad"
    # Check if within threshold (neutral zone)
    elif abs_deviation <= (threshold * 100):
        direction = "→"
        status_text = "On track"
        color_class = "text-success"  # GREEN: "On track" means good performance
        is_good = True
    else:
        # Outside threshold - interpret based on metric type
        is_above = deviation_percent > 0

        if metric_type == "higher_better":
            # Higher is better (Velocity, Efficiency, Deployment Frequency)
            if is_above:
                direction = "↗"
                status_text = f"+{int(round(deviation_percent))}% above forecast"
                color_class = "text-success"
                is_good = True
            else:
                direction = "↘"
                status_text = f"{int(round(deviation_percent))}% vs forecast"
                color_class = "text-danger"
                is_good = False
        else:  # lower_better
            # Lower is better (Lead Time, CFR, MTTR)
            if is_above:
                direction = "↗"
                status_text = f"+{int(round(deviation_percent))}% vs forecast"
                color_class = "text-danger"
                is_good = False
            else:
                direction = "↘"
                status_text = f"{int(round(deviation_percent))}% vs forecast"
                color_class = "text-success"
                is_good = True

    return {
        "direction": direction,
        "deviation_percent": round(deviation_percent, 1),
        "status_text": status_text,
        "color_class": color_class,
        "is_good": is_good,
    }


def calculate_flow_load_range(
    forecast_value: float, range_percent: float = 0.20, decimal_precision: int = 0
) -> Dict[str, Any]:
    """
    Calculate acceptable WIP range for Flow Load forecast.

    Flow Load represents work in progress and has bidirectional health implications:
    - Too high = bottleneck, context switching
    - Too low = under-utilization, idle capacity

    Args:
        forecast_value: Forecasted Flow Load (items in progress)
        range_percent: Range percentage above/below forecast (default: 0.20 = ±20%)
        decimal_precision: Decimal places for range bounds (default: 0 for whole items)

    Returns:
        Dictionary with range data:
        {
            "lower": float,  # Minimum healthy WIP
            "upper": float   # Maximum healthy WIP
        }

    Raises:
        ValueError: If forecast_value is zero or negative
        ValueError: If range_percent is negative or > 1.0
        TypeError: If inputs are not numeric

    Examples:
        >>> calculate_flow_load_range(15.0)
        {"lower": 12.0, "upper": 18.0}

        >>> calculate_flow_load_range(10.0, range_percent=0.30)
        {"lower": 7.0, "upper": 13.0}
    """
    # Input validation
    if not isinstance(forecast_value, (int, float)):
        raise TypeError(f"forecast_value must be numeric, got {type(forecast_value)}")

    if not isinstance(range_percent, (int, float)):
        raise TypeError(f"range_percent must be numeric, got {type(range_percent)}")

    if forecast_value <= 0:
        raise ValueError(f"forecast_value must be positive, got {forecast_value}")

    if range_percent < 0 or range_percent > 1.0:
        raise ValueError(
            f"range_percent must be between 0 and 1.0, got {range_percent}"
        )

    # Calculate range bounds
    lower_bound = forecast_value * (1 - range_percent)
    upper_bound = forecast_value * (1 + range_percent)

    # Round to specified precision
    lower_bound = round(lower_bound, decimal_precision)
    upper_bound = round(upper_bound, decimal_precision)

    return {"lower": lower_bound, "upper": upper_bound}
