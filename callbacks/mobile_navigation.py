"""
Mobile Navigation Callbacks

This module provides callbacks for mobile navigation functionality including
drawer navigation, bottom navigation, and swipe gesture support.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports

# Third-party library imports
from dash import callback, Input, Output, State, html, no_update, clientside_callback

# Application imports


#######################################################################
# MOBILE NAVIGATION CALLBACKS
#######################################################################


@callback(
    [
        Output("mobile-drawer", "style"),
        Output("mobile-drawer-overlay", "style"),
        Output("mobile-nav-state", "data"),
    ],
    [
        Input("mobile-menu-toggle", "n_clicks"),
        Input("mobile-drawer-close", "n_clicks"),
        Input("mobile-drawer-overlay", "n_clicks"),
    ],
    [State("mobile-nav-state", "data")],
    prevent_initial_call=True,
)
def handle_mobile_drawer(menu_clicks, close_clicks, overlay_clicks, nav_state):
    """Handle mobile drawer open/close actions."""
    if not nav_state:
        nav_state = {
            "drawer_open": False,
            "active_tab": "tab-burndown",
            "swipe_enabled": True,
        }

    # Determine if we should toggle the drawer
    total_clicks = (menu_clicks or 0) + (close_clicks or 0) + (overlay_clicks or 0)

    if total_clicks > 0:
        # Toggle drawer state
        drawer_open = not nav_state.get("drawer_open", False)
        nav_state["drawer_open"] = drawer_open

        if drawer_open:
            drawer_style = {"transform": "translateX(0)"}
            overlay_style = {"display": "block"}
        else:
            drawer_style = {"transform": "translateX(-100%)"}
            overlay_style = {"display": "none"}

        return drawer_style, overlay_style, nav_state

    return no_update, no_update, no_update


@callback(
    [
        Output("mobile-nav-state", "data", allow_duplicate=True),
    ],
    [
        Input("drawer-tab-burndown", "n_clicks"),
        Input("drawer-tab-items", "n_clicks"),
        Input("drawer-tab-points", "n_clicks"),
        Input("drawer-tab-scope-tracking", "n_clicks"),
        Input("bottom-nav-tab-burndown", "n_clicks"),
        Input("bottom-nav-tab-items", "n_clicks"),
        Input("bottom-nav-tab-points", "n_clicks"),
        Input("bottom-nav-tab-scope-tracking", "n_clicks"),
    ],
    [State("mobile-nav-state", "data")],
    prevent_initial_call=True,
)
def handle_mobile_tab_navigation(
    drawer_burndown,
    drawer_items,
    drawer_points,
    drawer_scope,
    bottom_burndown,
    bottom_items,
    bottom_points,
    bottom_scope,
    nav_state,
):
    """Handle tab navigation from mobile drawer and bottom navigation."""
    from dash import ctx

    if not ctx.triggered:
        return no_update

    if not nav_state:
        nav_state = {
            "drawer_open": False,
            "active_tab": "tab-burndown",
            "swipe_enabled": True,
        }

    # Determine which tab was clicked
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    tab_mapping = {
        "drawer-tab-burndown": "tab-burndown",
        "drawer-tab-items": "tab-items",
        "drawer-tab-points": "tab-points",
        "drawer-tab-scope-tracking": "tab-scope-tracking",
        "bottom-nav-tab-burndown": "tab-burndown",
        "bottom-nav-tab-items": "tab-items",
        "bottom-nav-tab-points": "tab-points",
        "bottom-nav-tab-scope-tracking": "tab-scope-tracking",
    }

    new_tab = tab_mapping.get(trigger_id)
    if new_tab:
        nav_state["active_tab"] = new_tab
        # Close drawer if it was opened via drawer navigation
        if trigger_id.startswith("drawer-"):
            nav_state["drawer_open"] = False

        return nav_state

    return no_update


# Clientside callback to sync mobile nav state with tab changes
clientside_callback(
    """
    function(nav_state) {
        // Sync mobile navigation with tab changes
        if (!nav_state || !nav_state.active_tab) {
            return window.dash_clientside.no_update;
        }
        
        // Find and click the appropriate tab
        const targetTab = nav_state.active_tab;
        const tabsContainer = document.getElementById('chart-tabs');
        if (tabsContainer) {
            const tabButtons = tabsContainer.querySelectorAll('[data-value="' + targetTab + '"]');
            if (tabButtons.length > 0) {
                tabButtons[0].click();
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("mobile-nav-state", "data", allow_duplicate=True),
    Input("mobile-nav-state", "data"),
    prevent_initial_call=True,
)


@callback(
    Output("mobile-bottom-navigation", "children"),
    [Input("mobile-nav-state", "data"), Input("chart-tabs", "active_tab")],
    prevent_initial_call=True,
)
def update_bottom_navigation_active_state(nav_state, active_tab):
    """Update the active state of bottom navigation items."""
    if not nav_state:
        nav_state = {
            "drawer_open": False,
            "active_tab": "tab-burndown",
            "swipe_enabled": True,
        }

    # Use the active tab from the main tabs component or nav state
    current_tab = active_tab or nav_state.get("active_tab", "tab-burndown")

    from ui.mobile_navigation import get_mobile_tabs_config

    tabs_config = get_mobile_tabs_config()
    nav_items = []

    for tab in tabs_config:
        is_active = tab["id"] == current_tab
        nav_items.append(
            html.Div(
                [
                    html.Button(
                        [
                            html.I(className=tab["icon"], style={"fontSize": "1.1rem"}),
                            html.Div(
                                tab["short_label"], className="mobile-bottom-nav-label"
                            ),
                        ],
                        id=f"bottom-nav-{tab['id']}",
                        className=f"mobile-bottom-nav-item {'active' if is_active else ''}",
                        style={
                            "color": tab["color"] if is_active else "#6c757d",
                            "flexDirection": "column",
                            "border": "none",
                            "background": "transparent"
                            if not is_active
                            else "rgba(13, 110, 253, 0.1)",
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

    return nav_items


# Clientside callback for touch feedback
clientside_callback(
    """
    function() {
        // Add touch feedback to mobile navigation elements
        const mobileNavItems = document.querySelectorAll('.mobile-bottom-nav-item, .mobile-drawer-item');
        
        mobileNavItems.forEach(item => {
            // Remove existing listeners to prevent duplicates
            item.removeEventListener('touchstart', touchStartHandler);
            item.removeEventListener('touchend', touchEndHandler);
            
            // Add touch feedback
            item.addEventListener('touchstart', touchStartHandler, { passive: true });
            item.addEventListener('touchend', touchEndHandler, { passive: true });
        });
        
        function touchStartHandler() {
            this.style.transform = 'scale(0.95)';
            this.style.opacity = '0.8';
        }
        
        function touchEndHandler() {
            this.style.transform = 'scale(1)';
            this.style.opacity = '1';
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("mobile-nav-state", "data", allow_duplicate=True),
    Input("mobile-bottom-navigation", "children"),
    prevent_initial_call=True,
)


@callback(
    Output("mobile-swipe-indicator", "style"),
    Input("chart-tabs", "active_tab"),
    prevent_initial_call=True,
)
def update_swipe_indicator(active_tab):
    """Show/hide swipe indicator based on context."""
    # Hide swipe indicator after user has interacted with tabs
    return {"display": "none"}


# Add interval component for swipe detection (to be added to layout)
def create_swipe_detector():
    """Create interval component for swipe gesture detection."""
    from dash import dcc

    return dcc.Interval(
        id="mobile-swipe-detector",
        interval=100,  # Check every 100ms
        n_intervals=0,
        max_intervals=0,  # Disabled by default, enabled by JavaScript
    )


#######################################################################
# REGISTRATION FUNCTION
#######################################################################


def register(app):
    """Register mobile navigation callbacks with the app."""
    # All callbacks are already defined with @callback decorators
    # This function is called by the callback registration system
    pass
