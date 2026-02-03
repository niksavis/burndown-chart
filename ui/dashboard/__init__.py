"""
Comprehensive Dashboard Package - Modular Analytics Platform

A modular dashboard package providing deep insights into project health,
team performance, and delivery forecasts. Organized into focused section modules.

Public API exports all dashboard section creators and utility functions.
"""

from __future__ import annotations

from dash import html
from datetime import datetime, timedelta
import logging

# Utility functions
from ui.dashboard.utils import (
    safe_divide,
    format_date_relative,
    calculate_project_health_score,
    get_health_status,
    get_brief_health_reason,
    create_metric_card,
    create_mini_sparkline,
    create_progress_ring,
)

# Section creators
from ui.dashboard.executive_summary import (
    create_executive_summary_section,
)
from ui.dashboard.throughput_analytics import (
    create_throughput_analytics_section,
)
from ui.dashboard.forecast_analytics import (
    get_forecast_history,
    create_forecast_analytics_section,
)
from ui.dashboard.activity_quality import (
    create_recent_activity_section,
    create_quality_scope_section,
)
from ui.dashboard.insights_engine import (
    create_insights_section,
)


__all__ = [
    # Utilities
    "safe_divide",
    "format_date_relative",
    "calculate_project_health_score",
    "get_health_status",
    "get_brief_health_reason",
    "create_metric_card",
    "create_mini_sparkline",
    "create_progress_ring",
    # Section creators
    "create_executive_summary_section",
    "create_throughput_analytics_section",
    "get_forecast_history",
    "create_forecast_analytics_section",
    "create_recent_activity_section",
    "create_quality_scope_section",
    "create_insights_section",
    # Main dashboard function
    "create_comprehensive_dashboard",
]


#######################################################################
# MAIN DASHBOARD ORCHESTRATOR
#######################################################################


