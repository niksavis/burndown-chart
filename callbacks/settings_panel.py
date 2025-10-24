"""
Settings Panel Callbacks

Handles opening/closing of the settings collapsible panel.
"""

import logging
from dash import Input, Output, State, callback, ctx, no_update

logger = logging.getLogger(__name__)


@callback(
    [
        Output("settings-collapse", "is_open"),
        Output("parameter-collapse", "is_open", allow_duplicate=True),
    ],
    [Input("settings-button", "n_clicks")],
    [
        State("settings-collapse", "is_open"),
        State("parameter-collapse", "is_open"),
    ],
    prevent_initial_call=True,
)
def toggle_settings_panel(settings_clicks, settings_is_open, parameter_is_open):
    """
    Toggle settings panel open/close and close parameter panel if open.

    This ensures only one flyout panel is open at a time for better UX.

    Args:
        settings_clicks: Number of clicks on settings button
        settings_is_open: Current settings panel state
        parameter_is_open: Current parameter panel state

    Returns:
        tuple: (new_settings_state, new_parameter_state)
    """
    # Check which button triggered the callback
    if not ctx.triggered_id:
        logger.warning("No trigger ID - preventing panel state change")
        return no_update, no_update

    # CRITICAL FIX: Prevent firing on initial button render
    if settings_clicks is None:
        logger.warning("Clicks is None - this is initial render, keeping panel closed")
        return False, no_update

    if settings_clicks == 0:
        logger.warning("Clicks is 0 - this is initial state, keeping panel closed")
        return False, no_update

    new_settings_state = not settings_is_open
    logger.info(f"Toggling settings panel to: {new_settings_state}")

    # If opening settings panel, close parameter panel
    if new_settings_state and parameter_is_open:
        logger.info("Closing parameter panel because settings panel is opening")
        return new_settings_state, False

    return new_settings_state, no_update
