"""Callbacks for field mapping configuration.

Handles field mapping modal interactions, Jira field discovery,
validation, and persistence.
"""

from dash import callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import logging

from data.field_mapper import (
    load_field_mappings,
    save_field_mappings,
    get_field_mappings_hash,
)
from data.jira_simple import get_jira_config
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
        current_mappings = load_field_mappings()

        # Get Jira configuration to fetch available fields
        jira_config = get_jira_config()

        # STUB: Phase 4 - Mock available fields
        # Phase 5+ will fetch real fields from Jira API
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
    State("field-mapping-content", "children"),
    prevent_initial_call=True,
)
def save_field_mappings_callback(
    n_clicks: int | None,
    form_content: Any,
) -> Any:
    """Save field mappings when Save button is clicked.

    Validates all mappings, saves to persistence layer,
    and triggers cache invalidation.

    Args:
        n_clicks: Number of save button clicks
        form_content: Current form content (to extract values)

    Returns:
        Success or error alert
    """
    if n_clicks is None:
        return no_update

    try:
        # STUB: Phase 4 - Mock mapping collection
        # Phase 5+ will extract actual values from form dropdowns
        new_mappings = _get_mock_mappings()

        # Validate mappings
        # Note: validate_field_mapping expects field_metadata dict
        # For now, we'll just save without validation in the stub

        # Save mappings
        save_field_mappings(new_mappings)

        # Log mapping hash change for cache invalidation
        new_hash = get_field_mappings_hash()
        logger.info(f"Field mappings saved, new hash: {new_hash}")

        return create_field_mapping_success_alert()

    except Exception as e:
        logger.error(f"Error saving field mappings: {e}")
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
