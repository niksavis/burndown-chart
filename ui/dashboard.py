"""
Dashboard UI Module

This module provides the dashboard layout components for the Dashboard tab.
Supports User Story 2: Dashboard as Primary Landing View.
Updated to match DORA/Flow metrics visual design for unified user experience.
"""

#######################################################################
# IMPORTS
#######################################################################
# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html, dcc


#######################################################################
# DASHBOARD LAYOUT FUNCTIONS
#######################################################################


def create_dashboard_layout(
    metrics: dict | None = None, pert_chart=None
) -> dbc.Container:
    """
    Create complete dashboard layout with metrics cards and PERT timeline.

    This function supports User Story 2: Dashboard as Primary Landing View.
    Updated to match DORA/Flow metrics visual design with:
    - Modern metric cards with performance badges
    - Compact overview section with light gray background
    - Consistent spacing and typography
    - Responsive grid layout

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

    return dbc.Container(
        [
            # Store for tracking if user has seen welcome banner (uses localStorage)
            dcc.Store(
                id="dashboard-welcome-dismissed", storage_type="local", data=False
            ),
            # Welcome banner for first-time users (dismissible)
            html.Div(
                id="dashboard-welcome-banner",
                children=[],  # Will be populated by callback based on storage
            ),
            # Compact overview section with distinct background (similar to DORA/Flow)
            html.Div(
                id="dashboard-overview-wrapper",
                children=[
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    id="dashboard-overview",
                                    children=[],  # Will be populated by callback
                                ),
                            ],
                            className="pt-3 px-3 pb-0",  # Top and side padding, no bottom padding
                        ),
                        className="mb-3 overview-section",
                        style={
                            "backgroundColor": "#f8f9fa",  # Light gray background
                            "border": "none",
                            "borderRadius": "8px",
                        },
                    ),
                    # Info banner with balanced spacing
                    html.P(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "Project health metrics updated in real-time. Use ",
                            html.Strong("Update Data"),
                            " button to refresh from JIRA.",
                        ],
                        className="text-muted small mb-3 mt-3",  # Equal top and bottom margin
                    ),
                ],
                style={"display": "block"},  # Always shown for dashboard
            ),
            # Metrics Cards Grid (modern style matching DORA/Flow)
            html.Div(
                id="dashboard-metrics-cards-container",
                children=[],  # Will be populated by callback
                className="mb-4",
            ),
            # PERT Timeline Chart Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-chart-line me-2"),
                                            "PERT Timeline Analysis",
                                        ],
                                        className="fw-bold",
                                    ),
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
                                className="border-0 shadow-sm",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Information and help section
            html.Div(
                id="dashboard-info-section",
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                [
                                                    html.I(
                                                        className="fas fa-lightbulb me-2"
                                                    ),
                                                    "About Project Dashboard",
                                                ],
                                                className="fw-bold",
                                            ),
                                            dbc.CardBody(
                                                [
                                                    html.P(
                                                        "The Project Dashboard provides real-time visibility into your project's health and progress:",
                                                        className="mb-3",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-calendar-check text-primary me-2"
                                                                            ),
                                                                            html.Strong(
                                                                                "Completion Forecast"
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        "PERT-based estimate of project completion date",
                                                                        className="text-muted small mb-0",
                                                                    ),
                                                                ],
                                                                md=6,
                                                                className="mb-3",
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-tachometer-alt text-success me-2"
                                                                            ),
                                                                            html.Strong(
                                                                                "Velocity Trends"
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        "Team throughput and delivery pace",
                                                                        className="text-muted small mb-0",
                                                                    ),
                                                                ],
                                                                md=6,
                                                                className="mb-3",
                                                            ),
                                                        ]
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-tasks text-warning me-2"
                                                                            ),
                                                                            html.Strong(
                                                                                "Remaining Work"
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        "Outstanding items and story points",
                                                                        className="text-muted small mb-0",
                                                                    ),
                                                                ],
                                                                md=6,
                                                                className="mb-3",
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-chart-line text-info me-2"
                                                                            ),
                                                                            html.Strong(
                                                                                "PERT Timeline"
                                                                            ),
                                                                        ],
                                                                        className="mb-1",
                                                                    ),
                                                                    html.P(
                                                                        "Optimistic, likely, and pessimistic scenarios",
                                                                        className="text-muted small mb-0",
                                                                    ),
                                                                ],
                                                                md=6,
                                                                className="mb-3",
                                                            ),
                                                        ]
                                                    ),
                                                    html.Hr(className="my-3"),
                                                    html.P(
                                                        [
                                                            html.I(
                                                                className="fas fa-sync-alt me-2"
                                                            ),
                                                            "Data refreshes automatically from JIRA. Navigate to ",
                                                            html.Strong("Settings"),
                                                            " tab to configure data sources and update parameters.",
                                                        ],
                                                        className="mb-0 text-muted small",
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="border-0 shadow-sm",
                                    ),
                                ],
                                width=12,
                            ),
                        ],
                        className="mb-4",
                    )
                ],
                style={"display": "block"},  # Always shown for dashboard
            ),
            # Store for dashboard metrics data
            dcc.Store(id="dashboard-metrics-store", data={}),
        ],
        fluid=True,
        className="dashboard-container py-4",
    )
