"""Query Management Callbacks for Unified Query Workflow.

Handles inline query creation, editing, saving, and state management.
Implements the Save/Save As/Discard workflow with auto-name generation.

Workflow:
1. Select query from dropdown → Load query data
2. Select "→ Create New Query" → Clear fields
3. Edit JQL/name → Enable Save/Save As/Discard buttons
4. Save → Overwrite selected query (destructive)
5. Save As → Create new query with UUID
6. Discard → Revert to last saved state
"""

import logging

from dash import Input, Output, State, callback, html, no_update
from dash.exceptions import PreventUpdate

from ui.toast_notifications import create_error_toast, create_success_toast

logger = logging.getLogger(__name__)


# ============================================================================
# Change Detection & Button State Management
# ============================================================================


@callback(
    [
        Output("save-query-btn", "disabled"),
        Output("save-as-query-btn", "disabled"),
        Output("discard-query-changes-btn", "disabled"),
        Output("data-operations-alert", "is_open", allow_duplicate=True),
    ],
    [
        Input("query-name-input", "value"),
        Input("query-jql-editor", "value"),
        Input("query-selector", "value"),
    ],
    [
        State("query-selector", "options"),
    ],
    prevent_initial_call="initial_duplicate",
)
def manage_button_states(
    current_name: str,
    current_jql: str,
    selected_query_id: str,
    dropdown_options: list,
) -> tuple[bool, bool, bool, bool]:
    """Manage Save/Save As/Discard button states based on changes.

    Button Logic:
    - Save: Enabled when JQL changed (and not "Create New")
    - Save As: Enabled when name OR JQL changed
    - Discard: Enabled when name OR JQL changed
    - Alert: Show when changes detected (prevents Update Data)

    Note: When switching queries, there's a brief moment where the dropdown value
    changes but the JQL/name haven't updated yet. We detect this and suppress the
    alert to avoid showing "unsaved changes" during legitimate query switches.

    Args:
        current_name: Current query name from input
        current_jql: Current JQL from editor
        selected_query_id: Selected query ID from dropdown
        dropdown_options: Current dropdown options (to get original values)

    Returns:
        Tuple of (save_disabled, save_as_disabled, discard_disabled, show_alert)
    """
    from dash import callback_context

    logger.info(
        f"[QueryManagement] CALLBACK FIRED - selected_query_id='{selected_query_id}', "
        f"current_name='{current_name}', current_jql='{current_jql[:60] if current_jql else '(empty)'}...'"
    )

    # Detect if query-selector triggered this callback (query switch in progress)
    ctx = callback_context
    triggered_by_selector = False
    if ctx.triggered:
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        triggered_by_selector = trigger_id == "query-selector"
        if triggered_by_selector:
            logger.info(
                "[QueryManagement] Query switch in progress - suppressing alert to avoid race condition"
            )

    try:
        # Handle "Create New Query" mode
        if selected_query_id == "__create_new__":
            # Creating new query - enable Save/Save As when JQL is entered
            has_name = bool(current_name and current_name.strip())
            has_jql = bool(current_jql and current_jql.strip())
            has_any_content = has_name or has_jql

            # Save: Enabled when JQL is present (name auto-generated if empty)
            save_disabled = not has_jql
            # Save As: Enabled when JQL is present (user can provide custom name)
            save_as_disabled = not has_jql
            # Discard: Enabled when any content (can clear fields)
            discard_disabled = not has_any_content

            logger.info(
                f"[QueryManagement] Create New mode - Name: '{current_name}', JQL: '{current_jql[:50] if current_jql else ''}...', "
                f"Save: {not save_disabled}, Save As: {not save_as_disabled}, Discard: {not discard_disabled}"
            )

            logger.info(
                f"[QueryManagement] RETURNING: save_disabled={save_disabled}, save_as_disabled={save_as_disabled}, "
                f"discard_disabled={discard_disabled}, alert={has_any_content}"
            )

            # Suppress alert if triggered by query selector (race condition during switch)
            show_alert = has_any_content and not triggered_by_selector

            return save_disabled, save_as_disabled, discard_disabled, show_alert

        # Handle no query selected (empty dropdown)
        if not selected_query_id:
            # This is the first query in profile - enable Save/Save As when JQL is entered
            has_name = bool(current_name and current_name.strip())
            has_jql = bool(current_jql and current_jql.strip())
            has_any_content = has_name or has_jql

            # For first query: Enable Save when JQL present (name will be auto-generated)
            # Save: Enabled when JQL is present (name auto-generated if empty)
            save_disabled = not has_jql
            # Save As: Enabled when JQL is present (user can provide custom name)
            save_as_disabled = not has_jql
            # Discard: Enabled when any content present (can clear fields)
            discard_disabled = not has_any_content

            logger.info(
                f"[QueryManagement] First query mode (no selection) - Name: '{current_name}', JQL: '{current_jql[:50] if current_jql else ''}...', "
                f"Save: {not save_disabled}, Save As: {not save_as_disabled}, Discard: {not discard_disabled}"
            )

            logger.info(
                f"[QueryManagement] RETURNING: save_disabled={save_disabled}, save_as_disabled={save_as_disabled}, "
                f"discard_disabled={discard_disabled}, alert={has_any_content}"
            )

            # Suppress alert if triggered by query selector (race condition during switch)
            show_alert = has_any_content and not triggered_by_selector

            return save_disabled, save_as_disabled, discard_disabled, show_alert

        # Get original query data from dropdown options
        from data.query_manager import get_active_profile_id, list_queries_for_profile

        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        query = next((q for q in queries if q.get("id") == selected_query_id), None)
        if not query:
            logger.warning(f"Query {selected_query_id} not found in profile")
            return True, True, True, False

        original_name = query.get("name", "")
        original_jql = query.get("jql", "")

        # Detect changes
        name_changed = (current_name or "") != original_name
        jql_changed = (current_jql or "") != original_jql
        any_changes = name_changed or jql_changed

        # Button states based on changes
        save_disabled = not jql_changed  # Save only enabled when JQL changed
        save_as_disabled = not any_changes  # Save As enabled when anything changed
        discard_disabled = not any_changes  # Discard enabled when anything changed

        # Suppress alert if triggered by query selector (race condition during switch)
        # When switching queries, the selector changes first, then JQL/name update async
        show_alert = any_changes and not triggered_by_selector

        logger.debug(
            f"Button states - Save: {not save_disabled}, Save As: {not save_as_disabled}, "
            f"Discard: {not discard_disabled}, Alert: {show_alert} (triggered_by_selector: {triggered_by_selector})"
        )

        return save_disabled, save_as_disabled, discard_disabled, show_alert

    except Exception as e:
        logger.error(f"Failed to manage button states: {e}")
        # Safe defaults - disable all buttons
        return True, True, True, False


