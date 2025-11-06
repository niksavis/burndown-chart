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

    # Required fields validation
    required_field_mappings = [
        "deployment_date",
        "change_failure",
        "affected_environment",
        "flow_item_type",
        "work_started_date",
        "work_completed_date",
    ]

    field_mappings = config.get("field_mappings", {})
    for field in required_field_mappings:
        if not field_mappings.get(field):
            errors.append(f"Required field mapping missing: {field}")

    # Project validation
    dev_projects = config.get("development_projects", [])
    devops_projects = config.get("devops_projects", [])

    if not dev_projects:
        errors.append("At least one development project is required")

    if not devops_projects:
        warnings.append("DevOps projects empty - DORA metrics will not work")

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
    if not prod_env_values:
        warnings.append(
            "Production environment values empty - MTTR calculation will not work"
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
        messages.append("❌ Errors:")
        for error in errors:
            messages.append(f"  • {error}")

    warnings = validation_result.get("warnings", [])
    if warnings:
        if messages:
            messages.append("")  # Blank line separator
        messages.append("⚠️ Warnings:")
        for warning in warnings:
            messages.append(f"  • {warning}")

    if not messages:
        return "✅ Configuration is valid"

    return "\n".join(messages)
