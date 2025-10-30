"""Callbacks for DORA and Flow metrics dashboard.

Handles user interactions and metric calculations for DORA/Flow dashboards.
Follows layered architecture: callbacks delegate to data layer for all business logic.
"""

from dash import callback, Output, Input, State, html, ALL, callback_context, no_update
import dash_bootstrap_components as dbc
from typing import Dict
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


def parse_time_period(
    time_period: str,
    custom_start: str | None = None,
    custom_end: str | None = None,
) -> tuple[datetime, datetime]:
    """Parse time period selection to actual date range.

    Args:
        time_period: Selected time period ('7', '30', '90', or 'custom')
        custom_start: Custom start date (ISO 8601) if time_period == 'custom'
        custom_end: Custom end date (ISO 8601) if time_period == 'custom'

    Returns:
        Tuple of (start_date, end_date) as timezone-aware datetime objects

    Raises:
        ValueError: If custom period selected but dates not provided
    """
    now = datetime.now(timezone.utc)

    if time_period == "custom":
        if not custom_start or not custom_end:
            # Fallback to last 30 days if custom selected but no dates
            logger.warning(
                "Custom period selected but no dates provided, falling back to 30 days"
            )
            return now - timedelta(days=30), now

        try:
            start = datetime.fromisoformat(custom_start.replace("Z", "+00:00"))
            end = datetime.fromisoformat(custom_end.replace("Z", "+00:00"))

            # Ensure timezone aware
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)

            return start, end
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing custom dates: {e}")
            return now - timedelta(days=30), now

    # Parse preset periods
    days = int(time_period) if time_period in ["7", "30", "90"] else 30
    return now - timedelta(days=days), now


