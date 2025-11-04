"""
Settings Panel Callbacks

Handles opening/closing of the settings collapsible panel and loading default/last used JQL query.
"""

import logging
from dash import Input, Output, State, callback, ctx, no_update

logger = logging.getLogger(__name__)


@callback(
    [
        Output("settings-collapse", "is_open", allow_duplicate=True),
        Output("parameter-collapse", "is_open", allow_duplicate=True),
        Output("jira-jql-query", "value", allow_duplicate=True),
        Output("jira-query-profile-selector", "value", allow_duplicate=True),
    ],
    [
        Input("settings-button", "n_clicks"),
    ],
    [
        State("settings-collapse", "is_open"),
        State("parameter-collapse", "is_open"),
    ],
    prevent_initial_call=True,
)
def toggle_settings_panel(settings_clicks, settings_is_open, parameter_is_open):
    """
    Toggle settings panel open/close and close parameter panel if open.
    When opening, load the default saved query or last used query into JQL textarea.
    Match loaded JQL query against saved queries and select the matching profile.

    This ensures only one flyout panel is open at a time for better UX.

    Args:
        settings_clicks: Number of clicks on settings button
        settings_is_open: Current settings panel state
        parameter_is_open: Current parameter panel state

    Returns:
        tuple: (new_settings_state, new_parameter_state, jql_query_value, profile_selector_value)
    """
    # Check which button triggered the callback
    if not ctx.triggered_id:
        logger.warning("No trigger ID - preventing panel state change")
        return no_update, no_update, no_update, no_update

    # CRITICAL FIX: Prevent firing on initial button render
    if settings_clicks is None:
        logger.warning(
            "Settings button clicks is None - this is initial render, keeping panel closed"
        )
        return False, no_update, no_update, no_update

    if settings_clicks == 0:
        logger.warning(
            "Settings button clicks is 0 - this is initial state, keeping panel closed"
        )
        return False, no_update, no_update, no_update

    new_settings_state = not settings_is_open
    logger.info(f"Toggling settings panel to: {new_settings_state}")

    # When opening settings panel, DO NOT modify JQL editor or dropdown
    # The JQL editor already has the correct value from its initial_value
    # The dropdown already has the correct value from its initial value
    # Only update these if the panel is CLOSING and we need to reset something
    jql_query_value = no_update
    profile_selector_value = no_update

    # Note: We removed the logic that loads default/last used query when opening
    # because it was overwriting user's unsaved changes. The JQL editor and dropdown
    # already have correct initial values set in the UI layer.

    # If opening settings panel, close parameter panel
    if new_settings_state and parameter_is_open:
        logger.info("Closing parameter panel because settings panel is opening")
        return new_settings_state, False, jql_query_value, profile_selector_value

    return new_settings_state, no_update, jql_query_value, profile_selector_value


def _match_jql_to_profile(jql_query: str, profiles: list) -> str:
    """
    Match a JQL query string to a saved profile by comparing query content.

    Args:
        jql_query: JQL query string to match
        profiles: List of query profile dictionaries

    Returns:
        str: Profile ID if match found, empty string otherwise
    """
    if not jql_query or not profiles:
        return ""

    # Normalize the query for comparison (strip whitespace and lowercase)
    normalized_query = jql_query.strip().lower()

    for profile in profiles:
        profile_jql = profile.get("jql", "")
        if profile_jql.strip().lower() == normalized_query:
            return profile.get("id", "")

    return ""
