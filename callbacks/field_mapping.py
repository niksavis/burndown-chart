"""Callbacks for field mapping configuration.

Handles field mapping modal interactions, Jira field discovery,
validation, and persistence.
"""

from dash import callback, callback_context, Output, Input, State, no_update, ALL, html
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import logging

from data.field_mapper import (
    load_field_mappings,
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

            # Handle multi-select dropdown: extract first value or empty string
            if isinstance(new_value, list):
                current_state["field_mappings"][metric][field] = (
                    new_value[0] if new_value else ""
                )
            else:
                current_state["field_mappings"][metric][field] = new_value or ""

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
            message = "ℹ️ Field type information unavailable"
            color = "info"
        elif actual_type == required_type:
            # Perfect match
            message = f"✓ Field type matches requirement ({required_type})"
            color = "success"
        else:
            # Check if types are compatible
            is_valid, validation_msg = validate_field_mapping(
                internal_field, selected_field_id, field_metadata
            )

            if is_valid:
                # Compatible but not exact match
                message = f"⚠ Field type is {actual_type}, expected {required_type} (may work)"
                color = "warning"
            else:
                # Incompatible
                message = (
                    f"✗ Incompatible: field is {actual_type}, expected {required_type}"
                )
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
    State("field-mapping-state-store", "data"),
    prevent_initial_call="initial_duplicate",
)
def render_tab_content(
    active_tab: str, metadata: dict, is_open: bool, state_data: dict
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

    # If state is empty, initialize it from saved settings
    if not state_data:
        # Helper to safely extract flow type mappings
        flow_mappings = settings.get("flow_type_mappings", {}) or {}

        def safe_get_flow_mapping(flow_type, key):
            """Safely extract flow mapping, handling None values."""
            flow_config = flow_mappings.get(flow_type, {})
            if flow_config is None:
                return []
            return flow_config.get(key, []) or []

        state_data = {
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
            return create_field_mapping_error_alert(str(e)), no_update

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

        return create_issue_type_config_form(
            devops_task_types=display_settings.get("devops_task_types", []),
            bug_types=display_settings.get("bug_types", []),
            story_types=display_settings.get("story_types", []),
            task_types=display_settings.get("task_types", []),
            available_issue_types=metadata.get("issue_types", []),
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
        # Get production environment field value options
        prod_env_field = settings.get("field_mappings", {}).get("target_environment")
        available_env_values = []
        if prod_env_field and metadata.get("field_options"):
            available_env_values = metadata.get("field_options", {}).get(
                prod_env_field, []
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
    ],
    Input("fetch-metadata-button", "n_clicks"),
    Input("field-mapping-modal", "is_open"),
    State("jira-metadata-store", "data"),
    prevent_initial_call=True,
)
def fetch_metadata(n_clicks: int, is_open: bool, current_metadata: dict):
    """
    Fetch JIRA metadata when button clicked or modal opened (if not cached).

    Args:
        n_clicks: Number of times fetch button clicked
        is_open: Whether modal is open
        current_metadata: Currently cached metadata

    Returns:
        Dictionary with fetched metadata
    """
    from data.jira_metadata import create_metadata_fetcher
    from data.persistence import load_app_settings

    # Determine trigger
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # If modal just opened and we have cached data, don't refetch
    if trigger_id == "field-mapping-modal" and current_metadata:
        return no_update, no_update

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
            return {"error": "JIRA not configured"}, error_alert

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
        affected_env_field = settings.get("field_mappings", {}).get(
            "affected_environment"
        )
        env_options = []
        if affected_env_field:
            logger.info(
                f"[FieldMapping] Fetching field options for affected_environment field: {affected_env_field}"
            )
            env_options = fetcher.fetch_field_options(affected_env_field)
            logger.info(
                f"[FieldMapping] Found {len(env_options)} environment values: {env_options}"
            )
            auto_detected_prod = fetcher.auto_detect_production_identifiers(env_options)
            logger.info(
                f"[FieldMapping] Auto-detected production identifiers: {auto_detected_prod}"
            )
        else:
            logger.warning(
                "[FieldMapping] affected_environment field not mapped, cannot fetch environment values"
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
        field_options_dict = {}
        if affected_env_field:
            field_options_dict[affected_env_field] = env_options
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

        return metadata, success_alert

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
        return {"error": str(e)}, error_alert


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

        # Projects
        if "development_projects" in state_data:
            settings["development_projects"] = state_data["development_projects"]
        if "devops_projects" in state_data:
            settings["devops_projects"] = state_data["devops_projects"]

        # Issue Types
        if "devops_task_types" in state_data:
            settings["devops_task_types"] = state_data["devops_task_types"]
        if "bug_types" in state_data:
            settings["bug_types"] = state_data["bug_types"]
        if "story_types" in state_data:
            settings["story_types"] = state_data["story_types"]
        if "task_types" in state_data:
            settings["task_types"] = state_data["task_types"]

        # Flow type mappings
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
                "issue_types": state_data.get("flow_technical_debt_issue_types", []),
                "effort_categories": state_data.get(
                    "flow_technical_debt_effort_categories", []
                ),
            },
            "Risk": {
                "issue_types": state_data.get("flow_risk_issue_types", []),
                "effort_categories": state_data.get("flow_risk_effort_categories", []),
            },
        }
        settings["flow_type_mappings"] = flow_type_mappings

        # Statuses
        if "completion_statuses" in state_data:
            settings["completion_statuses"] = state_data["completion_statuses"]
        if "active_statuses" in state_data:
            settings["active_statuses"] = state_data["active_statuses"]
        if "flow_start_statuses" in state_data:
            settings["flow_start_statuses"] = state_data["flow_start_statuses"]
        if "wip_statuses" in state_data:
            settings["wip_statuses"] = state_data["wip_statuses"]

        # Environment
        if "production_environment_values" in state_data:
            settings["production_environment_values"] = state_data[
                "production_environment_values"
            ]

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

        # Clear state store after successful save
        return True, success_alert, {}

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
    prevent_initial_call=True,
)
def clear_field_mapping_state_on_profile_switch(profile_id):
    """Clear field mapping state store AND metadata cache when switching profiles.

    This prevents old field mappings and JIRA metadata from persisting in browser memory
    after switching profiles. Critical for data isolation between profiles.

    Bug Fix 1: When user deletes profile "Apache" and creates new profile "Apache",
    the old field mappings were still shown in Configure JIRA Mappings modal
    because the state store (storage_type="memory") persisted across profile changes.

    Bug Fix 2: When switching from Profile 1 (Atlassian JIRA) to Profile 2 (Spring JIRA),
    the field fetching was still using Profile 1's cached metadata and JIRA connection,
    causing data leakage between profiles.

    Args:
        profile_id: ID of newly selected profile

    Returns:
        Tuple of (empty state dict, empty metadata dict) to clear both stores
    """
    logger.info(
        f"[FieldMapping] Clearing state store AND metadata cache due to profile switch to: {profile_id}"
    )
    return {}, {}  # Clear both state store and metadata cache
