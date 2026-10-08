from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html


def _reconstruct_namespace_from_source_rule(source_rule: dict[str, Any]) -> str:

    try:
        source = source_rule.get("source", {})
        source_type = source.get("type", "")

        if source_type == "changelog_timestamp":
            field = source.get("field", "")
            to_value = source.get("to_value", "")
            return f"{field}:{to_value}.DateTime" if to_value else field

        elif source_type == "changelog_event":
            field = source.get("field", "")
            to_value = source.get("to_value", "")
            return f"{field}:{to_value}.Occurred" if to_value else field

        elif source_type == "field_value":
            field = source.get("field", "")
            property_path = source.get("property_path")

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

        return source.get("field", "")

    except Exception:
        return ""


def extract_field_id_from_namespace(namespace_value: str) -> str:

    if not namespace_value:
        return ""

    value = namespace_value.strip()

    if ":" in value:
        value = value.split(":")[0]

    if "." in value:
        value = value.split(".")[-1]

    return value


def create_field_mapping_modal() -> dbc.Modal:

    modal = dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Configure JIRA Mappings"),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    dbc.Collapse(
                        dbc.Alert(
                            [
                                html.P(
                                    [
                                        html.I(
                                            className="fas fa-exclamation-triangle me-2"
                                        ),
                                        "Auto-Configure will overwrite your "
                                        "current configuration with automatically "
                                        "detected values from JIRA.",
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
                    dcc.Loading(
                        id="field-mapping-loading",
                        type="default",
                        children=html.Div(id="field-mapping-content"),
                    ),
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
                                        "Fetching fields, projects, and "
                                        "statuses from JIRA.",
                                        className="text-muted small",
                                    ),
                                ],
                                className="text-center py-5",
                            ),
                        ],
                        id="metadata-loading-overlay",
                        className=(
                            "position-absolute top-0 start-0 w-100 h-100 "
                            "d-flex align-items-center "
                            "justify-content-center"
                        ),
                        style={
                            "zIndex": 1000,
                            "visibility": "hidden",
                            "opacity": 0,
                            "pointerEvents": "none",
                            "backgroundColor": "rgba(255, 255, 255, 0.95)",
                        },
                    ),
                    html.Div(id="field-mapping-status"),
                    dcc.Store(id="field-mapping-save-success", data=None),
                    dcc.Store(
                        id="namespace-autocomplete-data",
                        storage_type="memory",
                        data=None,
                    ),
                    dcc.Store(
                        id="namespace-collected-values",
                        storage_type="memory",
                        data={},
                    ),
                    dcc.Store(
                        id="field-mapping-state-store",
                        storage_type="memory",
                        data={},
                    ),
                    dcc.Store(
                        id="auto-configure-refresh-trigger",
                        data=0,
                    ),
                    dcc.Store(
                        id="validate-mappings-trigger",
                        storage_type="memory",
                        data=0,
                    ),
                    dcc.Store(
                        id="fetched-field-values-store",
                        storage_type="memory",
                        data={},
                    ),
                    dcc.Store(
                        id="field-fetch-trigger",
                        storage_type="memory",
                        data={"effort_category": None, "affected_environment": None},
                    ),
                ],
                style={"position": "relative"},
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Close",
                        id="field-mapping-cancel-button",
                        color="secondary",
                        outline=True,
                        className="me-auto",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-magic me-2"), "Auto-Configure"],
                        id="auto-configure-button",
                        color="info",
                        outline=True,
                        className="me-2",
                        disabled=True,
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-check-circle me-2"), "Validate"],
                        id="validate-mappings-button",
                        color="success",
                        outline=True,
                        className="me-2",
                        disabled=True,
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save Mappings"],
                        id="field-mapping-save-button",
                        color="primary",
                        disabled=True,
                    ),
                ]
            ),
        ],
        id="field-mapping-modal",
        size="xl",
        is_open=False,
        backdrop="static",
        centered=True,
    )

    return modal


