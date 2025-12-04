"""Callbacks for field mapping configuration.

Handles field mapping modal interactions, Jira field discovery,
validation, and persistence.
"""

from dash import callback, callback_context, Output, Input, State, no_update, ALL, html
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import logging

from data.field_mapper import (
    fetch_available_jira_fields,
)
from ui.field_mapping_modal import (
    create_field_mapping_form,
    create_field_mapping_error_alert,
)
from ui.toast_notifications import (
    create_success_toast,
    create_error_toast,
)

logger = logging.getLogger(__name__)


def _create_dora_flow_mappings_display(field_mappings: Dict) -> html.Div:
    """Create a read-only display of DORA/Flow field mappings.

    Args:
        field_mappings: Nested dict with 'dora' and 'flow' keys

    Returns:
        html.Div with formatted display of current mappings
    """
    content = []

    # DORA Metrics Section
    if "dora" in field_mappings:
        content.append(html.H5("DORA Metrics Configuration", className="mt-3 mb-3"))
        dora = field_mappings["dora"]

        for metric_name, metric_fields in dora.items():
            # Format metric name nicely
            display_name = metric_name.replace("_", " ").title()
            content.append(html.H6(display_name, className="text-primary mt-3"))

            # Create table of field mappings
            rows = []
            for field_name, field_value in metric_fields.items():
                rows.append(
                    html.Tr(
                        [
                            html.Td(
                                field_name.replace("_", " ").title(),
                                className="font-weight-bold",
                            ),
                            html.Td(html.Code(str(field_value))),
                        ]
                    )
                )

            content.append(
                html.Table(
                    [html.Tbody(rows)], className="table table-sm table-borderless mb-3"
                )
            )

    # Flow Metrics Section
    if "flow" in field_mappings:
        content.append(html.H5("Flow Metrics Configuration", className="mt-4 mb-3"))
        flow = field_mappings["flow"]

        for metric_name, metric_fields in flow.items():
            # Format metric name nicely
            display_name = metric_name.replace("_", " ").title()
            content.append(html.H6(display_name, className="text-primary mt-3"))

            # Create table of field mappings
            rows = []
            for field_name, field_value in metric_fields.items():
                if isinstance(field_value, list):
                    field_value = ", ".join(field_value)
                rows.append(
                    html.Tr(
                        [
                            html.Td(
                                field_name.replace("_", " ").title(),
                                className="font-weight-bold",
                            ),
                            html.Td(html.Code(str(field_value))),
                        ]
                    )
                )

            content.append(
                html.Table(
                    [html.Tbody(rows)], className="table table-sm table-borderless mb-3"
                )
            )

    # Add informational alert
    return html.Div(
        [
            dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "DORA and Flow metrics use structured field mappings configured in ",
                    html.Code("app_settings.json"),
                    ". See ",
                    html.Code("DORA_FLOW_FIELD_MAPPING.md"),
                    " for detailed documentation on these mappings.",
                ],
                color="info",
                className="mb-4",
            ),
            *content,
        ]
    )


# ============================================================================
# STATE MANAGEMENT - Real-time tracking of all form changes
# ============================================================================


