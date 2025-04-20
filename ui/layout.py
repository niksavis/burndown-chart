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

# Import UI components and grid templates
from ui.components import create_help_modal
from ui.cards import (
    create_forecast_graph_card,
    create_forecast_info_card,
    create_input_parameters_card,
    create_statistics_data_card,
    create_project_summary_card,
    create_pert_analysis_card,
    create_project_status_card,
)
from ui.tabs import create_tabs
from ui.grid_templates import (
    create_full_width_layout,
    create_two_column_layout,
    create_two_cards_layout,
    create_content_section,
)

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
                    html.Div(
                        [
                            html.I(className="fas fa-question-circle me-2"),
                            "How to Use This App",
                        ],
                        id="help-button",
                        className="btn btn-info btn-sm shadow d-flex align-items-center",
                        style={
                            "cursor": "pointer",
                            "fontWeight": "500",
                            "transition": "all 0.2s ease",
                            "borderRadius": "0.375rem",
                        },
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
            # App header with consistent styling
            create_full_width_layout(
                html.H1(
                    "Project Burndown Forecast",
                    className="text-center my-4",
                ),
                row_class="mb-3",
            ),
            # Help modal
            create_help_modal(),
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
            create_two_cards_layout(
                # Left card - Input Parameters
                create_input_parameters_card(
                    settings,
                    avg_points_per_item,
                    estimated_total_points,
                ),
                # Right card - Project Dashboard
                create_project_summary_card(
                    statistics_df,
                    settings,
                    pert_data={
                        "pert_time_items": 30,  # Provide default value instead of None
                        "pert_time_points": 35,  # Provide default value instead of None
                    },
                ),
                card1_width=4,  # Left card width (changed from 6 to 4 - 1/3 of the space)
                card2_width=8,  # Right card width (changed from 6 to 8 - 2/3 of the space)
                equal_height=True,  # Make cards the same height
            ),
            # Statistics Data Table - using full width layout
            create_full_width_layout(
                create_statistics_data_card(statistics),
                row_class="mb-4",
            ),
            # Footer
            create_content_section(
                title="",
                body=[
                    html.Hr(),
                    html.P(
                        [
                            f"© {current_year} ",
                            html.A(
                                "Project Burndown Forecast",
                                href="#",
                                className="text-decoration-none",
                            ),
                            " - All rights reserved.",
                        ],
                        className="text-muted small mb-1",
                    ),
                ],
                section_class="mt-5 mb-3",
            ),
        ],
        fluid=True,
        className="px-3 py-3",  # Add consistent container padding
    )
