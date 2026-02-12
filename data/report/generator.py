"""HTML report generator coordinator.

This module orchestrates the generation of self-contained HTML reports with project
metrics, charts, and analysis. It delegates to specialized modules for data loading,
metric calculation, chart generation, and rendering.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def generate_html_report(
    sections: List[str],
    time_period_weeks: int = 12,
    profile_id: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    """
    Generate a self-contained HTML report with project metrics snapshot.

    Args:
        sections: List of section identifiers to include in report
        time_period_weeks: Number of weeks to analyze (4, 12, 26, or 52)
        profile_id: Profile ID to generate report for (defaults to active profile)

    Returns:
        Tuple of (HTML string, metadata dict) where metadata contains:
            - profile_name: Display name of the profile
            - query_name: Display name of the query
            - time_period_weeks: Number of weeks in the analysis period

    Raises:
        ValueError: If no sections selected or data is invalid
    """
    if not sections:
        raise ValueError("At least one section must be selected for report generation")

    # Get active profile context
    from data.profile_manager import get_active_profile_and_query_display_names
    from data.query_manager import get_active_profile_id

    if not profile_id:
        profile_id = get_active_profile_id()

    context = get_active_profile_and_query_display_names()
    profile_name = context.get("profile_name") or profile_id
    query_name = context.get("query_name") or "Unknown Query"

    logger.info(
        f"Generating HTML report for {profile_name} / {query_name} "
        f"(sections={sections}, weeks={time_period_weeks})"
    )

    # Delegate to specialized modules
    from data.report.data_loader import load_report_data
    from data.report.chart_generator import generate_chart_scripts
    from data.report.renderer import render_template

    # Load and filter data for the time period
    report_data = load_report_data(profile_id, time_period_weeks)
    report_data["profile_id"] = profile_id  # Add for DORA metrics

    # Calculate all metrics for requested sections
    metrics = calculate_all_metrics(report_data, sections, time_period_weeks)

    # Add statistics to metrics for chart generation
    metrics["statistics"] = report_data["statistics"]

    # Generate Chart.js scripts for visualizations
    chart_scripts = generate_chart_scripts(metrics, sections)

    # Render HTML template
    html = render_template(
        profile_name=profile_name,
        query_name=query_name,
        time_period_weeks=time_period_weeks,
        sections=sections,
        metrics=metrics,
        chart_script="\n".join(chart_scripts),
    )

    logger.info(f"Report generated successfully: {len(html):,} bytes")

    # Return HTML and metadata for filename construction
    metadata = {
        "profile_name": profile_name,
        "query_name": query_name,
        "time_period_weeks": time_period_weeks,
    }
    return html, metadata


def generate_html_report_with_progress(
    sections: List[str],
    time_period_weeks: int = 12,
    profile_id: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    """
    Generate HTML report with progress updates.

    This is a wrapper around generate_html_report() that provides progress
    updates through the task_progress.json file.

    Args:
        sections: List of section identifiers to include in report
        time_period_weeks: Number of weeks to analyze
        profile_id: Profile ID to generate report for

    Returns:
        Tuple of (HTML string, metadata dict)
    """
    from data.report.renderer import update_report_progress

    try:
        update_report_progress(10, "Loading data...")
        html, metadata = generate_html_report(sections, time_period_weeks, profile_id)
        update_report_progress(100, "Report complete")
        return html, metadata
    except Exception as e:
        update_report_progress(0, f"Error: {str(e)}")
        raise


def calculate_all_metrics(
    report_data: Dict[str, Any], sections: List[str], time_period_weeks: int
) -> Dict[str, Any]:
    """
    Calculate all metrics for requested report sections.

    Args:
        report_data: Loaded and filtered report data
        sections: List of section identifiers
        time_period_weeks: Number of weeks in the analysis period

    Returns:
        Dictionary with metrics for each section
    """
    from data.report.domain_metrics import (
        calculate_burndown_metrics,
        calculate_bug_metrics,
        calculate_scope_metrics,
        calculate_flow_metrics,
        calculate_dora_metrics,
    )
    from data.report.dashboard_metrics import calculate_dashboard_metrics
    from data.report.helpers import calculate_budget_metrics

    metrics = {}

    # Extract show_points from settings (whether to use points or items for forecasting)
    show_points = report_data["settings"].get("show_points", False)

    # Calculate extended metrics first (needed for comprehensive health calculation)
    extended_metrics: Dict[str, Any] = {}

    # Bug Analysis metrics
    if "burndown" in sections:
        extended_metrics["bug_analysis"] = calculate_bug_metrics(
            report_data["jira_issues"],
            report_data["statistics"],
            report_data["settings"],
            report_data["weeks_count"],
        )

    # Flow metrics
    if "flow" in sections:
        extended_metrics["flow"] = calculate_flow_metrics(
            report_data["snapshots"],
            report_data["weeks_count"],
            report_data["week_labels"],  # Pass week labels for consistent filtering
        )

    # DORA metrics
    if "dora" in sections:
        extended_metrics["dora"] = calculate_dora_metrics(
            report_data["profile_id"], report_data["weeks_count"]
        )

    # Budget metrics (always calculated for health score)
    from data.query_manager import get_active_query_id

    # Note: Budget needs velocity which we calculate in dashboard, so we'll add it later
    # For now, mark that it's needed
    extended_metrics["budget_needed"] = True

    # Dashboard metrics (always calculated, shows summary)
    # Pass extended metrics for comprehensive health calculation
    metrics["dashboard"] = calculate_dashboard_metrics(
        report_data["all_statistics"],  # Use ALL stats for lifetime metrics
        report_data["statistics"],  # Windowed stats for velocity
        report_data["project_scope"],
        report_data["settings"],
        report_data["weeks_count"],
        show_points,
        extended_metrics,  # Pass extended metrics for health calculation
    )

    # Now calculate budget with velocity from dashboard
    if extended_metrics.get("budget_needed"):
        from data.query_manager import get_active_query_id

        query_id = get_active_query_id() or ""
        # Pass velocity from dashboard for accurate cost per item/point calculation
        velocity_items = metrics["dashboard"].get("velocity_items", 0.0)
        velocity_points = metrics["dashboard"].get("velocity_points", 0.0)
        extended_metrics["budget"] = calculate_budget_metrics(
            report_data["profile_id"],
            query_id,
            report_data["weeks_count"],
            velocity_items,
            velocity_points,
        )
        extended_metrics.pop("budget_needed")

        # CRITICAL FIX: Recalculate health_dimensions now that budget is available
        # The initial health calculation in calculate_dashboard_metrics() didn't have budget
        # This ensures Financial dimension is included when budget is configured
        from data.project_health_calculator import (
            calculate_comprehensive_project_health,
            prepare_dashboard_metrics_for_health,
        )

        # Prepare same dashboard metrics used in initial calculation
        dashboard = metrics["dashboard"]
        items_completion_pct = dashboard.get("items_completion_pct", 0)
        velocity_items = dashboard.get("velocity_items", 0)
        velocity_cv = dashboard.get("velocity_cv", 0)
        trend_direction = dashboard.get("trend_direction", "stable")
        recent_velocity_change = dashboard.get("recent_velocity_change", 0)
        schedule_variance_days = dashboard.get("schedule_variance_days", 0)
        completion_confidence = dashboard.get("completion_confidence", 50)

        logger.info(
            f"[REPORT HEALTH THIRD] velocity_items from dashboard={velocity_items:.2f}, "
            f"velocity_cv={velocity_cv:.2f}, schedule_var={schedule_variance_days:.2f}"
        )

        dashboard_metrics_for_health = prepare_dashboard_metrics_for_health(
            completion_percentage=items_completion_pct,
            current_velocity_items=velocity_items,
            velocity_cv=velocity_cv,
            trend_direction=trend_direction,
            recent_velocity_change=recent_velocity_change,
            schedule_variance_days=schedule_variance_days,
            completion_confidence=completion_confidence,
        )

        # Calculate scope_change_rate from dashboard (it's calculated there, not in scope metrics)
        scope_change_rate = dashboard.get("scope_change_rate", 0)

        # Recalculate comprehensive health WITH budget_metrics
        health_result = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_for_health,
            dora_metrics=extended_metrics.get("dora"),
            flow_metrics=extended_metrics.get("flow"),
            bug_metrics=extended_metrics.get("bug_analysis"),
            budget_metrics=extended_metrics.get("budget"),  # NOW has data
            scope_metrics={"scope_change_rate": scope_change_rate},
        )

        # Update dashboard metrics with correct health_dimensions including Financial
        metrics["dashboard"]["health_dimensions"] = health_result.get("dimensions", {})
        metrics["dashboard"]["health_score"] = health_result["overall_score"]

        logger.info(
            f"[REPORT HEALTH] Recalculated with budget: health_score={health_result['overall_score']:.1f}%, "
            f"financial_weight={health_result.get('dimensions', {}).get('financial', {}).get('weight', 0):.1f}%"
        )

    # Burndown metrics
    if "burndown" in sections:
        metrics["burndown"] = calculate_burndown_metrics(
            report_data["statistics"],
            report_data["project_scope"],
            report_data["weeks_count"],
        )

        # Bug Analysis (already calculated above for health)
        metrics["bug_analysis"] = extended_metrics.get("bug_analysis", {})

    # Scope metrics
    if "burndown" in sections:
        scope_metrics = calculate_scope_metrics(
            report_data["statistics"],
            report_data["project_scope"],
            report_data["weeks_count"],
        )
        metrics["scope"] = scope_metrics
        # Add to extended_metrics for health score
        # Include scope_change_rate from dashboard
        extended_metrics["scope"] = {
            **scope_metrics,
            "scope_change_rate": metrics["dashboard"].get("scope_change_rate", 0),
        }

    # Flow metrics (already calculated above for health)
    if "flow" in sections:
        metrics["flow"] = extended_metrics.get("flow", {})

    # DORA metrics (already calculated above for health)
    if "dora" in sections:
        metrics["dora"] = extended_metrics.get("dora", {})

    # Budget metrics (already calculated above)
    if "budget" in sections:
        metrics["budget"] = extended_metrics.get("budget", {})

    # Executive Summary (NEW - always calculated for reports)
    metrics["executive_summary"] = calculate_executive_summary(
        metrics["dashboard"], extended_metrics
    )

    # Actionable Insights/Recommendations (always calculated for reports)
    metrics["recommendations"] = calculate_recommendations(
        report_data["statistics"],
        metrics["dashboard"],
        extended_metrics,
        report_data["settings"],
        time_period_weeks,
    )

    return metrics


def calculate_executive_summary(
    dashboard_metrics: Dict[str, Any], extended_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate executive summary with top insights and risks.

    Args:
        dashboard_metrics: Dashboard metrics (health, completion, velocity, forecast)
        extended_metrics: Extended metrics (DORA, Flow, Bug, Budget, Scope)

    Returns:
        Dictionary with executive summary data
    """
    summary = {
        "has_data": dashboard_metrics.get("has_data", False),
        "health_score": dashboard_metrics.get("health_score", 0),
        "health_status": dashboard_metrics.get("health_status", "Unknown"),
        "completion_pct": dashboard_metrics.get("items_completion_pct", 0),
        "forecast_date": dashboard_metrics.get("forecast_date_items"),
        "deadline": dashboard_metrics.get("deadline"),
        "budget_runway_weeks": 0,
        "top_risks": [],
        "top_wins": [],
    }

    # Budget runway
    if "budget" in extended_metrics:
        budget = extended_metrics["budget"]
        if budget.get("has_data"):
            summary["budget_runway_weeks"] = budget.get("runway_weeks", 0)

    # Identify top 3 risks
    risks = []

    # Schedule risk
    if summary["forecast_date"] and summary["deadline"]:
        try:
            from datetime import datetime

            forecast_dt = datetime.strptime(summary["forecast_date"], "%Y-%m-%d")
            deadline_dt = datetime.strptime(summary["deadline"], "%Y-%m-%d")
            buffer_days = (deadline_dt - forecast_dt).days
            if buffer_days < 0:
                risks.append(
                    (
                        "Schedule",
                        f"Behind schedule by {abs(buffer_days)} days",
                        "critical",
                    )
                )
            elif buffer_days < 14:
                risks.append(
                    (
                        "Schedule",
                        f"Tight schedule, only {buffer_days} days buffer",
                        "high",
                    )
                )
        except Exception:
            pass

    # Budget risk
    if summary["budget_runway_weeks"] > 0:
        forecast_weeks = dashboard_metrics.get("forecast_weeks_items", 0)
        if forecast_weeks > summary["budget_runway_weeks"]:
            shortfall_weeks = forecast_weeks - summary["budget_runway_weeks"]
            risks.append(
                (
                    "Budget",
                    f"Budget depletes {shortfall_weeks:.0f} weeks before completion",
                    "critical",
                )
            )
        elif forecast_weeks * 1.2 > summary["budget_runway_weeks"]:
            risks.append(("Budget", "Budget runway tight if velocity drops", "high"))

    # Quality risk
    if "bug_analysis" in extended_metrics:
        bug_metrics = extended_metrics["bug_analysis"]
        if bug_metrics.get("has_data"):
            bug_capacity = bug_metrics.get("bug_capacity_consumption_pct", 0)
            if bug_capacity > 30:
                risks.append(
                    (
                        "Quality",
                        f"Bugs consuming {bug_capacity:.0f}% of capacity",
                        "high",
                    )
                )
            elif bug_capacity > 20:
                risks.append(
                    (
                        "Quality",
                        f"Bug workload elevated at {bug_capacity:.0f}%",
                        "medium",
                    )
                )

    # Velocity risk
    velocity_cv = dashboard_metrics.get("velocity_cv", 0)
    if velocity_cv > 50:
        risks.append(
            (
                "Predictability",
                f"High velocity variance (CV: {velocity_cv:.0f}%)",
                "medium",
            )
        )

    # Sort by severity and take top 3
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    risks.sort(key=lambda x: severity_order.get(x[2], 99))
    summary["top_risks"] = risks[:3]

    # Identify top 3 wins
    wins = []

    # Health win
    if summary["health_score"] >= 70:
        wins.append(
            (
                "Project Health",
                f"Strong overall health score: {summary['health_score']:.0f}%",
            )
        )
    elif summary["health_score"] >= 50:
        wins.append(
            ("Project Health", f"Stable health score: {summary['health_score']:.0f}%")
        )

    # Schedule win
    if summary["forecast_date"] and summary["deadline"]:
        try:
            from datetime import datetime

            forecast_dt = datetime.strptime(summary["forecast_date"], "%Y-%m-%d")
            deadline_dt = datetime.strptime(summary["deadline"], "%Y-%m-%d")
            buffer_days = (deadline_dt - forecast_dt).days
            if buffer_days >= 30:
                wins.append(
                    ("Schedule", f"Comfortable schedule buffer: {buffer_days} days")
                )
            elif buffer_days >= 14:
                wins.append(("Schedule", f"On track with {buffer_days} days buffer"))
        except Exception:
            pass

    # Velocity win
    trend = dashboard_metrics.get("trend_direction", "stable")
    if trend == "improving":
        change_pct = dashboard_metrics.get("recent_velocity_change", 0)
        wins.append(("Velocity", f"Team velocity improving: +{change_pct:.0f}%"))
    elif velocity_cv < 20:
        wins.append(("Predictability", f"Consistent velocity (CV: {velocity_cv:.0f}%)"))

    # Quality win
    if "bug_analysis" in extended_metrics:
        bug_metrics = extended_metrics["bug_analysis"]
        if bug_metrics.get("has_data"):
            bug_capacity = bug_metrics.get("bug_capacity_consumption_pct", 0)
            if bug_capacity < 15:
                wins.append(
                    ("Quality", f"Low bug workload: {bug_capacity:.0f}% of capacity")
                )

    summary["top_wins"] = wins[:3]

    return summary


