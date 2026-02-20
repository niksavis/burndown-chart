"""
Callbacks for unified profile management UI.

Handles profile create/rename/duplicate/delete via single unified modal.
"""

import logging
import time

from dash import Input, Output, State, callback, ctx, html, no_update

from data.profile_manager import (
    create_profile,
    delete_profile,
    duplicate_profile,
    get_active_profile,
    list_profiles,
    rename_profile,
    switch_profile,
)
from ui.toast_notifications import (
    create_error_toast,
    create_success_toast,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================


def _validate_profile_name(
    name: str, exclude_profile_id: str | None = None
) -> tuple:
    """Validate profile name with optional exclusion for rename.

    Args:
        name: Profile name to validate
        exclude_profile_id: Profile ID to exclude from duplicate check (for rename)

    Returns:
        Tuple of (is_valid, normalized_name, valid_flag, invalid_flag, feedback)
    """
    if not name or not name.strip():
        return (False, "", False, True, "Profile name is required")

    name = name.strip()
    if len(name) > 100:
        return (
            False,
            "",
            False,
            True,
            "Profile name too long (max 100 characters)",
        )

    # Check for duplicate names (excluding current profile for rename)
    existing_profiles = list_profiles()
    for profile in existing_profiles:
        if exclude_profile_id and profile["id"] == exclude_profile_id:
            continue
        if profile["name"].lower() == name.lower():
            return (
                False,
                "",
                False,
                True,
                "Profile with this name already exists",
            )

    return (True, name, True, False, "")


# ============================================================================
# Profile Selector Refresh
# ============================================================================


@callback(
    [
        Output("profile-selector", "options"),
        Output("profile-selector", "value"),
        Output("rename-profile-btn", "disabled"),
        Output("duplicate-profile-btn", "disabled"),
        Output("delete-profile-btn", "disabled"),
        Output("create-profile-btn", "className"),
    ],
    [
        Input("profile-form-modal", "is_open"),
        Input("delete-profile-modal", "is_open"),
        Input("profile-switch-trigger", "data"),
        Input("metrics-refresh-trigger", "data"),  # NEW: Refresh after import
    ],
    prevent_initial_call=True,
)
def refresh_profile_selector(
    form_modal_open, delete_modal_open, switch_trigger, metrics_refresh
):
    """Refresh profile dropdown options when modals close, profiles switch, or data refreshes (import), and manage button states."""
    profiles = list_profiles()
    active_profile = get_active_profile()
    active_profile_id = active_profile.id if active_profile else None

    # Build dropdown options with Active indicator
    options = []
    for profile in profiles:
        jira_info = ""
        if profile.get("jira_url"):
            jira_info = f" • {profile['jira_url']}"

        active_indicator = " (Active)" if profile["id"] == active_profile_id else ""
        label = f"{profile['name']}{active_indicator}{jira_info}"
        options.append({"label": label, "value": profile["id"]})

    # Disable rename/duplicate/delete buttons if no profiles
    has_profiles = len(profiles) > 0
    buttons_disabled = not has_profiles

    # Set dropdown value to active profile
    dropdown_value = (
        active_profile_id
        if active_profile_id
        else (profiles[0]["id"] if profiles else None)
    )

    # Highlight New button when no profiles exist
    new_button_class = "me-1 highlight-first-action" if not has_profiles else "me-1"

    return (
        options,
        dropdown_value,
        buttons_disabled,
        buttons_disabled,
        buttons_disabled,
        new_button_class,
    )


# ============================================================================
# Unified Modal Control (Open)
# ============================================================================


@callback(
    [
        Output("profile-form-modal", "is_open", allow_duplicate=True),
        Output("profile-form-mode", "data"),
        Output("profile-form-source-id", "data"),
        Output("profile-form-modal-title", "children"),
        Output("profile-form-name-label", "children"),
        Output("profile-form-name-input", "value"),
        Output("profile-form-description-input", "value"),
        Output("profile-form-description-container", "style"),
        Output("profile-form-context-info", "children"),
        Output("profile-form-confirm-btn", "children"),
    ],
    [
        Input("create-profile-btn", "n_clicks"),
        Input("rename-profile-btn", "n_clicks"),
        Input("duplicate-profile-btn", "n_clicks"),
    ],
    [State("profile-selector", "value")],
    prevent_initial_call=True,
)
def open_profile_form_modal(
    create_clicks,
    rename_clicks,
    duplicate_clicks,
    selected_profile_id,
):
    """Open modal and configure based on which button was clicked."""
    if not ctx.triggered:
        return no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Get selected profile info for rename/duplicate
    profiles = list_profiles()
    selected_profile = next(
        (p for p in profiles if p["id"] == selected_profile_id), None
    )

    if triggered_id == "create-profile-btn":
        return (
            True,  # is_open
            "create",  # mode
            None,  # source_id
            "Create New Profile",  # modal title
            "Profile Name",  # name label
            "",  # name value (empty)
            "",  # description value (empty)
            {},  # description visible
            "",  # context info (empty)
            [html.I(className="fas fa-plus me-2"), "Create Profile"],  # button
        )

    elif triggered_id == "rename-profile-btn":
        if not selected_profile:
            return no_update

        return (
            True,  # is_open
            "rename",  # mode
            selected_profile_id,  # source_id
            "Rename Profile",  # modal title
            "New Profile Name",  # name label
            selected_profile["name"],  # name value (pre-filled)
            "",  # description value (not used for rename)
            {"display": "none"},  # description hidden
            f"Renaming: {selected_profile['name']}",  # context info
            [html.I(className="fas fa-edit me-2"), "Rename Profile"],  # button
        )

    elif triggered_id == "duplicate-profile-btn":
        if not selected_profile:
            return no_update

        copy_suffix = " (Copy)"
        default_name = f"{selected_profile['name']}{copy_suffix}"

        return (
            True,  # is_open
            "duplicate",  # mode
            selected_profile_id,  # source_id
            "Duplicate Profile",  # modal title
            "New Profile Name",  # name label
            default_name,  # name value (pre-filled with copy)
            selected_profile.get("description", ""),  # description (copied)
            {},  # description visible
            f"Duplicating: {selected_profile['name']}",  # context info
            [html.I(className="fas fa-copy me-2"), "Duplicate Profile"],  # button
        )

    return no_update


# ============================================================================
# Modal Close (Cancel)
# ============================================================================


@callback(
    Output("profile-form-modal", "is_open", allow_duplicate=True),
    Input("profile-form-cancel-btn", "n_clicks"),
    State("profile-form-modal", "is_open"),
    prevent_initial_call=True,
)
def close_profile_form_modal(cancel_clicks, is_open):
    """Close modal when cancel button clicked."""
    if cancel_clicks:
        return False
    return is_open


# ============================================================================
# Real-time Name Validation
# ============================================================================


@callback(
    [
        Output("profile-form-name-input", "valid"),
        Output("profile-form-name-input", "invalid"),
        Output("profile-form-name-feedback-invalid", "children"),
        Output("profile-form-name-feedback-valid", "children"),
    ],
    [
        Input("profile-form-name-input", "value"),
        Input("profile-form-modal", "is_open"),
    ],
    [
        State("profile-form-mode", "data"),
        State("profile-form-source-id", "data"),
    ],
    prevent_initial_call=True,
)
def validate_profile_name_realtime(name, modal_open, mode, source_id):
    """Real-time validation of profile name as user types."""
    # Reset when modal closed
    if not modal_open:
        return False, False, "", ""

    # Empty state (neutral)
    if not name or not name.strip():
        return False, False, "", ""

    # For rename, exclude current profile from duplicate check
    exclude_id = source_id if mode == "rename" else None
    is_valid, _, valid_flag, invalid_flag, feedback = _validate_profile_name(
        name, exclude_profile_id=exclude_id
    )

    if is_valid:
        return True, False, "", "Profile name is available"
    else:
        return False, True, feedback, ""


# ============================================================================
# Form Submission (Create/Rename/Duplicate)
# ============================================================================


@callback(
    [
        Output("profile-form-error", "children"),
        Output("profile-form-error", "className"),
        Output("profile-form-modal", "is_open", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
        Output("profile-switch-trigger", "data", allow_duplicate=True),
    ],
    Input("profile-form-confirm-btn", "n_clicks"),
    [
        State("profile-form-mode", "data"),
        State("profile-form-source-id", "data"),
        State("profile-form-name-input", "value"),
        State("profile-form-description-input", "value"),
    ],
    prevent_initial_call=True,
)
def handle_profile_form_submit(n_clicks, mode, source_id, name, description):
    """Handle form submission for create/rename/duplicate operations."""
    if not n_clicks:
        return no_update

    # Validate name
    exclude_id = source_id if mode == "rename" else None
    is_valid, validated_name, _, _, error_msg = _validate_profile_name(
        name, exclude_profile_id=exclude_id
    )

    if not is_valid:
        return (
            error_msg,
            "alert alert-danger",
            no_update,  # keep modal open
            no_update,
            no_update,  # don't trigger refresh on validation error
        )

    try:
        if mode == "create":
            # Create new profile with default settings
            settings = {
                "description": description or "",
                "pert_factor": 1.2,
                "deadline": None,  # CRITICAL: Use None for empty dates (not "")
                "data_points_count": 20,
                "jira_config": {},
                "field_mappings": {},
            }
            profile_id = create_profile(validated_name, settings)

            # Switch to new profile
            switch_profile(profile_id)

            logger.info(f"[UI] Created and switched to profile: {validated_name}")

            trigger_value = int(time.time() * 1000)

            return (
                "",
                "alert alert-danger d-none",
                False,  # Close modal on success
                create_success_toast(
                    f"Profile '{validated_name}' created successfully"
                ),
                trigger_value,  # Trigger dropdown refresh
            )

        elif mode == "rename":
            # Rename existing profile
            if not source_id:
                raise ValueError("No profile selected for rename")

            rename_profile(source_id, validated_name)

            logger.info(f"[UI] Renamed profile to: {validated_name}")

            trigger_value = int(time.time() * 1000)

            return (
                "",
                "alert alert-danger d-none",
                False,  # Close modal on success
                create_success_toast(
                    f"Profile renamed to '{validated_name}' successfully"
                ),
                trigger_value,  # Trigger dropdown refresh to show new name
            )

        elif mode == "duplicate":
            # Duplicate existing profile
            if not source_id:
                raise ValueError("No profile selected for duplication")

            new_profile_id = duplicate_profile(
                source_id, validated_name, description or ""
            )

            # Switch to duplicated profile
            switch_profile(new_profile_id)

            logger.info(f"[UI] Duplicated and switched to profile: {validated_name}")

            trigger_value = int(time.time() * 1000)

            return (
                "",
                "alert alert-danger d-none",
                False,  # Close modal on success
                create_success_toast(
                    f"Profile '{validated_name}' duplicated successfully"
                ),
                trigger_value,  # Trigger dropdown refresh
            )

        else:
            raise ValueError(f"Unknown mode: {mode}")

    except Exception as e:
        logger.error(f"[UI] Error in profile {mode} operation: {e}")
        error_message = str(e)

        return (
            error_message,
            "alert alert-danger",
            no_update,  # keep modal open
            create_error_toast(f"Failed to {mode} profile: {error_message}"),
            no_update,  # don't trigger refresh on error
        )


# ============================================================================
# Delete Profile Modal (unchanged - keep existing logic)
# ============================================================================


@callback(
    [
        Output("delete-profile-modal", "is_open"),
        Output("delete-profile-target-id", "data"),
    ],
    [
        Input("delete-profile-btn", "n_clicks"),
        Input("cancel-delete-profile", "n_clicks"),
    ],
    [
        State("delete-profile-modal", "is_open"),
        State("profile-selector", "value"),
    ],
    prevent_initial_call=True,
)
def toggle_delete_profile_modal(delete_btn, cancel_btn, is_open, selected_profile_id):
    """Toggle delete profile confirmation modal and capture profile ID."""
    if not ctx.triggered:
        return is_open, no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "delete-profile-btn":
        # Capture the selected profile ID when opening modal
        return True, selected_profile_id
    elif triggered_id == "cancel-delete-profile":
        # Clear the target ID when closing
        return False, None

    return is_open, no_update


@callback(
    Output("delete-profile-warning", "children"),
    Input("delete-profile-modal", "is_open"),
    State("delete-profile-target-id", "data"),
    prevent_initial_call=True,
)
def update_delete_warning(is_open, profile_id):
    """Update delete modal with profile name from stored target ID."""
    if not is_open or not profile_id:
        return ""

    profiles = list_profiles()
    profile = next((p for p in profiles if p["id"] == profile_id), None)

    if profile:
        return [
            "You are about to permanently delete the profile: ",
            html.Strong(profile["name"]),
        ]

    return "Error: Profile not found"


@callback(
    Output("confirm-delete-profile", "disabled"),
    Input("delete-confirmation-input", "value"),
    prevent_initial_call=True,
)
def validate_delete_confirmation(confirmation_text):
    """Enable delete button only when DELETE is typed."""
    return confirmation_text != "DELETE"


@callback(
    [
        Output("delete-profile-error", "children"),
        Output("delete-profile-error", "className"),
        Output("delete-profile-modal", "is_open", allow_duplicate=True),
        Output("delete-confirmation-input", "value"),
        Output("app-notifications", "children", allow_duplicate=True),
        Output("profile-switch-trigger", "data", allow_duplicate=True),
        Output("metrics-refresh-trigger", "data", allow_duplicate=True),
    ],
    Input("confirm-delete-profile", "n_clicks"),
    [
        State("delete-profile-target-id", "data"),
        State("delete-confirmation-input", "value"),
    ],
    prevent_initial_call=True,
)
def handle_delete_profile(n_clicks, profile_id, confirmation_text):
    """Handle profile deletion using stored target ID."""
    if not n_clicks or confirmation_text != "DELETE":
        return no_update

    profiles = list_profiles()
    profile = next((p for p in profiles if p["id"] == profile_id), None)

    if not profile:
        return (
            "Profile not found",
            "alert alert-danger",
            no_update,
            no_update,
            create_error_toast("Profile not found"),
            no_update,
            no_update,
        )

    profile_name = profile["name"]

    try:
        delete_profile(profile_id)

        logger.info(f"[UI] Deleted profile: {profile_name}")

        # Trigger dropdown refresh and data reload for newly active profile
        import time

        trigger_value = int(time.time() * 1000)

        return (
            "",
            "alert alert-danger d-none",
            False,  # close modal
            "",  # clear confirmation input
            create_success_toast(f"Profile '{profile_name}' deleted successfully"),
            trigger_value,  # trigger dropdown refresh
            trigger_value,  # trigger data reload for newly active profile
        )

    except Exception as e:
        logger.error(f"[UI] Error deleting profile '{profile_id}': {e}")
        error_message = str(e)

        return (
            error_message,
            "alert alert-danger",
            no_update,  # keep modal open
            no_update,
            create_error_toast(f"Failed to delete profile: {error_message}"),
            no_update,
            no_update,
        )


# ============================================================================
# Profile Switching
# ============================================================================


@callback(
    [
        Output("app-notifications", "children", allow_duplicate=True),
        Output("profile-switch-trigger", "data", allow_duplicate=True),
    ],
    Input("profile-selector", "value"),
    prevent_initial_call=True,
)
def handle_profile_switch(new_profile_id):
    """Handle profile switching from dropdown."""
    if not new_profile_id:
        return no_update, no_update

    # Check if already active - prevents infinite loop when refresh_profile_selector
    # sets the dropdown value to the active profile
    active_profile = get_active_profile()
    if active_profile and active_profile.id == new_profile_id:
        return no_update, no_update

    try:
        profiles = list_profiles()
        profile = next((p for p in profiles if p["id"] == new_profile_id), None)

        if not profile:
            return create_error_toast("Profile not found"), no_update

        switch_profile(new_profile_id)

        logger.info(f"[UI] Switched to profile: {profile['name']}")

        # Increment trigger to refresh dropdown with new Active indicator
        trigger_value = int(time.time() * 1000)  # Use timestamp to ensure unique value

        return (
            create_success_toast(f"Switched to profile: {profile['name']}"),
            trigger_value,
        )

    except Exception as e:
        logger.error(f"[UI] Error switching profile: {e}")
        return create_error_toast(f"Failed to switch profile: {e}"), no_update
