"""Jira custom field mapping logic.

This module provides functions for fetching available Jira custom fields, validating
field type compatibility, and persisting field mappings to configuration.

Reference: DORA_Flow_Jira_Mapping.md
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from configuration.settings import APP_SETTINGS_FILE
from data.persistence import load_app_settings, load_jira_configuration
from data.performance_utils import FieldMappingIndex
from data.profile_manager import (
    get_active_profile_workspace,
    get_active_query_workspace,
)

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
    # Standard JIRA field types
    "issuetype": "select",
    "status": "select",
    "priority": "select",
    "resolution": "select",
    "project": "select",
    "user": "select",
    "version": "select",
    "securitylevel": "select",
    "component": "multiselect",
    "fixVersions": "multiselect",
    "labels": "multiselect",
}

# Internal field type requirements for DORA and Flow metrics
# Field names match official DORA and Flow Metrics documentation
INTERNAL_FIELD_TYPES = {
    # DORA Metrics fields (aligned with dora.dev standards)
    "deployment_date": "datetime",  # When deployment occurred
    "deployment_successful": "checkbox",  # Deployment success/failure
    "code_commit_date": "datetime",  # When code was committed
    "incident_detected_at": "datetime",  # When production issue found
    "incident_resolved_at": "datetime",  # When issue fixed in production
    "change_failure": "select",  # Deployment failure indicator (field or field=Value syntax)
    "affected_environment": "select",  # Environment affected by incidents
    "target_environment": "select",  # Deployment target environment
    "severity_level": "select",  # Incident priority/severity
    # Flow Metrics fields (aligned with Flow Framework standards)
    "flow_item_type": "select",  # Work category (Feature/Defect/Tech Debt/Risk)
    "status": "select",  # Current work status
    "work_started_date": "datetime",  # When work began (optional - can calculate from changelog)
    "work_completed_date": "datetime",  # When work finished (typically resolutiondate)
    "effort_category": "select",  # Secondary work classification
    "estimate": "number",  # Story points or effort estimation
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

    Uses flexible validation rules to accommodate real-world JIRA field usage:
    - Standard fields (issuetype, status, fixVersions) are always valid
    - Text fields can be used as select fields (JIRA returns string values)
    - Multiselect fields can provide datetime values (e.g., fixVersions release dates)
    - Value filter syntax (field=Value) is supported for conditional matching

    Args:
        internal_field: Internal field name (e.g., "deployment_date")
        jira_field_id: Jira field ID, optionally with value filter
            (e.g., "customfield_10100" or "customfield_10100=Yes")
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
        >>> validate_field_mapping(
        ...     "change_failure",
        ...     "customfield_12708=Yes",
        ...     {"customfield_12708": {"field_type": "select"}}
        ... )
        (True, None)
    """
    # Handle value filter syntax: "field=Value" or "field=Value1|Value2"
    # Extract just the field ID for validation
    actual_field_id = jira_field_id
    if "=" in jira_field_id:
        actual_field_id = jira_field_id.split("=", 1)[0].strip()
        logger.debug(
            f"Value filter syntax detected: '{jira_field_id}' -> field '{actual_field_id}'"
        )

    # Check if internal field has type requirement
    required_type = INTERNAL_FIELD_TYPES.get(internal_field)
    if not required_type:
        logger.warning(f"Unknown internal field: {internal_field}")
        return True, None  # Allow unknown fields for flexibility

    # Check if Jira field exists in metadata
    if actual_field_id not in field_metadata:
        return False, f"Jira field '{actual_field_id}' not found in available fields"

    # Get JIRA field type
    jira_field_type = field_metadata[actual_field_id].get("field_type", "text")

    # FLEXIBLE VALIDATION RULES
    # Allow standard JIRA fields to be used regardless of reported type
    standard_fields = [
        "issuetype",
        "status",
        "priority",
        "created",
        "updated",
        "resolutiondate",
        "fixVersions",
        "versions",
        "components",
    ]

    if actual_field_id in standard_fields:
        logger.debug(
            f"Standard field '{actual_field_id}' allowed for '{internal_field}'"
        )
        return True, None

    # Type compatibility matrix: which JIRA types can satisfy which requirements
    compatible_types = {
        "datetime": [
            "datetime",
            "multiselect",
            "text",
        ],  # fixVersions (multiselect) can provide dates
        "select": ["select", "text"],  # text fields often contain select-like values
        "text": ["text", "select"],  # select fields can provide text
        "number": ["number", "text"],  # text might contain numeric values
        "checkbox": ["checkbox", "select", "text"],  # various ways to represent boolean
        "multiselect": ["multiselect", "array"],
    }

    allowed_types = compatible_types.get(required_type, [required_type])

    if jira_field_type not in allowed_types:
        logger.warning(
            f"Type flexibility: '{internal_field}' expects '{required_type}', "
            f"but '{actual_field_id}' is '{jira_field_type}' - allowing anyway"
        )
        # Allow with warning instead of blocking
        return True, None

    return True, None


