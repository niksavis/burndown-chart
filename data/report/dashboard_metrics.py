"""Dashboard metrics calculation for HTML reports.

This module calculates comprehensive dashboard summary metrics using the same
methodology as the application's dashboard, including health scoring, velocity
analysis, PERT forecasting, and schedule variance tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_dashboard_metrics(
    all_statistics: List[Dict],
    windowed_statistics: List[Dict],
    project_scope: Dict,
    settings: Dict,
    weeks_count: int,
    show_points: bool = False,
    extended_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate dashboard summary metrics using LIFETIME-based calculations (same as app).

    CRITICAL RULES (matching data/processing.py):
    1. Statistics are INCREMENTAL (daily values) - must use .sum() not .iloc[-1]
    2. Use ALL statistics for completed items (lifetime total, not windowed)
    3. Total comes from settings.estimated_total_items (NOT calculated)
    4. Remaining = total - completed (same as app)
    5. Completion % = completed / total (LIFETIME, same as app)
    6. Health score uses comprehensive formula (6 dimensions: Delivery, Predictability, Quality, Efficiency, Sustainability, Financial)

    Args:
        all_statistics: ALL statistics for lifetime completion calculation
        windowed_statistics: Windowed statistics for velocity calculation
        project_scope: Current project scope with remaining items/points
        settings: App settings with deadline and milestone
        weeks_count: Actual number of weeks with data
        show_points: Whether to use points-based (True) or items-based (False) forecasting
        extended_metrics: Optional extended metrics (DORA, Flow, Bug, Budget) for comprehensive health calculation

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
            "velocity_items_recent_4w": 0,
            "velocity_points_recent_4w": 0,
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
        df_windowed["completed_points"].sum() if not df_windowed.empty else 0
    )

    # Get CURRENT remaining from project_scope (same as app)
    remaining_items = project_scope.get("remaining_items", 0)
    remaining_points = project_scope.get("remaining_total_points", 0)

    # Calculate WINDOW-BASED total = current remaining + completed in window (same as app)
    total_items = remaining_items + completed_items
    total_points = remaining_points + completed_points

    # Calculate WINDOW-BASED completion percentages (same as app)
    items_completion_pct = (
        (completed_items / total_items) * 100 if total_items > 0 else 0
    )
    points_completion_pct = (
        (completed_points / total_points) * 100 if total_points > 0 else 0
    )

    logger.info(
        f"[REPORT COMPLETION] completed_items={completed_items}, remaining_items={remaining_items}, "
        f"total_items={total_items}, completion_pct={items_completion_pct:.2f}%"
    )

    # CRITICAL: Filter to weeks_count BEFORE any health/velocity calculations
    # This ensures all health metrics use the same data window as the report request
    data_points_count = weeks_count
    df_for_velocity = df_windowed

    logger.info(
        f"[REPORT FILTER DEBUG] weeks_count={weeks_count}, df_windowed len={len(df_windowed)}, "
        f"data_points_count={data_points_count}"
    )

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

        # Generate the same week labels that the dashboard uses
        from data.time_period_calculator import get_iso_week, format_year_week

        weeks = []
        current_date = df_windowed_temp["date"].max()
        for i in range(data_points_count):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)

        week_labels = set(reversed(weeks))  # Convert to set for fast lookup

        # Filter by week_label if available, otherwise fall back to date range
        if "week_label" in df_windowed_temp.columns:
            df_for_velocity = df_windowed_temp[
                df_windowed_temp["week_label"].isin(week_labels)
            ]
            logger.info(
                f"[REPORT FILTER EARLY] Filtered to {len(df_for_velocity)} rows for health calculation (requested {data_points_count} weeks)"
            )
        else:
            # Fallback: date range filtering (old behavior for backward compatibility)
            latest_date = df_windowed_temp["date"].max()
            cutoff_date = latest_date - timedelta(weeks=data_points_count)
            df_for_velocity = df_windowed_temp[df_windowed_temp["date"] > cutoff_date]
            logger.warning(
                f"[REPORT FILTER EARLY] No week_label column - using date range filtering: {len(df_for_velocity)} rows"
            )

    # Calculate health metrics (same as app's dashboard.py)
    # Health score uses deduction-based formula starting at 100
    # CRITICAL: Use df_for_velocity (filtered to weeks_count) not df_windowed

    # Calculate velocity coefficient of variation (CV)
    velocity_cv = 0
    logger.info(
        f"[REPORT FILTER DEBUG] After filtering: df_for_velocity len={len(df_for_velocity)}"
    )
    if not df_for_velocity.empty and len(df_for_velocity) >= 2:
        weekly_velocities = df_for_velocity["completed_items"].tolist()
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

    # Calculate trend direction from filtered data
    trend_direction = "stable"
    recent_velocity_change = 0
    if not df_for_velocity.empty and len(df_for_velocity) >= 6:
        mid_point = len(df_for_velocity) // 2
        older_half = df_for_velocity.iloc[:mid_point]
        recent_half = df_for_velocity.iloc[mid_point:]

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

    # Schedule variance will be calculated after forecast (placeholder for now)
    schedule_variance_days = 0
    completion_confidence = 50  # Default confidence

    # Calculate velocity using filtered data (df_for_velocity was already filtered above)
    from data.processing import calculate_velocity_from_dataframe

    velocity_items_early = calculate_velocity_from_dataframe(
        df_for_velocity, "completed_items"
    )

    # Calculate comprehensive health score using v3.0 formula (6 dimensions)
    # Prepare dashboard metrics for health calculator using shared function (DRY)
    from data.project_health_calculator import (
        calculate_comprehensive_project_health,
        prepare_dashboard_metrics_for_health,
    )

    dashboard_metrics_for_health = prepare_dashboard_metrics_for_health(
        completion_percentage=items_completion_pct
        if not show_points
        else points_completion_pct,
        current_velocity_items=velocity_items_early,
        velocity_cv=velocity_cv,
        trend_direction=trend_direction,
        recent_velocity_change=recent_velocity_change,
        schedule_variance_days=schedule_variance_days,
        completion_confidence=50,  # Default, will be updated after PERT forecast
    )

    logger.info(
        f"[REPORT HEALTH FIRST] Input: completion_pct={items_completion_pct if not show_points else points_completion_pct:.2f}, "
        f"velocity_items={velocity_items_early:.2f}, velocity_cv={velocity_cv:.2f}, "
        f"trend={trend_direction}, recent_change={recent_velocity_change:.2f}, "
        f"schedule_var={schedule_variance_days:.2f}, confidence=50"
    )

    # Add extended metrics if available
    if extended_metrics is None:
        extended_metrics = {}

    # Calculate comprehensive health using same calculator as dashboard
    # Note: Using placeholder scope_change_rate=0 for initial calculation
    # Will be recalculated with correct value after df_for_velocity is created
    health_result = calculate_comprehensive_project_health(
        dashboard_metrics=dashboard_metrics_for_health,
        dora_metrics=extended_metrics.get("dora"),
        flow_metrics=extended_metrics.get("flow"),
        bug_metrics=extended_metrics.get("bug_analysis"),
        budget_metrics=extended_metrics.get("budget"),
        scope_metrics={"scope_change_rate": 0},  # Placeholder, recalculated later
    )

    health_score = health_result["overall_score"]

    # Determine health status using v3.0 thresholds
    if health_score >= 70:
        health_status = "GOOD"
    elif health_score >= 50:
        health_status = "CAUTION"
    elif health_score >= 30:
        health_status = "AT RISK"
    else:
        health_status = "CRITICAL"

    logger.info(
        f"[REPORT HEALTH] Comprehensive health_score={health_score}% status={health_status} "
        f"formula_version={health_result.get('formula_version')} "
        f"dimensions={len(health_result.get('dimensions', {}))}"
    )

    # Calculate velocity using EXACT SAME method as app dashboard
    # App uses calculate_velocity_from_dataframe() which returns WEEKLY velocity (items per week)
    # Velocity calculation - df_for_velocity was already filtered earlier (line ~690)
    # Just calculate velocity from the already-filtered dataframe
    from data.processing import calculate_velocity_from_dataframe

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

    # Calculate recent 4-week velocity for short-term performance indicator
    velocity_items_recent_4w = 0
    velocity_points_recent_4w = 0
    if not df_for_velocity.empty and len(df_for_velocity) >= 4:
        # Get most recent 4 weeks
        df_recent_4w = df_for_velocity.tail(4)
        velocity_items_recent_4w = calculate_velocity_from_dataframe(
            df_recent_4w, "completed_items"
        )
        velocity_points_recent_4w = calculate_velocity_from_dataframe(
            df_recent_4w, "completed_points"
        )
        logger.debug(
            f"[REPORT VELOCITY 4W] Recent 4 weeks: velocity_items={velocity_items_recent_4w:.2f}, "
            f"velocity_points={velocity_points_recent_4w:.2f}"
        )
    elif not df_for_velocity.empty:
        # If less than 4 weeks, use what we have
        velocity_items_recent_4w = velocity_items
        velocity_points_recent_4w = velocity_points

    # Calculate scope change rate from FILTERED data (same as app)
    # This must match the app's calculation in dashboard.py
    scope_change_rate = 0
    if not df_for_velocity.empty and "created_items" in df_for_velocity.columns:
        total_created = df_for_velocity["created_items"].sum()
        if total_items > 0:
            scope_change_rate = (total_created / total_items) * 100

    logger.debug(
        f"[REPORT SCOPE] scope_change_rate={scope_change_rate:.2f}% (from {len(df_for_velocity)} rows)"
    )

    # Get deadline and milestone from settings
    deadline = settings.get("deadline")
    milestone = settings.get("milestone")
    pert_factor = settings.get("pert_factor", 6)

    # Calculate PERT forecast using EXACT SAME method as app comprehensive dashboard
    # App uses calculate_rates() which returns empirical PERT days (not simplified formula)
    # This is in ui/dashboard.py and data/processing.py calculate_rates()
    from data.processing import compute_weekly_throughput, calculate_rates

    forecast_date = None
    forecast_months = None
    forecast_metric = "story points" if show_points else "items"
    pert_days = None
    forecast_date_items = None
    forecast_date_points = None

    # CRITICAL: Compute weekly throughput from FILTERED statistics (same as app)
    # Use df_for_velocity which respects data_points_count, not df_windowed
    grouped = compute_weekly_throughput(df_for_velocity)

    logger.info(
        f"[REPORT DATA] df_for_velocity rows={len(df_for_velocity)}, grouped weeks={len(grouped)}, "
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
    # IMPORTANT: Use df_for_velocity (filtered data) to match dashboard behavior
    last_date = (
        df_for_velocity["date"].iloc[-1]
        if not df_for_velocity.empty
        else datetime.now()
    )

    logger.info(
        f"[REPORT FORECAST] last_date={last_date.strftime('%Y-%m-%d') if hasattr(last_date, 'strftime') else last_date}, "
        f"pert_days={pert_days}, df_for_velocity_rows={len(df_for_velocity)}, "
        f"completion_date={(last_date + timedelta(days=pert_days)).strftime('%Y-%m-%d') if pert_days and pert_days > 0 else 'None'}"
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
        # CRITICAL: Preserve sign for health calculation
        # Negative = behind schedule (bad), Positive = ahead of schedule (good)
        # App: schedule_var = -(pert_days - days_to_deadline)
        # Simplified: schedule_var = days_to_deadline - pert_days
        schedule_variance_days = days_to_deadline - pert_days
        logger.info(
            f"[REPORT HEALTH] RECALC: schedule_variance_days={schedule_variance_days:.2f} "
            f"(pert_days={pert_days:.2f}, days_to_deadline={days_to_deadline})"
        )

        # Calculate confidence based on schedule buffer (same logic as dashboard)
        # Calculate completion confidence from schedule variance buffer
        # CRITICAL: Must match ui/dashboard.py confidence calculation EXACTLY
        # Any difference in thresholds causes health score divergence
        # Positive buffer (ahead of schedule) = higher confidence
        # Negative buffer (behind schedule) = lower confidence
        buffer_days = days_to_deadline - pert_days
        if buffer_days >= 28:  # Match app threshold (was 30)
            completion_confidence = 95  # Very high confidence
        elif buffer_days >= 14:
            completion_confidence = 80  # High confidence
        elif buffer_days >= 0:
            completion_confidence = 65  # Moderate confidence
        elif buffer_days >= -14:
            completion_confidence = 45  # Low confidence
        else:
            completion_confidence = 25  # Very low confidence

        # Recalculate comprehensive health score with updated schedule variance and confidence
        # ALWAYS use items_completion_pct for health (consistent with app)
        dashboard_metrics_for_health = prepare_dashboard_metrics_for_health(
            completion_percentage=items_completion_pct,  # Always items, not points
            current_velocity_items=velocity_items,
            velocity_cv=velocity_cv,
            trend_direction=trend_direction,
            recent_velocity_change=recent_velocity_change,
            schedule_variance_days=schedule_variance_days,  # Updated value
            completion_confidence=completion_confidence,  # Updated value
        )

        logger.info(
            f"[REPORT HEALTH] Input: completion_pct={items_completion_pct:.2f}, "
            f"velocity_items={velocity_items:.2f}, velocity_cv={velocity_cv:.2f}, "
            f"trend={trend_direction}, recent_change={recent_velocity_change:.2f}, "
            f"schedule_var={schedule_variance_days:.2f}, confidence={completion_confidence}, "
            f"scope_change_rate={scope_change_rate:.2f}"
        )

        health_result = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_for_health,
            dora_metrics=extended_metrics.get("dora"),
            flow_metrics=extended_metrics.get("flow"),
            bug_metrics=extended_metrics.get("bug_analysis"),
            budget_metrics=extended_metrics.get("budget"),
            scope_metrics={"scope_change_rate": scope_change_rate},
        )

        health_score = health_result["overall_score"]

        # Determine health status using v3.0 thresholds
        if health_score >= 70:
            health_status = "GOOD"
        elif health_score >= 50:
            health_status = "CAUTION"
        elif health_score >= 30:
            health_status = "AT RISK"
        else:
            health_status = "CRITICAL"

        logger.info(
            f"[REPORT HEALTH] FINAL health_score={health_score}% status={health_status} "
            f"(recalculated with schedule_variance_days={schedule_variance_days:.2f})"
        )
    else:
        # No deadline configured - recalculate health with final extended_metrics
        # This ensures budget_metrics are included even without deadline
        logger.info(
            "[REPORT HEALTH] No deadline - recalculating health with all extended metrics"
        )
        health_result = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_for_health,
            dora_metrics=extended_metrics.get("dora"),
            flow_metrics=extended_metrics.get("flow"),
            bug_metrics=extended_metrics.get("bug_analysis"),
            budget_metrics=extended_metrics.get("budget"),
            scope_metrics={"scope_change_rate": scope_change_rate},
        )
        health_score = health_result["overall_score"]
        if health_score >= 70:
            health_status = "GOOD"
        elif health_score >= 50:
            health_status = "CAUTION"
        elif health_score >= 30:
            health_status = "AT RISK"
        else:
            health_status = "CRITICAL"

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
        "velocity_items_recent_4w": velocity_items_recent_4w,
        "velocity_points_recent_4w": velocity_points_recent_4w,
        "weeks_count": weeks_count,
        "pert_time_items": pert_time_items,  # Raw PERT days for items (for deadline calculations)
        "pert_time_points": pert_time_points,  # Raw PERT days for points
        "pert_time_items_weeks": (pert_time_items / 7.0) if pert_time_items else 0,
        "pert_time_points_weeks": (pert_time_points / 7.0) if pert_time_points else 0,
        "show_points": show_points,  # Pass show_points flag for template
        "health_dimensions": health_result.get(
            "dimensions", {}
        ),  # Pass health dimensions for breakdown visualization
        "velocity_cv": velocity_cv,  # Pass velocity coefficient of variation
        "trend_direction": trend_direction,  # Pass trend direction
        "recent_velocity_change": recent_velocity_change,  # Pass recent velocity change for Delivery dimension
        "schedule_variance_days": schedule_variance_days,  # Pass schedule variance
        "completion_confidence": completion_confidence,  # Pass completion confidence
        "scope_change_rate": scope_change_rate,  # Pass scope change rate for Sustainability dimension display
        "forecast_weeks_items": (pert_time_items / 7.0)
        if pert_time_items
        else 0,  # Pass forecast weeks for budget alignment
    }
