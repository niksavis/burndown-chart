"""
Tab Navigation Module

This module provides the tab-based navigation components for the application
with enhanced mobile-first responsive design and navigation patterns.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from typing import TypedDict, List

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html

# Application imports
from configuration.settings import CHART_HELP_TEXTS
from ui.grid_utils import create_tab_content as grid_create_tab_content
from ui.tooltip_utils import create_info_tooltip
from ui.mobile_navigation import (
    create_mobile_navigation_system,
    get_mobile_tabs_config,
)
from ui.style_constants import get_color


#######################################################################
# TAB CONFIGURATION REGISTRY
#######################################################################


class TabConfig(TypedDict):
    """Type definition for tab configuration."""

    id: str
    label: str
    icon: str
    color: str
    order: int
    requires_data: bool
    help_content_id: str


# Central tab registry defining all application tabs
# Order determines display sequence (0 = first tab)
TAB_CONFIG: List[TabConfig] = [
    {
        "id": "tab-dashboard",
        "label": "Dashboard",
        "icon": "fa-tachometer-alt",
        "color": get_color("primary"),
        "order": 0,
        "requires_data": True,
        "help_content_id": "help-dashboard",
    },
    {
        "id": "tab-burndown",
        "label": "Burndown",
        "icon": "fa-chart-line",
        "color": get_color("info"),
        "order": 1,
        "requires_data": True,
        "help_content_id": "help-burndown",
    },
    {
        "id": "tab-items",
        "label": "Items per Week",
        "icon": "fa-tasks",
        "color": get_color("success"),
        "order": 2,
        "requires_data": True,
        "help_content_id": "help-items",
    },
    {
        "id": "tab-points",
        "label": "Points per Week",
        "icon": "fa-chart-bar",
        "color": get_color("warning"),
        "order": 3,
        "requires_data": True,
        "help_content_id": "help-points",
    },
    {
        "id": "tab-scope-tracking",
        "label": "Scope Tracking",
        "icon": "fa-project-diagram",
        "color": get_color("secondary"),
        "order": 4,
        "requires_data": True,
        "help_content_id": "help-scope",
    },
    {
        "id": "tab-bug-analysis",
        "label": "Bug Analysis",
        "icon": "fa-bug",
        "color": get_color("danger"),
        "order": 5,
        "requires_data": True,
        "help_content_id": "help-bug-analysis",
    },
    {
        "id": "tab-dora-metrics",
        "label": "DORA Metrics",
        "icon": "fa-rocket",
        "color": get_color("primary"),
        "order": 6,
        "requires_data": False,  # Has its own data loading
        "help_content_id": "help-dora",
    },
    {
        "id": "tab-flow-metrics",
        "label": "Flow Metrics",
        "icon": "fa-stream",
        "color": get_color("success"),
        "order": 7,
        "requires_data": False,  # Has its own data loading
        "help_content_id": "help-flow",
    },
]


def get_tab_by_id(tab_id: str) -> TabConfig | None:
    """
    Get tab configuration by ID.

    Args:
        tab_id: The tab ID to look up

    Returns:
        Tab configuration dictionary or None if not found
    """
    for tab in TAB_CONFIG:
        if tab["id"] == tab_id:
            return tab
    return None


def get_tabs_sorted() -> List[TabConfig]:
    """
    Get all tabs sorted by order.

    Returns:
        List of tab configurations sorted by order field
    """
    return sorted(TAB_CONFIG, key=lambda t: t["order"])


def validate_tab_id(tab_id: str) -> bool:
    """
    Validate if a tab ID exists in the registry.

    Args:
        tab_id: The tab ID to validate

    Returns:
        True if tab ID is valid, False otherwise
    """
    return any(tab["id"] == tab_id for tab in TAB_CONFIG)


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

    # Create responsive tab navigation
    # On mobile: Use drawer + bottom nav, on desktop: Use regular tabs
    return html.Div(
        [
            # Mobile navigation system (drawer + bottom nav) - only visible on mobile
            create_mobile_navigation_system(),
            # Regular tab navigation - hidden on mobile, visible on desktop
            html.Div(
                [
                    dbc.Tabs(
                        tabs,
                        id="chart-tabs",
                        active_tab="tab-dashboard",  # User Story 2: Dashboard as default view
                        className="mb-4 nav-tabs-modern d-none d-md-flex",  # Hidden on mobile
                    )
                ],
                className="desktop-tab-navigation",
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
        "tab-bug-analysis",
        "tab-dora-metrics",
        "tab-flow-metrics",
    ]:
        active_tab = "tab-burndown"

    # Tab-specific forecast info cards
    tab_info_cards = {
        "tab-burndown": create_forecast_info_card(),
        "tab-items": create_items_forecast_info_card(statistics_df, pert_data),
        "tab-points": create_points_forecast_info_card(statistics_df, pert_data),
        "tab-scope-tracking": html.Div(),  # Always provide a component, even if empty
        "tab-bug-analysis": html.Div(),  # Bug analysis has its own info cards in the content
        "tab-dora-metrics": html.Div(),  # DORA dashboard has its own info cards in the content
        "tab-flow-metrics": html.Div(),  # Flow dashboard has its own info cards in the content
    }

    # Enhanced tab titles with more descriptive content and icons
    tab_titles = {
        "tab-burndown": html.Div(
            [
                html.I(
                    className="fas fa-chart-line me-2",
                    style={"color": get_color("info")},
                ),
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
                html.I(
                    className="fas fa-tasks me-2", style={"color": get_color("success")}
                ),
                "Weekly Completed Items",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-points": html.Div(
            [
                html.I(
                    className="fas fa-chart-bar me-2",
                    style={"color": get_color("warning")},
                ),
                "Weekly Completed Points",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-scope-tracking": html.Div(
            [
                html.I(
                    className="fas fa-chart-bar me-2",
                    style={"color": get_color("secondary")},
                ),
                "Scope Change Analysis",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-bug-analysis": html.Div(
            [
                html.I(
                    className="fas fa-bug me-2", style={"color": get_color("danger")}
                ),
                "Bug Analysis & Quality Insights",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-dora-metrics": html.Div(
            [
                html.I(
                    className="fas fa-rocket me-2",
                    style={"color": get_color("primary")},
                ),
                "DORA Metrics",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-flow-metrics": html.Div(
            [
                html.I(
                    className="fas fa-stream me-2",
                    style={"color": get_color("success")},
                ),
                "Flow Metrics",
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
