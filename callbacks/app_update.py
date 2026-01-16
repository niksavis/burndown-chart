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
    Output("app-notifications", "children", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def display_update_notification_on_load(pathname: str):
    """Display update notification toast on page load if update is available.

    Args:
        pathname: URL pathname (triggers on page load)

    Returns:
        Toast notification or None
    """
    # Import app module to access VERSION_CHECK_RESULT
    import app
    from dash import no_update

    if not app.VERSION_CHECK_RESULT:
        return no_update

    progress = app.VERSION_CHECK_RESULT

    # Only show notification if update is available
    if progress.state == UpdateState.AVAILABLE:
        logger.info(
            "Update available - displaying toast notification",
            extra={
                "current_version": progress.current_version,
                "available_version": progress.available_version,
            },
        )

        from ui.toast_notifications import create_toast
        from dash import html

        # Create toast message with update info
        message = [
            html.Div(
                f"Version {progress.available_version} is available. You are running {progress.current_version}."
            ),
            html.Div(
                [
                    "Click the ",
                    html.I(className="fas fa-sync-alt"),
                    " update indicator in the footer to download.",
                ],
                className="mt-2",
                style={"fontSize": "0.85rem", "opacity": "0.9"},
            ),
        ]

        return create_toast(
            message=message,
            toast_type="info",
            header=f"Update Available",
            duration=8000,  # 8 seconds - longer for important message
            icon="arrow-circle-up",
        )

    return no_update


@callback(
    [
        Output("update-status-store", "data"),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    [
        Input("footer-update-indicator", "n_clicks"),
    ],
    State("update-status-store", "data"),
    prevent_initial_call=True,
)
def handle_update_download(
    indicator_clicks: int,
    status_data: Optional[dict],
):
    """Handle update download when user clicks footer indicator.

    Args:
        indicator_clicks: Number of clicks on footer update indicator
        status_data: Current update status from dcc.Store

    Returns:
        Tuple of (updated status data, toast notification)
    """
    from ui.toast_notifications import create_toast
    from dash import html

    if not indicator_clicks:
        return no_update, no_update

    logger.info("User clicked footer update indicator - starting download")

    # Import app module to access VERSION_CHECK_RESULT
    import app

    if not app.VERSION_CHECK_RESULT:
        logger.error("No VERSION_CHECK_RESULT available for download")
        return no_update, create_toast(
            "Update check not available. Please restart the app.",
            "warning",
            header="Update Error",
        )

    progress = app.VERSION_CHECK_RESULT

    # Check current state
    if progress.state == UpdateState.READY:
        # Already downloaded, launch installer
        logger.info("Update already downloaded - launching updater")
        if not progress.download_path:
            return no_update, create_toast(
                "Download path not found. Please restart and try again.",
                "danger",
                header="Installation Error",
            )

        try:
            success = launch_updater(progress.download_path)
            if not success:
                return status_data or {}, create_toast(
                    "Failed to launch updater. Please try downloading manually from GitHub.",
                    "danger",
                    header="Installation Error",
                    duration=10000,
                )
            # If successful, app will exit - return no_update
            return no_update, no_update

        except Exception as e:
            logger.error(f"Exception launching updater: {e}", exc_info=True)
            return status_data or {}, create_toast(
                f"Failed to launch updater: {str(e)}",
                "danger",
                header="Installation Error",
                duration=10000,
            )

    elif progress.state == UpdateState.AVAILABLE:
        # Need to download first
        logger.info("Starting download...")

        # Show downloading toast
        downloading_toast = create_toast(
            [
                html.Div("Downloading update... This may take a few minutes."),
                html.Div(
                    "The app will show another notification when ready to install.",
                    className="mt-2",
                    style={"fontSize": "0.85rem", "opacity": "0.8"},
                ),
            ],
            "info",
            header="Downloading Update",
            duration=5000,
            icon="spinner fa-spin",
        )

        try:
            # Perform download (synchronous for now)
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

                # Show ready to install toast
                ready_toast = create_toast(
                    [
                        html.Div(
                            f"Update to version {updated_progress.available_version} downloaded successfully!"
                        ),
                        html.Div(
                            [
                                "Click the ",
                                html.I(className="fas fa-sync-alt"),
                                " update indicator again to install.",
                            ],
                            className="mt-2",
                            style={"fontSize": "0.85rem", "opacity": "0.9"},
                        ),
                    ],
                    "success",
                    header="Ready to Install",
                    duration=10000,
                    icon="check-circle",
                )

                return (
                    {
                        "state": updated_progress.state.value,
                        "version": updated_progress.available_version,
                    },
                    ready_toast,
                )

            elif updated_progress.state == UpdateState.ERROR:
                logger.error(
                    "Download failed",
                    extra={"error": updated_progress.error_message},
                )
                error_toast = create_toast(
                    updated_progress.error_message
                    or "Download failed. Please try again or download manually from GitHub.",
                    "danger",
                    header="Download Failed",
                    duration=10000,
                )
                return (
                    {
                        "state": updated_progress.state.value,
                        "error": updated_progress.error_message,
                    },
                    error_toast,
                )

            else:
                # Unexpected state
                logger.warning(
                    f"Unexpected state after download: {updated_progress.state}"
                )
                return status_data or {}, downloading_toast

        except Exception as e:
            logger.error(f"Exception during download: {e}", exc_info=True)
            error_toast = create_toast(
                f"Download failed: {str(e)}",
                "danger",
                header="Download Error",
                duration=10000,
            )
            return {"state": "error", "error": str(e)}, error_toast

    else:
        # Unexpected state
        logger.warning(f"Cannot handle update in state: {progress.state}")
        return no_update, create_toast(
            f"Update in unexpected state: {progress.state.value}. Please restart the app.",
            "warning",
            header="Update Status",
        )

    return no_update, no_update
