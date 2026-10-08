import hashlib
import json
import logging
from typing import Any

import requests

from configuration import dora_config, flow_config
from data.performance_utils import FieldMappingIndex
from data.persistence import load_app_settings, load_jira_configuration
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)

JIRA_TYPE_MAPPING = {
    "datetime": "datetime",
    "date": "datetime",
    "number": "number",
    "string": "text",
    "option": "select",
    "array": "multiselect",
    "any": "checkbox",
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

INTERNAL_FIELD_TYPES = {
    "deployment_date": "datetime",
    "deployment_successful": "checkbox",
    "code_commit_date": "datetime",
    "incident_detected_at": "datetime",
    "incident_resolved_at": "datetime",
    "change_failure": "select",
    "affected_environment": "select",
    "target_environment": "select",
    "severity_level": "select",
    "flow_item_type": "select",
    "status": "select",
    "effort_category": "select",
    "estimate": "number",
}


def fetch_available_jira_fields() -> list[dict]:

    config = load_jira_configuration()
    base_url = config.get("base_url", "")

    if not base_url:
        raise requests.RequestException("No JIRA base URL configured")

    api_version = config.get("api_version", "v2")
    if api_version == "v3":
        endpoint = f"{base_url}/rest/api/3/field"
    else:
        endpoint = f"{base_url}/rest/api/2/field"

    token = config.get("token", "")

    try:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(endpoint, headers=headers, timeout=30)
        response.raise_for_status()

        jira_fields = response.json()

        transformed_fields = []
        for field in jira_fields:
            field_id = field.get("id", "")
            is_custom = field_id.startswith("customfield_")

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
    internal_field: str, jira_field_id: str, field_metadata: dict
) -> tuple[bool, str | None]:

    actual_field_id = jira_field_id
    if "=" in jira_field_id:
        actual_field_id = jira_field_id.split("=", 1)[0].strip()
        logger.debug(
            "Value filter syntax detected: "
            f"'{jira_field_id}' -> field '{actual_field_id}'"
        )

    required_type = INTERNAL_FIELD_TYPES.get(internal_field)
    if not required_type:
        logger.warning(f"Unknown internal field: {internal_field}")
        return True, None

    if actual_field_id not in field_metadata:
        return False, f"Jira field '{actual_field_id}' not found in available fields"

    jira_field_type = field_metadata[actual_field_id].get("field_type", "text")

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

    compatible_types = {
        "datetime": [
            "datetime",
            "multiselect",
            "text",
        ],
        "select": ["select", "text"],
        "text": ["text", "select"],
        "number": ["number", "text"],
        "checkbox": ["checkbox", "select", "text"],
        "multiselect": ["multiselect", "array"],
    }

    allowed_types = compatible_types.get(required_type, [required_type])

    if jira_field_type not in allowed_types:
        logger.warning(
            f"Type flexibility: '{internal_field}' expects '{required_type}', "
            f"but '{actual_field_id}' is '{jira_field_type}' - allowing anyway"
        )
        return True, None

    return True, None


def save_field_mappings(mappings: dict) -> bool:

    try:
        backend = get_backend()

        active_profile_id = backend.get_app_state("active_profile_id")
        if not active_profile_id:
            logger.error("No active profile to save field mappings to")
            return False

        settings = backend.get_profile(active_profile_id) or {}

        if "field_mappings" in mappings:
            settings["field_mappings"] = mappings["field_mappings"]

        if "field_metadata" in mappings:
            settings["field_metadata"] = mappings["field_metadata"]

        settings["id"] = active_profile_id

        backend.save_profile(settings)
        logger.info("Successfully saved field mappings to database")
        return True

    except Exception as e:
        logger.error(f"Failed to save field mappings: {e}")
        return False


def load_field_mappings() -> dict:

    try:
        settings = load_app_settings()

        if "dora_flow_config" in settings:
            return settings.get("dora_flow_config", {})

        flat_mappings = settings.get("field_mappings", {})

        dora_fields = {
            "deployment_date",
            "target_environment",
            "code_commit_date",
            "incident_detected_at",
            "incident_resolved_at",
            "change_failure",
            "production_impact",
            "affected_environment",
            "severity_level",
        }

        flow_fields = {
            "flow_item_type",
            "effort_category",
            "status",
        }

        dora_mappings = {k: v for k, v in flat_mappings.items() if k in dora_fields}
        flow_mappings = {k: v for k, v in flat_mappings.items() if k in flow_fields}

        return {"field_mappings": {"dora": dora_mappings, "flow": flow_mappings}}

    except Exception as e:
        logger.error(f"Failed to load field mappings: {e}")
        return {"field_mappings": {"dora": {}, "flow": {}}}