def calculate_retrospective_trends(
    issues: list,
    metric_name: str,
    metric_type: str,
    field_mappings: dict,
    time_period_days: int,
    num_points: int = 8,
) -> list:
    """Calculate historical trend data by analyzing JIRA issues in time buckets.

    Instead of waiting for daily snapshots to accumulate, this function
    retrospectively calculates metrics for different time windows within
    the available JIRA data.

    Args:
        issues: List of JIRA issues from cache
        metric_name: Name of metric (e.g., 'flow_velocity', 'deployment_frequency')
        metric_type: Either 'dora_metrics' or 'flow_metrics'
        field_mappings: JIRA field mappings
        time_period_days: Total time period (e.g., 30, 90)
        num_points: Number of data points to generate (default: 8)

    Returns:
        List of {"date": "2025-10-01", "value": 5.2} dictionaries
    """
    from data.flow_calculator import (
        calculate_flow_velocity,
        calculate_flow_time,
        calculate_flow_efficiency,
        calculate_flow_load,
    )
    from data.dora_calculator import (
        calculate_deployment_frequency,
        calculate_lead_time_for_changes,
        calculate_change_failure_rate,
        calculate_mean_time_to_recovery,
    )

    # Calculate bucket size (e.g., 30 days / 8 points = ~4 days per bucket)
    bucket_days = max(1, time_period_days // num_points)

    trend_data = []
    now = datetime.now(timezone.utc)

    logger.info(
        f"Retrospective trends: metric={metric_name}, time_period={time_period_days}days, "
        f"num_points={num_points}, bucket_days={bucket_days}, total_issues={len(issues)}"
    )

    # Generate data points going backwards in time
    for i in range(num_points):
        # Calculate end date for this bucket (going backwards)
        bucket_end = now - timedelta(days=i * bucket_days)
        bucket_start = bucket_end - timedelta(days=bucket_days)

        # Filter issues to this time window based on resolution/completion date
        bucket_issues = [
            issue
            for issue in issues
            if issue.get("fields", {}).get("resolutiondate")
            and bucket_start
            <= datetime.fromisoformat(
                issue["fields"]["resolutiondate"].replace("Z", "+00:00")
            )
            < bucket_end
        ]

        logger.info(
            f"Bucket {i}: {bucket_start.date()} to {bucket_end.date()} - {len(bucket_issues)} issues"
        )

        if not bucket_issues:
            continue  # Skip empty buckets

        # Calculate metric for this bucket
        try:
            if metric_type == "flow_metrics":
                if metric_name == "flow_velocity":
                    result = calculate_flow_velocity(
                        bucket_issues, field_mappings, bucket_start, bucket_end
                    )
                elif metric_name == "flow_time":
                    result = calculate_flow_time(bucket_issues, field_mappings)
                elif metric_name == "flow_efficiency":
                    result = calculate_flow_efficiency(bucket_issues, field_mappings)
                elif metric_name == "flow_load":
                    result = calculate_flow_load(bucket_issues, field_mappings)
                else:
                    continue  # Skip unsupported metrics
            elif metric_type == "dora_metrics":
                if metric_name == "deployment_frequency":
                    result = calculate_deployment_frequency(
                        bucket_issues,
                        field_mappings,
                        bucket_days,
                        start_date=bucket_start,
                        end_date=bucket_end,
                    )
                elif metric_name == "lead_time_for_changes":
                    result = calculate_lead_time_for_changes(
                        bucket_issues, field_mappings, bucket_days
                    )
                elif metric_name == "change_failure_rate":
                    # CFR needs separate deployment and incident lists
                    deployment_issues = [
                        issue
                        for issue in bucket_issues
                        if issue.get("fields", {}).get(
                            field_mappings.get("deployment_date")
                        )
                    ]
                    incident_issues = [
                        issue
                        for issue in bucket_issues
                        if issue.get("fields", {}).get(
                            field_mappings.get("incident_start")
                        )
                    ]
                    result = calculate_change_failure_rate(
                        deployment_issues, incident_issues, field_mappings, bucket_days
                    )
                elif metric_name == "mean_time_to_recovery":
                    result = calculate_mean_time_to_recovery(
                        bucket_issues, field_mappings, bucket_days
                    )
                else:
                    continue  # Skip unsupported metrics
            else:
                continue

            # Extract value from result
            logger.info(
                f"Bucket {i} calculation result: error_state={result.get('error_state')}, "
                f"has_value={'value' in result}, value={result.get('value', 'N/A')}"
            )

            if result.get("error_state") == "success" and "value" in result:
                trend_data.append(
                    {"date": bucket_start.date().isoformat(), "value": result["value"]}
                )
            else:
                logger.warning(
                    f"Bucket {i} skipped: error_state={result.get('error_state')}, "
                    f"error_msg={result.get('error_message', 'N/A')}"
                )
        except Exception as e:
            logger.warning(
                f"Error calculating {metric_name} for bucket {bucket_start}: {e}"
            )
            continue

    # Reverse to show oldest first (chronological order)
    trend_data.reverse()

    logger.info(
        f"Generated {len(trend_data)} retrospective trend points for {metric_name}"
    )
    return trend_data


@callback(
    Output("dora-metrics-cards-container", "children"),
    Output("dora-loading-state", "children"),
    Output("dora-metrics-store", "data"),
    Input("dora-refresh-button", "n_clicks"),
    Input("dora-time-period-select", "value"),
    State("dora-date-range-picker", "start_date"),
    State("dora-date-range-picker", "end_date"),
    prevent_initial_call=False,
)
def update_dora_metrics(
    n_clicks: int | None,
    time_period: str,
    custom_start: str | None,
    custom_end: str | None,
) -> tuple:
    """Update DORA metrics display.

    T048: Now handles time period selection and custom date ranges.
    Delegates to data layer for metric calculation.

    Args:
        n_clicks: Number of refresh button clicks
        time_period: Selected time period ('7', '30', '90', or 'custom')
        custom_start: Custom start date (ISO 8601) if time_period == 'custom'
        custom_end: Custom end date (ISO 8601) if time_period == 'custom'

    Returns:
        Tuple of (metrics_cards, loading_state, metrics_store_data)
    """
    from ui.dora_metrics_dashboard import create_dora_loading_cards_grid

    try:
        # Parse time period to actual dates
        start_date, end_date = parse_time_period(time_period, custom_start, custom_end)

        logger.info(
            f"DORA metrics requested for period: {start_date.isoformat()} to {end_date.isoformat()}"
        )

        # Load field mappings
        from data.dora_calculator import calculate_all_dora_metrics
        from data.field_mapper import load_field_mappings
        from data.jira_simple import load_jira_cache
        from data.persistence import load_app_settings

        mappings_data = load_field_mappings()
        all_field_mappings = mappings_data.get("field_mappings", {})

        # Extract DORA-specific mappings from nested structure
        field_mappings = all_field_mappings.get("dora", {})

        if not field_mappings:
            warning_alert = dbc.Alert(
                [
                    html.H5(
                        "⚠️ Field Mappings Not Configured", className="alert-heading"
                    ),
                    html.P(
                        "Please configure field mappings in the Settings panel to enable DORA metrics calculation."
                    ),
                    html.Hr(),
                    html.P(
                        "Navigate to Settings → Field Mapping to set up required fields.",
                        className="mb-0",
                    ),
                ],
                color="warning",
                dismissable=True,
            )
            return create_dora_loading_cards_grid(), warning_alert, {}

        # Validate JIRA configuration for DORA compatibility
        from data.field_mapper import validate_dora_jira_compatibility

        validation_result = validate_dora_jira_compatibility(field_mappings)
        validation_mode = validation_result.get("validation_mode", "unknown")
        compatibility_level = validation_result.get("compatibility_level", "unknown")

        logger.info(
            f"DORA validation: mode={validation_mode}, compatibility={compatibility_level}, "
            f"errors={validation_result.get('error_count', 0)}"
        )

        # Get cached issues (from previous JIRA fetch)
        settings = load_app_settings()
        jql_query = settings.get("jql_query", "")
        cache_loaded, issues = load_jira_cache(current_jql_query=jql_query)

        if not cache_loaded or not issues:
            info_alert = dbc.Alert(
                [
                    html.H5("ℹ️ No Data Available", className="alert-heading"),
                    html.P(
                        "Please fetch data from JIRA first using the 'Update Data from JIRA' button in Settings."
                    ),
                ],
                color="info",
                dismissable=True,
            )
            return create_dora_loading_cards_grid(), info_alert, {}

        # CRITICAL: Filter out DevOps project issues for DORA metrics
        # DORA metrics should ONLY calculate from development project issues
        # DevOps project data is used ONLY for metadata extraction, not metric calculation
        devops_projects = settings.get("devops_projects", [])
        if devops_projects:
            from data.project_filter import filter_development_issues

            total_issues_count = len(issues)
            issues = filter_development_issues(issues, devops_projects)
            filtered_count = total_issues_count - len(issues)

            if filtered_count > 0:
                logger.info(
                    f"DORA: Filtered out {filtered_count} DevOps project issues from {total_issues_count} total. "
                    f"Using {len(issues)} development project issues for DORA metrics."
                )

        logger.info(f"Calculating DORA metrics for {len(issues)} issues")

        # Calculate DORA metrics (Note: will show error states for missing Apache Kafka fields)
        # Split issues into deployments and incidents for proper calculation
        issues_dict = {
            "deployments": issues,  # All issues (will filter by deployment_date field)
            "incidents": issues,  # All issues (will filter by incident fields)
        }

        metrics = calculate_all_dora_metrics(
            issues=issues_dict,
            field_mappings=field_mappings,
            time_period_days=int(time_period)
            if time_period in ["7", "30", "90"]
            else 30,
        )

        # Render metric cards with alternative names if in issue_tracker mode
        from ui.metric_cards import create_metric_card

        alternative_names = validation_result.get("recommended_interpretation", {})

        cards = []
        for metric_name, metric_data in metrics.items():
            # Use alternative name if in issue_tracker mode
            if validation_mode == "issue_tracker" and metric_name in alternative_names:
                metric_data["alternative_name"] = alternative_names[metric_name]
            card = create_metric_card(metric_data)
            cards.append(card)

        logger.info(
            f"DORA metrics calculated: {len(cards)} cards (mode: {validation_mode})"
        )

        # Save metrics snapshot for historical trend analysis (T017: Historical trend data storage)
        from data.persistence import save_metrics_snapshot

        time_period_days = int(time_period) if time_period in ["7", "30", "90"] else 30
        save_metrics_snapshot("dora_metrics", metrics, time_period_days)

        # Show validation-aware alert
        if validation_mode == "issue_tracker":
            info_alert = dbc.Alert(
                [
                    html.H5("ℹ️ Issue Tracker Mode", className="alert-heading"),
                    html.P(
                        "Your JIRA instance uses standard fields without DevOps-specific tracking. "
                        "Metrics are reinterpreted for workflow analysis:"
                    ),
                    html.Ul(
                        [
                            html.Li(f"{name} → {alt_name}")
                            for name, alt_name in alternative_names.items()
                            if name in metrics
                        ]
                    ),
                    html.Hr(),
                    html.P(
                        "To enable full DORA metrics, configure custom fields for deployment and incident tracking.",
                        className="mb-0 small",
                    ),
                ],
                color="info",
                dismissable=True,
            )
        elif compatibility_level == "partial":
            warning_count = validation_result.get("warning_count", 0)
            info_alert = dbc.Alert(
                [
                    html.H5("⚠️ Partial DevOps Tracking", className="alert-heading"),
                    html.P(
                        f"Some DORA fields are missing or using proxy mappings. {warning_count} warnings detected."
                    ),
                    html.P(
                        "Check Settings → Field Mapping for details.",
                        className="mb-0",
                    ),
                ],
                color="warning",
                dismissable=True,
            )
        else:
            # Full DevOps mode or no issues
            info_alert = html.Div()  # Empty div

        return cards, info_alert, metrics

    except Exception as e:
        logger.error(f"Error updating DORA metrics: {e}", exc_info=True)
        error_alert = dbc.Alert(
            f"Error loading DORA metrics: {str(e)}",
            color="danger",
            dismissable=True,
        )
        return create_dora_loading_cards_grid(), error_alert, {}


@callback(
    [
        Output("dora-custom-date-label", "style"),
        Output("dora-date-range-picker", "style"),
    ],
    Input("dora-time-period-select", "value"),
)
def toggle_custom_date_range(time_period: str) -> tuple:
    """Show/hide custom date range picker based on time period selection.

    Args:
        time_period: Selected time period value

    Returns:
        Tuple of style dictionaries for label and date picker
    """
    if time_period == "custom":
        return (
            {"display": "block"},  # Show label
            {"display": "block"},  # Show date picker
        )
    else:
        return (
            {"display": "none"},  # Hide label
            {"display": "none"},  # Hide date picker
        )


# ============================================================================
# Flow Metrics Callbacks
# ============================================================================


@callback(
    Output("flow-metrics-cards-container", "children"),
    Output("flow-loading-state", "children"),
    Output("flow-metrics-store", "data"),
    Input("flow-refresh-button", "n_clicks"),
    Input("flow-time-period-select", "value"),
    State("flow-date-range-picker", "start_date"),
    State("flow-date-range-picker", "end_date"),
    prevent_initial_call=False,
)
def update_flow_metrics(
    n_clicks: int | None,
    time_period: str,
    custom_start: str | None,
    custom_end: str | None,
) -> tuple:
    """Update Flow metrics display.

    T050: Now handles time period selection and custom date ranges.
    Delegates to data layer for metric calculation.

    Args:
        n_clicks: Number of refresh button clicks
        time_period: Selected time period ('7', '30', '90', or 'custom')
        custom_start: Custom start date (ISO 8601) if time_period == 'custom'
        custom_end: Custom end date (ISO 8601) if time_period == 'custom'

    Returns:
        Tuple of (metrics_cards, loading_state, metrics_store_data)
    """
    from ui.flow_metrics_dashboard import create_flow_loading_cards_grid
    from data.flow_calculator import calculate_all_flow_metrics
    from data.field_mapper import load_field_mappings
    from data.jira_simple import load_jira_cache
    from data.persistence import load_app_settings

    try:
        # Parse time period to actual dates
        start_date, end_date = parse_time_period(time_period, custom_start, custom_end)

        logger.info(
            f"Flow metrics requested for period: {start_date.isoformat()} to {end_date.isoformat()}"
        )

        # Load field mappings
        mappings_data = load_field_mappings()
        all_field_mappings = mappings_data.get("field_mappings", {})

        # Extract Flow-specific mappings from nested structure
        field_mappings = all_field_mappings.get("flow", {})

        if not field_mappings:
            warning_alert = dbc.Alert(
                [
                    html.H5(
                        "⚠️ Field Mappings Not Configured", className="alert-heading"
                    ),
                    html.P(
                        "Please configure field mappings in the Settings panel to enable Flow metrics calculation."
                    ),
                    html.Hr(),
                    html.P(
                        "Navigate to Settings → Field Mapping to set up required fields.",
                        className="mb-0",
                    ),
                ],
                color="warning",
                dismissable=True,
            )
            return create_flow_loading_cards_grid(), warning_alert, {}

        # Validate JIRA configuration for Flow compatibility
        from data.field_mapper import validate_dora_jira_compatibility

        validation_result = validate_dora_jira_compatibility(field_mappings)
        validation_mode = validation_result.get("validation_mode", "unknown")
        compatibility_level = validation_result.get("compatibility_level", "unknown")

        logger.info(
            f"Flow validation: mode={validation_mode}, compatibility={compatibility_level}"
        )

        # Get cached issues (from previous JIRA fetch)
        settings = load_app_settings()
        jql_query = settings.get("jql_query", "")
        cache_loaded, issues = load_jira_cache(current_jql_query=jql_query)

        if not cache_loaded or not issues:
            info_alert = dbc.Alert(
                [
                    html.H5("ℹ️ No Data Available", className="alert-heading"),
                    html.P(
                        "Please fetch data from JIRA first using the 'Update Data from JIRA' button in Settings."
                    ),
                ],
                color="info",
                dismissable=True,
            )
            return create_flow_loading_cards_grid(), info_alert, {}

        # CRITICAL: Filter out DevOps project issues for Flow metrics
        # Flow metrics should ONLY calculate from development project issues
        # DevOps project data is used ONLY for metadata extraction, not metric calculation
        devops_projects = settings.get("devops_projects", [])
        if devops_projects:
            from data.project_filter import filter_development_issues

            total_issues_count = len(issues)
            issues = filter_development_issues(issues, devops_projects)
            filtered_count = total_issues_count - len(issues)

            if filtered_count > 0:
                logger.info(
                    f"Flow: Filtered out {filtered_count} DevOps project issues from {total_issues_count} total. "
                    f"Using {len(issues)} development project issues for Flow metrics."
                )

        logger.info(f"Calculating Flow metrics for {len(issues)} issues")

        # Calculate all Flow metrics
        metrics = calculate_all_flow_metrics(
            issues=issues,
            field_mappings=field_mappings,
            start_date=start_date,
            end_date=end_date,
        )

        # Render metric cards with validation-aware alternative names
        from ui.metric_cards import create_metric_card

        # Get alternative interpretations for issue tracker mode
        alternative_names = validation_result.get("recommended_interpretation", {})

        cards = []
        for metric_name, metric_data in metrics.items():
            # Add alternative name if in issue tracker mode
            if validation_mode == "issue_tracker" and metric_name in alternative_names:
                metric_data["alternative_name"] = alternative_names[metric_name]

            card = create_metric_card(metric_data)
            cards.append(card)

        logger.info(
            f"Flow metrics calculated successfully: {len(cards)} cards (validation_mode={validation_mode})"
        )

        # Save metrics snapshot for historical trend analysis (T017: Historical trend data storage)
        from data.persistence import save_metrics_snapshot

        time_period_days = (end_date - start_date).days
        save_metrics_snapshot("flow_metrics", metrics, time_period_days)

        # Create validation-aware alerts
        if validation_mode == "issue_tracker":
            # Show alternative interpretation alert
            alert_content = [
                html.H5("ℹ️ Issue Tracker Mode", className="alert-heading"),
                html.P(
                    "Your JIRA instance appears to be configured as a standard issue tracker. "
                    "Flow metrics have been reinterpreted for workflow analysis:"
                ),
                html.Ul(
                    [
                        html.Li(f"{metric}: {alt_name}")
                        for metric, alt_name in alternative_names.items()
                    ]
                ),
                html.P(
                    "For DevOps metrics, configure proper deployment and incident tracking fields in Field Mapping.",
                    className="mb-0 small",
                ),
            ]
            success_alert = dbc.Alert(
                alert_content, color="info", dismissable=True, duration=8000
            )
        elif (
            validation_mode == "devops"
            and validation_result.get("compatibility_level") == "partial"
        ):
            # Show partial configuration warning
            success_alert = dbc.Alert(
                [
                    html.H5("⚠️ Partial DevOps Tracking", className="alert-heading"),
                    html.P(
                        f"✅ Flow metrics calculated for {len(issues)} issues. "
                        "Some DevOps fields are missing - configure remaining fields for complete metrics."
                    ),
                ],
                color="warning",
                dismissable=True,
                duration=6000,
            )
        else:
            # Full DevOps tracking or unknown - show simple success
            success_alert = dbc.Alert(
                f"✅ Flow metrics calculated successfully for {len(issues)} issues",
                color="success",
                dismissable=True,
                duration=4000,
            )

        return cards, success_alert, metrics

    except Exception as e:
        logger.error(f"Error updating Flow metrics: {e}", exc_info=True)
        error_alert = dbc.Alert(
            [
                html.H5("❌ Error Calculating Metrics", className="alert-heading"),
                html.P(f"Error: {str(e)}"),
                html.Hr(),
                html.P(
                    "Check browser console and server logs for details.",
                    className="mb-0",
                ),
            ],
            color="danger",
            dismissable=True,
        )
        return create_flow_loading_cards_grid(), error_alert, {}


@callback(
    [
        Output("flow-custom-date-label", "style"),
        Output("flow-date-range-picker", "style"),
    ],
    Input("flow-time-period-select", "value"),
)
def toggle_flow_custom_date_range(time_period: str) -> tuple:
    """Show/hide custom date range picker for Flow metrics.

    Args:
        time_period: Selected time period value

    Returns:
        Tuple of style dictionaries for label and date picker
    """
    if time_period == "custom":
        return (
            {"display": "block"},  # Show label
            {"display": "block"},  # Show date picker
        )
    else:
        return (
            {"display": "none"},  # Hide label
            {"display": "none"},  # Hide date picker
        )


@callback(
    Output("flow-distribution-chart-container", "children"),
    Input("flow-time-period-select", "value"),
    prevent_initial_call=False,
)
def update_flow_distribution_chart(time_period: str):
    """Update Flow Distribution chart.

    Args:
        time_period: Selected time period

    Returns:
        Flow distribution chart or error message
    """
    try:
        from datetime import datetime, timedelta, timezone
        from dash import dcc
        from data.flow_calculator import calculate_flow_distribution
        from data.field_mapper import load_field_mappings
        from data.jira_simple import load_jira_cache
        from visualization.flow_charts import create_flow_distribution_chart

        # Load field mappings
        mappings_data = load_field_mappings()
        all_field_mappings = mappings_data.get("field_mappings", {})

        # Extract Flow-specific mappings from nested structure
        field_mappings = all_field_mappings.get("flow", {})

        # Calculate time period boundaries
        time_period_days = int(time_period) if time_period.isdigit() else 30
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=time_period_days)

        # Load cached JIRA issues
        cache_loaded, issues = load_jira_cache()

        if not cache_loaded or not issues:
            return dbc.Alert(
                "No JIRA data available. Please configure JIRA and fetch data first.",
                color="warning",
            )

        # CRITICAL: Filter out DevOps project issues for Flow Distribution
        # Flow distribution should ONLY calculate from development project issues
        from data.persistence import load_app_settings

        settings = load_app_settings()
        devops_projects = settings.get("devops_projects", [])
        if devops_projects:
            from data.project_filter import filter_development_issues

            total_issues_count = len(issues)
            issues = filter_development_issues(issues, devops_projects)
            filtered_count = total_issues_count - len(issues)

            if filtered_count > 0:
                logger.info(
                    f"Flow Distribution: Filtered out {filtered_count} DevOps project issues from {total_issues_count} total. "
                    f"Using {len(issues)} development project issues."
                )

        # Calculate flow distribution
        distribution_data = calculate_flow_distribution(
            issues, field_mappings, start_date, end_date
        )

        # Handle error states
        error_state = distribution_data.get("error_state", "success")
        if error_state != "success":
            error_message = distribution_data.get(
                "error_message", "Unable to calculate distribution"
            )
            return dbc.Alert(error_message, color="warning")

        # Create and return chart
        fig = create_flow_distribution_chart(distribution_data)
        return dcc.Graph(figure=fig, config={"displayModeBar": False})

    except Exception as e:
        logger.error(f"Error updating flow distribution chart: {e}", exc_info=True)
        return dbc.Alert(
            f"Error generating distribution chart: {str(e)}",
            color="danger",
        )


