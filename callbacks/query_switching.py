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
        Output("query-empty-state", "className"),
    ],
    Input("url", "pathname"),  # Trigger on page load
    prevent_initial_call=False,
)
def populate_query_dropdown(_pathname):
    """Populate query dropdown with queries from active profile.

    Returns:
        Tuple of (options, value, empty_state_class)
    """
    try:
        from data.query_manager import get_active_profile_id, list_queries_for_profile

        # Get active profile
        profile_id = get_active_profile_id()

        # List queries for this profile
        queries = list_queries_for_profile(profile_id)

        if not queries:
            # Show empty state
            return [], "", "mb-0"

        # Build dropdown options
        options = []
        active_value = ""

        for query in queries:
            label = query.get("name", "Unnamed Query")
            value = query.get("id", "")

            # Mark active query
            if query.get("is_active", False):
                label += " ★"
                active_value = value

            options.append({"label": label, "value": value})

        # Hide empty state
        return options, active_value, "mb-0 d-none"

    except Exception as e:
        logger.error(f"Failed to populate query dropdown: {e}")
        # Return safe defaults
        return [], "", "mb-0 d-none"


# ============================================================================
# Query Switching
# ============================================================================


@callback(
    [
        Output("url", "pathname", allow_duplicate=True),
        Output("query-loading-output", "children"),
    ],
    Input("query-selector", "value"),
    State("query-selector", "options"),
    prevent_initial_call=True,
)
def switch_query_callback(selected_query_id, options):
    """Switch to selected query and reload dashboard.

    Performance target: <50ms for switch operation.

    Args:
        selected_query_id: Query ID selected from dropdown
        options: Current dropdown options (for validation)

    Returns:
        Tuple of (pathname, loading_message)
    """
    if not selected_query_id:
        raise PreventUpdate

    try:
        import time
        from data.query_manager import switch_query, get_active_query_id

        # Check if already on this query
        current_query_id = get_active_query_id()
        if selected_query_id == current_query_id:
            raise PreventUpdate

        # Performance measurement
        start_time = time.perf_counter()

        # Switch query (atomic operation)
        switch_query(selected_query_id)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"Query switched to '{selected_query_id}' in {elapsed_ms:.2f}ms")

        # Trigger page reload by changing pathname (force dashboard refresh)
        # Return to root path to trigger full data reload
        return "/", ""

    except ValueError as e:
        logger.error(f"Query switch validation error: {e}")
        return no_update, f"Error: {e}"

    except Exception as e:
        logger.error(f"Failed to switch query: {e}")
        return no_update, f"Error switching query: {e}"


# ============================================================================
# Query Creation Modal
# ============================================================================


@callback(
    Output("workspace-create-query-modal", "is_open"),
    [
        Input("query-create-button", "n_clicks"),
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

    if triggered == "query-create-button":
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
        Output("query-dropdown", "options"),
        Output("query-dropdown", "value"),
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


# ============================================================================
# Query Deletion
# ============================================================================


@callback(
    Output("delete-query-feedback", "children"),
    Input("confirm-delete-query-btn", "n_clicks"),
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def delete_query_callback(confirm_clicks, selected_query_id):
    """Delete selected query from profile.

    Args:
        confirm_clicks: Confirm delete button clicks
        selected_query_id: Currently selected query ID

    Returns:
        Feedback message
    """
    if not confirm_clicks or not selected_query_id:
        raise PreventUpdate

    try:
        from data.query_manager import get_active_profile_id, delete_query

        profile_id = get_active_profile_id()

        # Delete query
        delete_query(profile_id, selected_query_id)

        logger.info(f"Deleted query '{selected_query_id}' from profile '{profile_id}'")

        return "Query deleted successfully!"

    except PermissionError as e:
        logger.warning(f"Query deletion prevented: {e}")
        return str(e)

    except ValueError as e:
        logger.warning(f"Query deletion validation failed: {e}")
        return str(e)

    except Exception as e:
        logger.error(f"Failed to delete query: {e}")
        return f"Error deleting query: {e}"
