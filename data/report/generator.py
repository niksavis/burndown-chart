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
