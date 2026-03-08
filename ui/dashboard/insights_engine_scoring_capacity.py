"""Insights Engine - Capacity, Scope, and Baseline Deviation Scoring."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _build_capacity_scope_insights(
    statistics_df: pd.DataFrame,
    budget_data: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build velocity plateau, scope management, and baseline deviation insights."""
    insights: list[dict[str, Any]] = []

    try:
        mid_point = len(statistics_df) // 2
        if mid_point > 2:
            recent_velocity = statistics_df.iloc[mid_point:]["completed_items"].mean()
            historical_velocity = statistics_df.iloc[:mid_point][
                "completed_items"
            ].mean()

            if (
                budget_data
                and historical_velocity > 0
                and abs(recent_velocity - historical_velocity)
                < historical_velocity * 0.05
            ):
                baseline_velocity = budget_data.get("baseline", {}).get(
                    "assumed_baseline_velocity", 0
                )
                if baseline_velocity > 0 and recent_velocity < baseline_velocity * 0.5:
                    pct_below = (1 - recent_velocity / baseline_velocity) * 100
                    insights.append(
                        {
                            "severity": "warning",
                            "message": (
                                "Stagnant Velocity - Team throughput "
                                "unchanged for "
                                f"{len(statistics_df)} weeks at "
                                f"{pct_below:.2f}% below baseline"
                            ),
                            "recommendation": (
                                "Investigate capacity constraints: Are we "
                                "hitting team size limits, facing "
                                "consistent blockers, or underutilizing "
                                "available capacity? Review sprint "
                                "retrospectives for patterns and consider "
                                "process improvements or removing "
                                "impediments."
                            ),
                        }
                    )
    except Exception:
        pass

    if "created_items" in statistics_df.columns:
        try:
            if len(statistics_df) >= 4:
                recent_created = statistics_df.tail(4)["created_items"].sum()
                recent_completed = statistics_df.tail(4)["completed_items"].sum()

                weeks_over = sum(
                    1
                    for _, row in statistics_df.tail(4).iterrows()
                    if row["created_items"] > row["completed_items"]
                )

                if recent_created > recent_completed and weeks_over >= 3:
                    excess_pct = (
                        (recent_created - recent_completed) / recent_completed * 100
                        if recent_completed > 0
                        else 0
                    )
                    insights.append(
                        {
                            "severity": "warning",
                            "message": (
                                "Accelerating Scope Creep - New items added "
                                "faster than completion rate for "
                                f"{weeks_over} consecutive weeks (backlog "
                                f"growing by {excess_pct:.2f}%)"
                            ),
                            "recommendation": (
                                "Implement change control immediately: "
                                "(1) Temporary freeze on new items to "
                                "stabilize backlog, (2) Require stakeholder "
                                "approval for all additions, (3) Establish "
                                "scope change budget/buffer in forecast, "
                                "(4) Review and prioritize existing backlog "
                                "before accepting new work."
                            ),
                        }
                    )

            if len(statistics_df) >= 4:
                recent_net = (
                    statistics_df.tail(4)["completed_items"].sum()
                    - statistics_df.tail(4)["created_items"].sum()
                )
                if recent_net > 0:
                    weeks_over = sum(
                        1
                        for _, row in statistics_df.tail(4).iterrows()
                        if row["completed_items"] > row["created_items"]
                    )
                    if weeks_over >= 4:
                        insights.append(
                            {
                                "severity": "success",
                                "message": (
                                    "Backlog Burn-Down Accelerating - "
                                    "Completing items faster than new additions "
                                    f"for {weeks_over} consecutive weeks"
                                ),
                                "recommendation": (
                                    "Leverage momentum to maximize value "
                                    "delivery: (1) Consider accepting "
                                    "additional valuable scope from backlog, "
                                    "(2) Advance future roadmap items to "
                                    "capitalize on team productivity, or "
                                    "(3) Use capacity for quality/UX "
                                    "enhancements. Coordinate with product "
                                    "stakeholders."
                                ),
                            }
                        )

            if len(statistics_df) >= 3:
                recent_created_3 = statistics_df.tail(3)["created_items"].sum()
                remaining = (
                    statistics_df.tail(1)["remaining_items"].iloc[0]
                    if len(statistics_df) > 0
                    and "remaining_items" in statistics_df.columns
                    else 0
                )

                if recent_created_3 == 0 and remaining > 0:
                    insights.append(
                        {
                            "severity": "info",
                            "message": (
                                "No New Requirements - Zero items added for "
                                "last 3 weeks"
                            ),
                            "recommendation": (
                                "Verify backlog health: (1) Is product backlog "
                                "refinement happening regularly? "
                                "(2) Are stakeholders engaged and providing "
                                "feedback? (3) Is this an intentional scope "
                                "freeze for delivery focus? Ensure pipeline "
                                "exists for future work and stakeholder "
                                "feedback loops remain active."
                            ),
                        }
                    )
        except Exception:
            pass

    if budget_data:
        try:
            actual_velocity = statistics_df["completed_items"].mean()
            baseline_velocity = budget_data.get("baseline", {}).get(
                "assumed_baseline_velocity", 0
            )

            if (
                baseline_velocity > 0
                and actual_velocity < baseline_velocity * 0.8
                and len(statistics_df) >= 4
            ):
                pct_below = (1 - actual_velocity / baseline_velocity) * 100
                insights.append(
                    {
                        "severity": "warning",
                        "message": (
                            "Underperforming Baseline - Team velocity "
                            f"{pct_below:.2f}% below planned baseline "
                            f"({actual_velocity:.2f} vs "
                            f"{baseline_velocity:.2f} items/week) for "
                            f"{len(statistics_df)} weeks"
                        ),
                        "recommendation": (
                            "Baseline assumptions appear incorrect. Actions: "
                            "(1) Adjust baseline expectations to realistic "
                            "levels and re-plan timeline, (2) Investigate root "
                            "causes of underperformance (team capacity, story "
                            "complexity, blockers), (3) Reset stakeholder "
                            "expectations with revised forecasts. Document "
                            "lessons learned for future planning."
                        ),
                    }
                )

            cost_variance_pct = budget_data.get("variance", {}).get(
                "cost_per_item_variance_pct", 0
            )
            if abs(cost_variance_pct) > 25:
                if cost_variance_pct > 0:
                    insights.append(
                        {
                            "severity": "warning",
                            "message": (
                                "Cost Efficiency Degraded - Items costing "
                                f"{cost_variance_pct:.2f}% more than baseline "
                                "assumption"
                            ),
                            "recommendation": (
                                "Stories more complex than expected or "
                                "velocity lower than planned. Review: "
                                "(1) Are stories properly sized and estimated? "
                                "(2) Is team capacity lower than assumed? "
                                "(3) Are there hidden complexities or technical "
                                "debt? Consider adjusting cost assumptions for "
                                "future planning."
                            ),
                        }
                    )
                else:
                    insights.append(
                        {
                            "severity": "success",
                            "message": (
                                "Cost Efficiency Improved - Items costing "
                                f"{abs(cost_variance_pct):.2f}% less than "
                                "baseline assumption"
                            ),
                            "recommendation": (
                                "Team more efficient than planned, possibly "
                                "due to higher velocity or simpler stories. "
                                "Consider: (1) Taking on additional valuable "
                                "scope within budget, (2) Reducing future "
                                "budget projections if sustainable, "
                                "(3) Documenting efficiency drivers for "
                                "replication. Verify this is sustainable before "
                                "committing to expanded scope."
                            ),
                        }
                    )
        except Exception:
            pass

    return insights
