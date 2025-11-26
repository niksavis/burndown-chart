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
    current_state["completion_statuses"] = (
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
# MODAL MANAGEMENT
# ============================================================================


@callback(
    Output("field-mapping-modal", "is_open"),
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
) -> bool:
    """Toggle field mapping modal open/closed.

    Args:
        open_clicks: Open button clicks (from settings panel)
        open_clicks_pattern: List of clicks from pattern-matched metric card buttons
        cancel_clicks: Cancel button clicks
        save_success: True when save is successful (triggers close)
        is_open: Current modal state

    Returns:
        New modal state (True = open, False = closed)
    """
    ctx = callback_context
    if not ctx.triggered:
        return is_open

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_value = ctx.triggered[0]["value"]

    # Debug logging
    logger.info(
        f"[FieldMapping] Modal toggle - trigger_id: {trigger_id}, value: {trigger_value}"
    )

    # Close on cancel
    if trigger_id == "field-mapping-cancel-button":
        return False

    # Close ONLY on successful save (when save_success is True)
    if trigger_id == "field-mapping-save-success" and save_success is True:
        return False

    # Open when open button clicked (from settings panel or metric cards)
    # Must verify it's an actual click (value > 0), not just a button being added to DOM (value = None or 0)
    if trigger_id == "open-field-mapping-modal" or (
        trigger_id.startswith("{") and "open-field-mapping" in trigger_id
    ):
        # Only open if there was an actual click (not None, not 0, not empty list)
        if trigger_value and trigger_value != 0:
            logger.info(f"[FieldMapping] Opening modal from trigger: {trigger_id}")
            return True
        else:
            logger.info(
                f"[FieldMapping] Ignoring button render/initial state - trigger: {trigger_id}, value: {trigger_value}"
            )
            return is_open

    logger.warning(f"[FieldMapping] Modal toggle - unhandled trigger: {trigger_id}")
    return is_open


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


@callback(
    Output(
        {"type": "field-validation-message", "metric": ALL, "field": ALL}, "children"
    ),
    Input({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    Input("field-mapping-content", "children"),  # Trigger when form loads
    prevent_initial_call=True,
)
def validate_field_selection_real_time(
    field_values: List[List[str]],
    form_content,  # Not used, just triggers callback
) -> List[html.Div]:
    """Show real-time validation feedback when user selects a field.

    Validates field type compatibility and shows color-coded alerts:
    - Green: Perfect type match
    - Yellow: Compatible type (may work)
    - Red: Incompatible type
    - Gray: No field selected

    Args:
        field_values: List of selected field values (each is a list due to multi=True)
        form_content: Form content (triggers validation when form loads)

    Returns:
        List of validation message components for each dropdown
    """
    from data.field_mapper import INTERNAL_FIELD_TYPES, validate_field_mapping

    logger.info(
        f"[FieldMapping] [FieldMapping] Validation callback triggered with {len(field_values)} field values"
    )

    # Get triggered dropdown context
    ctx = callback_context
    if not ctx.triggered:
        logger.warning("[FieldMapping] Validation callback - no trigger context")
        return [html.Div() for _ in field_values]

    logger.info(
        f"[FieldMapping] Validation callback - triggered by: {ctx.triggered[0]['prop_id']}"
    )

    # Fetch available fields using the same function as the form
    # This ensures consistent field metadata structure
    try:
        available_fields = fetch_available_jira_fields()
        logger.info(
            f"[FieldMapping] [FieldMapping] Validation callback - fetched {len(available_fields)} fields from JIRA"
        )
    except Exception as e:
        logger.error(f"[FieldMapping] Error fetching fields for validation: {e}")
        return [html.Div() for _ in field_values]

    # Build field metadata lookup from available fields
    field_metadata = {}
    logger.debug(
        f"[FieldMapping] Building field metadata from {len(available_fields)} fields"
    )
    for field in available_fields:
        field_id = field.get("field_id")
        field_type = field.get("field_type", "text")
        if field_id:
            field_metadata[field_id] = {"field_type": field_type}
    logger.info(
        f"[FieldMapping] [FieldMapping] Field metadata built with {len(field_metadata)} entries"
    )

    # Get all dropdown IDs from callback context
    # For pattern-matching callbacks with ALL, ctx.inputs_list contains the component IDs
    # Structure: ctx.inputs_list[0] is a list of dicts with component IDs
    # Example: [{"id": {"type": "...", "metric": "...", "field": "..."}, "property": "value", "value": [...]}]

    # Extract component IDs from inputs
    dropdown_ids = []
    if ctx.inputs_list and len(ctx.inputs_list) > 0:
        for input_item in ctx.inputs_list[0]:
            if isinstance(input_item, dict) and "id" in input_item:
                dropdown_ids.append(input_item["id"])

    logger.info(f"[FieldMapping] Found {len(dropdown_ids)} dropdown IDs")
    if len(dropdown_ids) > 0:
        logger.info(f"[FieldMapping] First dropdown ID structure: {dropdown_ids[0]}")

    # Validate each field selection
    results = []
    for i, (dropdown_id, value_list) in enumerate(zip(dropdown_ids, field_values)):
        # Extract field info from pattern-matching ID
        internal_field = dropdown_id.get("field", "")

        logger.info(
            f"[FieldMapping] Validating dropdown {i}: internal_field='{internal_field}', value_list={value_list}"
        )

        # Get selected field ID (first item in list due to multi=True)
        selected_field_id = (
            value_list[0] if value_list and len(value_list) > 0 else None
        )

        if not selected_field_id:
            # No field selected - show empty
            logger.debug(f"[FieldMapping] Dropdown {i}: No field selected")
            results.append(html.Div())
            continue

        # Get required type for this internal field
        required_type = INTERNAL_FIELD_TYPES.get(internal_field, "unknown")

        logger.info(
            f"[FieldMapping] Dropdown {i}: selected_field_id='{selected_field_id}', required_type='{required_type}'"
        )

        # Get actual field type from metadata
        actual_type = "unknown"
        if selected_field_id in field_metadata:
            actual_type = field_metadata[selected_field_id].get("field_type", "unknown")
            logger.info(
                f"[FieldMapping] Dropdown {i}: Found field type: actual_type={actual_type}, required_type={required_type}"
            )
        else:
            logger.warning(
                f"[FieldMapping] Dropdown {i}: Field {selected_field_id} not found in metadata. Sample available fields: {list(field_metadata.keys())[:10]}"
            )

        # Validate compatibility
        is_valid = True
        message = ""

        if actual_type == "unknown" or required_type == "unknown":
            # Cannot validate - show info
            message = "[i] Field type information unavailable"
            color = "info"
        elif actual_type == required_type:
            # Perfect match
            # Special message for issuetype field (most common standard field)
            if selected_field_id == "issuetype" and internal_field in [
                "flow_item_type",
                "issue_type",
            ]:
                message = "[OK] Field type matches requirement (issuetype)"
            else:
                message = f"[OK] Field type matches requirement ({required_type})"
            color = "success"
        else:
            # Check if types are compatible
            is_valid, validation_msg = validate_field_mapping(
                internal_field, selected_field_id, field_metadata
            )

            if is_valid:
                # Compatible but not exact match
                message = f"[WARN] Field type is {actual_type}, expected {required_type} (may work)"
                color = "warning"
            else:
                # Incompatible
                message = f"[X] Incompatible: field is {actual_type}, expected {required_type}"
                color = "danger"

        # Create validation alert
        results.append(
            dbc.Alert(
                message, color=color, className="mb-0 py-1 small", dismissable=False
            )
        )

    return results


# REMOVED: Old save_field_mappings_callback
# This callback has been replaced by save_comprehensive_mappings (line ~842)
# which handles all tabs (Fields, Projects, Types, Status, Environment) with comprehensive validation.
# The old callback only handled the Fields tab without comprehensive validation,
# causing inconsistent save behavior between tabs.


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
            "work_completed_date": "resolutiondate",
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
    State("field-mapping-state-store", "data"),  # Read-only state access
    prevent_initial_call="initial_duplicate",
)
def render_tab_content(
    active_tab: str,
    metadata: dict,
    is_open: bool,
    refresh_trigger: int,
    state_data: dict,
):
    """Render appropriate form based on active tab.

    This callback now uses the state store for all form values, ensuring
    data is preserved across tab switches.

    Args:
        active_tab: ID of currently active tab
        metadata: Cached JIRA metadata from store
        is_open: Whether modal is open
        state_data: Current form state from state store

    Returns:
        Tuple of (form component, updated state)
    """
    from data.persistence import load_app_settings
    from ui.project_config_form import create_project_config_form
    from ui.issue_type_config_form import create_issue_type_config_form
    from ui.status_config_form import create_status_config_form
    from ui.environment_config_form import create_environment_config_form

    # Don't render if modal is closed (but allow initial empty state)
    if not is_open and callback_context.triggered:
        return html.Div(), no_update

    # Initialize state from saved settings on first open
    settings = load_app_settings()
    metadata = metadata or {}

    # Check if state is empty or only contains profile tracking metadata
    # (state_data with only "_profile_id" key should be re-initialized)
    is_empty_state = not state_data or (
        len(state_data) == 1 and "_profile_id" in state_data
    )

    # If state is empty, initialize it from saved settings
    if is_empty_state:
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
            "completion_statuses": settings.get("completion_statuses", []),
            "active_statuses": settings.get("active_statuses", []),
            "flow_start_statuses": settings.get("flow_start_statuses", []),
            "wip_statuses": settings.get("wip_statuses", []),
            "production_environment_values": settings.get(
                "production_environment_values", []
            ),
        }
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
        effort_category_field = settings.get("field_mappings", {}).get(
            "effort_category"
        )
        available_effort_categories = []
        if effort_category_field and metadata.get("field_options"):
            available_effort_categories = metadata.get("field_options", {}).get(
                effort_category_field, []
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
            completion_statuses=display_settings.get("completion_statuses", []),
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

        # Priority 1: Use field options from metadata (if field was already mapped when modal opened)
        if affected_env_field and metadata.get("field_options"):
            available_env_values = metadata.get("field_options", {}).get(
                affected_env_field, []
            )
            logger.debug(
                f"[FieldMapping] Loaded {len(available_env_values)} values from metadata.field_options[{affected_env_field}]"
            )

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
        Output("jira-metadata-store", "data"),
        Output("field-mapping-status", "children", allow_duplicate=True),
        Output(
            "auto-configure-button", "disabled"
        ),  # Enable button after metadata loads
    ],
    Input("field-mapping-modal", "is_open"),
    State("jira-metadata-store", "data"),
    prevent_initial_call=True,
)
def fetch_metadata_on_modal_open(is_open: bool, current_metadata: dict):
    """
    Fetch JIRA metadata automatically when modal opens (if not cached).

    Args:
        is_open: Whether modal is open
        current_metadata: Currently cached metadata

    Returns:
        Tuple of (metadata_dict, status_alert, auto_configure_button_disabled)
    """
    from data.jira_metadata import create_metadata_fetcher
    from data.persistence import load_app_settings

    # Only fetch when modal opens
    if not is_open:
        return no_update, no_update, no_update

    # If we have cached data, don't refetch but enable auto-configure button
    if current_metadata and not current_metadata.get("error"):
        logger.info("[FieldMapping] Using cached metadata")
        return no_update, no_update, False  # Enable auto-configure button

    try:
        # Load JIRA configuration from profile.json
        from data.persistence import load_jira_configuration

        jira_config = load_jira_configuration()

        # Check if JIRA is configured (base_url is required)
        if (
            not jira_config.get("base_url")
            or jira_config.get("base_url", "").strip() == ""
        ):
            logger.warning("[FieldMapping] JIRA not configured, cannot fetch metadata")
            error_alert = dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        html.Span(
                            [
                                html.Strong("JIRA Not Configured"),
                                html.Br(),
                                html.Small(
                                    "Please configure JIRA connection first in the Connect tab.",
                                    style={"opacity": "0.85"},
                                ),
                            ]
                        ),
                    ],
                    className="d-flex align-items-start",
                ),
                color="danger",
                dismissable=True,
            )
            return (
                {"error": "JIRA not configured"},
                error_alert,
                True,
            )  # Keep button disabled

        # Create fetcher and fetch all metadata
        fetcher = create_metadata_fetcher(
            jira_url=jira_config.get("base_url", ""),
            jira_token=jira_config.get("token", ""),
            api_version=jira_config.get("api_version", "v2"),
        )

        logger.info("[FieldMapping] Fetching JIRA metadata...")

        # Fetch all metadata types
        fields = fetcher.fetch_fields()

        # Log all custom fields to help find the correct field ID
        custom_fields = [f for f in fields if f.get("custom", False)]
        logger.info(
            f"[FieldMapping] [FieldMapping] Found {len(custom_fields)} custom fields in JIRA:"
        )
        for field in custom_fields:
            logger.info(
                f"[FieldMapping] [FieldMapping]   - {field['id']}: {field['name']} (type: {field['type']})"
            )

        projects = fetcher.fetch_projects()
        issue_types = fetcher.fetch_issue_types()
        statuses = fetcher.fetch_statuses()

        # Auto-detect configurations
        auto_detected_types = fetcher.auto_detect_issue_types(issue_types)
        auto_detected_statuses = fetcher.auto_detect_statuses(statuses)

        # Load current settings for field mappings
        from data.persistence import load_app_settings

        settings = load_app_settings()

        # Fetch environment field options if mapped
        # affected_environment is the primary field for incident tracking and MTTR
        # If target_environment is also mapped to same field ID, values will be available for both
        # Note: field_mappings are nested under 'dora' and 'flow' categories
        dora_mappings = settings.get("field_mappings", {}).get("dora", {})
        affected_env_field = dora_mappings.get("affected_environment")
        target_env_field = dora_mappings.get("target_environment")

        env_options = []
        env_field_to_fetch = None

        # Fetch from affected_environment (primary field for Production Identifiers)
        if affected_env_field:
            env_field_to_fetch = affected_env_field
            logger.info(
                f"[FieldMapping] Fetching field options for affected_environment field: {affected_env_field}"
            )
        # Fallback to target_environment if affected_environment not mapped
        elif target_env_field:
            env_field_to_fetch = target_env_field
            logger.info(
                f"[FieldMapping] affected_environment not mapped, fetching from target_environment field: {target_env_field}"
            )

        if env_field_to_fetch:
            env_options = fetcher.fetch_field_options(env_field_to_fetch)
            logger.info(
                f"[FieldMapping] Found {len(env_options)} environment values: {env_options}"
            )
            auto_detected_prod = fetcher.auto_detect_production_identifiers(env_options)
            logger.info(
                f"[FieldMapping] Auto-detected production identifiers: {auto_detected_prod}"
            )
        else:
            logger.warning(
                "[FieldMapping] affected_environment field not mapped, cannot fetch environment values for Production Identifiers"
            )
            auto_detected_prod = []

        # Fetch effort category field options if mapped
        effort_category_field = settings.get("field_mappings", {}).get(
            "effort_category"
        )
        effort_category_options = []
        if effort_category_field:
            logger.info(
                f"[FieldMapping] Fetching field options for effort_category field: {effort_category_field}"
            )
            effort_category_options = fetcher.fetch_field_options(effort_category_field)
            logger.info(
                f"[FieldMapping] Found {len(effort_category_options)} effort category values: {effort_category_options}"
            )
        else:
            logger.warning(
                "[FieldMapping] effort_category field not mapped, cannot fetch effort category values"
            )

        # Build field_options dictionary with all fetched fields
        # Store environment options under the fetched field ID
        # If both target_environment and affected_environment point to same field, both will work
        field_options_dict = {}
        if env_field_to_fetch and env_options:
            field_options_dict[env_field_to_fetch] = env_options
            logger.info(
                f"[FieldMapping] Stored {len(env_options)} environment values under field ID: {env_field_to_fetch}"
            )

        if effort_category_field:
            field_options_dict[effort_category_field] = effort_category_options

        metadata = {
            "fields": fields,
            "projects": projects,
            "issue_types": issue_types,
            "statuses": statuses,
            "field_options": field_options_dict,
            "auto_detected": {
                "issue_types": auto_detected_types,
                "statuses": auto_detected_statuses,
                "production_identifiers": auto_detected_prod,
            },
            "fetched_at": callback_context.triggered[0]["value"],
        }

        logger.info(
            f"Successfully fetched metadata: {len(projects)} projects, {len(issue_types)} issue types, {len(statuses)} statuses"
        )

        # Show success toast message
        success_alert = dbc.Alert(
            html.Div(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    html.Span(
                        [
                            html.Strong("Metadata Fetched"),
                            html.Br(),
                            html.Small(
                                f"Loaded {len(projects)} projects, {len(issue_types)} issue types, {len(statuses)} statuses.",
                                style={"opacity": "0.85"},
                            ),
                        ]
                    ),
                ],
                className="d-flex align-items-start",
            ),
            color="success",
            dismissable=True,
            duration=4000,  # Auto-dismiss after 4 seconds
        )

        return metadata, success_alert, False  # Enable auto-configure button

    except Exception as e:
        logger.error(f"Error fetching JIRA metadata: {e}")
        error_alert = dbc.Alert(
            html.Div(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    html.Span(
                        [
                            html.Strong("Fetch Failed"),
                            html.Br(),
                            html.Small(
                                f"Error fetching metadata: {str(e)}",
                                style={"opacity": "0.85"},
                            ),
                        ]
                    ),
                ],
                className="d-flex align-items-start",
            ),
            color="danger",
            dismissable=True,
        )
        return {"error": str(e)}, error_alert, True  # Keep button disabled on error


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
        )

    try:
        # Validate metadata is available
        if not metadata or metadata.get("error"):
            error_alert = dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "Cannot auto-configure: JIRA metadata not available. Please ensure JIRA is connected.",
                ],
                color="danger",
                dismissable=True,
            )
            return (
                no_update,
                error_alert,
                False,  # Close confirmation modal
                no_update,  # Don't trigger refresh on error
            )

        # Get active profile to extract JQL query
        active_profile = get_active_profile()
        if not active_profile:
            error_alert = dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "Cannot auto-configure: No active profile found.",
                ],
                color="danger",
                dismissable=True,
            )
            return (
                no_update,
                error_alert,
                False,  # Close confirmation modal
                no_update,  # Don't trigger refresh on error
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
        new_state["completion_statuses"] = defaults["project_classification"][
            "completion_statuses"
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
        completion_count = len(
            defaults["project_classification"]["completion_statuses"]
        )
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

        # Create compact success message
        success_alert = dbc.Alert(
            [
                html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        html.Strong("Auto-Configuration Complete: "),
                        f"{completion_count + active_count + wip_count} statuses, ",
                        f"{feature_count + defect_count} work types, ",
                        f"{project_count} project{'s' if project_count != 1 else ''}. ",
                        html.Strong(
                            "Click 'Save Mappings' to apply.", className="ms-2"
                        ),
                    ],
                ),
            ],
            color="success",
            dismissable=True,
            duration=6000,
        )

        # Increment refresh trigger to force tab re-render with new state
        new_trigger = (current_trigger or 0) + 1
        return (
            new_state,
            success_alert,
            False,
            new_trigger,
        )  # Close modal, trigger refresh

    except Exception as e:
        logger.error(
            f"[AutoConfigure] Error during auto-configuration: {e}", exc_info=True
        )
        error_alert = dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                html.Div(
                    [
                        html.Strong("Auto-Configuration Failed"),
                        html.Br(),
                        html.Small(f"Error: {str(e)}", style={"opacity": "0.85"}),
                    ]
                ),
            ],
            color="danger",
            dismissable=True,
        )
        return (
            no_update,
            error_alert,
            False,
            no_update,
        )  # Close modal, don't trigger refresh


