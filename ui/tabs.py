"""
Tab Navigation Module

This module provides the tab-based navigation components for the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html

# Application imports
from ui.grid_utils import create_tab_content as grid_create_tab_content


def create_tabs():
    """
    Create tabs for navigating between different chart views.

    Returns:
        A Dash component containing the tab navigation interface
    """
    # Tab configuration with icons and descriptions for better UX
    tab_config = [
        {
            "id": "tab-burndown",
            "label": "Burndown Chart",
            "icon": "fas fa-chart-line",
            "color": "#0d6efd",  # Primary blue
        },
        {
            "id": "tab-items",
            "label": "Items per Week",
            "icon": "fas fa-tasks",
            "color": "#20c997",  # Teal
        },
        {
            "id": "tab-points",
            "label": "Points per Week",
            "icon": "fas fa-chart-bar",
            "color": "#fd7e14",  # Orange
        },
        {
            "id": "tab-scope-tracking",
            "label": "Scope Tracking",
            "icon": "fas fa-project-diagram",
            "color": "#6f42c1",  # Purple
        },
    ]

    # Generate tabs with enhanced markup for better visual feedback
    tabs = []
    for tab in tab_config:
        # Create a string label rather than a component
        tabs.append(
            dbc.Tab(
                label=tab["label"],
                tab_id=tab["id"],
                labelClassName="fw-medium tab-with-icon",  # Special class for styling
                activeLabelClassName="text-primary fw-bold",
                tab_style={"minWidth": "150px"},
            )
        )

    # Instead of using html.Style which doesn't exist, use dash's method for injecting CSS
    return html.Div(
        [
            # Add CSS styles using Dash's proper method
            html.Div(
                id="tab-icons-css",
                style={"display": "none"},
            ),
            dbc.Tabs(
                tabs,
                id="chart-tabs",
                active_tab="tab-burndown",
                className="mb-4 nav-tabs-modern",
            ),
            # Content div that will be filled based on active tab
            html.Div(html.Div(id="tab-content"), className="tab-content-container"),
        ]
    )


def create_tab_content(active_tab, charts, statistics_df=None, pert_data=None):
    """
    Generate content for the active tab using standardized layout.

    Args:
        active_tab: ID of the currently active tab
        charts: Dictionary of chart components for each tab
        statistics_df: DataFrame containing the project statistics (optional)
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        Dash component containing the active tab's content with consistent styling
    """
    # Import forecast info card functions
    from ui.cards import (
        create_items_forecast_info_card,
        create_points_forecast_info_card,
        create_forecast_info_card,
    )

    # Default to burndown chart if tab is None or invalid
    if active_tab not in [
        "tab-burndown",
        "tab-items",
        "tab-points",
        "tab-scope-tracking",
    ]:
        active_tab = "tab-burndown"

    # Tab-specific forecast info cards
    tab_info_cards = {
        "tab-burndown": create_forecast_info_card(),
        "tab-items": create_items_forecast_info_card(statistics_df, pert_data),
        "tab-points": create_points_forecast_info_card(statistics_df, pert_data),
        "tab-scope-tracking": None,  # No info card needed for scope tracking tab
    }

    # Enhanced tab titles with more descriptive content and icons
    tab_titles = {
        "tab-burndown": html.H5(
            [
                html.I(className="fas fa-chart-line me-2", style={"color": "#0d6efd"}),
                "Project Burndown Forecast",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center",
        ),
        "tab-items": html.H5(
            [
                html.I(className="fas fa-tasks me-2", style={"color": "#20c997"}),
                "Weekly Completed Items",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center",
        ),
        "tab-points": html.H5(
            [
                html.I(className="fas fa-chart-bar me-2", style={"color": "#fd7e14"}),
                "Weekly Completed Points",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center",
        ),
        "tab-scope-tracking": html.H5(
            [
                html.I(
                    className="fas fa-project-diagram me-2", style={"color": "#6f42c1"}
                ),
                "Scope Tracking Dashboard",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center",
        ),
    }

    # Create the tab content with consistent layout and styling - using the imported function
    return grid_create_tab_content(
        [
            # Tab title with enhanced styling
            html.H4(
                tab_titles.get(active_tab, "Chart View"),
                className="mb-4 pb-2 border-bottom",
            ),
            # Tab content
            charts.get(active_tab, html.Div("No chart available")),
            # Tab-specific info card
            tab_info_cards.get(active_tab, None),
        ],
        padding="p-4",  # Use consistent padding
    )
