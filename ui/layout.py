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

# Import from data modules
from data import (
    load_settings,
    load_statistics,
    calculate_total_points,
)

# Import UI components
from ui import (
    create_help_modal,
    create_forecast_graph_card,
    create_forecast_info_card,
    create_pert_analysis_card,
    create_input_parameters_card,
    create_statistics_data_card,
)

#######################################################################
# LAYOUT FUNCTION
#######################################################################


def serve_layout():
    """
    Serve a fresh layout with the latest data from disk.
    This is crucial for proper browser refresh behavior.

    Returns:
        Dash Container component with complete application layout
    """
    # Load fresh data from disk each time the layout is served
    current_settings = load_settings()
    current_statistics = load_statistics()

    # Calculate total points based on estimated values (for initial display)
    estimated_total_points, avg_points_per_item = calculate_total_points(
        current_settings["total_items"],
        current_settings["estimated_items"],
        current_settings["estimated_points"],
        current_statistics,
    )

    return dbc.Container(
        [
            # Page initialization complete flag (hidden)
            dcc.Store(id="app-init-complete", data=False),
            # Persistent storage for the current data
            dcc.Store(id="current-settings", data=current_settings),
            dcc.Store(id="current-statistics", data=current_statistics),
            # Store for calculation results
            dcc.Store(
                id="calculation-results",
                data={
                    "total_points": estimated_total_points,
                    "avg_points_per_item": avg_points_per_item,
                },
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
            # First row: Forecast Graph
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_forecast_graph_card(),
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
            # Third row: Input Parameters and PERT Analysis - adjust proportions
            dbc.Row(
                [
                    # Left: Input Parameters (wider for better form layout)
                    dbc.Col(
                        [
                            create_input_parameters_card(
                                current_settings,
                                avg_points_per_item,
                                estimated_total_points,
                            ),
                        ],
                        width=12,
                        lg=8,
                    ),
                    # Right: PERT Analysis (narrower but with improved internal layout)
                    dbc.Col(
                        [
                            create_pert_analysis_card(),
                        ],
                        width=12,
                        lg=4,
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
                            create_statistics_data_card(current_statistics),
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
                                "Project Burndown Forecast - Built with Dash",
                                className="text-center text-muted small",
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
