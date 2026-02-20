"""Validation helper functions for field mapping.

Provides comprehensive validation and alert generation for all configuration tabs.
"""

import logging

import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)


def _validate_all_tabs(state_data: dict, field_validation_errors: list) -> dict:
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
            "summary": {
                "fields": int,
                "statuses": int,
                "projects": int,
                "issue_types": int,
            },
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
                    "field": (
                        f"{err.get('metric', '').upper()} > "
                        f"{err.get('field', '').replace('_', ' ').title()}"
                    ),
                    "error": err.get("error", "Invalid value"),
                }
            )

    # Count configured fields (from namespace values in field_mappings)
    field_mappings = state_data.get("field_mappings", {})
    for metric in ["dora", "flow", "general"]:
        if metric in field_mappings:
            summary["fields"] += len([v for v in field_mappings[metric].values() if v])

    # Validate REQUIRED fields are mapped
    # These fields are marked as REQUIRED in the UI (field_mapping_modal.py)
    required_fields = {
        "general": {
            "completed_date": (
                "Completion Date (required for Velocity, Budget, Flow Velocity)"
            ),
            "created_date": (
                "Creation Date (required for Scope Tracking, Created Items)"
            ),
        },
        "dora": {
            "deployment_date": "Deployment Date (required for Deployment Frequency)",
            "incident_detected_at": "Incident Detected At (required for MTTR)",
            "incident_resolved_at": "Incident Resolved At (required for MTTR)",
            "change_failure": "Change Failure (required for CFR)",
            "affected_environment": "Affected Environment (required for MTTR)",
        },
        "flow": {
            "flow_item_type": "Flow Item Type (required for Flow Distribution)",
            "status": "Status (required for Flow Load and Flow State)",
        },
    }

    # Check each required field
    for metric, fields in required_fields.items():
        metric_mappings = field_mappings.get(metric, {})
        for field_id, field_label in fields.items():
            if not metric_mappings.get(field_id):
                # Field not mapped - add warning (not error, to allow partial config)
                warnings.append(
                    {
                        "tab": "Fields",
                        "field": field_label,
                        "warning": f"Required field not mapped: {field_label}",
                    }
                )

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
                "warning": (
                    "No completion statuses selected. Required for metrics calculation."
                ),
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
                    "warning": (
                        "Active statuses not in WIP: "
                        f"{', '.join(active_not_in_wip[:3])}"
                        f"{'...' if len(active_not_in_wip) > 3 else ''}"
                    ),
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
                    "warning": (
                        "Flow Start statuses not in WIP: "
                        f"{', '.join(flow_start_not_in_wip[:3])}"
                        f"{'...' if len(flow_start_not_in_wip) > 3 else ''}"
                    ),
                }
            )

    # CRITICAL: Validate WIP statuses don't include completion statuses
    if wip_statuses and flow_end_statuses:
        wip_set = set(wip_statuses)
        end_set = set(flow_end_statuses)
        completion_in_wip = wip_set & end_set
        if completion_in_wip:
            errors.append(
                {
                    "tab": "Status",
                    "field": "WIP Statuses",
                    "error": (
                        "WIP statuses MUST NOT include completion statuses. "
                        f"Found: {', '.join(completion_in_wip)}. "
                        "This causes Flow Load to incorrectly count completed "
                        "items as WIP."
                    ),
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
                "warning": (
                    "No projects selected. Select Development or DevOps projects."
                ),
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
                "warning": (
                    "No Feature or Defect types mapped. Required for Flow Distribution."
                ),
            }
        )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def _build_comprehensive_validation_alert(validation_result: dict):
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

    # Build alert content with improved layout.
    # Wrap in a single div to prevent column layout.
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
    # Use timestamp in ID to force complete re-render each time validation runs
    import time

    timestamp = int(time.time() * 1000)  # Millisecond timestamp

    return html.Div(
        dbc.Alert(
            html.Div(content_parts),
            color=color,
            dismissable=True,
            id=f"validation-result-alert-{timestamp}",
        ),
        id="validation-result-container",  # Stable container ID for positioning
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
                            "Validation Failed - "
                            f"{len(validation_errors)} error(s) found"
                        ),
                    ],
                    className="d-flex align-items-center mb-2",
                ),
                html.Ul(error_items, className="mb-2 ps-4"),
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1"),
                        "Fix the errors above before saving. "
                        "Use autocomplete to select valid values.",
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
