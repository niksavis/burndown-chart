"""
UI Layout Module

This module provides the main application layout structure and serves
a fresh layout with the latest data from disk on each page load.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd  # Add pandas for DataFrame conversion
from datetime import datetime

# Import from data modules
from data import (
    load_settings,
    load_statistics,
    calculate_total_points,
)

# Import UI components
from ui.components import create_help_modal
from ui.cards import (
    create_forecast_graph_card,
    create_forecast_info_card,
    create_pert_analysis_card,
    create_input_parameters_card,
    create_statistics_data_card,
    create_project_status_card,
)
from ui.tabs import create_tabs

#######################################################################
# LAYOUT FUNCTION
#######################################################################


def serve_layout():
    """
    Create the application layout.

    Returns:
        Dash application layout with all components
    """
    # Load initial data
    settings = load_settings()
    statistics, is_sample_data = load_statistics()

    app_layout = create_app_layout(settings, statistics, is_sample_data)
    return app_layout


def create_app_layout(settings, statistics, is_sample_data):
    """
    Serve a fresh layout with the latest data from disk.
    This is crucial for proper browser refresh behavior.

    Returns:
        Dash Container component with complete application layout
    """
    # Calculate total points based on estimated values (for initial display)
    estimated_total_points, avg_points_per_item = calculate_total_points(
        settings["total_items"],
        settings["estimated_items"],
        settings["estimated_points"],
        statistics,
    )

    # Create dataframe from statistics
    statistics_df = pd.DataFrame(statistics)

    # Get the current year for footer copyright
    current_year = datetime.now().year

    return dbc.Container(
        [
            # Page initialization complete flag (hidden)
            dcc.Store(id="app-init-complete", data=False),
            # Persistent storage for the current data
            dcc.Store(id="current-settings", data=settings),
            dcc.Store(id="current-statistics", data=statistics),
            # Store for sample data flag
            dcc.Store(id="is-sample-data", data=is_sample_data),
            # Store for calculation results
            dcc.Store(
                id="calculation-results",
                data={
                    "total_points": estimated_total_points,
                    "avg_points_per_item": avg_points_per_item,
                },
            ),
            # Store for date range selection
            dcc.Store(id="date-range-weeks", data=None),
            # Add an empty div to hold the forecast-graph (will be populated by callback)
            html.Div(
                dcc.Graph(id="forecast-graph", style={"display": "none"}),
                id="forecast-graph-container",
            ),
            # Sticky Help Button in top-right corner
            html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className="fas fa-question-circle mr-2"),
                            "How to Use This App",
                        ],
                        id="help-button",
                        color="info",
                        size="sm",
                        className="shadow",
                    ),
                ],
                style={
                    "position": "fixed",
                    "top": "20px",
                    "right": "20px",
                    "zIndex": "1000",
                },
            ),
            # Sample data notification banner (shown only when using sample data)
            html.Div(
                [
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle mr-2"),
                            html.Strong("Using Sample Data: "),
                            "You're currently viewing demo data. ",
                            "Upload your own data using the form below or add entries manually to start tracking your project.",
                            dbc.Button(
                                "Dismiss",
                                id="dismiss-sample-alert",
                                color="link",
                                size="sm",
                                className="ml-3",
                            ),
                        ],
                        id="sample-data-alert",
                        color="info",
                        dismissable=False,
                        is_open=is_sample_data,
                        className="mb-0",
                    ),
                ],
                style={
                    "position": "fixed",
                    "top": "0",
                    "left": "0",
                    "right": "0",
                    "zIndex": "1050",
                },
                id="sample-data-banner",
            ),
            # App header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                "Project Burndown Forecast",
                                className="text-center my-4",
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
            # Help modal
            create_help_modal(),
            # Tab Navigation and Charts Row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            # Tabbed interface
                                            create_tabs(),
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4",
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
            # Second row: Forecast Info Card
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_forecast_info_card(),
                        ],
                        width=12,
                    ),
                ]
            ),
            # New row: Project Status Summary Card
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_project_status_card(
                                statistics_df,  # Convert list to DataFrame
                                settings,  # Pass the entire settings dictionary
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Third row: Input Parameters and PERT Analysis - equal width cards
            dbc.Row(
                [
                    # Left: Input Parameters
                    dbc.Col(
                        [
                            create_input_parameters_card(
                                settings,
                                avg_points_per_item,
                                estimated_total_points,
                            ),
                        ],
                        width=12,
                        lg=6,  # Changed from 8 to 6 (equal width)
                    ),
                    # Right: PERT Analysis
                    dbc.Col(
                        [
                            create_pert_analysis_card(),
                        ],
                        width=12,
                        lg=6,  # Changed from 4 to 6 (equal width)
                    ),
                ],
                className="d-flex align-items-stretch mb-3",  # Make cards equal height
            ),
            # Spacer
            html.Div(className="mb-3"),
            # Fourth row: Statistics Data Table
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_statistics_data_card(statistics),
                        ],
                        width=12,
                    ),
                ]
            ),
            # Footer
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Hr(),
                            html.P(
                                [
                                    f"© {current_year} ",
                                    html.A(
                                        "Project Burndown Forecast",
                                        href="#",
                                        className="text-decoration-none",
                                    ),
                                    " - All rights reserved. ",
                                ],
                                className="text-muted small mb-1",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mt-4",
            ),
        ],
        fluid=True,
    )