@callback(
    Output("dora-flow-subtab-content", "children"),
    Input("dora-flow-subtabs", "active_tab"),
)
def switch_dora_flow_subtab(active_subtab: str):
    """Switch between DORA and Flow metrics dashboards.

    Args:
        active_subtab: Active sub-tab ID ('subtab-dora' or 'subtab-flow')

    Returns:
        Dashboard content for the selected sub-tab
    """
    if active_subtab == "subtab-flow":
        from ui.flow_metrics_dashboard import create_flow_dashboard

        return create_flow_dashboard()
    else:  # Default to DORA
        from ui.dora_metrics_dashboard import create_dora_dashboard

        return create_dora_dashboard()


@callback(
    Output({"type": "metric-trend-collapse", "metric": ALL}, "is_open"),
    Input({"type": "metric-trend-button", "metric": ALL}, "n_clicks"),
    State({"type": "metric-trend-collapse", "metric": ALL}, "is_open"),
    prevent_initial_call=True,
)
def toggle_trend_display(n_clicks_list, is_open_list):
    """Toggle trend chart visibility for metric cards using pattern matching.

    Args:
        n_clicks_list: List of n_clicks for each trend button
        is_open_list: Current is_open state for each trend collapse

    Returns:
        List of updated is_open states for each trend collapse
    """
    # Find which button was clicked using ctx.triggered_id
    if not callback_context.triggered:
        return is_open_list  # Return current state, don't use no_update with pattern-matching ALL

    triggered_id = callback_context.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict):
        return is_open_list

    # Get the metric name that was clicked
    clicked_metric = triggered_id.get("metric")
    if not clicked_metric:
        return is_open_list

    # Create result list with same length as inputs
    result = []

    # Get the list of output IDs from callback_context
    outputs_list = callback_context.outputs_list

    for i, output_spec in enumerate(outputs_list):
        # Extract the metric name from the output ID
        if isinstance(output_spec, dict) and "id" in output_spec:
            output_id = output_spec["id"]
            if isinstance(output_id, dict):
                metric_name = output_id.get("metric")
                # Get current state for this index
                current_state = is_open_list[i] if i < len(is_open_list) else False
                # Toggle if this is the clicked metric, otherwise keep unchanged
                new_state = (
                    not current_state
                    if metric_name == clicked_metric
                    else current_state
                )
                result.append(new_state)
            else:
                # Fallback: keep current state
                result.append(is_open_list[i] if i < len(is_open_list) else False)
        else:
            # Fallback: keep current state
            result.append(is_open_list[i] if i < len(is_open_list) else False)

    return result


