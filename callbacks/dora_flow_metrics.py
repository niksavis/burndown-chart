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
        Tuple of (metrics_cards, loading_state)
    """
    from ui.dora_metrics_dashboard import create_dora_loading_cards_grid

    try:
        # Parse time period to actual dates
        start_date, end_date = parse_time_period(time_period, custom_start, custom_end)

        logger.info(
            f"DORA metrics requested for period: {start_date.isoformat()} to {end_date.isoformat()}"
        )

        # TODO: Integrate with actual metric calculation
        # from data.dora_calculator import calculate_all_dora_metrics
        # from data.field_mapper import load_field_mappings, get_field_mappings_hash
        # from data.metrics_cache import generate_cache_key, load_cached_metrics, save_cached_metrics
        # from data.jira_simple import fetch_all_issues
        #
        # field_mappings = load_field_mappings()
        # field_hash = get_field_mappings_hash()
        # cache_key = generate_cache_key("dora", start_date.isoformat(), end_date.isoformat(), field_hash)
        #
        # # Try cache first
        # cached_metrics = load_cached_metrics(cache_key)
        # if cached_metrics:
        #     metrics = cached_metrics
        # else:
        #     # Fetch and calculate
        #     issues = fetch_all_issues()
        #     metrics = calculate_all_dora_metrics(issues, field_mappings["field_mappings"]["dora"], start_date, end_date)
        #     save_cached_metrics(cache_key, metrics)
        #
        # # Render metric cards
        # from ui.metric_cards import create_metric_card
        # cards = [create_metric_card(metric_data) for metric_data in metrics.values()]
        # return cards, None

        # Phase 6 stub - show parsed dates
        placeholder_alert = dbc.Alert(
            [
                f"DORA metrics calculation for period: ",
                html.Br(),
                f"Start: {start_date.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                html.Br(),
                f"End: {end_date.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                html.Br(),
                html.Br(),
                "Metric calculation will be integrated in next phase.",
            ],
            color="info",
            dismissable=True,
        )

        return create_dora_loading_cards_grid(), placeholder_alert

    except Exception as e:
        logger.error(f"Error updating DORA metrics: {e}", exc_info=True)
        error_alert = dbc.Alert(
            f"Error loading DORA metrics: {str(e)}",
            color="danger",
            dismissable=True,
        )
        return create_dora_loading_cards_grid(), error_alert


@callback(
    Output("dora-custom-date-range-container", "style"),
    Input("dora-time-period-select", "value"),
)
def toggle_custom_date_range(time_period: str) -> Dict[str, str]:
    """Show/hide custom date range picker based on time period selection.

    Args:
        time_period: Selected time period value

    Returns:
        Style dictionary for custom date range container
    """
    if time_period == "custom":
        return {"display": "block"}
    else:
        return {"display": "none"}


# ============================================================================
# Flow Metrics Callbacks
# ============================================================================


@callback(
    Output("flow-metrics-cards-container", "children"),
    Output("flow-loading-state", "children"),
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
        Tuple of (metrics_cards, loading_state)
    """
    from ui.flow_metrics_dashboard import create_flow_loading_cards_grid

    try:
        # Parse time period to actual dates
        start_date, end_date = parse_time_period(time_period, custom_start, custom_end)

        logger.info(
            f"Flow metrics requested for period: {start_date.isoformat()} to {end_date.isoformat()}"
        )

        # TODO: Integrate with actual metric calculation
        # from data.flow_calculator import calculate_all_flow_metrics
        # from data.field_mapper import load_field_mappings, get_field_mappings_hash
        # from data.metrics_cache import generate_cache_key, load_cached_metrics, save_cached_metrics
        # from data.jira_simple import fetch_all_issues
        #
        # field_mappings = load_field_mappings()
        # field_hash = get_field_mappings_hash()
        # cache_key = generate_cache_key("flow", start_date.isoformat(), end_date.isoformat(), field_hash)
        #
        # # Try cache first
        # cached_metrics = load_cached_metrics(cache_key)
        # if cached_metrics:
        #     metrics = cached_metrics
        # else:
        #     # Fetch and calculate
        #     issues = fetch_all_issues()
        #     metrics = calculate_all_flow_metrics(issues, field_mappings["field_mappings"]["flow"], start_date, end_date)
        #     save_cached_metrics(cache_key, metrics)
        #
        # # Render metric cards
        # from ui.metric_cards import create_metric_card
        # cards = [create_metric_card(metric_data) for metric_data in metrics.values()]
        # return cards, None

        # Phase 6 stub - show parsed dates
        placeholder_alert = dbc.Alert(
            [
                "Flow metrics calculation for period: ",
                html.Br(),
                f"Start: {start_date.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                html.Br(),
                f"End: {end_date.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                html.Br(),
                html.Br(),
                "Metric calculation will be integrated in next phase.",
            ],
            color="info",
            dismissable=True,
        )

        return create_flow_loading_cards_grid(), placeholder_alert

    except Exception as e:
        logger.error(f"Error updating Flow metrics: {e}", exc_info=True)
        error_alert = dbc.Alert(
            f"Error loading Flow metrics: {str(e)}",
            color="danger",
            dismissable=True,
        )
        return create_flow_loading_cards_grid(), error_alert


@callback(
    Output("flow-custom-date-range-container", "style"),
    Input("flow-time-period-select", "value"),
)
def toggle_flow_custom_date_range(time_period: str) -> Dict[str, str]:
    """Show/hide custom date range picker for Flow metrics.

    Args:
        time_period: Selected time period value

    Returns:
        Style dictionary for custom date range container
    """
    if time_period == "custom":
        return {"display": "block"}
    else:
        return {"display": "none"}


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
