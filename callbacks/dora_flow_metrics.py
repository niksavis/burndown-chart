"""DORA and Flow Metrics Dashboard Callbacks.

Handles metric calculations and display for DORA and Flow dashboards.
Uses ISO week bucketing (Monday-Sunday) with Data Points slider controlling display period.
Matches architecture of existing burndown/statistics dashboards.

All field mappings and configuration values come from app_settings.json - no hardcoded values.
"""

from dash import callback, Output, Input, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

from data.persistence import load_app_settings
from ui.metric_cards import create_metric_cards_grid
from ui.work_distribution_card import create_work_distribution_card
from configuration.help_content import FLOW_METRICS_TOOLTIPS, DORA_METRICS_TOOLTIPS

logger = logging.getLogger(__name__)


#######################################################################
# HELPER FUNCTIONS (Feature 009)
#######################################################################


def _calculate_dynamic_forecast(
    weekly_values: List[float],
    current_value: Optional[float],
    metric_type: str,
    metric_name: str = "",
) -> tuple:
    """Calculate forecast dynamically based on filtered weekly values (Feature 009).

    This function recalculates the forecast whenever the data_points slider changes,
    ensuring the forecast reflects the selected time window (e.g., 12w, 26w, 52w).

    Args:
        weekly_values: Historical weekly values (already filtered by data_points slider)
        current_value: Current week's value for trend calculation
        metric_type: "higher_better" or "lower_better"
        metric_name: Optional metric name for logging

    Returns:
        Tuple of (forecast_data, trend_vs_forecast) or (None, None) if insufficient data
    """
    from data.metrics_calculator import calculate_forecast, calculate_trend_vs_forecast

    # Need at least 4 weeks for meaningful forecast
    if not weekly_values or len(weekly_values) < 4:
        logger.debug(
            f"Insufficient data for forecast: {metric_name} has {len(weekly_values) if weekly_values else 0} weeks"
        )
        return None, None

    # Calculate forecast using filtered historical data
    try:
        forecast_data = calculate_forecast(weekly_values)
        if not forecast_data:
            return None, None

        # Calculate trend vs forecast
        trend_vs_forecast = None
        if current_value is not None:
            try:
                trend_vs_forecast = calculate_trend_vs_forecast(
                    current_value=float(current_value),
                    forecast_value=forecast_data["forecast_value"],
                    metric_type=metric_type,
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to calculate trend for {metric_name}: {e}")

        return forecast_data, trend_vs_forecast

    except Exception as e:
        logger.warning(f"Failed to calculate forecast for {metric_name}: {e}")
        return None, None


#######################################################################
# DORA METRICS CALLBACK
#######################################################################


@callback(
    Output("dora-metrics-cards-container", "children"),
    [
        Input("jira-issues-store", "data"),  # Check if JIRA data is loaded
        Input("chart-tabs", "active_tab"),
        Input("data-points-input", "value"),
        Input("metrics-refresh-trigger", "data"),  # Trigger refresh after calculation
    ],
    prevent_initial_call=False,
)
def load_and_display_dora_metrics(
    jira_data_store: Optional[Dict[str, Any]],
    active_tab: Optional[str],
    data_points: int,
    refresh_trigger: Optional[Any],
):
    """Load and display DORA metrics from cache.

    Similar to Flow metrics, loads pre-calculated weekly snapshots from
    metrics_snapshots.json instead of recalculating on every tab visit.

    Metrics are calculated when user clicks "Calculate Metrics" button in Settings,
    and saved to cache for instant display.

    Args:
        jira_data_store: Cached JIRA issues from global store (used to check if data is loaded)
        active_tab: Currently active tab (only process if DORA tab is active)
        data_points: Number of weeks to display (from Data Points slider)
        refresh_trigger: Timestamp of last metrics refresh (triggers update)

    Returns:
        Metrics cards HTML (no toast messages, consistent with Flow Metrics)
    """
    try:
        # Check if JIRA data is loaded FIRST (before checking for metrics)
        if not jira_data_store or not jira_data_store.get("issues"):
            from ui.empty_states import create_no_data_state

            logger.info("DORA: No JIRA data loaded, showing 'No Data' state")
            return create_no_data_state()

        # Get number of weeks to display (default 12 if not set)
        n_weeks = data_points if data_points and data_points > 0 else 12

        # Try to load from cache first
        from data.dora_metrics_calculator import load_dora_metrics_from_cache

        logger.info(f"DORA: Loading metrics from cache for {n_weeks} weeks")
        cached_metrics = load_dora_metrics_from_cache(n_weeks=n_weeks)

        # Store n_weeks in cached_metrics for display context
        if cached_metrics:
            cached_metrics["_n_weeks"] = n_weeks

        # CRITICAL DEBUG LOGGING
        logger.info("===== DORA METRICS DEBUG =====")
        logger.info(f"cached_metrics type: {type(cached_metrics)}")
        logger.info(f"cached_metrics is None: {cached_metrics is None}")
        logger.info(f"cached_metrics bool: {bool(cached_metrics)}")
        if cached_metrics:
            logger.info(f"cached_metrics keys: {list(cached_metrics.keys())}")
            for key, val in cached_metrics.items():
                if isinstance(val, dict):
                    logger.info(
                        f"  {key}: value={val.get('value')}, labels={len(val.get('weekly_labels', []))}"
                    )
                else:
                    logger.info(f"  {key}: {val}")
        logger.info("===== END DEBUG =====")

        logger.info(
            f"DORA: Cache loaded, data is {'available' if cached_metrics else 'empty'}"
        )

        if not cached_metrics:
            # No cache available - show unified empty state
            from ui.empty_states import create_no_metrics_state

            return create_no_metrics_state(metric_type="DORA")

        # Load metrics from cache and create display
        # Use .get() with defaults to safely handle missing or None values
        n_weeks_display = cached_metrics.get("_n_weeks", 12)

        # Import tier calculation function
        from data.dora_metrics import (
            _determine_performance_tier,
            DEPLOYMENT_FREQUENCY_TIERS,
            LEAD_TIME_TIERS,
            CHANGE_FAILURE_RATE_TIERS,
            MTTR_TIERS,
        )

        # Calculate performance tiers for each metric
        # Use RELEASE count as primary deployment frequency (unique fixVersions)
        # This represents actual production deployments, not individual operational tasks
        deployment_freq_value = cached_metrics.get("deployment_frequency", {}).get(
            "release_value",
            0,  # Use release_value (unique fixVersions) as primary metric
        )
        # Fallback to task count if release_value not available
        if deployment_freq_value == 0:
            deployment_freq_value = cached_metrics.get("deployment_frequency", {}).get(
                "value", 0
            )

        # Also keep task count for detailed view
        task_count_value = cached_metrics.get("deployment_frequency", {}).get(
            "value", 0
        )

        # Convert deployments/week to deployments/month for tier comparison
        deployments_per_month = deployment_freq_value * 4.33  # Average weeks per month

        deployment_freq_tier = _determine_performance_tier(
            deployments_per_month, DEPLOYMENT_FREQUENCY_TIERS
        )

        lead_time_value = cached_metrics.get("lead_time_for_changes", {}).get("value")
        lead_time_tier = (
            _determine_performance_tier(lead_time_value, LEAD_TIME_TIERS)
            if lead_time_value is not None
            else {"tier": "Unknown", "color": "secondary"}
        )

        cfr_value = cached_metrics.get("change_failure_rate", {}).get("value", 0)
        cfr_tier = _determine_performance_tier(cfr_value, CHANGE_FAILURE_RATE_TIERS)

        mttr_value = cached_metrics.get("mean_time_to_recovery", {}).get("value")
        mttr_tier = (
            _determine_performance_tier(mttr_value, MTTR_TIERS)
            if mttr_value is not None
            else {"tier": "Unknown", "color": "secondary"}
        )

        metrics_data = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": deployment_freq_value,  # Now uses release_value (unique fixVersions)
                "task_value": task_count_value,  # Individual operational tasks (for details)
                "release_value": cached_metrics.get("deployment_frequency", {}).get(
                    "release_value", 0
                ),
                "_n_weeks": n_weeks_display,  # For card footer display
                "unit": f"releases/week (avg {n_weeks_display}w)",  # Changed label from deployments to releases
                "error_state": "success",
                "performance_tier": deployment_freq_tier["tier"],
                "performance_tier_color": deployment_freq_tier["color"],
                "total_issue_count": cached_metrics.get("deployment_frequency", {}).get(
                    "total_issue_count", 0
                ),
                "tooltip": f"{DORA_METRICS_TOOLTIPS.get('deployment_frequency', '')} Average calculated over last {n_weeks_display} weeks. Shows unique releases (fixVersions) per week.",
                "weekly_labels": cached_metrics.get("deployment_frequency", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": cached_metrics.get("deployment_frequency", {}).get(
                    "weekly_values",
                    [],  # Use deployment values for primary chart line
                ),
                "weekly_release_values": cached_metrics.get(
                    "deployment_frequency", {}
                ).get(
                    "weekly_release_values", []
                ),  # Use release values for secondary chart line
            },
            "lead_time_for_changes": {
                "metric_name": "lead_time_for_changes",
                "value": cached_metrics.get("lead_time_for_changes", {}).get("value"),
                "value_hours": cached_metrics.get("lead_time_for_changes", {}).get(
                    "value_hours"
                ),  # Secondary: hours equivalent
                "value_days": cached_metrics.get("lead_time_for_changes", {}).get(
                    "value_days"
                ),  # Secondary: days equivalent
                "p95_value": cached_metrics.get("lead_time_for_changes", {}).get(
                    "p95_value"
                ),  # NEW: P95 lead time
                "mean_value": cached_metrics.get("lead_time_for_changes", {}).get(
                    "mean_value"
                ),  # NEW: Mean lead time
                "_n_weeks": n_weeks_display,  # For card footer display
                "unit": f"days ({n_weeks_display}w median avg)",
                "error_state": "success"
                if cached_metrics.get("lead_time_for_changes", {}).get("value")
                is not None
                else "no_data",
                "performance_tier": lead_time_tier["tier"],
                "performance_tier_color": lead_time_tier["color"],
                "total_issue_count": cached_metrics.get(
                    "lead_time_for_changes", {}
                ).get("total_issue_count", 0),
                "tooltip": f"{DORA_METRICS_TOOLTIPS.get('lead_time_for_changes', '')} Average calculated over last {n_weeks_display} weeks.",
                "weekly_labels": cached_metrics.get("lead_time_for_changes", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": cached_metrics.get("lead_time_for_changes", {}).get(
                    "weekly_values", []
                ),
            },
            "change_failure_rate": {
                "metric_name": "change_failure_rate",
                "value": cached_metrics.get("change_failure_rate", {}).get("value", 0),
                "release_value": cached_metrics.get("change_failure_rate", {}).get(
                    "release_value", 0
                ),  # NEW: Release-based CFR
                "_n_weeks": n_weeks_display,  # For card footer display
                "unit": f"% (agg {n_weeks_display}w)",
                "error_state": "success",
                "performance_tier": cfr_tier["tier"],
                "performance_tier_color": cfr_tier["color"],
                "total_issue_count": cached_metrics.get("change_failure_rate", {}).get(
                    "total_issue_count", 0
                ),
                "tooltip": f"{DORA_METRICS_TOOLTIPS.get('change_failure_rate', '')} Aggregate rate calculated over last {n_weeks_display} weeks. Deployment-based vs Release-based rates.",
                "weekly_labels": cached_metrics.get("change_failure_rate", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": cached_metrics.get("change_failure_rate", {}).get(
                    "weekly_values", []
                ),
                "weekly_release_values": cached_metrics.get(
                    "change_failure_rate", {}
                ).get("weekly_release_values", []),  # NEW: Release CFR per week
            },
            "mean_time_to_recovery": {
                "metric_name": "mean_time_to_recovery",
                "value": cached_metrics.get("mean_time_to_recovery", {}).get("value"),
                "value_hours": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "value_hours"
                ),  # Secondary: hours equivalent
                "value_days": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "value_days"
                ),  # Secondary: days equivalent
                "p95_value": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "p95_value"
                ),  # NEW: P95 MTTR
                "mean_value": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "mean_value"
                ),  # NEW: Mean MTTR
                "_n_weeks": n_weeks_display,  # For card footer display
                "unit": f"hours ({n_weeks_display}w median avg)",
                "error_state": "success"
                if cached_metrics.get("mean_time_to_recovery", {}).get("value")
                is not None
                else "no_data",
                "performance_tier": mttr_tier["tier"],
                "performance_tier_color": mttr_tier["color"],
                "total_issue_count": cached_metrics.get(
                    "mean_time_to_recovery", {}
                ).get("total_issue_count", 0),
                "tooltip": f"{DORA_METRICS_TOOLTIPS.get('mean_time_to_recovery', '')} Average calculated over last {n_weeks_display} weeks.",
                "weekly_labels": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": cached_metrics.get("mean_time_to_recovery", {}).get(
                    "weekly_values", []
                ),
            },
        }

        # Calculate forecast dynamically based on filtered data (Feature 009)
        # This ensures forecast updates when user changes data_points slider
        logger.info(
            f"DORA: Calculating dynamic forecasts for {data_points} weeks of data"
        )

        # Define metric types for trend calculation
        metric_type_mapping = {
            "deployment_frequency": "higher_better",
            "lead_time_for_changes": "lower_better",
            "change_failure_rate": "lower_better",
            "mean_time_to_recovery": "lower_better",
        }

        for metric_name in metrics_data.keys():
            weekly_values = metrics_data[metric_name].get("weekly_values", [])
            current_value = metrics_data[metric_name].get("value")
            metric_type = metric_type_mapping.get(metric_name, "higher_better")

            # Calculate dynamic forecast based on filtered weekly data
            forecast_data, trend_vs_forecast = _calculate_dynamic_forecast(
                weekly_values=weekly_values,
                current_value=current_value,
                metric_type=metric_type,
                metric_name=metric_name,
            )

            if forecast_data:
                metrics_data[metric_name]["forecast_data"] = forecast_data
                logger.info(
                    f"Calculated forecast for {metric_name}: {forecast_data.get('forecast_value')}"
                )
            if trend_vs_forecast:
                metrics_data[metric_name]["trend_vs_forecast"] = trend_vs_forecast

        return create_metric_cards_grid(metrics_data)

    except PreventUpdate:
        raise
    except Exception as e:
        logger.error(f"Error loading DORA metrics from cache: {e}", exc_info=True)

        return create_metric_cards_grid(
            {
                "deployment_frequency": {
                    "metric_name": "deployment_frequency",
                    "value": None,
                    "error_state": "error",
                    "error_message": "Error loading metrics - check logs",
                },
                "lead_time_for_changes": {
                    "metric_name": "lead_time_for_changes",
                    "value": None,
                    "error_state": "error",
                },
                "change_failure_rate": {
                    "metric_name": "change_failure_rate",
                    "value": None,
                    "error_state": "error",
                },
                "mean_time_to_recovery": {
                    "metric_name": "mean_time_to_recovery",
                    "value": None,
                    "error_state": "error",
                },
            }
        )


