"""Jira custom field mapping logic.

This module provides functions for fetching available Jira custom fields, validating
field type compatibility, and persisting field mappings to configuration.

Reference: DORA_Flow_Jira_Mapping.md
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple

import requests

from configuration.settings import APP_SETTINGS_FILE
from data.persistence import load_app_settings, load_jira_configuration

logger = logging.getLogger(__name__)

# Field type mapping from Jira schema types to internal types
JIRA_TYPE_MAPPING = {
    "datetime": "datetime",
    "date": "datetime",
    "number": "number",
    "string": "text",
    "option": "select",
    "array": "multiselect",
    "any": "checkbox",  # Jira checkbox type
}

# Internal field type requirements for DORA and Flow metrics
INTERNAL_FIELD_TYPES = {
    # DORA fields
    "deployment_date": "datetime",
    "target_environment": "select",
    "code_commit_date": "datetime",
    "deployed_to_production_date": "datetime",
    "incident_detected_at": "datetime",
    "incident_resolved_at": "datetime",
    "deployment_successful": "checkbox",
    "production_impact": "select",
    "incident_related": "text",
    # Flow fields
    "flow_item_type": "select",
    "work_started_date": "datetime",
    "work_completed_date": "datetime",
    "status_entry_timestamp": "datetime",
    "active_work_hours": "number",
    "flow_time_days": "number",
    "flow_efficiency_percent": "number",
    "completed_date": "datetime",
    "status": "select",
}


def fetch_available_jira_fields() -> List[Dict]:
    """Fetch all fields from Jira instance.

    Tries authenticated request first, then falls back to unauthenticated
    for public Jira instances like Apache Kafka.

    Returns:
        List of field dictionaries with structure:
        [
            {
                "field_id": "customfield_10100",
                "field_name": "Deployment Date",
                "field_type": "datetime",
                "is_custom": True,
                "schema": {...}
            },
            ...
        ]

    Raises:
        requests.RequestException: If Jira API call fails
    """
    config = load_jira_configuration()
    base_url = config.get("base_url", "")

    if not base_url:
        raise requests.RequestException("No JIRA base URL configured")

    # Use configured API version (v2 or v3)
    api_version = config.get("api_version", "v2")
    if api_version == "v3":
        endpoint = f"{base_url}/rest/api/3/field"
    else:
        endpoint = f"{base_url}/rest/api/2/field"

    token = config.get("token", "")

    # Try authenticated request first
    try:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(endpoint, headers=headers, timeout=30)
        response.raise_for_status()

        jira_fields = response.json()

        # Transform to our internal format
        transformed_fields = []
        for field in jira_fields:
            field_id = field.get("id", "")
            is_custom = field_id.startswith("customfield_")

            # Map Jira schema type to our internal type
            schema = field.get("schema", {})
            jira_type = schema.get("type", "string")
            internal_type = JIRA_TYPE_MAPPING.get(jira_type, "text")

            transformed_fields.append(
                {
                    "field_id": field_id,
                    "field_name": field.get("name", field_id),
                    "field_type": internal_type,
                    "is_custom": is_custom,
                    "schema": schema,
                }
            )

        logger.info(
            f"Fetched {len(transformed_fields)} fields from Jira "
            f"({sum(1 for f in transformed_fields if f['is_custom'])} custom fields)"
        )
        return transformed_fields

    except requests.RequestException as e:
        logger.error(f"Failed to fetch Jira fields: {e}")
        raise


def validate_field_mapping(
    internal_field: str, jira_field_id: str, field_metadata: Dict
) -> Tuple[bool, Optional[str]]:
    """Validate that Jira field type matches required internal field type.

    Args:
        internal_field: Internal field name (e.g., "deployment_date")
        jira_field_id: Jira field ID (e.g., "customfield_10100")
        field_metadata: Dictionary of available Jira fields with metadata

    Returns:
        Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error message") if invalid

    Example:
        >>> validate_field_mapping(
        ...     "deployment_date",
        ...     "customfield_10100",
        ...     {"customfield_10100": {"field_type": "datetime"}}
        ... )
        (True, None)
    """
    # Check if internal field has type requirement
    required_type = INTERNAL_FIELD_TYPES.get(internal_field)
    if not required_type:
        logger.warning(f"Unknown internal field: {internal_field}")
        return True, None  # Allow unknown fields for flexibility

    # Check if Jira field exists in metadata
    if jira_field_id not in field_metadata:
        return False, f"Jira field '{jira_field_id}' not found in available fields"

    # Check type compatibility
    jira_field_type = field_metadata[jira_field_id].get("field_type", "text")

    if jira_field_type != required_type:
        return (
            False,
            f"Field type mismatch: '{internal_field}' requires type "
            f"'{required_type}', but '{jira_field_id}' is type '{jira_field_type}'",
        )

    return True, None


def save_field_mappings(mappings: Dict) -> bool:
    """Save field mappings to app_settings.json (flat structure).

    Args:
        mappings: Dictionary with structure:
            {
                "field_mappings": {
                    "deployment_date": "resolutiondate",
                    "incident_start": "created",
                    "work_started_date": "created",
                    "work_type": "issuetype",
                    ...
                },
                "field_metadata": {
                    "resolutiondate": {
                        "name": "Resolution Date",
                        "type": "datetime",
                        "required": True
                    },
                    ...
                }
            }

    Returns:
        True if save successful, False otherwise
    """
    try:
        settings = load_app_settings()

        # Save to flat field_mappings structure (not nested dora_flow_config)
        if "field_mappings" in mappings:
            settings["field_mappings"] = mappings["field_mappings"]

        # Optionally save field_metadata if provided
        if "field_metadata" in mappings:
            settings["field_metadata"] = mappings["field_metadata"]

        # Write directly to JSON file
        with open(APP_SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)

        logger.info("Successfully saved field mappings to app_settings.json")
        return True

    except Exception as e:
        logger.error(f"Failed to save field mappings: {e}")
        return False


def load_field_mappings() -> Dict:
    """Load field mappings from app_settings.json.

    Returns:
        Dictionary with field_mappings (flat structure) and field_metadata
    """
    try:
        settings = load_app_settings()
        # Support both legacy nested structure and new flat structure
        if "dora_flow_config" in settings:
            # Legacy nested structure
            return settings.get("dora_flow_config", {})
        else:
            # New flat structure - return in expected format for UI
            return {"field_mappings": settings.get("field_mappings", {})}
    except Exception as e:
        logger.error(f"Failed to load field mappings: {e}")
        return {"field_mappings": {}}


def get_field_mappings_hash() -> str:
    """Calculate MD5 hash of current field mappings for cache invalidation.

    Returns:
        8-character hex hash of field mappings (or "00000000" if no mappings)

    Example:
        >>> get_field_mappings_hash()
        "a3f5c8d9"
    """
    try:
        settings = load_app_settings()
        mappings = settings.get("dora_flow_config", {}).get("field_mappings", {})

        # Create deterministic string representation
        mappings_str = json.dumps(mappings, sort_keys=True)

        # Calculate hash
        hash_object = hashlib.md5(mappings_str.encode())
        return hash_object.hexdigest()[:8]

    except Exception as e:
        logger.error(f"Failed to calculate field mappings hash: {e}")
        return "00000000"


def get_mapped_field_id(metric_type: str, internal_field: str) -> Optional[str]:
    """Get Jira field ID for an internal field name.

    Args:
        metric_type: "dora" or "flow"
        internal_field: Internal field name (e.g., "deployment_date")

    Returns:
        Jira field ID (e.g., "customfield_10100") or None if not mapped

    Example:
        >>> get_mapped_field_id("dora", "deployment_date")
        "customfield_10100"
    """
    mappings = load_field_mappings()
    return mappings.get("field_mappings", {}).get(metric_type, {}).get(internal_field)


def check_required_mappings(metric_name: str) -> Tuple[bool, List[str]]:
    """Check if all required field mappings exist for a metric.

    Args:
        metric_name: Name of metric (e.g., "deployment_frequency")

    Returns:
        Tuple of (all_mapped, missing_fields)
            - (True, []) if all required fields mapped
            - (False, ["field1", "field2"]) if some fields missing

    Example:
        >>> check_required_mappings("deployment_frequency")
        (True, [])
    """
    from configuration import dora_config, flow_config

    # Determine if DORA or Flow metric
    if metric_name in dora_config.REQUIRED_DORA_FIELDS:
        required_fields = dora_config.get_required_fields(metric_name)
        metric_type = "dora"
    elif metric_name in flow_config.REQUIRED_FLOW_FIELDS:
        required_fields = flow_config.get_required_fields(metric_name)
        metric_type = "flow"
    else:
        logger.warning(f"Unknown metric: {metric_name}")
        return False, []

    # Check mappings
    mappings = load_field_mappings()
    field_mappings = mappings.get("field_mappings", {}).get(metric_type, {})

    missing_fields = [field for field in required_fields if field not in field_mappings]

    return len(missing_fields) == 0, missing_fields