def create_field_mapping_form(
    available_fields: list[dict[str, Any]],
    current_mappings: dict[str, dict[str, str]],
) -> html.Div:

    standard_fields = []
    custom_fields = []

    for field in available_fields:
        field_type = field.get("field_type", "unknown")
        field_option = {
            "label": f"{field['field_name']} ({field['field_id']}) - [{field_type}]",
            "value": field["field_id"],
        }
        if field["field_id"].startswith("customfield_"):
            custom_fields.append(field_option)
        else:
            standard_fields.append(field_option)

    standard_fields.sort(key=lambda x: x["label"])
    custom_fields.sort(key=lambda x: x["label"])

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

    existing_field_ids = {
        opt["value"]
        for opt in field_options
        if opt.get("value") and not opt.get("disabled")
    }

    dora_deployment_date_help = (
        "When deployment occurred | REQUIRED for Deployment Frequency | "
        "Use: fixVersions OR customfield_XXXXX (datetime)"
    )
    dora_deployment_success_help = (
        "Filter failed deployments | OPTIONAL - if empty, assumes all successful "
        "| Type: checkbox/select"
    )
    dora_commit_date_help = (
        "When code was committed | OPTIONAL for Lead Time for Changes | Type: datetime"
    )
    dora_incident_detected_help = (
        "When production issue found | REQUIRED for MTTR | "
        "Typical field: created | Type: datetime"
    )
    dora_incident_resolved_help = (
        "When fix deployed | REQUIRED for MTTR | Options: resolutiondate "
        "(team fix time) or fixVersions (deployment to production)"
    )
    dora_change_failure_help = (
        "Deployment failure indicator | REQUIRED for CFR | "
        "Syntax: field=Value | Example: customfield_12708=Yes"
    )
    dora_affected_environment_help = (
        "Production bugs filter | REQUIRED for MTTR | Syntax: field=Value "
        "or field=Value1|Value2 | Example: customfield_11309=PROD"
    )
    dora_target_environment_help = (
        "Deployment target filter | OPTIONAL | Syntax: field=Value "
        "| Example: customfield_11309=PROD|Production"
    )
    dora_severity_help = (
        "Incident priority/severity | OPTIONAL for impact analysis "
        "| Typical field: priority | Type: select"
    )

    general_completed_date_help = (
        "When issue was completed/resolved | REQUIRED for Velocity, Budget, "
        "Flow Velocity | Supports nested fields: field.subfield | Type: datetime"
    )
    general_created_date_help = (
        "When issue was created | REQUIRED for Scope Tracking, Created Items "
        "| Standard field: created | Type: datetime"
    )
    general_updated_date_help = (
        "When issue was last modified | OPTIONAL for Delta Calculations "
        "| Standard field: updated | Type: datetime"
    )
    general_estimate_help = (
        "Story points or effort estimate | OPTIONAL for points tracking | Type: number"
    )
    general_sprint_help = (
        "Sprint field for Agile/Scrum boards | OPTIONAL for Sprint Tracker "
        "| Typically customfield_10020 | Type: array"
    )
    general_parent_help = (
        "Parent epic/feature field | OPTIONAL for Active Work Timeline | "
        "Modern JIRA: parent (standard) | Legacy JIRA: customfield_10006 "
        "or customfield_10014 (Epic Link) | Type: any "
        "(object, string, or custom)"
    )

    flow_item_type_help = (
        "Work category | REQUIRED for Flow Distribution | "
        "Typical field: issuetype | Type: select"
    )
    flow_status_help = (
        "Current work status | REQUIRED for Flow Load and Flow State "
        "| Typical field: status | Type: select"
    )
    flow_effort_category_help = (
        "Secondary work classification | OPTIONAL for enhanced Flow Distribution "
        "| Type: select"
    )

    all_current_field_ids = set()
    field_mappings_dict = current_mappings.get("field_mappings", {})

    for section_name in ["dora", "flow", "general"]:
        section_mappings = field_mappings_dict.get(section_name, {})
        if isinstance(section_mappings, dict):
            all_current_field_ids.update(
                v for v in section_mappings.values() if isinstance(v, str)
            )

    for field_id in all_current_field_ids:
        if field_id and field_id not in existing_field_ids:
            if field_id.startswith("customfield_"):
                field_options.append({"label": field_id, "value": field_id})
            else:
                insert_pos = next(
                    (
                        i
                        for i, opt in enumerate(field_options)
                        if opt.get("value") == "_separator_custom_"
                    ),
                    len(field_options),
                )
                field_options.insert(insert_pos, {"label": field_id, "value": field_id})

    dora_section = create_metric_section(
        "DORA Metrics",
        "dora",
        [
            (
                "deployment_date",
                "Deployment Date",
                "datetime",
                dora_deployment_date_help,
            ),
            (
                "deployment_successful",
                "Deployment Successful",
                "checkbox",
                dora_deployment_success_help,
            ),
            (
                "code_commit_date",
                "Code Commit Date",
                "datetime",
                dora_commit_date_help,
            ),
            (
                "incident_detected_at",
                "Incident Detected At",
                "datetime",
                dora_incident_detected_help,
            ),
            (
                "incident_resolved_at",
                "Incident Resolved At",
                "datetime",
                dora_incident_resolved_help,
            ),
            (
                "change_failure",
                "Change Failure",
                "select",
                dora_change_failure_help,
            ),
            (
                "affected_environment",
                "Affected Environment",
                "select",
                dora_affected_environment_help,
            ),
            (
                "target_environment",
                "Target Environment",
                "select",
                dora_target_environment_help,
            ),
            (
                "severity_level",
                "Severity Level",
                "select",
                dora_severity_help,
            ),
        ],
        field_options,
        current_mappings.get("field_mappings", {}).get("dora", {}),  # type: ignore
    )

    general_section = create_metric_section(
        "General Fields",
        "general",
        [
            (
                "completed_date",
                "Completion Date",
                "datetime",
                general_completed_date_help,
            ),
            (
                "created_date",
                "Creation Date",
                "datetime",
                general_created_date_help,
            ),
            (
                "updated_date",
                "Updated Date",
                "datetime",
                general_updated_date_help,
            ),
            (
                "estimate",
                "Estimate",
                "number",
                general_estimate_help,
            ),
            (
                "sprint_field",
                "Sprint",
                "array",
                general_sprint_help,
            ),
            (
                "parent_field",
                "Parent/Epic Link",
                "any",
                general_parent_help,
            ),
        ],
        field_options,
        current_mappings.get("field_mappings", {}).get("general", {}),  # type: ignore
    )

    flow_section = create_metric_section(
        "Flow Metrics",
        "flow",
        [
            (
                "flow_item_type",
                "Flow Item Type",
                "select",
                flow_item_type_help,
            ),
            (
                "status",
                "Status",
                "select",
                flow_status_help,
            ),
            (
                "effort_category",
                "Effort Category",
                "select",
                flow_effort_category_help,
            ),
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
    fields: list[tuple],
    field_options: list[dict],
    current_mappings: dict[str, str],
) -> dbc.Card:

    field_rows = []

    for field_id, label, _required_type, help_text in fields:
        raw_value = current_mappings.get(field_id, "")

        if isinstance(raw_value, dict):
            raw_value = _reconstruct_namespace_from_source_rule(raw_value)

        current_value = raw_value

        is_required = "REQUIRED" in help_text
        label_class = "form-label fw-bold" if is_required else "form-label"

        label_content = [
            label,
            html.Span(" *", className="text-danger") if is_required else None,
        ]

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
                    debounce=False,
                    persistence=False,
                ),
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
                dbc.Col(
                    [
                        field_input,
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
    return dbc.Alert(
        [
            html.I(className="fas fa-check-circle me-2"),
            "Field mappings saved successfully! "
            "Metrics will recalculate using new mappings.",
        ],
        color="success",
        dismissable=True,
        duration=4000,
    )


def create_field_mapping_error_alert(error_message: str) -> dbc.Alert:

    return dbc.Alert(
        [
            html.I(className="fas fa-exclamation-circle me-2"),
            f"Failed to save field mappings: {error_message}",
        ],
        color="danger",
        dismissable=True,
    )
