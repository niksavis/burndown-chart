"""Query Switching Callbacks for Profile Workspace Management.

Handles query selection, creation, editing, and deletion within profiles.
Integrates with data.query_manager for backend operations.
"""

from dash import callback, Output, Input, State, no_update, ctx, html
from dash.exceptions import PreventUpdate
import logging

from ui.toast_notifications import create_success_toast, create_error_toast

logger = logging.getLogger(__name__)


# ============================================================================
# Query Button State Management
# ============================================================================


@callback(
    [
        Output("load-query-data-btn", "disabled"),
        Output("delete-query-btn", "disabled"),
    ],
    [Input("query-selector", "value")],
)
def manage_query_button_states(selected_query):
    """Disable load/delete buttons when no query selected or Create New selected.

    Args:
        selected_query: Currently selected query ID

    Returns:
        Tuple of (load_disabled, delete_disabled)
    """
    # Disable if no selection or if "Create New Query" is selected
    disabled = not selected_query or selected_query == "__create_new__"
    return disabled, disabled


# ============================================================================
# Query Dropdown Population
# ============================================================================


@callback(
    [
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("query-jql-editor", "value", allow_duplicate=True),
        Output("query-name-input", "value", allow_duplicate=True),
        Output(
            "jira-jql-query", "value", allow_duplicate=True
        ),  # Sync legacy component on page load
    ],
    [
        Input("url", "pathname"),  # Trigger on page load
        Input("profile-selector", "value"),  # Trigger when profile changes
    ],
    prevent_initial_call="initial_duplicate",
)
def populate_query_dropdown(_pathname, profile_id):
    """Populate query dropdown with queries from active profile and set JQL.

    Includes special '→ Create New Query' option at the top for inline query creation.

    Args:
        _pathname: URL pathname (triggers on page load)
        profile_id: Selected profile ID from dropdown (triggers on profile change)

    Returns:
        Tuple of (options, value, jql_query, query_name, legacy_jql)
    """
    try:
        from data.query_manager import get_active_profile_id, list_queries_for_profile

        # Use provided profile_id if available (from profile-selector change),
        # otherwise get active profile from file system (on page load)
        if profile_id is None or profile_id == "":
            profile_id = get_active_profile_id()

        # List queries for this profile
        queries = list_queries_for_profile(profile_id)

        # Build dropdown options with "Create New" at the top
        options = [{"label": "→ Create New Query", "value": "__create_new__"}]
        active_value = ""
        active_jql = ""
        active_name = ""

        if not queries:
            # Only show "Create New" option - select it by default
            return options, "__create_new__", "", "", ""

        for query in queries:
            label = query.get("name", "Unnamed Query")
            value = query.get("id", "")

            # Mark active query
            if query.get("is_active", False):
                label += " [Active]"
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
        from data.query_manager import (
            get_active_profile_id,
            list_queries_for_profile,
        )

        # IMPORTANT: Do NOT call switch_query() here!
        # Switching the active query would cause other callbacks to load data
        # from the newly selected query before the user clicks "Load".
        # The actual query switch happens in load_query_cached_data() when
        # the user clicks the "Load Query Data" button.

        # Just refresh the dropdown to show the selected query's JQL and name
        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        options = [{"label": "→ Create New Query", "value": "__create_new__"}]
        selected_jql = ""
        selected_name = ""

        # Build dropdown options and find the selected query's details
        for query in queries:
            label = query.get("name", "Unnamed Query")
            value = query.get("id", "")

            # Mark active query with [Active] indicator
            if query.get("is_active", False):
                label += " [Active]"

            # Store JQL and name for the selected query
            if value == selected_query_id:
                selected_jql = query.get("jql", "")
                selected_name = query.get("name", "")

            options.append({"label": label, "value": value})

        # Validate that we found the selected query
        if not selected_jql and not selected_name:
            logger.error(
                f"Query selection failed: {selected_query_id} not found in profile"
            )
            # Query not found - don't update anything
            raise PreventUpdate

        logger.info(
            f"Query selected (not switched): '{selected_name}', JQL length: {len(selected_jql)} chars. "
            f"Data will load when user clicks 'Load Query Data' button."
        )
        return (
            options,
            selected_query_id,  # Keep the selected value
            selected_jql,
            selected_name,
            selected_jql,  # Sync to legacy component
        )

    except ValueError as e:
        logger.error(f"Query switch validation error: {e}")
        return no_update, no_update, no_update, no_update, no_update

    except PreventUpdate:
        # Re-raise PreventUpdate - this is expected behavior, not an error
        raise

    except Exception as e:
        logger.error(f"Failed to switch query: {type(e).__name__}: {e}")
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
        Output("app-notifications", "children", allow_duplicate=True),
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
        Tuple of (cleared_name, cleared_jql, feedback_message, options, query_id, toast)
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
            feedback = create_error_toast(
                "Query name is required",
                header="Validation Error",
            )
            return no_update, no_update, "", no_update, no_update, feedback

        if not query_jql or not query_jql.strip():
            feedback = create_error_toast(
                "JQL query is required",
                header="Validation Error",
            )
            return no_update, no_update, "", no_update, no_update, feedback

        # Get active profile
        profile_id = get_active_profile_id()

        # Create query
        query_id = create_query(profile_id, query_name.strip(), query_jql.strip())

        logger.info(f"Created query '{query_id}' in profile '{profile_id}'")

        # Get updated query list
        queries = list_queries_for_profile(profile_id)
        options = get_query_dropdown_options(queries)

        # Clear inputs and show success toast
        toast = create_success_toast(
            f"Query '{query_name}' created successfully!",
            header="Query Created",
        )
        return "", "", "", options, query_id, toast

    except ValueError as e:
        logger.warning(f"Query creation validation failed: {e}")
        feedback = create_error_toast(str(e), header="Validation Error")
        return no_update, no_update, "", no_update, no_update, feedback

    except Exception as e:
        logger.error(f"Failed to create query: {e}")
        feedback = create_error_toast(
            f"Error creating query: {e}",
            header="Creation Failed",
        )
        return no_update, no_update, "", no_update, no_update, feedback


