"""
Accordion Settings Panel Callbacks

Handles progressive disclosure and dependency enforcement for the new accordion-based
settings panel (Feature 011: Profile-First Dependency Architecture).

Callbacks:
1. update_configuration_status - Track completion of each dependency step
2. update_section_states - Enable/disable accordion sections based on dependencies
3. update_section_titles - Add status icons to section titles
4. enforce_query_save_before_data_ops - Disable data operations until query saved
"""

import logging
from dash import Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)


@callback(
    Output("configuration-status-store", "data"),
    [
        Input("profile-selector", "value"),
        Input("jira-config-status-indicator", "children"),
        Input("save-query-btn", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def update_configuration_status(profile_id, jira_status, save_query_clicks):
    """
    Track configuration completion status for dependency chain.

    Updates a status store that tracks which steps in the dependency chain
    are complete. Used to enable/disable accordion sections.

    Dependency Chain:
    1. Profile exists (always enabled)
    2. JIRA configured → enables Field Mappings & Query Management
    3. Field mappings configured → recommended but not required
    4. Query saved → enables Data Operations

    Args:
        profile_id: Currently active profile ID
        jira_status: JIRA connection status indicator content
        save_query_clicks: Number of times save query button clicked

    Returns:
        dict: Configuration status with enabled/complete flags for each section
    """
    # Determine JIRA configuration status
    # JIRA is configured if status indicator shows success
    jira_configured = False
    if jira_status:
        jira_status_str = str(jira_status)
        jira_configured = (
            "success" in jira_status_str.lower() or "✅" in jira_status_str
        )

    # Determine if query is saved
    # If save button has been clicked at least once, query is saved
    query_saved = save_query_clicks is not None and save_query_clicks > 0

    status = {
        "profile": {
            "enabled": True,  # Always enabled
            "complete": profile_id is not None,
            "icon": "✅" if profile_id else "⏳",
        },
        "jira": {
            "enabled": profile_id is not None,
            "complete": jira_configured,
            "icon": "✅" if jira_configured else ("⏳" if profile_id else "🔒"),
        },
        "fields": {
            "enabled": jira_configured,  # Enabled when JIRA configured
            "complete": False,  # Field mappings are optional
            "icon": "⏳" if jira_configured else "🔒",
        },
        "queries": {
            "enabled": jira_configured,  # Enabled when JIRA configured
            "complete": query_saved,
            "icon": "✅" if query_saved else ("⏳" if jira_configured else "🔒"),
        },
        "data_operations": {
            "enabled": query_saved,  # Enabled when query saved
            "complete": False,  # Always requires manual trigger
            "icon": "⏳" if query_saved else "🔒",
        },
    }

    logger.debug(
        f"[Config Status] Profile: {status['profile']['icon']}, "
        f"JIRA: {status['jira']['icon']}, "
        f"Fields: {status['fields']['icon']}, "
        f"Queries: {status['queries']['icon']}, "
        f"Data: {status['data_operations']['icon']}"
    )

    return status


@callback(
    [
        Output("jira-section-accordion", "class_name"),
        Output("field-mapping-section-accordion", "class_name"),
        Output("query-section-accordion", "class_name"),
        Output("data-actions-section-accordion", "class_name"),
    ],
    Input("configuration-status-store", "data"),
    prevent_initial_call=False,
)
def update_section_states(config_status):
    """
    Enable/disable accordion sections based on dependencies.

    Adds 'disabled' class to sections that should not be accessible yet.
    This provides visual feedback about which steps are blocked.

    Args:
        config_status: Configuration status dict from update_configuration_status

    Returns:
        tuple: CSS class names for each accordion section (4 sections)
    """
    if not config_status:
        # No status available - disable all except profile
        return (
            "accordion-item-disabled",
            "accordion-item-disabled",
            "accordion-item-disabled",
            "accordion-item-disabled",
        )

    # Enable sections based on their enabled flag
    jira_class = "" if config_status["jira"]["enabled"] else "accordion-item-disabled"
    fields_class = (
        "" if config_status["fields"]["enabled"] else "accordion-item-disabled"
    )
    queries_class = (
        "" if config_status["queries"]["enabled"] else "accordion-item-disabled"
    )
    data_class = (
        "" if config_status["data_operations"]["enabled"] else "accordion-item-disabled"
    )

    return jira_class, fields_class, queries_class, data_class


@callback(
    [
        Output("profile-section-accordion", "title"),
        Output("jira-section-accordion", "title"),
        Output("field-mapping-section-accordion", "title"),
        Output("query-section-accordion", "title"),
        Output("data-actions-section-accordion", "title"),
    ],
    Input("configuration-status-store", "data"),
    prevent_initial_call=False,
)
def update_section_titles(config_status):
    """
    Update section titles with status icons.

    Adds visual indicators (✅ ⏳ 🔒) to accordion section titles
    to show which steps are complete, in progress, or locked.

    Args:
        config_status: Configuration status dict

    Returns:
        tuple: Updated title strings for all 5 sections
    """
    if not config_status:
        # Default titles with no status icons
        return (
            "1️⃣ Profile Settings",
            "2️⃣ JIRA Configuration 🔒",
            "3️⃣ Field Mappings 🔒",
            "4️⃣ Query Management 🔒",
            "5️⃣ Data Operations 🔒",
        )

    # Build titles with status icons
    profile_title = f"1️⃣ Profile Settings {config_status['profile']['icon']}"
    jira_title = f"2️⃣ JIRA Configuration {config_status['jira']['icon']}"
    fields_title = f"3️⃣ Field Mappings {config_status['fields']['icon']}"
    queries_title = f"4️⃣ Query Management {config_status['queries']['icon']}"
    data_title = f"5️⃣ Data Operations {config_status['data_operations']['icon']}"

    return profile_title, jira_title, fields_title, queries_title, data_title


@callback(
    [
        Output("update-data-unified", "disabled"),
        Output("data-operations-alert", "children"),
        Output("data-operations-alert", "is_open"),
    ],
    Input("configuration-status-store", "data"),
    prevent_initial_call=False,
)
def enforce_query_save_before_data_ops(config_status):
    """
    Disable 'Update Data' button until query is saved.

    This enforces the rule: "Query must be saved before it can be executed"
    which prevents users from accidentally fetching data for unsaved queries.

    Args:
        config_status: Configuration status dict

    Returns:
        tuple: (button_disabled, alert_content, alert_is_open)
    """
    if not config_status:
        # No status - disable button
        return True, None, False

    # Check if query is saved
    query_saved = config_status.get("queries", {}).get("complete", False)

    if query_saved:
        # Query saved - enable data operations
        return False, None, False

    # Query not saved - show alert and disable button
    alert = dbc.Alert(
        [
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Query must be saved before fetching data. ",
            html.Strong("Click 'Save Query'"),
            " in the Query Management section first.",
        ],
        color="warning",
        className="mb-0",
    )

    return True, alert, True


# Callback for profile settings save button
@callback(
    Output("profile-settings-status", "children"),
    Input("save-profile-settings-btn", "n_clicks"),
    [
        State("profile-pert-factor-input", "value"),
        State("profile-deadline-input", "value"),
        State("profile-data-points-input", "value"),
        State("profile-show-milestone-checkbox", "value"),
        State("profile-milestone-input", "value"),
    ],
    prevent_initial_call=True,
)
def save_profile_settings(
    n_clicks, pert_factor, deadline, data_points, show_milestone, milestone_date
):
    """
    Save profile-level settings to profile.json.

    Updates the active profile's forecast settings and milestone configuration.

    Args:
        n_clicks: Number of times save button clicked
        pert_factor: PERT multiplier (1.0-3.0)
        deadline: Project deadline date (YYYY-MM-DD)
        data_points: Number of weeks to show (4-52)
        show_milestone: Whether to show milestone
        milestone_date: Milestone date (YYYY-MM-DD)

    Returns:
        dbc.Alert: Success or error message
    """
    if not n_clicks:
        return no_update

    try:
        from data.persistence import save_app_settings

        # Save to profile.json with individual parameters
        save_app_settings(
            pert_factor=pert_factor or 1.2,
            deadline=deadline,
            data_points_count=data_points or 12,
            show_milestone=show_milestone or False,
            milestone=milestone_date if show_milestone else None,
        )

        logger.info(
            f"[Profile Settings] Saved: pert_factor={pert_factor}, "
            f"deadline={deadline}, data_points={data_points}, "
            f"show_milestone={show_milestone}, milestone={milestone_date}"
        )

        return dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                "Profile settings saved successfully!",
            ],
            color="success",
            duration=3000,
        )

    except Exception as e:
        logger.error(f"[Profile Settings] Error saving: {e}", exc_info=True)
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Error saving settings: {e}",
            ],
            color="danger",
        )


