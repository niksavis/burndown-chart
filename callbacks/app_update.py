"""
Callbacks for application auto-update functionality.

Handles downloading and installing updates from GitHub releases.
"""

import logging
from dash import callback, Input, Output, State, no_update, ctx
from typing import Optional

from data.update_manager import (
    download_update,
    launch_updater,
    UpdateState,
)

logger = logging.getLogger(__name__)


@callback(
    Output("update-notification-container", "children", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def display_update_notification_on_load(pathname: str):
    """Display update notification on page load if update is available.

    Args:
        pathname: URL pathname (triggers on page load)

    Returns:
        Update notification component or None
    """
    # Import app module to access VERSION_CHECK_RESULT
    import app

    if not app.VERSION_CHECK_RESULT:
        return None

    progress = app.VERSION_CHECK_RESULT

    # Only show notification if update is available
    if progress.state == UpdateState.AVAILABLE:
        logger.info(
            "Update available - displaying notification",
            extra={
                "current_version": progress.current_version,
                "available_version": progress.available_version,
            },
        )

        from ui.update_notification import create_update_notification

        return create_update_notification(progress)

    return None


@callback(
    [
        Output("update-status-store", "data"),
        Output("update-notification-container", "children"),
    ],
    [
        Input("update-now-button", "n_clicks"),
        Input("update-install-button", "n_clicks"),
        Input("update-dismiss-button", "n_clicks"),
    ],
    State("update-status-store", "data"),
    prevent_initial_call=True,
)
def handle_update_actions(
    download_clicks: int,
    install_clicks: int,
    dismiss_clicks: int,
    status_data: Optional[dict],
):
    """Handle update button clicks (download, install, dismiss).

    Args:
        download_clicks: Number of clicks on "Update Now" button
        install_clicks: Number of clicks on "Install Now" button
        dismiss_clicks: Number of clicks on "Dismiss" button
        status_data: Current update status from dcc.Store

    Returns:
        Tuple of (updated status data, notification component)
    """
    triggered_id = ctx.triggered_id

    if not triggered_id:
        return no_update, no_update

    # Handle dismiss - clear notification
    if triggered_id == "update-dismiss-button":
        logger.info("User dismissed update notification")
        return status_data or {}, None

    # Handle install - launch updater and exit app
    if triggered_id == "update-install-button":
        logger.info("User clicked Install Now - launching updater")

        # Import app module to access VERSION_CHECK_RESULT
        import app

        if not app.VERSION_CHECK_RESULT:
            logger.error("No VERSION_CHECK_RESULT available for installation")
            return no_update, no_update

        progress = app.VERSION_CHECK_RESULT

        if progress.state != UpdateState.READY:
            logger.error(
                f"Cannot install update in state {progress.state}",
                extra={"state": progress.state.value},
            )
            return no_update, no_update

        if not progress.download_path:
            logger.error("No download_path available for installation")
            return no_update, no_update

        # Launch updater (this will exit the app)
        try:
            success = launch_updater(progress.download_path)
            if not success:
                logger.error("Failed to launch updater")
                from ui.update_notification import create_update_error_alert

                error_alert = create_update_error_alert(
                    "Failed to launch updater. Please try downloading manually."
                )
                return status_data or {}, error_alert

            # If we get here, updater launched successfully
            # App will exit shortly, so return no_update
            return no_update, no_update

        except Exception as e:
            logger.error(f"Exception launching updater: {e}", exc_info=True)
            from ui.update_notification import create_update_error_alert

            error_alert = create_update_error_alert(
                f"Failed to launch updater: {str(e)}"
            )
            return status_data or {}, error_alert

    # Handle download - start downloading update
    if triggered_id == "update-now-button":
        logger.info("User clicked Update Now - starting download")

        # Import app module to access VERSION_CHECK_RESULT
        import app

        if not app.VERSION_CHECK_RESULT:
            logger.error("No VERSION_CHECK_RESULT available for download")
            return no_update, no_update

        progress = app.VERSION_CHECK_RESULT

        if progress.state != UpdateState.AVAILABLE:
            logger.error(
                f"Cannot download update in state {progress.state}",
                extra={"state": progress.state.value},
            )
            return no_update, no_update

        # Start download in this callback (blocking)
        # In a production app, this would be in a background callback
        # But for simplicity, we'll do it synchronously here
        try:
            from ui.update_notification import (
                create_update_ready_alert,
                create_update_error_alert,
            )

            # Perform download
            logger.info("Starting download...")
            updated_progress = download_update(progress)

            # Update global VERSION_CHECK_RESULT
            app.VERSION_CHECK_RESULT = updated_progress

            # Check download result
            if updated_progress.state == UpdateState.READY:
                logger.info(
                    "Download complete",
                    extra={
                        "version": updated_progress.available_version,
                        "path": str(updated_progress.download_path),
                    },
                )
                ready_alert = create_update_ready_alert()
                return (
                    {
                        "state": updated_progress.state.value,
                        "version": updated_progress.available_version,
                    },
                    ready_alert,
                )

            elif updated_progress.state == UpdateState.ERROR:
                logger.error(
                    "Download failed",
                    extra={"error": updated_progress.error_message},
                )
                error_alert = create_update_error_alert(
                    updated_progress.error_message
                    or "Download failed. Please try again."
                )
                return (
                    {
                        "state": updated_progress.state.value,
                        "error": updated_progress.error_message,
                    },
                    error_alert,
                )

            else:
                # Unexpected state
                logger.warning(
                    f"Unexpected state after download: {updated_progress.state}"
                )
                return no_update, no_update

        except Exception as e:
            logger.error(f"Exception during download: {e}", exc_info=True)
            from ui.update_notification import create_update_error_alert

            error_alert = create_update_error_alert(f"Download failed: {str(e)}")
            return {"state": "error", "error": str(e)}, error_alert

    return no_update, no_update
