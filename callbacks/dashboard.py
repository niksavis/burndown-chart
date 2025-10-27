"""
Dashboard Callbacks Module

This module provides callbacks for the Dashboard tab.
Supports User Story 2: Dashboard as Primary Landing View.

Callback Contracts:
- DC-001: update_dashboard_metrics()
- DC-002: update_pert_timeline()
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging

# Third-party library imports
from dash import callback, Output, Input, no_update

# Application imports
from data.processing import calculate_dashboard_metrics, calculate_pert_timeline
from data.persistence import load_app_settings, load_project_data
from ui.cards import create_dashboard_metrics_card
from visualization.charts import create_pert_timeline_chart

# Configure logger
logger = logging.getLogger(__name__)


#######################################################################
# DASHBOARD CALLBACKS
#######################################################################


@callback(
    [
        Output("dashboard-forecast-card-container", "children"),
        Output("dashboard-velocity-card-container", "children"),
        Output("dashboard-remaining-card-container", "children"),
        Output("dashboard-pert-card-container", "children"),
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
    Update dashboard metric cards when data changes.

    Callback Contract: DC-001

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
        tuple: (forecast_card, velocity_card, remaining_card, pert_card)

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
            # Return empty cards with "No data" message
            empty_metrics = {
                "completion_forecast_date": None,
                "completion_confidence": None,
                "days_to_completion": None,
                "days_to_deadline": None,
                "completion_percentage": 0.0,
                "remaining_items": 0,
                "remaining_points": 0.0,
                "current_velocity_items": 0.0,
                "current_velocity_points": 0.0,
                "velocity_trend": "unknown",
            }
            return (
                create_dashboard_metrics_card(
                    empty_metrics, "forecast", id="dashboard-forecast-card"
                ),
                create_dashboard_metrics_card(
                    empty_metrics, "velocity", id="dashboard-velocity-card"
                ),
                create_dashboard_metrics_card(
                    empty_metrics, "remaining", id="dashboard-remaining-card"
                ),
                create_dashboard_metrics_card(
                    empty_metrics, "pert", id="dashboard-pert-card"
                ),
            )

        # Calculate dashboard metrics
        metrics = calculate_dashboard_metrics(statistics, settings)

        # Create metric cards
        forecast_card = create_dashboard_metrics_card(
            metrics, "forecast", id="dashboard-forecast-card"
        )
        velocity_card = create_dashboard_metrics_card(
            metrics, "velocity", id="dashboard-velocity-card"
        )
        remaining_card = create_dashboard_metrics_card(
            metrics, "remaining", id="dashboard-remaining-card"
        )
        pert_card = create_dashboard_metrics_card(
            metrics, "pert", id="dashboard-pert-card"
        )

        return forecast_card, velocity_card, remaining_card, pert_card

    except Exception as e:
        logger.error(f"Error updating dashboard metrics: {e}")
        # Return no_update to preserve existing cards
        return no_update, no_update, no_update, no_update


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
