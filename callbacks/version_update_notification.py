"""
Version Update Notification Callback

Shows a toast notification when a new version is available,
triggered after page initialization completes to avoid being
cleared by other page load callbacks.
"""

import logging
from dash import callback, Output, Input, html, no_update

from ui.toast_notifications import create_toast

logger = logging.getLogger(__name__)


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Input("app-init-complete", "data"),
    Input("version-check-info", "data"),
    prevent_initial_call=True,
)
def show_version_update_toast(app_init_complete, version_info):
    """
    Show version update toast after app initialization completes.

    This callback fires after page load callbacks finish, ensuring the
    toast notification is not cleared by other callbacks that output
    to app-notifications.

    Args:
        app_init_complete: Flag indicating app initialization is complete
        version_info: Dict with 'current' and 'latest' commit hashes, or None

    Returns:
        Toast component if update available, otherwise no_update
    """
    # Only show toast when app is initialized and update is available
    if not app_init_complete or not version_info:
        return no_update

    logger.info(
        f"[VERSION CHECK] Showing update notification: "
        f"{version_info.get('current')} -> {version_info.get('latest')}"
    )

    # Create toast notification with Update Now button
    import dash_bootstrap_components as dbc

    toast = create_toast(
        [
            html.Div("A new version is available on GitHub!"),
            html.Div(
                f"Current: {version_info.get('current', 'unknown')} → "
                f"Latest: {version_info.get('latest', 'unknown')}",
                className="mt-1",
                style={"fontSize": "0.85rem", "opacity": "0.9"},
            ),
            dbc.Button(
                [
                    html.I(className="bi bi-download me-1"),
                    "Update Now",
                ],
                id="update-now-btn",
                color="success",
                size="sm",
                className="mt-2",
                style={"fontSize": "0.85rem"},
            ),
        ],
        toast_type="info",
        header="Update Available",
        duration=15000,  # 15 seconds (longer since it shows after page load)
        icon="sync-alt",
    )

    return toast
