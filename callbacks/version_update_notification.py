"""
Version Update Notification Callback

Shows toast notifications for:
1. New version available (update check)
2. Successfully updated (version change on startup)

Triggered after page initialization completes to avoid being
cleared by other page load callbacks.
"""

import logging
from dash import callback, Output, Input, html, no_update

from ui.toast_notifications import create_toast
from data.update_manager import UpdateState
from data.version_tracker import check_and_update_version

logger = logging.getLogger(__name__)


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("update-toast-shown", "data"),
    Input("app-init-complete", "data"),
    Input("update-toast-shown", "data"),
    prevent_initial_call=True,
)
def show_version_update_toast(app_init_complete, toast_already_shown):
    """
    Show version update notifications after app initialization completes.

    Handles two types of notifications:
    1. "Successfully updated to vX.Y.Z" - shown when version changed since last run
    2. "Update available" - shown when new version is available for download

    This callback fires after page load callbacks finish, ensuring the
    toast notification is not cleared by other callbacks that output
    to app-notifications.

    Only shows once per browser session (tracked via dcc.Store with storage_type='session').

    Args:
        app_init_complete: Flag indicating app initialization is complete
        toast_already_shown: Boolean flag tracking if toast was already shown this session

    Returns:
        Tuple of (Toast component or no_update, toast_shown_flag)
    """
    # Don't show if already shown this session
    if toast_already_shown:
        return no_update, no_update

    # Only show toast when app is initialized
    if not app_init_complete:
        return no_update, no_update

    # Check if version changed - tracked for logging only
    # Success toast is shown by update_reconnect.js after reconnect
    version_changed, previous_version, current_version = check_and_update_version()

    if version_changed and previous_version:
        logger.info(
            f"Version changed: {previous_version} -> {current_version} (toast handled by JS)",
            extra={
                "operation": "version_update_notification",
                "previous_version": previous_version,
                "current_version": current_version,
            },
        )

    # Import app module to access VERSION_CHECK_RESULT
    import app

    if not app.VERSION_CHECK_RESULT:
        return no_update, no_update

    progress = app.VERSION_CHECK_RESULT

    # Handle manual update required (source code deployment)
    if progress.state == UpdateState.MANUAL_UPDATE_REQUIRED:
        logger.info(
            "Manual update required - displaying instructions after init",
            extra={
                "current_version": progress.current_version,
                "available_version": progress.available_version,
            },
        )

        import dash_bootstrap_components as dbc

        toast = create_toast(
            [
                html.Div(
                    f"Version {progress.available_version} is available. You are running {progress.current_version} from source code."
                ),
                dbc.Button(
                    [
                        html.I(className="fas fa-external-link-alt me-2"),
                        "View Releases",
                    ],
                    id="manual-update-instructions-button",
                    color="info",
                    size="sm",
                    className="mt-2",
                    n_clicks=0,
                ),
            ],
            toast_type="info",
            header="Update Available (Manual)",
            duration=20000,  # 20 seconds - enough time to read and click
            icon="arrow-circle-up",
        )

        return toast, True  # Mark toast as shown

    # Handle automatic update available (executable mode)
    if progress.state == UpdateState.AVAILABLE:
        logger.info(
            "Update available - displaying toast after init",
            extra={
                "current_version": progress.current_version,
                "available_version": progress.available_version,
            },
        )

        import dash_bootstrap_components as dbc

        toast = create_toast(
            [
                html.Div(
                    f"Version {progress.available_version} is available. You are running {progress.current_version}."
                ),
                dbc.Button(
                    [
                        html.I(className="fas fa-download me-2"),
                        "Download",
                    ],
                    id="download-update-button",
                    color="success",
                    size="sm",
                    className="mt-2",
                    n_clicks=0,
                ),
            ],
            toast_type="info",
            header="Update Available",
            duration=20000,  # 20 seconds - enough time to read and click
            icon="arrow-circle-up",
        )

        return toast, True  # Mark toast as shown

    # No update available or other state
    return no_update, no_update