@callback(
    [
        Output(
            {"type": "metric-trend-chart", "metric": "deployment_frequency"}, "children"
        ),
        Output(
            {"type": "metric-trend-chart", "metric": "lead_time_for_changes"},
            "children",
        ),
        Output(
            {"type": "metric-trend-chart", "metric": "change_failure_rate"}, "children"
        ),
        Output(
            {"type": "metric-trend-chart", "metric": "mean_time_to_recovery"},
            "children",
        ),
    ],
    [
        Input(
            {"type": "metric-trend-collapse", "metric": "deployment_frequency"},
            "is_open",
        ),
        Input(
            {"type": "metric-trend-collapse", "metric": "lead_time_for_changes"},
            "is_open",
        ),
        Input(
            {"type": "metric-trend-collapse", "metric": "change_failure_rate"},
            "is_open",
        ),
        Input(
            {"type": "metric-trend-collapse", "metric": "mean_time_to_recovery"},
            "is_open",
        ),
    ],
    State("dora-metrics-store", "data"),
    prevent_initial_call=True,
)
def render_dora_trend_charts(
    df_is_open, lt_is_open, cfr_is_open, mttr_is_open, dora_data
):
    """Render DORA trend charts when trend collapse is opened.

    Args:
        df_is_open: Deployment frequency collapse state
        lt_is_open: Lead time collapse state
        cfr_is_open: Change failure rate collapse state
        mttr_is_open: MTTR collapse state
        dora_data: DORA metrics data from store

    Returns:
        Tuple of chart components for each metric's trend-chart div
    """
    from dash import dcc
    from visualization.dora_charts import (
        create_deployment_frequency_chart,
        create_lead_time_chart,
        create_change_failure_rate_chart,
        create_mttr_chart,
    )

    results = []
    metrics = [
        ("deployment_frequency", df_is_open, create_deployment_frequency_chart),
        ("lead_time_for_changes", lt_is_open, create_lead_time_chart),
        ("change_failure_rate", cfr_is_open, create_change_failure_rate_chart),
        ("mean_time_to_recovery", mttr_is_open, create_mttr_chart),
    ]

    for metric_name, is_open, chart_func in metrics:
        if is_open and dora_data and metric_name in dora_data:
            try:
                metric_data = dora_data[metric_name]

                # Check if metric has error state (not "success" or None)
                error_state = metric_data.get("error_state")
                if error_state and error_state != "success":
                    results.append(
                        html.P(
                            f"Cannot display trend: {metric_data.get('error_message', 'No data available')}",
                            className="text-muted text-center my-3",
                        )
                    )
                else:
                    # Create chart with historical data
                    # Load historical trend data from persistence layer
                    from data.persistence import get_metric_trend_data

                    # Get time period from dora_data metadata (default to 30 days)
                    time_period_days = dora_data.get("time_period_days", 30)

                    # Get historical data for trend visualization
                    historical_data = get_metric_trend_data(
                        metric_type="dora_metrics",
                        metric_name=metric_name,
                        time_period_days=time_period_days,
                    )

                    # If insufficient historical data (< 3 points), calculate retrospective trends from JIRA cache
                    if not historical_data or len(historical_data) < 3:
                        logger.info(
                            f"Insufficient snapshot data ({len(historical_data) if historical_data else 0} points), "
                            f"calculating retrospective trends for {metric_name}"
                        )

                        # Load cached JIRA issues
                        from data.jira_simple import load_jira_cache
                        from data.field_mapper import load_field_mappings
                        from data.persistence import load_app_settings

                        # Get current JQL query and fields from settings to avoid cache invalidation
                        settings = load_app_settings()
                        current_jql = settings.get("jql_query", "")
                        points_field = settings.get("jira_config", {}).get(
                            "points_field", ""
                        )
                        base_fields = "key,created,resolutiondate,status,issuetype"
                        current_fields = (
                            f"{base_fields},{points_field}"
                            if points_field
                            else base_fields
                        )

                        # Load from cache (returns tuple: cache_loaded, issues)
                        cache_loaded, cached_issues = load_jira_cache(
                            current_jql, current_fields
                        )
                        mappings_data = load_field_mappings()
                        # Extract DORA-specific field mappings from nested structure
                        field_mappings = mappings_data.get("field_mappings", {}).get(
                            "dora", {}
                        )

                        if cache_loaded and cached_issues:
                            # CRITICAL: Filter out DevOps project issues for DORA trend calculation
                            devops_projects = settings.get("devops_projects", [])
                            if devops_projects:
                                from data.project_filter import (
                                    filter_development_issues,
                                )

                                total_issues_count = len(cached_issues)
                                cached_issues = filter_development_issues(
                                    cached_issues, devops_projects
                                )
                                filtered_count = total_issues_count - len(cached_issues)

                                if filtered_count > 0:
                                    logger.info(
                                        f"DORA Trend: Filtered out {filtered_count} DevOps project issues from {total_issues_count} total. "
                                        f"Using {len(cached_issues)} development project issues."
                                    )
                            historical_data = calculate_retrospective_trends(
                                issues=cached_issues,
                                metric_name=metric_name,
                                metric_type="dora_metrics",
                                field_mappings=field_mappings,
                                time_period_days=time_period_days,
                                num_points=8,
                            )

                    # Create chart with historical data (None if no history available)
                    figure = chart_func(
                        metric_data,
                        historical_data=historical_data if historical_data else None,
                    )
                    results.append(
                        dcc.Graph(
                            figure=figure,
                            config={"displayModeBar": False},
                            style={"height": "300px"},
                        )
                    )
            except Exception as e:
                logger.error(f"Error rendering trend chart for {metric_name}: {e}")
                results.append(
                    html.P(
                        "Error rendering chart",
                        className="text-danger text-center my-3",
                    )
                )
        else:
            # Not open or no data, return placeholder
            results.append(
                html.P(
                    "Trend chart will be displayed here",
                    className="text-muted text-center my-3",
                )
            )

    return tuple(results)


