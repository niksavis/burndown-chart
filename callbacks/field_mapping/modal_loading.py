"""Modal loading state management for field mapping.

Manages loading overlays and button states based on metadata availability.
"""

import logging

from dash import Input, Output, State, callback, no_update

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
    """Manage modal loading state based on app-level metadata store.

    Shows loading overlay while metadata is being fetched (metadata is None),
    disables buttons until metadata is available, and shows appropriate
    status messages.

    Args:
        is_open: Whether modal is open
        metadata: App-level JIRA metadata (None while loading, dict when loaded)

    Returns:
        Tuple of (
            status_alert,
            auto_configure_disabled,
            save_disabled,
            validate_disabled,
            overlay_style,
            toast_notification,
        )
    """
    # Style for showing/hiding the loading overlay
    # Note: Use visibility instead of display because
    # Bootstrap's d-flex class has !important.
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

    # Only process when modal is open
    if not is_open:
        return no_update, no_update, no_update, no_update, overlay_hidden, no_update

    # Metadata still loading (None) - show loading overlay, disable buttons
    if metadata is None:
        logger.info("[FieldMapping] Metadata loading, showing overlay")
        return (
            None,  # No status message while loading
            True,  # Disable auto-configure
            True,  # Disable save
            True,  # Disable validate
            overlay_visible,  # Show loading overlay
            no_update,  # No toast
        )

    # Metadata has error - show error message, disable auto-configure
    if metadata.get("error"):
        error_msg = metadata.get("error", "Unknown error")
        logger.warning(f"[FieldMapping] Metadata has error: {error_msg}")
        return (
            "",  # Clear inline status
            True,  # Disable auto-configure
            False,  # Keep save enabled (user might want to save partial config)
            True,  # Disable validate (needs metadata)
            overlay_hidden,  # Hide loading overlay
            create_error_toast(
                "Please configure JIRA connection first in the Connect tab.",
                header="JIRA Not Configured",
            ),
        )

    # Metadata loaded successfully - enable buttons, show success toast
    fields = metadata.get("fields", [])
    projects = metadata.get("projects", [])
    issue_types = metadata.get("issue_types", [])
    statuses = metadata.get("statuses", [])

    logger.info(
        f"[FieldMapping] Metadata ready: {len(fields)} fields, "
        f"{len(projects)} projects, {len(issue_types)} issue types, "
        f"{len(statuses)} statuses"
    )

    # Show brief success toast notification
    toast = create_success_toast(
        f"{len(fields)} fields, {len(projects)} projects, "
        f"{len(issue_types)} issue types available.",
        header="Metadata Ready",
    )

    return (
        no_update,  # Don't clear status - preserve validation messages
        False,  # Enable auto-configure
        False,  # Enable save
        False,  # Enable validate
        overlay_hidden,  # Hide loading overlay
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
    """Show/hide inline warning banner before auto-configure.

    Args:
        auto_click: Auto-configure button clicks
        cancel_click: Cancel button clicks
        is_open: Current banner visibility state

    Returns:
        Updated banner visibility state
    """
    from dash import ctx

    if not ctx.triggered_id:
        return no_update

    # Toggle banner state
    return not is_open
