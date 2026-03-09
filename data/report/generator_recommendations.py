"""Actionable recommendations generator for HTML reports.

Generates project health insights from velocity, budget, scope, deadline,
and quality metrics. Large inline sections are delegated to
generator_recommendation_signals for size compliance.
Part of data/report/generator.py split.
"""

from typing import Any

from data.report.generator_recommendation_signals import (
    _build_budget_forecast_insights,
    _build_deadline_scenario_insights,
)
from data.types import MetricsResult


def calculate_recommendations(
    statistics: list[dict],
    dashboard_metrics: MetricsResult,
    extended_metrics: dict[str, Any],
    settings: dict[str, Any],
    time_period_weeks: int,
) -> dict[str, Any]:
    """
    Generate actionable recommendations based on project metrics.

    This uses a simplified subset of the insights engine logic from the app,
    focusing on critical/high severity insights only for report conciseness.

    Args:
        statistics: List of project statistics dicts
        dashboard_metrics: Dashboard metrics (velocity, health, forecast)
        extended_metrics: Extended metrics (DORA, Flow, Bug, Budget)
        settings: Project settings
        time_period_weeks: Analysis window in weeks

    Returns:
        Dictionary with insights list and metadata
    """
    import pandas as pd

    from data.recommendations.budget_signals import (
        build_budget_health_signals,
    )
    from data.recommendations.correlation_signals import build_correlation_signals
    from data.recommendations.pace_signals import build_required_pace_signals
    from data.recommendations.velocity_signals import (
        build_throughput_signals,
        build_velocity_consistency_signals,
        build_velocity_trend_signals,
    )

    insights = []
    statistics_df = pd.DataFrame(statistics)

    if statistics_df.empty:
        return {"insights": [], "data_points_count": time_period_weeks}

    # === VELOCITY TRENDS ===
    velocity_signals = build_velocity_trend_signals(statistics_df)
    for signal in velocity_signals:
        metrics = signal["metrics"]
        if signal["id"] == "velocity_acceleration":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Accelerating Delivery - Team velocity increased "
                    f"{metrics['pct_change']:.0f}% in recent weeks "
                    f"({metrics['recent_velocity']:.1f} vs "
                    f"{metrics['historical_velocity']:.1f} items/week)",
                    "recommendation": (
                        "Consider taking on additional scope or bringing "
                        "forward deliverables to capitalize on this momentum."
                    ),
                }
            )
        elif signal["id"] == "velocity_decline":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Velocity Decline - Team velocity decreased "
                    f"{metrics['pct_change']:.0f}% recently "
                    f"({metrics['recent_velocity']:.1f} vs "
                    f"{metrics['historical_velocity']:.1f} items/week)",
                    "recommendation": (
                        "Review team capacity, identify blockers, and assess "
                        "scope complexity. Consider retrospectives to "
                        "understand root causes."
                    ),
                }
            )

    # === THROUGHPUT EFFICIENCY ===
    throughput_signals = build_throughput_signals(statistics_df)
    for signal in throughput_signals:
        metrics = signal["metrics"]
        if signal["id"] == "throughput_increase":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Increasing Throughput - Recent period delivered "
                    f"{metrics['recent_items']:.0f} items, "
                    "exceeding previous period by "
                    f"{metrics['pct_increase']:.0f}% "
                    f"({metrics['recent_items']:.0f} vs "
                    f"{metrics['prev_items']:.0f} items)",
                    "recommendation": (
                        "Analyze what's working well and consider scaling "
                        "successful practices across the team or to other "
                        "projects."
                    ),
                }
            )

    # === BUDGET HEALTH ===
    if "budget" in extended_metrics:
        budget = extended_metrics["budget"]
        if budget.get("has_data"):
            budget_signals = build_budget_health_signals(budget)
            for signal in budget_signals:
                metrics = signal["metrics"]
                if signal["id"] == "budget_critical":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Budget Critical - "
                            f"{metrics['utilization_pct']:.0f}% consumed with only "
                            f"{metrics['runway_weeks']:.1f} weeks remaining",
                            "recommendation": (
                                "Immediate action required: Review remaining "
                                "scope, consider budget increase, or reduce "
                                "team costs. Current burn rate: "
                                f"{metrics['currency']}"
                                f"{metrics['burn_rate']:,.0f}/week."
                            ),
                        }
                    )
                elif signal["id"] == "budget_alert":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": (
                                "Budget Alert - "
                                f"{metrics['utilization_pct']:.0f}% consumed, "
                                "approaching budget limits"
                            ),
                            "recommendation": (
                                "Monitor closely: "
                                f"{metrics['runway_weeks']:.1f} weeks of runway "
                                "remaining at current burn rate "
                                f"({metrics['currency']}"
                                f"{metrics['burn_rate']:,.0f}/week). "
                                "Consider optimizing team costs or adjusting "
                                "scope."
                            ),
                        }
                    )
                elif signal["id"] == "budget_limited_runway":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Limited Runway - Only "
                            f"{metrics['runway_weeks']:.1f} weeks of budget remaining",
                            "recommendation": (
                                "Plan for project completion or budget extension. "
                                "Current burn rate: "
                                f"{metrics['currency']}"
                                f"{metrics['burn_rate']:,.0f}/week. "
                                "Review if remaining scope aligns with "
                                "available runway."
                            ),
                        }
                    )
                elif signal["id"] == "budget_healthy":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Healthy Budget - "
                            f"{metrics['utilization_pct']:.0f}% consumed with "
                            f"{metrics['runway_weeks']:.1f} weeks of runway",
                            "recommendation": (
                                "Budget on track. Continue monitoring burn "
                                "rate "
                                f"({metrics['currency']}"
                                f"{metrics['burn_rate']:,.0f}/week) "
                                "and adjust forecasts as scope evolves."
                            ),
                        }
                    )

    # === SCOPE MANAGEMENT ===
    if not statistics_df.empty:
        from data.recommendations.scope_signals import build_scope_signals

        scope_signals = build_scope_signals(statistics_df)
        scope_warning_added = False

        for signal in scope_signals:
            metrics = signal["metrics"]
            if signal["id"] == "scope_creep_acceleration":
                weeks_over = metrics["weeks_over"]
                excess_pct = metrics["excess_pct"]
                insights.append(
                    {
                        "severity": "warning",
                        "message": (
                            "Accelerating Scope Creep - New items added faster "
                            "than completion rate for "
                            f"{weeks_over} consecutive weeks "
                            f"(backlog growing by {excess_pct:.0f}%)"
                        ),
                        "recommendation": (
                            "Implement change control immediately: "
                            "(1) Temporary freeze on new items to stabilize "
                            "backlog, (2) Require stakeholder approval for all "
                            "additions, (3) Establish scope change budget/"
                            "buffer in forecast, (4) Review and prioritize "
                            "existing backlog before accepting new work."
                        ),
                    }
                )
                scope_warning_added = True
            elif signal["id"] == "scope_burndown_acceleration":
                weeks_over = metrics["weeks_over"]
                insights.append(
                    {
                        "severity": "success",
                        "message": (
                            "Backlog Burn-Down Accelerating - Completing items "
                            "faster than new additions for "
                            f"{weeks_over} consecutive weeks"
                        ),
                        "recommendation": (
                            "Leverage momentum to maximize value delivery: "
                            "(1) Consider accepting additional valuable scope "
                            "from backlog, (2) Advance future roadmap items to "
                            "capitalize on team productivity, or (3) Use "
                            "capacity for quality/UX enhancements. Coordinate "
                            "with product stakeholders."
                        ),
                    }
                )
            elif signal["id"] == "scope_growth_ratio" and not scope_warning_added:
                if signal["severity"] == "warning":
                    ratio = metrics["ratio"]
                    total_created = metrics["total_created"]
                    total_completed = metrics["total_completed"]
                    insights.append(
                        {
                            "severity": "warning",
                            "message": (
                                "Scope Growth Outpacing Completion - "
                                f"{ratio:.2f} new items per completed item "
                                f"({total_created:.0f} created vs "
                                f"{total_completed:.0f} completed)"
                            ),
                            "recommendation": (
                                "Prioritize backlog discipline: throttle new "
                                "additions, confirm stakeholder approvals, "
                                "and focus delivery on existing commitments."
                            ),
                        }
                    )
                    scope_warning_added = True

    # === DEADLINE SCENARIOS ===
    # CRITICAL: Use same calculation method as app (insights_engine.py lines 233-239)
    # Calculate from current time, not from pre-calculated forecast_date string
    deadline = dashboard_metrics.get("deadline")
    _build_deadline_scenario_insights(dashboard_metrics, deadline, insights)

    # === VELOCITY CONSISTENCY ===
    consistency_signals = build_velocity_consistency_signals(statistics_df)
    for signal in consistency_signals:
        metrics = signal["metrics"]
        if signal["id"] == "velocity_inconsistent":
            insights.append(
                {
                    "severity": signal["severity"],
                    "message": "Inconsistent Velocity - High velocity variation "
                    f"({metrics['velocity_cv']:.0f}%) suggests unpredictable delivery",
                    "recommendation": (
                        "Investigate root causes: story sizing accuracy, "
                        "blockers, team availability, or external dependencies. "
                        "Consider establishing sprint commitments discipline."
                    ),
                }
            )

    # === BUDGET VS FORECAST MISALIGNMENT ===
    _build_budget_forecast_insights(
        extended_metrics, dashboard_metrics, deadline, insights
    )

    # === CROSS-DOMAIN CORRELATION SIGNALS ===
    # Construct pert_data from dashboard_metrics (same approximation used for
    # deadline scenarios above: optimistic = 70%, pessimistic = 130%)
    _pert_base = dashboard_metrics.get("pert_time_items", 0) or 0
    _pert_data_for_signals = (
        {
            "pert_time_items": _pert_base,
            "pert_optimistic_days": _pert_base * 0.7,
            "pert_pessimistic_days": _pert_base * 1.3,
        }
        if _pert_base
        else None
    )
    correlation_signals = build_correlation_signals(
        statistics_df,
        budget_data=extended_metrics.get("budget"),
        pert_data=_pert_data_for_signals,
        deadline=deadline,
        bug_metrics=extended_metrics.get("bug_analysis"),
        flow_metrics=extended_metrics.get("flow"),
        dora_metrics=extended_metrics.get("dora"),
    )
    for _signal in correlation_signals:
        insights.append(
            {
                "severity": _signal["severity"],
                "message": _signal["message"],
                "recommendation": _signal["recommendation"],
            }
        )

    # === REQUIRED PACE (if deadline set) ===
    if deadline and len(statistics_df) > 0:
        try:
            pace_signals = build_required_pace_signals(statistics_df, deadline)
            for signal in pace_signals:
                metrics = signal["metrics"]
                gap_items = metrics["gap_pct"] / 100 * metrics["remaining_items"]
                if signal["id"] == "pace_critically_behind":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Critically Behind - Current velocity "
                            f"{metrics['gap_pct']:.0f}% below required pace "
                            "to meet deadline "
                            f"({metrics['current_velocity_items']:.1f} vs "
                            f"{metrics['required_velocity_items']:.1f} items/week)",
                            "recommendation": (
                                "Immediate action required: "
                                "(1) Increase team capacity if possible, "
                                "(2) Aggressively descope by "
                                f"{metrics['gap_pct']:.0f}% "
                                "("
                                f"{gap_items:.0f} "
                                "items), "
                                "(3) Request deadline extension, or "
                                "(4) Accept partial delivery risk. Need "
                                f"{metrics['gap_absolute']:.1f} more items/week."
                            ),
                        }
                    )
                elif signal["id"] == "pace_at_risk":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Below Target - Current velocity "
                            f"{metrics['gap_pct']:.0f}% below required pace "
                            "to meet deadline",
                            "recommendation": (
                                "Close the gap by: "
                                "(1) Removing blockers to increase throughput, "
                                "(2) Reducing WIP limits, "
                                "(3) Descoping low-priority items (~"
                                f"{gap_items:.0f}"
                                " "
                                "items), "
                                "or (4) Minor deadline adjustment. Deadline "
                                "achievable with focused improvements."
                            ),
                        }
                    )
        except Exception:
            pass

    # === QUALITY ISSUES ===
    if "bug_analysis" in extended_metrics:
        bug_metrics = extended_metrics["bug_analysis"]
        if bug_metrics.get("has_data"):
            bug_capacity = bug_metrics.get("bug_capacity_consumption_pct", 0)
            if bug_capacity > 30:
                insights.append(
                    {
                        "severity": "warning",
                        "message": (
                            "High Bug Workload - Bugs consuming "
                            f"{bug_capacity:.0f}% of team capacity"
                        ),
                        "recommendation": (
                            "Quality issues impacting delivery capacity. "
                            "Review testing processes, increase code review "
                            "rigor, and allocate dedicated time for technical "
                            "debt reduction."
                        ),
                    }
                )

    # Sort by severity (danger > warning > info > success)
    severity_priority = {"danger": 0, "warning": 1, "info": 2, "success": 3}
    insights.sort(key=lambda x: severity_priority.get(x["severity"], 2))

    # Balanced filtering: Include critical risks AND positive signals
    # for stakeholder confidence
    # Take top 3 danger/warning + top 2 success (max 5 total)
    # If fewer successes, allow more danger/warning up to 5 total.
    danger_warning_all = [i for i in insights if i["severity"] in ("danger", "warning")]
    success_insights = [i for i in insights if i["severity"] == "success"][:2]
    danger_limit = (
        3 if len(success_insights) == 2 else max(0, 5 - len(success_insights))
    )
    danger_warning = danger_warning_all[:danger_limit]

    # Combine: dangers/warnings first, then successes
    balanced_insights = danger_warning + success_insights

    return {"insights": balanced_insights, "data_points_count": time_period_weeks}
