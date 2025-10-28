"""Callbacks for field mapping configuration.

Handles field mapping modal interactions, Jira field discovery,
validation, and persistence.
"""

from dash import callback, Output, Input, State, no_update, ALL, html
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
    Input("field-mapping-save-button", "n_clicks"),
    State("field-mapping-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_field_mapping_modal(
    open_clicks: int | None,
    cancel_clicks: int | None,
    save_clicks: int | None,
    is_open: bool,
) -> bool:
    """Toggle field mapping modal open/closed.

    Args:
        open_clicks: Open button clicks
        cancel_clicks: Cancel button clicks
        save_clicks: Save button clicks (closes after save)
        is_open: Current modal state

    Returns:
        New modal state (True = open, False = closed)
    """
    # Toggle modal state
    return not is_open


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
        # Load current field mappings
        current_mappings_data = load_field_mappings()
        current_mappings = current_mappings_data.get(
            "field_mappings", {"dora": {}, "flow": {}}
        )

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
    Output("field-mapping-status", "children"),
    Input("field-mapping-save-button", "n_clicks"),
    State({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    State({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "id"),
    prevent_initial_call=True,
)
def save_field_mappings_callback(
    n_clicks: int | None,
    field_values: List[str],
    field_ids: List[Dict],
) -> Any:
    """Save field mappings when Save button is clicked.

    Validates all mappings, saves to persistence layer,
    and triggers cache invalidation.

    Args:
        n_clicks: Number of save button clicks
        field_values: List of selected dropdown values
        field_ids: List of dropdown ID dictionaries with metric and field keys

    Returns:
        Success or error alert
    """
    if n_clicks is None:
        return no_update

    try:
        # Extract mappings from dropdown values
        new_mappings = {"field_mappings": {"dora": {}, "flow": {}}}

        for field_id_dict, field_value in zip(field_ids, field_values):
            if field_value:  # Only include non-empty mappings
                metric_type = field_id_dict.get("metric")
                internal_field = field_id_dict.get("field")

                if metric_type in ["dora", "flow"]:
                    new_mappings["field_mappings"][metric_type][internal_field] = (
                        field_value
                    )

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
            for metric_type in ["dora", "flow"]:
                for internal_field, jira_field_id in new_mappings["field_mappings"][
                    metric_type
                ].items():
                    is_valid, error_msg = validate_field_mapping(
                        internal_field, jira_field_id, field_metadata
                    )
                    if not is_valid:
                        validation_errors.append(f"{internal_field}: {error_msg}")

        if validation_errors:
            error_list = html.Ul([html.Li(err) for err in validation_errors])
            return dbc.Alert(
                [
                    html.H5("Validation Errors", className="alert-heading"),
                    html.P("The following field mappings have type mismatches:"),
                    error_list,
                ],
                color="danger",
                dismissable=True,
            )

        # Add field metadata to save structure
        if field_metadata:
            new_mappings["field_metadata"] = {
                field_id: {
                    "name": meta["field_name"],
                    "type": meta["field_type"],
                    "required": True,  # All mapped fields considered required
                }
                for field_id, meta in field_metadata.items()
                if field_id
                in [
                    jira_id
                    for metric in new_mappings["field_mappings"].values()
                    for jira_id in metric.values()
                ]
            }

        # Save mappings
        if save_field_mappings(new_mappings):
            # Invalidate metrics cache since mappings changed
            new_hash = get_field_mappings_hash()
            invalidate_cache()
            logger.info(f"Field mappings saved successfully, new hash: {new_hash}")

            return create_field_mapping_success_alert()
        else:
            return create_field_mapping_error_alert("Failed to save mappings to file")

    except Exception as e:
        logger.error(f"Error saving field mappings: {e}", exc_info=True)
        return create_field_mapping_error_alert(str(e))


def _get_mock_jira_fields() -> List[Dict[str, Any]]:
    """Get mock Jira fields for Phase 4 stub.

    Phase 5+ will replace with actual Jira API call.

    Returns:
        List of mock field metadata
    """
    return [
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
        {
            "field_id": "status",
            "field_name": "Status",
            "field_type": "status",
        },
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
