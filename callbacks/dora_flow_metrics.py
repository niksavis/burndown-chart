"""DORA and Flow Metrics Dashboard Callbacks.

Handles metric calculations and display for DORA and Flow dashboards.
Uses ISO week bucketing (Monday-Sunday) with Data Points slider controlling display period.
Matches architecture of existing burndown/statistics dashboards.

All field mappings and configuration values come from app_settings.json - no hardcoded values.
"""

from dash import callback, Output, Input, State, html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import logging

from data.iso_week_bucketing import (
    bucket_issues_by_week,
    get_week_range_description,
)
from data.dora_calculator import (
    calculate_deployment_frequency_v2,
    calculate_lead_time_for_changes_v2,
    calculate_change_failure_rate_v2,
    calculate_mttr_v2,
)

# project_filter functions will be used when implementing operational task filtering for DORA
from data.persistence import load_app_settings
from ui.metric_cards import create_metric_cards_grid

logger = logging.getLogger(__name__)


#######################################################################
# DORA METRICS CALLBACK
#######################################################################


@callback(
    [
        Output("dora-metrics-cards-container", "children"),
        Output("dora-loading-state", "children"),
    ],
    [
        Input("jira-issues-store", "data"),
        Input("data-points-input", "value"),
    ],
    [
        State("current-settings", "data"),
    ],
    prevent_initial_call=False,
)
def calculate_and_display_dora_metrics(
    jira_data_store: Optional[Dict[str, Any]],
    data_points: int,
    app_settings: Optional[Dict[str, Any]],
):
    """Calculate and display DORA metrics per ISO week.

    Uses Data Points slider to control how many weeks of historical data to display.
    Metrics calculated per ISO week (Monday-Sunday boundaries).

    Args:
        jira_data_store: Cached JIRA issues from global store
        data_points: Number of weeks to display (from Data Points slider)
        app_settings: Application settings including field mappings

    Returns:
        Tuple of (metrics_cards_html, loading_state_html)
    """
    try:
        # Validate inputs
        if not jira_data_store or not jira_data_store.get("issues"):
            empty_state = create_metric_cards_grid(
                {
                    "deployment_frequency": {
                        "metric_name": "deployment_frequency",
                        "value": None,
                        "error_state": "no_data",
                        "error_message": "No JIRA data available. Click 'Update Data' in Settings.",
                    },
                    "lead_time_for_changes": {
                        "metric_name": "lead_time_for_changes",
                        "value": None,
                        "error_state": "no_data",
                    },
                    "change_failure_rate": {
                        "metric_name": "change_failure_rate",
                        "value": None,
                        "error_state": "no_data",
                    },
                    "mean_time_to_recovery": {
                        "metric_name": "mean_time_to_recovery",
                        "value": None,
                        "error_state": "no_data",
                    },
                }
            )

            info_message = html.Div(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "No JIRA data loaded. Click 'Update Data' in Settings to load data.",
                ],
                className="alert alert-info",
            )

            return empty_state, info_message

        # Get issues directly - calculators expect dicts, not objects
        all_issues = jira_data_store.get("issues", [])
        logger.info(f"DORA: Processing {len(all_issues)} issues from jira-issues-store")

        if not app_settings:
            logger.warning("No app settings available, loading from disk")
            app_settings = load_app_settings()

        # Ensure we have app_settings (for type checker)
        if not app_settings:
            error_msg = "Failed to load app settings"
            logger.error(error_msg)
            return (
                create_metric_cards_grid(
                    {
                        "deployment_frequency": {
                            "metric_name": "deployment_frequency",
                            "value": None,
                            "error_state": "error",
                            "error_message": error_msg,
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
                ),
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        error_msg,
                    ],
                    className="alert alert-danger",
                ),
            )

        # Get number of weeks to display (default 12 if not set)
        n_weeks = data_points if data_points and data_points > 0 else 12

        # Get settings
        devops_projects = app_settings.get("devops_projects", [])
        field_mappings = app_settings.get("field_mappings", {}).get("dora", {})

        # Filter to DevOps projects only (dict format)
        devops_issues = [
            issue
            for issue in all_issues
            if issue.get("fields", {}).get("project", {}).get("key") in devops_projects
        ]

        if not devops_issues:
            warning_state = create_metric_cards_grid(
                {
                    "deployment_frequency": {
                        "metric_name": "deployment_frequency",
                        "value": None,
                        "error_state": "no_data",
                        "error_message": f"No issues in DevOps projects: {', '.join(devops_projects)}",
                    },
                    "lead_time_for_changes": {
                        "metric_name": "lead_time_for_changes",
                        "value": None,
                        "error_state": "no_data",
                    },
                    "change_failure_rate": {
                        "metric_name": "change_failure_rate",
                        "value": None,
                        "error_state": "no_data",
                    },
                    "mean_time_to_recovery": {
                        "metric_name": "mean_time_to_recovery",
                        "value": None,
                        "error_state": "no_data",
                    },
                }
            )

            warning_message = html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"No issues found in DevOps projects: {', '.join(devops_projects)}",
                ],
                className="alert alert-warning",
            )

            return warning_state, warning_message

        # Get configuration values (no defaults - must be configured)
        change_failure_field = field_mappings.get("deployment_successful")
        affected_env_field = field_mappings.get("affected_environment")
        production_value = app_settings.get("production_environment_value", "PROD")

        # Calculate date range for metrics (last N weeks)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=n_weeks * 7)

        # Bucket issues by ISO week (for future trend analysis)
        _ = bucket_issues_by_week(
            devops_issues, date_field="resolutiondate", n_weeks=n_weeks
        )

        # Separate development and operational issues
        # Development projects from all issues
        dev_projects = [
            p for p in app_settings.get("projects", []) if p not in devops_projects
        ]
        if not dev_projects:
            # Fallback: assume all non-devops projects are development
            all_projects = set(
                issue.get("fields", {}).get("project", {}).get("key")
                for issue in all_issues
            )
            dev_projects = list(all_projects - set(devops_projects))

        development_issues = [
            issue
            for issue in all_issues
            if issue.get("fields", {}).get("project", {}).get("key") in dev_projects
        ]

        operational_tasks = devops_issues  # DevOps project issues are operational tasks

        # Extract bugs for MTTR
        production_bugs = [
            issue
            for issue in development_issues
            if issue.get("fields", {}).get("issuetype", {}).get("name") == "Bug"
        ]

        # Calculate date range for metrics (last N weeks)
        start_date = end_date - timedelta(days=n_weeks * 7)

        # Calculate DORA metrics for entire period
        deployment_freq = calculate_deployment_frequency_v2(
            operational_tasks,
            start_date=start_date,
            end_date=end_date,
        )

        lead_time = calculate_lead_time_for_changes_v2(
            development_issues,
            operational_tasks,
            start_date=start_date,
            end_date=end_date,
        )

        cfr = calculate_change_failure_rate_v2(
            operational_tasks,
            change_failure_field_id=change_failure_field,
            start_date=start_date,
            end_date=end_date,
        )

        mttr = calculate_mttr_v2(
            production_bugs,
            operational_tasks,
            affected_environment_field_id=affected_env_field,
            production_value=production_value,
            start_date=start_date,
            end_date=end_date,
        )

        # TODO: Calculate weekly aggregates for trend visualization
        # For now, create simple trend data showing current value
        # This will be enhanced in Phase 3 with proper weekly bucketing

        # Create metric cards with placeholder trend data
        metrics_data = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": deployment_freq.get("deployment_count", 0),
                "unit": "deployments",
                "error_state": None
                if deployment_freq.get("deployment_count")
                else "no_data",
            },
            "lead_time_for_changes": {
                "metric_name": "lead_time_for_changes",
                "value": round(
                    lead_time.get("median_hours", 0) / 24, 1
                )  # Convert hours to days
                if lead_time.get("median_hours")
                else None,
                "unit": "days",
                "error_state": None
                if lead_time.get("median_hours") is not None
                else "no_data",
            },
            "change_failure_rate": {
                "metric_name": "change_failure_rate",
                "value": round(cfr.get("change_failure_rate_percent", 0), 1),
                "unit": "%",
                "error_state": None
                if cfr.get("total_deployments", 0) > 0
                else "no_data",
            },
            "mean_time_to_recovery": {
                "metric_name": "mean_time_to_recovery",
                "value": round(mttr.get("median_hours", 0), 1)
                if mttr.get("median_hours")
                else None,
                "unit": "hours",
                "error_state": None
                if mttr.get("median_hours") is not None
                else "no_data",
            },
        }

        # Create success message
        week_range = get_week_range_description(n_weeks)
        success_message = html.Div(
            [
                html.I(className="fas fa-check-circle me-2"),
                f"DORA metrics calculated for {week_range}. ",
                f"Analyzed {len(devops_issues)} issues from DevOps projects.",
            ],
            className="alert alert-success",
        )

        return create_metric_cards_grid(metrics_data), success_message

    except Exception as e:
        logger.error(f"Error calculating DORA metrics: {e}", exc_info=True)

        error_state = create_metric_cards_grid(
            {
                "deployment_frequency": {
                    "metric_name": "deployment_frequency",
                    "value": None,
                    "error_state": "error",
                    "error_message": "Calculation error - check logs",
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

        error_message = html.Div(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Error: {str(e)}",
            ],
            className="alert alert-danger",
        )

        return error_state, error_message


#######################################################################
# FLOW METRICS CALLBACK (SNAPSHOT-BASED)
#######################################################################


def _create_no_data_state() -> html.Div:
    """Create UI for when no JIRA data is available."""
    return html.Div(
        [
            html.I(className="fas fa-database fa-3x text-muted mb-3"),
            html.H5("No Data Available", className="text-muted mb-2"),
            html.P(
                "No JIRA data found. Click 'Update Data' in Settings to load project data.",
                className="text-muted",
            ),
        ],
        className="text-center p-5",
    )


def _create_missing_metrics_state(week_label: str) -> html.Div:
    """Create UI for when metrics snapshots are missing."""
    return html.Div(
        [
            html.I(className="fas fa-chart-line fa-3x text-warning mb-3"),
            html.H5("Metrics Not Available", className="text-dark mb-2"),
            html.P(
                f"Flow metrics for week {week_label} have not been calculated yet.",
                className="text-muted mb-3",
            ),
            html.P(
                [
                    "Click the ",
                    html.Strong("Refresh Metrics"),
                    " button below to calculate metrics from changelog data. ",
                    "This will take approximately 2 minutes.",
                ],
                className="text-muted mb-4",
            ),
            html.Div(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Metrics are calculated once per week and cached for instant display on future page loads.",
                ],
                className="alert alert-info",
            ),
        ],
        className="text-center p-5",
    )


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
            return (
                _create_no_data_state(),
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
            logger.warning(
                f"No Flow metrics snapshot found for week {current_week_label or 'unknown'}"
            )
            return (
                _create_missing_metrics_state(current_week_label or "current"),
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

        metrics_html = create_metric_cards_grid(metrics_data)

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
    Output("calculate-metrics-status", "children"),
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

    Note: Metrics are saved to cache file. When user opens Flow Metrics tab,
    it will automatically load the cached data. No need to trigger refresh
    since the Flow Metrics tab may not be loaded yet.

    Args:
        button_clicks: Number of times the Settings button has been clicked
        data_points: Number of weeks to calculate (from Data Points slider)

    Returns:
        Status message for Settings panel
    """
    # Check if button was clicked
    if not button_clicks:
        return ""

    try:
        # Show loading state
        logger.info("Starting Flow metrics calculation from Settings panel")

        # Import metrics calculator
        from data.metrics_calculator import calculate_metrics_for_last_n_weeks

        # Calculate metrics for the selected number of weeks
        # Default to 12 weeks if data_points is not set
        n_weeks = data_points if data_points and data_points > 0 else 12
        logger.info(
            f"Calculating metrics for {n_weeks} weeks (data_points={data_points})"
        )

        success, message = calculate_metrics_for_last_n_weeks(n_weeks=n_weeks)

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
                f"Flow metrics calculation completed successfully: {n_weeks} weeks"
            )

            return settings_status_html
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

            logger.warning("Flow metrics calculation had issues")

            return settings_status_html

    except Exception as e:
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

        return settings_status_html


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
