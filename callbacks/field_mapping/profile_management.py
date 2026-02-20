"""Profile management callbacks for field mapping.

Handles profile switching and state isolation between profiles.
"""

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
    """Clear field-mapping state and metadata cache on profile switch.

    This prevents old field mappings and JIRA metadata from persisting in browser memory
    after switching profiles. Critical for data isolation between profiles.

    Bug Fix 1: When user deletes profile "Apache" and creates new profile "Apache",
    the old field mappings were still shown in Configure JIRA Mappings modal
    because the state store (storage_type="memory") persisted across profile changes.

    Bug Fix 2: When switching from Profile 1 (Atlassian JIRA)
    to Profile 2 (Spring JIRA),
    the field fetching was still using Profile 1's cached metadata and JIRA connection,
    causing data leakage between profiles.

    Bug Fix 3: When profile selector is set to the same profile
    (e.g., during page init),
    don't clear state unnecessarily - this was causing field mappings to disappear when
    reopening the modal.

    Args:
        profile_id: ID of newly selected profile
        current_state: Current state store data (may contain previous profile ID)
        current_metadata: Current metadata store data

    Returns:
        Tuple of (empty state dict, empty metadata dict) to clear both stores,
        or no_update if profile hasn't actually changed
    """
    # Check if this is actually a profile change by looking at stored profile ID
    previous_profile_id = (current_state or {}).get("_profile_id")

    if previous_profile_id == profile_id:
        # Same profile - don't clear state (prevents losing data on modal reopen)
        logger.debug(
            "[FieldMapping] Profile selector set to same profile "
            f"({profile_id}), preserving state"
        )
        return no_update, no_update

    if previous_profile_id is None:
        # First profile set (app initialization) - don't clear, just mark the profile
        # The render_tab_content callback will initialize from settings
        logger.info(
            f"[FieldMapping] First profile set: {profile_id}. "
            "Marking profile without clearing."
        )
        # Preserve any existing state, just add profile tracking
        new_state = (current_state or {}).copy()
        new_state["_profile_id"] = profile_id
        return new_state, no_update  # Preserve state, don't clear metadata

    # Actual profile switch (different profile) - clear state and metadata
    logger.info(
        "[FieldMapping] Profile switch detected: "
        f"{previous_profile_id} → {profile_id}. "
        "Clearing state and metadata."
    )
    # Clear everything except profile tracking
    return {
        "_profile_id": profile_id
    }, {}  # Clear state to re-init from new profile, clear metadata
