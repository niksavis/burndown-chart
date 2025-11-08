"""
Mobile Navigation Module

This module provides mobile-optimized navigation components including
drawer navigation, swipe gestures, and bottom navigation for mobile devices.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html, dcc

# Application imports
# from ui.icon_utils import get_icon_class  # Import removed as not used


def create_mobile_drawer_navigation(tabs_config):
    """
    Create a mobile drawer navigation component that slides in from the side.

    Args:
        tabs_config: List of tab configuration dictionaries

    Returns:
        Dash component for mobile drawer navigation
    """
    drawer_items = []

    for tab in tabs_config:
        drawer_items.append(
            html.Li(
                dbc.Button(
                    [html.I(className=f"{tab['icon']} me-3"), tab["label"]],
                    id=f"drawer-{tab['id']}",
                    color="link",
                    className="mobile-drawer-item w-100 text-start",
                    style={"color": "#495057"},
                ),
                className="mb-2",
            )
        )

    return html.Div(
        [
            # Overlay
            html.Div(
                id="mobile-drawer-overlay",
                className="mobile-drawer-overlay",
                style={"display": "none"},
            ),
            # Drawer content
            html.Div(
                [
                    # Drawer header
                    html.Div(
                        [
                            html.H6("Navigation", className="mb-0 text-muted"),
                            dbc.Button(
                                html.I(className="fas fa-times"),
                                id="mobile-drawer-close",
                                color="link",
                                size="sm",
                                className="p-1",
                            ),
                        ],
                        className="mobile-drawer-header d-flex justify-content-between align-items-center p-3 border-bottom",
                    ),
                    # Drawer body
                    html.Div(
                        html.Ul(drawer_items, className="list-unstyled mb-0"),
                        className="mobile-drawer-body p-3",
                    ),
                ],
                id="mobile-drawer",
                className="mobile-drawer",
                style={"transform": "translateX(-100%)"},
            ),
        ],
        id="mobile-drawer-container",
    )


def create_mobile_bottom_navigation(tabs_config, active_tab="tab-dashboard"):
    """
    Create bottom navigation for mobile devices with primary actions.

    Args:
        tabs_config: List of tab configuration dictionaries
        active_tab: Currently active tab ID

    Returns:
        Dash component for mobile bottom navigation
    """
    nav_items = []

    for tab in tabs_config:
        is_active = tab["id"] == active_tab
        nav_items.append(
            html.Div(
                [
                    html.Button(
                        [
                            html.I(className=tab["icon"], style={"fontSize": "1.1rem"}),
                            html.Div(
                                tab["short_label"],
                                className="mobile-bottom-nav-label",
                            ),
                        ],
                        id=f"bottom-nav-{tab['id']}",
                        className=f"mobile-bottom-nav-item {'active' if is_active else ''}",
                        style={
                            "color": tab["color"] if is_active else "#6c757d",
                            "flexDirection": "column",
                            "border": "none",
                            "background": "rgba(13, 110, 253, 0.1)"
                            if is_active
                            else "transparent",
                            "padding": "0.375rem",
                            "minHeight": "44px",
                            "minWidth": "44px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "textDecoration": "none",
                            "transition": "all 0.2s ease",
                            "borderRadius": "0.5rem",
                            "fontWeight": "600" if is_active else "normal",
                        },
                    )
                ],
                className="mobile-bottom-nav-wrapper",
            )
        )

    return html.Div(
        nav_items,
        id="mobile-bottom-navigation",
        className="mobile-bottom-navigation d-md-none",
    )


def create_mobile_tab_controls():
    """
    Create mobile-specific tab controls including hamburger menu and swipe indicators.

    Returns:
        Dash component with mobile tab controls
    """
    return html.Div(
        [
            # Mobile hamburger menu button
            dbc.Button(
                html.I(className="fas fa-bars"),
                id="mobile-menu-toggle",
                color="outline-secondary",
                size="sm",
                className="mobile-menu-toggle d-md-none mobile-touch-target-sm",
                style={"minWidth": "44px", "minHeight": "44px"},
            ),
            # Swipe indicator for mobile tabs
            html.Div(
                [
                    html.I(className="fas fa-chevron-left me-1"),
                    html.Small("Swipe to navigate", className="text-muted"),
                    html.I(className="fas fa-chevron-right ms-1"),
                ],
                id="mobile-swipe-indicator",
                className="mobile-swipe-indicator d-md-none text-center mt-2",
            ),
        ],
        className="mobile-tab-controls",
    )


def create_mobile_tab_wrapper(children):
    """
    Create a wrapper for tabs with mobile-specific enhancements.

    Args:
        children: Tab content to wrap

    Returns:
        Dash component with mobile tab wrapper
    """
    return html.Div(
        [
            # Mobile controls
            create_mobile_tab_controls(),
            # Tab content with swipe detection
            html.Div(
                children,
                className="mobile-tab-content-wrapper swipe-enabled",
                id="mobile-tab-content-wrapper",
            ),
        ],
        className="mobile-tab-container",
    )


def get_mobile_tabs_config():
    """
    Get mobile-optimized tab configuration.

    Returns:
        List of tab configuration dictionaries optimized for mobile
    """
    from configuration.settings import get_bug_analysis_config

    tabs = [
        {
            "id": "tab-dashboard",
            "label": "Project Dashboard",
            "short_label": "Dashboard",
            "icon": "fas fa-tachometer-alt",
            "color": "#0d6efd",
        },
        {
            "id": "tab-burndown",
            "label": "Burndown Chart",
            "short_label": "Chart",
            "icon": "fas fa-chart-line",
            "color": "#0d6efd",
        },
        {
            "id": "tab-items",
            "label": "Items per Week",
            "short_label": "Items",
            "icon": "fas fa-tasks",
            "color": "#20c997",
        },
        {
            "id": "tab-points",
            "label": "Points per Week",
            "short_label": "Points",
            "icon": "fas fa-chart-bar",
            "color": "#fd7e14",
        },
        {
            "id": "tab-scope-tracking",
            "label": "Scope Changes",
            "short_label": "Scope",
            "icon": "fas fa-project-diagram",
            "color": "#6f42c1",
        },
    ]

    # Conditionally add Bug Analysis tab if enabled
    bug_config = get_bug_analysis_config()
    if bug_config.get("enabled", True):  # Default to True
        tabs.append(
            {
                "id": "tab-bug-analysis",
                "label": "Bug Analysis",
                "short_label": "Bugs",
                "icon": "fas fa-bug",
                "color": "#dc3545",
            }
        )

    # Add DORA Metrics tab
    tabs.append(
        {
            "id": "tab-dora-metrics",
            "label": "DORA Metrics",
            "short_label": "DORA",
            "icon": "fas fa-rocket",
            "color": "#6610f2",  # indigo color
        }
    )

    # Add Flow Metrics tab
    tabs.append(
        {
            "id": "tab-flow-metrics",
            "label": "Flow Metrics",
            "short_label": "Flow",
            "icon": "fas fa-stream",
            "color": "#20c997",  # teal color
        }
    )

    return tabs


def create_mobile_navigation_system():
    """
    Create the complete mobile navigation system including drawer and bottom nav.

    Returns:
        Dash component with complete mobile navigation system
    """
    tabs_config = get_mobile_tabs_config()

    return html.Div(
        [
            # Mobile drawer navigation
            create_mobile_drawer_navigation(tabs_config),
            # Bottom navigation for mobile
            create_mobile_bottom_navigation(tabs_config),
            # Mobile nav state store is now in main layout
        ]
    )
