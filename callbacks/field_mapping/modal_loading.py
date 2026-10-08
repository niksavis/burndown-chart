import logging

from dash import Input, Output, State, callback, ctx, no_update

from ui.toast_notifications import create_error_toast, create_success_toast

logger = logging.getLogger(__name__)


@callback(
    [
        Output("field-mapping-status", "children", allow_duplicate=True),
        Output("auto-configure-button", "disabled"),
        Output("field-mapping-save-button", "disabled"),
        Output("validate-mappings-button", "disabled"),
        Output("metadata-loading-overlay", "style"),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    [
        Input("field-mapping-modal", "is_open"),
        Input("jira-metadata-store", "data"),
    ],
    prevent_initial_call=True,
)
def manage_modal_loading_state(is_open: bool, metadata: dict):

    overlay_hidden = {
        "zIndex": 1000,
        "visibility": "hidden",
        "opacity": 0,
        "pointerEvents": "none",
    }
    overlay_visible = {
        "zIndex": 1000,
        "visibility": "visible",
        "opacity": 1,
        "pointerEvents": "auto",
        "backgroundColor": "rgba(255, 255, 255, 0.95)",
    }

    if not is_open:
        return no_update, no_update, no_update, no_update, overlay_hidden, no_update

    if metadata is None:
        logger.info("[FieldMapping] Metadata loading, showing overlay")
        return (
            None,
            True,
            True,
            True,
            overlay_visible,
            no_update,
        )

    if metadata.get("error"):
        error_msg = metadata.get("error", "Unknown error")
        logger.warning(f"[FieldMapping] Metadata has error: {error_msg}")
        return (
            "",
            True,
            False,
            True,
            overlay_hidden,
            create_error_toast(
                "Please configure JIRA connection first in the Connect tab.",
                header="JIRA Not Configured",
            ),
        )

    fields = metadata.get("fields", [])
    projects = metadata.get("projects", [])
    issue_types = metadata.get("issue_types", [])
    statuses = metadata.get("statuses", [])

    logger.info(
        f"[FieldMapping] Metadata ready: {len(fields)} fields, "
        f"{len(projects)} projects, {len(issue_types)} issue types, "
        f"{len(statuses)} statuses"
    )

    toast = create_success_toast(
        f"{len(fields)} fields, {len(projects)} projects, "
        f"{len(issue_types)} issue types available.",
        header="Metadata Ready",
    )

    return (
        no_update,
        False,
        False,
        False,
        overlay_hidden,
        toast,
    )


@callback(
    Output("auto-configure-warning-banner", "is_open"),
    [
        Input("auto-configure-button", "n_clicks"),
        Input("auto-configure-cancel-inline", "n_clicks"),
    ],
    State("auto-configure-warning-banner", "is_open"),
    prevent_initial_call=True,
)
def toggle_auto_configure_warning(auto_click, cancel_click, is_open):

    if not ctx.triggered_id:
        return no_update

    return not is_open
