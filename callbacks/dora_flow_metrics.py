"""DORA and Flow Metrics Dashboard Callbacks.

Handles metric calculations and display for DORA and Flow dashboards.
Uses ISO week bucketing (Monday-Sunday) with Data Points slider controlling display period.
Matches architecture of existing burndown/statistics dashboards.

All field mappings and configuration values come from app_settings.json - no hardcoded values.
"""

from dash import callback, Output, Input, State, html, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from data.persistence import load_app_settings
from ui.metric_cards import create_metric_cards_grid
from configuration.help_content import FLOW_METRICS_TOOLTIPS, DORA_METRICS_TOOLTIPS

logger = logging.getLogger(__name__)


#######################################################################
# DORA METRICS CALLBACK
#######################################################################


@callback(
    Output("dora-metrics-cards-container", "children"),
    [
        Input("chart-tabs", "active_tab"),
        Input("data-points-input", "value"),
        Input("metrics-refresh-trigger", "data"),  # Trigger refresh after calculation
    ],
    prevent_initial_call=False,
)
def load_and_display_dora_metrics(
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
        active_tab: Currently active tab (only process if DORA tab is active)
        data_points: Number of weeks to display (from Data Points slider)

    Returns:
        Metrics cards HTML (no toast messages, consistent with Flow Metrics)
    """
    try:
        # Only process if DORA tab is active (optimization)
        if active_tab != "tab-dora-metrics":
            raise PreventUpdate

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

        metrics_data = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": cached_metrics.get("deployment_frequency", {}).get("value", 0),
                "release_value": cached_metrics.get("deployment_frequency", {}).get(
                    "release_value", 0
                ),  # NEW
                "unit": f"deployments/week (avg {n_weeks_display}w)",
                "error_state": "success",
                "total_issue_count": cached_metrics.get("deployment_frequency", {}).get(
                    "total_issue_count", 0
                ),
                "tooltip": f"{DORA_METRICS_TOOLTIPS.get('deployment_frequency', '')} Average calculated over last {n_weeks_display} weeks. Deployment = operational task, Release = unique fixVersion.",
                "weekly_labels": cached_metrics.get("deployment_frequency", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": cached_metrics.get("deployment_frequency", {}).get(
                    "weekly_values", []
                ),
            },
            "lead_time_for_changes": {
                "metric_name": "lead_time_for_changes",
                "value": cached_metrics.get("lead_time_for_changes", {}).get("value"),
                "unit": f"days (avg {n_weeks_display}w)",
                "error_state": "success"
                if cached_metrics.get("lead_time_for_changes", {}).get("value")
                is not None
                else "no_data",
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
                "unit": f"% (agg {n_weeks_display}w)",
                "error_state": "success",
                "total_issue_count": cached_metrics.get("change_failure_rate", {}).get(
                    "total_issue_count", 0
                ),
                "tooltip": f"{DORA_METRICS_TOOLTIPS.get('change_failure_rate', '')} Aggregate rate calculated over last {n_weeks_display} weeks.",
                "weekly_labels": cached_metrics.get("change_failure_rate", {}).get(
                    "weekly_labels", []
                ),
                "weekly_values": cached_metrics.get("change_failure_rate", {}).get(
                    "weekly_values", []
                ),
            },
            "mean_time_to_recovery": {
                "metric_name": "mean_time_to_recovery",
                "value": cached_metrics.get("mean_time_to_recovery", {}).get("value"),
                "unit": f"hours (avg {n_weeks_display}w)",
                "error_state": "success"
                if cached_metrics.get("mean_time_to_recovery", {}).get("value")
                is not None
                else "no_data",
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
    [
        Output("flow-metrics-cards-container", "children"),
        Output("flow-distribution-chart-container", "children"),
    ],
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

            return (
                create_no_data_state(),
                html.Div("No distribution data", className="text-muted p-4"),
            )

        if not app_settings:
            logger.warning("No app settings available, loading from disk")
            app_settings = load_app_settings()

        # Ensure we have app_settings (for type checker)
        if not app_settings:
            error_msg = "Failed to load app settings"
            logger.error(error_msg)
            return (
                html.Div(error_msg, className="alert alert-danger p-4"),
                html.Div("Error", className="text-muted p-4"),
            )

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

        # Check if current week has snapshots (use flow_velocity as it's always saved)
        if not current_week_label or not has_metric_snapshot(
            current_week_label, "flow_velocity"
        ):
            from ui.empty_states import create_no_metrics_state

            logger.warning(
                f"No Flow metrics snapshot found for week {current_week_label or 'unknown'}"
            )
            return (
                create_no_metrics_state(metric_type="Flow"),
                html.Div(
                    "No distribution data available. Please refresh metrics.",
                    className="text-muted p-4",
                ),
            )

        # READ METRICS FROM SNAPSHOTS (instant, no calculation)
        from data.metrics_snapshots import get_metric_snapshot

        # Get current week metrics
        flow_time_snapshot = get_metric_snapshot(current_week_label, "flow_time")
        flow_efficiency_snapshot = get_metric_snapshot(
            current_week_label, "flow_efficiency"
        )
        flow_load_snapshot = get_metric_snapshot(current_week_label, "flow_load")

        # Extract values from snapshots (with defaults)
        median_flow_time = (
            flow_time_snapshot.get("median_days", 0) if flow_time_snapshot else 0
        )
        median_efficiency = (
            flow_efficiency_snapshot.get("overall_pct", 0)
            if flow_efficiency_snapshot
            else 0
        )
        wip_count = flow_load_snapshot.get("wip_count", 0) if flow_load_snapshot else 0

        # Get Flow Velocity from snapshot
        flow_velocity_snapshot = get_metric_snapshot(
            current_week_label, "flow_velocity"
        )
        total_velocity = (
            flow_velocity_snapshot.get("completed_count", 0)
            if flow_velocity_snapshot
            else 0
        )

        # Work Distribution: Use current week (consistent with other Flow metrics)
        # Show current week even if 0, matching Flow Velocity, Time, Efficiency, Load behavior
        distribution = (
            flow_velocity_snapshot.get("distribution", {})
            if flow_velocity_snapshot
            else {}
        )
        feature_count = distribution.get("feature", 0)
        defect_count = distribution.get("defect", 0)
        tech_debt_count = distribution.get("tech_debt", 0)
        risk_count = distribution.get("risk", 0)

        # Use velocity snapshot for issue count (always available, even when flow_time is N/A)
        issues_in_period_count = (
            flow_velocity_snapshot.get("completed_count", 0)
            if flow_velocity_snapshot
            else 0
        )

        logger.info(
            f"Flow metrics from snapshot {current_week_label}: "
            f"Flow Time={median_flow_time:.1f}d, Efficiency={median_efficiency:.1f}%, WIP={wip_count}, "
            f"Completed={issues_in_period_count} issues"
        )

        # Load historical metric values from snapshots for sparklines
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

        # Collect historical distribution data for all weeks
        distribution_history = []
        for week in week_labels:
            week_snapshot = get_metric_snapshot(week, "flow_velocity")
            if week_snapshot:
                week_dist = week_snapshot.get("distribution", {})
                distribution_history.append(
                    {
                        "week": week,
                        "feature": week_dist.get("feature", 0),
                        "defect": week_dist.get("defect", 0),
                        "tech_debt": week_dist.get("tech_debt", 0),
                        "risk": week_dist.get("risk", 0),
                        "total": week_snapshot.get("completed_count", 0),
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

        # Create distribution chart section with current week summary
        dist_html = dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5(
                                        f"Work Distribution Breakdown (Week {current_week_label})",
                                        className="mb-0",
                                    ),
                                    className="bg-light",
                                ),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Distribution of completed work across the four Flow item types. "
                                            "Recommended ranges: 40-60% Feature, 20-40% Defect, 10-20% Tech Debt, 0-10% Risk.",
                                            className="text-muted mb-3",
                                        ),
                                        # Current week summary with percentages and range indicators
                                        (
                                            lambda: (
                                                # Calculate percentages
                                                (
                                                    feature_pct := (
                                                        feature_count
                                                        / total_velocity
                                                        * 100
                                                    )
                                                    if total_velocity > 0
                                                    else 0
                                                ),
                                                (
                                                    defect_pct := (
                                                        defect_count
                                                        / total_velocity
                                                        * 100
                                                    )
                                                    if total_velocity > 0
                                                    else 0
                                                ),
                                                (
                                                    tech_debt_pct := (
                                                        tech_debt_count
                                                        / total_velocity
                                                        * 100
                                                    )
                                                    if total_velocity > 0
                                                    else 0
                                                ),
                                                (
                                                    risk_pct := (
                                                        risk_count
                                                        / total_velocity
                                                        * 100
                                                    )
                                                    if total_velocity > 0
                                                    else 0
                                                ),
                                                # Check if within recommended ranges
                                                (
                                                    feature_in_range := 40
                                                    <= feature_pct
                                                    <= 60
                                                ),
                                                (
                                                    defect_in_range := 20
                                                    <= defect_pct
                                                    <= 40
                                                ),
                                                (
                                                    tech_debt_in_range := 10
                                                    <= tech_debt_pct
                                                    <= 20
                                                ),
                                                (risk_in_range := 0 <= risk_pct <= 10),
                                                # Create UI
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.Div(
                                                                            [
                                                                                html.Span(
                                                                                    "Feature",
                                                                                    className="small text-muted d-block",
                                                                                ),
                                                                                html.Span(
                                                                                    f"{feature_count} ",
                                                                                    className="h4 mb-0",
                                                                                    style={
                                                                                        "color": "#198754"
                                                                                    },
                                                                                ),
                                                                                html.Span(
                                                                                    f"({feature_pct:.0f}%)",
                                                                                    className="h6 mb-0",
                                                                                    style={
                                                                                        "color": "#198754"
                                                                                    },
                                                                                ),
                                                                            ]
                                                                        ),
                                                                        html.Small(
                                                                            [
                                                                                html.I(
                                                                                    className=f"fas fa-{'check-circle text-success' if feature_in_range else 'exclamation-triangle text-warning'} me-1"
                                                                                ),
                                                                                html.Span(
                                                                                    "40-60%",
                                                                                    className="text-muted",
                                                                                ),
                                                                            ],
                                                                            className="d-block mt-1",
                                                                        ),
                                                                    ]
                                                                ),
                                                            ],
                                                            width=3,
                                                            className="text-center mb-3",
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.Div(
                                                                            [
                                                                                html.Span(
                                                                                    "Defect",
                                                                                    className="small text-muted d-block",
                                                                                ),
                                                                                html.Span(
                                                                                    f"{defect_count} ",
                                                                                    className="h4 mb-0",
                                                                                    style={
                                                                                        "color": "#dc3545"
                                                                                    },
                                                                                ),
                                                                                html.Span(
                                                                                    f"({defect_pct:.0f}%)",
                                                                                    className="h6 mb-0",
                                                                                    style={
                                                                                        "color": "#dc3545"
                                                                                    },
                                                                                ),
                                                                            ]
                                                                        ),
                                                                        html.Small(
                                                                            [
                                                                                html.I(
                                                                                    className=f"fas fa-{'check-circle text-success' if defect_in_range else 'exclamation-triangle text-warning'} me-1"
                                                                                ),
                                                                                html.Span(
                                                                                    "20-40%",
                                                                                    className="text-muted",
                                                                                ),
                                                                            ],
                                                                            className="d-block mt-1",
                                                                        ),
                                                                    ]
                                                                ),
                                                            ],
                                                            width=3,
                                                            className="text-center mb-3",
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.Div(
                                                                            [
                                                                                html.Span(
                                                                                    "Tech Debt",
                                                                                    className="small text-muted d-block",
                                                                                ),
                                                                                html.Span(
                                                                                    f"{tech_debt_count} ",
                                                                                    className="h4 mb-0",
                                                                                    style={
                                                                                        "color": "#fd7e14"
                                                                                    },
                                                                                ),
                                                                                html.Span(
                                                                                    f"({tech_debt_pct:.0f}%)",
                                                                                    className="h6 mb-0",
                                                                                    style={
                                                                                        "color": "#fd7e14"
                                                                                    },
                                                                                ),
                                                                            ]
                                                                        ),
                                                                        html.Small(
                                                                            [
                                                                                html.I(
                                                                                    className=f"fas fa-{'check-circle text-success' if tech_debt_in_range else 'exclamation-triangle text-warning'} me-1"
                                                                                ),
                                                                                html.Span(
                                                                                    "10-20%",
                                                                                    className="text-muted",
                                                                                ),
                                                                            ],
                                                                            className="d-block mt-1",
                                                                        ),
                                                                    ]
                                                                ),
                                                            ],
                                                            width=3,
                                                            className="text-center mb-3",
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.Div(
                                                                            [
                                                                                html.Span(
                                                                                    "Risk",
                                                                                    className="small text-muted d-block",
                                                                                ),
                                                                                html.Span(
                                                                                    f"{risk_count} ",
                                                                                    className="h4 mb-0",
                                                                                    style={
                                                                                        "color": "#ffc107"
                                                                                    },
                                                                                ),
                                                                                html.Span(
                                                                                    f"({risk_pct:.0f}%)",
                                                                                    className="h6 mb-0",
                                                                                    style={
                                                                                        "color": "#ffc107"
                                                                                    },
                                                                                ),
                                                                            ]
                                                                        ),
                                                                        html.Small(
                                                                            [
                                                                                html.I(
                                                                                    className=f"fas fa-{'check-circle text-success' if risk_in_range else 'exclamation-triangle text-warning'} me-1"
                                                                                ),
                                                                                html.Span(
                                                                                    "0-10%",
                                                                                    className="text-muted",
                                                                                ),
                                                                            ],
                                                                            className="d-block mt-1",
                                                                        ),
                                                                    ]
                                                                ),
                                                            ],
                                                            width=3,
                                                            className="text-center mb-3",
                                                        ),
                                                    ],
                                                    className="mb-3",
                                                ),
                                            )[
                                                -1
                                            ]  # Return only the dbc.Row, discard calculation results
                                        )()
                                        if total_velocity > 0
                                        else html.P(
                                            "No completed work this week.",
                                            className="text-muted text-center mb-3",
                                        ),
                                        # Historical trend chart
                                        dcc.Graph(
                                            figure=fig,
                                            config={"displayModeBar": False},
                                        ),
                                    ]
                                ),
                            ],
                            className="mb-4",
                        ),
                    ],
                    width=12,
                ),
            ],
        )

        # Load velocity historical values
        velocity_values = get_metric_weekly_values(
            week_labels, "flow_velocity", "completed_count"
        )

        # Create metric cards using same component as DORA
        # Reading from snapshots - error_state is "success" if data exists

        # Get individual metric issue counts from snapshots (not all use velocity count)
        flow_time_issue_count = (
            flow_time_snapshot.get("completed_count", 0) if flow_time_snapshot else 0
        )
        flow_efficiency_issue_count = (
            flow_efficiency_snapshot.get("completed_count", 0)
            if flow_efficiency_snapshot
            else 0
        )

        metrics_data = {
            "flow_velocity": {
                "metric_name": "flow_velocity",
                "value": total_velocity,
                "unit": "items/week",
                "error_state": "success",  # Always valid - 0 velocity is acceptable
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
                "unit": "days (median)",
                "error_state": "success",  # Always success - 0 is valid for weeks with no completions
                "total_issue_count": flow_time_issue_count,  # Use Flow Time's own completed count
                "weekly_labels": week_labels,
                "weekly_values": flow_time_values,
            },
            "flow_efficiency": {
                "metric_name": "flow_efficiency",
                "value": round(median_efficiency, 1)
                if median_efficiency is not None
                else 0,
                "unit": "% (median)",
                "error_state": "success",  # Always success - 0 is valid for weeks with no completions
                "total_issue_count": flow_efficiency_issue_count,  # Use Flow Efficiency's own completed count
                "weekly_labels": week_labels,
                "weekly_values": flow_efficiency_values,
            },
            "flow_load": {
                "metric_name": "flow_load",
                "value": wip_count if wip_count is not None else 0,
                "unit": "items (current WIP)",
                "error_state": "success" if flow_load_snapshot else "no_data",
                "total_issue_count": wip_count,  # Use WIP count itself (not completion count)
                "weekly_labels": week_labels,
                "weekly_values": flow_load_values,
            },
        }

        # Pass Flow metrics tooltips to grid function
        metrics_html = create_metric_cards_grid(
            metrics_data, tooltips=FLOW_METRICS_TOOLTIPS
        )

        return metrics_html, dist_html

    except Exception as e:
        logger.error(f"Error calculating Flow metrics: {e}", exc_info=True)

        return (
            html.Div("Error loading metrics", className="alert alert-danger p-4"),
            html.Div("Error loading chart", className="text-muted p-4"),
        )


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
    prevent_initial_call=True,
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

        # FIXED: Always calculate 52 weeks (1 year) regardless of Data Points slider
        # The data_points slider controls display filtering only, not calculation scope
        # This ensures users can adjust the slider without recalculating metrics
        n_weeks = 52
        logger.info(
            f"Calculating metrics for {n_weeks} weeks (full year of data, data_points slider={data_points})"
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
        success, message = calculate_metrics_for_last_n_weeks(n_weeks=n_weeks)

        # Mark task as completed
        TaskProgress.complete_task("calculate_metrics")

        # Reset button to normal state
        button_normal = [
            html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
            "Calculate Metrics",
        ]

        if success:
            # Create success message with icon matching Update Data format
            settings_status_html = html.Div(
                [
                    html.I(className="fas fa-check-circle me-2 text-success"),
                    html.Span(
                        f"Calculated {n_weeks} weeks of Flow & DORA metrics",
                        className="fw-medium",
                    ),
                ],
                className="text-success small text-center mt-2",
            )

            logger.info(
                f"Flow & DORA metrics calculation completed successfully: {n_weeks} weeks"
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
# CLIENTSIDE CALLBACKS - Button Loading States
#######################################################################


def register_calculate_metrics_button_spinner(app):
    """Register clientside callback for Calculate Metrics button loading state.

    This mimics the Update Data button behavior - shows a spinning calculator
    icon during processing and monitors for completion.
    """
    app.clientside_callback(
        """
        function(n_clicks) {
            // Button state management for Calculate Metrics button
            if (n_clicks && n_clicks > 0) {
                setTimeout(function() {
                    const button = document.getElementById('calculate-metrics-button');
                    if (button) {
                        const originalDisabled = button.disabled;
                        
                        // Set loading state with spinning icon
                        button.disabled = true;
                        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Calculating...';
                        
                        // Reset button after completion
                        const resetButton = function() {
                            if (button && button.disabled) {
                                button.disabled = false;
                                button.innerHTML = '<i class="fas fa-calculator me-2"></i>Calculate Metrics';
                            }
                        };
                        
                        // Longer timeout for metrics calculation (2.5 minutes max)
                        setTimeout(resetButton, 150000);
                        
                        // Monitor for completion by watching status updates
                        const observer = new MutationObserver(function(mutations) {
                            const statusArea = document.getElementById('calculate-metrics-status');
                            if (statusArea) {
                                const content = statusArea.innerHTML.toLowerCase();
                                // Detect completion messages
                                if (content.includes('weeks') || 
                                    content.includes('partial') ||
                                    content.includes('error')) {
                                    setTimeout(resetButton, 500);
                                    observer.disconnect();
                                }
                            }
                        });
                        
                        const targetNode = document.getElementById('calculate-metrics-status');
                        if (targetNode) {
                            observer.observe(targetNode, { childList: true, subtree: true });
                        }
                    }
                }, 50);
            }
            return null;
        }
        """,
        Output("calculate-metrics-button", "title"),
        [Input("calculate-metrics-button", "n_clicks")],
        prevent_initial_call=True,
    )


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
