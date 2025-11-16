"""Query Switching Callbacks for Profile Workspace Management.

Handles query selection, creation, editing, and deletion within profiles.
Integrates with data.query_manager for backend operations.
"""

from dash import callback, Output, Input, State, no_update, ctx, html
from dash.exceptions import PreventUpdate
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Query Dropdown Population
# ============================================================================


@callback(
    [
        Output("query-selector", "options"),
        Output("query-selector", "value"),
        Output("query-jql-editor", "value", allow_duplicate=True),
        Output("query-name-input", "value", allow_duplicate=True),
        Output(
            "jira-jql-query", "value", allow_duplicate=True
        ),  # Sync legacy component on page load
    ],
    Input("url", "pathname"),  # Trigger on page load
    prevent_initial_call="initial_duplicate",
)
def populate_query_dropdown(_pathname):
    """Populate query dropdown with queries from active profile and set JQL.

    Includes special '→ Create New Query' option at the top for inline query creation.

    Returns:
        Tuple of (options, value, jql_query, query_name, legacy_jql)
    """
    try:
        from data.query_manager import get_active_profile_id, list_queries_for_profile

        # Get active profile
        profile_id = get_active_profile_id()

        # List queries for this profile
        queries = list_queries_for_profile(profile_id)

        # Build dropdown options with "Create New" at the top
        options = [{"label": "→ Create New Query", "value": "__create_new__"}]
        active_value = ""
        active_jql = ""
        active_name = ""

        if not queries:
            # Only show "Create New" option
            return options, "", "", "", ""

        for query in queries:
            label = query.get("name", "Unnamed Query")
            value = query.get("id", "")

            # Mark active query
            if query.get("is_active", False):
                label += " ★"
                active_value = value
                active_jql = query.get("jql", "")
                active_name = query.get("name", "")

            options.append({"label": label, "value": value})

        logger.info(
            f"Populated query dropdown: {len(options) - 1} queries + Create New option. Active: {active_value}"
        )

        # Return options, active query, and its JQL + name (sync to both editors)
        return options, active_value, active_jql, active_name, active_jql

    except Exception as e:
        logger.error(f"Failed to populate query dropdown: {e}")
        # Return safe defaults with Create New option
        return (
            [{"label": "→ Create New Query", "value": "__create_new__"}],
            "",
            "",
            "",
            "",
        )


# ============================================================================
# Query Switching
# ============================================================================


@callback(
    [
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("query-jql-editor", "value", allow_duplicate=True),
        Output("query-name-input", "value", allow_duplicate=True),
        Output(
            "jira-jql-query", "value", allow_duplicate=True
        ),  # Sync legacy component for Update Data
    ],
    Input("query-selector", "value"),
    State("query-selector", "options"),
    prevent_initial_call=True,
)
def switch_query_callback(selected_query_id, current_options):
    """Switch to selected query and update dropdown and JQL editor.

    Handles two special cases:
    1. Regular query selection - loads query data
    2. "→ Create New Query" - clears fields for new query creation

    Performance target: <50ms for switch operation.

    Args:
        selected_query_id: Query ID selected from dropdown (or "__create_new__")
        current_options: Current dropdown options (for validation)

    Returns:
        Tuple of (updated_options, updated_value, jql_query, query_name, legacy_jql)
    """
    if not selected_query_id:
        raise PreventUpdate

    # Type guard to ensure selected_query_id is a string
    if not isinstance(selected_query_id, str):
        logger.warning(f"Invalid query ID type: {type(selected_query_id)}")
        raise PreventUpdate

    # Handle "Create New Query" selection
    if selected_query_id == "__create_new__":
        logger.info("Create New Query selected - clearing fields")
        # Keep dropdown options, clear value and fields (including legacy component)
        return no_update, "__create_new__", "", "", ""

    try:
        import time
        from data.query_manager import (
            switch_query,
            get_active_query_id,
            get_active_profile_id,
            list_queries_for_profile,
        )

        # Check if already on this query (None means no active query)
        current_query_id = get_active_query_id()
        if current_query_id and selected_query_id == current_query_id:
            raise PreventUpdate

        # Performance measurement
        start_time = time.perf_counter()

        # Switch query (atomic operation)
        switch_query(selected_query_id)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"Query switched to '{selected_query_id}' in {elapsed_ms:.2f}ms")

        # Refresh dropdown to update active indicator and get JQL + name
        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        options = [{"label": "→ Create New Query", "value": "__create_new__"}]
        active_value = ""
        active_jql = ""
        active_name = ""
        for query in queries:
            label = query.get("name", "Unnamed Query")
            value = query.get("id", "")
            if query.get("is_active", False):
                label += " ★"
                active_value = value
                active_jql = query.get("jql", "")
                active_name = query.get("name", "")
            options.append({"label": label, "value": value})

        logger.info(
            f"Query switched successfully, JQL and name updated (including legacy component)"
        )
        return (
            options,
            active_value,
            active_jql,
            active_name,
            active_jql,
        )  # Sync to legacy component

    except ValueError as e:
        logger.error(f"Query switch validation error: {e}")
        return no_update, no_update, no_update, no_update, no_update

    except Exception as e:
        logger.error(f"Failed to switch query: {e}")
        return no_update, no_update, no_update, no_update, no_update


