"""
Tab Navigation Module

This module provides the tab-based navigation components for the application.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime, timedelta
from ui.grid_templates import create_tab_content as create_standardized_tab_content


def create_tabs():
    """
    Create tabs for navigating between different chart views.

    Returns:
        A Dash component containing the tab navigation interface
    """
    return html.Div(
        [
            dbc.Tabs(
                [
                    dbc.Tab(
                        label="Burndown Chart",
                        tab_id="tab-burndown",
                        labelClassName="fw-medium",
                        activeLabelClassName="text-primary fw-bold",
                    ),
                    dbc.Tab(
                        label="Items per Week",
                        tab_id="tab-items",
                        labelClassName="fw-medium",
                        activeLabelClassName="text-primary fw-bold",
                    ),
                    dbc.Tab(
                        label="Points per Week",
                        tab_id="tab-points",
                        labelClassName="fw-medium",
                        activeLabelClassName="text-primary fw-bold",
                    ),
                ],
                id="chart-tabs",
                active_tab="tab-burndown",
                className="mb-3 nav-tabs-modern",
            ),
            # Content div that will be filled based on active tab
            html.Div(id="tab-content"),
        ]
    )


def create_tab_content(active_tab, charts):
    """
    Generate content for the active tab using standardized layout.

    Args:
        active_tab: ID of the currently active tab
        charts: Dictionary of chart components for each tab

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
    ]:
        active_tab = "tab-burndown"

    # Tab-specific forecast info cards
    tab_info_cards = {
        "tab-burndown": create_forecast_info_card(),
        "tab-items": create_items_forecast_info_card(),
        "tab-points": create_points_forecast_info_card(),
    }

    # Tab titles with more descriptive content
    tab_titles = {
        "tab-burndown": "Project Burndown Forecast",
        "tab-items": "Weekly Completed Items Analysis",
        "tab-points": "Weekly Velocity (Story Points)",
    }

    # Create the tab content with standardized layout and styling
    return create_standardized_tab_content(
        [
            # Tab title
            html.H4(
                tab_titles.get(active_tab, "Chart View"),
                className="mb-4",
            ),
            # Tab content
            charts.get(active_tab, html.Div("No chart available")),
            # Tab-specific info card
            tab_info_cards.get(active_tab, None),
        ],
        padding="p-4",  # Use consistent padding
    )
