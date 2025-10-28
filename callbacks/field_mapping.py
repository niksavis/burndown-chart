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
    save_field_mappings,
    get_field_mappings_hash,
    fetch_available_jira_fields,
    validate_field_mapping,
)
from data.metrics_cache import invalidate_cache
from ui.field_mapping_modal import (
    create_field_mapping_form,
    create_field_mapping_success_alert,
    create_field_mapping_error_alert,
)

logger = logging.getLogger(__name__)


@callback(
    Output("field-mapping-modal", "is_open"),
    Input("open-field-mapping-modal", "n_clicks"),
    Input("field-mapping-cancel-button", "n_clicks"),
    Input("field-mapping-save-success", "data"),  # Close only on successful save
    State("field-mapping-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_field_mapping_modal(
    open_clicks: int | None,
    cancel_clicks: int | None,
    save_success: bool | None,
    is_open: bool,
) -> bool:
    """Toggle field mapping modal open/closed.

    Args:
        open_clicks: Open button clicks
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

    # Close on cancel
    if trigger_id == "field-mapping-cancel-button":
        return False

    # Close ONLY on successful save (when save_success is True)
    if trigger_id == "field-mapping-save-success" and save_success is True:
        return False

    # Open when open button clicked
    if trigger_id == "open-field-mapping-modal":
        return True

    return is_open


@callback(
    Output("field-mapping-content", "children"),
    Input("field-mapping-modal", "is_open"),
    prevent_initial_call=True,
)
def populate_field_mapping_form(is_open: bool):
    """Populate field mapping form when modal opens.

    Fetches available Jira fields and current mappings,
    then generates the form dynamically.

    Args:
        is_open: Whether modal is open

    Returns:
        Field mapping form component or loading message
    """
    if not is_open:
        return no_update

    try:
        # Load current field mappings (flat structure from app_settings.json)
        current_mappings_data = load_field_mappings()
        flat_mappings = current_mappings_data.get("field_mappings", {})

        # Convert flat structure to nested structure expected by UI
        # DORA fields
        dora_fields = [
            "deployment_date",
            "deployment_successful",
            "incident_start",
            "incident_resolved",
            "target_environment",
            "code_commit_date",
            "deployed_to_production_date",
            "incident_detected_at",
            "incident_resolved_at",
            "production_impact",
            "incident_related",
        ]
        # Flow fields
        flow_fields = [
            "work_started_date",
            "work_completed_date",
            "work_type",
            "work_item_size",
            "flow_item_type",
            "status_entry_timestamp",
            "active_work_hours",
            "flow_time_days",
            "flow_efficiency_percent",
            "completed_date",
            "status",
        ]

        current_mappings = {
            "dora": {k: v for k, v in flat_mappings.items() if k in dora_fields},
            "flow": {k: v for k, v in flat_mappings.items() if k in flow_fields},
        }

        # Fetch available fields from Jira
        try:
            available_fields = fetch_available_jira_fields()
            logger.info(f"Fetched {len(available_fields)} fields from Jira")
        except Exception as e:
            logger.warning(f"Could not fetch Jira fields, using fallback: {e}")
            # Fallback to mock fields if Jira fetch fails
            available_fields = _get_mock_jira_fields()

        # Create and return the form
        form = create_field_mapping_form(available_fields, current_mappings)
        return form

    except Exception as e:
        logger.error(f"Error populating field mapping form: {e}")
        return dbc.Alert(
            f"Error loading field mappings: {str(e)}",
            color="danger",
        )


@callback(
    [
        Output("field-mapping-status", "children"),
        Output("field-mapping-save-success", "data"),
    ],
    Input("field-mapping-save-button", "n_clicks"),
    State({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    State({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "id"),
    prevent_initial_call=True,
)
def save_field_mappings_callback(
    n_clicks: int | None,
    field_values: List[str],
    field_ids: List[Dict],
) -> tuple[Any, bool | None]:
    """Save field mappings when Save button is clicked.

    Validates all mappings, saves to persistence layer,
    and triggers cache invalidation.

    Args:
        n_clicks: Number of save button clicks
        field_values: List of selected dropdown values
        field_ids: List of dropdown ID dictionaries with metric and field keys

    Returns:
        Tuple of (status alert, save_success flag for closing modal)
    """
    if n_clicks is None:
        return no_update, None

    try:
        # Extract mappings from dropdown values into nested structure
        nested_mappings = {"dora": {}, "flow": {}}

        for field_id_dict, field_value in zip(field_ids, field_values):
            if field_value:  # Only include non-empty mappings
                metric_type = field_id_dict.get("metric")
                internal_field = field_id_dict.get("field")

                if metric_type in ["dora", "flow"]:
                    nested_mappings[metric_type][internal_field] = field_value

        # Flatten nested structure to flat structure for app_settings.json
        flat_mappings = {}
        for metric_type in ["dora", "flow"]:
            for field_name, field_id in nested_mappings[metric_type].items():
                flat_mappings[field_name] = field_id

        # Create save structure with flat mappings
        new_mappings = {"field_mappings": flat_mappings}

        # Fetch available fields for validation
        try:
            available_fields = fetch_available_jira_fields()
            field_metadata = {f["field_id"]: f for f in available_fields}
        except Exception as e:
            logger.warning(f"Could not fetch fields for validation: {e}")
            # Proceed without validation if Jira is unavailable
            field_metadata = {}

        # Validate mappings if metadata available
        validation_errors = []
        if field_metadata:
            for internal_field, jira_field_id in flat_mappings.items():
                is_valid, error_msg = validate_field_mapping(
                    internal_field, jira_field_id, field_metadata
                )
                if not is_valid:
                    validation_errors.append(f"{internal_field}: {error_msg}")

        if validation_errors:
            error_list = html.Ul([html.Li(err) for err in validation_errors])
            error_alert = dbc.Alert(
                [
                    html.H5("Validation Errors", className="alert-heading"),
                    html.P("The following field mappings have type mismatches:"),
                    error_list,
                ],
                color="danger",
                dismissable=True,
            )
            # Return error alert and None for save_success (modal stays open)
            return error_alert, None

        # Add field metadata to save structure
        if field_metadata:
            new_mappings["field_metadata"] = {
                field_id: {
                    "name": meta["field_name"],
                    "type": meta["field_type"],
                    "required": True,  # All mapped fields considered required
                }
                for field_id, meta in field_metadata.items()
                if field_id in flat_mappings.values()
            }

        # Save mappings
        if save_field_mappings(new_mappings):
            # Invalidate metrics cache since mappings changed
            new_hash = get_field_mappings_hash()
            invalidate_cache()
            logger.info(f"Field mappings saved successfully, new hash: {new_hash}")

            # Return success alert and True to trigger modal close
            return create_field_mapping_success_alert(), True
        else:
            # Return error alert and None (modal stays open)
            return create_field_mapping_error_alert(
                "Failed to save mappings to file"
            ), None

    except Exception as e:
        logger.error(f"Error saving field mappings: {e}", exc_info=True)
        # Return error alert and None (modal stays open)
        return create_field_mapping_error_alert(str(e)), None


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
            "incident_related": "customfield_10006",
        },
        "flow": {
            "flow_item_type": "customfield_10007",
            "status": "status",
            "completed_date": "resolutiondate",
        },
    }