# ============================================================================
# Query Edit Modal
# ============================================================================


@callback(
    [
        Output("edit-query-modal", "is_open"),
        Output("edit-query-name-input", "value"),
        Output("edit-query-description-input", "value"),
        Output("edit-query-jql-input", "value"),
    ],
    [
        Input("edit-query-btn", "n_clicks"),
        Input("cancel-edit-query-button", "n_clicks"),
        Input("confirm-edit-query-button", "n_clicks"),
    ],
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def toggle_edit_query_modal(
    edit_clicks, cancel_clicks, confirm_clicks, selected_query_id
):
    """Toggle edit query modal and populate fields.

    Args:
        edit_clicks: Edit button clicks
        cancel_clicks: Cancel button clicks
        confirm_clicks: Confirm button clicks
        selected_query_id: Currently selected query ID

    Returns:
        Tuple of (is_open, name, description, jql)
    """
    triggered = ctx.triggered_id

    if triggered == "edit-query-btn":
        if not selected_query_id:
            raise PreventUpdate

        try:
            from data.query_manager import (
                get_active_profile_id,
                list_queries_for_profile,
            )

            profile_id = get_active_profile_id()
            queries = list_queries_for_profile(profile_id)

            # Find the selected query
            query = next((q for q in queries if q.get("id") == selected_query_id), None)

            if not query:
                logger.error(f"Query '{selected_query_id}' not found")
                raise PreventUpdate

            return (
                True,
                query.get("name", ""),
                query.get("description", ""),
                query.get("jql", ""),
            )

        except Exception as e:
            logger.error(f"Failed to load query for editing: {e}")
            raise PreventUpdate

    elif triggered in ("cancel-edit-query-button", "confirm-edit-query-button"):
        return False, "", "", ""

    raise PreventUpdate


# ============================================================================
# Query Creation Modal
# ============================================================================


@callback(
    Output("workspace-create-query-modal", "is_open"),
    [
        Input("create-query-btn", "n_clicks"),
        Input("workspace-save-create-query-button", "n_clicks"),
        Input("workspace-cancel-create-query-button", "n_clicks"),
    ],
    State("workspace-create-query-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_create_query_modal(create_clicks, save_clicks, cancel_clicks, is_open):
    """Toggle create query modal visibility.

    Args:
        create_clicks: Create button clicks
        save_clicks: Save button clicks
        cancel_clicks: Cancel button clicks
        is_open: Current modal state

    Returns:
        New modal state (open/closed)
    """
    triggered = ctx.triggered_id

    if triggered == "create-query-btn":
        return not is_open
    elif triggered in (
        "workspace-save-create-query-button",
        "workspace-cancel-create-query-button",
    ):
        return False

    return is_open


@callback(
    [
        Output("workspace-query-name-input", "value"),
        Output("workspace-query-jql-input", "value"),
        Output("workspace-query-creation-feedback", "children"),
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
    ],
    Input("workspace-save-create-query-button", "n_clicks"),
    [
        State("workspace-query-name-input", "value"),
        State("workspace-query-jql-input", "value"),
    ],
    prevent_initial_call=True,
)
def create_new_query_callback(save_clicks, query_name, query_jql):
    """Create new query in active profile.

    Args:
        save_clicks: Save button clicks
        query_name: Query name from input
        query_jql: JQL string from input

    Returns:
        Tuple of (cleared_name, cleared_jql, feedback_message, feedback_color)
    """
    if not save_clicks:
        raise PreventUpdate

    try:
        from data.query_manager import (
            get_active_profile_id,
            create_query,
            list_queries_for_profile,
        )
        from ui.query_selector import get_query_dropdown_options

        # Validate inputs
        if not query_name or not query_name.strip():
            feedback = html.Div(
                "Query name is required", className="alert alert-danger"
            )
            return no_update, no_update, feedback, no_update, no_update

        if not query_jql or not query_jql.strip():
            feedback = html.Div("JQL query is required", className="alert alert-danger")
            return no_update, no_update, feedback, no_update, no_update

        # Get active profile
        profile_id = get_active_profile_id()

        # Create query
        query_id = create_query(profile_id, query_name.strip(), query_jql.strip())

        logger.info(f"Created query '{query_id}' in profile '{profile_id}'")

        # Get updated query list
        queries = list_queries_for_profile(profile_id)
        options = get_query_dropdown_options(queries)

        # Clear inputs and show success
        feedback = html.Div(
            f"Query '{query_name}' created successfully!",
            className="alert alert-success",
        )
        return "", "", feedback, options, query_id

    except ValueError as e:
        logger.warning(f"Query creation validation failed: {e}")
        feedback = html.Div(str(e), className="alert alert-danger")
        return no_update, no_update, feedback, no_update, no_update

    except Exception as e:
        logger.error(f"Failed to create query: {e}")
        feedback = html.Div(
            f"Error creating query: {e}", className="alert alert-danger"
        )
        return no_update, no_update, feedback, no_update, no_update


# Query deletion moved to settings.py to use modal confirmation system
# This prevents accidental deletion by requiring user confirmation


# ============================================================================
# Query Deletion Modal Trigger
# ============================================================================


@callback(
    [
        Output("delete-jql-query-modal", "is_open", allow_duplicate=True),
        Output("delete-query-name", "children", allow_duplicate=True),
    ],
    Input("delete-query-btn", "n_clicks"),
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def trigger_delete_query_modal_from_selector(delete_clicks, selected_query_id):
    """Trigger delete query modal when delete button is clicked.

    Shows context-aware warnings:
    - Active query: Warns that charts will be cleared
    - Last query: Extra warning about losing all query data
    - Regular query: Standard deletion warning

    Args:
        delete_clicks: Delete button clicks
        selected_query_id: Currently selected query ID

    Returns:
        Tuple of (modal_open, query_display_text)
    """
    logger.info(
        f"[DELETE] Delete button clicked - delete_clicks={delete_clicks}, selected_query_id='{selected_query_id}'"
    )

    if not delete_clicks or not selected_query_id:
        logger.warning(
            f"[DELETE] Preventing update - delete_clicks={delete_clicks}, selected_query_id='{selected_query_id}'"
        )
        raise PreventUpdate

    # Prevent deletion of "Create New Query" placeholder
    if selected_query_id == "__create_new__":
        logger.warning("Cannot delete 'Create New Query' placeholder")
        raise PreventUpdate

    try:
        from data.query_manager import (
            get_active_profile_id,
            get_active_query_id,
            list_queries_for_profile,
        )

        # Get query info
        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        query = next((q for q in queries if q.get("id") == selected_query_id), None)
        if not query:
            logger.warning(f"Query {selected_query_id} not found")
            raise PreventUpdate

        query_name = query.get("name", "Unnamed Query")
        active_query_id = get_active_query_id()
        is_active = active_query_id and selected_query_id == active_query_id
        is_last_query = len(queries) == 1

        # Build contextual display text
        display_parts = [query_name]

        if is_active and is_last_query:
            display_parts.append(" ⚠️ ACTIVE & LAST QUERY - All charts will be cleared!")
            logger.warning(
                f"Opening delete modal for ACTIVE AND LAST query: {query_name}"
            )
        elif is_active:
            display_parts.append(" ★ ACTIVE - Charts will be cleared")
            logger.warning(f"Opening delete modal for ACTIVE query: {query_name}")
        elif is_last_query:
            display_parts.append(" ⚠️ LAST QUERY - Profile will have no queries")
            logger.warning(f"Opening delete modal for LAST query: {query_name}")
        else:
            logger.info(f"Opening delete modal for query: {query_name}")

        display_text = "".join(display_parts)

        # Open modal with context
        return True, display_text

    except Exception as e:
        logger.error(f"Failed to trigger delete modal: {e}")
        raise PreventUpdate
