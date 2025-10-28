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
                dbc.ModalTitle("Configure Jira Field Mappings"),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    # Instructions
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "Map your Jira custom fields to the internal fields required for DORA and Flow metrics calculations.",
                        ],
                        color="info",
                        className="mb-4",
                    ),
                    # Loading state
                    dcc.Loading(
                        id="field-mapping-loading",
                        type="default",
                        children=html.Div(id="field-mapping-content"),
                    ),
                    # Status messages
                    html.Div(id="field-mapping-status"),
                    # Hidden store for tracking successful save (triggers modal close)
                    dcc.Store(id="field-mapping-save-success", data=None),
                ],
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="field-mapping-cancel-button",
                        color="secondary",
                        className="me-2",
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
        field_option = {
            "label": f"{field['field_name']} ({field['field_id']})",
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
    field_options = [{"label": "-- Not Mapped --", "value": ""}]

    if standard_fields:
        field_options.append(
            {"label": "─── Standard Jira Fields ───", "value": "_separator_std_"}
        )
        field_options.extend(standard_fields)

    if custom_fields:
        field_options.append(
            {"label": "─── Custom Fields ───", "value": "_separator_custom_"}
        )
        field_options.extend(custom_fields)

    # DORA metrics field mappings
    dora_section = create_metric_section(
        "DORA Metrics",
        "dora",
        [
            (
                "deployment_date",
                "Deployment Date",
                "datetime",
                "When was this deployed to production?",
            ),
            (
                "target_environment",
                "Target Environment",
                "select",
                "Which environment was deployed to? (dev/staging/prod)",
            ),
            (
                "code_commit_date",
                "Code Commit Date",
                "datetime",
                "When was the code committed?",
            ),
            (
                "deployed_to_production_date",
                "Deployed to Production Date",
                "datetime",
                "When did this reach production?",
            ),
            (
                "incident_detected_at",
                "Incident Detected At",
                "datetime",
                "When was the incident first detected?",
            ),
            (
                "incident_resolved_at",
                "Incident Resolved At",
                "datetime",
                "When was the incident resolved?",
            ),
            (
                "deployment_successful",
                "Deployment Successful",
                "checkbox",
                "Was the deployment successful?",
            ),
            (
                "production_impact",
                "Production Impact",
                "select",
                "What was the production impact level?",
            ),
            (
                "incident_related",
                "Incident Related",
                "text",
                "Is this issue related to an incident?",
            ),
        ],
        field_options,
        current_mappings.get("dora", {}),
    )

    # Flow metrics field mappings
    flow_section = create_metric_section(
        "Flow Metrics",
        "flow",
        [
            (
                "flow_item_type",
                "Work Item Type",
                "select",
                "What type of work item is this? (feature/bug/task)",
            ),
            (
                "work_started_date",
                "Work Started Date",
                "datetime",
                "When did work actually start on this item?",
            ),
            (
                "work_completed_date",
                "Work Completed Date",
                "datetime",
                "When was the work completed?",
            ),
            (
                "status_entry_timestamp",
                "Status Entry Timestamp",
                "datetime",
                "When did this item enter the current status?",
            ),
            (
                "active_work_hours",
                "Active Work Hours",
                "number",
                "How many hours of active work?",
            ),
            (
                "flow_time_days",
                "Flow Time (Days)",
                "number",
                "How many days from start to completion?",
            ),
            (
                "flow_efficiency_percent",
                "Flow Efficiency (%)",
                "number",
                "What percentage of time was active work?",
            ),
            (
                "completed_date",
                "Completed Date",
                "datetime",
                "When was this item marked as completed?",
            ),
            ("status", "Status", "select", "What is the current status?"),
        ],
        field_options,
        current_mappings.get("flow", {}),
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

        field_row = dbc.Row(
            [
                # Field label and required type
                dbc.Col(
                    [
                        html.Label(
                            [
                                label,
                                html.Span(
                                    f" ({required_type})",
                                    className="text-muted small",
                                ),
                            ],
                            className="form-label fw-bold",
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
                            value=current_value,
                            placeholder="Type or select Jira field...",
                            className="mb-2",
                            clearable=True,
                            searchable=True,  # Allow typing to search/filter
                            optionHeight=50,  # Taller options for better readability
                            maxHeight=300,  # Limit dropdown height for better UX
                            style={
                                "position": "relative"
                            },  # Ensure proper positioning context
                        ),
                        # Validation message placeholder
                        html.Div(
                            id=f"field-mapping-{metric_type}-{field_id}-validation",
                            className="field-validation-message",
                        ),
                    ],
                    width=12,
                    md=8,
                    style={"overflow": "visible"},  # Allow dropdown to overflow column
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