@callback(
    Output("field-mapping-save-success", "data", allow_duplicate=True),
    Output("field-mapping-status", "children", allow_duplicate=True),
    Output("field-mapping-state-store", "data", allow_duplicate=True),
    Input("field-mapping-save-button", "n_clicks"),
    State("field-mapping-state-store", "data"),
    prevent_initial_call=True,
)
def save_comprehensive_mappings(n_clicks, state_data):
    """Save comprehensive configuration from state store.

    This simplified callback reads directly from the state store,
    eliminating the need for DOM parsing and complex extraction logic.

    Args:
        n_clicks: Number of times save button clicked
        state_data: Current form state from state store

    Returns:
        Tuple of (save_success, status_message, updated_state)
    """
    from data.persistence import save_app_settings, load_app_settings

    if not n_clicks:
        return no_update, no_update, no_update

    try:
        # Load current settings
        settings = load_app_settings()

        # Update settings from state store
        # Field mappings
        if "field_mappings" in state_data:
            settings["field_mappings"] = state_data["field_mappings"]
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
            settings["completion_statuses"] = proj_class.get("completion_statuses", [])
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
        if "completion_statuses" in state_data:
            settings["completion_statuses"] = state_data["completion_statuses"]
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
            completion_statuses=settings.get("completion_statuses"),
            active_statuses=settings.get("active_statuses"),
            flow_start_statuses=settings.get("flow_start_statuses"),
            wip_statuses=settings.get("wip_statuses"),
            flow_type_mappings=settings.get("flow_type_mappings"),
            cache_metadata=settings.get("cache_metadata"),
        )

        logger.info("[FieldMapping] Mappings saved successfully from state store")

        # Success alert
        success_alert = dbc.Alert(
            html.Div(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    html.Span(
                        [
                            html.Strong("Configuration Saved Successfully!"),
                            html.Br(),
                            html.Small(
                                "Your field mappings and configurations have been saved.",
                                style={"opacity": "0.85"},
                            ),
                        ]
                    ),
                ],
                className="d-flex align-items-start",
            ),
            color="success",
            dismissable=True,
            duration=4000,
        )

        # Keep state store intact so UI remains populated
        return True, success_alert, no_update

    except Exception as e:
        logger.error(f"[FieldMapping] Error saving mappings: {e}")
        error_alert = dbc.Alert(
            html.Div(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    html.Span(
                        [
                            html.Strong("Save Failed"),
                            html.Br(),
                            html.Small(
                                f"Error saving mappings: {str(e)}",
                                style={"opacity": "0.85"},
                            ),
                        ]
                    ),
                ],
                className="d-flex align-items-start",
            ),
            color="danger",
            dismissable=True,
        )
        return False, error_alert, no_update


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