# ============================================================================
# Auto-Generate Query Name from JQL
# ============================================================================


@callback(
    Output("query-name-input", "value", allow_duplicate=True),
    Input("query-jql-editor", "value"),
    [State("query-selector", "value"), State("query-name-input", "value")],
    prevent_initial_call=True,
)
def auto_generate_query_name(
    jql_query: str, selected_query_id: str, current_name: str
) -> str:
    """Auto-generate query name from JQL when creating new query.

    Only generates name when:
    1. "Create New Query" is selected OR no query selected (first query)
    2. JQL has content
    3. Name field is empty (don't overwrite manual names)

    Uses simple heuristics to create readable names:
    - Extract project key
    - Extract time range (e.g., "-12w")
    - Extract status filters
    - Format: "ProjectKey Last 12 Weeks"

    Args:
        jql_query: Current JQL query string
        selected_query_id: Selected query ID (or "__create_new__" or empty)
        current_name: Current value in query name input

    Returns:
        Generated query name or no_update
    """
    # Only auto-generate for "Create New Query" mode or no selection (first query)
    if selected_query_id and selected_query_id != "__create_new__":
        raise PreventUpdate

    # Don't overwrite manually entered names
    if current_name and current_name.strip():
        raise PreventUpdate

    if not jql_query or not jql_query.strip():
        raise PreventUpdate

    try:
        import re

        # Extract project key (e.g., "project = KAFKA")
        project_match = re.search(
            r"project\s*=\s*['\"]?(\w+)", jql_query, re.IGNORECASE
        )
        project = project_match.group(1) if project_match else "Query"

        # Extract time range (e.g., "created >= -12w")
        time_match = re.search(r"-(\d+)([wdmyh])", jql_query, re.IGNORECASE)
        if time_match:
            amount = time_match.group(1)
            unit_map = {
                "w": "Weeks",
                "d": "Days",
                "m": "Months",
                "y": "Years",
                "h": "Hours",
            }
            unit = unit_map.get(time_match.group(2).lower(), "")
            time_desc = f"Last {amount} {unit}"
        else:
            time_desc = ""

        # Extract status filter (e.g., "status = Done")
        status_match = re.search(r"status\s*=\s*['\"]?(\w+)", jql_query, re.IGNORECASE)
        status = status_match.group(1) if status_match else ""

        # Build name
        parts = [project]
        if time_desc:
            parts.append(time_desc)
        if status:
            parts.append(status)

        generated_name = " ".join(parts)

        logger.info(f"Auto-generated query name: {generated_name}")
        return generated_name

    except Exception as e:
        logger.error(f"Failed to auto-generate query name: {e}")
        raise PreventUpdate from e


