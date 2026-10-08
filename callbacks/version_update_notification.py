import logging

from dash import Input, Output, callback, html, no_update

from data.update_manager import UpdateState
from data.version_tracker import check_and_update_version
from ui.toast_notifications import create_toast

logger = logging.getLogger(__name__)


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("update-toast-shown", "data"),
    Input("app-init-complete", "data"),
    Input("update-toast-shown", "data"),
    prevent_initial_call=True,
)
def show_version_update_toast(app_init_complete, toast_already_shown):

    if toast_already_shown:
        return no_update, no_update

    if not app_init_complete:
        return no_update, no_update

    version_changed, previous_version, current_version = check_and_update_version()

    if version_changed and previous_version:
        logger.info(
            f"Version changed: {previous_version} -> {current_version} "
            "(toast handled by JS)",
            extra={
                "operation": "version_update_notification",
                "previous_version": previous_version,
                "current_version": current_version,
            },
        )
        return no_update, no_update

    import app  # noqa: PLC0415

    if not app.VERSION_CHECK_RESULT:
        return no_update, no_update

    progress = app.VERSION_CHECK_RESULT

    if progress.state == UpdateState.MANUAL_UPDATE_REQUIRED:
        logger.info(
            "Manual update required - displaying instructions after init",
            extra={
                "current_version": progress.current_version,
                "available_version": progress.available_version,
            },
        )

        import dash_bootstrap_components as dbc  # noqa: PLC0415

        toast = create_toast(
            [
                html.Div(
                    f"Version {progress.available_version} is available. "
                    f"You are running {progress.current_version} from source code."
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
            icon="arrow-circle-up",
        )

        return toast, True

    if progress.state == UpdateState.AVAILABLE:
        logger.info(
            "Update available - displaying toast after init",
            extra={
                "current_version": progress.current_version,
                "available_version": progress.available_version,
            },
        )

        import dash_bootstrap_components as dbc  # noqa: PLC0415

        toast = create_toast(
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

        return toast, True

    return no_update, no_update
