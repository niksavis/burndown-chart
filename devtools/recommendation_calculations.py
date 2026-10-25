import pandas as pd

from data.persistence import load_app_settings, load_unified_project_data
from data.recommendations.budget_signals import (
    build_budget_forecast_signals_from_dashboard,
    build_budget_forecast_signals_from_pert,
    build_budget_health_signals,
)
from data.recommendations.correlation_signals import build_correlation_signals
from data.recommendations.pace_signals import build_required_pace_signals
from data.types import MetricsResult

CORRELATION_IDS = (
    "unstable_delivery_scope_creep",
    "budget_forecast_uncertainty",
    "performance_surplus",
    "high_wip_long_lead_time",
    "bug_velocity_drain",
    "quality_scope_pressure",
    "dora_velocity_divergence",
)


def _indexed(signals: list[dict]) -> dict:
    return {
        "signals": {signal["id"]: signal for signal in signals},
        "present": {
            identifier: any(signal["id"] == identifier for signal in signals)
            for identifier in CORRELATION_IDS
        },
        "count": len(signals),
    }


def recommendation_calculations() -> dict:
    frame = pd.DataFrame(load_unified_project_data()["statistics"])
    deadline = load_app_settings().get("deadline")
    budget = {
        "utilization_percentage": 290 / 3,
        "runway_weeks": 10 / 37,
        "burn_rate": 1110,
        "currency_symbol": "EUR",
    }
    dashboard: MetricsResult = {
        "has_data": True,
        "completed_items": 32,
        "remaining_items": 16,
        "health_score": 72,
        "health_status": "good",
        "pert_time_items_weeks": 4,
    }
    return {
        "pace": _indexed(build_required_pace_signals(frame, deadline)),
        "budget": _indexed(build_budget_health_signals(budget)),
        "budget_missing": _indexed(build_budget_health_signals(None)),
        "forecast_missing": _indexed(
            build_budget_forecast_signals_from_pert(None, None)
        ),
        "forecast_pert": _indexed(
            build_budget_forecast_signals_from_pert(
                budget, {"pert_time_items": 28, "pert_pessimistic_days": 28}
            )
        ),
        "forecast_dashboard": _indexed(
            build_budget_forecast_signals_from_dashboard(budget, dashboard)
        ),
        "correlations": _correlations(frame),
    }


def _correlations(frame: pd.DataFrame) -> dict:
    cases = {
        "missing": {},
        "unstable": {"budget_data": {"runway_weeks": 10 / 37}},
        "uncertain": {
            "budget_data": {"runway_weeks": 5},
            "pert_data": {"pert_optimistic_days": 7, "pert_pessimistic_days": 42},
        },
        "surplus": {
            "budget_data": {"runway_weeks": 8},
            "pert_data": {"pert_time_items": 28},
        },
        "wip": {
            "flow_metrics": {"has_data": True, "avg_wip": 20, "median_flow_time": 8}
        },
        "wip_boundary": {
            "flow_metrics": {"has_data": True, "avg_wip": 20, "median_flow_time": 7}
        },
        "bugs": {"bug_metrics": {"has_data": True, "bug_investment_pct": 25}},
        "quality": {"bug_metrics": {"has_data": True, "resolution_rate": 49}},
        "quality_zero": {"bug_metrics": {"has_data": True, "resolution_rate": 0}},
        "quality_boundary": {"bug_metrics": {"has_data": True, "resolution_rate": 50}},
        "dora": {"dora_metrics": {"has_data": True, "overall_tier": "medium"}},
        "dora_high": {"dora_metrics": {"has_data": True, "overall_tier": "high"}},
    }
    return {
        name: _indexed(build_correlation_signals(frame, **inputs))
        for name, inputs in cases.items()
    }
