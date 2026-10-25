from datetime import datetime

import pandas as pd

from data.demo.config import AS_OF
from data.metrics.blending import get_blend_metadata
from data.metrics.forecast_calculator import (
    calculate_ewma_forecast,
    calculate_flow_load_range,
    calculate_forecast,
)
from data.persistence import PersistenceBackend, load_app_settings
from data.processing_daily_forecast import daily_forecast, daily_forecast_burnup
from data.processing_weekly_forecast import generate_weekly_forecast
from data.recommendations.scope_signals import build_scope_signals
from data.recommendations.velocity_signals import (
    build_throughput_signals,
    build_velocity_consistency_signals,
    build_velocity_trend_signals,
)
from data.velocity_projections import (
    assess_pace_health,
    calculate_required_velocity,
    calculate_velocity_gap,
)
from ui.dashboard_enhanced.stats import (
    _calculate_confidence_intervals,
    _calculate_deadline_probability,
    _calculate_velocity_statistics,
)


def forecast_calculations(
    backend: PersistenceBackend, profile_id: str, source: str
) -> dict:
    statistics = backend.get_statistics(profile_id, "main")
    frame = pd.DataFrame(statistics)
    scope = backend.get_scope(profile_id, "main") or {}
    if source == "weekly-forecast":
        return generate_weekly_forecast(statistics, data_points_count=8)
    if source == "metric-forecast":
        values = frame["completed_items"].tolist()
        return {
            "weighted": calculate_forecast(values),
            "ewma": calculate_ewma_forecast(values),
            "wip_range": calculate_flow_load_range(11),
            "blend": get_blend_metadata(4, 4),
        }
    if source == "daily-forecast":
        start = AS_OF.replace(tzinfo=None)
        down = daily_forecast(scope["remaining_items"], 4 / 7, start)
        up = daily_forecast_burnup(
            scope["completed_items"], 4 / 7, start, scope["total_items"]
        )
        return {"down": _endpoint(down), "up": _endpoint(up)}
    if source == "recommendations":
        signals = (
            build_scope_signals(frame)
            + build_velocity_trend_signals(frame)
            + build_velocity_consistency_signals(frame)
            + build_throughput_signals(frame)
        )
        return {signal["id"]: signal for signal in signals}
    if source == "advanced-points":
        return _calculate_velocity_statistics(frame, "points")
    if source == "confidence-probability":
        summary = _calculate_velocity_statistics(frame)
        return {
            "intervals": _calculate_confidence_intervals(
                28, summary["mean"], summary["std_dev"], 16
            ),
            "equal": _calculate_deadline_probability(
                28, 28, summary["std_dev"], summary["mean"]
            ),
            "before": _calculate_deadline_probability(
                27, 28, summary["std_dev"], summary["mean"]
            ),
        }
    if source == "pace":
        return _pace(frame, scope)
    raise ValueError(f"Unknown forecast diagnostic source: {source}")


def _endpoint(series: tuple[list[datetime], list[float]]) -> dict:
    dates, values = series
    return {
        "first": values[0] if values else None,
        "last": values[-1] if values else None,
        "end": dates[-1].isoformat() if dates else None,
        "count": len(values),
    }


def _pace(frame: pd.DataFrame, scope: dict) -> dict:
    deadline = load_app_settings().get("deadline")
    if deadline is None:
        return {}
    current = AS_OF.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    result = {}
    for metric in ("items", "points"):
        required = calculate_required_velocity(
            scope[f"remaining_{metric}"], datetime.fromisoformat(deadline), current
        )
        velocity = frame[f"completed_{metric}"].mean()
        result[metric] = {
            "required": required,
            "gap": calculate_velocity_gap(velocity, required),
            "health": assess_pace_health(velocity, required),
        }
    return result
