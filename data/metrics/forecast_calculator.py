import logging
from typing import Any

logger = logging.getLogger(__name__)


def calculate_forecast(
    historical_values: list[float],
    weights: list[float] | None = None,
    min_weeks: int = 2,
    decimal_precision: int = 1,
) -> dict[str, Any] | None:

    if not isinstance(historical_values, list):
        raise TypeError("historical_values must be a list")

    if not historical_values:
        return None

    for v in historical_values:
        if not isinstance(v, (int, float)):
            raise TypeError(f"All historical values must be numbers, got {type(v)}")

    if any(v < 0 for v in historical_values):
        negative_val = min(historical_values)
        raise ValueError(f"Historical values cannot be negative: {negative_val}")

    if len(historical_values) < min_weeks:
        return None

    if weights is not None:
        if len(weights) != len(historical_values):
            raise ValueError(
                f"Weights length ({len(weights)}) must match "
                f"historical_values length ({len(historical_values)})"
            )

        weight_sum = sum(weights)
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0 (got {weight_sum})")

        weights_to_use = weights
    else:
        if len(historical_values) == 4:
            weights_to_use = [0.1, 0.2, 0.3, 0.4]
        else:
            equal_weight = 1.0 / len(historical_values)
            weights_to_use = [equal_weight] * len(historical_values)

    forecast_value = sum(
        v * w for v, w in zip(historical_values, weights_to_use, strict=False)
    )

    forecast_value = round(forecast_value, decimal_precision)

    confidence = "established" if len(historical_values) == 4 else "building"

    return {
        "forecast_value": forecast_value,
        "forecast_range": None,
        "historical_values": historical_values.copy(),
        "weights_applied": weights_to_use.copy()
        if isinstance(weights_to_use, list)
        else list(weights_to_use),
        "weeks_available": len(historical_values),
        "confidence": confidence,
    }


def calculate_ewma_forecast(
    historical_values: list[float],
    alpha: float = 0.3,
    min_weeks: int = 2,
    decimal_precision: int = 1,
) -> dict[str, Any] | None:

    if not isinstance(historical_values, list):
        raise TypeError("historical_values must be a list")

    if not historical_values:
        return None

    if alpha <= 0 or alpha >= 1:
        raise ValueError("alpha must be between 0 and 1")

    for v in historical_values:
        if not isinstance(v, (int, float)):
            raise TypeError(f"All historical values must be numbers, got {type(v)}")

    if any(v < 0 for v in historical_values):
        negative_val = min(historical_values)
        raise ValueError(f"Historical values cannot be negative: {negative_val}")

    if len(historical_values) < min_weeks:
        return None

    smoothed = float(historical_values[0])
    for value in historical_values[1:]:
        smoothed = alpha * float(value) + (1 - alpha) * smoothed

    return {
        "forecast_value": round(smoothed, decimal_precision),
        "alpha": alpha,
        "weeks_available": len(historical_values),
    }


def calculate_trend_vs_forecast(
    current_value: float,
    forecast_value: float,
    metric_type: str,
    threshold: float = 0.10,
    previous_period_value: float | None = None,
) -> dict[str, Any]:

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

    if forecast_value == 0:
        if current_value == 0:
            direction = "→"
            status_text = "On track"
            color_class = "text-success"
            is_good = True
            deviation_percent = 0.0
        elif metric_type == "lower_better":
            direction = "↗"
            status_text = "Above forecast"
            color_class = "text-danger"
            is_good = False
            deviation_percent = 100.0
        else:
            direction = "↗"
            status_text = "Above forecast"
            color_class = "text-success"
            is_good = True
            deviation_percent = 100.0

        return {
            "direction": direction,
            "deviation_percent": deviation_percent,
            "status_text": status_text,
            "color_class": color_class,
            "is_good": is_good,
        }

    deviation_percent = ((current_value - forecast_value) / forecast_value) * 100

    abs_deviation = abs(deviation_percent)

    if current_value == 0 and deviation_percent == -100.0:
        direction = "↘"
        status_text = "Week starting..."
        color_class = "text-secondary"
        is_good = True
    elif abs_deviation <= (threshold * 100):
        direction = "→"
        status_text = "On track"
        color_class = "text-success"
        is_good = True
    else:
        is_above = deviation_percent > 0

        if metric_type == "higher_better":
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
        else:
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
) -> dict[str, Any]:

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

    lower_bound = forecast_value * (1 - range_percent)
    upper_bound = forecast_value * (1 + range_percent)

    lower_bound = round(lower_bound, decimal_precision)
    upper_bound = round(upper_bound, decimal_precision)

    return {"lower": lower_bound, "upper": upper_bound}