logger.info("[Callbacks] Accordion settings panel callbacks registered")


@callback(
    Output("query-jql-editor", "value"),
    Input("query-selector", "value"),
    prevent_initial_call=True,
)
def load_query_jql(query_id):
    """
    Load selected query's JQL into the editor.

    When user selects a different query from the dropdown, populate
    the JQL editor with that query's JQL string.

    Args:
        query_id: Selected query ID

    Returns:
        str: JQL query string for the selected query
    """
    if not query_id:
        return ""

    try:
        from data.query_manager import get_active_profile_id, PROFILES_DIR
        import json

        profile_id = get_active_profile_id()
        query_file = PROFILES_DIR / profile_id / "queries" / query_id / "query.json"

        if not query_file.exists():
            logger.warning(f"[Query Load] Query file not found: {query_file}")
            return ""

        with open(query_file, "r", encoding="utf-8") as f:
            query_data = json.load(f)

        jql = query_data.get("jql", "")
        logger.info(f"[Query Load] Loaded JQL for query '{query_id}': {jql[:50]}...")

        return jql

    except Exception as e:
        logger.error(
            f"[Query Load] Error loading query '{query_id}': {e}", exc_info=True
        )
        return ""


@callback(
    Output("query-save-status", "children"),
    Input("save-query-btn", "n_clicks"),
    [
        State("query-selector", "value"),
        State("query-jql-editor", "value"),
    ],
    prevent_initial_call=True,
)
def save_query_changes(n_clicks, query_id, jql):
    """
    Save changes to the current query.

    Updates the selected query's JQL in its query.json file.

    Args:
        n_clicks: Number of times save button clicked
        query_id: Currently selected query ID
        jql: JQL query string from editor

    Returns:
        dbc.Alert: Success or error message
    """
    if not n_clicks:
        return no_update

    if not query_id:
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                "No query selected",
            ],
            color="warning",
            duration=3000,
        )

    if not jql or not jql.strip():
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                "JQL query cannot be empty",
            ],
            color="warning",
            duration=3000,
        )

    try:
        from data.query_manager import get_active_profile_id, update_query

        profile_id = get_active_profile_id()

        # Update query with new JQL
        success = update_query(profile_id, query_id, jql=jql.strip())

        if success:
            logger.info(f"[Query Save] Successfully updated query '{query_id}'")
            return dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Query '{query_id}' saved successfully!",
                ],
                color="success",
                duration=3000,
            )
        else:
            return dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "Failed to save query",
                ],
                color="danger",
                duration=3000,
            )

    except Exception as e:
        logger.error(
            f"[Query Save] Error saving query '{query_id}': {e}", exc_info=True
        )
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Error saving query: {e}",
            ],
            color="danger",
        )


@callback(
    Output("query-jql-editor", "value", allow_duplicate=True),
    Input("cancel-query-edit-btn", "n_clicks"),
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def cancel_query_edit(n_clicks, query_id):
    """
    Cancel query editing and reload original JQL.

    Reloads the query's JQL from file, discarding any unsaved changes.

    Args:
        n_clicks: Number of times cancel button clicked
        query_id: Currently selected query ID

    Returns:
        str: Original JQL query string
    """
    if not n_clicks or not query_id:
        return no_update

    try:
        from data.query_manager import get_active_profile_id, PROFILES_DIR
        import json

        profile_id = get_active_profile_id()
        query_file = PROFILES_DIR / profile_id / "queries" / query_id / "query.json"

        if not query_file.exists():
            logger.warning(f"[Query Cancel] Query file not found: {query_file}")
            return no_update

        with open(query_file, "r", encoding="utf-8") as f:
            query_data = json.load(f)

        jql = query_data.get("jql", "")
        logger.info(f"[Query Cancel] Reloaded original JQL for query '{query_id}'")

        return jql

    except Exception as e:
        logger.error(
            f"[Query Cancel] Error reloading query '{query_id}': {e}", exc_info=True
        )
        return no_update