def create_comprehensive_dashboard(
    statistics_df,
    statistics_df_unfiltered,
    pert_time_items,
    pert_time_points,
    avg_weekly_items,
    avg_weekly_points,
    med_weekly_items,
    med_weekly_points,
    days_to_deadline,
    total_items,
    total_points,
    deadline_str,
    show_points=True,
    additional_context=None,
    data_points_count=None,
):
    """
    Create a comprehensive project dashboard with all available metrics.

    This dashboard provides:
    - Executive summary with project health scoring
    - Throughput analytics with trend analysis
    - Multi-method forecasting with confidence intervals
    - Actionable insights and recommendations

    Args:
        statistics_df: DataFrame with filtered project statistics (respects data_points_count slider)
        statistics_df_unfiltered: DataFrame with ALL project statistics (for Recent Completions)
        pert_time_items: PERT forecast time for items
        pert_time_points: PERT forecast time for points
        avg_weekly_items: Average weekly items completed
        avg_weekly_points: Average weekly points completed
        med_weekly_items: Median weekly items completed
        med_weekly_points: Median weekly points completed
        days_to_deadline: Days until project deadline
        total_items: Total items in project scope
        total_points: Total points in project scope
        deadline_str: Deadline date string
        show_points: Whether to show points-based metrics
        additional_context: Optional additional metrics and context

    Returns:
        html.Div: Complete dashboard layout
    """
    # CRITICAL FIX: Dashboard shows CURRENT remaining work, not windowed scope
    # The Data Points slider filters statistics for forecasting, but remaining is always current
    from data.persistence import load_unified_project_data
    from ui.budget_section import _create_budget_section

    unified_data = load_unified_project_data()
    project_scope = unified_data.get("project_scope", {})

    # Use CURRENT remaining values directly - slider doesn't affect remaining work
    total_items = project_scope.get("remaining_items", 0)
    total_points = project_scope.get("remaining_total_points", 0)

    # Prepare forecast data
    # Use points-based forecast when available, otherwise use items-based
    forecast_days = (
        pert_time_points if (show_points and pert_time_points) else pert_time_items
    )

    logger = logging.getLogger(__name__)

    logger.info("[DASHBOARD] Using current remaining work (independent of slider):")
    logger.info(
        f"  data_points_count={data_points_count or 'all'}, "
        f"total_items={total_items}, total_points={total_points}"
    )

    logger.info(
        f"[DASHBOARD PERT] Input PERT values: pert_time_items={pert_time_items}, "
        f"pert_time_points={pert_time_points}, show_points={show_points}, "
        f"chosen forecast_days={forecast_days}"
    )

    schedule_variance_calc = (
        (
            days_to_deadline - forecast_days
        )  # Positive = ahead of schedule (buffer), negative = behind
        if (forecast_days and days_to_deadline)
        else 0
    )
    logger.info(
        f"[APP SCHEDULE] forecast_days={forecast_days}, days_to_deadline={days_to_deadline}, schedule_variance={schedule_variance_calc}"
    )

    # Extract last statistics date for forecast starting point (aligns with weekly data structure)
    # CRITICAL: Statistics are weekly-based (Mondays), so use last Monday data point not datetime.now()
    # Use iloc[-1] (not max()) to ensure we get the LAST date in the sorted/filtered dataframe
    # This matches report_generator.py logic exactly (df_windowed["date"].iloc[-1])
    last_date = (
        statistics_df["date"].iloc[-1]
        if not statistics_df.empty and "date" in statistics_df.columns
        else datetime.now()
    )

    logger.info(
        f"[DASHBOARD FORECAST] last_date={last_date.strftime('%Y-%m-%d') if hasattr(last_date, 'strftime') else last_date}, "
        f"forecast_days={forecast_days}, statistics_rows={len(statistics_df)}, "
        f"completion_date={(last_date + timedelta(days=forecast_days)).strftime('%Y-%m-%d') if forecast_days else 'None'}"
    )

    forecast_data = {
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "velocity_cv": 25,  # Default coefficient of variation
        "schedule_variance_days": schedule_variance_calc,
        "last_date": last_date,  # Starting point for forecast calculations
        "completion_date": (last_date + timedelta(days=forecast_days)).strftime(
            "%Y-%m-%d"
        )
        if forecast_days
        else None,
    }

    # Calculate velocity statistics for confidence intervals
    velocity_std = 0
    velocity_mean = 0

    if not statistics_df.empty and len(statistics_df) >= 4:
        # Use population std (ddof=0) to match report calculation
        velocity_std = statistics_df["completed_items"].std(ddof=0)
        velocity_mean = statistics_df["completed_items"].mean()
        if velocity_mean > 0:
            forecast_data["velocity_cv"] = (velocity_std / velocity_mean) * 100
            logger.info(
                f"[HEALTH DEBUG] Velocity CV calculation: std={velocity_std:.2f}, "
                f"mean={velocity_mean:.2f}, CV={forecast_data['velocity_cv']:.2f}%, "
                f"statistics_rows={len(statistics_df)}"
            )

    # Calculate statistically-based confidence intervals
    # Using Monte Carlo-inspired approach: forecast uncertainty grows with remaining work
    # Standard error of completion time ≈ (remaining / velocity) * (velocity_std / velocity_mean)
    # This accounts for: more remaining work = more uncertainty, higher velocity variance = more uncertainty

    # Use points-based forecast when available (matches report and burndown chart)
    forecast_days = pert_time_points if pert_time_points else pert_time_items

    # Calculate deadline probability for BOTH items and points tracks
    def calculate_deadline_probability(
        forecast, days_to_deadline, velocity_mean, velocity_std, weeks_observed
    ):
        """Calculate deadline probability for a given forecast."""
        if not forecast or velocity_mean <= 0 or velocity_std <= 0:
            return 75 if (forecast or 0) <= (days_to_deadline or 0) else 25

        cv_ratio = velocity_std / velocity_mean
        weeks_remaining = max(1, forecast / 7)
        uncertainty_factor = (weeks_remaining / weeks_observed) ** 0.5
        forecast_std_days = forecast * cv_ratio * uncertainty_factor

        if days_to_deadline > 0 and forecast_std_days > 0:
            z_score = (days_to_deadline - forecast) / forecast_std_days
            return 100 / (1 + 2.718 ** (-1.7 * z_score))
        else:
            return 75 if forecast <= days_to_deadline else 25

    weeks_observed = len(statistics_df) if not statistics_df.empty else 1
    deadline_probability_items = calculate_deadline_probability(
        pert_time_items, days_to_deadline, velocity_mean, velocity_std, weeks_observed
    )
    deadline_probability_points = (
        calculate_deadline_probability(
            pert_time_points,
            days_to_deadline,
            velocity_mean,
            velocity_std,
            weeks_observed,
        )
        if pert_time_points
        else None
    )

    if forecast_days and velocity_mean > 0 and velocity_std > 0:
        # Coefficient of variation as a ratio (not percentage)
        cv_ratio = velocity_std / velocity_mean

        # Forecast standard deviation: uncertainty scales with forecast duration and velocity variability
        # Using: σ_forecast ≈ forecast_days * CV * sqrt(weeks_remaining / weeks_observed)
        weeks_remaining = max(1, forecast_days / 7)  # Convert days to weeks
        uncertainty_factor = (weeks_remaining / weeks_observed) ** 0.5

        forecast_std_days = forecast_days * cv_ratio * uncertainty_factor

        # Confidence intervals using z-scores:
        # 50% CI: ±0.67σ (but we show median which equals PERT estimate)
        # 95% CI: +1.65σ (one-tailed, conservative estimate)
        ci_50_days = forecast_days  # Median = PERT estimate (50th percentile)
        ci_95_days = forecast_days + (1.65 * forecast_std_days)  # 95th percentile

        # Use combined probability (average when both available, or single track)
        deadline_probability = (
            deadline_probability_points
            if pert_time_points
            else deadline_probability_items
        )
    else:
        # Fallback for insufficient data: use conservative fixed offsets
        ci_50_days = forecast_days if forecast_days else 0
        ci_95_days = (forecast_days + 14) if forecast_days else 0
        deadline_probability = (
            deadline_probability_points
            if pert_time_points
            else deadline_probability_items
        )

    # Ensure deadline_probability is not None before using in min()
    final_deadline_prob = (
        deadline_probability if deadline_probability is not None else 75
    )

    confidence_data = {
        "ci_50": max(0, ci_50_days),
        "ci_80": pert_time_items if pert_time_items else 0,  # Keep for compatibility
        "ci_95": max(0, ci_95_days),
        "deadline_probability": max(0, min(100, final_deadline_prob)),
        "deadline_probability_items": max(0, min(100, deadline_probability_items)),
        "deadline_probability_points": max(0, min(100, deadline_probability_points))
        if deadline_probability_points
        else None,
    }

    # Prepare settings for sections
    settings = {
        "total_items": total_items,
        "total_points": total_points,
        "deadline": deadline_str,
        "show_points": show_points,
        "extended_metrics": additional_context.get("extended_metrics", {})
        if additional_context
        else {},
    }

    # Extract budget data from additional_context for insights
    budget_data = additional_context.get("budget_data") if additional_context else None

    # Construct PERT data for insights (need optimistic/pessimistic for uncertainty analysis)
    # Calculate PERT bounds based on velocity variability
    pert_optimistic_days = 0
    pert_pessimistic_days = 0
    if pert_time_items and velocity_mean > 0 and velocity_std > 0:
        # Optimistic: -1σ scenario (faster than typical)
        cv_ratio = velocity_std / velocity_mean
        optimistic_factor = 1 - cv_ratio
        pessimistic_factor = 1 + (
            1.5 * cv_ratio
        )  # More conservative on pessimistic side
        pert_optimistic_days = max(1, pert_time_items * max(0.5, optimistic_factor))
        pert_pessimistic_days = pert_time_items * pessimistic_factor
    elif pert_time_items:
        # Fallback: use simple ±25% range
        pert_optimistic_days = pert_time_items * 0.75
        pert_pessimistic_days = pert_time_items * 1.25

    pert_data = {
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "pert_optimistic_days": pert_optimistic_days,
        "pert_pessimistic_days": pert_pessimistic_days,
        "last_date": last_date,
    }

    return html.Div(
        [
            # Page header
            # Executive Summary
            create_executive_summary_section(
                statistics_df, forecast_data, settings, avg_weekly_items
            ),
            # Throughput Analytics
            create_throughput_analytics_section(
                statistics_df,
                forecast_data,
                settings,
                data_points_count,
                additional_context,
            ),
            # Recent Completions Section - uses unfiltered data for consistent 4-week view
            create_recent_activity_section(statistics_df_unfiltered, show_points),
            # Delivery Forecast Section
            create_forecast_analytics_section(
                forecast_data,
                confidence_data,
                budget_data=budget_data,
                show_points=show_points,
                remaining_items=total_items,
                remaining_points=total_points,
                avg_weekly_items=avg_weekly_items,
                avg_weekly_points=avg_weekly_points,
                days_to_deadline=days_to_deadline,
                deadline_str=deadline_str,
            ),
            # Budget & Resource Tracking (conditional on budget configuration)
            _create_budget_section(
                profile_id=additional_context.get("profile_id", "")
                if additional_context
                else "",
                query_id=additional_context.get("query_id", "")
                if additional_context
                else "",
                week_label=additional_context.get("current_week_label", "")
                if additional_context
                else "",
                budget_data=budget_data,
                points_available=show_points,
                data_points_count=data_points_count or 12,
            ),
            # Quality & Scope Section
            create_quality_scope_section(statistics_df, settings),
            # Insights Section
            create_insights_section(
                statistics_df,
                settings,
                budget_data,
                pert_data=pert_data,
                deadline=settings.get("deadline") if settings else None,
            ),
        ],
        className="dashboard-comprehensive",
    )
