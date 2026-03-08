"""Insights Engine - Pace and Cross-Domain Correlation Scoring."""

from __future__ import annotations

from typing import Any

import pandas as pd

from data.recommendations.correlation_signals import build_correlation_signals
from data.recommendations.pace_signals import build_required_pace_signals


def _build_pace_correlation_insights(
    statistics_df: pd.DataFrame,
    budget_data: dict[str, Any] | None,
    pert_data: dict[str, Any] | None,
    deadline: str | None,
    bug_metrics: dict[str, Any] | None,
    flow_metrics: dict[str, Any] | None,
    dora_metrics: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build cross-domain correlation and required pace insights."""
    insights: list[dict[str, Any]] = []

    for signal in build_correlation_signals(
        statistics_df,
        budget_data=budget_data,
        pert_data=pert_data,
        deadline=deadline,
        bug_metrics=bug_metrics,
        flow_metrics=flow_metrics,
        dora_metrics=dora_metrics,
    ):
        insights.append(
            {
                "severity": signal["severity"],
                "message": signal["message"],
                "recommendation": signal["recommendation"],
            }
        )

    if deadline and not statistics_df.empty:
        try:
            pace_signals = build_required_pace_signals(statistics_df, deadline)
            for signal in pace_signals:
                metrics = signal["metrics"]
                if signal["id"] == "pace_critically_behind":
                    gap_items = metrics["gap_pct"] / 100 * metrics["remaining_items"]
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Critically Behind - Current velocity "
                            f"{metrics['gap_pct']:.0f}% below required pace "
                            "to meet deadline "
                            f"({metrics['current_velocity_items']:.1f} vs "
                            f"{metrics['required_velocity_items']:.1f} items/week)",
                            "recommendation": (
                                "Immediate action required: (1) Increase team "
                                "capacity if possible, (2) Aggressively descope "
                                "to reduce remaining work by "
                                f"{metrics['gap_pct']:.0f}% "
                                f"({gap_items:.0f} "
                                "items), (3) Request deadline extension of "
                                f"~{metrics['delay_days']:.0f} days, or "
                                "(4) Accept partial delivery risk. Current pace "
                                "will miss deadline by significant margin. Need "
                                f"{metrics['gap_absolute']:.1f} more items/week."
                            ),
                        }
                    )
                elif signal["id"] == "pace_at_risk":
                    gap_items = metrics["gap_pct"] / 100 * metrics["remaining_items"]
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Below Target - Current velocity "
                            f"{metrics['gap_pct']:.0f}% below required pace, need "
                            f"{metrics['gap_absolute']:.1f} more items/week "
                            "to meet deadline",
                            "recommendation": (
                                "Close the gap by: (1) Removing blockers to "
                                "increase throughput "
                                f"{metrics['gap_pct']:.0f}%, (2) Reducing WIP "
                                "limits to improve flow, (3) Descoping "
                                "low-priority items (~"
                                f"{gap_items:.0f} "
                                f"items, {metrics['gap_pct']:.0f}% of remaining "
                                "work), or (4) Minor deadline adjustment "
                                f"(+{metrics['delay_days']:.0f} days). Deadline "
                                "achievable with focused improvements."
                            ),
                        }
                    )
                elif signal["id"] == "pace_significantly_ahead":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Significantly Ahead - Current velocity "
                            f"{metrics['ahead_pct']:.0f}% above required pace, "
                            f"tracking to complete ~{metrics['days_ahead']:.0f} "
                            "days early",
                            "recommendation": (
                                "Capitalize on momentum: (1) Consider adding "
                                "high-value scope from backlog (~"
                                f"{metrics['extra_capacity_items']:.0f} items, "
                                f"{metrics['ahead_pct']:.0f}% more capacity "
                                "available), (2) Bring forward future roadmap "
                                "items, (3) Invest in quality improvements or "
                                "technical debt reduction, or (4) Communicate "
                                "early completion potential to stakeholders. "
                                "Strong delivery position."
                            ),
                        }
                    )
                elif signal["id"] == "pace_on_track":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace On Track - Current velocity "
                            f"{metrics['ahead_pct']:.0f}% above required pace, "
                            "well-positioned to meet deadline",
                            "recommendation": (
                                "Maintain current momentum and monitor for "
                                "changes. Consider small scope additions or "
                                "quality investments if sustained. Continue "
                                "removing blockers and maintaining team "
                                "capacity."
                            ),
                        }
                    )
                elif signal["id"] == "pace_metric_divergence":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Metric Divergence - Items pace "
                            f"({metrics['ratio_items']:.0%}) and points pace "
                            f"({metrics['ratio_points']:.0%}) significantly differ",
                            "recommendation": (
                                "Investigate story sizing accuracy: "
                                "(1) Are larger items being completed without "
                                "proportional points delivery? (2) Review "
                                "estimation practices in refinement, "
                                "(3) Consider whether items or points is more "
                                "accurate predictor for this team, (4) Adjust "
                                "forecasting primary metric accordingly. This "
                                "divergence suggests estimation inconsistency."
                            ),
                        }
                    )
                elif signal["id"] == "pace_deadline_exceeded":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": (
                                "Deadline Exceeded - Project deadline has "
                                "passed with work remaining"
                            ),
                            "recommendation": (
                                "Critical status: (1) Establish new realistic "
                                "deadline based on current velocity and "
                                "remaining work, (2) Prioritize ruthlessly - "
                                "complete only critical MVP features, "
                                "(3) Communicate revised timeline to all "
                                "stakeholders immediately, (4) Conduct "
                                "post-mortem to understand planning gaps and "
                                "prevent recurrence."
                            ),
                        }
                    )
        except Exception:
            pass

    return insights
