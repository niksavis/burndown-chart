"""
Callbacks for profile management UI interactions.

Handles profile creation, switching, duplication, and deletion.
"""

import logging
from dash import callback, Output, Input, State, no_update, ctx

from data.profile_manager import (
    create_profile,
    switch_profile,
    delete_profile,
    duplicate_profile,
    list_profiles,
    get_active_profile,
)
from ui.toast_notifications import (
    create_success_toast,
    create_error_toast,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================


def _toggle_modal(trigger_button_id: str, cancel_buttons: list, is_open: bool) -> bool:
    """Reusable modal toggle logic.

    Args:
        trigger_button_id: ID of button that opens modal
        cancel_buttons: List of button IDs that close modal
        is_open: Current modal state

    Returns:
        New modal state (True=open, False=closed)
    """
    if not ctx.triggered:
        return is_open

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == trigger_button_id:
        return True
    elif triggered_id in cancel_buttons:
        return False
    return is_open


def _validate_profile_name(name: str) -> tuple:
    """Validate profile name with consistent rules.

    Args:
        name: Profile name to validate

    Returns:
        Tuple of (is_valid, error_message, valid_flag, invalid_flag, feedback)
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

    # Check for duplicate names
    existing_profiles = list_profiles()
    if any(p["name"].lower() == name.lower() for p in existing_profiles):
        return (
            False,
            "",
            False,
            True,
            "Profile with this name already exists",
        )

    return (True, name, True, False, "")


# ============================================================================
# Callbacks
# ============================================================================


@callback(
    [
        Output("profile-selector", "options"),
        Output("profile-selector", "value"),
        Output("duplicate-profile-btn", "disabled"),
        Output("delete-profile-btn", "disabled"),
    ],
    [
        Input("create-profile-modal", "is_open"),
        Input("duplicate-profile-modal", "is_open"),
        Input("delete-profile-modal", "is_open"),
    ],
)
def refresh_profile_selector(create_open, duplicate_open, delete_open):
    """Refresh profile dropdown when modals close and manage button states."""
    profiles = list_profiles()
    active_profile = get_active_profile()
    active_profile_id = active_profile.id if active_profile else None

    # Build dropdown options with Active indicator for current profile
    options = []
    for profile in profiles:
        # Create label with metadata
        jira_info = ""
        if profile.get("jira_url"):
            jira_info = f" • {profile['jira_url']}"

        # Add Active indicator for the currently active profile
        active_indicator = " (Active)" if profile["id"] == active_profile_id else ""
        label = f"{profile['name']}{active_indicator}{jira_info}"
        options.append({"label": label, "value": profile["id"]})

    # Determine current value
    value = (
        active_profile.id if active_profile else (profiles[0]["id"] if profiles else "")
    )

    # Disable duplicate/delete buttons if no profiles
    has_profiles = len(profiles) > 0
    buttons_disabled = not has_profiles

    return options, value, buttons_disabled, buttons_disabled


@callback(
    Output("create-profile-modal", "is_open"),
    [
        Input("create-profile-btn", "n_clicks"),
        Input("cancel-create-profile", "n_clicks"),
        # Note: confirm-create-profile is NOT listed here because
        # handle_create_profile controls modal close on success.
        # This prevents race condition where modal closes before creation completes.
    ],
    [State("create-profile-modal", "is_open")],
    prevent_initial_call=True,
)
def toggle_create_profile_modal(create_btn, cancel_btn, is_open):
    """Toggle create profile modal open/close (open and cancel only)."""
    return _toggle_modal(
        "create-profile-btn",
        ["cancel-create-profile"],
        is_open,
    )


@callback(
    [
        Output("new-profile-name", "valid"),
        Output("new-profile-name", "invalid"),
        Output("profile-name-feedback", "children"),
        Output("profile-name-feedback-valid", "children"),
    ],
    [
        Input("new-profile-name", "value"),
        Input("create-profile-modal", "is_open"),
    ],
    prevent_initial_call=True,
)
def validate_profile_name_realtime(name, modal_is_open):
    """Real-time validation of profile name as user types.

    This provides immediate feedback without waiting for confirm button.
    """
    # Reset validation when modal opens/closes
    if not modal_is_open:
        return False, False, "", ""

    # If empty, show neither valid nor invalid (neutral state)
    if not name or not name.strip():
        return False, False, "", ""

    # Use shared validation logic
    is_valid, _, valid_flag, invalid_flag, feedback = _validate_profile_name(name)

    if is_valid:
        return True, False, "", "Profile name is available"
    else:
        return False, True, feedback, ""


@callback(
    [
        Output("create-profile-error", "children"),
        Output("create-profile-error", "className"),
        Output("new-profile-name", "valid", allow_duplicate=True),
        Output("new-profile-name", "invalid", allow_duplicate=True),
        Output("profile-name-feedback", "children", allow_duplicate=True),
        Output("profile-name-feedback-valid", "children", allow_duplicate=True),
        Output("create-profile-modal", "is_open", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    [Input("confirm-create-profile", "n_clicks")],
    [State("new-profile-name", "value"), State("new-profile-description", "value")],
    prevent_initial_call=True,
)
def handle_create_profile(n_clicks, name, description):
    """Handle profile creation.

    This callback controls modal close on success to ensure profile is created
    and switched to BEFORE refresh_profile_selector fires. Prevents race condition.
    """
    if not n_clicks:
        return "", "alert alert-danger d-none", None, None, "", "", no_update, no_update

    is_valid, validated_name, valid_flag, invalid_flag, feedback = (
        _validate_profile_name(name)
    )
    if not is_valid:
        # Keep modal open on validation error
        return (
            "",
            "alert alert-danger d-none",
            valid_flag,
            invalid_flag,
            feedback,
            "",
            no_update,
            no_update,
        )

    name = validated_name

    try:
        # Create profile with default settings
        settings = {
            "description": description or "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }
        profile_id = create_profile(name, settings)

        # Switch to newly created profile automatically
        switch_profile(profile_id)

        logger.info(
            f"Created new profile: {name} (ID: {profile_id}) and switched to it"
        )

        # Show success toast notification
        toast = create_success_toast(
            f"Profile '{name}' created and activated.",
            header="Profile Created",
        )

        # Close modal on success
        return "", "alert alert-danger d-none", True, False, "", "", False, toast
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to create profile: {error_msg}")
        # Keep modal open on error
        return (
            error_msg,
            "alert alert-danger",
            False,
            True,
            "Failed to create profile",
            "",
            no_update,
            no_update,
        )


@callback(
    Output("duplicate-profile-modal", "is_open"),
    [
        Input("duplicate-profile-btn", "n_clicks"),
        Input("cancel-duplicate-profile", "n_clicks"),
        # Note: confirm-duplicate-profile is NOT listed here because
        # handle_duplicate_profile controls modal close on success.
        # This prevents race condition where modal closes before profile creation completes.
    ],
    [State("duplicate-profile-modal", "is_open")],
)
def toggle_duplicate_profile_modal(duplicate_btn, cancel_btn, is_open):
    """Toggle duplicate profile modal open/close (open and cancel only)."""
    return _toggle_modal(
        "duplicate-profile-btn",
        ["cancel-duplicate-profile"],
        is_open,
    )


@callback(
    [
        Output("duplicate-profile-info", "children"),
        Output("duplicate-profile-name", "value"),
    ],
    [Input("duplicate-profile-modal", "is_open")],
    [State("profile-selector", "value")],
)
def populate_duplicate_modal(is_open, selected_profile_id):
    """Populate duplicate modal with current profile info."""
    if not is_open or not selected_profile_id:
        return "", ""

    profiles = list_profiles()
    current_profile = next(
        (p for p in profiles if p["id"] == selected_profile_id), None
    )

    if not current_profile:
        return "Profile not found.", ""

    info_text = f"Creating a copy of '{current_profile['name']}' with all its settings and queries."
    suggested_name = f"{current_profile['name']} Copy"

    return info_text, suggested_name


@callback(
    [
        Output("duplicate-profile-error", "children"),
        Output("duplicate-profile-error", "className"),
        Output("duplicate-profile-name", "valid"),
        Output("duplicate-profile-name", "invalid"),
        Output("duplicate-name-feedback", "children"),
        Output("duplicate-profile-modal", "is_open", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    [Input("confirm-duplicate-profile", "n_clicks")],
    [
        State("duplicate-profile-name", "value"),
        State("duplicate-profile-description", "value"),
        State("profile-selector", "value"),
    ],
    prevent_initial_call=True,
)
def handle_duplicate_profile(n_clicks, name, description, source_profile_id):
    """Handle profile duplication - creates complete copy of source profile.

    This callback controls modal close on success to ensure profile is created
    BEFORE refresh_profile_selector fires. Prevents race condition.
    """
    if not n_clicks:
        return "", "alert alert-danger d-none", None, None, "", no_update, no_update

    if not source_profile_id:
        # Keep modal open on validation error
        return (
            "No source profile selected",
            "alert alert-danger",
            False,
            True,
            "Select a profile to duplicate",
            no_update,
            no_update,
        )

    is_valid, validated_name, valid_flag, invalid_flag, feedback = (
        _validate_profile_name(name)
    )
    if not is_valid:
        # Keep modal open on validation error
        return (
            "",
            "alert alert-danger d-none",
            valid_flag,
            invalid_flag,
            feedback,
            no_update,
            no_update,
        )

    name = validated_name

    try:
        # Use duplicate_profile to create a complete copy
        profile_id = duplicate_profile(source_profile_id, name, description or "")

        # Switch to newly duplicated profile automatically
        switch_profile(profile_id)

        logger.info(
            f"Duplicated profile '{source_profile_id}' to: {name} (ID: {profile_id}) and switched to it"
        )

        # Show success toast notification
        toast = create_success_toast(
            f"Profile '{name}' created and activated.",
            header="Profile Duplicated",
        )

        # Close modal on success - triggers refresh_profile_selector
        return "", "alert alert-danger d-none", True, False, "", False, toast
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to duplicate profile: {error_msg}")

        # Show error toast notification
        error_toast = create_error_toast(
            f"Failed to duplicate profile: {error_msg}",
            header="Duplication Failed",
        )

        # Keep modal open on error
        return (
            error_msg,
            "alert alert-danger",
            False,
            True,
            "Failed to duplicate profile",
            no_update,
            error_toast,
        )


@callback(
    Output("delete-profile-modal", "is_open"),
    [
        Input("delete-profile-btn", "n_clicks"),
        Input("cancel-delete-profile", "n_clicks"),
        # Note: confirm-delete-profile is NOT listed here because
        # handle_delete_profile controls modal close on success.
        # This prevents race condition where modal closes before deletion completes.
    ],
    [State("delete-profile-modal", "is_open")],
)
def toggle_delete_profile_modal(delete_btn, cancel_btn, is_open):
    """Toggle delete profile modal open/close (open and cancel only)."""
    return _toggle_modal(
        "delete-profile-btn",
        ["cancel-delete-profile"],
        is_open,
    )


@callback(
    Output("delete-profile-warning", "children"),
    [Input("delete-profile-modal", "is_open")],
    [State("profile-selector", "value")],
    prevent_initial_call=True,
)
def populate_delete_modal(is_open, selected_profile_id):
    """Populate delete modal with profile warning."""
    if not is_open or not selected_profile_id:
        return ""

    profiles = list_profiles()
    current_profile = next(
        (p for p in profiles if p["id"] == selected_profile_id), None
    )

    if not current_profile:
        return "Profile not found."

    query_count = current_profile.get("query_count", 0)
    warning = f"You are about to delete the profile '{current_profile['name']}'"

    if query_count > 0:
        warning += f" which contains {query_count} queries."
    else:
        warning += "."

    return warning


@callback(
    [
        Output("confirm-delete-profile", "disabled"),
        Output("delete-confirmation-input", "value"),
    ],
    [
        Input("delete-confirmation-input", "value"),
        Input("delete-profile-modal", "is_open"),
    ],
)
def enable_delete_button(confirmation_text, modal_open):
    """Enable delete button only when 'DELETE' is typed. Clear input when modal closes."""
    if not ctx.triggered:
        return True, ""

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Clear input when modal closes
    if triggered_id == "delete-profile-modal" and not modal_open:
        return True, ""

    # Enable/disable button based on input
    return confirmation_text != "DELETE", no_update


@callback(
    [
        Output("delete-profile-error", "children"),
        Output("delete-profile-error", "className"),
        Output("profile-selector", "options", allow_duplicate=True),
        Output("profile-selector", "value", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
        Output("delete-profile-modal", "is_open", allow_duplicate=True),
    ],
    [Input("confirm-delete-profile", "n_clicks")],
    [State("profile-selector", "value"), State("delete-confirmation-input", "value")],
    prevent_initial_call=True,
)
def handle_delete_profile(n_clicks, profile_id, confirmation):
    """Handle profile deletion.

    This callback controls modal close on success to ensure profile is deleted
    BEFORE refresh_profile_selector fires. Prevents race condition.
    """
    if not n_clicks or confirmation != "DELETE":
        return (
            "",
            "alert alert-danger d-none",
            no_update,
            no_update,
            no_update,
            no_update,
        )

    if not profile_id:
        return (
            "No profile selected.",
            "alert alert-danger",
            no_update,
            no_update,
            no_update,
            no_update,  # Keep modal open
        )

    try:
        profiles = list_profiles()
        profile_to_delete = next((p for p in profiles if p["id"] == profile_id), None)
        if not profile_to_delete:
            error_notification = create_error_toast(
                "Profile not found.",
                header="Delete Failed",
            )
            return (
                "",
                "alert alert-danger d-none",
                no_update,
                no_update,
                error_notification,
                False,  # Close modal
            )

        delete_profile(profile_id)
        logger.info(f"Deleted profile: {profile_to_delete['name']} (ID: {profile_id})")

        updated_profiles = list_profiles()
        new_active_profile = get_active_profile()
        new_active_id = (
            new_active_profile.id
            if new_active_profile
            else (updated_profiles[0]["id"] if updated_profiles else "")
        )

        # Build options with consistent format (Active indicator + JIRA info)
        profile_options = []
        for p in updated_profiles:
            jira_info = ""
            if p.get("jira_url"):
                jira_info = f" • {p['jira_url']}"
            active_indicator = " (Active)" if p["id"] == new_active_id else ""
            label = f"{p['name']}{active_indicator}{jira_info}"
            profile_options.append({"label": label, "value": p["id"]})

        # Return success with no error message
        # The modal will close (no error to keep it open)
        # Show toast notification for successful deletion
        notification = create_success_toast(
            f"Deleted profile: {profile_to_delete['name']}",
            header="Profile Deleted",
            icon="trash",
        )

        # Close modal on success
        return (
            "",
            "alert alert-danger d-none",
            profile_options,
            new_active_id,
            notification,
            False,  # Close modal
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to delete profile: {error_msg}")
        return (
            error_msg,
            "alert alert-danger",
            no_update,
            no_update,
            no_update,
            no_update,
        )  # Keep modal open on error


@callback(
    [
        Output("app-notifications", "children", allow_duplicate=True),
        Output("profile-selector", "options", allow_duplicate=True),
    ],
    [Input("profile-selector", "value")],
    prevent_initial_call=True,
)
def handle_profile_switch(selected_profile_id):
    """Handle profile switching and refresh profile dropdown to show star marker.

    Note: Query dropdown is updated by populate_query_dropdown callback in query_switching.py
    which triggers on profile-selector value changes.
    """
    if not selected_profile_id:
        return no_update, no_update

    try:
        active_profile = get_active_profile()
        if active_profile and active_profile.id == selected_profile_id:
            return no_update, no_update  # Already active

        switch_profile(selected_profile_id)
        logger.info(f"Switched to profile: {selected_profile_id}")

        # Get profile name for notification
        active_profile = get_active_profile()
        profile_name = active_profile.name if active_profile else selected_profile_id

        # Show success notification
        notification = create_success_toast(
            f"Switched to profile: {profile_name}",
            header="Profile Switched",
        )

        # Update dropdown options to reflect new Active indicator
        profiles = list_profiles()
        active_profile_id = active_profile.id if active_profile else None
        profile_options = []
        for p in profiles:
            jira_info = ""
            if p.get("jira_url"):
                jira_info = f" • {p['jira_url']}"
            active_indicator = " (Active)" if p["id"] == active_profile_id else ""
            label = f"{p['name']}{active_indicator}{jira_info}"
            profile_options.append({"label": label, "value": p["id"]})

        return notification, profile_options
    except Exception as e:
        logger.error(f"Failed to switch profile: {e}")
        return no_update, no_update
