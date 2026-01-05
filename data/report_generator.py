"""HTML report generator for burndown charts and metrics.

This module generates self-contained HTML reports with project metrics, charts, and analysis.
All calculations use consistent time-based filtering and proper data aggregation methods.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

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

    # Load and filter data for the time period
    report_data = _load_report_data(profile_id, time_period_weeks)
    report_data["profile_id"] = profile_id  # Add for DORA metrics

    # Calculate all metrics for requested sections
    metrics = _calculate_all_metrics(report_data, sections, time_period_weeks)

    # Add statistics to metrics for chart generation
    metrics["statistics"] = report_data["statistics"]

    # Generate Chart.js scripts for visualizations
    chart_scripts = _generate_chart_scripts(metrics, sections)

    # Render HTML template
    html = _render_template(
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


def _load_report_data(profile_id: str, weeks: int) -> Dict[str, Any]:
    """
    Load all data needed for report generation.

    Loads project scope, statistics, snapshots, settings, and JIRA issues.
    Applies time-based filtering to statistics and snapshots to match the
    requested time period, excluding the current incomplete week.

    Args:
        profile_id: Profile ID to load data for
        weeks: Number of weeks to include in the period

    Returns:
        Dictionary containing:
            - project_scope: Current project scope (remaining items/points)
            - statistics: Filtered statistics for the time period
            - snapshots: Filtered weekly snapshots for the time period
            - settings: App settings (deadline, milestone, bug types)
            - jira_issues: Raw JIRA issues for ad-hoc calculations
            - weeks_count: Actual number of weeks with data
    """
    from data.persistence import load_unified_project_data, load_app_settings
    from data.metrics_snapshots import load_snapshots
    from data.profile_manager import get_active_query_workspace

    # Load core data
    project_data = load_unified_project_data()
    all_snapshots = load_snapshots()
    settings = load_app_settings()

    # Load JIRA issues from cache
    jira_issues = []
    try:
        query_workspace = get_active_query_workspace()
        cache_file = query_workspace / "jira_cache.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                jira_issues = cache_data.get("issues", [])
        logger.info(f"Loaded {len(jira_issues)} JIRA issues for report")
    except Exception as e:
        logger.warning(f"Could not load JIRA issues: {e}")

    # Calculate time period boundaries
    # CRITICAL: Use last statistics date as reference, not datetime.now()
    # Statistics are weekly (Mondays), so using "now" may exclude valid weeks
    all_stats = project_data.get("statistics", [])

    # Find the last statistics date to use as reference
    last_stat_date = None
    if all_stats:
        for stat in all_stats:
            stat_date = datetime.fromisoformat(stat["date"].replace("Z", "+00:00"))
            if last_stat_date is None or stat_date > last_stat_date:
                last_stat_date = stat_date

    # Use last stat date if available, otherwise fall back to now
    reference_date = last_stat_date if last_stat_date else datetime.now()
    cutoff_date = reference_date - timedelta(weeks=weeks)

    # Use ISO week format (%V) to match app and metrics snapshots (Monday-based weeks)
    current_week = reference_date.strftime("%G-W%V")

    # Filter statistics to time period (get last N weeks from reference date)
    filtered_stats = []
    if all_stats:
        for stat in all_stats:
            stat_date = datetime.fromisoformat(stat["date"].replace("Z", "+00:00"))
            # Include if within the time window (last N weeks from reference date)
            if stat_date >= cutoff_date and stat_date <= reference_date:
                filtered_stats.append(stat)

    # Filter snapshots to time period (exclude current incomplete week)
    filtered_snapshots = {}
    if all_snapshots:
        for week_label, snapshot_data in all_snapshots.items():
            week_date = _parse_week_label(week_label)
            # Include if >= cutoff AND not current week
            if week_date >= cutoff_date and week_label != current_week:
                filtered_snapshots[week_label] = snapshot_data

    # Use REQUESTED weeks, not snapshot count
    # The velocity calculation groups statistics by ISO week, so it doesn't need to match snapshot count
    # CRITICAL: This must match the user's selected data window in the app (data_points_count)
    weeks_count = weeks

    logger.info(
        f"Loaded data: {len(filtered_stats)} statistics, "
        f"{len(filtered_snapshots)} snapshot weeks (using requested weeks={weeks_count})"
    )

    return {
        "project_scope": project_data.get("project_scope", {}),
        "statistics": filtered_stats,
        "all_statistics": all_stats,  # Full history for lifetime metrics
        "snapshots": filtered_snapshots,
        "settings": settings,
        "jira_issues": jira_issues,
        "weeks_count": weeks_count,
    }


def _calculate_all_metrics(
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
    metrics = {}

    # Extract show_points from settings (whether to use points or items for forecasting)
    show_points = report_data["settings"].get("show_points", False)

    # Dashboard metrics (always calculated, shows summary)
    metrics["dashboard"] = _calculate_dashboard_metrics(
        report_data["all_statistics"],  # Use ALL stats for lifetime metrics
        report_data["statistics"],  # Windowed stats for velocity
        report_data["project_scope"],
        report_data["settings"],
        report_data["weeks_count"],
        show_points,
    )

    # Burndown metrics
    if "burndown" in sections:
        metrics["burndown"] = _calculate_burndown_metrics(
            report_data["statistics"],
            report_data["project_scope"],
            report_data["weeks_count"],
        )

        # Bug Analysis (sub-section of burndown)
        metrics["bug_analysis"] = _calculate_bug_metrics(
            report_data["jira_issues"],
            report_data["statistics"],
            report_data["settings"],
            report_data["weeks_count"],
        )

    # Scope metrics
    if "burndown" in sections:
        metrics["scope"] = _calculate_scope_metrics(
            report_data["statistics"],
            report_data["project_scope"],
            report_data["weeks_count"],
        )

    # Flow metrics
    if "flow" in sections:
        metrics["flow"] = _calculate_flow_metrics(
            report_data["snapshots"], report_data["weeks_count"]
        )

    # DORA metrics
    if "dora" in sections:
        metrics["dora"] = _calculate_dora_metrics(
            report_data["profile_id"], report_data["weeks_count"]
        )

    # Budget metrics
    if "budget" in sections:
        from data.query_manager import get_active_query_id

        query_id = get_active_query_id() or ""
        # Pass velocity_points from dashboard for cost_per_point calculation
        velocity_points = metrics["dashboard"].get("velocity_points", 0.0)
        metrics["budget"] = _calculate_budget_metrics(
            report_data["profile_id"],
            query_id,
            report_data["weeks_count"],
            velocity_points,
        )

    return metrics


def _calculate_dashboard_metrics(
    all_statistics: List[Dict],
    windowed_statistics: List[Dict],
    project_scope: Dict,
    settings: Dict,
    weeks_count: int,
    show_points: bool = False,
) -> Dict[str, Any]:
    """
    Calculate dashboard summary metrics using LIFETIME-based calculations (same as app).

    CRITICAL RULES (matching data/processing.py):
    1. Statistics are INCREMENTAL (daily values) - must use .sum() not .iloc[-1]
    2. Use ALL statistics for completed items (lifetime total, not windowed)
    3. Total comes from settings.estimated_total_items (NOT calculated)
    4. Remaining = total - completed (same as app)
    5. Completion % = completed / total (LIFETIME, same as app)
    6. Health score uses weighted formula (progress 25%, schedule 30%, velocity 25%, confidence 20%)

    Args:
        all_statistics: ALL statistics for lifetime completion calculation
        windowed_statistics: Windowed statistics for velocity calculation
        project_scope: Current project scope with remaining items/points
        settings: App settings with deadline and milestone
        weeks_count: Actual number of weeks with data
        show_points: Whether to use points-based (True) or items-based (False) forecasting

    Returns:
        Dictionary with dashboard metrics
    """
    if not all_statistics:
        return {
            "has_data": False,
            "completed_items": 0,
            "completed_points": 0,
            "remaining_items": 0,
            "remaining_points": 0,
            "total_items": 0,
            "total_points": 0,
            "items_completion_pct": 0,
            "points_completion_pct": 0,
            "health_score": 0,
            "health_status": "Unknown",
            "deadline": None,
            "milestone": None,
            "velocity_items": 0,
            "velocity_points": 0,
        }

    # Calculate completed items from WINDOWED statistics (same as app)
    df_windowed = pd.DataFrame(windowed_statistics)
    # Convert date column to datetime for proper date arithmetic
    if not df_windowed.empty and "date" in df_windowed.columns:
        df_windowed["date"] = pd.to_datetime(
            df_windowed["date"], format="mixed", errors="coerce"
        )

    # Create dataframe from ALL statistics for last date (same as app in processing.py)
    df_all = pd.DataFrame(all_statistics)
    if not df_all.empty and "date" in df_all.columns:
        df_all["date"] = pd.to_datetime(df_all["date"], format="mixed", errors="coerce")

    completed_items = (
        int(df_windowed["completed_items"].sum()) if not df_windowed.empty else 0
    )
    completed_points = (
        round(df_windowed["completed_points"].sum(), 1) if not df_windowed.empty else 0
    )

    # Get CURRENT remaining from project_scope (same as app)
    remaining_items = project_scope.get("remaining_items", 0)
    remaining_points = project_scope.get("remaining_total_points", 0)

    # Calculate WINDOW-BASED total = current remaining + completed in window (same as app)
    total_items = remaining_items + completed_items
    total_points = remaining_points + completed_points

    # Calculate WINDOW-BASED completion percentages (same as app)
    items_completion_pct = (
        round((completed_items / total_items) * 100, 1) if total_items > 0 else 0
    )
    points_completion_pct = (
        round((completed_points / total_points) * 100, 1) if total_points > 0 else 0
    )

    # Calculate health metrics (same as app's dashboard_comprehensive.py)
    # Health score uses deduction-based formula starting at 100

    # Calculate velocity coefficient of variation (CV)
    velocity_cv = 0
    if not df_windowed.empty and len(df_windowed) >= 2:
        weekly_velocities = df_windowed["completed_items"].tolist()
        mean_vel = (
            sum(weekly_velocities) / len(weekly_velocities)
            if len(weekly_velocities) > 0
            else 0
        )
        if mean_vel > 0:
            variance = sum((x - mean_vel) ** 2 for x in weekly_velocities) / len(
                weekly_velocities
            )
            std_dev = variance**0.5
            velocity_cv = (std_dev / mean_vel) * 100

    # Calculate trend direction from windowed data
    trend_direction = "stable"
    recent_velocity_change = 0
    if not df_windowed.empty and len(df_windowed) >= 6:
        mid_point = len(df_windowed) // 2
        older_half = df_windowed.iloc[:mid_point]
        recent_half = df_windowed.iloc[mid_point:]

        if len(older_half) > 0 and len(recent_half) > 0:
            older_velocity = older_half["completed_items"].sum() / len(older_half)
            recent_velocity = recent_half["completed_items"].sum() / len(recent_half)

            if older_velocity > 0:
                recent_velocity_change = (
                    (recent_velocity - older_velocity) / older_velocity
                ) * 100
                if recent_velocity_change > 10:
                    trend_direction = "improving"
                elif recent_velocity_change < -10:
                    trend_direction = "declining"

    # Calculate scope change rate
    scope_change_rate = 0
    if not df_windowed.empty and "created_items" in df_windowed.columns:
        total_created = df_windowed["created_items"].sum()
        if total_items > 0:
            scope_change_rate = (total_created / total_items) * 100

    # Schedule variance will be calculated after forecast (placeholder for now)
    schedule_variance_days = 0

    # Calculate health score using continuous proportional formula (same as app)
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(
        f"[REPORT HEALTH] velocity_cv={velocity_cv}, schedule_variance_days={schedule_variance_days}, scope_change_rate={scope_change_rate}, trend_direction={trend_direction}, recent_velocity_change={recent_velocity_change}"
    )

    # Velocity consistency (30 points max)
    velocity_score = max(0, 30 * (1 - min(velocity_cv / 50, 1)))
    logger.debug(f"[REPORT HEALTH] velocity_score={velocity_score:.2f}")

    # Schedule performance (25 points max) - will be updated after forecast
    schedule_score = max(0, 25 * (1 - min(schedule_variance_days / 60, 1)))
    logger.debug(f"[REPORT HEALTH] schedule_score={schedule_score:.2f}")

    # Scope stability (20 points max)
    scope_score = max(0, 20 * (1 - min(scope_change_rate / 40, 1)))
    logger.debug(f"[REPORT HEALTH] scope_score={scope_score:.2f}")

    # Quality trends (15 points max)
    if trend_direction == "improving":
        trend_score = 15
    elif trend_direction == "stable":
        trend_score = 10
    else:  # declining
        trend_score = 0
    logger.debug(f"[REPORT HEALTH] trend_score={trend_score}")

    # Recent performance (10 points max)
    if recent_velocity_change >= 0:
        recent_score = 5 + min(5, 5 * (recent_velocity_change / 20))
    else:
        recent_score = max(0, 5 * (1 + recent_velocity_change / 20))
    logger.debug(f"[REPORT HEALTH] recent_score={recent_score:.2f}")

    health_score = int(
        velocity_score + schedule_score + scope_score + trend_score + recent_score
    )
    health_score = max(0, min(100, health_score))
    logger.debug(
        f"[REPORT HEALTH] INITIAL health_score={health_score} (before schedule recalc)"
    )

    # Determine health status (same as app)
    if health_score >= 80:
        health_status = "EXCELLENT"
    elif health_score >= 60:
        health_status = "GOOD"
    elif health_score >= 40:
        health_status = "MODERATE"
    else:
        health_status = "AT RISK"

    # Calculate velocity using EXACT SAME method as app dashboard
    # App uses calculate_velocity_from_dataframe() which returns WEEKLY velocity (items per week)
    # NOT daily average! The app filters to last N data points then calculates weekly velocity
    from data.processing import calculate_velocity_from_dataframe

    data_points_count = settings.get("data_points_count", weeks_count)

    # CRITICAL FIX: Filter by actual date range, not row count
    df_for_velocity = df_windowed
    if (
        data_points_count > 0
        and not df_windowed.empty
        and "date" in df_windowed.columns
    ):
        df_windowed_temp = df_windowed.copy()
        df_windowed_temp["date"] = pd.to_datetime(
            df_windowed_temp["date"], format="mixed", errors="coerce"
        )
        df_windowed_temp = df_windowed_temp.dropna(subset=["date"]).sort_values(
            "date", ascending=True
        )

        latest_date = df_windowed_temp["date"].max()
        cutoff_date = latest_date - timedelta(weeks=data_points_count)
        df_for_velocity = df_windowed_temp[df_windowed_temp["date"] >= cutoff_date]

    # Use the same function as app (returns items PER WEEK, not per day)
    velocity_items = calculate_velocity_from_dataframe(
        df_for_velocity, "completed_items"
    )
    velocity_points = calculate_velocity_from_dataframe(
        df_for_velocity, "completed_points"
    )

    logger.debug(
        f"[REPORT VELOCITY] df_windowed len={len(df_windowed)}, data_points_count={data_points_count}, df_for_velocity len={len(df_for_velocity)}"
    )
    logger.debug(
        f"[REPORT VELOCITY] velocity_items={velocity_items:.2f} items/week, velocity_points={velocity_points:.2f} points/week"
    )

    # Get deadline and milestone from settings
    deadline = settings.get("deadline")
    milestone = settings.get("milestone")
    pert_factor = settings.get("pert_factor", 6)

    # Calculate PERT forecast using EXACT SAME method as app comprehensive dashboard
    # App uses calculate_rates() which returns empirical PERT days (not simplified formula)
    # This is in ui/dashboard_comprehensive.py and data/processing.py calculate_rates()
    from data.processing import compute_weekly_throughput, calculate_rates

    forecast_date = None
    forecast_months = None
    forecast_metric = "story points" if show_points else "items"
    pert_days = None
    forecast_date_items = None
    forecast_date_points = None

    # Compute weekly throughput from windowed statistics (same as app)
    grouped = compute_weekly_throughput(df_windowed)

    logger.info(
        f"[REPORT DATA] df_windowed rows={len(df_windowed)}, grouped weeks={len(grouped)}, "
        f"data_points_count={data_points_count}"
    )

    # Get PERT times using same function as app (empirical best/worst)
    pert_time_items, _, _, pert_time_points, _, _ = calculate_rates(
        grouped,
        remaining_items,  # Use remaining, not total
        remaining_points,
        pert_factor,
        show_points,
    )

    # Use points or items PERT time based on show_points setting (same as app)
    pert_days = (
        pert_time_points if (show_points and pert_time_points) else pert_time_items
    )

    logger.debug(
        f"[REPORT FORECAST] velocity_items={velocity_items:.2f}, velocity_points={velocity_points:.2f}, "
        f"remaining_items={remaining_items}, remaining_points={remaining_points:.2f}, "
        f"pert_factor={pert_factor}, pert_days={pert_days}, pert_time_items={pert_time_items:.2f}, "
        f"pert_time_points={pert_time_points:.2f}, show_points={show_points}"
    )

    # Get last statistics date for forecast starting point
    # CRITICAL: Statistics are weekly-based (Mondays), so we must use the last Monday data point
    # NOT datetime.now() which could be any day of the week
    # This aligns with burndown chart which uses df_calc["date"].iloc[-1]
    last_date = (
        df_windowed["date"].iloc[-1] if not df_windowed.empty else datetime.now()
    )

    if pert_days and pert_days > 0:
        # Start forecast from last statistics date (last Monday), not today
        # This aligns with weekly data aggregation structure
        forecast_date_obj = last_date + timedelta(days=pert_days)
        forecast_date = forecast_date_obj.strftime("%Y-%m-%d")

        # Calculate months to forecast from last date
        forecast_months = round(pert_days / 30.44)  # Average days per month

    # Calculate both items and points forecast dates for display (matching dashboard logic)
    # Only show if pert time is positive (not 0 which means no data or already complete)
    if pert_time_items and pert_time_items > 0:
        forecast_date_items_obj = last_date + timedelta(days=pert_time_items)
        forecast_date_items = forecast_date_items_obj.strftime("%Y-%m-%d")
        logger.info(
            f"[REPORT] Calculated forecast_date_items: {forecast_date_items} (pert_time_items={pert_time_items:.2f} days from {last_date.strftime('%Y-%m-%d')})"
        )

    if pert_time_points and pert_time_points > 0:
        forecast_date_points_obj = last_date + timedelta(days=pert_time_points)
        forecast_date_points = forecast_date_points_obj.strftime("%Y-%m-%d")
        logger.info(
            f"[REPORT] Calculated forecast_date_points: {forecast_date_points} (pert_time_points={pert_time_points:.2f} days from {last_date.strftime('%Y-%m-%d')})"
        )

    logger.info(
        f"[REPORT] Final forecast values: forecast_date={forecast_date}, "
        f"forecast_date_items={forecast_date_items}, forecast_date_points={forecast_date_points}"
    )

    # Calculate months to deadline (from last statistics date, not today)
    deadline_months = None
    days_to_deadline = None
    if deadline:
        try:
            deadline_obj = datetime.strptime(deadline, "%Y-%m-%d")
            # Use last_date for consistency with weekly data structure
            days_to_deadline = (deadline_obj - last_date).days
            deadline_months = round(days_to_deadline / 30.44)
        except ValueError:
            pass

    # Recalculate schedule variance now that forecast is complete
    if pert_days and days_to_deadline:
        schedule_variance_days = abs(pert_days - days_to_deadline)
        logger.debug(
            f"[REPORT HEALTH] RECALC: schedule_variance_days={schedule_variance_days} (pert_days={pert_days}, days_to_deadline={days_to_deadline})"
        )

        # Recalculate health score with schedule variance (same as app)
        # Velocity consistency (30 points max)
        velocity_score = max(0, 30 * (1 - min(velocity_cv / 50, 1)))

        # Schedule performance (25 points max)
        schedule_score = max(0, 25 * (1 - min(schedule_variance_days / 60, 1)))
        logger.debug(f"[REPORT HEALTH] RECALC: schedule_score={schedule_score:.2f}")

        # Scope stability (20 points max)
        scope_score = max(0, 20 * (1 - min(scope_change_rate / 40, 1)))

        # Quality trends (15 points max)
        if trend_direction == "improving":
            trend_score = 15
        elif trend_direction == "stable":
            trend_score = 10
        else:  # declining
            trend_score = 0

        # Recent performance (10 points max)
        if recent_velocity_change >= 0:
            recent_score = 5 + min(5, 5 * (recent_velocity_change / 20))
        else:
            recent_score = max(0, 5 * (1 + recent_velocity_change / 20))

        health_score = int(
            velocity_score + schedule_score + scope_score + trend_score + recent_score
        )
        health_score = max(0, min(100, health_score))
        logger.debug(
            f"[REPORT HEALTH] FINAL health_score={health_score} (after schedule recalc)"
        )

        # Update health status
        if health_score >= 80:
            health_status = "EXCELLENT"
        elif health_score >= 60:
            health_status = "GOOD"
        elif health_score >= 40:
            health_status = "MODERATE"
        else:
            health_status = "AT RISK"

    return {
        "has_data": True,
        "completed_items": completed_items,
        "completed_points": completed_points,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
        "total_items": total_items,
        "total_points": total_points,
        "items_completion_pct": items_completion_pct,
        "points_completion_pct": points_completion_pct,
        "health_score": health_score,
        "health_status": health_status,
        "deadline": deadline,
        "deadline_months": deadline_months,
        "milestone": milestone,
        "forecast_date": forecast_date,
        "forecast_date_items": forecast_date_items,
        "forecast_date_points": forecast_date_points,
        "forecast_months": forecast_months,
        "forecast_metric": forecast_metric,
        "velocity_items": velocity_items,
        "velocity_points": velocity_points,
        "weeks_count": weeks_count,
        "pert_time_items_weeks": (pert_time_items / 7.0) if pert_time_items else 0,
        "pert_time_points_weeks": (pert_time_points / 7.0) if pert_time_points else 0,
        "show_points": show_points,  # Pass show_points flag for template
    }


def _calculate_burndown_metrics(
    statistics: List[Dict], project_scope: Dict, weeks_count: int
) -> Dict[str, Any]:
    """
    Calculate burndown chart metrics and projections.

    Args:
        statistics: Filtered statistics for the time period
        project_scope: Current project scope
        weeks_count: Actual number of weeks with data

    Returns:
        Dictionary with burndown metrics and weekly data
    """
    from data.processing import calculate_velocity_from_dataframe

    if not statistics:
        return {"has_data": False, "weeks_count": weeks_count}

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore

    # Calculate velocity using proper week counting
    velocity_items = calculate_velocity_from_dataframe(df, "completed_items")
    velocity_points = calculate_velocity_from_dataframe(df, "completed_points")

    # Get current remaining from project scope
    remaining_items = project_scope.get("remaining_items", 0)
    remaining_points = project_scope.get("remaining_total_points", 0)

    # Calculate weeks to completion
    weeks_remaining_items = (
        round(remaining_items / velocity_items, 1)
        if velocity_items > 0
        else float("inf")
    )
    weeks_remaining_points = (
        round(remaining_points / velocity_points, 1)
        if velocity_points > 0
        else float("inf")
    )

    # Calculate weekly breakdown for chart
    weekly_data = _calculate_weekly_breakdown(statistics)

    # Calculate historical remaining work for burndown chart
    historical_data = _calculate_historical_burndown(statistics, project_scope)

    return {
        "has_data": True,
        "velocity_items": velocity_items,
        "velocity_points": velocity_points,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
        "weeks_remaining_items": weeks_remaining_items,
        "weeks_remaining_points": weeks_remaining_points,
        "weekly_data": weekly_data,
        "historical_data": historical_data,
        "weeks_count": weeks_count,
    }


def _calculate_bug_metrics(
    jira_issues: List[Dict],
    statistics: List[Dict],
    settings: Dict,
    weeks_count: int,
) -> Dict[str, Any]:
    """
    Calculate bug analysis metrics using proper bug processing functions.

    Args:
        jira_issues: Raw JIRA issues
        statistics: Filtered statistics
        settings: App settings with bug type mappings
        weeks_count: Number of weeks in period

    Returns:
        Dictionary with bug analysis metrics
    """
    from data.bug_processing import (
        calculate_bug_metrics_summary,
        forecast_bug_resolution,
        calculate_bug_statistics,
        filter_bug_issues,
    )

    if not jira_issues:
        return {"has_data": False}

    try:
        # Get bug type mappings
        bug_types = settings.get("bug_types", {})

        # Calculate date range
        date_to = datetime.now()
        date_from = (
            date_to - timedelta(weeks=weeks_count)
            if weeks_count > 0
            else date_to - timedelta(weeks=12)
        )

        # Filter bugs WITHOUT date filter for current state metrics (open bugs count)
        all_bug_issues = filter_bug_issues(
            jira_issues,
            bug_type_mappings=bug_types,
            date_from=None,  # No date filter for current state
            date_to=None,
        )

        # Filter bugs WITH date filter for historical metrics (resolution rate, trends)
        timeline_filtered_bugs = filter_bug_issues(
            jira_issues,
            bug_type_mappings=bug_types,
            date_from=date_from,
            date_to=date_to,
        )

        if not all_bug_issues and not timeline_filtered_bugs:
            return {"has_data": False}

        # Calculate weekly bug statistics using timeline-filtered bugs
        points_field = settings.get("points_field", "customfield_10016")
        weekly_stats = []
        try:
            weekly_stats = calculate_bug_statistics(
                timeline_filtered_bugs,
                date_from,
                date_to,
                story_points_field=points_field,
            )
        except Exception as e:
            logger.warning(f"Failed to calculate bug statistics: {e}")

        # Calculate summary metrics using BOTH bug lists (like the app does)
        bug_summary = calculate_bug_metrics_summary(
            all_bug_issues=all_bug_issues,
            timeline_filtered_bugs=timeline_filtered_bugs,
            weekly_stats=weekly_stats,
            date_from=date_from,
            date_to=date_to,
            all_project_issues=jira_issues,  # Pass all issues for capacity calculation
        )

        # Calculate bug resolution forecast
        forecast = None
        open_bugs = bug_summary.get("open_bugs", 0)
        if open_bugs > 0 and weekly_stats:
            try:
                # Use min(8, weeks_count) to match app behavior but respect shorter periods
                # 8 weeks is optimal for trend analysis, but use less if data window is smaller
                forecast_weeks = min(8, weeks_count)
                forecast = forecast_bug_resolution(
                    open_bugs=open_bugs,
                    weekly_stats=weekly_stats,
                    use_last_n_weeks=forecast_weeks,
                )
            except Exception as e:
                logger.warning(f"Failed to calculate bug forecast: {e}")

        # Calculate bug investment percentage from weekly stats
        total_completed = sum(s.get("completed_items", 0) for s in statistics)
        total_bugs_resolved = sum(s.get("bugs_resolved", 0) for s in weekly_stats)
        bug_investment_pct = (
            round((total_bugs_resolved / total_completed) * 100, 1)
            if total_completed > 0
            else 0
        )

        # Convert resolution rate from decimal to percentage
        resolution_rate = bug_summary.get("resolution_rate", 0)
        resolution_rate_pct = round(resolution_rate * 100, 1)

        # Round average age
        avg_age_days = round(bug_summary.get("avg_age_days", 0), 1)

        # Count closed bugs from timeline-filtered bugs
        closed_bugs = bug_summary.get("closed_bugs", 0)

        return {
            "has_data": True,
            "open_bugs": bug_summary.get("open_bugs", 0),
            "total_bugs": bug_summary.get("total_bugs", 0),
            "closed_bugs": closed_bugs,
            "resolution_rate": resolution_rate_pct,
            "avg_age_days": avg_age_days,
            "forecast_weeks": forecast.get("most_likely_weeks") if forecast else None,
            "forecast_date": forecast.get("most_likely_date") if forecast else None,
            "avg_closure_rate": forecast.get("avg_closure_rate") if forecast else None,
            "weeks_analyzed": forecast.get("weeks_analyzed") if forecast else None,
            "bug_investment_pct": bug_investment_pct,
            "weekly_stats": weekly_stats,
            "date_from": date_from.strftime("%b %d, %Y"),
            "date_to": date_to.strftime("%b %d, %Y"),
        }
    except Exception as e:
        logger.error(f"Error calculating bug metrics: {e}", exc_info=True)
        return {"has_data": False, "error": str(e)}


def _calculate_scope_metrics(
    statistics: List[Dict], project_scope: Dict, weeks_count: int
) -> Dict[str, Any]:
    """
    Calculate scope change metrics comparing window start vs current.

    Args:
        statistics: Filtered statistics for the time period
        project_scope: Current project scope (remaining items/points)
        weeks_count: Number of weeks in period

    Returns:
        Dictionary with scope metrics including creation/completion ratios
    """
    if not statistics or len(statistics) < 2:
        return {"has_data": False}

    df = pd.DataFrame(statistics)

    # Calculate creation/completion totals for the period
    total_created_items = int(df["created_items"].sum())
    total_created_points = round(df["created_points"].sum(), 1)
    total_completed_items = int(df["completed_items"].sum())
    total_completed_points = round(df["completed_points"].sum(), 1)

    # Current scope from project_scope (remaining work)
    current_items = project_scope.get("remaining_items", 0)
    current_points = round(project_scope.get("remaining_total_points", 0), 1)

    # Calculate initial scope at window start
    # Work backwards from current: Initial = Current + Completed - Created
    # This accounts for both work completed and new work added during the period
    initial_items = current_items + total_completed_items - total_created_items
    initial_points = round(
        current_points + total_completed_points - total_created_points, 1
    )

    logger.debug(
        f"[SCOPE BASELINE] Current: {current_items} items, {current_points:.2f} points"
    )
    logger.debug(
        f"[SCOPE BASELINE] Total completed in period: {total_completed_items} items, {total_completed_points:.2f} points"
    )
    logger.debug(
        f"[SCOPE BASELINE] Total created in period: {total_created_items} items, {total_created_points:.2f} points"
    )
    logger.debug(
        f"[SCOPE BASELINE] Calculated initial: {initial_items} items, {initial_points:.2f} points"
    )

    # Calculate net change: Current - Initial = (Current) - (Current + Completed - Created) = Created - Completed
    items_change = current_items - initial_items
    points_change = round(current_points - initial_points, 1)

    # Calculate creation/completion ratios
    items_ratio = (
        round(total_created_items / total_completed_items, 2)
        if total_completed_items > 0
        else 0
    )
    points_ratio = (
        round(total_created_points / total_completed_points, 2)
        if total_completed_points > 0
        else 0
    )

    return {
        "has_data": True,
        "initial_items": initial_items,
        "initial_points": round(initial_points, 1),
        "final_items": current_items,
        "final_points": round(current_points, 1),
        "items_change": items_change,
        "points_change": round(points_change, 1),
        "created_items": total_created_items,
        "created_points": total_created_points,
        "completed_items": total_completed_items,
        "completed_points": total_completed_points,
        "items_ratio": items_ratio,
        "points_ratio": points_ratio,
        "weeks_count": weeks_count,
    }


def _calculate_flow_metrics(
    snapshots: Dict[str, Dict], weeks_count: int
) -> Dict[str, Any]:
    """
    Load Flow metrics from snapshots (matches app implementation).

    Uses the same snapshot reading logic as callbacks/dora_flow_metrics.py
    to ensure identical calculations with aggregation across the period.

    Args:
        snapshots: Filtered weekly snapshots (NOT USED - we read directly from cache)
        weeks_count: Number of weeks to load from snapshots

    Returns:
        Dictionary with Flow metrics matching app display
    """
    from data.time_period_calculator import get_iso_week, format_year_week
    from data.metrics_snapshots import get_metric_snapshot, get_available_weeks

    logger.info(f"Loading Flow metrics from snapshots for {weeks_count} weeks")

    # Generate week labels (same as app)
    weeks = []
    current_date = datetime.now()
    for i in range(weeks_count):
        year, week = get_iso_week(current_date)
        week_label = format_year_week(year, week)
        weeks.append(week_label)
        current_date = current_date - timedelta(days=7)

    week_labels = list(reversed(weeks))  # Oldest to newest
    current_week_label = week_labels[-1] if week_labels else ""

    # Check if any data exists
    available_weeks = get_available_weeks()
    has_any_data = any(week in available_weeks for week in week_labels)

    if not has_any_data:
        logger.warning("No Flow metrics snapshots found")
        return {"has_data": False, "weeks_count": weeks_count}

    # Load weekly values from snapshots (same as app)
    from data.metrics_snapshots import get_metric_weekly_values

    # Note: flow_load (WIP) is loaded separately as point-in-time snapshot below
    flow_time_values = get_metric_weekly_values(week_labels, "flow_time", "median_days")
    flow_efficiency_values = get_metric_weekly_values(
        week_labels, "flow_efficiency", "overall_pct"
    )
    velocity_values = get_metric_weekly_values(
        week_labels, "flow_velocity", "completed_count"
    )

    # AGGREGATE metrics across period (same as app)
    # Flow Velocity: Average items/week
    avg_velocity = (
        round(sum(velocity_values) / len(velocity_values), 1) if velocity_values else 0
    )

    # Flow Time: Median of weekly medians (exclude zeros = weeks with no completions)
    non_zero_flow_times = [v for v in flow_time_values if v > 0]
    if non_zero_flow_times:
        sorted_times = sorted(non_zero_flow_times)
        mid = len(sorted_times) // 2
        median_flow_time = (
            sorted_times[mid]
            if len(sorted_times) % 2 == 1
            else (sorted_times[mid - 1] + sorted_times[mid]) / 2
        )
    else:
        median_flow_time = 0

    # Flow Efficiency: Average efficiency across period (exclude zeros)
    non_zero_efficiency = [v for v in flow_efficiency_values if v > 0]
    avg_efficiency = (
        round(sum(non_zero_efficiency) / len(non_zero_efficiency), 1)
        if non_zero_efficiency
        else 0
    )

    # Flow Load (WIP): Current week snapshot (point-in-time metric)
    flow_load_snapshot = get_metric_snapshot(current_week_label, "flow_load")
    if not flow_load_snapshot and available_weeks:
        # Find most recent week with data
        for week in week_labels[::-1]:  # Start from most recent
            flow_load_snapshot = get_metric_snapshot(week, "flow_load")
            if flow_load_snapshot:
                logger.info(
                    f"Using WIP from {week} (current {current_week_label} not available)"
                )
                break
    wip_count = flow_load_snapshot.get("wip_count", 0) if flow_load_snapshot else 0

    # Collect distribution data across ALL weeks for aggregated totals
    total_feature = 0
    total_defect = 0
    total_tech_debt = 0
    total_risk = 0
    total_completed = 0
    distribution_history = []

    for week in week_labels:
        week_snapshot = get_metric_snapshot(week, "flow_velocity")
        if week_snapshot:
            week_dist = week_snapshot.get("distribution", {})
            week_feature = week_dist.get("feature", 0)
            week_defect = week_dist.get("defect", 0)
            week_tech_debt = week_dist.get("tech_debt", 0)
            week_risk = week_dist.get("risk", 0)
            week_total = week_snapshot.get("completed_count", 0)

            # Accumulate totals
            total_feature += week_feature
            total_defect += week_defect
            total_tech_debt += week_tech_debt
            total_risk += week_risk
            total_completed += week_total

            distribution_history.append(
                {
                    "week": week,
                    "feature": week_feature,
                    "defect": week_defect,
                    "tech_debt": week_tech_debt,
                    "risk": week_risk,
                    "total": week_total,
                }
            )
        else:
            distribution_history.append(
                {
                    "week": week,
                    "feature": 0,
                    "defect": 0,
                    "tech_debt": 0,
                    "risk": 0,
                    "total": 0,
                }
            )

    logger.info(
        f"Flow metrics loaded: Velocity={avg_velocity:.1f} items/week, "
        f"Flow Time={median_flow_time:.1f}d, Efficiency={avg_efficiency:.1f}%, WIP={wip_count}"
    )

    return {
        "has_data": True,
        "velocity": avg_velocity,  # Average items/week
        "flow_time": round(median_flow_time, 1),  # Median days
        "efficiency": avg_efficiency,  # Average percentage
        "wip": wip_count,  # Current WIP count
        "work_distribution": {
            "feature": total_feature,
            "defect": total_defect,
            "tech_debt": total_tech_debt,
            "risk": total_risk,
            "total": total_completed,
        },
        "distribution_history": distribution_history,
        "weeks_count": weeks_count,
    }


def _calculate_dora_metrics(profile_id: str, weeks_count: int) -> Dict[str, Any]:
    """
    Load DORA metrics from cache (matches app implementation).

    Uses the same load_dora_metrics_from_cache() function as the app's
    callbacks/dora_flow_metrics.py to ensure identical calculations.

    Args:
        profile_id: Active profile ID for cache access (not currently used by load function)
        weeks_count: Number of weeks to load from cache

    Returns:
        Dictionary with DORA metrics matching app display
    """
    from data.dora_metrics_calculator import load_dora_metrics_from_cache

    logger.info(f"Loading DORA metrics from cache for {weeks_count} weeks")

    # Load from cache using the same function as the app
    cached_metrics = load_dora_metrics_from_cache(n_weeks=weeks_count)

    if not cached_metrics:
        logger.warning("No DORA metrics found in cache")
        return {"has_data": False, "weeks_count": weeks_count}

    # Extract values matching app structure
    # Deployment Frequency: Use release count (unique fixVersions) as primary
    deploy_data = cached_metrics.get("deployment_frequency", {})
    deployment_freq = deploy_data.get("release_value", 0)  # Primary: unique releases
    deployment_freq_tasks = deploy_data.get("value", 0)  # Secondary: task count

    # Lead Time: value is already in days, value_hours is in hours
    lead_time_data = cached_metrics.get("lead_time_for_changes", {})
    lead_time_days = lead_time_data.get(
        "value"
    )  # Already in days (median of weekly medians)
    lead_time_hours = lead_time_data.get(
        "value_hours"
    )  # In hours for secondary display

    # Change Failure Rate: Percentage
    cfr_data = cached_metrics.get("change_failure_rate", {})
    change_failure_rate = cfr_data.get("value", 0)  # Percentage

    # MTTR: value is already in hours (median of weekly medians), convert to days
    mttr_data = cached_metrics.get("mean_time_to_recovery", {})
    mttr_hours = mttr_data.get("value")  # Already in hours (median of weekly medians)
    mttr_days = round(mttr_hours / 24, 1) if mttr_hours else None

    # Get weekly values for trend analysis
    weekly_labels = deploy_data.get("weekly_labels", [])

    logger.info(
        f"DORA metrics loaded: DF={deployment_freq} releases/week, "
        f"LT={lead_time_days}d, CFR={change_failure_rate}%, MTTR={mttr_days}d"
    )

    return {
        "has_data": True,
        "deployment_frequency": deployment_freq,  # Releases per week
        "deployment_frequency_tasks": deployment_freq_tasks,  # Tasks per week
        "lead_time_days": lead_time_days,  # Days (None if no data)
        "lead_time_hours": lead_time_hours,  # Hours (None if no data)
        "change_failure_rate": change_failure_rate,  # Percentage
        "mttr_days": mttr_days,  # Days (None if no data)
        "mttr_hours": mttr_hours,  # Hours (None if no data)
        "weekly_labels": weekly_labels,  # For charts
        "weeks_count": weeks_count,
        # Include full cached data for detailed reporting
        "_raw": cached_metrics,
    }


# ============================================================================
# Helper Functions
# ============================================================================


def _calculate_weekly_breakdown(statistics: List[Dict]) -> List[Dict]:
    """
    Calculate weekly breakdown of created/completed items and points.

    Args:
        statistics: List of daily statistics

    Returns:
        List of weekly aggregates with ISO week labels
    """
    if not statistics:
        return []

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore
    df["week"] = df["date"].dt.strftime("%Y-W%U")  # type: ignore

    # Group by week and aggregate
    weekly = (
        df.groupby("week")
        .agg(
            {
                "created_items": "sum",
                "completed_items": "sum",
                "created_points": "sum",
                "completed_points": "sum",
            }
        )
        .reset_index()
    )

    # Convert to list of dicts with formatted week labels
    weekly_data = []
    for _, row in weekly.iterrows():
        weekly_data.append(
            {
                "date": row["week"],
                "created_items": int(row["created_items"]),
                "completed_items": int(row["completed_items"]),
                "created_points": int(row["created_points"]),
                "completed_points": int(row["completed_points"]),
            }
        )

    return weekly_data


def _calculate_budget_metrics(
    profile_id: str, query_id: str, weeks_count: int, velocity_points: float = 0.0
) -> Dict[str, Any]:
    """
    Calculate budget metrics for report using proper budget calculator functions.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        weeks_count: Number of weeks in analysis period
        velocity_points: Story points velocity for cost_per_point calculation

    Returns:
        Dictionary with budget metrics and weekly tracking data including cost breakdown
    """
    from data.persistence.factory import get_backend
    from data.budget_calculator import (
        calculate_budget_consumed,
        calculate_runway,
        calculate_cost_breakdown_by_type,
    )
    from data.iso_week_bucketing import get_week_label
    from datetime import datetime

    logger.info(f"Calculating budget metrics for {profile_id}/{query_id}")

    backend = get_backend()
    budget_settings = backend.get_budget_settings(profile_id)

    if not budget_settings:
        logger.info("No budget configured for profile")
        return {"has_data": False}

    # Get budget revisions for history
    revisions = backend.get_budget_revisions(profile_id) or []

    # Calculate latest budget state
    time_allocated = budget_settings.get("time_allocated_weeks", 0)
    cost_per_week = budget_settings.get("team_cost_per_week_eur", 0.0)
    budget_total = budget_settings.get("budget_total_eur", 0.0)
    currency = budget_settings.get("currency_symbol", "€")

    # Get current week for calculations
    current_week = get_week_label(datetime.now())

    # Use proper budget calculator functions (same as app)
    try:
        # Calculate consumption using actual budget calculator
        consumed_eur, budget_total_calc, consumed_pct = calculate_budget_consumed(
            profile_id, query_id, current_week
        )

        # Calculate runway using actual budget calculator
        runway_weeks, burn_rate = calculate_runway(
            profile_id, query_id, current_week, data_points_count=weeks_count
        )

        # Calculate cost breakdown by work type
        cost_breakdown = calculate_cost_breakdown_by_type(
            profile_id, query_id, current_week
        )

        # Get cost per item/point from velocity
        from data.budget_calculator import _get_velocity

        velocity_items = _get_velocity(profile_id, query_id, current_week)
        cost_per_item = cost_per_week / velocity_items if velocity_items > 0 else 0
        cost_per_point = cost_per_week / velocity_points if velocity_points > 0 else 0

        # Use 999999 as sentinel for infinity (Jinja2 compatible)
        if runway_weeks == float("inf"):
            runway_weeks = 999999

        logger.info(
            f"Budget metrics calculated: consumed={consumed_pct:.1f}%, "
            f"runway={runway_weeks:.1f}w, burn_rate={burn_rate:.2f}"
        )

    except Exception as e:
        logger.error(f"Failed to calculate budget metrics: {e}", exc_info=True)
        # Fallback to basic calculations
        consumed_eur = 0.0
        consumed_pct = 0.0
        burn_rate = cost_per_week
        runway_weeks = 0
        cost_breakdown = {}
        cost_per_item = 0.0
        cost_per_point = 0.0

    return {
        "has_data": True,
        "time_allocated_weeks": time_allocated,
        "cost_per_week": cost_per_week,
        "budget_total": budget_total,
        "currency_symbol": currency,
        "consumed_amount": consumed_eur,
        "consumed_percentage": consumed_pct,
        "remaining_amount": budget_total - consumed_eur,
        "runway_weeks": runway_weeks,
        "revision_count": len(revisions),
        "burn_rate": burn_rate,
        "cost_per_item": cost_per_item,
        "cost_per_point": cost_per_point,
        "cost_breakdown": cost_breakdown,
    }


def _calculate_historical_burndown(
    statistics: List[Dict], project_scope: Dict
) -> Dict[str, List]:
    """Calculate historical remaining work for burndown chart."""
    if not statistics:
        return {"dates": [], "remaining_items": [], "remaining_points": []}

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.sort_values("date")

    current_remaining_items = project_scope.get("remaining_items", 0)
    current_remaining_points = project_scope.get("remaining_total_points", 0)

    df["cumulative_completed_items"] = df["completed_items"][::-1].cumsum()[::-1]
    df["cumulative_completed_points"] = df["completed_points"][::-1].cumsum()[::-1]

    df["historical_remaining_items"] = (
        current_remaining_items + df["cumulative_completed_items"]
    )
    df["historical_remaining_points"] = (
        current_remaining_points + df["cumulative_completed_points"]
    )

    # Format dates and convert to lists
    dates = [d.strftime("%Y-%m-%d") for d in df["date"]]
    remaining_items = [round(x) for x in df["historical_remaining_items"]]
    remaining_points = [round(x) for x in df["historical_remaining_points"]]

    return {
        "dates": dates,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
    }


def _generate_chart_scripts(metrics: Dict[str, Any], sections: List[str]) -> List[str]:
    """
    Generate Chart.js initialization scripts for visualizations.

    Args:
        metrics: Calculated metrics dictionary
        sections: List of sections to generate charts for

    Returns:
        List of JavaScript code strings
    """
    scripts = []

    # Burndown chart with milestone/forecast/deadline
    if "burndown" in sections and metrics.get("burndown", {}).get("has_data"):
        dashboard_metrics = metrics.get("dashboard", {})
        scripts.append(
            _generate_burndown_chart(
                metrics["burndown"],
                dashboard_metrics.get("milestone"),
                dashboard_metrics.get("forecast_date"),
                dashboard_metrics.get("deadline"),
                dashboard_metrics.get("show_points", False),
            )
        )

    # Weekly breakdown chart (for burndown section)
    if "burndown" in sections and metrics.get("burndown", {}).get("weekly_data"):
        scripts.append(
            _generate_weekly_breakdown_chart(
                metrics["burndown"]["weekly_data"],
                metrics.get("dashboard", {}).get("show_points", False),
            )
        )

    # Scope changes chart
    if "burndown" in sections and metrics.get("scope", {}).get("has_data"):
        scripts.append(_generate_scope_changes_chart(metrics))

    # Bug trends chart
    if (
        "burndown" in sections
        and metrics.get("bug_analysis", {}).get("has_data")
        and metrics["bug_analysis"].get("weekly_stats")
    ):
        scripts.append(
            _generate_bug_trends_chart(metrics["bug_analysis"]["weekly_stats"])
        )

    # Work distribution chart (for flow section)
    if "flow" in sections and metrics.get("flow", {}).get("has_data"):
        scripts.append(_generate_work_distribution_chart(metrics["flow"]))

    return scripts


def _generate_burndown_chart(
    burndown_metrics: Dict,
    milestone: str,
    forecast_date: str,
    deadline: str,
    show_points: bool = False,
) -> str:
    """Generate Chart.js script for burndown chart with milestone/forecast/deadline lines."""
    historical = burndown_metrics.get("historical_data", {})
    dates = historical.get("dates", [])
    dates_js = json.dumps(dates)
    items = historical.get("remaining_items", [])
    points = historical.get("remaining_points", [])

    # Build annotations for milestone, forecast, deadline with named keys
    annotations = {}

    if milestone:
        annotations["milestone"] = f"""{{
            type: 'line',
            xMin: '{milestone}',
            xMax: '{milestone}',
            borderColor: '#ffc107',
            borderWidth: 3,
            borderDash: [10, 5],
            label: {{
                display: true,
                content: 'Milestone',
                position: 'start',
                yAdjust: -60,
                backgroundColor: '#ffc107',
                color: '#000'
            }}
        }}"""

    if forecast_date:
        annotations["forecast"] = f"""{{
            type: 'line',
            xMin: '{forecast_date}',
            xMax: '{forecast_date}',
            borderColor: '#198754',
            borderWidth: 2,
            borderDash: [5, 5],
            label: {{
                display: true,
                content: 'Forecast',
                position: 'start',
                yAdjust: -30,
                backgroundColor: '#198754',
                color: '#fff'
            }}
        }}"""

    if deadline:
        annotations["deadline"] = f"""{{
            type: 'line',
            xMin: '{deadline}',
            xMax: '{deadline}',
            borderColor: '#dc3545',
            borderWidth: 2,
            label: {{
                display: true,
                content: 'Deadline',
                position: 'start',
                yAdjust: 0,
                backgroundColor: '#dc3545',
                color: '#fff'
            }}
        }}"""

    # Format as key: value pairs
    annotations_js = ",\n                ".join(
        [f"{k}: {v}" for k, v in annotations.items()]
    )

    # Build datasets conditionally
    datasets = [
        {
            "label": "Remaining Items",
            "data": items,
            "borderColor": "#0d6efd",
            "backgroundColor": "rgba(13, 110, 253, 0.1)",
            "tension": 0.4,
            "borderWidth": 2,
            "yAxisID": "y",
        }
    ]

    if show_points:
        datasets.append(
            {
                "label": "Remaining Points",
                "data": points,
                "borderColor": "#fd7e14",
                "backgroundColor": "rgba(253, 126, 20, 0.1)",
                "tension": 0.4,
                "borderWidth": 2,
                "yAxisID": "y1",
            }
        )

    datasets_js = json.dumps(datasets)

    # Build scales conditionally
    scales_config = {
        "x": {
            "grid": {"display": False},
            "ticks": {"maxRotation": 45, "minRotation": 45},
        },
        "y": {
            "type": "linear",
            "display": True,
            "position": "left",
            "title": {"display": True, "text": "Items"},
            "grid": {"color": "#e9ecef"},
        },
    }

    if show_points:
        scales_config["y1"] = {
            "type": "linear",
            "display": True,
            "position": "right",
            "title": {"display": True, "text": "Points"},
            "grid": {"drawOnChartArea": False},
        }

    scales_js = json.dumps(scales_config)

    return f"""
    (function() {{
        const ctx = document.getElementById('burndownChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {dates_js},
                    datasets: {datasets_js}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    scales: {scales_js},
                    plugins: {{
                        legend: {{ display: true, position: 'top' }},
                        annotation: {{
                            annotations: {{
                                {annotations_js}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def _generate_weekly_breakdown_chart(
    weekly_data: List[Dict], show_points: bool = False
) -> str:
    """Generate Chart.js script for weekly breakdown chart."""
    dates = [w["date"] for w in weekly_data]
    dates_js = json.dumps(dates)
    items_created = [w["created_items"] for w in weekly_data]
    items_closed = [-w["completed_items"] for w in weekly_data]
    points_created = [w["created_points"] for w in weekly_data]
    points_closed = [-w["completed_points"] for w in weekly_data]

    # Build datasets conditionally
    datasets = [
        {
            "label": "Items Created",
            "data": items_created,
            "backgroundColor": "#0d6efd",
            "stack": "items",
        },
        {
            "label": "Items Closed",
            "data": items_closed,
            "backgroundColor": "#0d6efd",
            "stack": "items",
        },
    ]

    if show_points:
        datasets.extend(
            [
                {
                    "label": "Points Created",
                    "data": points_created,
                    "backgroundColor": "#fd7e14",
                    "stack": "points",
                },
                {
                    "label": "Points Closed",
                    "data": points_closed,
                    "backgroundColor": "#fd7e14",
                    "stack": "points",
                },
            ]
        )

    datasets_js = json.dumps(datasets)

    return f"""
    (function() {{
        const ctx = document.getElementById('weeklyBreakdownChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {dates_js},
                    datasets: {datasets_js}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ stacked: true, grid: {{ display: false }} }},
                        y: {{ 
                            stacked: true,
                            grid: {{ color: '#e9ecef' }},
                            ticks: {{
                                callback: function(value) {{
                                    return Math.abs(value);
                                }}
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: true, position: 'bottom' }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ' + Math.abs(context.parsed.y);
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def _generate_scope_changes_chart(metrics: Dict[str, Any]) -> str:
    """Generate Chart.js script for scope changes over time chart."""
    statistics = metrics.get("statistics", [])
    if not statistics:
        return ""

    df = pd.DataFrame(statistics)

    # Convert date to datetime and generate week labels
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore
    df["year"] = df["date"].dt.isocalendar().year  # type: ignore
    # Use vectorized string formatting to avoid DataFrame return issues
    df["week_label"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    # Group by week to aggregate daily data
    weekly_df = (
        df.groupby("week_label")
        .agg({"created_items": "sum", "completed_items": "sum"})
        .reset_index()
    )

    weeks_js = json.dumps(weekly_df["week_label"].tolist())
    created_items_js = json.dumps(weekly_df["created_items"].tolist())
    completed_items_js = json.dumps(weekly_df["completed_items"].tolist())

    return f"""
    (function() {{
        const ctx = document.getElementById('scopeChangesChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {weeks_js},
                    datasets: [
                        {{
                            label: 'Items Created',
                            data: {created_items_js},
                            backgroundColor: 'rgba(220, 53, 69, 0.6)',
                            borderColor: 'rgba(220, 53, 69, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Items Completed',
                            data: {completed_items_js},
                            backgroundColor: 'rgba(25, 135, 84, 0.6)',
                            borderColor: 'rgba(25, 135, 84, 1)',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    scales: {{
                        x: {{ 
                            grid: {{ display: false }},
                            ticks: {{ maxRotation: 45, minRotation: 45 }}
                        }},
                        y: {{ 
                            beginAtZero: true,
                            grid: {{ color: '#e9ecef' }},
                            title: {{ display: true, text: 'Items' }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: true, position: 'bottom' }},
                        tooltip: {{
                            callbacks: {{
                                afterBody: function(context) {{
                                    const idx = context[0].dataIndex;
                                    const created = context[0].chart.data.datasets[0].data[idx];
                                    const completed = context[0].chart.data.datasets[1].data[idx];
                                    const net = created - completed;
                                    return 'Net Change: ' + (net > 0 ? '+' : '') + net + ' items';
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def _generate_bug_trends_chart(weekly_stats: List[Dict]) -> str:
    """Generate Chart.js script for bug trends chart showing only items with warning backgrounds."""
    weeks_js = json.dumps(
        [s.get("week_start_date", s.get("week", ""))[:10] for s in weekly_stats]
    )
    bugs_created_js = json.dumps([s.get("bugs_created", 0) for s in weekly_stats])
    bugs_resolved_js = json.dumps([s.get("bugs_resolved", 0) for s in weekly_stats])

    # Calculate warning periods (3+ consecutive weeks where created > resolved)
    annotations = {}
    consecutive_negative_weeks = 0
    warning_start_idx = None

    for idx, stat in enumerate(weekly_stats):
        if stat.get("bugs_created", 0) > stat.get("bugs_resolved", 0):
            consecutive_negative_weeks += 1
            if consecutive_negative_weeks == 1:
                warning_start_idx = idx
        else:
            # Check if we had 3+ consecutive negative weeks
            if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
                # Get week labels for this warning period
                start_week = weekly_stats[warning_start_idx].get(
                    "week_start_date", weekly_stats[warning_start_idx].get("week", "")
                )[:10]
                end_week = weekly_stats[idx - 1].get(
                    "week_start_date", weekly_stats[idx - 1].get("week", "")
                )[:10]
                # Add background box annotation
                annotations[f"warning_{warning_start_idx}"] = f"""{{ 
                    type: 'box',
                    xMin: '{start_week}',
                    xMax: '{end_week}',
                    backgroundColor: 'rgba(255, 165, 0, 0.15)',
                    borderWidth: 0
                }}"""
            consecutive_negative_weeks = 0
            warning_start_idx = None

    # Check final period if it ends with warnings
    if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
        start_week = weekly_stats[warning_start_idx].get(
            "week_start_date", weekly_stats[warning_start_idx].get("week", "")
        )[:10]
        end_week = weekly_stats[-1].get(
            "week_start_date", weekly_stats[-1].get("week", "")
        )[:10]
        annotations[f"warning_{warning_start_idx}"] = f"""{{ 
            type: 'box',
            xMin: '{start_week}',
            xMax: '{end_week}',
            backgroundColor: 'rgba(255, 165, 0, 0.15)',
            borderWidth: 0
        }}"""

    # Build annotations JavaScript with key-value pairs
    if annotations:
        annotations_js = ",\n                                ".join(
            [f"{key}: {value}" for key, value in annotations.items()]
        )
    else:
        annotations_js = ""

    return f"""
    (function() {{
        const ctx = document.getElementById('bugTrendsChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {weeks_js},
                    datasets: [
                        {{
                            label: 'Bugs Created',
                            data: {bugs_created_js},
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            tension: 0.4,
                            borderWidth: 2,
                            fill: false
                        }},
                        {{
                            label: 'Bugs Closed',
                            data: {bugs_resolved_js},
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            tension: 0.4,
                            borderWidth: 2,
                            fill: false
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ grid: {{ display: false }} }},
                        y: {{
                            beginAtZero: true,
                            grid: {{ color: '#e9ecef' }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: true, position: 'bottom' }},
                        annotation: {{
                            annotations: {{
                                {annotations_js}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def _generate_bug_investment_chart(bug_pct: float) -> str:
    """Generate Chart.js script for bug investment pie chart."""
    feature_pct = round(100 - bug_pct, 1)

    return f"""
    (function() {{
        const ctx = document.getElementById('bugInvestmentChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: ['Feature Work', 'Bug Work'],
                    datasets: [{{
                        data: [{feature_pct}, {bug_pct}],
                        backgroundColor: ['#0d6efd', '#dc3545'],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: true, position: 'bottom' }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.label + ': ' + context.parsed + '%';
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def _generate_work_distribution_chart(flow_metrics: Dict[str, Any]) -> str:
    """Generate Chart.js script for work distribution stacked bar chart over time."""
    # Get weekly distribution history
    distribution_history = flow_metrics.get("distribution_history", [])

    if not distribution_history:
        return ""

    # Extract data for each flow type
    weeks_js = json.dumps([d["week"] for d in distribution_history])

    # Calculate percentages for each week
    feature_pct = []
    defect_pct = []
    tech_debt_pct = []
    risk_pct = []

    for week_data in distribution_history:
        total = week_data["total"]
        if total > 0:
            feature_pct.append(round((week_data["feature"] / total) * 100, 1))
            defect_pct.append(round((week_data["defect"] / total) * 100, 1))
            tech_debt_pct.append(round((week_data["tech_debt"] / total) * 100, 1))
            risk_pct.append(round((week_data["risk"] / total) * 100, 1))
        else:
            feature_pct.append(0)
            defect_pct.append(0)
            tech_debt_pct.append(0)
            risk_pct.append(0)

    feature_pct_js = json.dumps(feature_pct)
    defect_pct_js = json.dumps(defect_pct)
    tech_debt_pct_js = json.dumps(tech_debt_pct)
    risk_pct_js = json.dumps(risk_pct)

    # Also keep counts for tooltips
    feature_counts_js = json.dumps([d["feature"] for d in distribution_history])
    defect_counts_js = json.dumps([d["defect"] for d in distribution_history])
    tech_debt_counts_js = json.dumps([d["tech_debt"] for d in distribution_history])
    risk_counts_js = json.dumps([d["risk"] for d in distribution_history])

    return f"""
    (function() {{
        const ctx = document.getElementById('workDistributionChart');
        if (ctx) {{
            const featureCounts = {feature_counts_js};
            const defectCounts = {defect_counts_js};
            const techDebtCounts = {tech_debt_counts_js};
            const riskCounts = {risk_counts_js};
            
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {weeks_js},
                    datasets: [
                        {{
                            label: 'Feature',
                            data: {feature_pct_js},
                            backgroundColor: 'rgba(24, 128, 80, 0.65)',
                            borderColor: 'white',
                            borderWidth: 0.5,
                            counts: featureCounts
                        }},
                        {{
                            label: 'Defect',
                            data: {defect_pct_js},
                            backgroundColor: 'rgba(210, 50, 65, 0.65)',
                            borderColor: 'white',
                            borderWidth: 0.5,
                            counts: defectCounts
                        }},
                        {{
                            label: 'Tech Debt',
                            data: {tech_debt_pct_js},
                            backgroundColor: 'rgba(245, 120, 19, 0.65)',
                            borderColor: 'white',
                            borderWidth: 0.5,
                            counts: techDebtCounts
                        }},
                        {{
                            label: 'Risk',
                            data: {risk_pct_js},
                            backgroundColor: 'rgba(245, 185, 7, 0.65)',
                            borderColor: 'white',
                            borderWidth: 0.5,
                            counts: riskCounts
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            stacked: true,
                            grid: {{ display: false }},
                            ticks: {{
                                maxRotation: 45,
                                minRotation: 45
                            }}
                        }},
                        y: {{
                            stacked: true,
                            beginAtZero: true,
                            max: 100,
                            grid: {{ color: 'rgba(0,0,0,0.05)' }},
                            ticks: {{
                                callback: function(value) {{
                                    return value + '%';
                                }}
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ 
                            display: true, 
                            position: 'bottom',
                            labels: {{
                                boxWidth: 12,
                                padding: 10
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const count = context.dataset.counts[context.dataIndex];
                                    const pct = context.parsed.y.toFixed(1);
                                    return context.dataset.label + ': ' + pct + '% (' + count + ' items)';
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def _render_template(
    profile_name: str,
    query_name: str,
    time_period_weeks: int,
    sections: List[str],
    metrics: Dict[str, Any],
    chart_script: str,
) -> str:
    """
    Render HTML report template with provided data.

    Args:
        profile_name: Profile display name
        query_name: Query display name
        time_period_weeks: Number of weeks in analysis
        sections: List of sections included
        metrics: Calculated metrics dictionary
        chart_script: Combined Chart.js initialization scripts

    Returns:
        Rendered HTML string
    """
    from jinja2 import Environment, FileSystemLoader

    # Setup Jinja2 environment with custom filters
    template_dir = Path(__file__).parent.parent / "report_assets"
    env = Environment(loader=FileSystemLoader(template_dir))

    # Add number formatting filters
    def format_int(value):
        """Format as integer (no decimals)."""
        if value is None:
            return "0"
        return f"{int(round(value)):,}"

    def format_decimal1(value):
        """Format with 1 decimal place."""
        if value is None:
            return "0.0"
        return f"{value:.1f}"

    def format_decimal2(value):
        """Format with 2 decimal places."""
        if value is None:
            return "0.00"
        return f"{value:.2f}"

    env.filters["int"] = format_int
    env.filters["dec1"] = format_decimal1
    env.filters["dec2"] = format_decimal2

    template = env.get_template("report_template.html")

    # Generate timestamp with day of week
    generated_at = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

    # Get weeks count from metrics (actual weeks with data)
    weeks_count = metrics.get("dashboard", {}).get("weeks_count", time_period_weeks)

    # Load and embed external dependencies for offline reports
    from data.report_assets_embedder import embed_report_dependencies

    embedded_deps = embed_report_dependencies()

    html = template.render(
        profile_name=profile_name,
        query_name=query_name,
        generated_at=generated_at,
        time_period_weeks=time_period_weeks,
        weeks_count=weeks_count,
        sections=sections,
        metrics=metrics,
        chart_script=chart_script,
        show_points=metrics.get("dashboard", {}).get(
            "show_points", False
        ),  # Pass show_points flag
        # Embedded dependencies for offline use
        bootstrap_css=embedded_deps["bootstrap_css"],
        fontawesome_css=embedded_deps["fontawesome_css"],
        chartjs=embedded_deps["chartjs"],
        chartjs_annotation=embedded_deps["chartjs_annotation"],
    )

    return html


def _parse_week_label(week_label: str) -> datetime:
    """
    Parse ISO week label to datetime.

    Args:
        week_label: Week label in format "YYYY-WXX" (ISO 8601)

    Returns:
        Datetime for the Monday of that ISO week
    """
    try:
        # Use ISO 8601 week date format: %G (ISO year), %V (ISO week), %u (ISO weekday where 1=Monday)
        return datetime.strptime(week_label + "-1", "%G-W%V-%u")
    except ValueError:
        # Fallback to current date if parsing fails
        logger.warning(f"Could not parse week label: {week_label}")
        return datetime.now()


def _update_report_progress(percent: int, message: str) -> None:
    """Helper to update report generation progress.

    Args:
        percent: Progress percentage (0-100)
        message: Progress message
    """
    import json
    from pathlib import Path

    progress_file = Path("task_progress.json")
    if not progress_file.exists():
        return

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        if state.get("task_id") != "generate_report":
            return

        # Update report_progress object (consistent with fetch_progress/calculate_progress)
        state["report_progress"] = {"percent": percent, "message": message}

        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to update report progress: {e}")


def generate_html_report_with_progress(
    sections: List[str],
    time_period_weeks: int = 12,
    profile_id: Optional[str] = None,
) -> None:
    """
    Generate HTML report with progress tracking for background task.

    This function wraps generate_html_report() and adds progress updates
    via TaskProgress. The generated report is saved to a temporary file
    and the path is stored in progress data for download retrieval.

    Args:
        sections: List of section identifiers to include in report
        time_period_weeks: Number of weeks to analyze
        profile_id: Profile ID to generate report for

    Side effects:
        - Updates task_progress.json with progress updates
        - Creates temporary HTML file with report content
        - Updates progress data with report_file path on completion
    """
    from data.task_progress import TaskProgress
    from data.query_manager import get_active_profile_id

    try:
        # Ensure we have a profile_id
        if not profile_id:
            profile_id = get_active_profile_id()

        if not profile_id:
            raise ValueError("No active profile for report generation")

        # Progress checkpoint 1: Initialization
        _update_report_progress(5, "Initializing report generation...")

        # Progress checkpoint 2: Loading project data
        _update_report_progress(10, "Loading project data...")
        report_data = _load_report_data(profile_id, time_period_weeks)
        report_data["profile_id"] = profile_id

        # Progress checkpoint 3: Loading snapshots
        _update_report_progress(20, "Loading metrics snapshots...")
        # Get display names for metadata
        from data.profile_manager import get_active_profile_and_query_display_names

        context = get_active_profile_and_query_display_names()
        profile_name = context.get("profile_name") or profile_id
        query_name = context.get("query_name") or "Unknown Query"

        # Progress checkpoint 4: Dashboard metrics
        _update_report_progress(30, "Calculating dashboard metrics...")

        # Calculate metrics incrementally with progress updates
        metrics = {}
        show_points = report_data["settings"].get("show_points", False)

        # Dashboard always calculated
        metrics["dashboard"] = _calculate_dashboard_metrics(
            report_data["all_statistics"],
            report_data["statistics"],
            report_data["project_scope"],
            report_data["settings"],
            report_data["weeks_count"],
            show_points,
        )

        # Progress checkpoint 5: Section-specific metrics (DORA)
        if "dora" in sections:
            _update_report_progress(45, "Calculating DORA metrics...")
            metrics["dora"] = _calculate_dora_metrics(profile_id, time_period_weeks)

        # Progress checkpoint 6: Section-specific metrics (Flow)
        if "flow" in sections:
            _update_report_progress(55, "Calculating Flow metrics...")
            metrics["flow"] = _calculate_flow_metrics(
                report_data["snapshots"], time_period_weeks
            )

        # Add remaining sections without DORA/Flow
        _update_report_progress(60, "Finalizing metrics calculations...")
        remaining_sections = [s for s in sections if s not in ["dora", "flow"]]
        if remaining_sections:
            # Calculate remaining metrics in batch
            remaining_metrics = _calculate_all_metrics(
                report_data, remaining_sections, time_period_weeks
            )
            metrics.update(remaining_metrics)

        metrics["statistics"] = report_data["statistics"]

        # Progress checkpoint 7: Generating charts
        _update_report_progress(70, "Generating interactive charts...")
        chart_scripts = _generate_chart_scripts(metrics, sections)

        # Progress checkpoint 8: Rendering HTML
        _update_report_progress(80, "Rendering HTML template...")
        html = _render_template(
            profile_name=profile_name,
            query_name=query_name,
            time_period_weeks=time_period_weeks,
            sections=sections,
            metrics=metrics,
            chart_script="\n".join(chart_scripts),
        )

        # Progress checkpoint 9: Preparing download
        _update_report_progress(90, "Preparing download...")

        # Progress checkpoint 10: Finalizing
        _update_report_progress(95, "Finalizing report...")

        # Save to temporary file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_profile = profile_name.replace(" ", "_").replace("/", "_")
        safe_query = query_name.replace(" ", "_").replace("/", "_")
        filename = f"{timestamp}_{safe_profile}_{safe_query}_{time_period_weeks}w.html"

        # Create temp file in app directory for easy cleanup
        temp_file = Path("temp_reports") / filename
        temp_file.parent.mkdir(exist_ok=True)

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(
            f"Report saved to temporary file: {temp_file} ({len(html):,} bytes)"
        )

        # Complete task with report file path (100% shown by complete_task)
        TaskProgress.complete_task(
            "generate_report", "Report ready for download", report_file=str(temp_file)
        )

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        TaskProgress.fail_task("generate_report", str(e))
        raise
