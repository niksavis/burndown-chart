import logging
import threading

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, callback_context, html, no_update

from data.update_manager import (
    UpdateState,
    download_update,
    launch_updater,
)
from ui.toast_notifications import create_toast

logger = logging.getLogger(__name__)

_download_thread: threading.Thread | None = None
_download_in_progress = False


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Input("footer-update-indicator", "n_clicks"),
    prevent_initial_call=True,
)
def handle_footer_update_click(footer_clicks: int):

    import app  # noqa: PLC0415

    if not callback_context.triggered:
        return no_update

    triggered_prop = callback_context.triggered[0]["prop_id"]
    if ".n_clicks" not in triggered_prop:
        return no_update

    logger.info("Footer update button clicked")

    if not app.VERSION_CHECK_RESULT:
        return no_update

    progress = app.VERSION_CHECK_RESULT

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

    elif progress.state == UpdateState.MANUAL_UPDATE_REQUIRED:
        logger.info("Footer clicked in MANUAL mode - opening GitHub releases page")

        import webbrowser  # noqa: PLC0415

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
    global _download_thread, _download_in_progress

    import app  # noqa: PLC0415

    if not callback_context.triggered:
        return no_update, no_update, True

    triggered_prop = callback_context.triggered[0]["prop_id"]

    if ".n_clicks" not in triggered_prop:
        return no_update, no_update, True

    if not download_clicks or download_clicks == 0:
        return no_update, no_update, True

    logger.info(f"Download button clicked (n_clicks={download_clicks})")

    if not app.VERSION_CHECK_RESULT:
        return no_update, no_update, True

    progress = app.VERSION_CHECK_RESULT

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
            False,
        )

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
            progress.state = UpdateState.ERROR
            progress.error_message = str(e)
            app.VERSION_CHECK_RESULT = progress
        finally:
            _download_in_progress = False

    _download_thread = threading.Thread(target=download_background, daemon=True)
    _download_thread.start()

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
        duration=300000,
        icon="download",
        dismissable=True,
    )

    return (
        {"state": "downloading"},
        downloading_toast,
        False,
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

    import app  # noqa: PLC0415

    progress = app.VERSION_CHECK_RESULT

    if not progress or not _download_in_progress:
        if progress and progress.state == UpdateState.READY:
            logger.info("Download complete - showing Update button toast")

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

    if progress and _download_in_progress:
        percent = progress.progress_percent or 0
        logger.debug(f"Download progress: {percent}%")
        return no_update, no_update, percent, f"{percent}% complete"

    return no_update, no_update, 0, "Starting..."


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Input("install-update-button", "n_clicks"),
    State("update-status-store", "data"),
    prevent_initial_call=True,
)
def handle_update_install(install_clicks: int, status_data: dict | None):

    import app  # noqa: PLC0415

    if not install_clicks:
        return no_update

    logger.info("User clicked Update button - launching updater")

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

        def launch_and_exit():
            try:
                logger.info("Launching updater in background thread")
                if progress.download_path:
                    launch_updater(progress.download_path)
            except SystemExit:
                pass
            except Exception as e:
                logger.error(f"Failed to launch updater: {e}", exc_info=True)

        import threading  # noqa: PLC0415

        update_thread = threading.Timer(2.0, launch_and_exit)
        update_thread.daemon = True
        update_thread.start()

        logger.info("Updater scheduled to launch - app will close shortly")

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

    if not n_clicks:
        return no_update

    logger.info(
        "Manual update instructions button clicked - opening GitHub releases page"
    )

    import webbrowser  # noqa: PLC0415

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
