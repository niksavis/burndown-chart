"""
Tab Navigation Module

This module provides the tab-based navigation components for the application.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime, timedelta


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
                        labelClassName="font-weight-bold",
                        activeLabelClassName="text-primary",
                    ),
                    dbc.Tab(
                        label="Items per Week",
                        tab_id="tab-items",
                        labelClassName="font-weight-bold",
                        activeLabelClassName="text-primary",
                    ),
                    dbc.Tab(
                        label="Points per Week",
                        tab_id="tab-points",
                        labelClassName="font-weight-bold",
                        activeLabelClassName="text-primary",
                    ),
                ],
                id="chart-tabs",
                active_tab="tab-burndown",
                className="mb-3",
            ),
            # Content div that will be filled based on active tab
            html.Div(id="tab-content", className="p-2"),
        ]
    )


def create_tab_content(active_tab, charts):
    """
    Generate content for the active tab.

    Args:
        active_tab: ID of the currently active tab
        charts: Dictionary of chart components for each tab

    Returns:
        Dash component containing the active tab's content
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

    # Return the appropriate chart based on the active tab
    return html.Div(
        [
            # Tab title
            html.H4(
                {
                    "tab-burndown": "Project Burndown Forecast",
                    "tab-items": "Weekly Completed Items",
                    "tab-points": "Weekly Completed Points",
                }[active_tab],
                className="mb-4",
            ),
            # Tab content
            charts.get(active_tab, html.Div("No chart available")),
            # Tab-specific info card
            tab_info_cards.get(active_tab, None),
        ],
        # Add transition animation with CSS
        className="tab-content-container",
        style={
            "animation": "fadeIn 0.5s ease-in-out",
        },
    )
