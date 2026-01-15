"""
About Dialog Callbacks

Handles opening and closing of the About dialog modal from footer button.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import Input, Output, State, callback


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
