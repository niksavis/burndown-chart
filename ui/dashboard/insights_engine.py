"""Insights Engine - Actionable Insights, Recommendations, and Risk Analysis.

This module generates comprehensive intelligence for project health monitoring,
including velocity trends, budget alerts, scope analysis, deadline risk assessment,
and multi-metric correlation patterns.

The insights engine provides:
- Velocity analysis (acceleration, decline, consistency)
- Budget health monitoring (utilization, runway, burn rate)
- Scope change tracking (growth patterns, creep detection)
- Deadline risk assessment (PERT-based forecast vs deadline)
- Budget-forecast alignment analysis
- Multi-metric correlation patterns (compound risks and opportunities)
- Baseline deviation detection

Functions:
    create_insights_section: Generate actionable insights section with comprehensive intelligence
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from dash import html
import dash_bootstrap_components as dbc

from data.recommendations.budget_signals import (
    build_budget_forecast_signals_from_pert,
    build_budget_health_signals,
)
from data.recommendations.pace_signals import build_required_pace_signals
from data.recommendations.scope_signals import build_scope_signals
from data.recommendations.velocity_signals import (
    build_throughput_signals,
    build_velocity_consistency_signals,
    build_velocity_trend_signals,
)


def create_insights_section(
    statistics_df: pd.DataFrame,
    settings: dict[str, Any],
    budget_data: dict[str, Any] | None,
    pert_data: dict[str, Any] | None,
    deadline: str | None,
) -> html.Div:
    """Create actionable insights section with comprehensive intelligence.

    Args:
        statistics_df: Filtered project statistics (by data_points_count in callback)
        settings: Project settings dictionary
        budget_data: Budget baseline vs actual data
        pert_data: PERT forecast data (optimistic, most likely, pessimistic)
        deadline: Project deadline date string

    Returns:
        html.Div containing actionable insights section

    Note: statistics_df is already filtered by data_points_count in the callback.
    For velocity comparison, we split the filtered data into two halves:
    - First half: "historical" baseline velocity
    - Second half: "recent" velocity trend

    IMPORTANT: Scope growth calculations here use the SAME filtered time window as the
    Scope Analysis tab. Both calculate from the same statistics_df filtered by the
    Data Points slider. The numbers should always match. If they don't match:
    - Check if viewing stale/cached data (refresh the page)
    - Verify both tabs are using the same data_points_count setting
    """
    insights = []

    if not statistics_df.empty:
        # Velocity insights - compare first half vs second half of filtered data
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
                        "recommendation": "Consider taking on additional scope or bringing forward deliverables to capitalize on this momentum.",
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
                        "recommendation": "Review team capacity, identify blockers, and assess scope complexity. Consider retrospectives to understand root causes.",
                    }
                )

        # Budget insights (if budget data is available)
        budget_signals = build_budget_health_signals(budget_data)
        for signal in budget_signals:
            metrics = signal["metrics"]
            if signal["id"] == "budget_no_consumption":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": "Budget Status - No consumption detected",
                        "recommendation": "Budget tracking will begin once team velocity and costs are established. Ensure project parameters and team costs are configured correctly.",
                    }
                )
            elif signal["id"] == "budget_critical":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": "Budget Critical - "
                        f"{metrics['utilization_pct']:.2f}% consumed with only "
                        f"{metrics['runway_weeks']:.2f} weeks remaining",
                        "recommendation": "Immediate action required: Review remaining scope, consider budget increase, or reduce team costs. Current burn rate: "
                        f"{metrics['currency']}{metrics['burn_rate']:,.0f}/week.",
                    }
                )
            elif signal["id"] == "budget_alert":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": "Budget Alert - "
                        f"{metrics['utilization_pct']:.2f}% consumed, approaching budget limits",
                        "recommendation": "Monitor closely: "
                        f"{metrics['runway_weeks']:.2f} weeks of runway remaining at current burn rate "
                        f"({metrics['currency']}{metrics['burn_rate']:,.2f}/week). Consider optimizing team costs or adjusting scope.",
                    }
                )
            elif signal["id"] == "budget_limited_runway":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": "Limited Runway - Only "
                        f"{metrics['runway_weeks']:.2f} weeks of budget remaining",
                        "recommendation": "Plan for project completion or budget extension. Current burn rate: "
                        f"{metrics['currency']}{metrics['burn_rate']:,.0f}/week. Review if remaining scope aligns with available runway.",
                    }
                )
            elif signal["id"] == "budget_healthy":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": "Healthy Budget - "
                        f"{metrics['utilization_pct']:.2f}% consumed with "
                        f"{metrics['runway_weeks']:.2f} weeks of runway",
                        "recommendation": "Budget on track. Continue monitoring burn rate "
                        f"({metrics['currency']}{metrics['burn_rate']:,.0f}/week) and adjust forecasts as scope evolves.",
                    }
                )

        # Scope change insights
        scope_signals = build_scope_signals(statistics_df)
        for signal in scope_signals:
            metrics = signal["metrics"]
            if signal["id"] == "scope_creep_acceleration":
                weeks_over = metrics["weeks_over"]
                excess_pct = metrics["excess_pct"]
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": f"Accelerating Scope Creep - New items added faster than completion rate for {weeks_over} consecutive weeks (backlog growing by {excess_pct:.2f}%)",
                        "recommendation": "Implement change control immediately: (1) Temporary freeze on new items to stabilize backlog, (2) Require stakeholder approval for all additions, (3) Establish scope change buffer in forecast, (4) Review and prioritize existing backlog before accepting new work.",
                    }
                )
            elif signal["id"] == "scope_burndown_acceleration":
                weeks_over = metrics["weeks_over"]
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": f"Backlog Burn-Down Accelerating - Completing items faster than new additions for {weeks_over} consecutive weeks",
                        "recommendation": "Leverage momentum to maximize value delivery: (1) Consider accepting additional valuable scope, (2) Advance roadmap items, or (3) Use capacity for quality/UX enhancements. Coordinate with product stakeholders.",
                    }
                )
            elif signal["id"] == "scope_growth_ratio":
                ratio = metrics["ratio"]
                scope_growth = metrics["total_created"]
                scope_completion = metrics["total_completed"]
                weeks_count = metrics["weeks_count"]
                time_window_desc = (
                    f" over {weeks_count} weeks" if weeks_count > 0 else ""
                )
                if signal["severity"] == "warning":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": f"High Scope Growth{time_window_desc} - For every completed item, {ratio:.2f} new items are being created ({scope_growth} created vs {scope_completion} completed)",
                            "recommendation": "Consider scope prioritization and implement change management processes. Assess if continuous scope growth impacts delivery predictability.",
                        }
                    )
                else:
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": f"Active Scope Management{time_window_desc} - Moderate scope growth with {ratio:.2f} new items created per completed item ({scope_growth} created vs {scope_completion} completed)",
                            "recommendation": "Continue monitoring scope changes and maintaining stakeholder feedback loops to ensure alignment.",
                        }
                    )

        # Consistency insights
        consistency_signals = build_velocity_consistency_signals(statistics_df)
        for signal in consistency_signals:
            metrics = signal["metrics"]
            if signal["id"] == "velocity_consistent":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": "Predictable Delivery - Low velocity variation "
                        f"({metrics['velocity_cv']:.2f}%) indicates predictable delivery rhythm",
                        "recommendation": "Maintain current practices and leverage this predictability for better sprint planning and stakeholder commitments.",
                    }
                )
            elif signal["id"] == "velocity_inconsistent":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": "Inconsistent Velocity - High velocity variation "
                        f"({metrics['velocity_cv']:.2f}%) suggests unpredictable delivery",
                        "recommendation": "Investigate root causes: story sizing accuracy, blockers, team availability, or external dependencies. Consider establishing sprint commitments discipline.",
                    }
                )

        # Throughput efficiency insights - compare first half vs second half of filtered data
        throughput_signals = build_throughput_signals(statistics_df)
        for signal in throughput_signals:
            metrics = signal["metrics"]
            if signal["id"] == "throughput_increase":
                insights.append(
                    {
                        "severity": signal["severity"],
                        "message": "Increasing Throughput - Recent period delivered "
                        f"{metrics['recent_items']:.0f} items, exceeding previous period by "
                        f"{metrics['pct_increase']:.2f}% "
                        f"({metrics['recent_items']:.0f} vs {metrics['prev_items']:.0f} items)",
                        "recommendation": "Analyze what's working well and consider scaling successful practices across the team or to other projects.",
                    }
                )

    # === NEW INSIGHTS: Forecast vs Reality Alignment ===
    if pert_data and deadline:
        from datetime import datetime
        import pandas as pd

        try:
            # Parse deadline
            deadline_date = pd.to_datetime(deadline)
            if not pd.isna(deadline_date):
                current_date = datetime.combine(
                    datetime.now().date(), datetime.min.time()
                )
                days_to_deadline = max(0, (deadline_date - current_date).days)

                pert_most_likely_days = pert_data.get("pert_time_items", 0)
                pert_optimistic_days = pert_data.get("pert_optimistic_days", 0)
                pert_pessimistic_days = pert_data.get("pert_pessimistic_days", 0)

                # A3: Deadline Risk Alert (CRITICAL)
                if days_to_deadline > 0 and pert_most_likely_days > days_to_deadline:
                    days_over = pert_most_likely_days - days_to_deadline
                    weeks_over = days_over / 7.0
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Deadline At Risk - Current forecast shows completion {days_over:.2f} days ({weeks_over:.2f} weeks) after deadline",
                            "recommendation": f"Escalate immediately. Options: (1) Descope to MVP and reduce scope by {(days_over / pert_most_likely_days * 100):.2f}%, (2) Request deadline extension, (3) Increase team capacity (with ramp-up risk). Review deadline feasibility with stakeholders.",
                        }
                    )

                # G2: Optimistic Scenario Misses Deadline (CRITICAL)
                elif (
                    days_to_deadline > 0
                    and pert_optimistic_days > 0
                    and pert_optimistic_days > days_to_deadline
                ):
                    days_over = pert_optimistic_days - days_to_deadline
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Deadline Unachievable - Even best-case scenario completes {days_over:.2f} days after deadline",
                            "recommendation": "Immediate action required. Deadline is mathematically unattainable without dramatic changes: (1) Aggressively descope to critical MVP features only, (2) Negotiate deadline extension immediately, (3) Consider increasing team size (requires ramp-up time). No realistic path exists with current parameters.",
                        }
                    )

                # G1: Pessimistic Scenario Still Meets Deadline (SUCCESS)
                elif (
                    days_to_deadline > 0
                    and pert_pessimistic_days > 0
                    and pert_pessimistic_days < days_to_deadline
                ):
                    buffer_days = days_to_deadline - pert_pessimistic_days
                    insights.append(
                        {
                            "severity": "success",
                            "message": f"High Deadline Confidence - Even pessimistic forecast completes {buffer_days:.2f} days before deadline ({(buffer_days / days_to_deadline * 100):.2f}% buffer)",
                            "recommendation": "Strong position. Consider: (1) Committing to stretch goals or additional features, (2) Adding low-risk quality enhancements, (3) Building buffer for technical debt or documentation. Use confidence to negotiate valuable scope additions.",
                        }
                    )

                # A1: Forecast Slippage Alert (HIGH)
                if budget_data and pert_most_likely_days > 0:
                    baseline_end = budget_data.get("baseline", {}).get(
                        "allocated_end_date"
                    )
                    if baseline_end:
                        baseline_date = pd.to_datetime(baseline_end)
                        forecast_date = current_date + pd.Timedelta(
                            days=pert_most_likely_days
                        )
                        slippage_days = (forecast_date - baseline_date).days

                        if slippage_days > 14:  # >2 weeks slippage
                            slippage_weeks = slippage_days / 7.0
                            insights.append(
                                {
                                    "severity": "warning",
                                    "message": f"Forecast Slippage - Project expected to complete {slippage_weeks:.2f} weeks after planned end date",
                                    "recommendation": f"Re-evaluate scope priorities and adjust timeline expectations. Current velocity suggests {(pert_most_likely_days / 7.0):.2f} weeks needed vs {budget_data.get('baseline', {}).get('time_allocated_weeks', 0):.2f} weeks allocated. Consider descoping {(slippage_days / pert_most_likely_days * 100):.2f}% of remaining work or extending timeline.",
                                }
                            )

                # A2: Forecast Confidence Warning (MEDIUM)
                if (
                    pert_optimistic_days > 0
                    and pert_pessimistic_days > 0
                    and (pert_pessimistic_days - pert_optimistic_days) / 7.0 > 4
                ):
                    range_weeks = (pert_pessimistic_days - pert_optimistic_days) / 7.0
                    insights.append(
                        {
                            "severity": "warning",
                            "message": f"Low Forecast Confidence - Wide prediction range (±{range_weeks:.2f} weeks) indicates delivery uncertainty",
                            "recommendation": "Improve predictability by: (1) Stabilizing team capacity and reducing interruptions, (2) Breaking down large stories into smaller chunks, (3) Reducing work-in-progress limits, (4) Addressing recurring blockers. Use Monte Carlo projections for stakeholder communication to set realistic expectations.",
                        }
                    )
        except Exception:
            # Silently skip if date parsing fails
            pass

    # === NEW INSIGHTS: Budget vs Forecast Misalignment ===
    if pert_data and budget_data:
        try:
            budget_forecast_signals = build_budget_forecast_signals_from_pert(
                budget_data, pert_data
            )
            for signal in budget_forecast_signals:
                metrics = signal["metrics"]
                if signal["id"] == "budget_exhaustion_before_completion":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Budget Exhaustion Before Completion - Budget runs out "
                            f"{metrics['shortfall_weeks']:.2f} weeks before forecast completion",
                            "recommendation": "Critical misalignment detected. Forecast requires "
                            f"{metrics['pert_forecast_weeks']:.2f} weeks but only "
                            f"{metrics['runway_weeks']:.2f} weeks of budget remain. Required actions: (1) Reduce burn rate by scaling down team, (2) Secure additional budget "
                            f"({metrics['shortfall_pct']:.2f}% increase needed), or (3) Aggressively descope to fit runway.",
                        }
                    )
                elif signal["id"] == "budget_surplus_likely":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Budget Surplus Likely - Project forecast suggests "
                            f"{metrics['surplus_weeks']:.2f} weeks of unspent budget",
                            "recommendation": "Consider value-adding opportunities: (1) Adding high-priority backlog items within scope, (2) Investing in technical debt reduction or quality improvements, (3) Enhancing UX/documentation, or (4) Reallocating surplus to other initiatives. Confirm assumptions and opportunities with stakeholders.",
                        }
                    )
        except Exception:
            pass

    # === NEW INSIGHTS: Velocity & Capacity Patterns ===
    if not statistics_df.empty:
        try:
            # C1: Velocity Plateau Alert (MEDIUM)
            mid_point = len(statistics_df) // 2
            if mid_point > 2:
                recent_velocity = statistics_df.iloc[mid_point:][
                    "completed_items"
                ].mean()
                historical_velocity = statistics_df.iloc[:mid_point][
                    "completed_items"
                ].mean()

                # Check if stagnant AND below baseline
                if (
                    budget_data
                    and historical_velocity > 0
                    and abs(recent_velocity - historical_velocity)
                    < historical_velocity * 0.05
                ):
                    baseline_velocity = budget_data.get("baseline", {}).get(
                        "assumed_baseline_velocity", 0
                    )
                    if (
                        baseline_velocity > 0
                        and recent_velocity < baseline_velocity * 0.5
                    ):
                        pct_below = (1 - recent_velocity / baseline_velocity) * 100
                        insights.append(
                            {
                                "severity": "warning",
                                "message": f"Stagnant Velocity - Team throughput unchanged for {len(statistics_df)} weeks at {pct_below:.2f}% below baseline",
                                "recommendation": "Investigate capacity constraints: Are we hitting team size limits, facing consistent blockers, or underutilizing available capacity? Review sprint retrospectives for patterns and consider process improvements or removing impediments.",
                            }
                        )
        except Exception:
            pass

    # === NEW INSIGHTS: Scope & Requirements Management ===
    if not statistics_df.empty and "created_items" in statistics_df.columns:
        try:
            # D1: Scope Creep Acceleration (HIGH)
            if len(statistics_df) >= 4:
                recent_created = statistics_df.tail(4)["created_items"].sum()
                recent_completed = statistics_df.tail(4)["completed_items"].sum()

                # Check if sustained pattern
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
                            "message": f"Accelerating Scope Creep - New items added faster than completion rate for {weeks_over} consecutive weeks (backlog growing by {excess_pct:.2f}%)",
                            "recommendation": "Implement change control immediately: (1) Temporary freeze on new items to stabilize backlog, (2) Require stakeholder approval for all additions, (3) Establish scope change budget/buffer in forecast, (4) Review and prioritize existing backlog before accepting new work.",
                        }
                    )

            # D2: Backlog Burn-Down Accelerating (SUCCESS)
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
                                "message": f"Backlog Burn-Down Accelerating - Completing items faster than new additions for {weeks_over} consecutive weeks",
                                "recommendation": "Leverage momentum to maximize value delivery: (1) Consider accepting additional valuable scope from backlog, (2) Advance future roadmap items to capitalize on team productivity, or (3) Use capacity for quality/UX enhancements. Coordinate with product stakeholders.",
                            }
                        )

            # D3: Zero New Items Warning (INFO)
            if len(statistics_df) >= 3:
                recent_created = statistics_df.tail(3)["created_items"].sum()
                remaining = (
                    statistics_df.tail(1)["remaining_items"].iloc[0]
                    if len(statistics_df) > 0
                    and "remaining_items" in statistics_df.columns
                    else 0
                )

                if recent_created == 0 and remaining > 0:
                    insights.append(
                        {
                            "severity": "info",
                            "message": "No New Requirements - Zero items added for last 3 weeks",
                            "recommendation": "Verify backlog health: (1) Is product backlog refinement happening regularly? (2) Are stakeholders engaged and providing feedback? (3) Is this an intentional scope freeze for delivery focus? Ensure pipeline exists for future work and stakeholder feedback loops remain active.",
                        }
                    )
        except Exception:
            pass

    # === NEW INSIGHTS: Multi-Metric Correlations ===
    if not statistics_df.empty and budget_data:
        try:
            velocity_cv = (
                (
                    statistics_df["completed_items"].std()
                    / statistics_df["completed_items"].mean()
                    * 100
                )
                if statistics_df["completed_items"].mean() > 0
                else 0
            )

            # H1: High Variance + Scope Growth (CRITICAL)
            if (
                velocity_cv > 40
                and "created_items" in statistics_df.columns
                and statistics_df["created_items"].sum()
                > statistics_df["completed_items"].sum() * 0.2
            ):
                insights.append(
                    {
                        "severity": "danger",
                        "message": f"Unstable Delivery + Scope Creep - High velocity variation ({velocity_cv:.2f}%) combined with increasing scope creates critical delivery risk",
                        "recommendation": "Dual intervention required: (1) Stabilize velocity through consistent team capacity, better story sizing, and reduced context switching, (2) Implement strict change control to prevent scope additions until delivery stabilizes. Consider freezing new features until predictability improves.",
                    }
                )

            # H2: Low Runway + High Forecast Uncertainty (CRITICAL)
            if pert_data:
                import math

                runway_weeks = budget_data.get("runway_weeks", 0)
                pert_optimistic_days = pert_data.get("pert_optimistic_days", 0)
                pert_pessimistic_days = pert_data.get("pert_pessimistic_days", 0)

                if (
                    not math.isinf(runway_weeks)
                    and runway_weeks > 0
                    and runway_weeks < 6
                    and pert_optimistic_days > 0
                    and pert_pessimistic_days > 0
                    and (pert_pessimistic_days - pert_optimistic_days) / 7.0 > 4
                ):
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Budget Risk + Forecast Uncertainty - Limited budget ({runway_weeks:.2f} weeks) combined with unpredictable delivery creates critical planning risk",
                            "recommendation": "Urgently stabilize project: (1) Define and commit to minimum viable scope that fits budget, (2) Increase forecast accuracy by breaking stories into smaller pieces and reducing WIP, (3) Secure budget contingency or prepare for partial delivery. Risk of budget overrun or incomplete delivery is high.",
                        }
                    )

            # H3: Accelerating Velocity + Budget Surplus (OPPORTUNITY)
            mid_point = len(statistics_df) // 2
            if mid_point > 0 and pert_data:
                import math

                recent_velocity = statistics_df.iloc[mid_point:][
                    "completed_items"
                ].mean()
                historical_velocity = statistics_df.iloc[:mid_point][
                    "completed_items"
                ].mean()
                runway_weeks = budget_data.get("runway_weeks", 0)
                pert_forecast_weeks = (
                    pert_data.get("pert_time_items", 0) / 7.0
                    if pert_data.get("pert_time_items")
                    else 0
                )

                if (
                    historical_velocity > 0
                    and recent_velocity > historical_velocity * 1.15
                    and not math.isinf(runway_weeks)
                    and runway_weeks > 0
                    and pert_forecast_weeks > 0
                    and runway_weeks > pert_forecast_weeks + 3
                ):
                    velocity_increase = (
                        recent_velocity / historical_velocity - 1
                    ) * 100
                    surplus_weeks = runway_weeks - pert_forecast_weeks
                    insights.append(
                        {
                            "severity": "success",
                            "message": f"Performance Surplus - Team accelerating ({velocity_increase:.2f}% increase) while budget has {surplus_weeks:.2f} weeks headroom",
                            "recommendation": "Opportunity to maximize value delivery: (1) Bring forward high-value roadmap items from future releases, (2) Invest in technical debt reduction or architecture improvements, (3) Enhance product quality, UX, or documentation. Coordinate with stakeholders to capitalize on this favorable position.",
                        }
                    )
        except Exception:
            pass

    # === NEW INSIGHTS: Baseline Deviation Patterns ===
    if not statistics_df.empty and budget_data:
        try:
            actual_velocity = statistics_df["completed_items"].mean()
            baseline_velocity = budget_data.get("baseline", {}).get(
                "assumed_baseline_velocity", 0
            )

            # F1: Baseline Velocity Miss (HIGH)
            if (
                baseline_velocity > 0
                and actual_velocity < baseline_velocity * 0.8
                and len(statistics_df) >= 4
            ):
                pct_below = (1 - actual_velocity / baseline_velocity) * 100
                insights.append(
                    {
                        "severity": "warning",
                        "message": f"Underperforming Baseline - Team velocity {pct_below:.2f}% below planned baseline ({actual_velocity:.2f} vs {baseline_velocity:.2f} items/week) for {len(statistics_df)} weeks",
                        "recommendation": "Baseline assumptions appear incorrect. Actions: (1) Adjust baseline expectations to realistic levels and re-plan timeline, (2) Investigate root causes of underperformance (team capacity, story complexity, blockers), (3) Reset stakeholder expectations with revised forecasts. Document lessons learned for future planning.",
                    }
                )

            # F2: Cost Per Item Deviation (MEDIUM)
            cost_variance_pct = budget_data.get("variance", {}).get(
                "cost_per_item_variance_pct", 0
            )
            if abs(cost_variance_pct) > 25:
                if cost_variance_pct > 0:
                    insights.append(
                        {
                            "severity": "warning",
                            "message": f"Cost Efficiency Degraded - Items costing {cost_variance_pct:.2f}% more than baseline assumption",
                            "recommendation": "Stories more complex than expected or velocity lower than planned. Review: (1) Are stories properly sized and estimated? (2) Is team capacity lower than assumed? (3) Are there hidden complexities or technical debt? Consider adjusting cost assumptions for future planning.",
                        }
                    )
                else:
                    insights.append(
                        {
                            "severity": "success",
                            "message": f"Cost Efficiency Improved - Items costing {abs(cost_variance_pct):.2f}% less than baseline assumption",
                            "recommendation": "Team more efficient than planned, possibly due to higher velocity or simpler stories. Consider: (1) Taking on additional valuable scope within budget, (2) Reducing future budget projections if sustainable, (3) Documenting efficiency drivers for replication. Verify this is sustainable before committing to expanded scope.",
                        }
                    )
        except Exception:
            pass

    # === NEW INSIGHTS: Required Pace to Deadline ===
    if deadline and not statistics_df.empty:
        try:
            pace_signals = build_required_pace_signals(statistics_df, deadline)
            for signal in pace_signals:
                metrics = signal["metrics"]
                if signal["id"] == "pace_critically_behind":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Critically Behind - Current velocity "
                            f"{metrics['gap_pct']:.0f}% below required pace to meet deadline "
                            f"({metrics['current_velocity_items']:.1f} vs "
                            f"{metrics['required_velocity_items']:.1f} items/week)",
                            "recommendation": "Immediate action required: (1) Increase team capacity if possible, (2) Aggressively descope to reduce remaining work by "
                            f"{metrics['gap_pct']:.0f}% ({metrics['gap_pct'] / 100 * metrics['remaining_items']:.0f} items), (3) Request deadline extension of ~{metrics['delay_days']:.0f} days, or (4) Accept partial delivery risk. Current pace will miss deadline by significant margin. Need {metrics['gap_absolute']:.1f} more items/week.",
                        }
                    )
                elif signal["id"] == "pace_at_risk":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Below Target - Current velocity "
                            f"{metrics['gap_pct']:.0f}% below required pace, need "
                            f"{metrics['gap_absolute']:.1f} more items/week to meet deadline",
                            "recommendation": "Close the gap by: (1) Removing blockers to increase throughput "
                            f"{metrics['gap_pct']:.0f}%, (2) Reducing WIP limits to improve flow, (3) Descoping low-priority items (~{metrics['gap_pct'] / 100 * metrics['remaining_items']:.0f} items, {metrics['gap_pct']:.0f}% of remaining work), or (4) Minor deadline adjustment (+{metrics['delay_days']:.0f} days). Deadline achievable with focused improvements.",
                        }
                    )
                elif signal["id"] == "pace_significantly_ahead":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Significantly Ahead - Current velocity "
                            f"{metrics['ahead_pct']:.0f}% above required pace, tracking to complete ~{metrics['days_ahead']:.0f} days early",
                            "recommendation": "Capitalize on momentum: (1) Consider adding high-value scope from backlog (~"
                            f"{metrics['extra_capacity_items']:.0f} items, {metrics['ahead_pct']:.0f}% more capacity available), (2) Bring forward future roadmap items, (3) Invest in quality improvements or technical debt reduction, or (4) Communicate early completion potential to stakeholders. Strong delivery position.",
                        }
                    )
                elif signal["id"] == "pace_on_track":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace On Track - Current velocity "
                            f"{metrics['ahead_pct']:.0f}% above required pace, well-positioned to meet deadline",
                            "recommendation": "Maintain current momentum and monitor for changes. Consider small scope additions or quality investments if sustained. Continue removing blockers and maintaining team capacity.",
                        }
                    )
                elif signal["id"] == "pace_metric_divergence":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Metric Divergence - Items pace "
                            f"({metrics['ratio_items']:.0%}) and points pace ({metrics['ratio_points']:.0%}) significantly differ",
                            "recommendation": "Investigate story sizing accuracy: (1) Are larger items being completed without proportional points delivery? (2) Review estimation practices in refinement, (3) Consider whether items or points is more accurate predictor for this team, (4) Adjust forecasting primary metric accordingly. This divergence suggests estimation inconsistency.",
                        }
                    )
                elif signal["id"] == "pace_deadline_exceeded":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Deadline Exceeded - Project deadline has passed with work remaining",
                            "recommendation": "Critical status: (1) Establish new realistic deadline based on current velocity and remaining work, (2) Prioritize ruthlessly - complete only critical MVP features, (3) Communicate revised timeline to all stakeholders immediately, (4) Conduct post-mortem to understand planning gaps and prevent recurrence.",
                        }
                    )
        except Exception:
            pass

    # Sort insights by severity priority
    severity_priority = {"danger": 0, "warning": 1, "info": 2, "success": 3}
    insights.sort(key=lambda x: severity_priority.get(x["severity"], 2))

    # Limit to top 10 most important insights to avoid overwhelming users
    insights = insights[:10]

    if not insights:
        insights.append(
            {
                "severity": "success",
                "message": "Stable Performance - Project metrics are within normal ranges, no immediate concerns detected",
                "recommendation": "Continue current practices and monitor for changes in upcoming weeks. Consider documenting what's working well.",
            }
        )

    # Map severity to configuration (matching Quality Insights style)
    def get_severity_config(severity: str):
        severity_configs = {
            "danger": {
                "icon": "fa-exclamation-triangle",
                "color": "danger",
                "badge_text": "Critical",
            },
            "warning": {
                "icon": "fa-exclamation-circle",
                "color": "warning",
                "badge_text": "High",
            },
            "info": {
                "icon": "fa-info-circle",
                "color": "info",
                "badge_text": "Medium",
            },
            "success": {
                "icon": "fa-check-circle",
                "color": "success",
                "badge_text": "Low",
            },
        }
        return severity_configs.get(severity, severity_configs["info"])

    # Create insight items with expandable details (matching Quality Insights structure)
    insight_items = []
    for idx, insight in enumerate(insights):
        severity_config = get_severity_config(insight["severity"])
        collapse_id = f"actionable-insight-collapse-{idx}"

        insight_item = dbc.Card(
            [
                dbc.CardHeader(
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className=f"fas {severity_config['icon']} me-2"
                                    ),
                                    html.Span(
                                        insight["message"],
                                        className="insight-header-text",
                                    ),
                                ],
                                className="insight-header-main",
                            ),
                            html.Div(
                                [
                                    dbc.Badge(
                                        severity_config["badge_text"],
                                        color=severity_config["color"],
                                        className="insight-severity-badge",
                                    ),
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"actionable-insight-toggle-{idx}",
                                        color="link",
                                        size="sm",
                                        className="p-0 insight-toggle-btn",
                                    ),
                                ],
                                className="insight-header-actions",
                            ),
                        ],
                        className="insight-header-row",
                    ),
                    className=f"bg-{severity_config['color']} bg-opacity-10 border-{severity_config['color']}",
                    style={"cursor": "pointer"},
                    id=f"actionable-insight-header-{idx}",
                ),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.H6("Recommendation:", className="fw-bold mb-2"),
                            html.P(
                                insight["recommendation"],
                                className="mb-0",
                            ),
                        ],
                        className="insight-body",
                    ),
                    id=collapse_id,
                    is_open=False,
                ),
            ],
            className="mb-2",
        )
        insight_items.append(insight_item)

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-lightbulb me-2", style={"color": "#ffc107"}
                    ),
                    "Actionable Insights",
                ],
                className="mb-3 mt-4",
            ),
            html.Div(insight_items, className="mb-4"),
        ],
    )