def calculate_recommendations(
    statistics: List[Dict],
    dashboard_metrics: Dict[str, Any],
    extended_metrics: Dict[str, Any],
    settings: Dict[str, Any],
    time_period_weeks: int,
) -> Dict[str, Any]:
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
        build_budget_forecast_signals_from_dashboard,
        build_budget_health_signals,
    )
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
                    "recommendation": "Consider taking on additional scope or bringing forward deliverables to capitalize on this momentum.",
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
                    "recommendation": "Review team capacity, identify blockers, and assess scope complexity. Consider retrospectives to understand root causes.",
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
                    f"{metrics['recent_items']:.0f} items, exceeding previous period by "
                    f"{metrics['pct_increase']:.0f}% "
                    f"({metrics['recent_items']:.0f} vs {metrics['prev_items']:.0f} items)",
                    "recommendation": "Analyze what's working well and consider scaling successful practices across the team or to other projects.",
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
                            "recommendation": "Immediate action required: Review remaining scope, consider budget increase, or reduce team costs. Current burn rate: "
                            f"{metrics['currency']}{metrics['burn_rate']:,.0f}/week.",
                        }
                    )
                elif signal["id"] == "budget_alert":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Budget Alert - "
                            f"{metrics['utilization_pct']:.0f}% consumed, approaching budget limits",
                            "recommendation": "Monitor closely: "
                            f"{metrics['runway_weeks']:.1f} weeks of runway remaining at current burn rate "
                            f"({metrics['currency']}{metrics['burn_rate']:,.0f}/week). Consider optimizing team costs or adjusting scope.",
                        }
                    )
                elif signal["id"] == "budget_limited_runway":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Limited Runway - Only "
                            f"{metrics['runway_weeks']:.1f} weeks of budget remaining",
                            "recommendation": "Plan for project completion or budget extension. Current burn rate: "
                            f"{metrics['currency']}{metrics['burn_rate']:,.0f}/week. Review if remaining scope aligns with available runway.",
                        }
                    )
                elif signal["id"] == "budget_healthy":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Healthy Budget - "
                            f"{metrics['utilization_pct']:.0f}% consumed with "
                            f"{metrics['runway_weeks']:.1f} weeks of runway",
                            "recommendation": "Budget on track. Continue monitoring burn rate "
                            f"({metrics['currency']}{metrics['burn_rate']:,.0f}/week) and adjust forecasts as scope evolves.",
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
                        "message": f"Accelerating Scope Creep - New items added faster than completion rate for {weeks_over} consecutive weeks (backlog growing by {excess_pct:.0f}%)",
                        "recommendation": "Implement change control immediately: (1) Temporary freeze on new items to stabilize backlog, (2) Require stakeholder approval for all additions, (3) Establish scope change budget/buffer in forecast, (4) Review and prioritize existing backlog before accepting new work.",
                    }
                )
                scope_warning_added = True
            elif signal["id"] == "scope_burndown_acceleration":
                weeks_over = metrics["weeks_over"]
                insights.append(
                    {
                        "severity": "success",
                        "message": f"Backlog Burn-Down Accelerating - Completing items faster than new additions for {weeks_over} consecutive weeks",
                        "recommendation": "Leverage momentum to maximize value delivery: (1) Consider accepting additional valuable scope from backlog, (2) Advance future roadmap items to capitalize on team productivity, or (3) Use capacity for quality/UX enhancements. Coordinate with product stakeholders.",
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
                            "message": f"Scope Growth Outpacing Completion - {ratio:.2f} new items per completed item ({total_created:.0f} created vs {total_completed:.0f} completed)",
                            "recommendation": "Prioritize backlog discipline: throttle new additions, confirm stakeholder approvals, and focus delivery on existing commitments.",
                        }
                    )
                    scope_warning_added = True

    # === DEADLINE SCENARIOS ===
    # CRITICAL: Use same calculation method as app (insights_engine.py lines 233-239)
    # Calculate from current time, not from pre-calculated forecast_date string
    deadline = dashboard_metrics.get("deadline")
    if deadline:
        try:
            from datetime import datetime
            import pandas as pd

            deadline_date = pd.to_datetime(deadline)
            if not pd.isna(deadline_date):
                current_date = datetime.combine(
                    datetime.now().date(), datetime.min.time()
                )
                days_to_deadline = max(0, (deadline_date - current_date).days)

                # Use raw PERT days (same as app's pert_most_likely_days)
                pert_most_likely_days = dashboard_metrics.get("pert_time_items", 0)

                # Get PERT range for advanced scenarios
                # Calculate optimistic/pessimistic using PERT formula
                # Optimistic = pert_time * 0.7, Pessimistic = pert_time * 1.3 (approximate)
                pert_optimistic_days = (
                    pert_most_likely_days * 0.7 if pert_most_likely_days else 0
                )
                pert_pessimistic_days = (
                    pert_most_likely_days * 1.3 if pert_most_likely_days else 0
                )

                # A3: Deadline At Risk (CRITICAL)
                if days_to_deadline > 0 and pert_most_likely_days > days_to_deadline:
                    days_over = pert_most_likely_days - days_to_deadline
                    weeks_over = days_over / 7.0
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Deadline At Risk - Current forecast shows completion {days_over:.2f} days ({weeks_over:.2f} weeks) after deadline",
                            "recommendation": "Escalate immediately. Options: (1) Descope to MVP, (2) Request deadline extension, (3) Increase team capacity (with ramp-up risk). Review deadline feasibility with stakeholders.",
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
                            "message": f"Deadline Unachievable - Even best-case scenario completes {days_over:.0f} days after deadline",
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
                    buffer_pct = (
                        (buffer_days / days_to_deadline * 100)
                        if days_to_deadline > 0
                        else 0
                    )
                    insights.append(
                        {
                            "severity": "success",
                            "message": f"High Deadline Confidence - Even pessimistic forecast completes {buffer_days:.0f} days before deadline ({buffer_pct:.0f}% buffer)",
                            "recommendation": "Strong position. Consider: (1) Committing to stretch goals or additional features, (2) Adding low-risk quality enhancements, (3) Building buffer for technical debt or documentation. Use confidence to negotiate valuable scope additions.",
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
                            "message": f"Low Forecast Confidence - Wide prediction range (±{range_weeks:.0f} weeks) indicates delivery uncertainty",
                            "recommendation": "Improve predictability by: (1) Stabilizing team capacity and reducing interruptions, (2) Breaking down large stories into smaller chunks, (3) Reducing work-in-progress limits, (4) Addressing recurring blockers. Use Monte Carlo projections for stakeholder communication to set realistic expectations.",
                        }
                    )
        except Exception:
            pass

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
                    "recommendation": "Investigate root causes: story sizing accuracy, blockers, team availability, or external dependencies. Consider establishing sprint commitments discipline.",
                }
            )

    # === BUDGET VS FORECAST MISALIGNMENT ===
    if "budget" in extended_metrics and deadline:
        try:
            budget = extended_metrics["budget"]
            if budget.get("has_data"):
                budget_forecast_signals = build_budget_forecast_signals_from_dashboard(
                    budget, dashboard_metrics
                )
                for signal in budget_forecast_signals:
                    metrics = signal["metrics"]
                    if signal["id"] == "budget_exhaustion_before_completion":
                        insights.append(
                            {
                                "severity": signal["severity"],
                                "message": "Budget Exhaustion Before Completion - Budget runs out "
                                f"{metrics['shortfall_weeks']:.1f} weeks before forecast completion",
                                "recommendation": "Critical misalignment detected. Forecast requires "
                                f"{metrics['pert_forecast_weeks']:.1f} weeks but only "
                                f"{metrics['runway_weeks']:.1f} weeks of budget remain. Required actions: (1) Reduce burn rate by scaling down team, (2) Secure additional budget "
                                f"({metrics['shortfall_pct']:.0f}% increase needed), or (3) Aggressively descope to fit runway.",
                            }
                        )
                    elif signal["id"] == "budget_surplus_likely":
                        insights.append(
                            {
                                "severity": signal["severity"],
                                "message": "Budget Surplus Likely - Project forecast suggests "
                                f"{metrics['surplus_weeks']:.1f} weeks of unspent budget",
                                "recommendation": "Consider value-adding opportunities: (1) Adding high-priority backlog items within scope, (2) Investing in technical debt reduction or quality improvements, (3) Enhancing UX/documentation, or (4) Reallocating surplus to other initiatives. Confirm assumptions and opportunities with stakeholders.",
                            }
                        )
        except Exception:
            pass

    # === COMPOUND RISK PATTERNS ===
    if not statistics_df.empty and "budget" in extended_metrics:
        try:
            # Calculate velocity CV for compound risks
            velocity_cv = (
                (
                    statistics_df["completed_items"].std()
                    / statistics_df["completed_items"].mean()
                    * 100
                )
                if statistics_df["completed_items"].mean() > 0
                else 0
            )

            # H1: High Variance + Scope Growth (CRITICAL compound risk)
            if (
                velocity_cv > 40
                and "created_items" in statistics_df.columns
                and statistics_df["created_items"].sum()
                > statistics_df["completed_items"].sum() * 0.2
            ):
                insights.append(
                    {
                        "severity": "danger",
                        "message": f"Unstable Delivery + Scope Creep - High velocity variation ({velocity_cv:.0f}%) combined with increasing scope creates critical delivery risk",
                        "recommendation": "Dual intervention required: (1) Stabilize velocity through consistent team capacity, better story sizing, and reduced context switching, (2) Implement strict change control to prevent scope additions until delivery stabilizes. Consider freezing new features until predictability improves.",
                    }
                )

            # H2: Low Runway + High Forecast Uncertainty (CRITICAL compound risk)
            budget = extended_metrics["budget"]
            if budget.get("has_data"):
                import math

                runway_weeks = budget.get("runway_weeks", 0)
                pert_forecast_weeks = dashboard_metrics.get("pert_time_items_weeks", 0)
                pert_pessimistic_weeks = (
                    pert_forecast_weeks * 1.3 if pert_forecast_weeks else 0
                )
                pert_optimistic_weeks = (
                    pert_forecast_weeks * 0.7 if pert_forecast_weeks else 0
                )

                if (
                    not math.isinf(runway_weeks)
                    and runway_weeks > 0
                    and runway_weeks < 6
                    and pert_optimistic_weeks > 0
                    and pert_pessimistic_weeks > 0
                    and (pert_pessimistic_weeks - pert_optimistic_weeks) > 4
                ):
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Budget Risk + Forecast Uncertainty - Limited budget ({runway_weeks:.1f} weeks) combined with unpredictable delivery creates critical planning risk",
                            "recommendation": "Urgently stabilize project: (1) Define and commit to minimum viable scope that fits budget, (2) Increase forecast accuracy by breaking stories into smaller pieces and reducing WIP, (3) Secure budget contingency or prepare for partial delivery. Risk of budget overrun or incomplete delivery is high.",
                        }
                    )
        except Exception:
            pass

    # === REQUIRED PACE (if deadline set) ===
    if deadline and len(statistics_df) > 0:
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
                            "recommendation": "Immediate action required: (1) Increase team capacity if possible, (2) Aggressively descope by "
                            f"{metrics['gap_pct']:.0f}% ({metrics['gap_pct'] / 100 * metrics['remaining_items']:.0f} items), (3) Request deadline extension, or (4) Accept partial delivery risk. Need {metrics['gap_absolute']:.1f} more items/week.",
                        }
                    )
                elif signal["id"] == "pace_at_risk":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": "Pace Below Target - Current velocity "
                            f"{metrics['gap_pct']:.0f}% below required pace to meet deadline",
                            "recommendation": "Close the gap by: (1) Removing blockers to increase throughput, (2) Reducing WIP limits, (3) Descoping low-priority items (~"
                            f"{metrics['gap_pct'] / 100 * metrics['remaining_items']:.0f} items), or (4) Minor deadline adjustment. Deadline achievable with focused improvements.",
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
                        "message": f"High Bug Workload - Bugs consuming {bug_capacity:.0f}% of team capacity",
                        "recommendation": "Quality issues impacting delivery capacity. Review testing processes, increase code review rigor, and allocate dedicated time for technical debt reduction.",
                    }
                )

    # Sort by severity (danger > warning > info > success)
    severity_priority = {"danger": 0, "warning": 1, "info": 2, "success": 3}
    insights.sort(key=lambda x: severity_priority.get(x["severity"], 2))

    # Balanced filtering: Include critical risks AND positive signals for stakeholder confidence
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