@callback(
    [
        Output({"type": "metric-trend-chart", "metric": "flow_velocity"}, "children"),
        Output({"type": "metric-trend-chart", "metric": "flow_time"}, "children"),
        Output({"type": "metric-trend-chart", "metric": "flow_efficiency"}, "children"),
        Output({"type": "metric-trend-chart", "metric": "flow_load"}, "children"),
        Output(
            {"type": "metric-trend-chart", "metric": "flow_distribution"}, "children"
        ),
    ],
    [
        Input({"type": "metric-trend-collapse", "metric": "flow_velocity"}, "is_open"),
        Input({"type": "metric-trend-collapse", "metric": "flow_time"}, "is_open"),
        Input(
            {"type": "metric-trend-collapse", "metric": "flow_efficiency"}, "is_open"
        ),
        Input({"type": "metric-trend-collapse", "metric": "flow_load"}, "is_open"),
        Input(
            {"type": "metric-trend-collapse", "metric": "flow_distribution"}, "is_open"
        ),
    ],
    State("flow-metrics-store", "data"),
    prevent_initial_call=True,
)
def render_flow_trend_charts(
    fv_is_open, ft_is_open, fe_is_open, fl_is_open, fd_is_open, flow_data
):
    """Render Flow trend charts when trend collapse is opened.

    Args:
        fv_is_open: Flow velocity collapse state
        ft_is_open: Flow time collapse state
        fe_is_open: Flow efficiency collapse state
        fl_is_open: Flow load collapse state
        fd_is_open: Flow distribution collapse state
        flow_data: Flow metrics data from store

    Returns:
        Tuple of chart components for each metric's trend-chart div
    """
    from dash import dcc
    from visualization.flow_charts import (
        create_flow_velocity_trend_chart,
        create_flow_time_trend_chart,
        create_flow_efficiency_trend_chart,
        create_flow_load_trend_chart,
        create_flow_distribution_chart,
    )

    results = []
    metrics = [
        ("flow_velocity", fv_is_open, create_flow_velocity_trend_chart),
        ("flow_time", ft_is_open, create_flow_time_trend_chart),
        ("flow_efficiency", fe_is_open, create_flow_efficiency_trend_chart),
        ("flow_load", fl_is_open, create_flow_load_trend_chart),
        ("flow_distribution", fd_is_open, create_flow_distribution_chart),
    ]

    for metric_name, is_open, chart_func in metrics:
        if is_open and flow_data and metric_name in flow_data:
            try:
                metric_data = flow_data[metric_name]

                # Check if metric has error state (not "success" or None)
                error_state = metric_data.get("error_state")
                if error_state and error_state != "success":
                    results.append(
                        html.P(
                            f"Cannot display trend: {metric_data.get('error_message', 'No data available')}",
                            className="text-muted text-center my-3",
                        )
                    )
                else:
                    # Create chart with historical data
                    # Load historical trend data from persistence layer
                    from data.persistence import get_metric_trend_data

                    # Get time period from flow_data metadata (default to 30 days)
                    time_period_days = flow_data.get("time_period_days", 30)

                    # Note: flow_distribution uses different function signature (just current data)
                    if metric_name == "flow_distribution":
                        figure = chart_func(metric_data)
                    else:
                        # Get historical data for trend visualization
                        historical_data = get_metric_trend_data(
                            metric_type="flow_metrics",
                            metric_name=metric_name,
                            time_period_days=time_period_days,
                        )

                        # If insufficient historical data (< 3 points), calculate retrospective trends from JIRA cache
                        if not historical_data or len(historical_data) < 3:
                            logger.info(
                                f"Insufficient snapshot data ({len(historical_data) if historical_data else 0} points), "
                                f"calculating retrospective trends for {metric_name}"
                            )

                            # Load cached JIRA issues
                            from data.jira_simple import load_jira_cache
                            from data.field_mapper import load_field_mappings
                            from data.persistence import load_app_settings

                            # Get current JQL query and fields from settings to avoid cache invalidation
                            settings = load_app_settings()
                            current_jql = settings.get("jql_query", "")
                            points_field = settings.get("jira_config", {}).get(
                                "points_field", ""
                            )
                            base_fields = "key,created,resolutiondate,status,issuetype"
                            current_fields = (
                                f"{base_fields},{points_field}"
                                if points_field
                                else base_fields
                            )

                            # Load from cache (returns tuple: cache_loaded, issues)
                            cache_loaded, cached_issues = load_jira_cache(
                                current_jql, current_fields
                            )
                            mappings_data = load_field_mappings()
                            # Extract Flow-specific field mappings from nested structure
                            field_mappings = mappings_data.get(
                                "field_mappings", {}
                            ).get("flow", {})

                            if cache_loaded and cached_issues:
                                # CRITICAL: Filter out DevOps project issues for Flow trend calculation
                                devops_projects = settings.get("devops_projects", [])
                                if devops_projects:
                                    from data.project_filter import (
                                        filter_development_issues,
                                    )

                                    total_issues_count = len(cached_issues)
                                    cached_issues = filter_development_issues(
                                        cached_issues, devops_projects
                                    )
                                    filtered_count = total_issues_count - len(
                                        cached_issues
                                    )

                                    if filtered_count > 0:
                                        logger.info(
                                            f"Flow Trend: Filtered out {filtered_count} DevOps project issues from {total_issues_count} total. "
                                            f"Using {len(cached_issues)} development project issues."
                                        )
                                historical_data = calculate_retrospective_trends(
                                    issues=cached_issues,
                                    metric_name=metric_name,
                                    metric_type="flow_metrics",
                                    field_mappings=field_mappings,
                                    time_period_days=time_period_days,
                                    num_points=8,
                                )

                        # If still no data, show single current point
                        if not historical_data:
                            historical_data = [
                                {
                                    "date": datetime.now().date().isoformat(),
                                    "value": metric_data.get("value", 0),
                                }
                            ]

                        figure = chart_func(historical_data)

                    results.append(
                        dcc.Graph(
                            figure=figure,
                            config={"displayModeBar": False},
                            style={"height": "300px"},
                        )
                    )
            except Exception as e:
                logger.error(f"Error rendering trend chart for {metric_name}: {e}")
                results.append(
                    html.P(
                        "Error rendering chart",
                        className="text-danger text-center my-3",
                    )
                )
        else:
            # Not open or no data, return placeholder
            results.append(
                html.P(
                    "Trend chart will be displayed here",
                    className="text-muted text-center my-3",
                )
            )

    return tuple(results)


