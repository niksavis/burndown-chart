"""Modal core callbacks for field mapping.

Handles modal toggle and single-selection enforcement.
"""

import logging
from typing import Any

from dash import ALL, Input, Output, State, callback, callback_context, no_update

logger = logging.getLogger(__name__)


@callback(
    Output("field-mapping-modal", "is_open"),
    Output("fetched-field-values-store", "data", allow_duplicate=True),
    Input("open-field-mapping-modal", "n_clicks"),
    Input(
        {"type": "open-field-mapping", "index": ALL}, "n_clicks"
    ),  # Pattern-matching for metric cards
    Input("field-mapping-cancel-button", "n_clicks"),
    Input(
        "field-mapping-save-button", "n_clicks"
    ),  # Close on save click (toast shows result)
    State("field-mapping-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_field_mapping_modal(
    open_clicks: int | None,
    open_clicks_pattern: list,  # List of clicks from pattern-matched buttons
    cancel_clicks: int | None,
    save_clicks: int | None,
    is_open: bool,
) -> tuple[bool, Any]:  # Second element is dict or no_update
    """Toggle field mapping modal open/closed.

    Args:
        open_clicks: Open button clicks (from settings panel)
        open_clicks_pattern: List of clicks from pattern-matched metric card buttons
        cancel_clicks: Cancel button clicks
        save_clicks: Save button clicks (closes modal, toast shows result)
        is_open: Current modal state

    Returns:
        Tuple of (new modal state, fetched values store data)
        - Modal state: True = open, False = closed
        - Store data: Empty dict {} when opening
          (clears stale data), no_update otherwise
    """
    ctx = callback_context
    if not ctx.triggered:
        return is_open, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_value = ctx.triggered[0]["value"]

    # Debug logging
    logger.info(
        "[FieldMapping] Modal toggle - "
        f"trigger_id: {trigger_id}, value: {trigger_value}"
    )

    # Close on cancel - don't clear store (user might reopen)
    if trigger_id == "field-mapping-cancel-button":
        return False, no_update

    # Close on save button click - toast notification will show result
    if trigger_id == "field-mapping-save-button" and save_clicks:
        logger.info("[FieldMapping] Closing modal after save click")
        return False, no_update

    # Open when open button clicked (from settings panel or metric cards)
    # Verify it's an actual click (value > 0), not button DOM insertion
    # (value = None or 0)
    if trigger_id == "open-field-mapping-modal" or (
        trigger_id.startswith("{") and "open-field-mapping" in trigger_id
    ):
        # Only open if there was an actual click (not None, not 0, not empty list)
        if trigger_value and trigger_value != 0:
            logger.info(f"[FieldMapping] Opening modal from trigger: {trigger_id}")
            # Clear fetched field values when opening
            # to prevent stale data from other profiles
            return True, {}
        else:
            logger.info(
                "[FieldMapping] Ignoring button render/initial state - "
                f"trigger: {trigger_id}, value: {trigger_value}"
            )
            return is_open, no_update

    logger.warning(f"[FieldMapping] Modal toggle - unhandled trigger: {trigger_id}")
    return is_open, no_update


@callback(
    Output({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    Input({"type": "field-mapping-dropdown", "metric": ALL, "field": ALL}, "value"),
    prevent_initial_call=True,
)
def enforce_single_selection_in_multi_dropdown(
    field_values: list[list[str]],
) -> list[list[str]]:
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
