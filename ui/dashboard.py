"""
Dashboard UI Module

This module provides the dashboard layout components for the Dashboard tab.
Supports User Story 2: Dashboard as Primary Landing View.
"""

#######################################################################
# IMPORTS
#######################################################################
# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html

# Application imports
from ui.cards import create_dashboard_metrics_card
from ui.style_constants import get_responsive_cols


#######################################################################
# DASHBOARD LAYOUT FUNCTIONS
#######################################################################


def create_dashboard_layout(metrics: dict | None = None, pert_chart=None) -> html.Div:
    """
    Create complete dashboard layout with metrics cards and PERT timeline.

    This function supports User Story 2: Dashboard as Primary Landing View.
    It composes all dashboard components in a responsive grid layout:
    - 2x2 grid of metric cards on desktop
    - Stacked cards on mobile
    - PERT timeline chart below cards

    Args:
        metrics: DashboardMetrics dictionary (optional for initial render)
        pert_chart: PERT timeline chart figure (optional for initial render)

    Returns:
        html.Div: Complete dashboard layout

    Example:
        >>> metrics = calculate_dashboard_metrics(stats, settings)
        >>> layout = create_dashboard_layout(metrics)
    """
    # Default empty metrics if none provided
    if metrics is None:
        metrics = {
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

    # Create responsive column configuration
    # Mobile: 12 cols (full width), Tablet: 6 cols (2 per row), Desktop: 3 cols (4 per row)
    col_config = get_responsive_cols(mobile=12, tablet=6, desktop=3)

    return html.Div(
        [
            # Dashboard Header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4(
                                [
                                    html.I(className="fas fa-tachometer-alt me-2"),
                                    "Project Dashboard",
                                ],
                                className="mb-1",
                            ),
                            html.P(
                                "Real-time project health metrics and forecasts",
                                className="text-muted mb-3",
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
            # Metrics Cards Row
            dbc.Row(
                [
                    # Completion Forecast Card
                    dbc.Col(
                        [
                            html.Div(
                                id="dashboard-forecast-card-container",
                                children=create_dashboard_metrics_card(
                                    metrics,
                                    card_type="forecast",
                                    id="dashboard-forecast-card",
                                ),
                            ),
                        ],
                        **col_config,
                        className="mb-3",
                    ),
                    # Velocity Card
                    dbc.Col(
                        [
                            html.Div(
                                id="dashboard-velocity-card-container",
                                children=create_dashboard_metrics_card(
                                    metrics,
                                    card_type="velocity",
                                    id="dashboard-velocity-card",
                                ),
                            ),
                        ],
                        **col_config,
                        className="mb-3",
                    ),
                    # Remaining Work Card
                    dbc.Col(
                        [
                            html.Div(
                                id="dashboard-remaining-card-container",
                                children=create_dashboard_metrics_card(
                                    metrics,
                                    card_type="remaining",
                                    id="dashboard-remaining-card",
                                ),
                            ),
                        ],
                        **col_config,
                        className="mb-3",
                    ),
                    # PERT Timeline Card
                    dbc.Col(
                        [
                            html.Div(
                                id="dashboard-pert-card-container",
                                children=create_dashboard_metrics_card(
                                    metrics,
                                    card_type="pert",
                                    id="dashboard-pert-card",
                                ),
                            ),
                        ],
                        **col_config,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),
            # PERT Timeline Chart Row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="dashboard-pert-timeline-container",
                                                children=[
                                                    html.Div(
                                                        "Loading timeline...",
                                                        className="text-center text-muted py-5",
                                                    )
                                                ]
                                                if pert_chart is None
                                                else pert_chart,
                                            ),
                                        ],
                                    ),
                                ],
                                className="shadow-sm",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mt-4",
            ),
        ],
        id="dashboard-main-container",
    )
