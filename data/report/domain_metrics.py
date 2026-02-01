"""Domain-specific metrics calculations for report generation.

This module contains calculations for specific domains:
- Burndown metrics (velocity, remaining work)
- Bug metrics (resolution rate, capacity consumption)
- Scope metrics (scope creep, creation/completion ratios)
- Flow metrics (velocity, efficiency, WIP)
- DORA metrics (deployment frequency, lead time, CFR, MTTR)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_burndown_metrics(
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
    from data.report.helpers import (
        calculate_weekly_breakdown,
        calculate_historical_burndown,
    )

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
        remaining_items / velocity_items if velocity_items > 0 else float("inf")
    )
    weeks_remaining_points = (
        remaining_points / velocity_points if velocity_points > 0 else float("inf")
    )

    # Calculate weekly breakdown for chart
    weekly_data = calculate_weekly_breakdown(statistics)

    # Calculate historical remaining work for burndown chart
    historical_data = calculate_historical_burndown(statistics, project_scope)

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


def calculate_bug_metrics(
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
        logger.warning("[REPORT BUG] No JIRA issues available for bug analysis")
        return {"has_data": False}

    try:
        # Get bug type mappings
        bug_types = settings.get("bug_types", {})
        logger.info(
            f"[REPORT BUG] Processing {len(jira_issues)} JIRA issues with bug_types={bug_types}"
        )

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
            logger.warning(
                f"[REPORT BUG] No bugs found matching configured types. "
                f"Total JIRA issues: {len(jira_issues)}, bug_types={bug_types}"
            )
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
            (total_bugs_resolved / total_completed) * 100 if total_completed > 0 else 0
        )

        # Convert resolution rate from decimal to percentage
        resolution_rate = bug_summary.get("resolution_rate", 0)
        resolution_rate_pct = resolution_rate * 100

        # Round average age
        avg_age_days = bug_summary.get("avg_age_days", 0)

        # Count closed bugs from timeline-filtered bugs
        closed_bugs = bug_summary.get("closed_bugs", 0)

        return {
            "has_data": True,
            "open_bugs": bug_summary.get("open_bugs", 0),
            "total_bugs": bug_summary.get("total_bugs", 0),
            "closed_bugs": closed_bugs,
            "resolution_rate": resolution_rate_pct,
            "avg_age_days": avg_age_days,
            "capacity_consumed_by_bugs": bug_summary.get(
                "capacity_consumed_by_bugs", 0
            ),
            "forecast_weeks": forecast.get("most_likely_weeks") if forecast else None,
            "forecast_date": forecast.get("most_likely_date") if forecast else None,
            "avg_closure_rate": forecast.get("avg_closure_rate") if forecast else None,
            "weeks_analyzed": forecast.get("weeks_analyzed") if forecast else None,
            "bug_investment_pct": bug_investment_pct,
            "bug_capacity_consumption_pct": bug_summary.get(
                "capacity_consumed_by_bugs", 0
            ),  # Alias for health calculator
            "weekly_stats": weekly_stats,
            "date_from": date_from.strftime("%b %d, %Y"),
            "date_to": date_to.strftime("%b %d, %Y"),
        }
    except Exception as e:
        logger.error(f"Error calculating bug metrics: {e}", exc_info=True)
        return {"has_data": False, "error": str(e)}


def calculate_scope_metrics(
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
    total_created_points = df["created_points"].sum()
    total_completed_items = int(df["completed_items"].sum())
    total_completed_points = df["completed_points"].sum()

    # Current scope from project_scope (remaining work)
    current_items = project_scope.get("remaining_items", 0)
    current_points = project_scope.get("remaining_total_points", 0)

    # Calculate initial scope at window start
    # Work backwards from current: Initial = Current + Completed - Created
    # This accounts for both work completed and new work added during the period
    initial_items = current_items + total_completed_items - total_created_items
    initial_points = current_points + total_completed_points - total_created_points

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
    points_change = current_points - initial_points

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


def calculate_flow_metrics(
    snapshots: Dict[str, Dict],
    weeks_count: int,
    week_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Load Flow metrics from snapshots (matches app implementation).

    Uses the same snapshot reading logic as callbacks/dora_flow_metrics.py
    to ensure identical calculations with aggregation across the period.

    Args:
        snapshots: Filtered weekly snapshots (NOT USED - we read directly from cache)
        weeks_count: Number of weeks to load from snapshots
        week_labels: Pre-filtered week labels to use (ensures consistency with statistics filtering)

    Returns:
        Dictionary with Flow metrics matching app display
    """
    from data.time_period_calculator import get_iso_week, format_year_week
    from data.metrics_snapshots import get_metric_snapshot, get_available_weeks

    logger.info(f"Loading Flow metrics from snapshots for {weeks_count} weeks")

    # Use provided week labels if available (ensures same time window as statistics)
    if week_labels:
        week_labels = list(week_labels)  # Use pre-filtered labels
        logger.info(f"[FLOW METRICS] Using provided week labels: {week_labels}")
    else:
        # Fallback: Generate week labels (same as app)
        weeks = []
        current_date = datetime.now()
        for i in range(weeks_count):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)
        week_labels = list(reversed(weeks))  # Oldest to newest
        logger.warning(
            f"[FLOW METRICS] Generated week labels (should use provided): {week_labels}"
        )

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
    avg_velocity = sum(velocity_values) / len(velocity_values) if velocity_values else 0

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
        sum(non_zero_efficiency) / len(non_zero_efficiency)
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
        f"Flow metrics loaded: Velocity={avg_velocity:.2f} items/week, "
        f"Flow Time={median_flow_time:.2f}d, Efficiency={avg_efficiency:.2f}%, WIP={wip_count}"
    )

    # Check if there's any meaningful data (not all zeros)
    # has_data should be True only if at least ONE metric has real values
    has_meaningful_data = (
        (avg_velocity > 0)  # At least some velocity
        or (median_flow_time > 0)  # Flow time exists
        or (avg_efficiency > 0)  # Efficiency exists
        or (wip_count > 0)  # WIP exists
        or (total_completed > 0)  # Any completed work in distribution
    )

    if not has_meaningful_data:
        logger.info("No meaningful Flow data - all metrics are zero")
        return {"has_data": False, "weeks_count": weeks_count}

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


