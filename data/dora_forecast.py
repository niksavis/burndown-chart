"""Forecast helpers for DORA and Flow dashboard callbacks."""

from __future__ import annotations

import logging
from typing import Any

from data.metrics_calculator import calculate_forecast, calculate_trend_vs_forecast

logger = logging.getLogger(__name__)

DURATION_METRICS = {
    "lead_time_for_changes",
    "mean_time_to_recovery",
    "flow_time",
    "flow_efficiency",
}


def _select_weeks_for_forecast(
    weekly_values: list[float], metric_name: str
) -> list[float] | None:
    """Select weeks used for forecast based on metric type."""
    if metric_name in DURATION_METRICS:
        non_zero_weeks = [value for value in weekly_values if value > 0]
        selected_weeks = (
            non_zero_weeks[-4:] if len(non_zero_weeks) >= 4 else non_zero_weeks
        )
        if len(selected_weeks) < 2:
            return None
        selected_count = len(selected_weeks)
        total_count = len(weekly_values)
        logger.info(
            f"[Forecast] {metric_name}: Using last {selected_count} "
            f"non-zero weeks from {total_count} total weeks"
        )
        return selected_weeks

    logger.info(
        f"[Forecast] {metric_name}: Using last 4 weeks (including zeros if present)"
    )
    return weekly_values[-4:]


def calculate_dynamic_forecast(
    weekly_values: list[float],
    current_value: float | None,
    metric_type: str,
    metric_name: str = "",
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Calculate dynamic forecast and trend metadata for dashboard cards."""
    if not weekly_values or len(weekly_values) < 4:
        week_count = len(weekly_values) if weekly_values else 0
        logger.debug(
            f"Insufficient data for forecast: {metric_name} has {week_count} weeks"
        )
        return None, None

    weeks_to_use = _select_weeks_for_forecast(weekly_values, metric_name)
    if not weeks_to_use:
        logger.debug(
            f"Insufficient non-zero data for forecast: "
            f"{metric_name} has no valid week window"
        )
        return None, None

    try:
        forecast_data = calculate_forecast(weeks_to_use)
        if not forecast_data:
            return None, None

        forecast_data["weeks_with_data"] = len(weeks_to_use)
        forecast_data["used_non_zero_filter"] = metric_name in DURATION_METRICS

        trend_vs_forecast: dict[str, Any] | None = None
        if current_value is not None:
            try:
                trend_vs_forecast = calculate_trend_vs_forecast(
                    current_value=float(current_value),
                    forecast_value=forecast_data["forecast_value"],
                    metric_type=metric_type,
                )
            except (ValueError, TypeError) as exc:
                logger.warning(f"Failed to calculate trend for {metric_name}: {exc}")

        return forecast_data, trend_vs_forecast
    except Exception as exc:
        logger.warning(f"Failed to calculate forecast for {metric_name}: {exc}")
        return None, None
