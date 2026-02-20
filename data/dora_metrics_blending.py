"""DORA metrics blending helpers.

Contains behavior-preserving blending utilities used by DORA callbacks.
"""

from __future__ import annotations

import logging
from typing import Any

from data.metrics.blending import calculate_current_week_blend, get_blend_metadata
from data.metrics_calculator import calculate_forecast

logger = logging.getLogger(__name__)


def _blend_metric_series(
    weekly_values: list[float],
    filter_zero_prior_weeks: bool,
    metric_log_name: str,
) -> tuple[list[float] | None, dict[str, Any] | None]:
    """Return adjusted weekly values and blend metadata for a metric series."""
    if not weekly_values or len(weekly_values) < 2:
        return None, None

    current_week_actual = weekly_values[-1]
    prior_weeks = weekly_values[:-1]
    if filter_zero_prior_weeks:
        prior_weeks = [value for value in prior_weeks if value > 0]

    forecast_weeks = prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks
    if len(forecast_weeks) < 2:
        return None, None

    try:
        forecast_data = calculate_forecast(forecast_weeks)
        forecast_value = forecast_data.get("forecast_value", 0) if forecast_data else 0
        if forecast_value <= 0:
            return None, None

        blended_value = calculate_current_week_blend(
            current_week_actual, forecast_value
        )
        blend_metadata = get_blend_metadata(current_week_actual, forecast_value)

        adjusted_values = list(weekly_values)
        adjusted_values[-1] = blended_value

        logger.info(
            f"[Blending] {metric_log_name} - Actual: {current_week_actual:.1f}, "
            f"Forecast: {forecast_value:.1f}, Blended: {blended_value:.1f}"
        )
        return adjusted_values, blend_metadata
    except Exception as exc:
        logger.warning(f"Failed to blend {metric_log_name.lower()}: {exc}")
        return None, None


def calculate_dora_blended_series(cached_metrics: dict[str, Any]) -> dict[str, Any]:
    """Calculate blended weekly series for selected DORA metrics."""
    deployment_weekly_values = cached_metrics.get("deployment_frequency", {}).get(
        "weekly_values", []
    )
    deployment_adjusted, deployment_metadata = _blend_metric_series(
        weekly_values=deployment_weekly_values,
        filter_zero_prior_weeks=False,
        metric_log_name="Deployment Frequency",
    )

    lead_time_weekly_values = cached_metrics.get("lead_time_for_changes", {}).get(
        "weekly_values", []
    )
    lead_time_adjusted, lead_time_metadata = _blend_metric_series(
        weekly_values=lead_time_weekly_values,
        filter_zero_prior_weeks=True,
        metric_log_name="Lead Time",
    )

    mttr_weekly_values = cached_metrics.get("mean_time_to_recovery", {}).get(
        "weekly_values", []
    )
    mttr_adjusted, mttr_metadata = _blend_metric_series(
        weekly_values=mttr_weekly_values,
        filter_zero_prior_weeks=True,
        metric_log_name="MTTR",
    )

    return {
        "deployment_weekly_values": deployment_weekly_values,
        "deployment_weekly_values_adjusted": deployment_adjusted,
        "deployment_blend_metadata": deployment_metadata,
        "lead_time_weekly_values": lead_time_weekly_values,
        "lead_time_weekly_values_adjusted": lead_time_adjusted,
        "lead_time_blend_metadata": lead_time_metadata,
        "mttr_weekly_values": mttr_weekly_values,
        "mttr_weekly_values_adjusted": mttr_adjusted,
        "mttr_blend_metadata": mttr_metadata,
    }
