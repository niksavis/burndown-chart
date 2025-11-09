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
from data.metrics_cache import invalidate_cache
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
        f"Field mapping modal toggle - trigger_id: {trigger_id}, value: {trigger_value}"
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
            logger.info(f"Opening field mapping modal from trigger: {trigger_id}")
            return True
        else:
            logger.info(
                f"Ignoring button render/initial state - trigger: {trigger_id}, value: {trigger_value}"
            )
            return is_open

    logger.warning(f"Field mapping modal toggle - unhandled trigger: {trigger_id}")
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

    logger.info(f"Validation callback triggered with {len(field_values)} field values")

    # Get triggered dropdown context
    ctx = callback_context
    if not ctx.triggered:
        logger.warning("Validation callback - no trigger context")
        return [html.Div() for _ in field_values]

    logger.info(f"Validation callback - triggered by: {ctx.triggered[0]['prop_id']}")

    # Fetch available fields using the same function as the form
    # This ensures consistent field metadata structure
    try:
        available_fields = fetch_available_jira_fields()
        logger.info(
            f"Validation callback - fetched {len(available_fields)} fields from JIRA"
        )
    except Exception as e:
        logger.error(f"Error fetching fields for validation: {e}")
        return [html.Div() for _ in field_values]

    # Build field metadata lookup from available fields
    field_metadata = {}
    logger.debug(f"Building field metadata from {len(available_fields)} fields")
    for field in available_fields:
        field_id = field.get("field_id")
        field_type = field.get("field_type", "text")
        if field_id:
            field_metadata[field_id] = {"field_type": field_type}
    logger.info(f"Field metadata built with {len(field_metadata)} entries")

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

    logger.info(f"Found {len(dropdown_ids)} dropdown IDs")
    if len(dropdown_ids) > 0:
        logger.info(f"First dropdown ID structure: {dropdown_ids[0]}")

    # Validate each field selection
    results = []
    for i, (dropdown_id, value_list) in enumerate(zip(dropdown_ids, field_values)):
        # Extract field info from pattern-matching ID
        internal_field = dropdown_id.get("field", "")

        logger.info(
            f"Validating dropdown {i}: internal_field='{internal_field}', value_list={value_list}"
        )

        # Get selected field ID (first item in list due to multi=True)
        selected_field_id = (
            value_list[0] if value_list and len(value_list) > 0 else None
        )

        if not selected_field_id:
            # No field selected - show empty
            logger.debug(f"Dropdown {i}: No field selected")
            results.append(html.Div())
            continue

        # Get required type for this internal field
        required_type = INTERNAL_FIELD_TYPES.get(internal_field, "unknown")

        logger.info(
            f"Dropdown {i}: selected_field_id='{selected_field_id}', required_type='{required_type}'"
        )

        # Get actual field type from metadata
        actual_type = "unknown"
        if selected_field_id in field_metadata:
            actual_type = field_metadata[selected_field_id].get("field_type", "unknown")
            logger.info(
                f"Dropdown {i}: Found field type: actual_type={actual_type}, required_type={required_type}"
            )
        else:
            logger.warning(
                f"Dropdown {i}: Field {selected_field_id} not found in metadata. Sample available fields: {list(field_metadata.keys())[:10]}"
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
    Input("mappings-tabs", "active_tab"),
    Input("jira-metadata-store", "data"),
    Input(
        "field-mapping-modal", "is_open"
    ),  # Changed to Input to trigger on modal open
    prevent_initial_call=False,
)
def render_tab_content(active_tab: str, metadata: dict, is_open: bool):
    """
    Render appropriate form based on active tab.

    Args:
        active_tab: ID of currently active tab
        metadata: Cached JIRA metadata from store
        is_open: Whether modal is open

    Returns:
        Form component for the active tab
    """
    from data.persistence import load_app_settings
    from ui.project_config_form import create_project_config_form
    from ui.issue_type_config_form import create_issue_type_config_form
    from ui.status_config_form import create_status_config_form
    from ui.environment_config_form import create_environment_config_form

    # Don't render if modal is closed (but allow initial empty state)
    if not is_open and callback_context.triggered:
        # Modal closed after being open - clear content
        return html.Div()

    # Load current settings
    settings = load_app_settings()
    metadata = metadata or {}

    # Render content based on active tab
    if active_tab == "tab-fields":
        # Existing field mapping form (already implemented)
        try:
            available_fields = fetch_available_jira_fields()
            current_mappings = load_field_mappings()
            return create_field_mapping_form(available_fields, current_mappings)
        except Exception as e:
            logger.error(f"Error loading field mappings: {e}")
            return create_field_mapping_error_alert(str(e))

    elif active_tab == "tab-projects":
        return create_project_config_form(
            development_projects=settings.get("development_projects", []),
            devops_projects=settings.get("devops_projects", []),
            available_projects=metadata.get("projects", []),
        )

    elif active_tab == "tab-types":
        # Get flow_type_mappings from settings (new structure)
        flow_type_mappings = settings.get("flow_type_mappings", {})

        # Get effort category field options if mapped (same pattern as environment)
        effort_category_field = settings.get("field_mappings", {}).get(
            "effort_category"
        )
        available_effort_categories = []
        if effort_category_field and metadata.get("field_options"):
            available_effort_categories = metadata.get("field_options", {}).get(
                effort_category_field, []
            )

        return create_issue_type_config_form(
            devops_task_types=settings.get("devops_task_types", []),
            bug_types=settings.get("bug_types", []),
            story_types=settings.get("story_types", []),  # DEPRECATED
            task_types=settings.get("task_types", []),  # DEPRECATED
            available_issue_types=metadata.get("issue_types", []),
            flow_type_mappings=flow_type_mappings,
            available_effort_categories=available_effort_categories,
        )

    elif active_tab == "tab-status":
        return create_status_config_form(
            completion_statuses=settings.get("completion_statuses", []),
            active_statuses=settings.get("active_statuses", []),
            flow_start_statuses=settings.get("flow_start_statuses", []),
            wip_statuses=settings.get("wip_statuses", []),
            available_statuses=metadata.get("statuses", []),
        )

    elif active_tab == "tab-environment":
        # Get environment field options if affected_environment is mapped
        affected_env_field = settings.get("field_mappings", {}).get(
            "affected_environment"
        )
        env_options = []
        if affected_env_field and metadata.get("field_options"):
            env_options = metadata.get("field_options", {}).get(affected_env_field, [])

        return create_environment_config_form(
            production_environment_values=settings.get(
                "production_environment_values", []
            ),
            available_environment_values=env_options,
        )

    return html.Div("Unknown tab")


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
        # Load JIRA configuration
        settings = load_app_settings()
        jira_config = settings.get("jira_config", {})

        if not jira_config.get("configured"):
            logger.warning("JIRA not configured, cannot fetch metadata")
            error_alert = dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        html.Span(
                            [
                                html.Strong("JIRA Not Configured"),
                                html.Br(),
                                html.Small(
                                    "Please configure JIRA connection first.",
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

        logger.info("Fetching JIRA metadata...")

        # Fetch all metadata types
        fields = fetcher.fetch_fields()

        # Log all custom fields to help find the correct field ID
        custom_fields = [f for f in fields if f.get("custom", False)]
        logger.info(f"Found {len(custom_fields)} custom fields in JIRA:")
        for field in custom_fields:
            logger.info(f"  - {field['id']}: {field['name']} (type: {field['type']})")

        projects = fetcher.fetch_projects()
        issue_types = fetcher.fetch_issue_types()
        statuses = fetcher.fetch_statuses()

        # Auto-detect configurations
        auto_detected_types = fetcher.auto_detect_issue_types(issue_types)
        auto_detected_statuses = fetcher.auto_detect_statuses(statuses)

        # Fetch environment field options if mapped
        affected_env_field = settings.get("field_mappings", {}).get(
            "affected_environment"
        )
        env_options = []
        if affected_env_field:
            logger.info(
                f"Fetching field options for affected_environment field: {affected_env_field}"
            )
            env_options = fetcher.fetch_field_options(affected_env_field)
            logger.info(f"Found {len(env_options)} environment values: {env_options}")
            auto_detected_prod = fetcher.auto_detect_production_identifiers(env_options)
            logger.info(f"Auto-detected production identifiers: {auto_detected_prod}")
        else:
            logger.warning(
                "affected_environment field not mapped, cannot fetch environment values"
            )
            auto_detected_prod = []

        # Fetch effort category field options if mapped
        effort_category_field = settings.get("field_mappings", {}).get(
            "effort_category"
        )
        effort_category_options = []
        if effort_category_field:
            logger.info(
                f"Fetching field options for effort_category field: {effort_category_field}"
            )
            effort_category_options = fetcher.fetch_field_options(effort_category_field)
            logger.info(
                f"Found {len(effort_category_options)} effort category values: {effort_category_options}"
            )
        else:
            logger.warning(
                "effort_category field not mapped, cannot fetch effort category values"
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
    Input("field-mapping-save-button", "n_clicks"),
    State("mappings-tabs", "active_tab"),
    State("field-mapping-content", "children"),
    prevent_initial_call=True,
)
def save_comprehensive_mappings(n_clicks, active_tab, content_children):
    """
    Save comprehensive mappings configuration to app_settings.json.

    This callback handles ALL tabs: Fields, Projects, Types, Status, and Environment.
    It extracts values from the rendered content dynamically.

    Validates configuration and provides feedback on errors/warnings.
    """
    from data.persistence import save_app_settings, load_app_settings
    from data.config_validation import (
        validate_comprehensive_config,
        format_validation_messages,
    )

    if not n_clicks:
        return no_update, no_update

    # Note: This callback now handles ALL tabs including Fields tab
    # The old save_field_mappings_callback is deprecated

    # Extract dropdown values from the content children
    # This requires parsing the component tree to find dropdown values
    def extract_dropdown_value(component_id, children):
        """Recursively extract dropdown value from component tree."""
        if children is None:
            return None

        # Handle dict (component)
        if isinstance(children, dict):
            # Check if this is the dropdown we're looking for
            props = children.get("props", {})
            if props.get("id") == component_id:
                return props.get("value")
            # Recursively search children
            for key in ["children", "content"]:
                if key in props:
                    result = extract_dropdown_value(component_id, props[key])
                    if result is not None:
                        return result
        # Handle list
        elif isinstance(children, list):
            for child in children:
                result = extract_dropdown_value(component_id, child)
                if result is not None:
                    return result

        return None

    # Extract values based on active tab
    dev_projects = None
    devops_projects = None
    devops_task_types = None
    bug_types = None
    story_types = None
    task_types = None
    completion_statuses = None
    active_statuses = None
    flow_start_statuses = None
    wip_statuses = None
    production_env_values = None
    field_mappings = None  # NEW: For Fields tab

    # Flow type mapping variables
    flow_feature_types = None
    flow_feature_categories = None
    flow_defect_types = None
    flow_defect_categories = None
    flow_tech_debt_types = None
    flow_tech_debt_categories = None
    flow_risk_types = None
    flow_risk_categories = None

    if active_tab == "tab-fields":
        # Extract field mappings from dropdown values
        # Field mappings use pattern-matched IDs: {"type": "field-mapping-dropdown", "metric": "dora|flow", "field": "field_name"}
        def extract_field_mappings_from_children(children):
            """Extract all field mapping dropdown values from component tree."""
            mappings = {}

            def traverse(node):
                if isinstance(node, dict):
                    props = node.get("props", {})
                    component_id = props.get("id")

                    # Check if this is a field mapping dropdown
                    if (
                        isinstance(component_id, dict)
                        and component_id.get("type") == "field-mapping-dropdown"
                    ):
                        field_name = component_id.get("field")
                        value = props.get("value")
                        # Multi-select dropdowns return lists, extract first value
                        if isinstance(value, list) and len(value) > 0:
                            mappings[field_name] = value[0]
                        elif value:
                            mappings[field_name] = value

                    # Recursively search children
                    for key in ["children", "content"]:
                        if key in props:
                            traverse(props[key])
                elif isinstance(node, list):
                    for child in node:
                        traverse(child)

            traverse(children)
            return mappings

        field_mappings = extract_field_mappings_from_children(content_children)
        logger.info(f"Extracted field mappings from Fields tab: {field_mappings}")

    elif active_tab == "tab-projects":
        dev_projects = extract_dropdown_value(
            "development-projects-dropdown", content_children
        )
        devops_projects = extract_dropdown_value(
            "devops-projects-dropdown", content_children
        )
    elif active_tab == "tab-types":
        devops_task_types = extract_dropdown_value(
            "devops-task-types-dropdown", content_children
        )
        bug_types = extract_dropdown_value("bug-types-dropdown", content_children)
        story_types = extract_dropdown_value(
            "story-types-dropdown", content_children
        )  # DEPRECATED
        task_types = extract_dropdown_value(
            "task-types-dropdown", content_children
        )  # DEPRECATED

        # Extract Flow type mappings (new structure)
        flow_feature_types = extract_dropdown_value(
            "flow-feature-issue-types-dropdown", content_children
        )
        flow_feature_categories = extract_dropdown_value(
            "flow-feature-effort-categories-dropdown", content_children
        )
        flow_defect_types = extract_dropdown_value(
            "flow-defect-issue-types-dropdown", content_children
        )
        flow_defect_categories = extract_dropdown_value(
            "flow-defect-effort-categories-dropdown", content_children
        )
        flow_tech_debt_types = extract_dropdown_value(
            "flow-technical-debt-issue-types-dropdown", content_children
        )
        flow_tech_debt_categories = extract_dropdown_value(
            "flow-technical-debt-effort-categories-dropdown", content_children
        )
        flow_risk_types = extract_dropdown_value(
            "flow-risk-issue-types-dropdown", content_children
        )
        flow_risk_categories = extract_dropdown_value(
            "flow-risk-effort-categories-dropdown", content_children
        )
    elif active_tab == "tab-status":
        completion_statuses = extract_dropdown_value(
            "completion-statuses-dropdown", content_children
        )
        active_statuses = extract_dropdown_value(
            "active-statuses-dropdown", content_children
        )
        flow_start_statuses = extract_dropdown_value(
            "flow-start-statuses-dropdown", content_children
        )
        wip_statuses = extract_dropdown_value("wip-statuses-dropdown", content_children)
    elif active_tab == "tab-environment":
        production_env_values = extract_dropdown_value(
            "production-environment-values-dropdown", content_children
        )

    try:
        # Load current settings
        settings = load_app_settings()

        # DEBUG: Log received values
        logger.info(
            f"Save mappings callback - received completion_statuses: {completion_statuses}, type: {type(completion_statuses)}"
        )
        logger.info(f"Save mappings callback - active tab: {active_tab}")

        # Update field_mappings if from Fields tab
        if field_mappings is not None:
            settings["field_mappings"] = field_mappings
            logger.info(f"Updated field_mappings from Fields tab: {field_mappings}")

        # Update with new values (only update non-None values)
        if dev_projects is not None:
            settings["development_projects"] = (
                dev_projects
                if isinstance(dev_projects, list)
                else [dev_projects]
                if dev_projects
                else []
            )

        if devops_projects is not None:
            settings["devops_projects"] = (
                devops_projects
                if isinstance(devops_projects, list)
                else [devops_projects]
                if devops_projects
                else []
            )

        if devops_task_types is not None:
            settings["devops_task_types"] = (
                devops_task_types
                if isinstance(devops_task_types, list)
                else [devops_task_types]
                if devops_task_types
                else []
            )

        if bug_types is not None:
            settings["bug_types"] = (
                bug_types
                if isinstance(bug_types, list)
                else [bug_types]
                if bug_types
                else []
            )

        if story_types is not None:
            settings["story_types"] = (
                story_types
                if isinstance(story_types, list)
                else [story_types]
                if story_types
                else []
            )

        if task_types is not None:
            settings["task_types"] = (
                task_types
                if isinstance(task_types, list)
                else [task_types]
                if task_types
                else []
            )

        # Save Flow type mappings (new structure)
        if active_tab == "tab-types":
            # Build flow_type_mappings structure
            flow_type_mappings = {}

            # Helper function to normalize to list
            def to_list(value):
                if value is None:
                    return []
                return value if isinstance(value, list) else [value] if value else []

            # Feature mapping
            flow_type_mappings["Feature"] = {
                "issue_types": to_list(flow_feature_types),
                "effort_categories": to_list(flow_feature_categories),
            }

            # Defect mapping
            flow_type_mappings["Defect"] = {
                "issue_types": to_list(flow_defect_types),
                "effort_categories": to_list(flow_defect_categories),
            }

            # Technical Debt mapping
            flow_type_mappings["Technical_Debt"] = {
                "issue_types": to_list(flow_tech_debt_types),
                "effort_categories": to_list(flow_tech_debt_categories),
            }

            # Risk mapping
            flow_type_mappings["Risk"] = {
                "issue_types": to_list(flow_risk_types),
                "effort_categories": to_list(flow_risk_categories),
            }

            settings["flow_type_mappings"] = flow_type_mappings
            logger.info(f"Updated flow_type_mappings: {flow_type_mappings}")

        if completion_statuses is not None:
            settings["completion_statuses"] = (
                completion_statuses
                if isinstance(completion_statuses, list)
                else [completion_statuses]
                if completion_statuses
                else []
            )

        if active_statuses is not None:
            settings["active_statuses"] = (
                active_statuses
                if isinstance(active_statuses, list)
                else [active_statuses]
                if active_statuses
                else []
            )

        if flow_start_statuses is not None:
            settings["flow_start_statuses"] = (
                flow_start_statuses
                if isinstance(flow_start_statuses, list)
                else [flow_start_statuses]
                if flow_start_statuses
                else []
            )

        if wip_statuses is not None:
            settings["wip_statuses"] = (
                wip_statuses
                if isinstance(wip_statuses, list)
                else [wip_statuses]
                if wip_statuses
                else []
            )

        if production_env_values is not None:
            settings["production_environment_values"] = (
                production_env_values
                if isinstance(production_env_values, list)
                else [production_env_values]
                if production_env_values
                else []
            )

        # DEBUG: Log updated settings
        logger.info(
            f"Save mappings - updated completion_statuses in settings: {settings.get('completion_statuses')}"
        )

        # Validate comprehensive configuration
        validation_result = validate_comprehensive_config(settings)

        # Check for errors (block save)
        if validation_result["errors"]:
            error_message = format_validation_messages(validation_result)
            error_alert = dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        html.Span(
                            [
                                html.Strong("Validation Errors"),
                                html.Br(),
                                html.Small(
                                    "Configuration has errors:",
                                    style={"opacity": "0.85"},
                                ),
                                html.Pre(error_message, className="mt-2 mb-0"),
                            ]
                        ),
                    ],
                    className="d-flex align-items-start",
                ),
                color="danger",
                dismissable=True,
            )
            return no_update, error_alert

        # Save settings (now includes field_mappings for Fields tab)
        save_app_settings(
            pert_factor=settings.get("pert_factor"),
            deadline=settings.get("deadline"),
            data_points_count=settings.get("data_points_count"),
            show_milestone=settings.get("show_milestone"),
            milestone=settings.get("milestone"),
            show_points=settings.get("show_points"),
            jql_query=settings.get("jql_query"),
            last_used_data_source=settings.get("last_used_data_source"),
            active_jql_profile_id=settings.get("active_jql_profile_id"),
            jira_config=settings.get("jira_config"),
            field_mappings=settings.get(
                "field_mappings"
            ),  # Now saved for Fields tab too
            devops_projects=settings.get("devops_projects"),
            development_projects=settings.get("development_projects"),
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
        )

        # Invalidate metrics cache since configuration changed
        invalidate_cache()

        logger.info(f"Comprehensive mappings saved successfully from tab: {active_tab}")

        # Show success with warnings if any
        if validation_result["warnings"]:
            warning_message = format_validation_messages(validation_result)
            success_alert = dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        html.Span(
                            [
                                html.Strong("Configuration Saved"),
                                html.Br(),
                                html.Small(
                                    "Configuration saved with warnings:",
                                    style={"opacity": "0.85"},
                                ),
                                html.Pre(warning_message, className="mt-2 mb-0"),
                            ]
                        ),
                    ],
                    className="d-flex align-items-start",
                ),
                color="warning",
                dismissable=True,
            )
        else:
            success_alert = dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        html.Span(
                            [
                                html.Strong("Configuration Saved"),
                                html.Br(),
                                html.Small(
                                    f"Configuration for {active_tab.replace('tab-', '').title()} saved successfully.",
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

        # Keep modal open - return no_update for save success store
        return no_update, success_alert

    except Exception as e:
        logger.error(f"Error saving comprehensive mappings: {e}")
        error_alert = dbc.Alert(
            html.Div(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    html.Span(
                        [
                            html.Strong("Save Failed"),
                            html.Br(),
                            html.Small(
                                f"Failed to save configuration: {str(e)}",
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
        # Keep modal open
        return no_update, error_alert