def save_field_mappings(mappings: Dict) -> bool:
    """Save field mappings to profile.json (flat structure).

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

        # Get profile-level path (field mappings shared across all queries)
        workspace = get_active_profile_workspace()
        settings_file = workspace / "profile.json"

        with open(str(settings_file), "w") as f:
            json.dump(settings, f, indent=2)

        logger.info("Successfully saved field mappings to profile.json")
        return True

    except Exception as e:
        logger.error(f"Failed to save field mappings: {e}")
        return False


def load_field_mappings() -> Dict:
    """Load field mappings from profile.json.

    Converts flat field_mappings structure to nested dora/flow structure
    expected by the UI.

    Returns:
        Dictionary with structure:
        {
            "field_mappings": {
                "dora": { "deployment_date": "fixVersions", ... },
                "flow": { "effort_category": "customfield_10003", ... }
            }
        }
    """
    try:
        settings = load_app_settings()

        # Support both legacy nested structure and new flat structure
        if "dora_flow_config" in settings:
            # Legacy nested structure - return as-is
            return settings.get("dora_flow_config", {})

        # New flat structure - convert to nested structure for UI
        flat_mappings = settings.get("field_mappings", {})

        # Define which fields belong to DORA vs Flow metrics
        dora_fields = {
            "deployment_date",
            "target_environment",
            "code_commit_date",
            "incident_detected_at",
            "incident_resolved_at",
            "change_failure",  # Changed from deployment_successful to change_failure
            "production_impact",
            "affected_environment",
            "severity_level",
        }

        flow_fields = {
            "flow_item_type",
            "effort_category",
            "work_started_date",
            "work_completed_date",
            "status",
        }

        # Separate into dora and flow dictionaries
        dora_mappings = {k: v for k, v in flat_mappings.items() if k in dora_fields}
        flow_mappings = {k: v for k, v in flat_mappings.items() if k in flow_fields}

        return {"field_mappings": {"dora": dora_mappings, "flow": flow_mappings}}

    except Exception as e:
        logger.error(f"Failed to load field mappings: {e}")
        return {"field_mappings": {"dora": {}, "flow": {}}}


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
        # Support both legacy nested structure and new flat structure
        if "dora_flow_config" in settings:
            mappings = settings.get("dora_flow_config", {}).get("field_mappings", {})
        else:
            mappings = settings.get("field_mappings", {})

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


def create_field_mapping_index(field_mappings: Dict[str, str]) -> FieldMappingIndex:
    """Create FieldMappingIndex for O(1) field lookups.

    This function creates an optimized index for fast bidirectional field mapping
    lookups, providing ~95% speedup over repeated dictionary access.

    Use this when performing multiple field lookups in tight loops (e.g., processing
    hundreds or thousands of JIRA issues in metric calculations).

    Args:
        field_mappings: Flat dictionary of internal field -> JIRA field mappings
            Example: {
                "deployment_date": "customfield_10100",
                "incident_start": "created",
                "work_started_date": "customfield_10200"
            }

    Returns:
        FieldMappingIndex instance with O(1) lookup performance

    Example:
        >>> from data.persistence import load_app_settings
        >>> settings = load_app_settings()
        >>> field_mappings = settings.get("field_mappings", {})
        >>> index = create_field_mapping_index(field_mappings)
        >>> jira_field = index.get_jira_field("deployment_date")  # O(1)
        >>> internal_field = index.get_internal_field("customfield_10100")  # O(1)

    Performance:
        - Standard dict.get(): O(n) when called repeatedly in loops
        - FieldMappingIndex: O(1) for all lookups after initialization
        - Benchmark: ~95% speedup for 1000 lookups (see test_performance.py)
    """
    return FieldMappingIndex(field_mappings)


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


# ============================================================================
# Data Source Validation (Feature 007 - Data Quality)
# ============================================================================


def validate_dora_jira_compatibility(field_mappings: Dict[str, str]) -> Dict[str, Any]:
    """Validate if JIRA configuration is suitable for DORA/Flow metrics.

    Detects inappropriate proxy field mappings that produce misleading metrics.
    Provides validation mode recommendations: 'devops' vs 'issue_tracker'.

    Args:
        field_mappings: Dictionary of internal field -> JIRA field mappings
            Example: {"deployment_date": "resolutiondate", ...}

    Returns:
        Dictionary with structure:
        {
            "validation_mode": "devops" | "issue_tracker" | "unknown",
            "compatibility_level": "full" | "partial" | "unsuitable",
            "warnings": [
                {
                    "severity": "error" | "warning" | "info",
                    "field": "deployment_date",
                    "mapped_to": "resolutiondate",
                    "issue": "Treats all resolved issues as deployments",
                    "recommendation": "Add custom field for actual deployment tracking"
                },
                ...
            ],
            "recommended_interpretation": {
                "deployment_frequency": "Issue Resolution Frequency",
                "lead_time_for_changes": "Issue Resolution Time",
                ...
            },
            "alternative_metrics_available": True | False
        }

    Example:
        >>> mappings = {
        ...     "deployment_date": "resolutiondate",
        ...     "incident_detected_at": "created"
        ... }
        >>> result = validate_dora_jira_compatibility(mappings)
        >>> result["validation_mode"]
        'issue_tracker'
        >>> result["compatibility_level"]
        'unsuitable'
    """
    warnings = []
    devops_field_count = 0
    proxy_field_count = 0

    # Standard JIRA fields that are proxies (not real DORA fields)
    STANDARD_JIRA_FIELDS = {
        "created",
        "resolutiondate",
        "updated",
        "status",
        "issuetype",
        "priority",
        "resolution",
    }

    # DORA-specific field patterns
    DEVOPS_FIELD_PATTERNS = {
        "deployment",
        "deploy",
        "release",
        "incident",
        "production",
        "build",
        "pipeline",
    }

    # Check each DORA/Flow mapping
    CRITICAL_DORA_FIELDS = {
        "deployment_date": {
            "purpose": "Track actual production deployments",
            "proxy_issue": "Treats all resolved issues as deployments",
            "recommendation": "Add custom field for deployment date/time",
        },
        "deployment_successful": {
            "purpose": "Track deployment success/failure",
            "proxy_issue": "Cannot distinguish successful vs failed deployments",
            "recommendation": "Add boolean/checkbox field for deployment status",
        },
        "incident_detected_at": {
            "purpose": "Track production incident detection",
            "proxy_issue": "Treats all issues as production incidents",
            "recommendation": "Add custom field for incident detection timestamp",
        },
        "incident_resolved_at": {
            "purpose": "Track incident resolution",
            "proxy_issue": "Cannot accurately measure incident recovery time",
            "recommendation": "Add custom field for incident resolution timestamp",
        },
    }

    # Validate each critical field
    for internal_field, field_info in CRITICAL_DORA_FIELDS.items():
        if internal_field not in field_mappings:
            warnings.append(
                {
                    "severity": "warning",
                    "field": internal_field,
                    "mapped_to": None,
                    "issue": f"Field not mapped - {field_info['purpose']} will not be tracked",
                    "recommendation": field_info["recommendation"],
                }
            )
            continue

        jira_field = field_mappings[internal_field]

        # Check if using standard JIRA field as proxy
        if jira_field in STANDARD_JIRA_FIELDS:
            proxy_field_count += 1
            warnings.append(
                {
                    "severity": "error",
                    "field": internal_field,
                    "mapped_to": jira_field,
                    "issue": field_info["proxy_issue"],
                    "recommendation": field_info["recommendation"],
                }
            )
        # Check if using proper DevOps-specific field
        elif any(pattern in jira_field.lower() for pattern in DEVOPS_FIELD_PATTERNS):
            devops_field_count += 1
            warnings.append(
                {
                    "severity": "info",
                    "field": internal_field,
                    "mapped_to": jira_field,
                    "issue": None,
                    "recommendation": "[OK] Appears to be a proper DevOps tracking field",
                }
            )
        else:
            # Custom field but unclear purpose
            warnings.append(
                {
                    "severity": "warning",
                    "field": internal_field,
                    "mapped_to": jira_field,
                    "issue": "Verify this field tracks the intended data",
                    "recommendation": "Check JIRA field configuration and usage",
                }
            )

    # Check work_started_date mapping
    if "work_started_date" in field_mappings:
        jira_field = field_mappings["work_started_date"]
        if jira_field == "created":
            warnings.append(
                {
                    "severity": "warning",
                    "field": "work_started_date",
                    "mapped_to": "created",
                    "issue": "Using issue creation date instead of actual work start (e.g., 'In Progress' status change)",
                    "recommendation": "Consider using status change timestamp or custom field for accurate Flow Time calculation",
                }
            )

    # Determine validation mode and compatibility
    error_count = sum(1 for w in warnings if w["severity"] == "error")

    if devops_field_count >= 3 and error_count == 0:
        validation_mode = "devops"
        compatibility_level = "full"
    elif devops_field_count >= 1 and error_count <= 2:
        validation_mode = "devops"
        compatibility_level = "partial"
    elif proxy_field_count >= 2:  # Changed from >= 3 to >= 2 for better detection
        validation_mode = "issue_tracker"
        compatibility_level = "unsuitable"
    else:
        validation_mode = "unknown"
        compatibility_level = "partial"

    # Provide alternative interpretations for issue tracker mode
    recommended_interpretation = {}
    if validation_mode == "issue_tracker":
        recommended_interpretation = {
            "deployment_frequency": "Issue Resolution Frequency",
            "lead_time_for_changes": "Issue Cycle Time (Created → Resolved)",
            "change_failure_rate": "Not Applicable (No deployment tracking)",
            "mean_time_to_recovery": "Issue Resolution Time",
            "flow_velocity": "Issue Completion Rate",
            "flow_time": "Issue Cycle Time",
            "flow_efficiency": "Not Applicable (Requires time tracking fields)",
            "flow_load": "Work In Progress",
            "flow_distribution": "Issue Type Distribution",
        }

    return {
        "validation_mode": validation_mode,
        "compatibility_level": compatibility_level,
        "devops_field_count": devops_field_count,
        "proxy_field_count": proxy_field_count,
        "error_count": error_count,
        "warning_count": sum(1 for w in warnings if w["severity"] == "warning"),
        "warnings": warnings,
        "recommended_interpretation": recommended_interpretation,
        "alternative_metrics_available": validation_mode == "issue_tracker"
        and compatibility_level == "unsuitable",
    }