#######################################################################
# FLOW METRICS CALLBACK (SNAPSHOT-BASED)
#######################################################################


@callback(
    Output("flow-metrics-cards-container", "children"),
    [
        Input("jira-issues-store", "data"),
        Input("data-points-input", "value"),
        Input("metrics-refresh-trigger", "data"),  # NEW: Trigger from Refresh button
    ],
    [
        State("current-settings", "data"),
    ],
    prevent_initial_call=False,
)
def calculate_and_display_flow_metrics(
    jira_data_store: Optional[Dict[str, Any]],
    data_points: int,
    metrics_refresh_trigger: Optional[int],
    app_settings: Optional[Dict[str, Any]],
):
    """Display Flow metrics per ISO week from snapshots.

    PERFORMANCE: Reads pre-calculated weekly snapshots from metrics_snapshots.json
    instead of calculating live (2-minute operation). Metrics are refreshed manually
    via the "Refresh Metrics" button.

    Uses Data Points slider to control how many weeks of historical data to display.
    Metrics aggregated per ISO week (Monday-Sunday boundaries).

    Args:
        jira_data_store: Cached JIRA issues from global store (used for context)
        data_points: Number of weeks to display (from Data Points slider)
        metrics_refresh_trigger: Timestamp of last metrics refresh (triggers update)
        app_settings: Application settings including field mappings

    Returns:
        Tuple of (metrics_cards_html, distribution_chart_html)
    """
    try:
        # Validate inputs
        if not jira_data_store or not jira_data_store.get("issues"):
            from ui.empty_states import create_no_data_state

            # Return no_data state for all metrics (Work Distribution included in same container)
            return create_no_data_state()

        if not app_settings:
            logger.warning("No app settings available, loading from disk")
            app_settings = load_app_settings()

        # Ensure we have app_settings (for type checker)
        if not app_settings:
            error_msg = "Failed to load app settings"
            logger.error(error_msg)
            return html.Div(error_msg, className="alert alert-danger p-4")

        # Get number of weeks to display (default 12 if not set)
        n_weeks = data_points if data_points and data_points > 0 else 12

        # Generate week labels for display
        from data.time_period_calculator import get_iso_week, format_year_week
        from data.metrics_snapshots import has_metric_snapshot

        weeks = []
        current_date = datetime.now()
        for i in range(n_weeks):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)

        week_labels = list(reversed(weeks))  # Oldest to newest
        current_week_label = week_labels[-1] if week_labels else ""

        logger.info(
            f"Flow: Reading snapshots for {len(week_labels)} weeks: {week_labels[:3]}...{week_labels[-3:]}"
        )

        # Check if ANY week has snapshots (not just current week)
        # This prevents "No Metrics" message when historical data exists but current week is missing
        from data.metrics_snapshots import get_available_weeks

        available_weeks = get_available_weeks()
        has_any_data = any(week in available_weeks for week in week_labels)

        if not has_any_data:
            from ui.empty_states import create_no_metrics_state

            logger.warning(
                f"No Flow metrics snapshots found for any of the {len(week_labels)} weeks"
            )

            # Return no_metrics state for metrics + HIDE Work Distribution card (like other cards)
            return (
                create_no_metrics_state(metric_type="Flow"),
                html.Div(),  # Empty div - hide Work Distribution when no metrics
            )

        # READ METRICS FROM SNAPSHOTS (instant, no calculation)
        # AGGREGATED across all weeks in selected period (like DORA metrics)
        from data.metrics_snapshots import get_metric_snapshot

        # Load historical metric values from snapshots for sparklines AND aggregation
        from data.metrics_snapshots import get_metric_weekly_values

        flow_load_values = get_metric_weekly_values(
            week_labels, "flow_load", "wip_count"
        )
        flow_time_values = get_metric_weekly_values(
            week_labels, "flow_time", "median_days"
        )
        flow_efficiency_values = get_metric_weekly_values(
            week_labels, "flow_efficiency", "overall_pct"
        )
        velocity_values = get_metric_weekly_values(
            week_labels, "flow_velocity", "completed_count"
        )

        # AGGREGATE Flow metrics across selected period (like DORA)
        # Flow Velocity: Average items/week across period
        non_zero_velocity = [v for v in velocity_values if v > 0]
        avg_velocity = (
            sum(velocity_values) / len(velocity_values) if velocity_values else 0
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
            sum(non_zero_efficiency) / len(non_zero_efficiency)
            if non_zero_efficiency
            else 0
        )

        # Flow Load (WIP): Current week snapshot ONLY (WIP is a point-in-time metric)
        # If current week missing, use most recent available week
        flow_load_snapshot = get_metric_snapshot(current_week_label, "flow_load")
        if not flow_load_snapshot and available_weeks:
            # Find most recent week with data
            for week in week_labels[::-1]:  # Start from most recent
                flow_load_snapshot = get_metric_snapshot(week, "flow_load")
                if flow_load_snapshot:
                    logger.info(
                        f"Flow: Using WIP data from {week} (current week {current_week_label} not available)"
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

                # Accumulate totals for aggregated display
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

        # Use aggregated values for display
        feature_count = total_feature
        defect_count = total_defect
        tech_debt_count = total_tech_debt
        risk_count = total_risk
        total_velocity = total_completed
        issues_in_period_count = total_completed

        logger.info(
            f"Flow metrics AGGREGATED over {n_weeks} weeks: "
            f"Velocity={avg_velocity:.1f} items/week (total {total_completed}), "
            f"Flow Time={median_flow_time:.1f}d (median), Efficiency={avg_efficiency:.1f}% (avg), "
            f"WIP={wip_count} (current week {current_week_label})"
        )

        # Note: dist_card layout moved to distribution chart section below
        # (Keeping 4-card grid for Flow metrics consistency)

        # Create stacked area chart for distribution history
        import plotly.graph_objects as go

        fig = go.Figure()

        # Calculate percentages for each trace upfront
        trace_configs = [
            ("Feature", "feature", "rgba(25, 135, 84, 1)", "rgba(25, 135, 84, 0.4)"),
            ("Defect", "defect", "rgba(220, 53, 69, 1)", "rgba(220, 53, 69, 0.4)"),
            (
                "Tech Debt",
                "tech_debt",
                "rgba(253, 126, 20, 1)",
                "rgba(253, 126, 20, 0.4)",
            ),
            ("Risk", "risk", "rgba(255, 193, 7, 1)", "rgba(255, 193, 7, 0.4)"),
        ]

        # Add traces for each work type (stacked area) with percentage hover
        # Color scheme: Feature (green/growth), Defect (red/problems), Tech Debt (orange/maintenance), Risk (yellow/caution)
        for trace_name, field_key, line_color, fill_color in trace_configs:
            # Calculate percentage for each week
            percentages = []
            for week_data in distribution_history:
                total = week_data["total"]
                count = week_data[field_key]
                pct = (count / total * 100) if total > 0 else 0
                percentages.append(f"{pct:.0f}")

            fig.add_trace(
                go.Scatter(
                    x=[d["week"] for d in distribution_history],
                    y=[d[field_key] for d in distribution_history],
                    name=trace_name,
                    mode="lines",
                    line=dict(width=0.5, color=line_color),
                    fillcolor=fill_color,
                    stackgroup="one",
                    customdata=percentages,
                    hovertemplate=f"%{{y}} {trace_name} (%{{customdata}}%)<extra></extra>",
                )
            )

        fig.update_layout(
            title={
                "text": "Work Distribution Over Time<br><sub style='font-size:10px;color:gray'>Hover for percentages. Target: 40-60% Feature, 20-40% Defect, 10-20% Tech Debt, 0-10% Risk</sub>",
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title="Week",
            yaxis_title="Number of Items",
            hovermode="x unified",
            height=400,
            margin=dict(
                l=50, r=120, t=80, b=70
            ),  # Increased bottom margin from 40 to 70 for angled labels
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        fig.update_xaxes(
            type="category",  # Force categorical axis to prevent date interpretation
            categoryorder="array",  # Use exact order from data
            categoryarray=[
                d["week"] for d in distribution_history
            ],  # Explicit week order
            showgrid=True,
            gridwidth=1,
            gridcolor="lightgray",
            tickangle=-45,  # Angle labels to prevent overlap
            tickfont=dict(size=9),  # Smaller font for better fit
        )
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

        # Create Work Distribution card using new component (2x width, matches other metric cards)
        distribution_data = {
            "feature": feature_count,
            "defect": defect_count,
            "tech_debt": tech_debt_count,
            "risk": risk_count,
            "total": total_velocity,
        }

        dist_card = create_work_distribution_card(
            distribution_data=distribution_data,
            week_label=f"{n_weeks}w aggregate",
            distribution_history=distribution_history,
            card_id="work-distribution-card",
        )

        # Create metric cards using same component as DORA
        # AGGREGATED across selected period (like DORA metrics)

        # Import performance tier calculation functions
        from ui.flow_metrics_dashboard import (
            _get_flow_performance_tier,
            _get_flow_performance_tier_color,
        )

        metrics_data = {
            "flow_velocity": {
                "metric_name": "flow_velocity",
                "value": round(avg_velocity, 1),  # Average items/week over period
                "_n_weeks": n_weeks,  # For card footer display
                "unit": f"items/week (avg {n_weeks}w)",
                "error_state": "success",  # Always valid - 0 velocity is acceptable
                "performance_tier": _get_flow_performance_tier(
                    "flow_velocity", avg_velocity
                ),
                "performance_tier_color": _get_flow_performance_tier_color(
                    "flow_velocity", avg_velocity
                ),
                "total_issue_count": issues_in_period_count,
                "weekly_labels": week_labels,
                "weekly_values": velocity_values,
                "details": {
                    "Feature": feature_count,
                    "Defect": defect_count,
                    "Technical Debt": tech_debt_count,
                    "Risk": risk_count,
                },
            },
            "flow_time": {
                "metric_name": "flow_time",
                "value": round(median_flow_time, 1)
                if median_flow_time is not None
                else 0,
                "_n_weeks": n_weeks,  # For card footer display
                "unit": f"days (median {n_weeks}w)",
                "error_state": "success",  # Always success - 0 is valid for weeks with no completions
                "performance_tier": _get_flow_performance_tier(
                    "flow_time", median_flow_time if median_flow_time is not None else 0
                ),
                "performance_tier_color": _get_flow_performance_tier_color(
                    "flow_time", median_flow_time if median_flow_time is not None else 0
                ),
                "total_issue_count": issues_in_period_count,
                "weekly_labels": week_labels,
                "weekly_values": flow_time_values,
            },
            "flow_efficiency": {
                "metric_name": "flow_efficiency",
                "value": round(avg_efficiency, 1) if avg_efficiency is not None else 0,
                "_n_weeks": n_weeks,  # For card footer display
                "unit": f"% (avg {n_weeks}w)",
                "error_state": "success",  # Always success - 0 is valid for weeks with no completions
                "performance_tier": _get_flow_performance_tier(
                    "flow_efficiency",
                    avg_efficiency if avg_efficiency is not None else 0,
                ),
                "performance_tier_color": _get_flow_performance_tier_color(
                    "flow_efficiency",
                    avg_efficiency if avg_efficiency is not None else 0,
                ),
                "total_issue_count": issues_in_period_count,
                "weekly_labels": week_labels,
                "weekly_values": flow_efficiency_values,
            },
            "flow_load": {
                "metric_name": "flow_load",
                "value": wip_count if wip_count is not None else 0,
                "_n_weeks": n_weeks,  # For card footer display
                "unit": f"items (current WIP)",  # WIP is always current snapshot
                "error_state": "success" if flow_load_snapshot else "no_data",
                "performance_tier": _get_flow_performance_tier(
                    "flow_load", wip_count if wip_count is not None else 0
                ),
                "performance_tier_color": _get_flow_performance_tier_color(
                    "flow_load", wip_count if wip_count is not None else 0
                ),
                "total_issue_count": wip_count,  # Use WIP count itself (not completion count)
                "weekly_labels": week_labels,
                "weekly_values": flow_load_values,
            },
        }

        # Calculate forecast dynamically based on filtered data (Feature 009)
        # This ensures forecast updates when user changes data_points slider
        logger.info(
            f"FLOW: Calculating dynamic forecasts for {data_points} weeks of data"
        )

        # Define metric types for trend calculation
        flow_metric_types = {
            "flow_velocity": "higher_better",
            "flow_time": "lower_better",
            "flow_efficiency": "higher_better",  # Note: 25-40% is ideal, but higher generally better
            "flow_load": "lower_better",
        }

        for metric_name in [
            "flow_velocity",
            "flow_time",
            "flow_efficiency",
            "flow_load",
        ]:
            weekly_values = metrics_data[metric_name].get("weekly_values", [])
            current_value = metrics_data[metric_name].get("value")
            metric_type = flow_metric_types.get(metric_name, "higher_better")

            # Calculate dynamic forecast based on filtered weekly data
            forecast_data, trend_vs_forecast = _calculate_dynamic_forecast(
                weekly_values=weekly_values,
                current_value=current_value,
                metric_type=metric_type,
                metric_name=metric_name,
            )

            if forecast_data:
                metrics_data[metric_name]["forecast_data"] = forecast_data

                # Special handling for Flow Load range
                if metric_name == "flow_load":
                    try:
                        from data.metrics_calculator import calculate_flow_load_range

                        FLOW_LOAD_RANGE_PERCENT = 0.20  # ±20% range
                        range_data = calculate_flow_load_range(
                            forecast_value=forecast_data["forecast_value"],
                            range_percent=FLOW_LOAD_RANGE_PERCENT,
                        )
                        forecast_data["forecast_range"] = range_data
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to calculate Flow Load range: {e}")

            if trend_vs_forecast:
                metrics_data[metric_name]["trend_vs_forecast"] = trend_vs_forecast

        # Pass Flow metrics tooltips to grid function
        metrics_html = create_metric_cards_grid(
            metrics_data, tooltips=FLOW_METRICS_TOOLTIPS
        )

        # Append Work Distribution card to the same grid (spans full width = 12 columns)
        # This ensures it has the same metric-cards-grid styling and shadow behavior
        dist_col = dbc.Col(dist_card, xs=12, lg=12, className="mb-3")
        if metrics_html and metrics_html.children:
            metrics_html.children.append(dist_col)

        return metrics_html

    except Exception as e:
        logger.error(f"Error calculating Flow metrics: {e}", exc_info=True)

        return html.Div("Error loading metrics", className="alert alert-danger p-4")


#######################################################################
# REFRESH METRICS CALLBACK
#######################################################################


@callback(
    [
        Output("calculate-metrics-status", "children"),
        Output("calculate-metrics-button", "disabled"),
        Output("calculate-metrics-button", "children"),
        Output("metrics-refresh-trigger", "data"),  # Trigger refresh after calculation
    ],
    [Input("calculate-metrics-button", "n_clicks")],
    [State("data-points-input", "value")],
    prevent_initial_call=False,  # Run on initial load to set button state with icon
)
def calculate_metrics_from_settings(
    button_clicks: Optional[int],
    data_points: Optional[int],
):
    """Calculate Flow and DORA metrics from Settings panel button.

    This is a separate callback from refresh_flow_metrics to avoid cross-tab
    dependency issues (Settings panel is always loaded, Flow tab may not be).

    Downloads changelog if needed, then calculates and saves results to
    metrics_snapshots.json for instant display on future page loads.

    IMPORTANT: Always calculates 52 weeks (1 year) regardless of Data Points slider.
    The slider only controls display filtering, not calculation scope.
    This ensures users can adjust the slider without recalculating.

    Note: Metrics are saved to cache file. When user opens Flow Metrics tab,
    it will automatically load the cached data. No need to trigger refresh
    since the Flow Metrics tab may not be loaded yet.

    Args:
        button_clicks: Number of times the Settings button has been clicked
        data_points: Number of weeks currently shown in Data Points slider (display only)

    Returns:
        Tuple of (status message, button disabled state, button children, refresh timestamp)
    """
    logger.info(
        f"[CALCULATE METRICS] Callback triggered - button_clicks={button_clicks}"
    )

    # Check if button was clicked
    if not button_clicks:
        return (
            "",
            False,
            [
                html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
                "Calculate Metrics",
            ],
            None,  # No refresh trigger
        )

    try:
        # Show loading state
        logger.info("Starting Flow metrics calculation from Settings panel")

        # Track task progress
        from data.task_progress import TaskProgress

        # CRITICAL FIX: Calculate metrics for the FULL data range from JIRA cache
        # NOT from today backwards, but from actual data boundaries
        # The data_points slider only controls DISPLAY, not calculation

        from data.jira_simple import load_jira_cache, get_jira_config
        from data.iso_week_bucketing import get_week_label, get_iso_week_bounds
        from datetime import timedelta

        # Calculate actual weeks from data, not from today
        weeks_to_calculate = []
        try:
            config = get_jira_config()
            cache_loaded, cached_issues = load_jira_cache(
                current_jql_query="",
                current_fields="created,resolutiondate",
                config=config,
            )

            if cache_loaded and cached_issues:
                # Extract all dates from issues
                all_dates = []
                for issue in cached_issues:
                    fields = issue.get("fields", {})

                    for field_name in ["created", "resolutiondate"]:
                        date_str = fields.get(field_name)
                        if date_str:
                            try:
                                all_dates.append(
                                    datetime.fromisoformat(
                                        date_str.replace("Z", "+00:00")
                                    )
                                )
                            except (ValueError, AttributeError):
                                pass

                if all_dates:
                    all_dates.sort()
                    earliest_date = all_dates[0]
                    latest_date = all_dates[-1]

                    logger.info(
                        f"Data range: {earliest_date.date()} to {latest_date.date()}"
                    )

                    # Generate week list from earliest to latest date
                    current = earliest_date
                    while current <= latest_date:
                        monday, sunday = get_iso_week_bounds(current)
                        week_label = get_week_label(current)
                        weeks_to_calculate.append((week_label, monday, sunday))

                        # Move to next week
                        current = current + timedelta(days=7)

                    # Remove duplicates (same week_label can appear from different dates)
                    seen_labels = set()
                    unique_weeks = []
                    for week_label, monday, sunday in weeks_to_calculate:
                        if week_label not in seen_labels:
                            seen_labels.add(week_label)
                            unique_weeks.append((week_label, monday, sunday))

                    weeks_to_calculate = unique_weeks
                    n_weeks = len(weeks_to_calculate)

                    logger.info(
                        f"Calculated {n_weeks} weeks from data range "
                        f"({earliest_date.date()} to {latest_date.date()})"
                    )
                else:
                    logger.warning(
                        "No dates found in cache, falling back to 52 weeks from today"
                    )
                    weeks_to_calculate = None
                    n_weeks = 52
            else:
                logger.warning("Cache not loaded, falling back to 52 weeks from today")
                weeks_to_calculate = None
                n_weeks = 52
        except Exception as e:
            logger.error(f"Error detecting data range: {e}", exc_info=True)
            weeks_to_calculate = None
            n_weeks = 52

        logger.info(
            f"Calculating metrics for {n_weeks} weeks based on actual data range. "
            f"Data Points slider ({data_points}) controls display only."
        )

        # Mark task as started
        TaskProgress.start_task(
            "calculate_metrics",
            f"Calculating {n_weeks} weeks of metrics",
            weeks=n_weeks,
        )

        # Import metrics calculator (now handles both Flow AND DORA metrics)
        from data.metrics_calculator import calculate_metrics_for_last_n_weeks

        # Calculate ALL metrics (Flow + DORA) using unified calculator
        # Pass custom weeks if we detected data range, otherwise let it use default (last N weeks from today)
        if weeks_to_calculate:
            success, message = calculate_metrics_for_last_n_weeks(
                n_weeks=n_weeks, custom_weeks=weeks_to_calculate
            )
        else:
            # Fallback to calculating last N weeks from today
            success, message = calculate_metrics_for_last_n_weeks(n_weeks=n_weeks)

        # Add forecasts to current week after metrics calculation (Feature 009)
        if success:
            from data.metrics_snapshots import add_forecasts_to_week
            from data.iso_week_bucketing import get_week_label

            current_week_label = get_week_label(datetime.now())
            logger.info(
                f"Adding forecasts to week {current_week_label} after metrics calculation"
            )

            forecast_success = add_forecasts_to_week(current_week_label)
            if forecast_success:
                logger.info(f"Successfully added forecasts to {current_week_label}")
            else:
                logger.warning(f"Failed to add forecasts to {current_week_label}")

        # Mark task as completed
        TaskProgress.complete_task("calculate_metrics")

        # Reset button to normal state
        button_normal = [
            html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
            "Calculate Metrics",
        ]

        # Extract actual weeks processed from the summary message
        # Message format: "[OK] Successfully calculated metrics for all X weeks (YYYY-WW to YYYY-WW)"
        actual_weeks_processed = n_weeks  # Default to requested weeks
        if "calculated metrics for all" in message.lower():
            import re

            match = re.search(r"all (\d+) weeks", message)
            if match:
                actual_weeks_processed = int(match.group(1))
        elif "calculated metrics for" in message.lower():
            # Handle partial success: "Calculated metrics for X/Y weeks"
            import re

            match = re.search(r"for (\d+)/(\d+) weeks", message)
            if match:
                actual_weeks_processed = int(match.group(1))

        if success:
            # Create success message with icon matching Update Data format
            settings_status_html = html.Div(
                [
                    html.I(className="fas fa-check-circle me-2 text-success"),
                    html.Span(
                        f"Calculated {actual_weeks_processed} weeks of Flow & DORA metrics",
                        className="fw-medium",
                    ),
                ],
                className="text-success small text-center mt-2",
            )

            logger.info(
                f"Flow & DORA metrics calculation completed successfully: {actual_weeks_processed} weeks processed (requested {n_weeks})"
            )

            # Trigger refresh of Flow and DORA tabs with timestamp
            refresh_timestamp = datetime.now().isoformat()
            return settings_status_html, False, button_normal, refresh_timestamp
        else:
            # Create warning message with icon
            settings_status_html = html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                    html.Span(
                        "Metrics calculated with warnings (check logs)",
                        className="fw-medium",
                    ),
                ],
                className="text-warning small text-center mt-2",
            )

            logger.warning("Flow & DORA metrics calculation had issues")

            # Still trigger refresh even with warnings (data was calculated)
            refresh_timestamp = datetime.now().isoformat()
            return settings_status_html, False, button_normal, refresh_timestamp

    except Exception as e:
        # Mark task as failed
        from data.task_progress import TaskProgress

        TaskProgress.complete_task("calculate_metrics")

        error_msg = f"Error calculating metrics: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Create error message with icon
        settings_status_html = html.Div(
            [
                html.I(className="fas fa-times-circle me-2 text-danger"),
                html.Span(
                    f"Calculation failed: {str(e)[:50]}",
                    className="fw-medium",
                ),
            ],
            className="text-danger small text-center mt-2",
        )

        # Reset button to normal state
        button_normal = [
            html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
            "Calculate Metrics",
        ]

        # No refresh trigger on error (data may be invalid)
        return settings_status_html, False, button_normal, None


#######################################################################
# METRIC DETAIL CHART COLLAPSE CALLBACKS
#######################################################################


@callback(
    Output("flow_velocity-details-collapse", "is_open"),
    Input("flow_velocity-details-btn", "n_clicks"),
    State("flow_velocity-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_flow_velocity_details(n_clicks, is_open):
    """Toggle Flow Velocity detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("flow_time-details-collapse", "is_open"),
    Input("flow_time-details-btn", "n_clicks"),
    State("flow_time-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_flow_time_details(n_clicks, is_open):
    """Toggle Flow Time detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("flow_efficiency-details-collapse", "is_open"),
    Input("flow_efficiency-details-btn", "n_clicks"),
    State("flow_efficiency-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_flow_efficiency_details(n_clicks, is_open):
    """Toggle Flow Efficiency detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("flow_load-details-collapse", "is_open"),
    Input("flow_load-details-btn", "n_clicks"),
    State("flow_load-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_flow_load_details(n_clicks, is_open):
    """Toggle Flow Load detailed chart collapse."""
    return not is_open if n_clicks else is_open


#######################################################################
# DORA METRIC DETAIL CHART COLLAPSE CALLBACKS
#######################################################################


@callback(
    Output("lead_time_for_changes-details-collapse", "is_open"),
    Input("lead_time_for_changes-details-btn", "n_clicks"),
    State("lead_time_for_changes-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_lead_time_details(n_clicks, is_open):
    """Toggle Lead Time for Changes detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("deployment_frequency-details-collapse", "is_open"),
    Input("deployment_frequency-details-btn", "n_clicks"),
    State("deployment_frequency-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_deployment_frequency_details(n_clicks, is_open):
    """Toggle Deployment Frequency detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("change_failure_rate-details-collapse", "is_open"),
    Input("change_failure_rate-details-btn", "n_clicks"),
    State("change_failure_rate-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_change_failure_rate_details(n_clicks, is_open):
    """Toggle Change Failure Rate detailed chart collapse."""
    return not is_open if n_clicks else is_open


@callback(
    Output("mean_time_to_recovery-details-collapse", "is_open"),
    Input("mean_time_to_recovery-details-btn", "n_clicks"),
    State("mean_time_to_recovery-details-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_mean_time_to_recovery_details(n_clicks, is_open):
    """Toggle Mean Time to Recovery detailed chart collapse."""
    return not is_open if n_clicks else is_open


#######################################################################
# TASK PROGRESS RESTORATION ON PAGE LOAD
#######################################################################


@callback(
    [
        Output("calculate-metrics-button", "disabled", allow_duplicate=True),
        Output("calculate-metrics-button", "children", allow_duplicate=True),
        Output("calculate-metrics-status", "children", allow_duplicate=True),
    ],
    Input("url", "pathname"),
    prevent_initial_call="initial_duplicate",  # Run on initial page load with duplicates
)
def restore_calculate_metrics_progress(pathname):
    """Restore Calculate Metrics button state if task is in progress.

    This callback runs on page load to check if a Calculate Metrics task
    was in progress before the page was refreshed or app restarted.
    If so, it restores the loading state and status message.

    Args:
        pathname: Current URL pathname (triggers on page load)

    Returns:
        Tuple of (button disabled state, button children, status message)
    """
    from data.task_progress import TaskProgress

    # Check if Calculate Metrics task is active
    active_task = TaskProgress.get_active_task()

    if active_task and active_task.get("task_id") == "calculate_metrics":
        # Task is in progress - restore loading state
        logger.info("Restoring Calculate Metrics progress state on page load")

        button_loading = [
            html.I(className="fas fa-spinner fa-spin", style={"marginRight": "0.5rem"}),
            "Calculating...",
        ]

        status_message = html.Div(
            [
                html.I(className="fas fa-spinner fa-spin me-2 text-primary"),
                html.Span(
                    TaskProgress.get_task_status_message("calculate_metrics")
                    or "Calculating metrics...",
                    className="fw-medium",
                ),
            ],
            className="text-primary small text-center mt-2",
        )

        return True, button_loading, status_message

    # No active task - return normal state
    button_normal = [
        html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
        "Calculate Metrics",
    ]

    return False, button_normal, ""
