"""
Configuration Validation Helpers

Provides validation functions for comprehensive JIRA mappings configuration.
"""

import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def validate_subset(
    subset: List[str], superset: List[str], subset_name: str, superset_name: str
) -> Tuple[bool, str]:
    """
    Validate that one list is a subset of another.

    Args:
        subset: List that should be contained in superset
        superset: List that should contain all subset elements
        subset_name: Human-readable name for subset (for error messages)
        superset_name: Human-readable name for superset (for error messages)

    Returns:
        Tuple of (is_valid, warning_message)
    """
    if not subset:
        return True, ""  # Empty subset is valid

    if not superset:
        return False, f"{superset_name} is empty but {subset_name} has values"

    subset_set = set(subset)
    superset_set = set(superset)

    if subset_set.issubset(superset_set):
        return True, ""

    # Find elements not in superset
    missing = subset_set - superset_set
    return (
        False,
        f"{subset_name} contains values not in {superset_name}: {', '.join(missing)}",
    )


def validate_project_overlap(
    development_projects: List[str], devops_projects: List[str]
) -> Tuple[bool, str]:
    """
    Check if there's overlap between development and devops projects.

    Args:
        development_projects: List of development project keys
        devops_projects: List of devops project keys

    Returns:
        Tuple of (has_overlap, warning_message)
    """
    dev_set = set(development_projects)
    devops_set = set(devops_projects)

    overlap = dev_set & devops_set

    if overlap:
        return (
            True,
            f"Projects appear in both lists: {', '.join(overlap)}. This is unusual but allowed.",
        )

    return False, ""


def validate_required_fields(
    config: Dict[str, Any], required_keys: List[str]
) -> Tuple[bool, List[str]]:
    """
    Validate that required configuration keys are present and non-empty.

    Args:
        config: Configuration dictionary
        required_keys: List of required key names

    Returns:
        Tuple of (is_valid, list_of_missing_keys)
    """
    missing_keys = []

    for key in required_keys:
        value = config.get(key)

        # Check if key exists and has a value
        if value is None:
            missing_keys.append(key)
        elif isinstance(value, (list, str)) and not value:
            missing_keys.append(key)

    return len(missing_keys) == 0, missing_keys


def validate_active_wip_subset(
    active_statuses: List[str], wip_statuses: List[str]
) -> Tuple[bool, str]:
    """
    Validate that active statuses are a subset of WIP statuses.

    This is critical for metric accuracy - active work should always be part of WIP.

    Args:
        active_statuses: List of active status names
        wip_statuses: List of WIP status names

    Returns:
        Tuple of (is_valid, warning_message)
    """
    return validate_subset(
        active_statuses, wip_statuses, "Active statuses", "WIP statuses"
    )


def validate_comprehensive_config(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Comprehensive validation of all configuration elements.

    Args:
        config: Complete configuration dictionary

    Returns:
        Dictionary with 'errors' and 'warnings' keys containing lists of messages
    """
    errors = []
    warnings = []

    # Field mappings validation - distinguish between required and optional
    # CRITICAL: Only Flow metrics baseline fields are truly required
    # DORA fields are optional since not all JIRA setups support them
    required_flow_fields = [
        "flow_item_type",  # Required for Flow metrics
        "work_completed_date",  # Required for Flow metrics
    ]

    # Optional DORA fields - warn if missing but don't block saving
    optional_dora_fields = [
        "deployment_date",  # DORA: Deployment Frequency
        "change_failure",  # DORA: Change Failure Rate
        "affected_environment",  # DORA: MTTR production filtering
        "incident_detected_at",  # DORA: MTTR
        "incident_resolved_at",  # DORA: MTTR
    ]

    # Access nested field mappings (flow and dora are sub-objects)
    field_mappings = config.get("field_mappings", {})
    flow_mappings = field_mappings.get("flow", {})
    dora_mappings = field_mappings.get("dora", {})

    # Check required FLOW fields (errors)
    for field in required_flow_fields:
        if not flow_mappings.get(field):
            errors.append(f"Required field mapping missing: {field}")

    # Check optional DORA fields (warnings only)
    missing_dora_fields = []
    for field in optional_dora_fields:
        if not dora_mappings.get(field):
            missing_dora_fields.append(field)

    if missing_dora_fields:
        warnings.append(
            f"Optional DORA field mappings not configured: {', '.join(missing_dora_fields)}. "
            "Some DORA metrics may be unavailable."
        )

    # Project validation
    dev_projects = config.get("development_projects", [])
    devops_projects = config.get("devops_projects", [])

    if not dev_projects:
        errors.append("At least one development project is required")

    # MODE 1 vs MODE 2 guidance
    if not devops_projects:
        warnings.append(
            "DevOps projects empty - using MODE 2 (field-based DORA detection). "
            "Configure field_mappings for DORA metrics to work."
        )

    has_overlap, overlap_msg = validate_project_overlap(dev_projects, devops_projects)
    if has_overlap:
        warnings.append(overlap_msg)

    # Issue type validation
    devops_task_types = config.get("devops_task_types", [])
    bug_types = config.get("bug_types", [])

    if not devops_task_types:
        warnings.append(
            "DevOps task types empty - DORA Deployment Frequency will not work"
        )

    if not bug_types:
        warnings.append(
            "Incident types empty - DORA MTTR will not work without production incident issue types"
        )

    # Status validation
    completion_statuses = config.get("completion_statuses", [])
    active_statuses = config.get("active_statuses", [])
    wip_statuses = config.get("wip_statuses", [])

    if not completion_statuses:
        errors.append("At least one completion status is required")

    is_valid, warning_msg = validate_active_wip_subset(active_statuses, wip_statuses)
    if not is_valid:
        warnings.append(
            f"Active statuses should be subset of WIP statuses. {warning_msg}"
        )

    # Environment validation
    prod_env_values = config.get("production_environment_values", [])
    affected_env_field = dora_mappings.get("affected_environment", "")

    # Only warn about production values if affected_environment is configured
    if affected_env_field and not prod_env_values:
        warnings.append(
            "Production environment values empty - MTTR will include all bugs (not just production)"
        )

    return {"errors": errors, "warnings": warnings}


def format_validation_messages(validation_result: Dict[str, List[str]]) -> str:
    """
    Format validation results into a human-readable message.

    Args:
        validation_result: Dictionary with 'errors' and 'warnings' keys

    Returns:
        Formatted string with validation messages
    """
    messages = []

    errors = validation_result.get("errors", [])
    if errors:
        messages.append("[!] Errors:")
        for error in errors:
            messages.append(f"  • {error}")

    warnings = validation_result.get("warnings", [])
    if warnings:
        if messages:
            messages.append("")  # Blank line separator
        messages.append("[!] Warnings:")
        for warning in warnings:
            messages.append(f"  • {warning}")

    if not messages:
        return "[OK] Configuration is valid"

    return "\n".join(messages)
