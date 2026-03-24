"""Tabbed settings panel callbacks.

Implements profile-first onboarding for the tabbed settings panel:
- Connect and Queries are disabled until at least one profile exists.
- Disabled tabs expose tooltip guidance and ARIA state.
- Active tab is forced back to Profile when gated tabs are unavailable.
"""

import logging

from dash import Input, Output, callback, no_update

logger = logging.getLogger(__name__)

PROFILE_REQUIRED_MESSAGE = "Create or import a profile first."


@callback(
    [
        Output("connect-settings-tab", "disabled"),
        Output("queries-settings-tab", "disabled"),
        Output("settings-tabs", "active_tab"),
        Output("connect-tab-disabled-tooltip", "style"),
        Output("queries-tab-disabled-tooltip", "style"),
    ],
    [
        Input("profile-selector", "options"),
        Input("settings-tabs", "active_tab"),
    ],
    prevent_initial_call=False,
)
def enforce_profile_first_tab_access(profile_options, active_tab):
    """Disable tabs that require a profile and expose onboarding guidance."""
    has_profiles = bool(profile_options)
    tabs_disabled = not has_profiles

    tooltip_style = {} if tabs_disabled else {"display": "none"}

    next_active_tab = no_update
    if tabs_disabled and active_tab in {"connect-tab", "queries-tab"}:
        next_active_tab = "profile-tab"

    logger.debug(
        "[Tabs] profile_count=%s tabs_disabled=%s active_tab=%s",
        len(profile_options or []),
        tabs_disabled,
        active_tab,
    )

    return (
        tabs_disabled,
        tabs_disabled,
        next_active_tab,
        tooltip_style,
        tooltip_style,
    )


logger.info("[Callbacks] Tabbed settings callbacks registered")
