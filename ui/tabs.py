"""
Tab Navigation Module

This module provides the tab-based navigation components for the application
with enhanced mobile-first responsive design and navigation patterns.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html

# Application imports
from configuration.settings import CHART_HELP_TEXTS
from ui.grid_utils import create_tab_content as grid_create_tab_content
from ui.tooltip_utils import create_info_tooltip
from ui.mobile_navigation import (
    create_mobile_navigation_system,
    create_mobile_tab_wrapper,
    get_mobile_tabs_config,
)


def create_tabs():
    """
    Create tabs for navigating between different chart views with mobile-first design.

    Returns:
        A Dash component containing the tab navigation interface with mobile enhancements
    """
    # Get mobile-optimized tab configuration
    tab_config = get_mobile_tabs_config()

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

    # Create mobile tab wrapper with navigation system
    tab_navigation = create_mobile_tab_wrapper(
        [
            dbc.Tabs(
                tabs,
                id="chart-tabs",
                active_tab="tab-burndown",
                className="mb-4 nav-tabs-modern",
            )
        ]
    )

    return html.Div(
        [
            # Mobile navigation system (drawer + bottom nav)
            create_mobile_navigation_system(),
            # Tab navigation with mobile wrapper
            tab_navigation,
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
        "tab-scope-tracking": html.Div(),  # Always provide a component, even if empty
    }

    # Enhanced tab titles with more descriptive content and icons
    tab_titles = {
        "tab-burndown": html.Div(
            [
                html.I(className="fas fa-chart-line me-2", style={"color": "#0d6efd"}),
                "Project Burndown Forecast",
                create_info_tooltip(
                    CHART_HELP_TEXTS["burndown_vs_burnup"],
                    "Burndown vs Burnup chart differences and when to use each approach",
                ),
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-items": html.Div(
            [
                html.I(className="fas fa-tasks me-2", style={"color": "#20c997"}),
                "Weekly Completed Items",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-points": html.Div(
            [
                html.I(className="fas fa-chart-bar me-2", style={"color": "#fd7e14"}),
                "Weekly Completed Points",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-scope-tracking": html.Div(
            [
                html.I(className="fas fa-chart-bar me-2", style={"color": "#fd7e14"}),
                "Scope Change Analysis",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
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
            # Tab content - ensure we always have content, never fallback to avoid React hooks issues
            charts.get(
                active_tab, charts.get("tab-burndown", html.Div("Loading chart..."))
            ),
            # Tab-specific info card
            tab_info_cards.get(active_tab, html.Div()),  # Always return a component
        ],
        padding="p-4",  # Use consistent padding
    )