# Export callbacks


@callback(
    Output("download-dora-csv", "data"),
    Input("export-dora-csv-button", "n_clicks"),
    State("dora-metrics-store", "data"),
    State("dora-time-period-select", "value"),
    prevent_initial_call=True,
)
def export_dora_csv(n_clicks, metrics_data, time_period):
    """Export DORA metrics to CSV format.

    Args:
        n_clicks: Button click counter (triggers callback)
        metrics_data: Current DORA metrics data from store
        time_period: Selected time period for context

    Returns:
        dict with filename and content for download
    """
    from data.metrics_export import export_dora_to_csv

    if not metrics_data:
        return no_update

    # Generate CSV content
    csv_content = export_dora_to_csv(metrics_data, f"{time_period} days")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dora_metrics_{timestamp}.csv"

    return {"content": csv_content, "filename": filename}


@callback(
    Output("download-dora-json", "data"),
    Input("export-dora-json-button", "n_clicks"),
    State("dora-metrics-store", "data"),
    State("dora-time-period-select", "value"),
    prevent_initial_call=True,
)
def export_dora_json(n_clicks, metrics_data, time_period):
    """Export DORA metrics to JSON format.

    Args:
        n_clicks: Button click counter (triggers callback)
        metrics_data: Current DORA metrics data from store
        time_period: Selected time period for context

    Returns:
        dict with filename and content for download
    """
    from data.metrics_export import export_dora_to_json

    if not metrics_data:
        return no_update

    # Generate JSON content
    json_content = export_dora_to_json(metrics_data, f"{time_period} days")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dora_metrics_{timestamp}.json"

    return {"content": json_content, "filename": filename}


