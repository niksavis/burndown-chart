"""
Settings Panel Callbacks

Handles opening/closing of the settings collapsible panel and loading default/last used JQL query.
"""

import logging
from dash import Input, Output, State, callback, ctx, no_update

logger = logging.getLogger(__name__)


@callback(
    [
        Output("settings-collapse", "is_open"),
        Output("parameter-collapse", "is_open", allow_duplicate=True),
        Output("jira-jql-query", "value", allow_duplicate=True),
        Output("jira-query-profile-selector", "value", allow_duplicate=True),
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
        logger.warning("Clicks is None - this is initial render, keeping panel closed")
        return False, no_update, no_update, no_update

    if settings_clicks == 0:
        logger.warning("Clicks is 0 - this is initial state, keeping panel closed")
        return False, no_update, no_update, no_update

    new_settings_state = not settings_is_open
    logger.info(f"Toggling settings panel to: {new_settings_state}")

    # If opening settings panel, load default/last used query
    jql_query_value = no_update
    profile_selector_value = no_update

    if new_settings_state:  # Panel is being opened
        try:
            from data.jira_query_manager import get_default_query, load_query_profiles
            from data.persistence import load_app_settings

            # Load app settings to get last used query and active profile ID
            app_settings = load_app_settings()
            active_profile_id = app_settings.get("active_jql_profile_id", "")
            last_used_jql = app_settings.get("jql_query", "project = JRASERVER")

            # Try to load default saved query first
            default_query = get_default_query()

            if default_query:
                # Load default saved query
                jql_query_value = default_query.get("jql", "")
                profile_selector_value = default_query.get("id", None)
                logger.info(f"Loaded default saved query: {default_query.get('name')}")

                # Update active_jql_profile_id if it doesn't match
                if active_profile_id != profile_selector_value:
                    logger.info(
                        f"Updating active_jql_profile_id to match default query: {profile_selector_value}"
                    )
                    # Note: We don't save here to avoid triggering another callback cascade
                    # The profile will be saved when user makes changes

            elif active_profile_id:
                # Try to load the active profile by ID
                all_profiles = load_query_profiles()
                active_profile = next(
                    (p for p in all_profiles if p.get("id") == active_profile_id), None
                )

                if active_profile:
                    jql_query_value = active_profile.get("jql", last_used_jql)
                    profile_selector_value = active_profile_id
                    logger.info(f"Loaded active profile: {active_profile.get('name')}")
                else:
                    # Active profile ID not found, fall back to last used query and match
                    jql_query_value = last_used_jql
                    profile_selector_value = _match_jql_to_profile(
                        last_used_jql, all_profiles
                    )
                    logger.info(
                        f"Active profile not found, loaded last used query and matched to profile: {profile_selector_value}"
                    )
            else:
                # No default and no active profile, load last used query and try to match
                all_profiles = load_query_profiles()
                jql_query_value = last_used_jql
                profile_selector_value = _match_jql_to_profile(
                    last_used_jql, all_profiles
                )

                if profile_selector_value:
                    matched_profile = next(
                        (
                            p
                            for p in all_profiles
                            if p.get("id") == profile_selector_value
                        ),
                        None,
                    )
                    logger.info(
                        f"Loaded last used query and matched to saved profile: {matched_profile.get('name') if matched_profile else 'unknown'}"
                    )
                else:
                    logger.info(
                        f"Loaded last used query (no matching saved profile): {last_used_jql[:50]}..."
                    )

        except Exception as e:
            logger.error(f"Error loading JQL query on panel open: {e}")
            # Keep current values if error occurs
            jql_query_value = no_update
            profile_selector_value = no_update

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
