"""Field mapping configuration modal UI.

Provides a modal interface for administrators to configure how Jira custom fields
map to internal fields required for DORA and Flow metrics.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import List, Dict, Any


def _reconstruct_namespace_from_source_rule(source_rule: Dict[str, Any]) -> str:
    """Reconstruct namespace string from a parsed SourceRule dict.

    This handles the case where old data was parsed to SourceRule before saving.
    We attempt to reconstruct the original namespace syntax.

    Args:
        source_rule: Dict representation of a SourceRule object

    Returns:
        Reconstructed namespace string, or empty string if reconstruction fails
    """
    try:
        source = source_rule.get("source", {})
        source_type = source.get("type", "")

        if source_type == "changelog_timestamp":
            # Changelog syntax: field:value.DateTime
            field = source.get("field", "")
            to_value = source.get("to_value", "")
            return f"{field}:{to_value}.DateTime" if to_value else field

        elif source_type == "changelog_event":
            # Changelog event: field:value.Occurred
            field = source.get("field", "")
            to_value = source.get("to_value", "")
            return f"{field}:{to_value}.Occurred" if to_value else field

        elif source_type == "field_value":
            # Field value: [project.]field[.property]
            field = source.get("field", "")
            property_path = source.get("property_path")

            # Check for project filter
            filters = source_rule.get("filters", [])
            project_prefix = ""
            for f in filters:
                if f.get("type") == "project":
                    projects = f.get("values", [])
                    if projects and projects != ["*"]:
                        project_prefix = "|".join(projects) + "."
                    elif projects == ["*"]:
                        project_prefix = "*."

            result = project_prefix + field
            if property_path:
                result += "." + property_path

            return result

        # Unknown type - return field if available
        return source.get("field", "")

    except Exception:
        return ""


def extract_field_id_from_namespace(namespace_value: str) -> str:
    """Extract the field ID from namespace syntax.

    Namespace formats supported:
    - "PROJECT.fieldId" → "fieldId"
    - "*.fieldId" → "fieldId"
    - "fieldId" → "fieldId" (no change)
    - "Status:Done.DateTime" → "Status" (changelog syntax - use first part)

    Args:
        namespace_value: Value that may contain namespace syntax

    Returns:
        Extracted field ID suitable for simple dropdown mode
    """
    if not namespace_value:
        return ""

    value = namespace_value.strip()

    # Handle changelog syntax (Status:value) - extract field name before colon
    if ":" in value:
        value = value.split(":")[0]

    # Handle project prefix (PROJECT.field or *.field) - extract field after last dot
    if "." in value:
        value = value.split(".")[-1]

    return value


def create_field_mapping_modal() -> dbc.Modal:
    """Create the field mapping configuration modal.

    Returns:
        dbc.Modal component with field mapping interface
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Configure JIRA Mappings"),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    # Auto-Configure Warning Banner (inline, collapsible)
                    dbc.Collapse(
                        dbc.Alert(
                            [
                                html.P(
                                    [
                                        html.I(
                                            className="fas fa-exclamation-triangle me-2"
                                        ),
                                        "Auto-Configure will overwrite your current configuration with automatically detected values from JIRA.",
                                    ],
                                    className="mb-3",
                                ),
                                html.Div(
                                    [
                                        dbc.Button(
                                            [
                                                html.I(className="fas fa-times me-2"),
                                                "Cancel",
                                            ],
                                            id="auto-configure-cancel-inline",
                                            color="secondary",
                                            size="sm",
                                            className="me-2",
                                        ),
                                        dbc.Button(
                                            [
                                                html.I(className="fas fa-check me-2"),
                                                "Yes, Auto-Configure Now",
                                            ],
                                            id="auto-configure-confirm-button",
                                            color="dark",
                                            size="sm",
                                        ),
                                    ],
                                    className="d-flex justify-content-end",
                                ),
                            ],
                            color="warning",
                            className="mb-3",
                        ),
                        id="auto-configure-warning-banner",
                        is_open=False,
                    ),
                    # Tabs for different configuration sections
                    dbc.Tabs(
                        id="mappings-tabs",
                        active_tab="tab-projects",
                        children=[
                            dbc.Tab(label="Projects", tab_id="tab-projects"),
                            dbc.Tab(label="Fields", tab_id="tab-fields"),
                            dbc.Tab(label="Types", tab_id="tab-types"),
                            dbc.Tab(label="Status", tab_id="tab-status"),
                            dbc.Tab(label="Environment", tab_id="tab-environment"),
                        ],
                        className="mb-3",
                    ),
                    # Loading state
                    dcc.Loading(
                        id="field-mapping-loading",
                        type="default",
                        children=html.Div(id="field-mapping-content"),
                    ),
                    # Metadata loading overlay - shown while fetching JIRA metadata
                    html.Div(
                        [
                            html.Div(
                                [
                                    dbc.Spinner(
                                        color="primary",
                                        size="lg",
                                        spinner_class_name="mb-3",
                                    ),
                                    html.H5(
                                        "Loading JIRA Metadata...",
                                        className="text-primary mb-2",
                                    ),
                                    html.P(
                                        "Fetching fields, projects, and statuses from JIRA.",
                                        className="text-muted small",
                                    ),
                                ],
                                className="text-center py-5",
                            ),
                        ],
                        id="metadata-loading-overlay",
                        className="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center",
                        style={
                            "zIndex": 1000,
                            "visibility": "hidden",
                            "opacity": 0,
                            "pointerEvents": "none",
                            "backgroundColor": "rgba(255, 255, 255, 0.95)",
                        },
                    ),
                    # Status messages
                    html.Div(id="field-mapping-status"),
                    # Hidden stores (jira-metadata-store moved to app level in layout.py)
                    dcc.Store(id="field-mapping-save-success", data=None),
                    dcc.Store(
                        id="namespace-autocomplete-data",
                        storage_type="memory",
                        data=None,
                    ),  # Pre-built autocomplete dataset for clientside filtering
                    dcc.Store(
                        id="namespace-collected-values",
                        storage_type="memory",
                        data={},
                    ),  # Collected namespace input values at save time
                    dcc.Store(
                        id="field-mapping-state-store",
                        storage_type="memory",
                        data={},
                    ),  # Real-time state tracking - survives tab switches
                    dcc.Store(
                        id="auto-configure-refresh-trigger",
                        data=0,
                    ),  # Trigger tab re-render after auto-configure
                    dcc.Store(
                        id="validate-mappings-trigger",
                        storage_type="memory",
                        data=0,
                    ),  # Trigger validation without saving
                    dcc.Store(
                        id="fetched-field-values-store",
                        storage_type="memory",
                        data={},
                    ),  # Cache for dynamically fetched field values (effort_category, affected_environment)
                    dcc.Store(
                        id="field-fetch-trigger",
                        storage_type="memory",
                        data={"effort_category": None, "affected_environment": None},
                    ),  # Trigger field value fetching when namespace inputs change
                ],
                style={"position": "relative"},  # Required for overlay positioning
            ),
            dbc.ModalFooter(
                [
                    # Standard web pattern: Close on left (safe exit), actions grouped on right
                    dbc.Button(
                        "Close",
                        id="field-mapping-cancel-button",
                        color="secondary",
                        outline=True,  # Outline style for less prominence
                        className="me-auto",  # Push to left, creates visual separation
                    ),
                    # Action buttons grouped on right: Auto-Configure → Validate → Save
                    # Note: Metadata is now fetched automatically when modal opens
                    dbc.Button(
                        [html.I(className="fas fa-magic me-2"), "Auto-Configure"],
                        id="auto-configure-button",
                        color="info",
                        outline=True,  # Less prominent than Save
                        className="me-2",
                        disabled=True,  # Enabled after metadata loads
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-check-circle me-2"), "Validate"],
                        id="validate-mappings-button",
                        color="success",
                        outline=True,  # Less prominent than Save
                        className="me-2",
                        disabled=True,  # Enabled after metadata loads
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save Mappings"],
                        id="field-mapping-save-button",
                        color="primary",
                        disabled=True,  # Enabled after metadata loads
                    ),
                ]
            ),
        ],
        id="field-mapping-modal",
        size="xl",
        is_open=False,
        backdrop="static",  # Prevent closing by clicking outside
        centered=True,
    )

    return modal