# ============================================================================
# Save Query (Overwrite)
# ============================================================================


@callback(
    [
        Output("query-save-status", "children", allow_duplicate=True),
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("save-query-btn", "n_clicks"),
    [
        State("query-name-input", "value"),
        State("query-jql-editor", "value"),
        State("query-selector", "value"),
    ],
    prevent_initial_call=True,
)
def save_query_overwrite(
    n_clicks: int,
    query_name: str,
    query_jql: str,
    selected_query_id: str,
) -> tuple:
    """Save query by overwriting the selected query (destructive operation).

    Validation:
    - Cannot save if "Create New Query" is selected
    - Requires valid query name and JQL
    - Confirms destructive overwrite with user

    Args:
        n_clicks: Button click count
        query_name: Query name from input
        query_jql: JQL query from editor
        selected_query_id: Selected query ID to overwrite

    Returns:
        Tuple of (status_message, updated_options, updated_value, toast_notification)
    """
    if not n_clicks:
        raise PreventUpdate

    try:
        # Handle no query selected (first query in profile)
        if not selected_query_id:
            # Creating first query - treat like "Save As" with auto-generated name
            if not query_jql or not query_jql.strip():
                feedback = create_error_toast(
                    "JQL query cannot be empty",
                    header="Validation Error",
                )
                return "", no_update, no_update, feedback

            # Auto-generate name if empty
            if not query_name or not query_name.strip():
                from data.query_name_generator import generate_query_name

                query_name = generate_query_name(query_jql.strip())
                logger.info(
                    f"[QueryManagement] Auto-generated name for first query: '{query_name}'"
                )

            # Create first query
            from data.query_manager import (
                create_query,
                get_active_profile_id,
                list_queries_for_profile,
                switch_query,
            )

            profile_id = get_active_profile_id()
            new_query_id = create_query(profile_id, query_name, query_jql.strip())
            switch_query(new_query_id)

            logger.info(
                f"[QueryManagement] Created first query '{new_query_id}' in profile '{profile_id}'"
            )

            # Refresh dropdown and select new query
            from data.query_manager import get_query_dropdown_options

            options = get_query_dropdown_options(profile_id)

            toast = create_success_toast(
                f"Query '{query_name}' created successfully!",
                header="Query Created",
            )

            return "", options, new_query_id, toast

        # Handle "Create New Query" mode - same logic as "no selection"
        if selected_query_id == "__create_new__":
            # Creating new query - treat like first query
            if not query_jql or not query_jql.strip():
                feedback = create_error_toast(
                    "JQL query cannot be empty",
                    header="Validation Error",
                )
                return "", no_update, no_update, feedback

            # Auto-generate name if empty
            if not query_name or not query_name.strip():
                from data.query_name_generator import generate_query_name

                query_name = generate_query_name(query_jql.strip())
                logger.info(
                    f"[QueryManagement] Auto-generated name for new query: '{query_name}'"
                )

            # Create new query
            from data.query_manager import (
                create_query,
                get_active_profile_id,
                list_queries_for_profile,
                switch_query,
            )

            profile_id = get_active_profile_id()

            # Check for name collision
            queries = list_queries_for_profile(profile_id)
            for query in queries:
                if query.get("name", "").strip() == query_name.strip():
                    from ui.toast_notifications import create_warning_toast

                    feedback = create_warning_toast(
                        f"Query name '{query_name}' already exists. Please choose a different name.",
                        header="Name Collision",
                    )
                    return "", no_update, no_update, feedback

            new_query_id = create_query(profile_id, query_name, query_jql.strip())
            switch_query(new_query_id)

            logger.info(
                f"[QueryManagement] Created new query '{new_query_id}' in profile '{profile_id}'"
            )

            # Refresh dropdown and select new query
            from data.query_manager import get_query_dropdown_options

            options = get_query_dropdown_options(profile_id)

            toast = create_success_toast(
                f"Query '{query_name}' created successfully!",
                header="Query Created",
            )

            return "", options, new_query_id, toast

        # Validate inputs for existing query update
        if not query_name or not query_name.strip():
            feedback = create_error_toast(
                "Query name cannot be empty",
                header="Validation Error",
            )
            return "", no_update, no_update, feedback

        if not query_jql or not query_jql.strip():
            feedback = create_error_toast(
                "JQL query cannot be empty",
                header="Validation Error",
            )
            return "", no_update, no_update, feedback

        # Update query
        from data.query_manager import (
            get_active_profile_id,
            list_queries_for_profile,
            update_query,
        )

        profile_id = get_active_profile_id()

        # Check for name collision with OTHER queries
        queries = list_queries_for_profile(profile_id)
        for query in queries:
            if (
                query.get("id") != selected_query_id
                and query.get("name", "").strip() == query_name.strip()
            ):
                from ui.toast_notifications import create_warning_toast

                feedback = create_warning_toast(
                    f"Query name '{query_name}' already exists. Please choose a different name.",
                    header="Name Collision",
                )
                return "", no_update, no_update, feedback

        update_query(
            profile_id, selected_query_id, query_name.strip(), query_jql.strip()
        )

        logger.info(f"Query '{selected_query_id}' updated successfully")

        # Refresh dropdown
        from data.query_manager import get_query_dropdown_options

        options = get_query_dropdown_options(profile_id)

        toast = create_success_toast(
            f"Query '{query_name}' saved successfully!",
            header="Query Saved",
        )

        return "", options, selected_query_id, toast

    except ValueError as e:
        logger.warning(f"Query save validation failed: {e}")
        feedback = create_error_toast(str(e), header="Validation Error")
        return "", no_update, no_update, feedback

    except Exception as e:
        logger.error(f"Failed to save query: {e}")
        feedback = create_error_toast(f"Error saving query: {e}", header="Save Failed")
        return "", no_update, no_update, feedback


# ============================================================================
# Save As (Create New Query)
# ============================================================================


@callback(
    [
        Output("query-save-status", "children", allow_duplicate=True),
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("save-as-query-btn", "n_clicks"),
    [
        State("query-name-input", "value"),
        State("query-jql-editor", "value"),
    ],
    prevent_initial_call=True,
)
def save_query_as_new(
    n_clicks: int,
    query_name: str,
    query_jql: str,
) -> tuple:
    """Save query as new (create new query with UUID).

    Safe operation - does not overwrite existing queries.

    Validation:
    - Requires valid query name and JQL
    - Checks for name collisions

    Args:
        n_clicks: Button click count
        query_name: Query name from input
        query_jql: JQL query from editor

    Returns:
        Tuple of (status_message, updated_options, new_query_id, toast_notification)
    """
    if not n_clicks:
        raise PreventUpdate

    try:
        # Validate inputs
        if not query_name or not query_name.strip():
            feedback = create_error_toast(
                "Query name cannot be empty",
                header="Validation Error",
            )
            return "", no_update, no_update, feedback

        if not query_jql or not query_jql.strip():
            feedback = create_error_toast(
                "JQL query cannot be empty",
                header="Validation Error",
            )
            return "", no_update, no_update, feedback

        # Create new query
        from data.query_manager import (
            create_query,
            get_active_profile_id,
            list_queries_for_profile,
        )

        profile_id = get_active_profile_id()

        # Check for name collision
        queries = list_queries_for_profile(profile_id)
        for query in queries:
            if query.get("name", "").strip() == query_name.strip():
                from ui.toast_notifications import create_warning_toast

                feedback = create_warning_toast(
                    f"Query name '{query_name}' already exists. Please choose a different name.",
                    header="Name Collision",
                )
                return "", no_update, no_update, feedback

        query_id = create_query(profile_id, query_name.strip(), query_jql.strip())

        logger.info(f"New query '{query_id}' created successfully")

        # Refresh dropdown and select new query
        from data.query_manager import get_query_dropdown_options

        options = get_query_dropdown_options(profile_id)

        toast = create_success_toast(
            f"New query '{query_name}' created successfully!",
            header="Query Created",
        )

        return "", options, query_id, toast

    except ValueError as e:
        logger.warning(f"Query creation validation failed: {e}")
        feedback = create_error_toast(str(e), header="Validation Error")
        return "", no_update, no_update, feedback

    except Exception as e:
        logger.error(f"Failed to create query: {e}")
        feedback = create_error_toast(
            f"Error creating query: {e}",
            header="Creation Failed",
        )
        return "", no_update, no_update, feedback


# ============================================================================
# Discard Changes
# ============================================================================


@callback(
    [
        Output("query-name-input", "value", allow_duplicate=True),
        Output("query-jql-editor", "value", allow_duplicate=True),
        Output("query-save-status", "children", allow_duplicate=True),
    ],
    Input("discard-query-changes-btn", "n_clicks"),
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def discard_query_changes(n_clicks: int, selected_query_id: str) -> tuple:
    """Discard changes and revert to last saved state.

    Behavior:
    - If "Create New Query": Clear all fields
    - If existing query: Reload original name and JQL

    Args:
        n_clicks: Button click count
        selected_query_id: Selected query ID (or "__create_new__")

    Returns:
        Tuple of (query_name, query_jql, status_message)
    """
    if not n_clicks:
        raise PreventUpdate

    try:
        # Handle "Create New Query" mode - clear fields
        if selected_query_id == "__create_new__":
            feedback = html.Div(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Fields cleared",
                ],
                className="alert alert-info",
            )
            return "", "", feedback

        # Handle existing query - reload original data
        from data.query_manager import get_active_profile_id, list_queries_for_profile

        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        query = next((q for q in queries if q.get("id") == selected_query_id), None)
        if not query:
            logger.warning(f"Query {selected_query_id} not found")
            raise PreventUpdate

        original_name = query.get("name", "")
        original_jql = query.get("jql", "")

        feedback = html.Div(
            [
                html.I(className="fas fa-undo me-2"),
                "Changes discarded",
            ],
            className="alert alert-info",
        )

        logger.info(f"Discarded changes for query '{selected_query_id}'")
        return original_name, original_jql, feedback

    except Exception as e:
        logger.error(f"Failed to discard changes: {e}")
        raise PreventUpdate from e