@callback(
    Output("download-flow-csv", "data"),
    Input("export-flow-csv-button", "n_clicks"),
    State("flow-metrics-store", "data"),
    State("flow-time-period-select", "value"),
    prevent_initial_call=True,
)
def export_flow_csv(n_clicks, metrics_data, time_period):
    """Export Flow metrics to CSV format.

    Args:
        n_clicks: Button click counter (triggers callback)
        metrics_data: Current Flow metrics data from store
        time_period: Selected time period for context

    Returns:
        dict with filename and content for download
    """
    from data.metrics_export import export_flow_to_csv

    if not metrics_data:
        return no_update

    # Generate CSV content
    csv_content = export_flow_to_csv(metrics_data, f"{time_period} days")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"flow_metrics_{timestamp}.csv"

    return {"content": csv_content, "filename": filename}


@callback(
    Output("download-flow-json", "data"),
    Input("export-flow-json-button", "n_clicks"),
    State("flow-metrics-store", "data"),
    State("flow-time-period-select", "value"),
    prevent_initial_call=True,
)
def export_flow_json(n_clicks, metrics_data, time_period):
    """Export Flow metrics to JSON format.

    Args:
        n_clicks: Button click counter (triggers callback)
        metrics_data: Current Flow metrics data from store
        time_period: Selected time period for context

    Returns:
        dict with filename and content for download
    """
    from data.metrics_export import export_flow_to_json

    if not metrics_data:
        return no_update

    # Generate JSON content
    json_content = export_flow_to_json(metrics_data, f"{time_period} days")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"flow_metrics_{timestamp}.json"

    return {"content": json_content, "filename": filename}