# Query deletion moved to settings.py to use modal confirmation system
# This prevents accidental deletion by requiring user confirmation

# NOTE: Data is NOT automatically loaded when switching queries.
# User must explicitly click "Load Query Data" button to populate UI with query data.
# This allows creating/editing queries without triggering data loads.


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
            display_parts.append(
                " [!] ACTIVE & LAST QUERY - All charts will be cleared!"
            )
            logger.warning(
                f"Opening delete modal for ACTIVE AND LAST query: {query_name}"
            )
        elif is_active:
            display_parts.append(" [ACTIVE] - Charts will be cleared")
            logger.warning(f"Opening delete modal for ACTIVE query: {query_name}")
        elif is_last_query:
            display_parts.append(" [!] LAST QUERY - Profile will have no queries")
            logger.warning(f"Opening delete modal for LAST query: {query_name}")
        else:
            logger.info(f"Opening delete modal for query: {query_name}")

        display_text = "".join(display_parts)

        # Open modal with context
        return True, display_text

    except Exception as e:
        logger.error(f"Failed to trigger delete modal: {e}")
        raise PreventUpdate


# ============================================================================
# Load Query Data
# ============================================================================


@callback(
    [
        Output("statistics-table", "data", allow_duplicate=True),
        Output("total-items-input", "value", allow_duplicate=True),
        Output("estimated-items-input", "value", allow_duplicate=True),
        Output("total-points-display", "value", allow_duplicate=True),
        Output("estimated-points-input", "value", allow_duplicate=True),
        Output("current-settings", "data", allow_duplicate=True),
        Output("update-data-status", "children", allow_duplicate=True),
        Output("current-statistics", "data", allow_duplicate=True),
        Output("jira-cache-status", "children", allow_duplicate=True),
        Output(
            "query-selector", "options", allow_duplicate=True
        ),  # Update dropdown to show [Active]
    ],
    Input("load-query-data-btn", "n_clicks"),
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def load_query_cached_data(n_clicks, selected_query_id):
    """Load cached data for the selected query without fetching from JIRA.

    This switches the active query and loads its cached project_data.json.
    No JIRA API calls are made - only loads existing cached data.

    Args:
        n_clicks: Button click count
        selected_query_id: Selected query ID from dropdown

    Returns:
        Tuple of (statistics, total_items, estimated_items, total_points,
                  estimated_points, settings, status_message)
    """
    if not n_clicks or not selected_query_id:
        raise PreventUpdate

    if selected_query_id == "__create_new__":
        logger.warning("Cannot load data for 'Create New Query' placeholder")
        status_message = html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                "Please select an existing query to load data.",
            ],
            className="text-warning small mt-2",
        )
        raise PreventUpdate

    try:
        from data.query_manager import (
            switch_query,
            get_active_profile_id,
            list_queries_for_profile,
        )
        from data.persistence import load_unified_project_data, load_app_settings

        # Switch to the selected query
        switch_query(selected_query_id)
        logger.info(f"Switched to query: {selected_query_id}")

        # Refresh dropdown to show [Active] indicator on the newly active query
        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)
        dropdown_options = [{"label": "→ Create New Query", "value": "__create_new__"}]
        for query in queries:
            label = query.get("name", "Unnamed Query")
            value = query.get("id", "")
            if query.get("is_active", False):
                label += " [Active]"
            dropdown_options.append({"label": label, "value": value})

        # Load cached data for this query
        unified_data = load_unified_project_data()

        # Extract statistics
        statistics = unified_data.get("statistics", [])
        logger.info(
            f"[QUERY SWITCH] Loaded {len(statistics)} statistics for query {selected_query_id}"
        )
        if statistics:
            logger.info(
                f"[QUERY SWITCH] First stat: {statistics[0].get('date', 'NO DATE')} - items: {statistics[0].get('remaining_items', 'NO ITEMS')}, points: {statistics[0].get('remaining_total_points', 'NO POINTS')}"
            )
            logger.info(
                f"[QUERY SWITCH] Last stat: {statistics[-1].get('date', 'NO DATE')} - items: {statistics[-1].get('remaining_items', 'NO ITEMS')}, points: {statistics[-1].get('remaining_total_points', 'NO POINTS')}"
            )

        # Extract scope
        scope = unified_data.get("project_scope", {})
        estimated_items = scope.get("estimated_items", 0)
        estimated_points = scope.get("estimated_points", 0)

        # Get actual remaining values from project scope
        total_items = scope.get("remaining_items", 0)
        total_points = scope.get("remaining_total_points", 0)

        # Format total_points for display field
        total_points_display = f"{total_points:.0f}"

        # Load settings and update with current scope data
        settings = load_app_settings()

        # CRITICAL: After query switch, settings MUST include current scope data
        # for forecast calculations to work. This is especially important after
        # migration when switching to a different query for the first time.
        if scope:
            settings["total_items"] = total_items
            settings["total_points"] = total_points
            settings["estimated_items"] = estimated_items
            settings["estimated_points"] = estimated_points
            logger.info(
                f"[QUERY SWITCH] Updated settings with scope: "
                f"items={total_items}, points={total_points}"
            )

        # Create success message
        data_points_count = len(statistics)
        status_message = html.Div(
            [
                html.I(className="fas fa-check-circle me-2 text-success"),
                html.Span(
                    f"Loaded cached data: {data_points_count} weekly data point{'s' if data_points_count != 1 else ''}",
                    className="fw-medium",
                ),
            ],
            className="text-success small mt-2",
        )

        logger.info(
            f"Loaded cached data for query {selected_query_id}: "
            f"{data_points_count} data points, {total_items} items"
        )

        # Create cache status message to trigger dashboard refresh
        cache_status = html.Div(
            [
                html.I(className="fas fa-database me-2 text-muted"),
                html.Span("Cached data loaded", className="small"),
            ],
            className="text-muted small mt-2",
        )

        return (
            statistics,
            total_items,
            estimated_items,
            total_points_display,
            estimated_points,
            settings,
            status_message,
            statistics,  # Update current-statistics store to trigger dashboard/charts
            cache_status,  # Update jira-cache-status to trigger dashboard refresh
            dropdown_options,  # Update dropdown to show [Active] on newly loaded query
        )

    except Exception as e:
        logger.error(f"Failed to load query data: {e}")
        error_message = html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                html.Span(
                    f"Failed to load cached data: {str(e)}", className="fw-medium"
                ),
            ],
            className="text-danger small mt-2",
        )
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            error_message,
            no_update,  # Don't update current-statistics on error
            no_update,  # Don't update jira-cache-status on error
            no_update,  # Don't update dropdown on error
        )