def create_field_mapping_form(
    available_fields: List[Dict[str, Any]],
    current_mappings: Dict[str, Dict[str, str]],
) -> html.Div:
    """Create the field mapping form with namespace inputs for all required fields.

    Args:
        available_fields: List of available Jira fields with metadata
        current_mappings: Currently configured field mappings

    Returns:
        html.Div containing the complete field mapping form
    """
    # Separate standard fields from custom fields for better UX
    standard_fields = []
    custom_fields = []

    for field in available_fields:
        # Include field type in dropdown label for better clarity
        field_type = field.get("field_type", "unknown")
        field_option = {
            "label": f"{field['field_name']} ({field['field_id']}) - [{field_type}]",
            "value": field["field_id"],
        }
        if field["field_id"].startswith("customfield_"):
            custom_fields.append(field_option)
        else:
            standard_fields.append(field_option)

    # Sort each group alphabetically
    standard_fields.sort(key=lambda x: x["label"])
    custom_fields.sort(key=lambda x: x["label"])

    # Prepare field options with standard fields first (easier to find)
    # Note: No "Not Mapped" option needed - clearable dropdown handles empty state
    field_options = []

    if standard_fields:
        field_options.append(
            {
                "label": "─── Standard Jira Fields ───",
                "value": "_separator_std_",
                "disabled": True,
            }
        )
        field_options.extend(standard_fields)

    if custom_fields:
        field_options.append(
            {
                "label": "─── Custom Fields ───",
                "value": "_separator_custom_",
                "disabled": True,
            }
        )
        field_options.extend(custom_fields)

    # Add current mapped field IDs to options if not already present (ensures they display)
    existing_field_ids = {
        opt["value"]
        for opt in field_options
        if opt.get("value") and not opt.get("disabled")
    }

    # Collect all currently mapped field IDs from all field mapping sections
    all_current_field_ids = set()
    field_mappings_dict = current_mappings.get("field_mappings", {})

    # Iterate through all field mapping sections (dora, flow, general)
    for section_name in ["dora", "flow", "general"]:
        section_mappings = field_mappings_dict.get(section_name, {})
        if isinstance(section_mappings, dict):
            # Add all field IDs (values) from this section
            all_current_field_ids.update(
                v for v in section_mappings.values() if isinstance(v, str)
            )

    # Add any missing current field IDs to options
    for field_id in all_current_field_ids:
        if field_id and field_id not in existing_field_ids:
            # Add to appropriate section based on field ID type
            if field_id.startswith("customfield_"):
                field_options.append({"label": field_id, "value": field_id})
            else:
                # Insert standard fields before custom fields separator
                insert_pos = next(
                    (
                        i
                        for i, opt in enumerate(field_options)
                        if opt.get("value") == "_separator_custom_"
                    ),
                    len(field_options),
                )
                field_options.insert(insert_pos, {"label": field_id, "value": field_id})

    # DORA metrics field mappings
    dora_section = create_metric_section(
        "DORA Metrics",
        "dora",
        [
            (
                "deployment_date",
                "Deployment Date",
                "datetime",
                "When deployment occurred | REQUIRED for Deployment Frequency | Use: fixVersions OR customfield_XXXXX (datetime)",
            ),
            (
                "deployment_successful",
                "Deployment Successful",
                "checkbox",
                "Filter failed deployments | OPTIONAL - if empty, assumes all successful | Type: checkbox/select",
            ),
            (
                "code_commit_date",
                "Code Commit Date",
                "datetime",
                "When code was committed | OPTIONAL for Lead Time for Changes | Type: datetime",
            ),
            (
                "incident_detected_at",
                "Incident Detected At",
                "datetime",
                "When production issue found | REQUIRED for MTTR | Typical field: created | Type: datetime",
            ),
            (
                "incident_resolved_at",
                "Incident Resolved At",
                "datetime",
                "When fix deployed | REQUIRED for MTTR | Options: resolutiondate (team fix time) or fixVersions (deployment to production)",
            ),
            (
                "change_failure",
                "Change Failure",
                "select",
                "Deployment failure indicator | REQUIRED for CFR | Syntax: field=Value | Example: customfield_12708=Yes",
            ),
            (
                "affected_environment",
                "Affected Environment",
                "select",
                "Production bugs filter | REQUIRED for MTTR | Syntax: field=Value or field=Value1|Value2 | Example: customfield_11309=PROD",
            ),
            (
                "target_environment",
                "Target Environment",
                "select",
                "Deployment target filter | OPTIONAL | Syntax: field=Value | Example: customfield_11309=PROD|Production",
            ),
            (
                "severity_level",
                "Severity Level",
                "select",
                "Incident priority/severity | OPTIONAL for impact analysis | Typical field: priority | Type: select",
            ),
        ],
        field_options,
        current_mappings.get("field_mappings", {}).get("dora", {}),  # type: ignore
    )

    # General fields used across all features (velocity, budget, flow metrics, bug analysis)
    general_section = create_metric_section(
        "General Fields",
        "general",
        [
            (
                "completed_date",
                "Completion Date",
                "datetime",
                "When issue was completed/resolved | REQUIRED for Velocity, Budget, Flow Velocity | Supports nested fields: field.subfield | Type: datetime",
            ),
            (
                "created_date",
                "Creation Date",
                "datetime",
                "When issue was created | REQUIRED for Scope Tracking, Created Items | Standard field: created | Type: datetime",
            ),
            (
                "updated_date",
                "Updated Date",
                "datetime",
                "When issue was last modified | OPTIONAL for Delta Calculations | Standard field: updated | Type: datetime",
            ),
            (
                "estimate",
                "Estimate",
                "number",
                "Story points or effort estimate | OPTIONAL for points tracking | Type: number",
            ),
            (
                "sprint_field",
                "Sprint",
                "array",
                "Sprint field for Agile/Scrum boards | OPTIONAL for Sprint Tracker | Typically customfield_10020 | Type: array",
            ),
            (
                "parent_field",
                "Parent/Epic Link",
                "any",
                "Parent epic/feature field | OPTIONAL for Active Work Timeline | Modern JIRA: parent (standard) | Legacy JIRA: customfield_10006 or customfield_10014 (Epic Link) | Type: any (object, string, or custom)",
            ),
        ],
        field_options,
        current_mappings.get("field_mappings", {}).get("general", {}),  # type: ignore
    )

    # Flow metrics field mappings
    flow_section = create_metric_section(
        "Flow Metrics",
        "flow",
        [
            (
                "flow_item_type",
                "Flow Item Type",
                "select",
                "Work category | REQUIRED for Flow Distribution | Typical field: issuetype | Type: select",
            ),
            (
                "status",
                "Status",
                "select",
                "Current work status | REQUIRED for Flow Load and Flow State | Typical field: status | Type: select",
            ),
            (
                "effort_category",
                "Effort Category",
                "select",
                "Secondary work classification | OPTIONAL for enhanced Flow Distribution | Type: select",
            ),
            # NOTE: work_started_date is obsolete.
            # Flow Time now uses flow_start_statuses and flow_end_statuses lists
            # from Project Classification to find status transitions in changelog.
            # NOTE: completed_date moved to General Fields section (used by multiple features)
        ],
        field_options,
        current_mappings.get("field_mappings", {}).get("flow", {}),  # type: ignore
    )

    return html.Div(
        [
            general_section,
            html.Hr(className="my-4"),
            dora_section,
            html.Hr(className="my-4"),
            flow_section,
        ],
        className="field-mapping-form",
    )


