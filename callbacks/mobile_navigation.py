"""
Mobile Navigation Callbacks

This module provides callbacks for mobile navigation functionality including
drawer navigation, bottom navigation, and swipe gestures.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import (
    callback,
    Input,
    Output,
    State,
    no_update,
    clientside_callback,
)


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
            "active_tab": "tab-dashboard",
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


# Clientside callback to handle mobile navigation tab switching
clientside_callback(
    """
    function(dashboard_clicks, burndown_clicks, items_clicks, points_clicks, scope_clicks, bugs_clicks, dora_clicks, flow_clicks) {
        // Get the callback context to see which button was clicked
        if (!window.dash_clientside.callback_context.triggered.length) {
            return window.dash_clientside.no_update;
        }
        
        const trigger_id = window.dash_clientside.callback_context.triggered[0].prop_id.split('.')[0];
        
        // Map mobile nav buttons to tab IDs
        const tab_mapping = {
            'bottom-nav-tab-dashboard': 'tab-dashboard',
            'bottom-nav-tab-burndown': 'tab-burndown',
            'bottom-nav-tab-scope-tracking': 'tab-scope-tracking',
            'bottom-nav-tab-bug-analysis': 'tab-bug-analysis',
            'bottom-nav-tab-dora-metrics': 'tab-dora-metrics',
            'bottom-nav-tab-flow-metrics': 'tab-flow-metrics',
            'bottom-nav-tab-statistics-data': 'tab-statistics-data'
        };
        
        const target_tab = tab_mapping[trigger_id];
        
        if (target_tab) {
            // Update JavaScript state immediately to prevent conflicts
            if (window.mobileNavigation && window.mobileNavigation.mobileNavState) {
                window.mobileNavigation.mobileNavState.currentTab = target_tab;
            }
            
            return target_tab;
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("chart-tabs", "active_tab", allow_duplicate=True),
    [
        Input("bottom-nav-tab-dashboard", "n_clicks"),
        Input("bottom-nav-tab-burndown", "n_clicks"),
        Input("bottom-nav-tab-scope-tracking", "n_clicks"),
        Input("bottom-nav-tab-bug-analysis", "n_clicks"),
        Input("bottom-nav-tab-dora-metrics", "n_clicks"),
        Input("bottom-nav-tab-flow-metrics", "n_clicks"),
        Input("bottom-nav-tab-statistics-data", "n_clicks"),
    ],
    prevent_initial_call=True,
)


# Use clientside callback to update mobile navigation styling without recreating elements
clientside_callback(
    """
    function(nav_state, active_tab) {
        // Only update if we have an active tab
        if (!active_tab) {
            return window.dash_clientside.no_update;
        }
        
        // Tab configuration (matching Python config)
        const tabs_config = [
            { id: 'tab-dashboard', color: '#0d6efd' },
            { id: 'tab-burndown', color: '#0d6efd' },
            { id: 'tab-items', color: '#20c997' },
            { id: 'tab-points', color: '#fd7e14' },
            { id: 'tab-scope-tracking', color: '#6f42c1' },
            { id: 'tab-bug-analysis', color: '#dc3545' },
            { id: 'tab-dora-metrics', color: '#6610f2' },
            { id: 'tab-flow-metrics', color: '#20c997' }
        ];
        
        // Update each button's styling without recreating elements
        tabs_config.forEach(tab => {
            const button = document.getElementById('bottom-nav-' + tab.id);
            if (button) {
                const is_active = tab.id === active_tab;
                
                // Update classes
                if (is_active) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
                
                // Update styles
                button.style.color = is_active ? tab.color : '#6c757d';
                button.style.background = is_active ? 'rgba(13, 110, 253, 0.1)' : 'transparent';
                button.style.fontWeight = is_active ? '600' : 'normal';
            }
        });
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("mobile-nav-state", "data", allow_duplicate=True),
    [Input("mobile-nav-state", "data"), Input("chart-tabs", "active_tab")],
    prevent_initial_call=True,
)


# Clientside callback to sync JavaScript state with active tab
clientside_callback(
    """
    function(active_tab) {
        // Synchronize JavaScript state with the actual active tab
        if (window.mobileNavigation && window.mobileNavigation.mobileNavState && active_tab) {
            window.mobileNavigation.mobileNavState.currentTab = active_tab;
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("mobile-nav-state", "data", allow_duplicate=True),
    Input("chart-tabs", "active_tab"),
    prevent_initial_call=True,
)


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
    Output("ui-state", "data", allow_duplicate=True),
    Input("mobile-bottom-navigation", "children"),
    prevent_initial_call=True,
)


#######################################################################
# REGISTRATION FUNCTION
#######################################################################


def register(app):
    """Register mobile navigation callbacks with the app."""
    # All callbacks are already defined with @callback decorators
    # This function is called by the callback registration system
    pass
