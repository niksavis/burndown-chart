"""
Integrated Query Management Callbacks

Implements all callbacks for the unified JQL-first query management system.
Handles state management, query switching, saving, reverting, and deletion.

Workflow:
1. JQL editor changes → update state, show unsaved indicator
2. Save → generate name, show modal with update/new options
3. Switch query → check unsaved, prompt if needed, load JQL
4. Revert → restore saved JQL, clear unsaved state
5. Delete → confirm, remove files, switch to next query
"""

import logging
from datetime import datetime
from typing import Any

from dash import Input, Output, State, callback, ctx, no_update
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


# ============================================================================
# CALLBACK 1: JQL Editor Change Detection
# ============================================================================


@callback(
    [
        Output("query-state-store", "data"),
        Output("query-unsaved-badge", "style"),
        Output("integrated-save-query-button", "disabled"),
        Output("integrated-revert-query-button", "style"),
        Output("query-name-suggestion", "children"),
        Output("query-name-suggestion-container", "style"),
    ],
    Input("integrated-jql-editor", "value"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def detect_jql_changes(
    current_jql: str,
    state: dict[str, Any],
) -> tuple:
    """
    Detect JQL editor changes and update UI state.

    Compares current JQL with saved version to determine if changes exist.
    Updates unsaved indicator, enables/disables buttons, generates name suggestion.

    Args:
        current_jql: Current JQL in editor
        state: Query state from store

    Returns:
        Tuple of (updated_state, badge_style, save_disabled, revert_style,
                  suggested_name, suggestion_container_style)
    """
    if state is None:
        state = {
            "activeQueryId": None,
            "activeQueryName": None,
            "savedJql": "",
            "currentJql": "",
            "hasUnsavedChanges": False,
            "lastModified": None,
            "suggestedName": "",
        }

    # Update current JQL in state
    saved_jql = state.get("savedJql", "")
    current_jql = current_jql or ""

    # Determine if changes exist
    has_unsaved_changes = current_jql.strip() != saved_jql.strip()

    # Generate suggested name if JQL exists
    suggested_name = ""
    if current_jql.strip():
        from data.query_name_generator import generate_query_name

        suggested_name = generate_query_name(current_jql)

    # Update state
    state["currentJql"] = current_jql
    state["hasUnsavedChanges"] = has_unsaved_changes
    state["suggestedName"] = suggested_name
    state["lastModified"] = datetime.now().isoformat()

    # UI updates
    badge_style = (
        {"display": "inline-block"} if has_unsaved_changes else {"display": "none"}
    )
    save_disabled = not bool(current_jql.strip())  # Enable if JQL has content
    revert_style = {"display": "block"} if has_unsaved_changes else {"display": "none"}
    suggestion_style = {"display": "block"} if suggested_name else {"display": "none"}

    return (
        state,
        badge_style,
        save_disabled,
        revert_style,
        suggested_name,
        suggestion_style,
    )


# ============================================================================
# CALLBACK 2: Query Dropdown Change (with Unsaved Check)
# ============================================================================


@callback(
    [
        Output("unsaved-changes-modal", "is_open"),
        Output("unsaved-changes-query-name", "children"),
        Output("unsaved-changes-jql-preview", "children"),
        Output("pending-query-switch-store", "data"),
    ],
    Input("integrated-query-selector", "value"),
    [
        State("query-state-store", "data"),
        State("unsaved-changes-modal", "is_open"),
    ],
    prevent_initial_call=True,
)
def handle_query_dropdown_change(
    selected_query_id: str | None,
    state: dict[str, Any],
    modal_is_open: bool,
) -> tuple:
    """
    Handle query selection with unsaved changes check.

    If unsaved changes exist, opens modal to prompt user.
    Otherwise, proceeds with loading query (handled by separate callback).

    Args:
        selected_query_id: ID of selected query
        state: Query state from store
        modal_is_open: Current modal state

    Returns:
        Tuple of (modal_is_open, query_name, jql_preview, pending_query_id)
    """
    if not selected_query_id or not state:
        raise PreventUpdate

    # Check if switching to same query (no-op)
    if selected_query_id == state.get("activeQueryId"):
        raise PreventUpdate

    # Check for unsaved changes
    has_unsaved = state.get("hasUnsavedChanges", False)

    if has_unsaved:
        # Show unsaved changes modal
        query_name = state.get("activeQueryName", "current query")
        current_jql = state.get("currentJql", "")

        return (
            True,  # Open modal
            query_name,
            current_jql,
            selected_query_id,  # Store pending switch
        )

    # No unsaved changes - allow switch (handled by load callback)
    return no_update, no_update, no_update, selected_query_id


# ============================================================================
# CALLBACK 3: Load Query JQL (after unsaved handled)
# ============================================================================


@callback(
    [
        Output("integrated-jql-editor", "value"),
        Output("query-state-store", "data", allow_duplicate=True),
        Output("integrated-delete-query-button", "disabled"),
        Output("query-last-saved-time", "children"),
        Output("query-last-saved-indicator", "style"),
    ],
    Input("pending-query-switch-store", "data"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def load_query_jql(
    query_id: str | None,
    state: dict[str, Any],
) -> tuple:
    """
    Load selected query's JQL into editor.

    Updates editor content and state to reflect loaded query.
    Resets unsaved changes flag.

    Args:
        query_id: ID of query to load
        state: Current query state

    Returns:
        Tuple of (jql_value, updated_state, delete_disabled, last_saved, indicator_style)
    """
    if not query_id:
        raise PreventUpdate

    try:
        from data.query_manager import get_active_profile_id, list_queries_for_profile

        # Load query data
        profile_id = get_active_profile_id()
        all_queries = list_queries_for_profile(profile_id)
        query = next((q for q in all_queries if q.get("id") == query_id), None)
        if not query:
            logger.warning(f"Query {query_id} not found")
            raise PreventUpdate

        query_name = query.get("name", "Unnamed")
        query_jql = query.get("jql", "")

        # Update state
        if state is None:
            state = {}

        state["activeQueryId"] = query_id
        state["activeQueryName"] = query_name
        state["savedJql"] = query_jql
        state["currentJql"] = query_jql
        state["hasUnsavedChanges"] = False
        state["lastModified"] = datetime.now().isoformat()

        # Format last saved time
        last_saved_text = "Just now"

        return (
            query_jql,  # Load into editor
            state,
            False,  # Enable delete button
            last_saved_text,
            {"display": "block"},  # Show last saved indicator
        )

    except Exception as e:
        logger.error(f"Error loading query {query_id}: {e}")
        raise PreventUpdate from e


# ============================================================================
# CALLBACK 4: Unsaved Changes Modal Actions
# ============================================================================


@callback(
    [
        Output("unsaved-changes-modal", "is_open", allow_duplicate=True),
        Output("save-query-modal", "is_open"),
        Output("pending-query-switch-store", "data", allow_duplicate=True),
    ],
    [
        Input("unsaved-changes-save-button", "n_clicks"),
        Input("unsaved-changes-discard-button", "n_clicks"),
        Input("unsaved-changes-cancel-button", "n_clicks"),
    ],
    State("pending-query-switch-store", "data"),
    prevent_initial_call=True,
)
def handle_unsaved_changes_modal(
    save_clicks: int,
    discard_clicks: int,
    cancel_clicks: int,
    pending_query_id: str | None,
) -> tuple:
    """
    Handle unsaved changes modal button clicks.

    Save: Opens save query modal
    Discard: Proceeds with query switch (clears pending)
    Cancel: Closes modal, stays on current query

    Args:
        save_clicks: Save button clicks
        discard_clicks: Discard button clicks
        cancel_clicks: Cancel button clicks
        pending_query_id: Query user was trying to switch to

    Returns:
        Tuple of (unsaved_modal_open, save_modal_open, pending_query_id)
    """
    triggered = ctx.triggered_id

    if triggered == "unsaved-changes-save-button":
        # Open save modal, keep pending switch
        return False, True, pending_query_id

    elif triggered == "unsaved-changes-discard-button":
        # Proceed with switch (triggers load callback)
        return False, False, pending_query_id

    elif triggered == "unsaved-changes-cancel-button":
        # Cancel switch, clear pending
        return False, False, None

    raise PreventUpdate


# ============================================================================
# CALLBACK 5: Open Save Query Modal
# ============================================================================


@callback(
    [
        Output("save-query-modal", "is_open", allow_duplicate=True),
        Output("save-query-jql-preview", "children"),
        Output("save-query-name-input", "value"),
        Output("save-query-mode-radio", "value"),
        Output("save-query-mode-container", "style"),
    ],
    Input("integrated-save-query-button", "n_clicks"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def open_save_query_modal(
    n_clicks: int,
    state: dict[str, Any],
) -> tuple:
    """
    Open save query modal with current JQL and suggested name.

    Determines if this is a new query or update to existing.
    Pre-fills suggested name and sets appropriate mode.

    Args:
        n_clicks: Save button clicks
        state: Current query state

    Returns:
        Tuple of (modal_open, jql_preview, suggested_name, mode, mode_container_style)
    """
    if not n_clicks or not state:
        raise PreventUpdate

    current_jql = state.get("currentJql", "")
    suggested_name = state.get("suggestedName", "")
    active_query_id = state.get("activeQueryId")

    # Determine mode: update existing or save as new
    if active_query_id:
        mode = "update"  # Has active query, default to update
    else:
        mode = "new"  # No active query, must save as new

    # Show/hide mode container (hide if new query)
    mode_container_style = (
        {"display": "block"} if active_query_id else {"display": "none"}
    )

    return (
        True,  # Open modal
        current_jql,
        suggested_name,
        mode,
        mode_container_style,
    )


# ============================================================================
# CALLBACK 6: Save Query Confirm
# ============================================================================


@callback(
    [
        Output("save-query-modal", "is_open", allow_duplicate=True),
        Output("save-query-name-validation", "children"),
        Output("query-state-store", "data", allow_duplicate=True),
        Output("integrated-query-selector", "options"),
        Output("integrated-query-selector", "value"),
    ],
    Input("save-query-confirm-button", "n_clicks"),
    [
        State("save-query-name-input", "value"),
        State("save-query-mode-radio", "value"),
        State("query-state-store", "data"),
    ],
    prevent_initial_call=True,
)
def save_query_confirm(
    n_clicks: int,
    query_name: str,
    save_mode: str,
    state: dict[str, Any],
) -> tuple:
    """
    Save query (update existing or create new).

    Validates name, creates/updates query, refreshes dropdown.
    Shows data loss warning handled by modal UI.

    Args:
        n_clicks: Confirm button clicks
        query_name: User-entered query name
        save_mode: "update" or "new"
        state: Current query state

    Returns:
        Tuple of (modal_open, validation_msg, updated_state, dropdown_options, selected_value)
    """
    if not n_clicks or not state:
        raise PreventUpdate

    try:
        from data.query_manager import (
            create_query,
            get_active_profile_id,
            list_queries_for_profile,
            update_query,
        )
        from data.query_name_generator import validate_query_name

        # Validate name
        profile_id = get_active_profile_id()
        all_queries = list_queries_for_profile(profile_id)
        existing_names = [q.get("name", "") for q in all_queries]

        # If updating, exclude current query name from validation
        if save_mode == "update" and state.get("activeQueryName"):
            existing_names = [
                n for n in existing_names if n != state.get("activeQueryName")
            ]

        is_valid, error_msg = validate_query_name(query_name, existing_names)
        if not is_valid:
            return no_update, error_msg, no_update, no_update, no_update

        current_jql = state.get("currentJql", "")

        if save_mode == "update":
            # Update existing query
            query_id = state.get("activeQueryId")
            if not query_id:
                return (
                    no_update,
                    "No active query to update",
                    no_update,
                    no_update,
                    no_update,
                )
            update_query(profile_id, query_id, name=query_name, jql=current_jql)
            logger.info(f"Updated query {query_id}: {query_name}")

            # Update state
            state["activeQueryName"] = query_name
            state["savedJql"] = current_jql
            state["hasUnsavedChanges"] = False

            selected_query_id = query_id

        else:
            # Create new query
            query_id = create_query(profile_id, query_name, current_jql)
            logger.info(f"Created query {query_id}: {query_name}")

            # Update state
            state["activeQueryId"] = query_id
            state["activeQueryName"] = query_name
            state["savedJql"] = current_jql
            state["hasUnsavedChanges"] = False

            selected_query_id = query_id

        # Refresh dropdown options
        all_queries = list_queries_for_profile(profile_id)
        dropdown_options = [
            {
                "label": f"{q.get('name', 'Unnamed')} {'[Active]' if q.get('id') == selected_query_id else ''}",
                "value": q.get("id", ""),
            }
            for q in all_queries
        ]

        return (
            False,  # Close modal
            "",  # Clear validation
            state,
            dropdown_options,
            selected_query_id,
        )

    except Exception as e:
        logger.error(f"Error saving query: {e}")
        return (
            no_update,
            f"Error saving query: {str(e)}",
            no_update,
            no_update,
            no_update,
        )


# ============================================================================
# CALLBACK 7: Cancel Save Query Modal
# ============================================================================


@callback(
    Output("save-query-modal", "is_open", allow_duplicate=True),
    Input("save-query-cancel-button", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_save_query_modal(n_clicks: int) -> bool:
    """Close save query modal without saving."""
    if not n_clicks:
        raise PreventUpdate
    return False


# ============================================================================
# CALLBACK 8: Revert Changes
# ============================================================================


@callback(
    [
        Output("integrated-jql-editor", "value", allow_duplicate=True),
        Output("query-state-store", "data", allow_duplicate=True),
    ],
    Input("integrated-revert-query-button", "n_clicks"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def revert_query_changes(
    n_clicks: int,
    state: dict[str, Any],
) -> tuple:
    """
    Revert JQL editor to last saved version.

    Restores savedJql to editor, clears unsaved changes flag.

    Args:
        n_clicks: Revert button clicks
        state: Current query state

    Returns:
        Tuple of (jql_value, updated_state)
    """
    if not n_clicks or not state:
        raise PreventUpdate

    saved_jql = state.get("savedJql", "")

    # Update state
    state["currentJql"] = saved_jql
    state["hasUnsavedChanges"] = False

    return saved_jql, state


# ============================================================================
# CALLBACK 9: Open Delete Query Modal
# ============================================================================


@callback(
    [
        Output("delete-query-modal", "is_open"),
        Output("delete-query-name-display", "children"),
        Output("delete-query-jql-display", "children"),
    ],
    Input("integrated-delete-query-button", "n_clicks"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def open_delete_query_modal(
    n_clicks: int,
    state: dict[str, Any],
) -> tuple:
    """
    Open delete query confirmation modal.

    Shows query name and JQL being deleted.

    Args:
        n_clicks: Delete button clicks
        state: Current query state

    Returns:
        Tuple of (modal_open, query_name, query_jql)
    """
    if not n_clicks or not state:
        raise PreventUpdate

    query_name = state.get("activeQueryName", "Unnamed")
    current_jql = state.get("currentJql", "")

    return True, query_name, current_jql


# ============================================================================
# CALLBACK 10: Confirm Delete Query
# ============================================================================


@callback(
    [
        Output("delete-query-modal", "is_open", allow_duplicate=True),
        Output("integrated-query-selector", "options", allow_duplicate=True),
        Output("integrated-query-selector", "value", allow_duplicate=True),
        Output("integrated-jql-editor", "value", allow_duplicate=True),
        Output("query-state-store", "data", allow_duplicate=True),
    ],
    Input("delete-query-confirm-button", "n_clicks"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def confirm_delete_query(
    n_clicks: int,
    state: dict[str, Any],
) -> tuple:
    """
    Delete query and switch to first remaining query.

    Deletes query files, updates dropdown, loads next query.
    Prevents deletion if last query in profile.

    Args:
        n_clicks: Confirm button clicks
        state: Current query state

    Returns:
        Tuple of (modal_open, dropdown_options, selected_value, jql_value, updated_state)
    """
    if not n_clicks or not state:
        raise PreventUpdate

    try:
        from data.query_manager import (
            delete_query,
            get_active_profile_id,
            list_queries_for_profile,
        )

        query_id = state.get("activeQueryId")
        profile_id = get_active_profile_id()

        # Delete query (allow deletion of last query)
        if not query_id:
            raise PreventUpdate
        delete_query(profile_id, query_id, allow_cascade=True)
        logger.info(f"Deleted query {query_id}")

        # Get remaining queries
        remaining_queries = list_queries_for_profile(profile_id)
        first_query = remaining_queries[0] if remaining_queries else None

        if first_query:
            # Load first remaining query
            first_query_id = first_query.get("id")
            first_query_jql = first_query.get("jql", "")
            first_query_name = first_query.get("name", "")

            # Update state
            state["activeQueryId"] = first_query_id
            state["activeQueryName"] = first_query_name
            state["savedJql"] = first_query_jql
            state["currentJql"] = first_query_jql
            state["hasUnsavedChanges"] = False

            # Update dropdown
            dropdown_options = [
                {
                    "label": f"{q.get('name', 'Unnamed')} {'[Active]' if q.get('id') == first_query_id else ''}",
                    "value": q.get("id", ""),
                }
                for q in remaining_queries
            ]

            return (
                False,  # Close modal
                dropdown_options,
                first_query_id,
                first_query_jql,
                state,
            )
        else:
            # No queries left - user deleted the last query, return to empty state
            return (
                False,
                [],
                None,
                "",
                {
                    "activeQueryId": None,
                    "activeQueryName": None,
                    "savedJql": "",
                    "currentJql": "",
                    "hasUnsavedChanges": False,
                    "lastModified": None,
                    "suggestedName": "",
                },
            )

    except Exception as e:
        logger.error(f"Error deleting query: {e}")
        raise PreventUpdate from e


# ============================================================================
# CALLBACK 11: Cancel Delete Query Modal
# ============================================================================


@callback(
    Output("delete-query-modal", "is_open", allow_duplicate=True),
    Input("delete-query-cancel-button", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_delete_query_modal(n_clicks: int) -> bool:
    """Close delete query modal without deleting."""
    if not n_clicks:
        raise PreventUpdate
    return False


# ============================================================================
# CALLBACK 12: Initialize Query Dropdown on Load
# ============================================================================


@callback(
    [
        Output("integrated-query-selector", "options", allow_duplicate=True),
        Output("integrated-query-selector", "value", allow_duplicate=True),
    ],
    Input("query-state-store", "data"),
    prevent_initial_call="initial_duplicate",  # Allow running on initial load with allow_duplicate
)
def initialize_query_dropdown(state: dict[str, Any]) -> tuple:
    """
    Initialize query dropdown with queries from active profile.

    Runs on page load to populate dropdown with saved queries.

    Args:
        state: Query state (may be initial default)

    Returns:
        Tuple of (dropdown_options, selected_value)
    """
    try:
        from data.query_manager import get_active_profile_id, list_queries_for_profile

        profile_id = get_active_profile_id()
        if not profile_id:
            return [], None

        all_queries = list_queries_for_profile(profile_id)
        if not all_queries:
            return [], None

        # Get active query from state or use first
        active_query_id = state.get("activeQueryId") if state else None
        if not active_query_id and all_queries:
            active_query_id = all_queries[0].get("id")

        dropdown_options = [
            {
                "label": f"{q.get('name', 'Unnamed')} {'[Active]' if q.get('id') == active_query_id else ''}",
                "value": q.get("id", ""),
            }
            for q in all_queries
        ]

        return dropdown_options, active_query_id

    except Exception as e:
        logger.error(f"Error initializing query dropdown: {e}")
        return [], None
