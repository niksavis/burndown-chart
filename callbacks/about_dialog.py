"""
About Dialog Callbacks

Handles opening and closing of the About dialog modal from footer button,
and clientside license search/filter functionality.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import Input, Output, State, callback, clientside_callback


#######################################################################
# CALLBACKS
#######################################################################


@callback(
    Output("about-modal", "is_open"),
    [
        Input("about-button", "n_clicks"),
        Input("about-close-button", "n_clicks"),
    ],
    [State("about-modal", "is_open")],
    prevent_initial_call=True,
)
def toggle_about_modal(
    about_clicks: int | None, close_clicks: int | None, is_open: bool
) -> bool:
    """Toggle About modal visibility.

    Args:
        about_clicks: Number of clicks on About button in footer
        close_clicks: Number of clicks on Close button in modal
        is_open: Current modal state

    Returns:
        New modal state (open/closed)
    """
    # Toggle modal state on any button click
    return not is_open


@callback(
    Output("about-tabs", "active_tab"),
    Input("view-changelog-link", "n_clicks"),
    prevent_initial_call=True,
)
def switch_to_changelog_tab(n_clicks: int | None) -> str:
    """Switch to changelog tab when 'View full changelog' link is clicked.

    Args:
        n_clicks: Number of clicks on changelog link

    Returns:
        Tab ID to activate
    """
    return "about-tab-changelog"


# Clientside callback for license search/filter (for instant response)
# Triggers on modal open (to initialize count) and search input changes
# Returns formatted string with count (e.g., "Showing 5 of 59 dependencies")
clientside_callback(
    """
    function(isOpen, searchValue) {
        // Only run filter if modal is open
        if (isOpen) {
            return window.dash_clientside.about_dialog.filterLicenses(searchValue);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("license-count-text", "children"),
    Input("about-modal", "is_open"),
    Input("license-search-input", "value"),
    prevent_initial_call=False,
)
