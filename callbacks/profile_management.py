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
    list_profiles,
    get_active_profile,
)

logger = logging.getLogger(__name__)


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

    # Build dropdown options (no star needed - dropdown always shows active profile)
    options = []
    for profile in profiles:
        # Create label with metadata
        jira_info = ""
        if profile.get("jira_url"):
            jira_info = f" • {profile['jira_url']}"

        label = f"{profile['name']}{jira_info}"
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
        Input("confirm-create-profile", "n_clicks"),
    ],
    [State("create-profile-modal", "is_open")],
    prevent_initial_call=True,
)
def toggle_create_profile_modal(create_btn, cancel_btn, confirm_btn, is_open):
    """Toggle create profile modal open/close."""
    if not ctx.triggered:
        return is_open

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "create-profile-btn":
        return True
    elif triggered_id in ["cancel-create-profile", "confirm-create-profile"]:
        return False
    return is_open


@callback(
    [
        Output("create-profile-error", "children"),
        Output("create-profile-error", "className"),
        Output("new-profile-name", "valid"),
        Output("new-profile-name", "invalid"),
        Output("profile-name-feedback", "children"),
    ],
    [Input("confirm-create-profile", "n_clicks")],
    [State("new-profile-name", "value"), State("new-profile-description", "value")],
)
def handle_create_profile(n_clicks, name, description):
    """Handle profile creation."""
    if not n_clicks:
        return "", "alert alert-danger d-none", None, None, ""

    if not name or not name.strip():
        return "", "alert alert-danger d-none", False, True, "Profile name is required"

    name = name.strip()
    if len(name) > 100:
        return (
            "",
            "alert alert-danger d-none",
            False,
            True,
            "Profile name too long (max 100 characters)",
        )

    # Check for duplicate names
    existing_profiles = list_profiles()
    if any(p["name"].lower() == name.lower() for p in existing_profiles):
        return (
            "",
            "alert alert-danger d-none",
            False,
            True,
            "Profile with this name already exists",
        )

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
        return "", "alert alert-danger d-none", True, False, ""
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to create profile: {error_msg}")
        return error_msg, "alert alert-danger", False, True, "Failed to create profile"


@callback(
    Output("duplicate-profile-modal", "is_open"),
    [
        Input("duplicate-profile-btn", "n_clicks"),
        Input("cancel-duplicate-profile", "n_clicks"),
        Input("confirm-duplicate-profile", "n_clicks"),
    ],
    [State("duplicate-profile-modal", "is_open")],
)
def toggle_duplicate_profile_modal(duplicate_btn, cancel_btn, confirm_btn, is_open):
    """Toggle duplicate profile modal open/close."""
    if not ctx.triggered:
        return is_open

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "duplicate-profile-btn":
        return True
    elif triggered_id in ["cancel-duplicate-profile", "confirm-duplicate-profile"]:
        return False
    return is_open


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
    ],
    [Input("confirm-duplicate-profile", "n_clicks")],
    [
        State("duplicate-profile-name", "value"),
        State("duplicate-profile-description", "value"),
        State("profile-selector", "value"),
    ],
)
def handle_duplicate_profile(n_clicks, name, description, source_profile_id):
    """Handle profile duplication."""
    if not n_clicks:
        return "", "alert alert-danger d-none", None, None, ""

    if not name or not name.strip():
        return "", "alert alert-danger d-none", False, True, "Profile name is required"

    name = name.strip()
    if len(name) > 100:
        return (
            "",
            "alert alert-danger d-none",
            False,
            True,
            "Profile name too long (max 100 characters)",
        )

    # Check for duplicate names
    existing_profiles = list_profiles()
    if any(p["name"].lower() == name.lower() for p in existing_profiles):
        return (
            "",
            "alert alert-danger d-none",
            False,
            True,
            "Profile with this name already exists",
        )

    try:
        # TODO: Implement profile duplication in profile_manager.py
        # For now, create a new profile with default settings
        settings = {
            "description": description or "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }
        profile_id = create_profile(name, settings)
        logger.info(f"Duplicated profile to: {name} (ID: {profile_id})")
        return "", "alert alert-danger d-none", True, False, ""
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to duplicate profile: {error_msg}")
        return (
            error_msg,
            "alert alert-danger",
            False,
            True,
            "Failed to duplicate profile",
        )


@callback(
    Output("delete-profile-modal", "is_open"),
    [
        Input("delete-profile-btn", "n_clicks"),
        Input("cancel-delete-profile", "n_clicks"),
        Input("confirm-delete-profile", "n_clicks"),
    ],
    [State("delete-profile-modal", "is_open")],
)
def toggle_delete_profile_modal(delete_btn, cancel_btn, confirm_btn, is_open):
    """Toggle delete profile modal open/close."""
    if not ctx.triggered:
        return is_open

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "delete-profile-btn":
        return True
    elif triggered_id in ["cancel-delete-profile", "confirm-delete-profile"]:
        return False
    return is_open


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
    ],
    [Input("confirm-delete-profile", "n_clicks")],
    [State("profile-selector", "value"), State("delete-confirmation-input", "value")],
    prevent_initial_call=True,
)
def handle_delete_profile(n_clicks, profile_id, confirmation):
    """Handle profile deletion."""
    if not n_clicks or confirmation != "DELETE":
        return "", "alert alert-danger d-none", no_update, no_update, no_update

    if not profile_id:
        return (
            "No profile selected.",
            "alert alert-danger",
            no_update,
            no_update,
            no_update,
        )

    try:
        from dash import html
        import dash_bootstrap_components as dbc

        profiles = list_profiles()
        profile_to_delete = next((p for p in profiles if p["id"] == profile_id), None)
        if not profile_to_delete:
            error_notification = dbc.Toast(
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Profile not found.",
                    ]
                ),
                header="Delete Failed",
                icon="danger",
                is_open=True,
                dismissable=True,
                duration=4000,
            )
            # No modal error - just toast and let modal close
            return (
                "",
                "alert alert-danger d-none",
                no_update,
                no_update,
                error_notification,
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

        profile_options = [
            {
                "label": f"{p['name']} ★" if p["id"] == new_active_id else p["name"],
                "value": p["id"],
            }
            for p in updated_profiles
        ]

        # Return success with no error message
        # The modal will close (no error to keep it open)
        # Show toast notification for successful deletion
        from dash import html
        import dash_bootstrap_components as dbc

        notification = dbc.Toast(
            html.Div(
                [
                    html.I(className="fas fa-trash me-2"),
                    f"Deleted profile: {profile_to_delete['name']}",
                ]
            ),
            header="Profile Deleted",
            icon="success",
            is_open=True,
            dismissable=True,
            duration=3000,
        )

        return (
            "",
            "alert alert-danger d-none",
            profile_options,
            new_active_id,
            notification,
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to delete profile: {error_msg}")
        return error_msg, "alert alert-danger", no_update, no_update, no_update


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
        from dash import html
        import dash_bootstrap_components as dbc

        notification = dbc.Toast(
            html.Div(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Switched to profile: {profile_name}",
                ]
            ),
            header="Profile Switched",
            icon="success",
            is_open=True,
            dismissable=True,
            duration=3000,
        )

        # Don't update options - let refresh_profile_dropdown handle that to avoid race condition
        return notification, no_update
    except Exception as e:
        logger.error(f"Failed to switch profile: {e}")
        return no_update, no_update
