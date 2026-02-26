"""Callbacks for auto-fetching field values when field mappings change.

Implements Option 5 (Hybrid Auto-Fetch with Visual Indicator) for field mapping UX:
- When user changes effort_category or affected_environment field mapping
- Auto-fetch available values from JIRA (1000 issues from dev projects)
- Update Types/Environment tab dropdowns immediately
- Show toast notification with results
"""

import logging
from typing import Any

from dash import Input, Output, State, callback, ctx, no_update

from ui.toast_notifications import create_success_toast, create_warning_toast

logger = logging.getLogger(__name__)


def _extract_field_id(namespace_value: str | None) -> str | None:
    """Extract clean field ID from namespace syntax.

    Examples:
        "customfield_13204" -> "customfield_13204"
        "customfield_11309=PROD" -> "customfield_11309"
        "PROJECT.customfield_13204" -> "customfield_13204"
        "status:Done.DateTime" -> None (not a simple field)

    Args:
        namespace_value: Raw namespace input value

    Returns:
        Clean field ID or None if not a simple field reference
    """
    if not namespace_value or not isinstance(namespace_value, str):
        return None

    value = namespace_value.strip()

    # Skip changelog syntax (status:Done.DateTime) - not a simple field
    if ":" in value and ".DateTime" in value:
        return None
    if ":" in value and ".Occurred" in value:
        return None

    # Strip =Value suffix (e.g., "customfield_11309=PROD" -> "customfield_11309")
    if "=" in value:
        value = value.split("=")[0]

    # Strip project prefix (e.g., "PROJECT.customfield_13204" -> "customfield_13204")
    if "." in value:
        parts = value.split(".")
        # Take last part if it looks like a field ID
        value = parts[-1]

    # Validate it looks like a field ID
    if value.startswith("customfield_") or value in [
        "status",
        "issuetype",
        "priority",
        "resolution",
    ]:
        return value

    return value if value else None


def _fetch_field_values(field_id: str, jira_config: dict[str, Any]) -> list[str]:
    """Fetch available values for a field from JIRA.

    Args:
        field_id: JIRA field ID (e.g., customfield_13204)
        jira_config: JIRA configuration with base_url, token, api_version

    Returns:
        List of available values for the field
    """
    if not field_id or not jira_config.get("base_url"):
        return []

    try:
        from data.jira.metadata_fetcher import create_metadata_fetcher

        fetcher = create_metadata_fetcher(
            jira_url=jira_config.get("base_url", ""),
            jira_token=jira_config.get("token", ""),
            api_version=jira_config.get("api_version", "v2"),
        )

        values = fetcher.fetch_field_options(field_id)
        logger.info(f"[FieldValueFetch] Fetched {len(values)} values for {field_id}")
        return values

    except Exception as e:
        logger.error(f"[FieldValueFetch] Error fetching values for {field_id}: {e}")
        return []


@callback(
    Output("fetched-field-values-store", "data", allow_duplicate=True),
    Input("field-mapping-modal", "is_open"),
    prevent_initial_call=True,
)
def prefetch_field_values_on_modal_open(is_open: bool):
    """Prefetch field values when the modal opens with already-configured fields.

    Solves the chicken-and-egg problem on first-time configuration: if
    effort_category or affected_environment fields are already saved in settings,
    fetch their available values immediately so the Types/Environment tab dropdowns
    are populated without requiring a prior 'Update Data' run.

    This callback always runs AFTER toggle_field_mapping_modal (in modal_core.py)
    because it depends on the is_open output of that callback.  The store is
    therefore already cleared to {} before this callback fires.

    Args:
        is_open: Whether the field mapping modal is open

    Returns:
        Dict with pre-fetched field values, or no_update when closing
    """
    if not is_open:
        return no_update

    from data.persistence import load_app_settings, load_jira_configuration

    settings = load_app_settings() or {}
    jira_config = load_jira_configuration() or {}

    if not jira_config.get("base_url"):
        logger.debug("[FieldValueFetch] Skipping pre-fetch: JIRA URL not configured")
        return no_update

    field_mappings = settings.get("field_mappings", {}) or {}
    effort_cat_raw = (field_mappings.get("flow") or {}).get("effort_category")
    affected_env_raw = (field_mappings.get("dora") or {}).get("affected_environment")

    if not effort_cat_raw and not affected_env_raw:
        logger.debug(
            "[FieldValueFetch] Skipping pre-fetch: "
            "effort_category and affected_environment not configured"
        )
        return no_update

    prefetched: dict = {}

    effort_cat_id = _extract_field_id(effort_cat_raw)
    if effort_cat_id:
        values = _fetch_field_values(effort_cat_id, jira_config)
        if values:
            prefetched["effort_category"] = {
                "field_id": effort_cat_id,
                "values": values,
            }
            logger.info(
                f"[FieldValueFetch] Pre-fetched {len(values)} effort categories "
                f"for {effort_cat_id}"
            )

    affected_env_id = _extract_field_id(affected_env_raw)
    if affected_env_id:
        values = _fetch_field_values(affected_env_id, jira_config)
        if values:
            prefetched["affected_environment"] = {
                "field_id": affected_env_id,
                "values": values,
            }
            logger.info(
                f"[FieldValueFetch] Pre-fetched {len(values)} environment values "
                f"for {affected_env_id}"
            )

    return prefetched if prefetched else no_update


