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
        field_mappings = mappings_data.get("field_mappings", {})

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

        # Render metric cards
        from ui.metric_cards import create_metric_card

        cards = []
        for metric_name, metric_data in metrics.items():
            card = create_metric_card(metric_data)
            cards.append(card)

        logger.info(
            f"DORA metrics calculated: {len(cards)} cards (may show error states for missing fields)"
        )

        # Show info message about Apache Kafka limitations
        info_alert = dbc.Alert(
            [
                html.H5("ℹ️ Apache Kafka JIRA Limitations", className="alert-heading"),
                html.P(
                    "Apache Kafka JIRA does not have deployment or incident tracking fields."
                ),
                html.P(
                    "Metrics will show 'missing field mapping' errors. This is expected.",
                    className="mb-0",
                ),
            ],
            color="info",
            dismissable=True,
            duration=6000,
        )

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
        field_mappings = mappings_data.get("field_mappings", {})

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

        logger.info(f"Calculating Flow metrics for {len(issues)} issues")

        # Calculate all Flow metrics
        metrics = calculate_all_flow_metrics(
            issues=issues,
            field_mappings=field_mappings,
            start_date=start_date,
            end_date=end_date,
        )

        # Render metric cards
        from ui.metric_cards import create_metric_card

        cards = []
        for metric_name, metric_data in metrics.items():
            card = create_metric_card(metric_data)
            cards.append(card)

        logger.info(f"Flow metrics calculated successfully: {len(cards)} cards")

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
        Flow distribution chart or placeholder
    """
    # Phase 5 stub - return placeholder
    return dbc.Alert(
        "Distribution chart will be populated with real data after JIRA integration",
        color="info",
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
        return no_update

    triggered_id = callback_context.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict):
        return no_update

    # Get the metric name that was clicked
    clicked_metric = triggered_id.get("metric")
    if not clicked_metric:
        return no_update

    # Toggle the state for the clicked metric, keep others unchanged
    # We need to match against all callback contexts to find the right index
    result = []
    for output_id in callback_context.outputs_list:
        if (
            isinstance(output_id, dict)
            and output_id.get("type") == "metric-trend-collapse"
        ):
            metric_name = output_id.get("metric")
            # Find the current state for this metric
            idx = len(result)
            if idx < len(is_open_list):
                current_state = is_open_list[idx]
                # Toggle if this is the clicked metric, otherwise keep unchanged
                new_state = (
                    not current_state
                    if metric_name == clicked_metric
                    else current_state
                )
                result.append(new_state)

    return result


@callback(
    [
        Output("deployment_frequency-trend-chart", "children"),
        Output("lead_time_for_changes-trend-chart", "children"),
        Output("change_failure_rate-trend-chart", "children"),
        Output("mean_time_to_recovery-trend-chart", "children"),
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

                # Check if metric has error state
                if "error_state" in metric_data:
                    results.append(
                        html.P(
                            f"Cannot display trend: {metric_data.get('error_message', 'No data available')}",
                            className="text-muted text-center my-3",
                        )
                    )
                else:
                    # Create chart (without historical data for now)
                    # Historical data would need to be fetched/calculated separately
                    figure = chart_func(metric_data, historical_data=None)
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
        Output("flow_velocity-trend-chart", "children"),
        Output("flow_time-trend-chart", "children"),
        Output("flow_efficiency-trend-chart", "children"),
        Output("flow_load-trend-chart", "children"),
        Output("flow_distribution-trend-chart", "children"),
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

                # Check if metric has error state
                if "error_state" in metric_data:
                    results.append(
                        html.P(
                            f"Cannot display trend: {metric_data.get('error_message', 'No data available')}",
                            className="text-muted text-center my-3",
                        )
                    )
                else:
                    # Create chart
                    # Note: flow_distribution uses different function signature
                    if metric_name == "flow_distribution":
                        figure = chart_func(metric_data)
                    else:
                        # Other flow metrics expect historical data list
                        # For now, create single-point chart from current data
                        historical_data = [
                            {
                                "date": datetime.now().isoformat(),
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