def calculate_dora_metrics(profile_id: str, weeks_count: int) -> Dict[str, Any]:
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
    mttr_days = mttr_hours / 24 if mttr_hours else None

    # Get weekly values for trend analysis
    weekly_labels = deploy_data.get("weekly_labels", [])

    logger.info(
        f"DORA metrics loaded: DF={deployment_freq} releases/week, "
        f"LT={lead_time_days}d, CFR={change_failure_rate}%, MTTR={mttr_days}d"
    )

    # Check if there's any meaningful data (not all zeros/None)
    # has_data should be True only if at least ONE metric has real values
    has_meaningful_data = (
        (deployment_freq > 0)  # At least one deployment
        or (lead_time_days is not None and lead_time_days > 0)  # Lead time exists
        or (mttr_days is not None and mttr_days > 0)  # MTTR exists
        # CFR can be legitimately 0% (no failures), so we check if deployment count exists
        or (deployment_freq_tasks > 0)  # Has tasks for CFR calculation
    )

    if not has_meaningful_data:
        logger.info("No meaningful DORA data - all metrics are zero or None")
        return {"has_data": False, "weeks_count": weeks_count}

    return {
        "has_data": True,
        "deployment_frequency": deployment_freq,  # Releases per week
        "deployment_frequency_tasks": deployment_freq_tasks,  # Tasks per week
        "lead_time": lead_time_days
        or 0,  # CRITICAL: Map to 'lead_time' for health calculator (app uses this key)
        "lead_time_days": lead_time_days,  # Days (None if no data) - keep for report charts
        "lead_time_hours": lead_time_hours,  # Hours (None if no data)
        "change_failure_rate": change_failure_rate,  # Percentage
        "mttr_hours": mttr_hours
        or 0,  # CRITICAL: Health calculator expects hours, not days
        "mttr_days": mttr_days,  # Days (None if no data) - keep for report charts
        "weekly_labels": weekly_labels,  # For charts
        "weeks_count": weeks_count,
        # Include full cached data for detailed reporting
        "_raw": cached_metrics,
    }
