"""Insights Engine - Scoring Orchestration.

Combines signal-group scoring helpers, sorts by severity, limits output,
and provides a fallback insight when no signals are produced.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ui.dashboard.insights_engine_scoring_capacity import (
    _build_capacity_scope_insights,
)
from ui.dashboard.insights_engine_scoring_delivery import _build_delivery_insights
from ui.dashboard.insights_engine_scoring_forecast import (
    _build_deadline_budget_forecast_insights,
)
from ui.dashboard.insights_engine_scoring_pace import _build_pace_correlation_insights


def _build_insights_list(
    statistics_df: pd.DataFrame,
    settings: dict[str, Any],
    budget_data: dict[str, Any] | None,
    pert_data: dict[str, Any] | None,
    deadline: str | None,
    bug_metrics: dict[str, Any] | None = None,
    flow_metrics: dict[str, Any] | None = None,
    dora_metrics: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build, prioritize, and cap insights from all scoring groups."""
    _ = settings
    insights: list[dict[str, Any]] = []

    if not statistics_df.empty:
        insights.extend(_build_delivery_insights(statistics_df, budget_data))

    insights.extend(
        _build_deadline_budget_forecast_insights(pert_data, deadline, budget_data)
    )

    if not statistics_df.empty:
        insights.extend(_build_capacity_scope_insights(statistics_df, budget_data))

    insights.extend(
        _build_pace_correlation_insights(
            statistics_df,
            budget_data,
            pert_data,
            deadline,
            bug_metrics,
            flow_metrics,
            dora_metrics,
        )
    )

    severity_priority = {"danger": 0, "warning": 1, "info": 2, "success": 3}
    insights.sort(key=lambda x: severity_priority.get(x["severity"], 2))
    insights = insights[:10]

    if not insights:
        insights.append(
            {
                "severity": "success",
                "message": (
                    "Stable Performance - Project metrics are within normal "
                    "ranges, no immediate concerns detected"
                ),
                "recommendation": (
                    "Continue current practices and monitor for changes in "
                    "upcoming weeks. Consider documenting what is working well."
                ),
            }
        )

    return insights