def create_metric_section(
    title: str,
    metric_type: str,
    fields: List[tuple],
    field_options: List[Dict],
    current_mappings: Dict[str, str],
) -> dbc.Card:
    """Create a section for a specific metric type (DORA or Flow).

    Uses namespace syntax inputs with autocomplete for field mapping.
    Supports project scoping (e.g., PROJECT.status:Done.DateTime) and
    extractors for changelog fields.

    Args:
        title: Section title (e.g., "DORA Metrics")
        metric_type: Metric type identifier ("dora" or "flow")
        fields: List of (field_id, label, required_type, help_text) tuples
        field_options: Available Jira field options (for validation reference)
        current_mappings: Current mappings for this metric type

    Returns:
        dbc.Card containing the field mapping controls
    """
    field_rows = []

    for field_id, label, required_type, help_text in fields:
        raw_value = current_mappings.get(field_id, "")

        # Handle case where value is a dict (parsed SourceRule) - extract original string
        # This can happen if old data was parsed before save
        if isinstance(raw_value, dict):
            # Try to reconstruct namespace string from SourceRule
            raw_value = _reconstruct_namespace_from_source_rule(raw_value)

        current_value = raw_value

        # Determine if field is required based on help text
        is_required = "REQUIRED" in help_text
        label_class = "form-label fw-bold" if is_required else "form-label"

        # Add required indicator to label
        label_content = [
            label,
            html.Span(" *", className="text-danger") if is_required else None,
        ]

        # Namespace syntax input with CLIENTSIDE autocomplete
        # All filtering happens in browser via namespace_autocomplete_clientside.js
        # No server round-trips = no focus loss
        #
        # NOTE: We use dcc.Input but read values via clientside JS (collectNamespaceValues)
        # which reads directly from DOM. This avoids React state sync issues when
        # JavaScript modifies the input value during autocomplete selection.
        field_input = html.Div(
            [
                dcc.Input(
                    id={
                        "type": "namespace-field-input",
                        "metric": metric_type,
                        "field": field_id,
                    },
                    type="text",
                    value=current_value,
                    placeholder="Type to search fields... (e.g., status:Done.DateTime)",
                    className="form-control namespace-input",
                    autoComplete="off",
                    # Disable debounce to ensure immediate DOM updates
                    debounce=False,
                    persistence=False,  # Don't persist - we manage state ourselves
                ),
                # Autocomplete dropdown - populated by clientside callback
                html.Div(
                    id={
                        "type": "namespace-suggestions",
                        "metric": metric_type,
                        "field": field_id,
                    },
                    className="namespace-suggestions-dropdown",
                ),
            ],
            className="namespace-input-container position-relative mb-2",
        )

        field_row = dbc.Row(
            [
                # Field label and help text
                dbc.Col(
                    [
                        html.Label(
                            label_content,
                            className=label_class,
                        ),
                        html.P(
                            [
                                html.I(className="fas fa-info-circle me-1 text-info"),
                                help_text,
                            ],
                            className="text-muted small mb-2",
                        ),
                    ],
                    width=12,
                    md=4,
                ),
                # Field input (dropdown or namespace input)
                dbc.Col(
                    [
                        field_input,
                        # Validation message placeholder (pattern-matching ID for callback)
                        html.Div(
                            id={
                                "type": "field-validation-message",
                                "metric": metric_type,
                                "field": field_id,
                            },
                            className="field-validation-message",
                        ),
                    ],
                    width=12,
                    md=8,
                ),
            ],
            className="mb-3",
        )
        field_rows.append(field_row)

    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(title, className="mb-0"),
                className="bg-light",
            ),
            dbc.CardBody(field_rows),
        ],
        className="mb-3",
    )