def get_field_mappings_hash() -> str:

    try:
        settings = load_app_settings()
        if "dora_flow_config" in settings:
            mappings = settings.get("dora_flow_config", {}).get("field_mappings", {})
        else:
            mappings = settings.get("field_mappings", {})

        mappings_str = json.dumps(mappings, sort_keys=True)

        hash_object = hashlib.md5(mappings_str.encode(), usedforsecurity=False)
        return hash_object.hexdigest()[:8]

    except Exception as e:
        logger.error(f"Failed to calculate field mappings hash: {e}")
        return "00000000"


def get_mapped_field_id(metric_type: str, internal_field: str) -> str | None:

    mappings = load_field_mappings()
    return mappings.get("field_mappings", {}).get(metric_type, {}).get(internal_field)


def create_field_mapping_index(field_mappings: dict[str, str]) -> FieldMappingIndex:

    return FieldMappingIndex(field_mappings)


def check_required_mappings(metric_name: str) -> tuple[bool, list[str]]:

    if metric_name in dora_config.REQUIRED_DORA_FIELDS:
        required_fields = dora_config.get_required_fields(metric_name)
        metric_type = "dora"
    elif metric_name in flow_config.REQUIRED_FLOW_FIELDS:
        required_fields = flow_config.get_required_fields(metric_name)
        metric_type = "flow"
    else:
        logger.warning(f"Unknown metric: {metric_name}")
        return False, []

    mappings = load_field_mappings()
    field_mappings = mappings.get("field_mappings", {}).get(metric_type, {})

    missing_fields = [field for field in required_fields if field not in field_mappings]

    return len(missing_fields) == 0, missing_fields


def validate_dora_jira_compatibility(field_mappings: dict[str, str]) -> dict[str, Any]:

    warnings = []
    devops_field_count = 0
    proxy_field_count = 0

    STANDARD_JIRA_FIELDS = {
        "created",
        "resolutiondate",
        "updated",
        "status",
        "issuetype",
        "priority",
        "resolution",
    }

    DEVOPS_FIELD_PATTERNS = {
        "deployment",
        "deploy",
        "release",
        "incident",
        "production",
        "build",
        "pipeline",
    }

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

    for internal_field, field_info in CRITICAL_DORA_FIELDS.items():
        if internal_field not in field_mappings:
            warnings.append(
                {
                    "severity": "warning",
                    "field": internal_field,
                    "mapped_to": None,
                    "issue": "Field not mapped - "
                    f"{field_info['purpose']} will not be tracked",
                    "recommendation": field_info["recommendation"],
                }
            )
            continue

        jira_field = field_mappings[internal_field]

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
        elif any(pattern in jira_field.lower() for pattern in DEVOPS_FIELD_PATTERNS):
            devops_field_count += 1
            warnings.append(
                {
                    "severity": "info",
                    "field": internal_field,
                    "mapped_to": jira_field,
                    "issue": None,
                    "recommendation": "[OK] Appears to be a proper "
                    "DevOps tracking field",
                }
            )
        else:
            warnings.append(
                {
                    "severity": "warning",
                    "field": internal_field,
                    "mapped_to": jira_field,
                    "issue": "Verify this field tracks the intended data",
                    "recommendation": "Check JIRA field configuration and usage",
                }
            )

    error_count = sum(1 for w in warnings if w["severity"] == "error")

    if devops_field_count >= 3 and error_count == 0:
        validation_mode = "devops"
        compatibility_level = "full"
    elif devops_field_count >= 1 and error_count <= 2:
        validation_mode = "devops"
        compatibility_level = "partial"
    elif proxy_field_count >= 2:
        validation_mode = "issue_tracker"
        compatibility_level = "unsuitable"
    else:
        validation_mode = "unknown"
        compatibility_level = "partial"

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
