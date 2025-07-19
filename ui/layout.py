"""
UI Layout Module

This module provides the main application layout structure and serves
a fresh layout with the latest data from disk on each page load.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime

# Third-party library imports
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

# Application imports
from configuration import __version__
from data import (
    calculate_total_points,
    load_app_settings,
    load_project_data,
    load_statistics,
)
from ui.cards import (
    create_input_parameters_card,
    create_project_summary_card,
    create_statistics_data_card,
)
from ui.grid_utils import (
    create_full_width_layout,
    create_two_column_layout,
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
    # Load initial data using new separated functions
    app_settings = load_app_settings()
    project_data = load_project_data()
    statistics, is_sample_data = load_statistics()

    # Merge app settings and project data for backward compatibility
    settings = {**app_settings, **project_data}

    app_layout = create_app_layout(settings, statistics, is_sample_data)
    return app_layout


def create_app_layout(settings, statistics, is_sample_data):
    """
    Serve a fresh layout with the latest data from disk.
    This is crucial for proper browser refresh behavior.

    Args:
        settings: Dictionary with application settings
        statistics: List of dictionaries with statistics data
        is_sample_data: Boolean indicating if the data is sample data

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
            # Store for selected chart type (burndown or burnup)
            dcc.Store(id="selected-chart-type", data="burndown"),
            # Add an empty div to hold the forecast-graph (will be populated by callback)
            html.Div(
                dcc.Graph(id="forecast-graph", style={"display": "none"}),
                id="forecast-graph-container",
            ),
            # Sample data notification banner (shown only when using sample data)
            html.Div(
                [
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            html.Strong("Using Sample Data: "),
                            "You're currently viewing demo data. ",
                            "Upload your own data using the form below or add entries manually to start tracking your project.",
                            dbc.Button(
                                "Dismiss",
                                id="dismiss-sample-alert",
                                color="link",
                                size="sm",
                                className="ms-3",
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
            # App header with minimal design to maximize content space
            create_full_width_layout(
                html.Div(
                    [
                        dbc.Row(
                            [
                                # Logo and title on the left
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-tachometer-alt",
                                                    style={
                                                        "fontSize": "1.1rem",
                                                        "color": "#0d6efd",
                                                        "marginRight": "0.5rem",
                                                    },
                                                ),
                                                html.H5(
                                                    "Project Metrics",
                                                    className="mb-0 d-inline",
                                                    style={
                                                        "fontWeight": "500",
                                                        "fontSize": "1.6rem",
                                                    },
                                                ),
                                            ],
                                            className="d-flex align-items-center",
                                        )
                                    ],
                                    width="auto",
                                ),
                            ],
                            className="align-items-center",
                        )
                    ],
                    className="py-1 border-bottom mb-3",
                ),
                row_class="",
            ),
            # Tab Navigation and Charts Row - using full width template
            create_full_width_layout(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                # Tabbed interface
                                create_tabs(),
                            ]
                        ),
                    ],
                    className="shadow-sm",
                ),
                row_class="mb-4",
            ),
            # Project Dashboard and Input Parameters Cards - using two cards layout
            # Changed to use create_two_column_layout with xl breakpoint instead of the default md
            # This will make the cards stack on screens smaller than xl (1200px) instead of md (768px)
            create_two_column_layout(
                left_content=create_input_parameters_card(
                    settings,
                    avg_points_per_item,
                    estimated_total_points,
                ),
                right_content=create_project_summary_card(
                    statistics_df,
                    settings,
                    pert_data={
                        "pert_time_items": 30,  # Provide default value instead of None
                        "pert_time_points": 35,  # Provide default value instead of None
                    },
                ),
                left_width=4,  # Left card width (4/12 or 33%)
                right_width=8,  # Right card width (8/12 or 67%)
                breakpoint="xl",  # Changed from default "md" to "xl" to stack earlier
                className="mb-4",  # Added margin bottom for consistency
            ),
            # Statistics Data Table - using full width layout
            create_full_width_layout(
                create_statistics_data_card(statistics),
                row_class="mb-4",
            ),
            # Minimal footer with useful information
            html.Div(
                [
                    html.Hr(className="my-3"),
                    dbc.Row(
                        [
                            # Left column - app info
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className="fas fa-chart-line me-2 text-muted"
                                        ),
                                        "Burndown Chart ",
                                        html.Span(
                                            f"v{__version__}", className="text-muted"
                                        ),
                                    ],
                                    className="text-secondary",
                                ),
                                width={"size": "auto"},
                            ),
                            # Center column - GitHub link only
                            dbc.Col(
                                html.Small(
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-code me-1"),
                                            "GitHub",
                                        ],
                                        color="link",
                                        size="sm",
                                        className="text-decoration-none px-2",
                                        href="https://github.com/niksavis/burndown-chart",
                                        target="_blank",
                                    ),
                                ),
                                className="text-center",
                                width=True,
                            ),
                            # Right column - Data info
                            dbc.Col(
                                html.Small(
                                    [
                                        f"Last updated: {datetime.now().strftime('%b %d, %Y')}",
                                    ],
                                    className="text-muted text-end",
                                ),
                                width={"size": "auto"},
                            ),
                        ],
                        className="d-flex justify-content-between align-items-center",
                    ),
                ],
                className="mt-4 mb-2",
            ),
        ],
        fluid=True,
        className="px-3 py-3",  # Add consistent container padding
    )