def create_validation_message(
    is_valid: bool,
    message: str,
) -> dbc.Alert:
    """Create a validation message for a field mapping.

    Args:
        is_valid: Whether the mapping is valid
        message: Validation message to display

    Returns:
        dbc.Alert with validation feedback
    """
    if is_valid:
        return dbc.Alert(
            [html.I(className="fas fa-check-circle me-2"), message],
            color="success",
            className="mb-0 py-1 small",
        )
    else:
        return dbc.Alert(
            [html.I(className="fas fa-exclamation-triangle me-2"), message],
            color="warning",
            className="mb-0 py-1 small",
        )


def create_field_mapping_success_alert() -> dbc.Alert:
    """Create success alert for field mappings saved."""
    return dbc.Alert(
        [
            html.I(className="fas fa-check-circle me-2"),
            "Field mappings saved successfully! Metrics will recalculate using new mappings.",
        ],
        color="success",
        dismissable=True,
        duration=4000,
    )


def create_field_mapping_error_alert(error_message: str) -> dbc.Alert:
    """Create error alert for field mapping save failure.

    Args:
        error_message: Error message to display

    Returns:
        dbc.Alert with error message
    """
    return dbc.Alert(
        [
            html.I(className="fas fa-exclamation-circle me-2"),
            f"Failed to save field mappings: {error_message}",
        ],
        color="danger",
        dismissable=True,
    )