# ============================================================================
# Auto-Reload Data When Query Switches
# ============================================================================


# DISABLED: Auto-reload on query switch
# User requirement: Query dropdown should not trigger data loading automatically
# Data should only be loaded via explicit "Load Data" button click
# This allows users to select and modify queries without triggering data loads
#
# @callback(
#     [
#         Output("statistics-table", "data", allow_duplicate=True),
#         Output("current-statistics", "data", allow_duplicate=True),
#         Output("current-settings", "data", allow_duplicate=True),
#         Output("total-items-input", "value", allow_duplicate=True),
#         Output("estimated-items-input", "value", allow_duplicate=True),
#         Output("total-points-display", "value", allow_duplicate=True),
#         Output("estimated-points-input", "value", allow_duplicate=True),
#     ],
#     Input("query-selector", "value"),
#     State("query-selector", "options"),
#     prevent_initial_call=True,
# )
# def auto_reload_data_on_query_switch(selected_query_id, current_options):
#     """Automatically reload statistics and settings when query switches.
#
#     This ensures that switching queries immediately updates all displayed data
#     without requiring manual "Load Data" button click.
#
#     Args:
#         selected_query_id: Newly selected query ID
#         current_options: Current dropdown options (for validation)
#
#     Returns:
#         Tuple of (statistics, statistics_store, settings, total_items,
#                   estimated_items, total_points, estimated_points)
#     """
#     if not selected_query_id or selected_query_id == "__create_new__":
#         raise PreventUpdate
#
#     try:
#         from data.persistence import (
#             load_statistics,
#             load_unified_project_data,
#             load_app_settings,
#         )
#
#         # Load statistics from database for active query
#         statistics, _ = load_statistics()
#
#         # Load unified project data for scope
#         unified_data = load_unified_project_data()
#         scope = unified_data.get("project_scope", {})
#
#         estimated_items = scope.get("estimated_items", 0)
#         estimated_points = scope.get("estimated_points", 0)
#         total_items = scope.get("remaining_items", 0)
#         total_points = scope.get("remaining_total_points", 0)
#         total_points_display = f"{total_points:.0f}"
#
#         # Load settings and update with actual scope values
#         settings = load_app_settings()
#         settings = {**settings}
#         settings.update(
#             {
#                 "total_items": total_items,
#                 "total_points": total_points,
#                 "estimated_items": estimated_items,
#                 "estimated_points": estimated_points,
#             }
#         )
#
#         logger.info(
#             f"Auto-reloaded data for query {selected_query_id}: {len(statistics)} data points"
#         )
#
#         return (
#             statistics,
#             statistics,  # Update store
#             settings,
#             total_items,
#             estimated_items,
#             total_points_display,
#             estimated_points,
#         )
#
#     except Exception as e:
#         logger.error(f"Failed to auto-reload data on query switch: {e}")
#         raise PreventUpdate
