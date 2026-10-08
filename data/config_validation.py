import logging
from typing import Any

logger = logging.getLogger(__name__)


def validate_subset(
    subset: list[str], superset: list[str], subset_name: str, superset_name: str
) -> tuple[bool, str]:

    if not subset:
        return True, ""

    if not superset:
        return False, f"{superset_name} is empty but {subset_name} has values"

    subset_set = set(subset)
    superset_set = set(superset)

    if subset_set.issubset(superset_set):
        return True, ""

    missing = subset_set - superset_set
    return (
        False,
        f"{subset_name} contains values not in {superset_name}: {', '.join(missing)}",
    )


def validate_project_overlap(
    development_projects: list[str], devops_projects: list[str]
) -> tuple[bool, str]:

    dev_set = set(development_projects)
    devops_set = set(devops_projects)

    overlap = dev_set & devops_set

    if overlap:
        return (
            True,
            "Projects appear in both lists: "
            f"{', '.join(overlap)}. This is unusual but allowed.",
        )

    return False, ""


def validate_required_fields(
    config: dict[str, Any], required_keys: list[str]
) -> tuple[bool, list[str]]:

    missing_keys = []

    for key in required_keys:
        value = config.get(key)

        if value is None:
            missing_keys.append(key)
        elif isinstance(value, (list, str)) and not value:
            missing_keys.append(key)

    return len(missing_keys) == 0, missing_keys


def validate_active_wip_subset(
    active_statuses: list[str], wip_statuses: list[str]
) -> tuple[bool, str]:

    return validate_subset(
        active_statuses, wip_statuses, "Active statuses", "WIP statuses"
    )


def validate_wip_excludes_completion(
    wip_statuses: list[str], flow_end_statuses: list[str]
) -> tuple[bool, str]:

    if not wip_statuses or not flow_end_statuses:
        return True, ""

    wip_set = set(wip_statuses)
    end_set = set(flow_end_statuses)

    overlap = wip_set & end_set

    if overlap:
        return (
            False,
            "WIP statuses should NOT include completion statuses. "
            f"Found: {', '.join(overlap)}. "
            "This causes Flow Load (WIP count) to incorrectly include completed items.",
        )

    return True, ""


def validate_comprehensive_config(config: dict[str, Any]) -> dict[str, list[str]]:

    errors = []
    warnings = []

    required_flow_fields = [
        "flow_item_type",
    ]

    optional_dora_fields = [
        "deployment_date",
        "change_failure",
        "affected_environment",
        "incident_detected_at",
        "incident_resolved_at",
    ]

    field_mappings = config.get("field_mappings", {})
    flow_mappings = field_mappings.get("flow", {})
    dora_mappings = field_mappings.get("dora", {})

    for field in required_flow_fields:
        if not flow_mappings.get(field):
            errors.append(f"Required field mapping missing: {field}")

    missing_dora_fields = []
    for field in optional_dora_fields:
        if not dora_mappings.get(field):
            missing_dora_fields.append(field)

    if missing_dora_fields:
        warnings.append(
            "Optional DORA field mappings not configured: "
            f"{', '.join(missing_dora_fields)}. "
            "Some DORA metrics may be unavailable."
        )

    dev_projects = config.get("development_projects", [])
    devops_projects = config.get("devops_projects", [])

    if not dev_projects:
        errors.append("At least one development project is required")

    if not devops_projects:
        warnings.append(
            "DevOps projects empty - using MODE 2 (field-based DORA detection). "
            "Configure field_mappings for DORA metrics to work."
        )

    has_overlap, overlap_msg = validate_project_overlap(dev_projects, devops_projects)
    if has_overlap:
        warnings.append(overlap_msg)

    devops_task_types = config.get("devops_task_types", [])
    bug_types = config.get("bug_types", [])

    if not devops_task_types:
        warnings.append(
            "DevOps task types empty - DORA Deployment Frequency will not work"
        )

    if not bug_types:
        warnings.append(
            "Incident types empty - DORA MTTR will not work "
            "without production incident issue types"
        )

    flow_end_statuses = config.get("flow_end_statuses", [])
    active_statuses = config.get("active_statuses", [])
    wip_statuses = config.get("wip_statuses", [])

    if not flow_end_statuses:
        errors.append("At least one completion status is required")

    is_valid, warning_msg = validate_active_wip_subset(active_statuses, wip_statuses)
    if not is_valid:
        warnings.append(
            f"Active statuses should be subset of WIP statuses. {warning_msg}"
        )

    is_valid, warning_msg = validate_wip_excludes_completion(
        wip_statuses, flow_end_statuses
    )
    if not is_valid:
        errors.append(warning_msg)

    prod_env_values = config.get("production_environment_values", [])
    affected_env_field = dora_mappings.get("affected_environment", "")

    if affected_env_field and not prod_env_values:
        warnings.append(
            "Production environment values empty - MTTR will include all bugs "
            "(not just production)"
        )

    return {"errors": errors, "warnings": warnings}


def format_validation_messages(validation_result: dict[str, list[str]]) -> str:

    messages = []

    errors = validation_result.get("errors", [])
    if errors:
        messages.append("[!] Errors:")
        for error in errors:
            messages.append(f"  • {error}")

    warnings = validation_result.get("warnings", [])
    if warnings:
        if messages:
            messages.append("")
        messages.append("[!] Warnings:")
        for warning in warnings:
            messages.append(f"  • {warning}")

    if not messages:
        return "[OK] Configuration is valid"

    return "\n".join(messages)
