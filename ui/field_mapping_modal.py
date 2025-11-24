"""Field mapping configuration modal UI.

Provides a modal interface for administrators to configure how Jira custom fields
map to internal fields required for DORA and Flow metrics.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import List, Dict, Any


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
                    # Instructions
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "Configure how your JIRA instance maps to the application. Use tabs to navigate between different configuration categories.",
                        ],
                        color="info",
                        className="mb-3",
                    ),
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
                    # Status messages
                    html.Div(id="field-mapping-status"),
                    # Hidden stores
                    dcc.Store(id="field-mapping-save-success", data=None),
                    dcc.Store(id="jira-metadata-store", data=None),  # Cache metadata
                    dcc.Store(
                        id="field-mapping-state-store",
                        storage_type="memory",
                        data={},
                    ),  # Real-time state tracking - survives tab switches
                ],
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
                    # Action buttons grouped on right: Auto-Configure → Save
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
                        [html.I(className="fas fa-save me-2"), "Save Mappings"],
                        id="field-mapping-save-button",
                        color="primary",
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
    """Create the field mapping form with dropdowns for all required fields.

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

    # Collect all currently mapped field IDs from both dora and flow sections
    all_current_field_ids = set()
    field_mappings_dict = current_mappings.get("field_mappings", {})

    # Iterate through dora and flow sections
    for section_name in ["dora", "flow"]:
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
                "When deployment occurred | REQUIRED for Deployment Frequency | Typical field: customfield_XXXXX | Type: datetime",
            ),
            (
                "deployment_successful",
                "Deployment Successful",
                "checkbox",
                "Deployment success/failure indicator | OPTIONAL for enhanced Change Failure Rate | Type: checkbox",
            ),
            (
                "code_commit_date",
                "Code Commit Date",
                "datetime",
                "When code was committed | OPTIONAL for Lead Time for Changes | Type: datetime",
            ),
            (
                "deployed_to_production_date",
                "Deployed to Production",
                "datetime",
                "Production deployment timestamp | OPTIONAL for Lead Time for Changes | Type: datetime",
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
                "When issue fixed in production | REQUIRED for MTTR | Typical field: resolutiondate | Type: datetime",
            ),
            (
                "change_failure",
                "Change Failure",
                "select",
                "Deployment failure indicator | REQUIRED for Change Failure Rate | Values: Yes/No/None | Type: select",
            ),
            (
                "affected_environment",
                "Affected Environment",
                "select",
                "Environment affected by incident | REQUIRED for production bug filtering (MTTR) | Type: select",
            ),
            (
                "target_environment",
                "Target Environment",
                "select",
                "Deployment target environment | OPTIONAL for environment-specific metrics | Type: select",
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
                "work_started_date",
                "Work Started Date",
                "datetime",
                "When work began | OPTIONAL - calculated from first WIP status if empty | Type: datetime",
            ),
            (
                "work_completed_date",
                "Work Completed Date",
                "datetime",
                "When work finished | REQUIRED for Flow Velocity, Flow Time, Flow Distribution | Typical field: resolutiondate | Type: datetime",
            ),
            (
                "effort_category",
                "Effort Category",
                "select",
                "Secondary work classification | OPTIONAL for enhanced Flow Distribution | Type: select",
            ),
            (
                "estimate",
                "Estimate",
                "number",
                "Story points or effort | OPTIONAL for capacity planning | Typical field: Story Points | Type: number",
            ),
        ],
        field_options,
        current_mappings.get("field_mappings", {}).get("flow", {}),  # type: ignore
    )

    return html.Div(
        [
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

    Args:
        title: Section title (e.g., "DORA Metrics")
        metric_type: Metric type identifier ("dora" or "flow")
        fields: List of (field_id, label, required_type, help_text) tuples
        field_options: Available Jira field options for dropdowns
        current_mappings: Current mappings for this metric type

    Returns:
        dbc.Card containing the field mapping controls
    """
    field_rows = []

    for field_id, label, required_type, help_text in fields:
        current_value = current_mappings.get(field_id, "")

        # Ensure options are a list of dicts for Dash compatibility
        dash_options = []
        for opt in field_options:
            if isinstance(opt, dict) and "label" in opt and "value" in opt:
                dash_options.append({"label": opt["label"], "value": opt["value"]})
            else:
                dash_options.append(opt)

        # Determine if field is required based on help text
        is_required = "REQUIRED" in help_text
        label_class = "form-label fw-bold" if is_required else "form-label"

        # Add required indicator to label
        label_content = [
            label,
            html.Span(" *", className="text-danger") if is_required else None,
        ]

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
                            help_text,
                            className="text-muted small mb-2",
                        ),
                    ],
                    width=12,
                    md=4,
                ),
                # Dropdown for selecting Jira field
                dbc.Col(
                    [
                        dcc.Dropdown(
                            id={
                                "type": "field-mapping-dropdown",
                                "metric": metric_type,
                                "field": field_id,
                            },
                            options=dash_options,
                            value=[current_value]
                            if current_value
                            else [],  # Multi expects list
                            placeholder="Type or select Jira field...",
                            className="mb-2",
                            clearable=True,
                            searchable=True,
                            optionHeight=50,
                            maxHeight=300,
                            multi=True,  # Enable multi-select for consistent styling
                        ),
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
