"""
Dashboard Callbacks Module

This module provides callbacks for the Dashboard tab.
Supports User Story 2: Dashboard as Primary Landing View.

Callback Contracts:
- DC-001: update_dashboard_metrics()
- DC-002: update_pert_timeline()
- DC-003: handle_quick_navigation()
- DC-004: handle_quick_settings()
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging

# Third-party library imports
from dash import callback, Output, Input, no_update, html, ctx

# Application imports
from data.processing import calculate_dashboard_metrics, calculate_pert_timeline
from data.persistence import load_app_settings, load_project_data
from ui.dashboard_cards import (
    create_dashboard_forecast_card,
    create_dashboard_velocity_card,
    create_dashboard_remaining_card,
    create_dashboard_pert_card,
    create_dashboard_overview_content,
)
from visualization.charts import create_pert_timeline_chart

# Configure logger
logger = logging.getLogger(__name__)


#######################################################################
# DASHBOARD CALLBACKS
#######################################################################


@callback(
    [
        Output("dashboard-overview", "children"),
        Output("dashboard-metrics-cards-container", "children"),
    ],
    [
        Input("statistics-data-store", "data"),
        Input("jira-cache-status", "children"),
        Input("parameter-panel-state", "data"),
    ],
    prevent_initial_call=False,
)
def update_dashboard_metrics(statistics_data, jira_status, parameter_state):
    """
    Update dashboard overview and metric cards when data changes.

    Callback Contract: DC-001

    This callback follows User Story 2 requirements:
    - Updates when statistics change
    - Updates when JIRA data refreshes
    - Updates when parameters change
    - Handles missing data gracefully
    - Uses modern metric card design matching DORA/Flow metrics

    Args:
        statistics_data: Statistics data from store
        jira_status: JIRA cache status text (triggers refresh)
        parameter_state: Current parameter panel state

    Returns:
        tuple: (overview_content, metrics_cards_grid)

    Raises:
        PreventUpdate: If no valid data available
    """
    try:
        # Load current settings and project data
        settings = load_app_settings()
        project_data = load_project_data()

        # Use statistics from store if available, otherwise from project data
        statistics = (
            statistics_data if statistics_data else project_data.get("statistics", [])
        )

        if not statistics:
            logger.warning("No statistics data available for dashboard metrics")
            # Return empty state
            from ui.empty_states import create_no_data_state

            empty_overview = html.Div(
                html.P("No data available", className="text-muted text-center mb-0"),
                className="py-2",
            )
            empty_cards = create_no_data_state()

            return empty_overview, empty_cards

        # Calculate dashboard metrics
        metrics = calculate_dashboard_metrics(statistics, settings)

        # Create overview section
        overview_content = create_dashboard_overview_content(metrics)

        # Create individual metric cards using new dashboard_cards module
        forecast_card = create_dashboard_forecast_card(metrics)
        velocity_card = create_dashboard_velocity_card(metrics)
        remaining_card = create_dashboard_remaining_card(metrics)
        pert_card = create_dashboard_pert_card(metrics)

        # Create grid layout for cards (2 cards per row on desktop)
        import dash_bootstrap_components as dbc

        cards_grid = dbc.Row(
            [
                dbc.Col(forecast_card, xs=12, lg=6, className="mb-3"),
                dbc.Col(velocity_card, xs=12, lg=6, className="mb-3"),
                dbc.Col(remaining_card, xs=12, lg=6, className="mb-3"),
                dbc.Col(pert_card, xs=12, lg=6, className="mb-3"),
            ],
            className="metric-cards-grid",
        )

        return overview_content, cards_grid

    except Exception as e:
        logger.error(f"Error updating dashboard metrics: {e}")
        # Return no_update to preserve existing content
        return no_update, no_update


@callback(
    Output("dashboard-pert-timeline-container", "children"),
    [
        Input("statistics-data-store", "data"),
        Input("jira-cache-status", "children"),
        Input("parameter-panel-state", "data"),
    ],
    prevent_initial_call=False,
)
def update_pert_timeline(statistics_data, jira_status, parameter_state):
    """
    Update PERT timeline chart when data changes.

    Callback Contract: DC-002

    This callback follows User Story 2 requirements:
    - Updates when statistics change
    - Updates when JIRA data refreshes
    - Updates when parameters change
    - Handles missing data gracefully

    Args:
        statistics_data: Statistics data from store
        jira_status: JIRA cache status text (triggers refresh)
        parameter_state: Current parameter panel state

    Returns:
        dcc.Graph: PERT timeline chart or error message

    Raises:
        PreventUpdate: If no valid data available
    """
    try:
        # Load current settings and project data
        settings = load_app_settings()
        project_data = load_project_data()

        # Use statistics from store if available, otherwise from project data
        statistics = (
            statistics_data if statistics_data else project_data.get("statistics", [])
        )

        if not statistics:
            logger.warning("No statistics data available for PERT timeline")
            from dash import html

            return html.Div(
                [
                    html.I(className="fas fa-info-circle fa-2x text-muted mb-2"),
                    html.P("No data available", className="text-muted"),
                ],
                className="text-center py-5",
            )

        # Calculate PERT timeline data
        pert_data = calculate_pert_timeline(statistics, settings)

        # Create PERT timeline chart
        pert_chart = create_pert_timeline_chart(pert_data)

        return pert_chart

    except Exception as e:
        logger.error(f"Error updating PERT timeline: {e}")
        from dash import html

        return html.Div(
            [
                html.I(className="fas fa-exclamation-triangle fa-2x text-warning mb-2"),
                html.P("Error loading timeline", className="text-muted"),
            ],
            className="text-center py-5",
        )


@callback(
    Output("chart-tabs", "active_tab"),
    [
        Input("dashboard-view-burndown", "n_clicks"),
        Input("dashboard-view-bugs", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def handle_quick_navigation(burndown_clicks, bugs_clicks):
    """
    Handle quick action navigation buttons.

    Args:
        burndown_clicks: Number of clicks on View Burndown button
        bugs_clicks: Number of clicks on Bug Analysis button

    Returns:
        Tab ID to navigate to
    """
    triggered_id = ctx.triggered_id

    if triggered_id == "dashboard-view-burndown":
        return "tab-burndown"
    elif triggered_id == "dashboard-view-bugs":
        return "tab-bug-analysis"

    return no_update


@callback(
    Output("settings-collapse", "is_open"),
    Input("dashboard-open-settings", "n_clicks"),
    prevent_initial_call=True,
)
def handle_quick_settings(n_clicks):
    """
    Handle quick action to open settings panel.

    Args:
        n_clicks: Number of clicks on Settings button

    Returns:
        Boolean to open settings panel
    """
    if n_clicks:
        return True
    return no_update


#######################################################################
# CALLBACK REGISTRATION
#######################################################################


def register(app):
    """
    Register dashboard callbacks with the app.

    This function is called by the main callback registry to register
    all dashboard-related callbacks.

    Args:
        app: The Dash application instance
    """
    # Callbacks are auto-registered via @callback decorator
    # This function exists for consistency with other callback modules
    logger.info("Dashboard callbacks registered")