@callback(
    [
        Output("fetched-field-values-store", "data"),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    [
        Input(
            {
                "type": "namespace-field-input",
                "metric": "flow",
                "field": "effort_category",
            },
            "n_blur",
        ),
        Input(
            {
                "type": "namespace-field-input",
                "metric": "dora",
                "field": "affected_environment",
            },
            "n_blur",
        ),
    ],
    [
        State(
            {
                "type": "namespace-field-input",
                "metric": "flow",
                "field": "effort_category",
            },
            "value",
        ),
        State(
            {
                "type": "namespace-field-input",
                "metric": "dora",
                "field": "affected_environment",
            },
            "value",
        ),
        State("fetched-field-values-store", "data"),
    ],
    prevent_initial_call=True,
)
def fetch_field_values_on_blur(
    effort_category_blur: int,
    affected_environment_blur: int,
    effort_category_value: str,
    affected_environment_value: str,
    current_store: dict[str, Any],
):
    """Fetch values when field-mapping inputs lose focus.

    Triggered when user finishes typing and leaves the field (on blur).
    Only fetches if value looks like a valid field ID AND has changed since last fetch.
    Shows toast notification with results.
    """
    if not ctx.triggered:
        return no_update, no_update

    triggered_id = ctx.triggered_id
    if not triggered_id:
        return no_update, no_update

    # Load JIRA config from profile (not from a store)
    from data.persistence import load_jira_configuration

    jira_config = load_jira_configuration() or {}

    # Initialize store if needed
    if current_store is None:
        current_store = {}

    # Determine which field triggered the callback
    field_type = triggered_id.get("field") if isinstance(triggered_id, dict) else None

    toast = None
    updated_store = current_store.copy()

    if field_type == "effort_category" and effort_category_value:
        field_id = _extract_field_id(effort_category_value)

        if field_id:
            # Check if this field was already fetched with same field_id
            existing = current_store.get("effort_category", {})
            if existing.get("field_id") == field_id:
                logger.debug(
                    "[FieldValueFetch] Skipping effort_category fetch - "
                    f"already fetched for {field_id}"
                )
                return no_update, no_update

            logger.info(
                f"[FieldValueFetch] Fetching effort_category values for {field_id}"
            )
            values = _fetch_field_values(field_id, jira_config)

            updated_store["effort_category"] = {
                "field_id": field_id,
                "values": values,
            }

            if values:
                toast = create_success_toast(
                    f"Found {len(values)} effort categories",
                    header="Field Values Loaded",
                )
            else:
                toast = create_warning_toast(
                    "No effort category values found in recent issues",
                    header="Field Values",
                    duration=4000,
                )

    elif field_type == "affected_environment" and affected_environment_value:
        field_id = _extract_field_id(affected_environment_value)

        if field_id:
            # Check if this field was already fetched with same field_id
            existing = current_store.get("affected_environment", {})
            if existing.get("field_id") == field_id:
                logger.debug(
                    "[FieldValueFetch] Skipping affected_environment fetch - "
                    f"already fetched for {field_id}"
                )
                return no_update, no_update

            logger.info(
                f"[FieldValueFetch] Fetching affected_environment values for {field_id}"
            )
            values = _fetch_field_values(field_id, jira_config)

            updated_store["affected_environment"] = {
                "field_id": field_id,
                "values": values,
            }

            if values:
                toast = create_success_toast(
                    f"Found {len(values)} environment values",
                    header="Field Values Loaded",
                )
            else:
                toast = create_warning_toast(
                    "No environment values found in recent issues",
                    header="Field Values",
                    duration=4000,
                )

    return updated_store, toast if toast else no_update
