"""
Callbacks for application auto-update functionality.

Handles downloading and installing updates from GitHub releases.
Uses background threading for downloads to provide progress feedback.
"""

import logging
import threading

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, no_update

from data.update_manager import (
    UpdateState,
    download_update,
    launch_updater,
)

logger = logging.getLogger(__name__)

# Global variable to track download thread
_download_thread: threading.Thread | None = None
_download_in_progress = False


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Input("footer-update-indicator", "n_clicks"),
    prevent_initial_call=True,
)
def handle_footer_update_click(footer_clicks: int):
    """Handle clicks on footer update indicator.

    Re-shows the appropriate toast based on current state:
    - AVAILABLE: Re-show Download button toast
    - READY: Re-show Update button toast
    - MANUAL_UPDATE_REQUIRED: Open GitHub releases page

    Args:
        footer_clicks: Number of clicks on footer update indicator

    Returns:
        Toast notification
    """
    from dash import callback_context, html

    import app
    from ui.toast_notifications import create_toast

    # Check if actually clicked
    if not callback_context.triggered:
        return no_update

    triggered_prop = callback_context.triggered[0]["prop_id"]
    if ".n_clicks" not in triggered_prop:
        return no_update

    logger.info("Footer update button clicked")

    # Get current update state
    if not app.VERSION_CHECK_RESULT:
        return no_update

    progress = app.VERSION_CHECK_RESULT

    # READY state: Re-show Update button toast
    if progress.state == UpdateState.READY:
        logger.info("Footer clicked in READY state - re-showing install toast")

        ready_toast = create_toast(
            [
                html.Div(f"Update v{progress.available_version} is ready to install."),
                html.Div(
                    [
                        dbc.Button(
                            "Update",
                            id="install-update-button",
                            color="success",
                            size="sm",
                            className="mt-2",
                        ),
                    ],
                ),
            ],
            "success",
            header="Download Complete",
            duration=20000,
            icon="check-circle",
        )
        return ready_toast

    # AVAILABLE state: Re-show Download button toast (consistent with READY behavior)
    elif progress.state == UpdateState.AVAILABLE:
        logger.info("Footer clicked in AVAILABLE state - re-showing download toast")

        download_toast = create_toast(
            [
                html.Div(
                    f"Version {progress.available_version} is available. "
                    f"You are running {progress.current_version}."
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
            duration=20000,
            icon="arrow-circle-up",
        )
        return download_toast

    # MANUAL_UPDATE_REQUIRED: Open GitHub releases (source code mode)
    elif progress.state == UpdateState.MANUAL_UPDATE_REQUIRED:
        logger.info("Footer clicked in MANUAL mode - opening GitHub releases page")

        import webbrowser

        webbrowser.open(
            "https://github.com/niksavis/burndown-chart/releases",
            new=2,
            autoraise=True,
        )

        return create_toast(
            "Opening GitHub releases page in your browser...",
            "info",
            header="Manual Update",
            duration=3000,
            icon="external-link-alt",
        )

    # Any other state - shouldn't happen but handle gracefully
    else:
        return no_update


@callback(
    [
        Output("update-status-store", "data", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
        Output("download-progress-poll", "disabled", allow_duplicate=True),
    ],
    Input("download-update-button", "n_clicks"),
    State("update-status-store", "data"),
    prevent_initial_call=True,
)
def handle_toast_download_click(download_clicks: int, status_data: dict | None):
    """Handle download when user clicks Download button in toast notification."""
    global _download_thread, _download_in_progress
    from dash import callback_context, html

    import app
    from ui.toast_notifications import create_toast

    # Check if button was actually clicked
    if not callback_context.triggered:
        return no_update, no_update, True

    triggered_prop = callback_context.triggered[0]["prop_id"]

    # Only proceed if n_clicks was actually triggered
    if ".n_clicks" not in triggered_prop:
        return no_update, no_update, True

    # Verify it's the download button and clicks > 0
    if not download_clicks or download_clicks == 0:
        return no_update, no_update, True

    logger.info(f"Download button clicked (n_clicks={download_clicks})")

    if not app.VERSION_CHECK_RESULT:
        return no_update, no_update, True

    progress = app.VERSION_CHECK_RESULT

    # Check if download already in progress
    if _download_in_progress:
        logger.warning("Download already in progress")
        return (
            status_data or {},
            create_toast(
                "Download already in progress. Please wait...",
                "info",
                header="Download In Progress",
                duration=3000,
            ),
            False,  # Keep polling enabled
        )

    # Start download in background thread
    def download_background():
        global _download_in_progress
        try:
            _download_in_progress = True
            logger.info("Background download thread started")
            updated_progress = download_update(progress)
            app.VERSION_CHECK_RESULT = updated_progress
            logger.info(
                f"Background download complete - state: {updated_progress.state}",
                extra={
                    "download_path": str(updated_progress.download_path)
                    if updated_progress.download_path
                    else None
                },
            )
        except Exception as e:
            logger.error(f"Background download failed: {e}", exc_info=True)
            # Set error state
            progress.state = UpdateState.ERROR
            progress.error_message = str(e)
            app.VERSION_CHECK_RESULT = progress
        finally:
            _download_in_progress = False

    _download_thread = threading.Thread(target=download_background, daemon=True)
    _download_thread.start()

    # Show downloading toast with progress
    downloading_toast = create_toast(
        [
            html.Div("Downloading update...", id="download-status-text"),
            dbc.Progress(
                id="download-progress-bar-inline",
                value=0,
                className="mt-2",
                animated=True,
                striped=True,
            ),
            html.Div(
                "0% complete",
                id="download-percent-text",
                className="mt-1 text-center",
                style={"fontSize": "0.85rem", "opacity": "0.8"},
            ),
            html.Div(
                (
                    "You can dismiss this notification - "
                    "progress will continue in the footer."
                ),
                className="mt-2",
                style={"fontSize": "0.75rem", "opacity": "0.6"},
            ),
        ],
        "info",
        header="Downloading Update",
        duration=300000,  # 5 minutes - long enough for download
        icon="download",
        dismissable=True,
    )

    return (
        {"state": "downloading"},
        downloading_toast,
        False,  # Enable polling interval
    )


@callback(
    [
        Output("app-notifications", "children", allow_duplicate=True),
        Output("download-progress-poll", "disabled", allow_duplicate=True),
        Output("download-progress-bar-inline", "value", allow_duplicate=True),
        Output("download-percent-text", "children", allow_duplicate=True),
    ],
    Input("download-progress-poll", "n_intervals"),
    prevent_initial_call=True,
)
def poll_download_progress(n_intervals):
    """Poll download progress and update UI.

    Checks global VERSION_CHECK_RESULT for download status and shows
    completion toast when download finishes. Updates progress bar.

    Args:
        n_intervals: Number of polling intervals

    Returns:
        Tuple of (
            toast notification,
            poll interval disabled,
            progress value,
            progress text,
        )
    """
    from dash import html

    import app
    from ui.toast_notifications import create_toast

    progress = app.VERSION_CHECK_RESULT

    if not progress or not _download_in_progress:
        # Check if download completed
        if progress and progress.state == UpdateState.READY:
            logger.info("Download complete - showing Update button toast")

            # Show completion toast with Update button
            ready_toast = create_toast(
                [
                    html.Div(
                        f"Update v{progress.available_version} is ready to install."
                    ),
                    html.Div(
                        [
                            dbc.Button(
                                "Update",
                                id="install-update-button",
                                color="success",
                                size="sm",
                                className="mt-2",
                            ),
                        ],
                    ),
                ],
                "success",
                header="Download Complete",
                duration=20000,
                icon="check-circle",
            )

            # Footer will show "Update Ready" via footer-update-container dynamic update
            return ready_toast, True, 100, "Download complete!"

        elif progress and progress.state == UpdateState.ERROR:
            logger.error(f"Download failed: {progress.error_message}")

            error_toast = create_toast(
                progress.error_message or "Download failed. Please try again.",
                "danger",
                header="Download Failed",
                duration=10000,
            )

            return error_toast, True, 0, "Download failed"

    # Still downloading - update progress
    if progress and _download_in_progress:
        percent = progress.progress_percent or 0
        logger.debug(f"Download progress: {percent}%")
        return no_update, no_update, percent, f"{percent}% complete"

    # No status yet
    return no_update, no_update, 0, "Starting..."


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Input("install-update-button", "n_clicks"),
    State("update-status-store", "data"),
    prevent_initial_call=True,
)
def handle_update_install(install_clicks: int, status_data: dict | None):
    """Handle update installation when user clicks Update button.

    This will launch the updater executable which will:
    1. Wait for the current app to close
    2. Replace the executable with the new version
    3. Restart the application

    Args:
        install_clicks: Number of clicks on Update button
        status_data: Current update status from dcc.Store

    Returns:
        Toast notification about the update process
    """
    import app
    from ui.toast_notifications import create_toast

    if not install_clicks:
        return no_update

    logger.info("User clicked Update button - launching updater")

    # Get current update progress
    progress = app.VERSION_CHECK_RESULT
    if not progress or progress.state != UpdateState.READY:
        logger.warning(
            f"Cannot install: unexpected state {progress.state if progress else 'None'}"
        )
        toast = create_toast(
            "Update not ready. Please download the update first.",
            "warning",
            header="Update Not Ready",
            duration=5000,
        )
        return toast

    if not progress.download_path:
        logger.error("Download path is missing")
        toast = create_toast(
            "Update file not found. Please download the update again.",
            "danger",
            header="Update Error",
            duration=5000,
        )
        return toast

    try:
        # Schedule updater launch in background to allow callback to return
        def launch_and_exit():
            try:
                logger.info("Launching updater in background thread")
                if progress.download_path:  # Type guard
                    launch_updater(progress.download_path)
                # launch_updater calls sys.exit(0), so this line won't be reached
            except SystemExit:
                # This is expected - updater calls sys.exit(0)
                pass
            except Exception as e:
                logger.error(f"Failed to launch updater: {e}", exc_info=True)

        # Start updater in background thread with 2 second delay
        # to give overlay time to show
        import threading

        update_thread = threading.Timer(2.0, launch_and_exit)
        update_thread.daemon = True
        update_thread.start()

        logger.info("Updater scheduled to launch - app will close shortly")

        # NO toast during update - overlay provides all feedback
        # Toast rendering blocks Dash UI updates, preventing overlay from appearing
        # Success toast will show after reconnect (handled by update_reconnect.js)
        return no_update

    except Exception as e:
        logger.error(f"Exception scheduling updater: {e}", exc_info=True)
        error_toast = create_toast(
            f"Update failed: {str(e)}",
            "danger",
            header="Update Error",
            duration=10000,
        )
        return error_toast


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Input("manual-update-instructions-button", "n_clicks"),
    prevent_initial_call=True,
)
def handle_manual_update_instructions(n_clicks: int):
    """Handle clicks on manual update instructions button in startup toast.

    Opens GitHub releases page in browser.

    Args:
        n_clicks: Number of clicks on button

    Returns:
        Toast notification confirming browser opened
    """
    if not n_clicks:
        return no_update

    logger.info(
        "Manual update instructions button clicked - opening GitHub releases page"
    )

    # Open GitHub releases page in browser
    import webbrowser

    webbrowser.open(
        "https://github.com/niksavis/burndown-chart/releases",
        new=2,  # Open in new tab
        autoraise=True,
    )

    from ui.toast_notifications import create_toast

    return create_toast(
        "Opening GitHub releases page in your browser...",
        "info",
        header="Manual Update",
        duration=3000,
        icon="external-link-alt",
    )


# NOTE: Overlay trigger is handled by assets/update_button_handler.js
# which attaches a native click event listener in capture phase.
# This ensures overlay appears BEFORE Dash's callback queue processes,
# solving the race condition where toast rendering blocked overlay display.
