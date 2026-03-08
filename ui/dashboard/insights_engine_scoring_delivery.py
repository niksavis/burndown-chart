"""Insights Engine - Delivery Signal Group Scoring.

Builds insight dictionaries for delivery-oriented signal groups:
velocity trend, budget health, scope change, velocity consistency,
and throughput efficiency.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data.recommendations.budget_signals import build_budget_health_signals
from data.recommendations.scope_signals import build_scope_signals
from data.recommendations.velocity_signals import (
    build_throughput_signals,
    build_velocity_consistency_signals,
    build_velocity_trend_signals,
)


def _build_delivery_insights(
    statistics_df: pd.DataFrame, budget_data: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Build velocity, budget, scope, consistency, and throughput insights."""
    insights: list[dict[str, Any]] = []

    velocity_signals = build_velocity_trend_signals(statistics_df)
    for signal in velocity_signals:
        metrics = signal["metrics"]
        if signal["id"] == "velocity_acceleration":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Accelerating Delivery - Team velocity increased "
                    f"{metrics['pct_change']:.2f}% in recent weeks "
                    f"({metrics['recent_velocity']:.1f} vs "
                    f"{metrics['historical_velocity']:.1f} items/week)",
                    "recommendation": (
                        "Consider taking on additional scope or bringing "
                        "forward deliverables to capitalize on this "
                        "momentum."
                    ),
                }
            )
        elif signal["id"] == "velocity_decline":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Velocity Decline - Team velocity decreased "
                    f"{metrics['pct_change']:.2f}% recently "
                    f"({metrics['recent_velocity']:.1f} vs "
                    f"{metrics['historical_velocity']:.1f} items/week)",
                    "recommendation": (
                        "Review team capacity, identify blockers, and "
                        "assess scope complexity. Consider retrospectives "
                        "to understand root causes."
                    ),
                }
            )

    budget_signals = build_budget_health_signals(budget_data)
    for signal in budget_signals:
        metrics = signal["metrics"]
        if signal["id"] == "budget_no_consumption":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Budget Status - No consumption detected",
                    "recommendation": (
                        "Budget tracking will begin once team velocity "
                        "and costs are established. Ensure project "
                        "parameters and team costs are configured "
                        "correctly."
                    ),
                }
            )
        elif signal["id"] == "budget_critical":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Budget Critical - "
                    f"{metrics['utilization_pct']:.2f}% consumed with only "
                    f"{metrics['runway_weeks']:.2f} weeks remaining",
                    "recommendation": (
                        "Immediate action required: Review remaining "
                        "scope, consider budget increase, or reduce team "
                        "costs. Current burn rate: "
                        f"{metrics['currency']}{metrics['burn_rate']:,.0f}/week."
                    ),
                }
            )
        elif signal["id"] == "budget_alert":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": (
                        "Budget Alert - "
                        f"{metrics['utilization_pct']:.2f}% consumed, "
                        "approaching budget limits"
                    ),
                    "recommendation": (
                        "Monitor closely: "
                        f"{metrics['runway_weeks']:.2f} weeks of runway "
                        "remaining at current burn rate "
                        f"({metrics['currency']}{metrics['burn_rate']:,.2f}/week). "
                        "Consider optimizing team costs or adjusting scope."
                    ),
                }
            )
        elif signal["id"] == "budget_limited_runway":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Limited Runway - Only "
                    f"{metrics['runway_weeks']:.2f} weeks of budget remaining",
                    "recommendation": (
                        "Plan for project completion or budget extension. "
                        "Current burn rate: "
                        f"{metrics['currency']}{metrics['burn_rate']:,.0f}/week. "
                        "Review if remaining scope aligns with available "
                        "runway."
                    ),
                }
            )
        elif signal["id"] == "budget_healthy":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Healthy Budget - "
                    f"{metrics['utilization_pct']:.2f}% consumed with "
                    f"{metrics['runway_weeks']:.2f} weeks of runway",
                    "recommendation": (
                        "Budget on track. Continue monitoring burn rate "
                        f"({metrics['currency']}{metrics['burn_rate']:,.0f}/week) "
                        "and adjust forecasts as scope evolves."
                    ),
                }
            )

    scope_signals = build_scope_signals(statistics_df)
    for signal in scope_signals:
        metrics = signal["metrics"]
        if signal["id"] == "scope_creep_acceleration":
            weeks_over = metrics["weeks_over"]
            excess_pct = metrics["excess_pct"]
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": (
                        "Accelerating Scope Creep - New items added faster "
                        "than completion rate for "
                        f"{weeks_over} consecutive weeks (backlog growing by "
                        f"{excess_pct:.2f}%)"
                    ),
                    "recommendation": (
                        "Implement change control immediately: (1) Temporary "
                        "freeze on new items to stabilize backlog, (2) Require "
                        "stakeholder approval for all additions, (3) Establish "
                        "scope change buffer in forecast, (4) Review and "
                        "prioritize existing backlog before accepting new work."
                    ),
                }
            )
        elif signal["id"] == "scope_burndown_acceleration":
            weeks_over = metrics["weeks_over"]
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": (
                        "Backlog Burn-Down Accelerating - Completing items "
                        "faster than new additions for "
                        f"{weeks_over} consecutive weeks"
                    ),
                    "recommendation": (
                        "Leverage momentum to maximize value delivery: "
                        "(1) Consider accepting additional valuable scope, "
                        "(2) Advance roadmap items, or (3) Use capacity for "
                        "quality/UX enhancements. Coordinate with product "
                        "stakeholders."
                    ),
                }
            )
        elif signal["id"] == "scope_growth_ratio":
            ratio = metrics["ratio"]
            scope_growth = metrics["total_created"]
            scope_completion = metrics["total_completed"]
            weeks_count = metrics["weeks_count"]
            time_window_desc = f" over {weeks_count} weeks" if weeks_count > 0 else ""
            if signal["severity"] == "warning":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": (
                            f"High Scope Growth{time_window_desc} - For every "
                            f"completed item, {ratio:.2f} new items are being "
                            f"created ({scope_growth} created vs "
                            f"{scope_completion} completed)"
                        ),
                        "recommendation": (
                            "Consider scope prioritization and implement "
                            "change management processes. Assess if "
                            "continuous scope growth impacts delivery "
                            "predictability."
                        ),
                    }
                )
            else:
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": (
                            f"Active Scope Management{time_window_desc} - "
                            f"Moderate scope growth with {ratio:.2f} new "
                            f"items created per completed item "
                            f"({scope_growth} created vs "
                            f"{scope_completion} completed)"
                        ),
                        "recommendation": (
                            "Continue monitoring scope changes and "
                            "maintaining stakeholder feedback loops to "
                            "ensure alignment."
                        ),
                    }
                )

    consistency_signals = build_velocity_consistency_signals(statistics_df)
    for signal in consistency_signals:
        metrics = signal["metrics"]
        if signal["id"] == "velocity_consistent":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Predictable Delivery - Low velocity variation "
                    f"({metrics['velocity_cv']:.2f}%) indicates "
                    "predictable delivery rhythm",
                    "recommendation": (
                        "Maintain current practices and leverage this "
                        "predictability for better sprint planning and "
                        "stakeholder commitments."
                    ),
                }
            )
        elif signal["id"] == "velocity_inconsistent":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Inconsistent Velocity - High velocity variation "
                    f"({metrics['velocity_cv']:.2f}%) suggests "
                    "unpredictable delivery",
                    "recommendation": (
                        "Investigate root causes: story sizing accuracy, "
                        "blockers, team availability, or external "
                        "dependencies. Consider establishing sprint "
                        "commitments discipline."
                    ),
                }
            )

    throughput_signals = build_throughput_signals(statistics_df)
    for signal in throughput_signals:
        metrics = signal["metrics"]
        if signal["id"] == "throughput_increase":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": (
                        "Increasing Throughput - Recent period delivered "
                        f"{metrics['recent_items']:.0f} items, exceeding "
                        "previous period by "
                        f"{metrics['pct_increase']:.2f}% "
                        f"({metrics['recent_items']:.0f} vs "
                        f"{metrics['prev_items']:.0f} items)"
                    ),
                    "recommendation": (
                        "Analyze what is working well and consider scaling "
                        "successful practices across the team or to other "
                        "projects."
                    ),
                }
            )

    return insights
