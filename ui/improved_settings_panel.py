"""
Improved Settings Panel Component

Restructured for better UX workflow:
1. JIRA Connection (setup)
2. Workspace Profiles (context)
3. Query Builder (what to fetch)
4. Data Actions (execute)
5. Import/Export (data management)
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import html

from ui.profile_modals import (
    create_profile_deletion_modal,
    create_profile_form_modal,
)

#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _get_default_jql_query():
    """Get default JQL query from settings."""
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jql_query", "project = JRASERVER")
    except ImportError:
        return "project = JRASERVER"


def create_improved_settings_panel(is_open: bool = False):
    """
    Create an improved settings panel with better UX workflow as a flyout.

    This creates a collapsible settings panel similar to the parameter panel,
    with numbered workflow sections for better UX.

    Args:
        is_open: Whether panel should start in expanded state

    Returns:
        html.Div: Complete settings panel with collapse functionality
    """
    return html.Div(
        [
            # Collapsible settings panel content only
            # (no banner - drops down from main banner)
            dbc.Collapse(
                create_settings_panel_content(),
                id="settings-collapse",
                is_open=is_open,
            ),
            # Modals
            create_profile_form_modal(),
            create_profile_deletion_modal(),
        ],
        id="settings-panel",
        className="settings-panel-container",
    )


def create_settings_panel_content():
    """
    Create the content for the settings panel flyout.

    Uses tabbed layout instead of accordion to fix dropdown clipping issues:
    1. Profile - workspace context
    2. JIRA - connection setup
    3. Fields - DORA/Flow field configuration
    4. Queries - define queries for data fetch
    5. Data - execute fetch and import/export
    """
    from ui.tabbed_settings_panel import create_tabbed_settings_panel

    # Return the tabbed panel - cleaner UI without overflow issues
    return create_tabbed_settings_panel()


# Keep the old function for backward compatibility but redirect to new one
def create_settings_panel():
    """Create the settings panel - redirects to improved version."""
    return create_improved_settings_panel()
