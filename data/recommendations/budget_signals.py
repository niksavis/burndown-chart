"""Shared budget recommendation signals."""

from __future__ import annotations

import math
from typing import Any


def build_budget_health_signals(
    budget_data: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build budget health signals from budget data.

    Args:
        budget_data: Budget metrics dictionary.

    Returns:
        List of signal dictionaries with severity and metrics.
    """
    if not budget_data:
        return []

    utilization_pct = float(budget_data.get("utilization_percentage", 0))
    runway_weeks = float(budget_data.get("runway_weeks", 0))
    burn_rate = float(budget_data.get("burn_rate", 0))
    currency = budget_data.get("currency_symbol", "€")

    signals: list[dict[str, Any]] = []

    if math.isinf(runway_weeks):
        signals.append(
            {
                "id": "budget_no_consumption",
                "severity": "info",
                "metrics": {
                    "utilization_pct": utilization_pct,
                    "runway_weeks": runway_weeks,
                    "burn_rate": burn_rate,
                    "currency": currency,
                },
            }
        )
        return signals

    if utilization_pct > 90:
        signals.append(
            {
                "id": "budget_critical",
                "severity": "danger",
                "metrics": {
                    "utilization_pct": utilization_pct,
                    "runway_weeks": runway_weeks,
                    "burn_rate": burn_rate,
                    "currency": currency,
                },
            }
        )
    elif utilization_pct > 75:
        signals.append(
            {
                "id": "budget_alert",
                "severity": "warning",
                "metrics": {
                    "utilization_pct": utilization_pct,
                    "runway_weeks": runway_weeks,
                    "burn_rate": burn_rate,
                    "currency": currency,
                },
            }
        )
    elif runway_weeks < 8 and runway_weeks > 0:
        signals.append(
            {
                "id": "budget_limited_runway",
                "severity": "warning",
                "metrics": {
                    "utilization_pct": utilization_pct,
                    "runway_weeks": runway_weeks,
                    "burn_rate": burn_rate,
                    "currency": currency,
                },
            }
        )
    elif utilization_pct < 50 and runway_weeks > 12:
        signals.append(
            {
                "id": "budget_healthy",
                "severity": "success",
                "metrics": {
                    "utilization_pct": utilization_pct,
                    "runway_weeks": runway_weeks,
                    "burn_rate": burn_rate,
                    "currency": currency,
                },
            }
        )

    return signals


def build_budget_forecast_signals(
    runway_weeks: float,
    pert_forecast_weeks: float,
    pert_pessimistic_weeks: float,
) -> list[dict[str, Any]]:
    """Build budget vs forecast signals from weeks-based inputs.

    Args:
        runway_weeks: Budget runway in weeks.
        pert_forecast_weeks: Forecast duration in weeks.
        pert_pessimistic_weeks: Pessimistic duration in weeks.

    Returns:
        List of signal dictionaries with severity and metrics.
    """
    signals: list[dict[str, Any]] = []

    if math.isinf(runway_weeks) or pert_forecast_weeks <= 0:
        return signals

    if runway_weeks > 0 and runway_weeks < pert_forecast_weeks - 2:
        shortfall_weeks = pert_forecast_weeks - runway_weeks
        shortfall_pct = (shortfall_weeks / pert_forecast_weeks) * 100
        signals.append(
            {
                "id": "budget_exhaustion_before_completion",
                "severity": "danger",
                "metrics": {
                    "shortfall_weeks": shortfall_weeks,
                    "shortfall_pct": shortfall_pct,
                    "runway_weeks": runway_weeks,
                    "pert_forecast_weeks": pert_forecast_weeks,
                },
            }
        )
    elif pert_pessimistic_weeks > 0 and runway_weeks > pert_pessimistic_weeks + 4:
        surplus_weeks = runway_weeks - pert_pessimistic_weeks
        signals.append(
            {
                "id": "budget_surplus_likely",
                "severity": "success",
                "metrics": {
                    "surplus_weeks": surplus_weeks,
                    "runway_weeks": runway_weeks,
                    "pert_pessimistic_weeks": pert_pessimistic_weeks,
                },
            }
        )

    return signals


def build_budget_forecast_signals_from_pert(
    budget_data: dict[str, Any] | None,
    pert_data: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build budget vs forecast signals using PERT data."""
    if not budget_data or not pert_data:
        return []

    runway_weeks = float(budget_data.get("runway_weeks", 0))
    pert_forecast_weeks = (
        float(pert_data.get("pert_time_items", 0)) / 7.0
        if pert_data.get("pert_time_items")
        else 0
    )
    pert_pessimistic_weeks = (
        float(pert_data.get("pert_pessimistic_days", 0)) / 7.0
        if pert_data.get("pert_pessimistic_days")
        else 0
    )

    return build_budget_forecast_signals(
        runway_weeks, pert_forecast_weeks, pert_pessimistic_weeks
    )


def build_budget_forecast_signals_from_dashboard(
    budget_data: dict[str, Any] | None,
    dashboard_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build budget vs forecast signals using dashboard metrics."""
    if not budget_data:
        return []

    runway_weeks = float(budget_data.get("runway_weeks", 0))
    pert_forecast_weeks = float(dashboard_metrics.get("pert_time_items_weeks", 0))
    pert_pessimistic_weeks = pert_forecast_weeks * 1.3 if pert_forecast_weeks else 0

    return build_budget_forecast_signals(
        runway_weeks, pert_forecast_weeks, pert_pessimistic_weeks
    )