@callback(
    Output("field-mapping-state-store", "data"),
    Input({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_form_state_changes(*args):
    """Track field mapping dropdown changes in real-time.

    This callback fires whenever ANY field mapping dropdown (Fields tab) changes.
    Tab-specific dropdowns are tracked via the render callback instead.

    Args:
        *args: All dropdown values followed by current state

    Returns:
        Updated state dict with current form values
    """
    from dash import ctx

    # Get current state (last argument)
    current_state = args[-1] or {}

    # Get triggered input
    triggered = ctx.triggered_id

    if not triggered:
        return no_update

    # Get the new value
    new_value = ctx.triggered[0]["value"]

    # Update state based on which input was triggered
    if isinstance(triggered, dict):
        # Field mapping dropdown (pattern-matched ID)
        # Structure: {"type": "field-mapping-dropdown", "metric": "dora", "field": "deployment_date"}
        if triggered.get("type") == "field-mapping-dropdown":
            metric = triggered.get("metric")
            field = triggered.get("field")

            # Initialize field_mappings structure if not exists
            if "field_mappings" not in current_state:
                current_state["field_mappings"] = {}
            if metric not in current_state["field_mappings"]:
                current_state["field_mappings"][metric] = {}

            # Handle multi-select dropdown: extract first value
            # CRITICAL: Only store if value exists (non-empty)
            # Empty/missing fields should NOT be in field_mappings - this allows
            # variable extraction to fall back to changelog-based extraction
            if isinstance(new_value, list):
                if new_value:  # Only store if list has values
                    current_state["field_mappings"][metric][field] = new_value[0]
                elif field in current_state.get("field_mappings", {}).get(metric, {}):
                    # Remove field if user cleared it
                    del current_state["field_mappings"][metric][field]
            else:
                if new_value:  # Only store if value is non-empty
                    current_state["field_mappings"][metric][field] = new_value
                elif field in current_state.get("field_mappings", {}).get(metric, {}):
                    # Remove field if user cleared it
                    del current_state["field_mappings"][metric][field]

    logger.info(f"[StateTracking] Updated state for {triggered}: {new_value}")

    return current_state


# ============================================================================
# NAMESPACE FIELD INPUT STATE TRACKING
# ============================================================================
# NOTE: Namespace inputs do NOT use server-side state tracking.
# Server-side callbacks cause React to re-render inputs, which loses
# autocomplete selections (the "stat" vs "status" bug).
#
# Instead, namespace field values are collected at SAVE time via a
# clientside callback that reads directly from the DOM.
# See: save_field_mappings() and assets/namespace_autocomplete_clientside.js


# ============================================================================
# TAB-SPECIFIC STATE TRACKING
# These callbacks track dropdowns that only exist in specific tabs
# ============================================================================


@callback(
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("development-projects-dropdown", "value"),
    Input("devops-projects-dropdown", "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_projects_tab_changes(dev_projects, devops_projects, current_state):
    """Track Projects tab dropdown changes."""
    current_state = current_state or {}
    current_state["development_projects"] = (
        dev_projects
        if isinstance(dev_projects, list)
        else ([dev_projects] if dev_projects else [])
    )
    current_state["devops_projects"] = (
        devops_projects
        if isinstance(devops_projects, list)
        else ([devops_projects] if devops_projects else [])
    )
    return current_state


@callback(
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("devops-task-types-dropdown", "value"),
    Input("bug-types-dropdown", "value"),
    Input("flow-feature-issue-types-dropdown", "value"),
    Input("flow-feature-effort-categories-dropdown", "value"),
    Input("flow-defect-issue-types-dropdown", "value"),
    Input("flow-defect-effort-categories-dropdown", "value"),
    Input("flow-technical-debt-issue-types-dropdown", "value"),
    Input("flow-technical-debt-effort-categories-dropdown", "value"),
    Input("flow-risk-issue-types-dropdown", "value"),
    Input("flow-risk-effort-categories-dropdown", "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_types_tab_changes(*args):
    """Track Types tab dropdown changes."""
    current_state = args[-1] or {}

    # Map args to state keys (REMOVED story_types and task_types - deprecated)
    state_keys = [
        "devops_task_types",
        "bug_types",
        "flow_feature_issue_types",
        "flow_feature_effort_categories",
        "flow_defect_issue_types",
        "flow_defect_effort_categories",
        "flow_technical_debt_issue_types",
        "flow_technical_debt_effort_categories",
        "flow_risk_issue_types",
        "flow_risk_effort_categories",
    ]

    for i, key in enumerate(state_keys):
        value = args[i]
        current_state[key] = (
            value if isinstance(value, list) else ([value] if value else [])
        )
        # Log Technical Debt changes specifically
        if key == "flow_technical_debt_issue_types" and value:
            logger.info(
                f"[FieldMapping] track_types_tab_changes: Storing {key}={value}"
            )

    return current_state


@callback(
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("completion-statuses-dropdown", "value"),
    Input("active-statuses-dropdown", "value"),
    Input("flow-start-statuses-dropdown", "value"),
    Input("wip-statuses-dropdown", "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_status_tab_changes(completion, active, flow_start, wip, current_state):
    """Track Status tab dropdown changes."""
    current_state = current_state or {}
    current_state["flow_end_statuses"] = (
        completion
        if isinstance(completion, list)
        else ([completion] if completion else [])
    )
    current_state["active_statuses"] = (
        active if isinstance(active, list) else ([active] if active else [])
    )
    current_state["flow_start_statuses"] = (
        flow_start
        if isinstance(flow_start, list)
        else ([flow_start] if flow_start else [])
    )
    current_state["wip_statuses"] = (
        wip if isinstance(wip, list) else ([wip] if wip else [])
    )
    return current_state


@callback(
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("production-environment-values-dropdown", "value"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def track_environment_tab_changes(prod_env, current_state):
    """Track Environment tab dropdown changes."""
    from dash import ctx

    # Only process if this was triggered by an actual user interaction
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update

    current_state = current_state or {}
    current_state["production_environment_values"] = (
        prod_env if isinstance(prod_env, list) else ([prod_env] if prod_env else [])
    )
    return current_state


# ============================================================================
# STATUS VALIDATION - Active and Flow Start should be subsets of WIP
# ============================================================================


@callback(
    Output("active-wip-subset-warning", "children"),
    Input("active-statuses-dropdown", "value"),
    Input("wip-statuses-dropdown", "value"),
    prevent_initial_call=True,
)
def validate_active_wip_subset(active_statuses, wip_statuses):
    """Validate that Active statuses are a subset of WIP statuses.

    Shows a warning alert only when Active contains statuses not in WIP.

    Args:
        active_statuses: List of selected active status names
        wip_statuses: List of selected WIP status names

    Returns:
        Warning alert if validation fails, empty div otherwise
    """
    active_set = set(active_statuses or [])
    wip_set = set(wip_statuses or [])

    # Find statuses in Active that are not in WIP
    not_in_wip = active_set - wip_set

    if not_in_wip:
        # Show warning with specific statuses
        status_list = ", ".join(sorted(not_in_wip))
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong("Warning: "),
                f"These Active statuses are not in WIP: {status_list}",
            ],
            color="warning",
            className="py-2 px-3 mb-0 small",
        )

    # No issues - return empty
    return html.Div()


@callback(
    Output("flow-start-wip-subset-warning", "children"),
    Input("flow-start-statuses-dropdown", "value"),
    Input("wip-statuses-dropdown", "value"),
    prevent_initial_call=True,
)
def validate_flow_start_wip_subset(flow_start_statuses, wip_statuses):
    """Validate that Flow Start statuses are a subset of WIP statuses.

    Shows a warning alert only when Flow Start contains statuses not in WIP.

    Args:
        flow_start_statuses: List of selected flow start status names
        wip_statuses: List of selected WIP status names

    Returns:
        Warning alert if validation fails, empty div otherwise
    """
    flow_start_set = set(flow_start_statuses or [])
    wip_set = set(wip_statuses or [])

    # Find statuses in Flow Start that are not in WIP
    not_in_wip = flow_start_set - wip_set

    if not_in_wip:
        # Show warning with specific statuses
        status_list = ", ".join(sorted(not_in_wip))
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong("Warning: "),
                f"These Flow Start statuses are not in WIP: {status_list}",
            ],
            color="warning",
            className="py-2 px-3 mb-0 small",
        )

    # No issues - return empty
    return html.Div()


# ============================================================================
# MODAL MANAGEMENT
# ============================================================================


@callback(
    Output("field-mapping-modal", "is_open"),
    Output("fetched-field-values-store", "data", allow_duplicate=True),
    Input("open-field-mapping-modal", "n_clicks"),
    Input(
        {"type": "open-field-mapping", "index": ALL}, "n_clicks"
    ),  # Pattern-matching for metric cards
    Input("field-mapping-cancel-button", "n_clicks"),
    Input("field-mapping-save-success", "data"),  # Close only on successful save
    State("field-mapping-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_field_mapping_modal(
    open_clicks: int | None,
    open_clicks_pattern: list,  # List of clicks from pattern-matched buttons
    cancel_clicks: int | None,
    save_success: bool | None,
    is_open: bool,
) -> tuple[bool, Any]:  # Second element is dict or no_update
    """Toggle field mapping modal open/closed.

    Args:
        open_clicks: Open button clicks (from settings panel)
        open_clicks_pattern: List of clicks from pattern-matched metric card buttons
        cancel_clicks: Cancel button clicks
        save_success: True when save is successful (triggers close)
        is_open: Current modal state

    Returns:
        Tuple of (new modal state, fetched values store data)
        - Modal state: True = open, False = closed
        - Store data: Empty dict {} when opening (clears stale data), no_update otherwise
    """
    ctx = callback_context
    if not ctx.triggered:
        return is_open, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_value = ctx.triggered[0]["value"]

    # Debug logging
    logger.info(
        f"[FieldMapping] Modal toggle - trigger_id: {trigger_id}, value: {trigger_value}"
    )

    # Close on cancel - don't clear store (user might reopen)
    if trigger_id == "field-mapping-cancel-button":
        return False, no_update

    # Close ONLY on successful save (when save_success is True)
    if trigger_id == "field-mapping-save-success" and save_success is True:
        return False, no_update

    # Open when open button clicked (from settings panel or metric cards)
    # Must verify it's an actual click (value > 0), not just a button being added to DOM (value = None or 0)
    if trigger_id == "open-field-mapping-modal" or (
        trigger_id.startswith("{") and "open-field-mapping" in trigger_id
    ):
        # Only open if there was an actual click (not None, not 0, not empty list)
        if trigger_value and trigger_value != 0:
            logger.info(f"[FieldMapping] Opening modal from trigger: {trigger_id}")
            # Clear fetched field values when opening to prevent stale data from other profiles
            return True, {}
        else:
            logger.info(
                f"[FieldMapping] Ignoring button render/initial state - trigger: {trigger_id}, value: {trigger_value}"
            )
            return is_open, no_update

    logger.warning(f"[FieldMapping] Modal toggle - unhandled trigger: {trigger_id}")
    return is_open, no_update


# OLD CALLBACK REMOVED - Now using render_tab_content() for 5-tab system
# The populate_field_mapping_form() callback was creating duplicate outputs
# and has been replaced by the comprehensive mappings system below


@callback(
    Output({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    Input({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    prevent_initial_call=True,
)
def enforce_single_selection_in_multi_dropdown(
    field_values: List[List[str]],
) -> List[List[str]]:
    """Enforce single selection in multi-select dropdowns for consistent styling.

    Multi-select dropdowns are used to get the blue pill styling automatically,
    but we only want one value selected at a time. This callback keeps only
    the most recently selected value.

    Args:
        field_values: List of selected values (each is a list due to multi=True)

    Returns:
        List of values with only the last selection kept (each a list with 0-1 items)
    """
    result = []
    for value_list in field_values:
        if value_list and len(value_list) > 1:
            # Keep only the last selected value
            result.append([value_list[-1]])
        else:
            # Keep empty list or single value as-is
            result.append(value_list if value_list else [])
    return result


# NOTE: The validate_field_selection_real_time callback was removed because
# we no longer use simple mode dropdowns. Namespace inputs use clientside
# validation in namespace_autocomplete_clientside.js instead.


def _get_mock_jira_fields() -> List[Dict[str, Any]]:
    """Get mock Jira fields for testing or when API fails.

    Includes standard Jira fields that work with Apache Kafka JIRA.

    Returns:
        List of mock field metadata
    """
    return [
        # Standard Jira fields (always available)
        {
            "field_id": "created",
            "field_name": "Created",
            "field_type": "datetime",
        },
        {
            "field_id": "resolutiondate",
            "field_name": "Resolution Date",
            "field_type": "datetime",
        },
        {
            "field_id": "issuetype",
            "field_name": "Issue Type",
            "field_type": "select",
        },
        {
            "field_id": "status",
            "field_name": "Status",
            "field_type": "select",
        },
        # Mock custom fields (for full Jira instances)
        {
            "field_id": "customfield_10001",
            "field_name": "Deployment Date",
            "field_type": "datetime",
        },
        {
            "field_id": "customfield_10002",
            "field_name": "Story Points",
            "field_type": "number",
        },
        {
            "field_id": "customfield_10003",
            "field_name": "Environment",
            "field_type": "select",
        },
        {
            "field_id": "customfield_10004",
            "field_name": "Commit Date",
            "field_type": "datetime",
        },
        {
            "field_id": "customfield_10005",
            "field_name": "Production Impact",
            "field_type": "select",
        },
        {
            "field_id": "customfield_10006",
            "field_name": "Incident Flag",
            "field_type": "checkbox",
        },
        {
            "field_id": "customfield_10007",
            "field_name": "Work Item Type",
            "field_type": "select",
        },
        {
            "field_id": "customfield_10008",
            "field_name": "Active Hours",
            "field_type": "number",
        },
    ]


def _get_mock_mappings() -> Dict[str, Dict[str, str]]:
    """Get mock field mappings for Phase 4 stub.

    Phase 5+ will extract actual values from form.

    Returns:
        Mock field mappings structure
    """
    return {
        "dora": {
            "deployment_date": "customfield_10001",
            "code_commit_date": "customfield_10004",
        },
        "flow": {
            "flow_item_type": "customfield_10007",
            "status": "status",
            "completed_date": "resolutiondate",
        },
    }


# ========================================================================
# NEW CALLBACKS FOR COMPREHENSIVE MAPPINGS (5-TAB SYSTEM)
# ========================================================================


@callback(
    Output("field-mapping-content", "children"),
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("mappings-tabs", "active_tab"),
    Input("jira-metadata-store", "data"),
    Input("field-mapping-modal", "is_open"),
    Input("auto-configure-refresh-trigger", "data"),  # Trigger from auto-configure
    Input(
        "fetched-field-values-store", "data"
    ),  # Trigger re-render when field values fetched (for Types/Environment tabs)
    State("field-mapping-state-store", "data"),  # Read-only state access
    State("namespace-collected-values", "data"),  # Collected namespace values from DOM
    prevent_initial_call="initial_duplicate",
)
def render_tab_content(
    active_tab: str,
    metadata: dict,
    is_open: bool,
    refresh_trigger: int,
    fetched_field_values: dict,
    state_data: dict,
    collected_namespace_values: dict,
):
    """Render appropriate form based on active tab.

    This callback now uses the state store for all form values, ensuring
    data is preserved across tab switches.

    Args:
        active_tab: ID of currently active tab
        metadata: Cached JIRA metadata from store
        is_open: Whether modal is open
        refresh_trigger: Trigger value from auto-configure
        fetched_field_values: Dynamically fetched field values (triggers re-render for Types/Env tabs)
        state_data: Current form state from state store
        collected_namespace_values: Values collected from namespace inputs (DOM)

    Returns:
        Tuple of (form component, updated state)
    """
    from dash import ctx
    from data.persistence import load_app_settings
    from ui.project_config_form import create_project_config_form
    from ui.issue_type_config_form import create_issue_type_config_form
    from ui.status_config_form import create_status_config_form
    from ui.environment_config_form import create_environment_config_form

    # Check what triggered this callback
    triggered_id = ctx.triggered_id if ctx.triggered else None

    # Debug logging
    logger.info(
        f"[FieldMapping] render_tab_content: tab={active_tab}, is_open={is_open}, "
        f"has_metadata={bool(metadata and metadata.get('fields'))}, "
        f"field_count={len(metadata.get('fields', [])) if metadata else 0}, "
        f"collected_values={bool(collected_namespace_values)}, "
        f"fetched_values={list((fetched_field_values or {}).keys())}, "
        f"triggered_by={triggered_id}"
    )

    # If triggered by fetched-field-values-store and we're on Fields tab, don't re-render
    # This prevents losing namespace input values when field values are fetched
    if triggered_id == "fetched-field-values-store" and active_tab == "tab-fields":
        logger.info(
            "[FieldMapping] Skipping Fields tab re-render on fetched values change"
        )
        return no_update, no_update

    # Don't render if modal is closed (but allow initial empty state)
    if not is_open and callback_context.triggered:
        return html.Div(), no_update

    # Initialize state from saved settings on first open
    settings = load_app_settings()
    metadata = metadata or {}

    # Ensure state_data is a dict
    state_data = state_data or {}

    # Merge collected namespace values into state_data field_mappings
    # This preserves values when switching tabs
    # IMPORTANT: Do this BEFORE checking for empty state
    if collected_namespace_values:
        state_data = state_data.copy()  # Don't mutate original
        field_mappings = (
            state_data.get("field_mappings", {}).copy()
            if state_data.get("field_mappings")
            else {}
        )

        # collected_namespace_values format: {_trigger: "save"|"mode_switch", values: {metric: {field: value}}}
        # Extract actual values from the wrapper structure
        actual_values = collected_namespace_values.get("values", {})
        if not actual_values and "_trigger" not in collected_namespace_values:
            # Backward compatibility: old format was {metric: {field: value}} directly
            actual_values = collected_namespace_values

        logger.debug(
            f"[FieldMapping] collected_namespace_values type: {type(collected_namespace_values)}, keys: {list(collected_namespace_values.keys()) if isinstance(collected_namespace_values, dict) else 'NOT DICT'}"
        )
        logger.debug(
            f"[FieldMapping] actual_values type: {type(actual_values)}, content: {actual_values}"
        )

        for metric, fields in actual_values.items():
            # Skip non-dict entries (like _trigger key that may have leaked through)
            if not isinstance(fields, dict):
                logger.debug(
                    f"[FieldMapping] Skipping non-dict entry: {metric}={fields}"
                )
                continue
            if metric not in field_mappings:
                field_mappings[metric] = {}
            elif not isinstance(field_mappings[metric], dict):
                field_mappings[metric] = {}
            for field, value in fields.items():
                if value:  # Only update if there's a value
                    field_mappings[metric][field] = value
                    logger.debug(
                        f"[FieldMapping] Merged collected value: {metric}.{field} = {value}"
                    )

        state_data["field_mappings"] = field_mappings
        logger.info(
            f"[FieldMapping] Merged {len(collected_namespace_values)} metric groups from collected values"
        )

    # Check if state is empty or only contains profile tracking metadata and/or field_mappings
    # (state_data with only "_profile_id" and/or "field_mappings" keys should be re-initialized with other settings)
    essential_keys = {"_profile_id", "field_mappings"}
    is_partial_state = not state_data or set(state_data.keys()).issubset(essential_keys)

    # If state is partial, initialize other fields from saved settings
    # BUT preserve any field_mappings that were just merged from collected values
    if is_partial_state:
        # Preserve existing field_mappings from merge
        existing_field_mappings = state_data.get("field_mappings", {})

        # Helper to safely extract flow type mappings
        flow_mappings = settings.get("flow_type_mappings", {}) or {}

        def safe_get_flow_mapping(flow_type, key):
            """Safely extract flow mapping, handling None values."""
            flow_config = flow_mappings.get(flow_type, {})
            if flow_config is None:
                return []
            return flow_config.get(key, []) or []

        # Preserve profile ID if it exists
        profile_id = (state_data or {}).get("_profile_id")

        # Initialize state with saved settings
        state_data = {
            "_profile_id": profile_id,  # Track current profile for switch detection
            "field_mappings": settings.get("field_mappings", {}),
            "development_projects": settings.get("development_projects", []),
            "devops_projects": settings.get("devops_projects", []),
            "devops_task_types": settings.get("devops_task_types", []),
            "bug_types": settings.get("bug_types", []),
            "story_types": settings.get("story_types", []),
            "task_types": settings.get("task_types", []),
            "flow_feature_issue_types": safe_get_flow_mapping("Feature", "issue_types"),
            "flow_feature_effort_categories": safe_get_flow_mapping(
                "Feature", "effort_categories"
            ),
            "flow_defect_issue_types": safe_get_flow_mapping("Defect", "issue_types"),
            "flow_defect_effort_categories": safe_get_flow_mapping(
                "Defect", "effort_categories"
            ),
            "flow_technical_debt_issue_types": safe_get_flow_mapping(
                "Technical Debt", "issue_types"
            ),
            "flow_technical_debt_effort_categories": safe_get_flow_mapping(
                "Technical Debt", "effort_categories"
            ),
            "flow_risk_issue_types": safe_get_flow_mapping("Risk", "issue_types"),
            "flow_risk_effort_categories": safe_get_flow_mapping(
                "Risk", "effort_categories"
            ),
            "flow_end_statuses": settings.get("flow_end_statuses", []),
            "active_statuses": settings.get("active_statuses", []),
            "flow_start_statuses": settings.get("flow_start_statuses", []),
            "wip_statuses": settings.get("wip_statuses", []),
            "production_environment_values": settings.get(
                "production_environment_values", []
            ),
        }

        # Merge in any field_mappings collected from namespace inputs
        # These take precedence over saved settings (user just typed them)
        if existing_field_mappings:
            if "field_mappings" not in state_data:
                state_data["field_mappings"] = {}
            for metric, fields in existing_field_mappings.items():
                if isinstance(fields, dict):
                    if metric not in state_data["field_mappings"]:
                        state_data["field_mappings"][metric] = {}
                    for field, value in fields.items():
                        if value:  # Only merge non-empty values
                            state_data["field_mappings"][metric][field] = value

        logger.info("[FieldMapping] Initialized state store from saved settings")

    # Use state data for rendering (preserves user changes across tabs)
    display_settings = state_data.copy()

    # Render content based on active tab
    if active_tab == "tab-fields":
        try:
            # Use cached fields from metadata store
            cached_fields = metadata.get("fields", [])

            # Transform cached metadata to expected format
            available_fields = []
            for field in cached_fields:
                available_fields.append(
                    {
                        "field_id": field.get("id", ""),
                        "field_name": field.get("name", ""),
                        "field_type": field.get("type", "string"),
                        "is_custom": field.get("custom", False),
                    }
                )

            # If no cached fields, fetch them (first time only)
            if not available_fields:
                logger.warning(
                    "[FieldMapping] No cached fields found, fetching from JIRA..."
                )
                available_fields = fetch_available_jira_fields()

            current_mappings = {
                "field_mappings": display_settings.get("field_mappings", {})
            }
            return create_field_mapping_form(
                available_fields, current_mappings
            ), state_data
        except Exception as e:
            logger.error(f"[FieldMapping] Error loading field mappings: {e}")
            return create_field_mapping_error_alert(str(e)), state_data

    elif active_tab == "tab-projects":
        return create_project_config_form(
            development_projects=display_settings.get("development_projects", []),
            devops_projects=display_settings.get("devops_projects", []),
            available_projects=metadata.get("projects", []),
        ), state_data

    elif active_tab == "tab-types":
        # Build flow_type_mappings from state
        flow_type_mappings = {
            "Feature": {
                "issue_types": display_settings.get("flow_feature_issue_types", []),
                "effort_categories": display_settings.get(
                    "flow_feature_effort_categories", []
                ),
            },
            "Defect": {
                "issue_types": display_settings.get("flow_defect_issue_types", []),
                "effort_categories": display_settings.get(
                    "flow_defect_effort_categories", []
                ),
            },
            "Technical Debt": {
                "issue_types": display_settings.get(
                    "flow_technical_debt_issue_types", []
                ),
                "effort_categories": display_settings.get(
                    "flow_technical_debt_effort_categories", []
                ),
            },
            "Risk": {
                "issue_types": display_settings.get("flow_risk_issue_types", []),
                "effort_categories": display_settings.get(
                    "flow_risk_effort_categories", []
                ),
            },
        }

        # Get effort category options
        # Priority 1: Use dynamically fetched values (from field_value_fetch callback)
        # Priority 2: Use metadata field_options (from modal open)
        available_effort_categories = []

        # Check fetched_field_values first (dynamic fetch when field changes)
        if fetched_field_values and fetched_field_values.get("effort_category"):
            available_effort_categories = fetched_field_values["effort_category"].get(
                "values", []
            )
            logger.info(
                f"[FieldMapping] Using {len(available_effort_categories)} dynamically fetched effort categories"
            )
        else:
            # Fallback to metadata field_options
            flow_field_mappings = settings.get("field_mappings", {}).get("flow", {})
            effort_category_field = flow_field_mappings.get("effort_category")
            if effort_category_field and metadata.get("field_options"):
                available_effort_categories = metadata.get("field_options", {}).get(
                    effort_category_field, []
                )
                logger.info(
                    f"[FieldMapping] Using {len(available_effort_categories)} effort categories from metadata"
                )

        available_issue_types_list = metadata.get("issue_types", [])
        logger.info(
            f"[FieldMapping] Rendering Types tab with {len(available_issue_types_list)} available issue types"
        )
        logger.info(
            f"[FieldMapping] Flow type mappings: Feature={len(flow_type_mappings.get('Feature', {}).get('issue_types', []))}, "
            f"Defect={len(flow_type_mappings.get('Defect', {}).get('issue_types', []))}, "
            f"TechnicalDebt={len(flow_type_mappings.get('Technical Debt', {}).get('issue_types', []))}, "
            f"Risk={len(flow_type_mappings.get('Risk', {}).get('issue_types', []))}"
        )

        return create_issue_type_config_form(
            devops_task_types=display_settings.get("devops_task_types", []),
            bug_types=display_settings.get("bug_types", []),
            story_types=display_settings.get("story_types", []),
            task_types=display_settings.get("task_types", []),
            available_issue_types=available_issue_types_list,
            flow_type_mappings=flow_type_mappings,
            available_effort_categories=available_effort_categories,
        ), state_data

    elif active_tab == "tab-status":
        return create_status_config_form(
            flow_end_statuses=display_settings.get("flow_end_statuses", []),
            active_statuses=display_settings.get("active_statuses", []),
            flow_start_statuses=display_settings.get("flow_start_statuses", []),
            wip_statuses=display_settings.get("wip_statuses", []),
            available_statuses=metadata.get("statuses", []),
        ), state_data

    elif active_tab == "tab-environment":
        # Get production environment field value options from affected_environment field
        # This is the field used for incident tracking and MTTR calculation
        # Note: field_mappings are nested under 'dora' and 'flow' categories
        dora_mappings = settings.get("field_mappings", {}).get("dora", {})
        affected_env_field = dora_mappings.get("affected_environment")

        available_env_values = []
        metadata_env_values = []
        fetched_env_values = []

        # Priority 1: Use field options from metadata (if field was already mapped when modal opened)
        if affected_env_field and metadata.get("field_options"):
            metadata_env_values = metadata.get("field_options", {}).get(
                affected_env_field, []
            )
            logger.debug(
                f"[FieldMapping] Loaded {len(metadata_env_values)} values from metadata.field_options[{affected_env_field}]"
            )

        # Priority 1b: Use fetched field values from store (auto-fetched when field mapping changed)
        if fetched_field_values and fetched_field_values.get("affected_environment"):
            fetched_env_values = fetched_field_values["affected_environment"].get(
                "values", []
            )
            logger.debug(
                f"[FieldMapping] Loaded {len(fetched_env_values)} values from fetched-field-values-store"
            )

        # Combine metadata and fetched values
        available_env_values = list(set(metadata_env_values + fetched_env_values))

        # Priority 2: Use field_values from state (populated by auto-configure from issue analysis)
        if not available_env_values:
            field_values = (state_data or {}).get("field_values", {})
            if field_values and "target_environment" in field_values:
                available_env_values = field_values["target_environment"]
                # Limit to first 50 values to prevent browser performance issues
                if len(available_env_values) > 50:
                    logger.warning(
                        f"[FieldMapping] Truncating environment values from {len(available_env_values)} to 50"
                    )
                    available_env_values = available_env_values[:50]
                logger.debug(
                    f"[FieldMapping] Loaded {len(available_env_values)} values from state_data.field_values.target_environment"
                )

        # Priority 3: Use auto-detected production identifiers from metadata as options
        # (at minimum, show these so user can select from them)
        if not available_env_values:
            auto_detected = (metadata or {}).get("auto_detected", {})
            prod_identifiers = auto_detected.get("production_identifiers", [])
            if prod_identifiers:
                available_env_values = prod_identifiers
                logger.debug(
                    f"[FieldMapping] Using {len(available_env_values)} auto-detected production identifiers as options"
                )

        return create_environment_config_form(
            production_environment_values=display_settings.get(
                "production_environment_values", []
            ),
            available_environment_values=available_env_values,
        ), state_data

    return html.Div("Select a tab to configure mappings."), state_data


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
    """
    Manage modal loading state based on app-level metadata store.

    Shows loading overlay while metadata is being fetched (metadata is None),
    disables buttons until metadata is available, and shows appropriate
    status messages.

    Args:
        is_open: Whether modal is open
        metadata: App-level JIRA metadata (None while loading, dict when loaded)

    Returns:
        Tuple of (status_alert, auto_configure_disabled, save_disabled, validate_disabled, overlay_style)
    """
    # Style for showing/hiding the loading overlay
    # Note: Use visibility instead of display because Bootstrap's d-flex class has !important
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
        f"{len(projects)} projects, {len(issue_types)} issue types, {len(statuses)} statuses"
    )

    # Show brief success toast notification
    toast = create_success_toast(
        f"{len(fields)} fields, {len(projects)} projects, "
        f"{len(issue_types)} issue types available.",
        header="Metadata Ready",
    )

    return (
        "",  # Clear inline status
        False,  # Enable auto-configure
        False,  # Enable save
        False,  # Enable validate
        overlay_hidden,  # Hide loading overlay
        toast,
    )


# ============================================================================
# AUTO-CONFIGURE WARNING BANNER TOGGLE
# ============================================================================


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


# ============================================================================
# AUTO-CONFIGURE FROM METADATA
# ============================================================================


@callback(
    [
        Output("field-mapping-state-store", "data", allow_duplicate=True),
        Output("field-mapping-status", "children", allow_duplicate=True),
        Output("auto-configure-warning-banner", "is_open", allow_duplicate=True),
        Output("auto-configure-refresh-trigger", "data"),  # Trigger tab re-render
        Output("auto-configure-confirm-button", "disabled"),
        Output("auto-configure-confirm-button", "children"),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("auto-configure-confirm-button", "n_clicks"),
    [
        State("jira-metadata-store", "data"),
        State("field-mapping-state-store", "data"),
        State(
            "auto-configure-refresh-trigger", "data"
        ),  # Get current value to increment
    ],
    prevent_initial_call=True,
    running=[
        (Output("auto-configure-confirm-button", "disabled"), True, False),
        (
            Output("auto-configure-confirm-button", "children"),
            [dbc.Spinner(size="sm", spinner_class_name="me-2"), "Configuring..."],
            [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
        ),
    ],
)
def auto_configure_from_metadata(
    n_clicks: int, metadata: Dict, current_state: Dict, current_trigger: int
):
    """Auto-configure profile settings from JIRA metadata.

    Generates smart defaults for all configuration sections:
    - Project classification (completion/active/WIP statuses)
    - Flow type mappings (Feature/Defect/TechnicalDebt/Risk)
    - Development projects (extracted from JQL query)

    Args:
        n_clicks: Number of times auto-configure button clicked
        metadata: JIRA metadata from jira-metadata-store
        current_state: Current state from state store

    Returns:
        Tuple of (updated_state, status_alert, banner_closed)
    """
    from data.auto_configure import generate_smart_defaults
    from data.profile_manager import get_active_profile, get_profile_file_path
    import json

    if not n_clicks:
        return (
            no_update,
            no_update,
            no_update,
            no_update,  # Don't trigger refresh
            no_update,  # Button disabled state
            no_update,  # Button children
            no_update,  # Toast notification
        )

    try:
        # Validate metadata is available
        if not metadata or metadata.get("error"):
            return (
                no_update,
                "",  # Clear inline status
                False,  # Close confirmation modal
                no_update,  # Don't trigger refresh on error
                False,  # Re-enable button
                [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
                create_error_toast(
                    "JIRA metadata not available. Please ensure JIRA is connected.",
                    header="Cannot Auto-Configure",
                ),
            )

        # Get active profile to extract JQL query
        active_profile = get_active_profile()
        if not active_profile:
            return (
                no_update,
                "",  # Clear inline status
                False,  # Close confirmation modal
                no_update,  # Don't trigger refresh on error
                False,  # Re-enable button
                [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
                create_error_toast(
                    "No active profile found.",
                    header="Cannot Auto-Configure",
                ),
            )

        profile_id = active_profile.id
        profile_path = get_profile_file_path(profile_id)

        # Load current profile to get active query JQL
        jql_query = None
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

                # Get active query ID from profile
                active_query_id = profile_data.get("active_query_id")

                # Fallback: If no active query, check if there are any queries
                if not active_query_id:
                    queries = profile_data.get("queries", [])
                    if queries and len(queries) > 0:
                        active_query_id = (
                            queries[0].get("id")
                            if isinstance(queries[0], dict)
                            else queries[0]
                        )
                        logger.info(
                            f"[AutoConfigure] No active query, using first query: {active_query_id}"
                        )
                    else:
                        # Last resort: Check for query directories
                        from pathlib import Path

                        queries_dir = Path(profile_path).parent / "queries"
                        if queries_dir.exists():
                            query_dirs = [
                                d for d in queries_dir.iterdir() if d.is_dir()
                            ]
                            if query_dirs:
                                active_query_id = query_dirs[0].name
                                logger.info(
                                    f"[AutoConfigure] Found query directory: {active_query_id}"
                                )

                if active_query_id:
                    # Load query file to get JQL
                    from data.profile_manager import get_query_file_path

                    query_path = get_query_file_path(profile_id, active_query_id)

                    try:
                        with open(query_path, "r", encoding="utf-8") as qf:
                            query_data = json.load(qf)
                            jql_query = query_data.get("jql", "")
                            logger.info(
                                f"[AutoConfigure] Loaded JQL query from active query: {jql_query}"
                            )
                    except Exception as qe:
                        logger.warning(f"Could not load query file: {qe}")
                else:
                    logger.warning(
                        "No active query ID found in profile and no fallback queries available"
                    )
        except Exception as e:
            logger.warning(f"Could not load profile data: {e}")

        logger.info(
            f"[AutoConfigure] Generating smart defaults for profile {profile_id}"
        )

        # Fetch recent issues for field detection (last 100 issues)
        issues = []
        if jql_query:
            try:
                from data.jira_simple import fetch_jira_issues

                logger.info(
                    "[AutoConfigure] Fetching last 100 issues for field analysis..."
                )
                # Modify JQL to get last 100 issues ordered by created date
                sample_jql = f"{jql_query} ORDER BY created DESC"

                # Get JIRA config from profile
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                    jira_config = profile_data.get("jira_config", {})

                # Build config dict for fetch_jira_issues (matches expected structure)
                fetch_config = {
                    "jql_query": sample_jql,
                    "api_endpoint": jira_config.get("base_url", "").rstrip("/")
                    + "/rest/api/2/search",
                    "token": jira_config.get("token", ""),
                    "story_points_field": jira_config.get("points_field", ""),
                    "field_mappings": {},  # Empty for field detection - we want ALL fields
                    "fields": "*all",  # CRITICAL: Request ALL fields including custom fields
                }

                # Fetch issues
                success, fetched_issues = fetch_jira_issues(
                    config=fetch_config, max_results=100
                )

                if success:
                    issues = fetched_issues
                    logger.info(
                        f"[AutoConfigure] Fetched {len(issues)} issues for analysis"
                    )
                else:
                    logger.warning(
                        "[AutoConfigure] Failed to fetch issues for field detection"
                    )

            except Exception as e:
                logger.warning(
                    f"[AutoConfigure] Could not fetch issues for field detection: {e}",
                    exc_info=True,
                )

        # Generate smart defaults using metadata and issues
        defaults = generate_smart_defaults(metadata, jql_query, issues)

        # Update state store with auto-configured values
        new_state = current_state.copy() if current_state else {}

        # CRITICAL: Store values in FLAT keys that the UI dropdowns read from
        # The render_tab_content callback reads from these flat keys to populate dropdowns
        new_state["flow_end_statuses"] = defaults["project_classification"][
            "flow_end_statuses"
        ]
        new_state["active_statuses"] = defaults["project_classification"][
            "active_statuses"
        ]
        new_state["flow_start_statuses"] = defaults["project_classification"][
            "flow_start_statuses"
        ]
        new_state["wip_statuses"] = defaults["project_classification"]["wip_statuses"]
        new_state["development_projects"] = defaults["project_classification"][
            "development_projects"
        ]
        new_state["devops_projects"] = defaults["project_classification"].get(
            "devops_projects", []
        )

        # Flow type mappings - store in flat keys for UI
        new_state["flow_feature_issue_types"] = defaults["flow_type_mappings"][
            "Feature"
        ]
        new_state["flow_defect_issue_types"] = defaults["flow_type_mappings"]["Defect"]
        new_state["flow_technical_debt_issue_types"] = defaults[
            "flow_type_mappings"
        ].get("Technical Debt", [])
        new_state["flow_risk_issue_types"] = defaults["flow_type_mappings"].get(
            "Risk", []
        )

        # Bug types - store in flat key for UI (Incident Types dropdown)
        if (
            "project_classification" in defaults
            and "bug_types" in defaults["project_classification"]
        ):
            new_state["bug_types"] = defaults["project_classification"]["bug_types"]
            logger.info(
                f"[AutoConfigure] Stored {len(new_state['bug_types'])} incident types for UI"
            )

        # DevOps task types - store in flat key for UI (DevOps Task Types dropdown)
        if (
            "project_classification" in defaults
            and "devops_task_types" in defaults["project_classification"]
        ):
            new_state["devops_task_types"] = defaults["project_classification"][
                "devops_task_types"
            ]
            logger.info(
                f"[AutoConfigure] Stored {len(new_state['devops_task_types'])} DevOps task types for UI"
            )

        # Field mappings - store if detected (DORA + Flow only)
        if "field_mappings" in defaults:
            new_state["field_mappings"] = defaults["field_mappings"]

        # Points field - store separately for jira_config (NOT in field_mappings)
        if "points_field" in defaults:
            new_state["points_field"] = defaults["points_field"]

        # Field values - store for dropdown population
        if "field_values" in defaults:
            new_state["field_values"] = defaults["field_values"]

        # ALSO store in nested structure for profile.json compatibility
        if "project_classification" not in new_state:
            new_state["project_classification"] = {}
        new_state["project_classification"].update(defaults["project_classification"])

        # Populate production_environment_values from auto-detected production identifiers
        # These are values matching patterns like "prod", "production", "live", "prd"
        auto_detected_prod = (
            metadata.get("auto_detected", {}).get("production_identifiers", [])
            if metadata
            else []
        )
        if auto_detected_prod:
            # Use auto-detected production identifiers for pre-selection
            new_state["project_classification"]["production_environment_values"] = (
                auto_detected_prod
            )
            new_state["production_environment_values"] = auto_detected_prod
            logger.info(
                f"[AutoConfigure] Pre-selected {len(auto_detected_prod)} auto-detected production identifiers: {auto_detected_prod}"
            )
        elif (
            "field_values" in defaults
            and "target_environment" in defaults["field_values"]
        ):
            # Fallback: If no auto-detected values, don't pre-select anything
            # The dropdown will show all available values for manual selection
            logger.info(
                f"[AutoConfigure] No auto-detected production identifiers found. "
                f"Available environment values: {len(defaults['field_values']['target_environment'])}"
            )

        if "flow_type_mappings" not in new_state:
            new_state["flow_type_mappings"] = {}
        for flow_type, issue_types in defaults["flow_type_mappings"].items():
            if flow_type not in new_state["flow_type_mappings"]:
                new_state["flow_type_mappings"][flow_type] = {
                    "issue_types": [],
                    "effort_categories": [],
                }
            new_state["flow_type_mappings"][flow_type]["issue_types"] = issue_types

            # Populate effort_categories from field_values if available
            if (
                "field_values" in defaults
                and "effort_category" in defaults["field_values"]
            ):
                new_state["flow_type_mappings"][flow_type]["effort_categories"] = (
                    defaults["field_values"]["effort_category"]
                )
                logger.info(
                    f"[AutoConfigure] Populated {len(defaults['field_values']['effort_category'])} effort categories for {flow_type}"
                )

        # Count what was configured
        completion_count = len(defaults["project_classification"]["flow_end_statuses"])
        active_count = len(defaults["project_classification"]["active_statuses"])
        wip_count = len(defaults["project_classification"]["wip_statuses"])
        feature_count = len(defaults["flow_type_mappings"]["Feature"])
        defect_count = len(defaults["flow_type_mappings"]["Defect"])
        project_count = len(defaults["project_classification"]["development_projects"])

        logger.info(
            f"[AutoConfigure] Generated defaults: {completion_count} completion, "
            f"{active_count} active, {wip_count} WIP statuses, "
            f"{feature_count} features, {defect_count} defects, {project_count} projects"
        )

        # Create success toast notification
        total_statuses = completion_count + active_count + wip_count
        total_types = feature_count + defect_count
        toast = create_success_toast(
            f"{total_statuses} statuses, {total_types} work types, "
            f"{project_count} project{'s' if project_count != 1 else ''}. "
            "Click 'Save Mappings' to apply.",
            header="Auto-Configuration Complete",
            duration=5000,
        )

        # Increment refresh trigger to force tab re-render with new state
        new_trigger = (current_trigger or 0) + 1
        return (
            new_state,
            "",  # Clear inline status
            False,
            new_trigger,
            False,  # Re-enable button
            [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
            toast,
        )  # Close modal, trigger refresh

    except Exception as e:
        logger.error(
            f"[AutoConfigure] Error during auto-configuration: {e}", exc_info=True
        )
        return (
            no_update,
            "",  # Clear inline status
            False,
            no_update,
            False,  # Re-enable button
            [html.I(className="fas fa-check me-2"), "Yes, Auto-Configure Now"],
            create_error_toast(f"Error: {str(e)}", header="Auto-Configuration Failed"),
        )  # Close modal, don't trigger refresh


# ============================================================================
# VALIDATE AND SAVE MAPPINGS
# ============================================================================


def _validate_all_tabs(state_data: Dict, field_validation_errors: list) -> Dict:
    """Validate all configuration tabs comprehensively.

    Args:
        state_data: Current form state from state store
        field_validation_errors: Validation errors from Fields tab (namespace inputs)

    Returns:
        Dict with validation results:
        {
            "is_valid": bool,
            "errors": [{"tab": str, "field": str, "error": str}, ...],
            "warnings": [{"tab": str, "field": str, "warning": str}, ...],
            "summary": {"fields": int, "statuses": int, "projects": int, "issue_types": int}
        }
    """
    errors = []
    warnings = []
    summary = {"fields": 0, "statuses": 0, "projects": 0, "issue_types": 0}

    state_data = state_data or {}

    # =========================================================================
    # 1. FIELDS TAB VALIDATION (from clientside namespace validation)
    # =========================================================================
    if field_validation_errors:
        for err in field_validation_errors:
            errors.append(
                {
                    "tab": "Fields",
                    "field": f"{err.get('metric', '').upper()} > {err.get('field', '').replace('_', ' ').title()}",
                    "error": err.get("error", "Invalid value"),
                }
            )

    # Count configured fields (from namespace values in field_mappings)
    field_mappings = state_data.get("field_mappings", {})
    for metric in ["dora", "flow"]:
        if metric in field_mappings:
            summary["fields"] += len([v for v in field_mappings[metric].values() if v])

    # =========================================================================
    # 2. STATUS TAB VALIDATION
    # =========================================================================
    # Get status values (check both flat and nested structure)
    flow_end_statuses = state_data.get("flow_end_statuses", [])
    if not flow_end_statuses and "project_classification" in state_data:
        flow_end_statuses = state_data["project_classification"].get(
            "flow_end_statuses", []
        )

    active_statuses = state_data.get("active_statuses", [])
    if not active_statuses and "project_classification" in state_data:
        active_statuses = state_data["project_classification"].get(
            "active_statuses", []
        )

    wip_statuses = state_data.get("wip_statuses", [])
    if not wip_statuses and "project_classification" in state_data:
        wip_statuses = state_data["project_classification"].get("wip_statuses", [])

    flow_start_statuses = state_data.get("flow_start_statuses", [])
    if not flow_start_statuses and "project_classification" in state_data:
        flow_start_statuses = state_data["project_classification"].get(
            "flow_start_statuses", []
        )

    # Count total statuses
    summary["statuses"] = (
        len(flow_end_statuses)
        + len(active_statuses)
        + len(wip_statuses)
        + len(flow_start_statuses)
    )

    # Validate: Completion statuses required
    if not flow_end_statuses:
        warnings.append(
            {
                "tab": "Status",
                "field": "Completion Statuses",
                "warning": "No completion statuses selected. Required for metrics calculation.",
            }
        )

    # Validate: WIP statuses required
    if not wip_statuses:
        warnings.append(
            {
                "tab": "Status",
                "field": "WIP Statuses",
                "warning": "No WIP statuses selected. Required for flow metrics.",
            }
        )

    # Validate: Active statuses should be subset of WIP
    if active_statuses and wip_statuses:
        wip_set = set(wip_statuses)
        active_not_in_wip = [s for s in active_statuses if s not in wip_set]
        if active_not_in_wip:
            warnings.append(
                {
                    "tab": "Status",
                    "field": "Active Statuses",
                    "warning": f"Active statuses not in WIP: {', '.join(active_not_in_wip[:3])}{'...' if len(active_not_in_wip) > 3 else ''}",
                }
            )

    # Validate: Flow Start statuses should be subset of WIP
    if flow_start_statuses and wip_statuses:
        wip_set = set(wip_statuses)
        flow_start_not_in_wip = [s for s in flow_start_statuses if s not in wip_set]
        if flow_start_not_in_wip:
            warnings.append(
                {
                    "tab": "Status",
                    "field": "Flow Start Statuses",
                    "warning": f"Flow Start statuses not in WIP: {', '.join(flow_start_not_in_wip[:3])}{'...' if len(flow_start_not_in_wip) > 3 else ''}",
                }
            )

    # =========================================================================
    # 3. PROJECT TAB VALIDATION
    # =========================================================================
    dev_projects = state_data.get("development_projects", [])
    if not dev_projects and "project_classification" in state_data:
        dev_projects = state_data["project_classification"].get(
            "development_projects", []
        )

    devops_projects = state_data.get("devops_projects", [])
    if not devops_projects and "project_classification" in state_data:
        devops_projects = state_data["project_classification"].get(
            "devops_projects", []
        )

    summary["projects"] = len(dev_projects) + len(devops_projects)

    # Validate: At least one project type should be selected
    if not dev_projects and not devops_projects:
        warnings.append(
            {
                "tab": "Projects",
                "field": "Project Selection",
                "warning": "No projects selected. Select Development or DevOps projects.",
            }
        )

    # =========================================================================
    # 4. ISSUE TYPE TAB VALIDATION
    # =========================================================================
    flow_type_mappings = state_data.get("flow_type_mappings", {})

    # Also check flat keys for backward compatibility
    feature_types = state_data.get("flow_feature_issue_types", [])
    if not feature_types and "Feature" in flow_type_mappings:
        feature_mapping = flow_type_mappings["Feature"]
        feature_types = (
            feature_mapping.get("issue_types", [])
            if isinstance(feature_mapping, dict)
            else feature_mapping
        )

    defect_types = state_data.get("flow_defect_issue_types", [])
    if not defect_types and "Defect" in flow_type_mappings:
        defect_mapping = flow_type_mappings["Defect"]
        defect_types = (
            defect_mapping.get("issue_types", [])
            if isinstance(defect_mapping, dict)
            else defect_mapping
        )

    tech_debt_types = state_data.get("flow_technical_debt_issue_types", [])
    if not tech_debt_types and "Technical Debt" in flow_type_mappings:
        td_mapping = flow_type_mappings["Technical Debt"]
        tech_debt_types = (
            td_mapping.get("issue_types", [])
            if isinstance(td_mapping, dict)
            else td_mapping
        )

    risk_types = state_data.get("flow_risk_issue_types", [])
    if not risk_types and "Risk" in flow_type_mappings:
        risk_mapping = flow_type_mappings["Risk"]
        risk_types = (
            risk_mapping.get("issue_types", [])
            if isinstance(risk_mapping, dict)
            else risk_mapping
        )

    summary["issue_types"] = (
        len(feature_types) + len(defect_types) + len(tech_debt_types) + len(risk_types)
    )

    # Validate: At least Feature or Defect should have mappings
    if not feature_types and not defect_types:
        warnings.append(
            {
                "tab": "Issue Types",
                "field": "Flow Type Mappings",
                "warning": "No Feature or Defect types mapped. Required for Flow Distribution.",
            }
        )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def _build_comprehensive_validation_alert(validation_result: Dict):
    """Build comprehensive validation alert showing all tabs' results."""
    errors = validation_result.get("errors", [])
    warnings = validation_result.get("warnings", [])
    summary = validation_result.get("summary", {})
    is_valid = validation_result.get("is_valid", True)

    # Build summary line
    summary_parts = []
    if summary.get("fields", 0) > 0:
        summary_parts.append(f"{summary['fields']} field(s)")
    if summary.get("statuses", 0) > 0:
        summary_parts.append(f"{summary['statuses']} status(es)")
    if summary.get("projects", 0) > 0:
        summary_parts.append(f"{summary['projects']} project(s)")
    if summary.get("issue_types", 0) > 0:
        summary_parts.append(f"{summary['issue_types']} issue type(s)")

    summary_text = ", ".join(summary_parts) if summary_parts else "No configuration"

    # Build error list
    error_items = []
    for err in errors:
        error_items.append(
            html.Li(
                [
                    html.Strong(f"{err['tab']} > {err['field']}: "),
                    html.Span(err["error"]),  # No text-danger - inherits alert color
                ],
                className="mb-1",
            )
        )

    # Build warning list
    warning_items = []
    for warn in warnings:
        warning_items.append(
            html.Li(
                [
                    html.Strong(f"{warn['tab']} > {warn['field']}: "),
                    html.Span(warn["warning"]),
                ],
                className="mb-1",
            )
        )

    # Determine alert color and icon
    if errors:
        color = "danger"
        icon = "fas fa-times-circle"
        title = f"Validation Failed - {len(errors)} error(s)"
    elif warnings:
        color = "warning"
        icon = "fas fa-exclamation-triangle"
        title = f"Validation Passed with {len(warnings)} warning(s)"
    else:
        color = "success"
        icon = "fas fa-check-circle"
        title = "Validation Passed"

    # Build alert content with improved layout - wrap in single div to prevent column layout
    content_parts = [
        # Header with icon and title
        html.Div(
            [
                html.I(className=f"{icon} me-2"),
                html.Strong(title),
            ],
            className="d-flex align-items-center mb-2",
        ),
        # Summary line
        html.Div(
            f"Configured: {summary_text}",
            className="mb-2",
            style={"fontSize": "0.9rem"},
        ),
    ]

    # Add errors section if present
    if error_items:
        content_parts.append(
            html.Div(
                [
                    html.Strong("Errors:", className="text-danger d-block mb-1"),
                    html.Ul(error_items, className="mb-2 ps-3"),
                ],
                className="mt-2",
            )
        )

    # Add warnings section if present
    if warning_items:
        content_parts.append(
            html.Div(
                [
                    html.Strong("Warnings:", className="text-warning d-block mb-1"),
                    html.Ul(warning_items, className="mb-0 ps-3"),
                ],
                className="mt-2",
            )
        )

    # Add success message at the bottom
    if is_valid and not warnings:
        content_parts.append(
            html.Div(
                "Click 'Save Mappings' to persist your changes.",
                className="mt-2",
                style={"fontSize": "0.85rem", "opacity": "0.85"},
            )
        )

    # Wrap all content in a single container div to ensure vertical stacking
    return dbc.Alert(
        html.Div(content_parts),
        color=color,
        dismissable=True,
        id="validation-result-alert",
    )


def _build_validation_error_alert(validation_errors):
    """Build validation error alert for display in modal."""
    error_items = []
    for err in validation_errors:
        metric_label = err.get("metric", "unknown").upper()
        field_label = err.get("field", "unknown").replace("_", " ").title()
        error_msg = err.get("error", "Invalid value")
        error_items.append(
            html.Li(
                [
                    html.Strong(f"{metric_label} > {field_label}: "),
                    html.Span(error_msg),
                ]
            )
        )

    return dbc.Alert(
        html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-times-circle me-2"),
                        html.Strong(
                            f"Validation Failed - {len(validation_errors)} error(s) found"
                        ),
                    ],
                    className="d-flex align-items-center mb-2",
                ),
                html.Ul(error_items, className="mb-2 ps-4"),
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1"),
                        "Fix the errors above before saving. Use autocomplete to select valid values.",
                    ],
                    className="text-muted",
                ),
            ]
        ),
        color="danger",
        dismissable=True,
    )


def _build_validation_success_alert(total_fields):
    """Build validation success alert for display in modal."""
    return dbc.Alert(
        html.Div(
            [
                html.I(className="fas fa-check-circle me-2"),
                html.Span(
                    [
                        html.Strong("Validation Passed!"),
                        html.Br(),
                        html.Small(
                            f"All {total_fields} configured field(s) are valid. "
                            "Click 'Save Mappings' to persist your changes.",
                            style={"opacity": "0.85"},
                        ),
                    ]
                ),
            ],
            className="d-flex align-items-start",
        ),
        color="success",
        dismissable=True,
    )


def _build_no_fields_alert():
    """Build info alert when no fields are configured."""
    return dbc.Alert(
        html.Div(
            [
                html.I(className="fas fa-info-circle me-2 text-info"),
                html.Span(
                    [
                        html.Strong("No Field Mappings Configured"),
                        html.Br(),
                        html.Small(
                            "Configure field mappings in the 'Fields' tab to enable "
                            "DORA and Flow metrics calculation.",
                            style={"opacity": "0.85"},
                        ),
                    ]
                ),
            ],
            className="d-flex align-items-start",
        ),
        color="info",
        dismissable=True,
    )


@callback(
    [
        Output("field-mapping-save-success", "data", allow_duplicate=True),
        Output("field-mapping-status", "children", allow_duplicate=True),
        Output("field-mapping-state-store", "data", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("namespace-collected-values", "data"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def save_or_validate_mappings(namespace_values, state_data):
    """Save, validate, or update state from collected namespace values.

    This callback handles "save", "validate", and "tab_switch" triggers from the
    clientside collectNamespaceValues function. The trigger type determines
    the action:

    - trigger="validate": Validates and shows results in modal (no save)
    - trigger="save": Validates, then saves if valid
    - trigger="tab_switch": Updates state store with collected values (preserves them)

    Values are collected by a clientside callback (collectNamespaceValues)
    that reads directly from the DOM and stores them in namespace-collected-values.

    Args:
        namespace_values: Collected values with trigger info from clientside callback
        state_data: Current form state from state store

    Returns:
        Tuple of (save_success, status_message, updated_state, toast_notification)
    """
    from data.persistence import save_app_settings, load_app_settings

    # namespace_values has structure: {trigger: "save"|"validate"|"tab_switch", values: {...}, validationErrors: [...]}
    if not namespace_values or not isinstance(namespace_values, dict):
        return no_update, no_update, no_update, no_update

    trigger = namespace_values.get("trigger", "")
    collected_values = namespace_values.get("values", {})
    validation_errors = namespace_values.get("validationErrors", [])

    # Handle TAB_SWITCH trigger - just update state store with collected values
    if trigger == "tab_switch":
        if not collected_values:
            return no_update, no_update, no_update, no_update

        # Merge collected namespace values into state_data
        state_data = (state_data or {}).copy()
        if "field_mappings" not in state_data:
            state_data["field_mappings"] = {}

        for metric, fields in collected_values.items():
            if not isinstance(fields, dict):
                continue
            if metric not in state_data["field_mappings"]:
                state_data["field_mappings"][metric] = {}
            for field, value in fields.items():
                if value and str(value).strip():
                    state_data["field_mappings"][metric][field] = str(value).strip()

        logger.info(
            f"[FieldMapping] Tab switch - saved {len(collected_values)} metric groups to state"
        )
        return no_update, no_update, state_data, no_update

    # Handle VALIDATE trigger - comprehensive validation across all tabs
    if trigger == "validate":
        # Merge collected field values into state for comprehensive validation
        state_with_fields = (state_data or {}).copy()
        if collected_values:
            if "field_mappings" not in state_with_fields:
                state_with_fields["field_mappings"] = {}
            for metric, fields in collected_values.items():
                if metric not in state_with_fields["field_mappings"]:
                    state_with_fields["field_mappings"][metric] = {}
                for field, value in fields.items():
                    if value:
                        state_with_fields["field_mappings"][metric][field] = value

        # Run comprehensive validation across all tabs
        validation_result = _validate_all_tabs(state_with_fields, validation_errors)

        logger.info(
            f"[FieldMapping] Comprehensive validation: "
            f"valid={validation_result['is_valid']}, "
            f"errors={len(validation_result['errors'])}, "
            f"warnings={len(validation_result['warnings'])}, "
            f"summary={validation_result['summary']}"
        )

        return (
            no_update,
            _build_comprehensive_validation_alert(validation_result),
            no_update,
            no_update,  # Validation uses inline alert (keeps validation in modal)
        )

    # Handle SAVE trigger
    if trigger != "save":
        # Unknown trigger - ignore
        logger.info(
            f"[FieldMapping] Unknown trigger detected, ignoring (trigger={trigger})"
        )
        return no_update, no_update, no_update, no_update

    # Check for validation errors - reject save if any invalid values
    if validation_errors:
        logger.warning(
            f"[FieldMapping] Save rejected due to validation errors: {validation_errors}"
        )
        return (
            False,
            _build_validation_error_alert(validation_errors),
            no_update,
            no_update,
        )

    try:
        # Load current settings
        settings = load_app_settings()

        # Use values collected by clientside callback from namespace inputs
        if collected_values and isinstance(collected_values, dict):
            logger.info(f"[FieldMapping] Saving namespace values: {collected_values}")
            # Build field_mappings from namespace input values
            state_data = state_data or {}
            if "field_mappings" not in state_data:
                state_data["field_mappings"] = {}

            # Merge collected namespace values into field_mappings
            for metric, fields in collected_values.items():
                if metric not in state_data["field_mappings"]:
                    state_data["field_mappings"][metric] = {}
                for field, value in fields.items():
                    if value and str(value).strip():
                        state_data["field_mappings"][metric][field] = str(value).strip()
                        logger.info(
                            f"[FieldMapping] Saved namespace value: {metric}.{field} = {value}"
                        )

        # Update settings from state store
        # Field mappings
        if "field_mappings" in state_data:
            # Store raw namespace strings WITHOUT parsing to SourceRule
            # Parsing should happen at metric calculation time, not save time
            # This ensures the UI can display the original namespace syntax
            raw_field_mappings = state_data["field_mappings"]
            settings["field_mappings"] = raw_field_mappings
            logger.info(
                f"[FieldMapping] Saved field mappings with {len(raw_field_mappings.get('dora', {}))} DORA "
                f"and {len(raw_field_mappings.get('flow', {}))} Flow fields"
            )
        else:
            logger.warning(
                "[FieldMapping] Field mappings not found in state - state may be empty"
            )

        # Read from nested project_classification structure (NEW format from auto-configure)
        if "project_classification" in state_data:
            proj_class = state_data["project_classification"]
            settings["development_projects"] = proj_class.get(
                "development_projects", []
            )
            settings["devops_projects"] = proj_class.get("devops_projects", [])
            settings["flow_end_statuses"] = proj_class.get("flow_end_statuses", [])
            settings["active_statuses"] = proj_class.get("active_statuses", [])
            settings["flow_start_statuses"] = proj_class.get("flow_start_statuses", [])
            settings["wip_statuses"] = proj_class.get("wip_statuses", [])

        # Read from nested flow_type_mappings structure (NEW format from auto-configure)
        if "flow_type_mappings" in state_data:
            settings["flow_type_mappings"] = state_data["flow_type_mappings"]

        # Fallback: Also check old flat keys for backward compatibility
        if "development_projects" in state_data:
            settings["development_projects"] = state_data["development_projects"]
        if "devops_projects" in state_data:
            settings["devops_projects"] = state_data["devops_projects"]
        if "flow_end_statuses" in state_data:
            settings["flow_end_statuses"] = state_data["flow_end_statuses"]
        if "active_statuses" in state_data:
            settings["active_statuses"] = state_data["active_statuses"]
        if "flow_start_statuses" in state_data:
            settings["flow_start_statuses"] = state_data["flow_start_statuses"]
        if "wip_statuses" in state_data:
            settings["wip_statuses"] = state_data["wip_statuses"]

        # Fallback: Old flow type keys (kept for backward compatibility with manual edits)
        if (
            "flow_feature_issue_types" in state_data
            or "flow_defect_issue_types" in state_data
        ):
            flow_type_mappings = {
                "Feature": {
                    "issue_types": state_data.get("flow_feature_issue_types", []),
                    "effort_categories": state_data.get(
                        "flow_feature_effort_categories", []
                    ),
                },
                "Defect": {
                    "issue_types": state_data.get("flow_defect_issue_types", []),
                    "effort_categories": state_data.get(
                        "flow_defect_effort_categories", []
                    ),
                },
                "Technical Debt": {
                    "issue_types": state_data.get(
                        "flow_technical_debt_issue_types", []
                    ),
                    "effort_categories": state_data.get(
                        "flow_technical_debt_effort_categories", []
                    ),
                },
                "Risk": {
                    "issue_types": state_data.get("flow_risk_issue_types", []),
                    "effort_categories": state_data.get(
                        "flow_risk_effort_categories", []
                    ),
                },
            }
            settings["flow_type_mappings"] = flow_type_mappings

        # Issue Types (old flat structure - kept for backward compatibility)
        if "devops_task_types" in state_data:
            settings["devops_task_types"] = state_data["devops_task_types"]
        if "bug_types" in state_data:
            settings["bug_types"] = state_data["bug_types"]
        if "story_types" in state_data:
            settings["story_types"] = state_data["story_types"]
        if "task_types" in state_data:
            settings["task_types"] = state_data["task_types"]

        # Environment
        if "production_environment_values" in state_data:
            settings["production_environment_values"] = state_data[
                "production_environment_values"
            ]

        # Points field - goes in jira_config, NOT field_mappings
        if "points_field" in state_data:
            if "jira_config" not in settings:
                settings["jira_config"] = {}
            settings["jira_config"]["points_field"] = state_data["points_field"]
            logger.info(
                f"[FieldMapping] Updated points_field in jira_config: {state_data['points_field']}"
            )

        # Save to disk - extract individual parameters from settings dict
        save_app_settings(
            pert_factor=settings.get("pert_factor", 1.2),
            deadline=settings.get("deadline"),
            data_points_count=settings.get("data_points_count"),
            show_milestone=settings.get("show_milestone"),
            milestone=settings.get("milestone"),
            show_points=settings.get("show_points"),
            jql_query=settings.get("jql_query"),
            last_used_data_source=settings.get("last_used_data_source"),
            active_jql_profile_id=settings.get("active_jql_profile_id"),
            jira_config=settings.get("jira_config"),
            field_mappings=settings.get("field_mappings"),
            development_projects=settings.get("development_projects"),
            devops_projects=settings.get("devops_projects"),
            devops_task_types=settings.get("devops_task_types"),
            bug_types=settings.get("bug_types"),
            story_types=settings.get("story_types"),
            task_types=settings.get("task_types"),
            production_environment_values=settings.get("production_environment_values"),
            flow_end_statuses=settings.get("flow_end_statuses"),
            active_statuses=settings.get("active_statuses"),
            flow_start_statuses=settings.get("flow_start_statuses"),
            wip_statuses=settings.get("wip_statuses"),
            flow_type_mappings=settings.get("flow_type_mappings"),
            cache_metadata=settings.get("cache_metadata"),
        )

        logger.info("[FieldMapping] Mappings saved successfully from state store")

        # Success toast notification
        toast = create_success_toast(
            "Your field mappings and configurations have been saved.",
            header="Configuration Saved",
        )

        # Keep state store intact so UI remains populated
        return True, "", no_update, toast

    except Exception as e:
        logger.error(f"[FieldMapping] Error saving mappings: {e}")
        toast = create_error_toast(
            f"Error saving mappings: {str(e)}",
            header="Save Failed",
        )
        return False, "", no_update, toast


@callback(
    [
        Output("field-mapping-state-store", "data", allow_duplicate=True),
        Output("jira-metadata-store", "data", allow_duplicate=True),
    ],
    Input("profile-selector", "value"),
    State("field-mapping-state-store", "data"),
    State("jira-metadata-store", "data"),
    prevent_initial_call=True,
)
def clear_field_mapping_state_on_profile_switch(
    profile_id, current_state, current_metadata
):
    """Clear field mapping state store AND metadata cache when switching profiles.

    This prevents old field mappings and JIRA metadata from persisting in browser memory
    after switching profiles. Critical for data isolation between profiles.

    Bug Fix 1: When user deletes profile "Apache" and creates new profile "Apache",
    the old field mappings were still shown in Configure JIRA Mappings modal
    because the state store (storage_type="memory") persisted across profile changes.

    Bug Fix 2: When switching from Profile 1 (Atlassian JIRA) to Profile 2 (Spring JIRA),
    the field fetching was still using Profile 1's cached metadata and JIRA connection,
    causing data leakage between profiles.

    Bug Fix 3: When profile selector is set to the same profile (e.g., during page init),
    don't clear state unnecessarily - this was causing field mappings to disappear when
    reopening the modal.

    Args:
        profile_id: ID of newly selected profile
        current_state: Current state store data (may contain previous profile ID)
        current_metadata: Current metadata store data

    Returns:
        Tuple of (empty state dict, empty metadata dict) to clear both stores,
        or no_update if profile hasn't actually changed
    """
    # Check if this is actually a profile change by looking at stored profile ID
    previous_profile_id = (current_state or {}).get("_profile_id")

    if previous_profile_id == profile_id:
        # Same profile - don't clear state (prevents losing data on modal reopen)
        logger.debug(
            f"[FieldMapping] Profile selector set to same profile ({profile_id}), preserving state"
        )
        return no_update, no_update

    if previous_profile_id is None:
        # First profile set (app initialization) - don't clear, just mark the profile
        # The render_tab_content callback will initialize from settings
        logger.info(
            f"[FieldMapping] First profile set: {profile_id}. Marking profile without clearing."
        )
        # Preserve any existing state, just add profile tracking
        new_state = (current_state or {}).copy()
        new_state["_profile_id"] = profile_id
        return new_state, no_update  # Preserve state, don't clear metadata

    # Actual profile switch (different profile) - clear state and metadata
    logger.info(
        f"[FieldMapping] Profile switch detected: {previous_profile_id} → {profile_id}. Clearing state and metadata."
    )
    # Clear everything except profile tracking
    return {
        "_profile_id": profile_id
    }, {}  # Clear state to re-init from new profile, clear metadata


#######################################################################
# CALLBACK: UPDATE FIELD MAPPING STATUS INDICATOR
#######################################################################


@callback(
    Output("field-mapping-status-indicator", "children"),
    [
        Input("field-mapping-modal", "is_open"),
        Input("field-mapping-save-button", "n_clicks"),
        Input("profile-selector", "value"),
    ],
    prevent_initial_call=False,  # Run on page load to show initial status
)
def update_field_mapping_status(modal_is_open, save_clicks, profile_id):
    """
    Update the field mapping status indicator to show whether fields are mapped.

    Args:
        modal_is_open: Whether the modal is currently open
        save_clicks: Number of times save button has been clicked (triggers refresh)
        profile_id: Active profile ID (triggers refresh on profile switch)

    Returns:
        Status indicator component showing mapping state
    """
    from data.persistence import load_app_settings
    import time

    try:
        # If triggered by profile switch, wait briefly for switch to complete
        if (
            callback_context.triggered
            and callback_context.triggered[0]["prop_id"] == "profile-selector.value"
        ):
            time.sleep(0.1)  # 100ms delay to let profile switch complete

        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})

        # Check if any DORA or Flow fields are mapped
        dora_mappings = field_mappings.get("dora", {})
        flow_mappings = field_mappings.get("flow", {})

        # Count non-empty mappings (excluding empty strings and None)
        dora_count = sum(1 for v in dora_mappings.values() if v and str(v).strip())
        flow_count = sum(1 for v in flow_mappings.values() if v and str(v).strip())
        total_count = dora_count + flow_count

        if total_count > 0:
            # Fields are mapped - show green success status
            return html.Div(
                [
                    html.I(className="fas fa-check-circle text-success me-2"),
                    html.Span(
                        f"Configured: {dora_count} DORA + {flow_count} Flow fields",
                        className="text-success small",
                        title=f"DORA metrics: {dora_count} fields mapped, Flow metrics: {flow_count} fields mapped",
                    ),
                ],
                className="d-flex align-items-center",
                style={"overflow": "hidden", "textOverflow": "ellipsis"},
            )
        else:
            # No fields mapped - show warning
            return html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                    html.Span(
                        "Configure field mappings to enable metrics",
                        className="text-muted small",
                    ),
                ],
                className="d-flex align-items-center",
            )

    except Exception as e:
        logger.error(f"Error loading field mapping status: {e}", exc_info=True)
        return html.Div(
            [
                html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                html.Span(
                    "Error loading field mappings",
                    className="text-muted small",
                ),
            ],
            className="d-flex align-items-center",
        )
