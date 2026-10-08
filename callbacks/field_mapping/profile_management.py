import logging

from dash import Input, Output, State, callback, no_update

logger = logging.getLogger(__name__)


@callback(
    [
        Output("field-mapping-state-store", "data", allow_duplicate=True),
        Output("jira-metadata-store", "data", allow_duplicate=True),
    ],
    Input("profile-selector", "value"),
    State("field-mapping-state-store", "data"),
    State("jira-metadata-store", "data"),
    prevent_initial_call=True,
)
def clear_field_mapping_state_on_profile_switch(
    profile_id, current_state, current_metadata
):

    previous_profile_id = (current_state or {}).get("_profile_id")

    if previous_profile_id == profile_id:
        logger.debug(
            "[FieldMapping] Profile selector set to same profile "
            f"({profile_id}), preserving state"
        )
        return no_update, no_update

    if previous_profile_id is None:
        logger.info(
            f"[FieldMapping] First profile set: {profile_id}. "
            "Marking profile without clearing."
        )
        new_state = (current_state or {}).copy()
        new_state["_profile_id"] = profile_id
        return new_state, no_update

    logger.info(
        "[FieldMapping] Profile switch detected: "
        f"{previous_profile_id} → {profile_id}. "
        "Clearing state and metadata."
    )
    return {"_profile_id": profile_id}, {}
