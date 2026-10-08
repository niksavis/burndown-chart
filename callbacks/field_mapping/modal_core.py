import logging
from typing import Any

from dash import ALL, Input, Output, State, callback, callback_context, no_update

logger = logging.getLogger(__name__)


@callback(
    Output("field-mapping-modal", "is_open"),
    Output("fetched-field-values-store", "data", allow_duplicate=True),
    Input("open-field-mapping-modal", "n_clicks"),
    Input({"type": "open-field-mapping", "index": ALL}, "n_clicks"),
    Input("field-mapping-cancel-button", "n_clicks"),
    Input("field-mapping-save-button", "n_clicks"),
    State("field-mapping-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_field_mapping_modal(
    open_clicks: int | None,
    open_clicks_pattern: list,
    cancel_clicks: int | None,
    save_clicks: int | None,
    is_open: bool,
) -> tuple[bool, Any]:

    ctx = callback_context
    if not ctx.triggered:
        return is_open, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_value = ctx.triggered[0]["value"]

    logger.info(
        "[FieldMapping] Modal toggle - "
        f"trigger_id: {trigger_id}, value: {trigger_value}"
    )

    if trigger_id == "field-mapping-cancel-button":
        return False, no_update

    if trigger_id == "field-mapping-save-button" and save_clicks:
        logger.info("[FieldMapping] Closing modal after save click")
        return False, no_update

    if trigger_id == "open-field-mapping-modal" or (
        trigger_id.startswith("{") and "open-field-mapping" in trigger_id
    ):
        if trigger_value and trigger_value != 0:
            logger.info(f"[FieldMapping] Opening modal from trigger: {trigger_id}")
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

    result = []
    for value_list in field_values:
        if value_list and len(value_list) > 1:
            result.append([value_list[-1]])
        else:
            result.append(value_list if value_list else [])
    return result
