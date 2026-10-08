import logging
from collections import Counter
from typing import Any

from data.field_detector_basic import (
    _detect_code_commit_date_field,
    _detect_parent_field,
    _detect_points_field,
    _detect_sprint_field,
)
from data.field_detector_dora import (
    _detect_deployment_date_field,
    _detect_environment_field,
    _detect_incident_related_fields,
    _detect_priority_severity_field,
)
from data.field_detector_quality import (
    _detect_change_failure_field,
    _detect_deployment_successful_field,
    _detect_effort_category_field,
)
from data.field_detector_utils import (  # noqa: F401
    DETECTION_THRESHOLDS,
    JAVA_CLASS_PATTERNS,
    _is_java_class_value,
)

logger = logging.getLogger(__name__)


def detect_fields_from_issues(
    issues: list[dict[str, Any]], metadata: dict[str, Any]
) -> dict[str, str]:

    logger.info(f"[FieldDetector] Analyzing {len(issues)} issues for field detection")

    if not issues:
        logger.warning("[FieldDetector] No issues provided, cannot detect fields")
        return {}

    if issues:
        first_issue = issues[0]
        logger.info(
            f"[FieldDetector] DEBUG: First issue keys: {list(first_issue.keys())}"
        )
        logger.info(
            f"[FieldDetector] DEBUG: First issue sample: {str(first_issue)[:500]}"
        )

    field_defs = {f["id"]: f for f in metadata.get("fields", [])}

    common_types = _get_common_issue_types(issues)
    common_type_summary = ", ".join(
        f"{issue_type}={count}" for issue_type, count in common_types.most_common(5)
    )
    logger.info(f"[FieldDetector] Common issue types: {common_type_summary}")

    target_types = set(
        [itype for itype, count in common_types.most_common(10) if count > 1]
    )
    sampled_issues = [
        issue
        for issue in issues
        if issue.get("fields", {}).get("issuetype", {}).get("name") in target_types
    ]

    logger.info(
        f"[FieldDetector] Analyzing {len(sampled_issues)} issues "
        f"from common types: {target_types}"
    )

    detections = {}

    points_field = _detect_points_field(sampled_issues, field_defs)
    if points_field:
        detections["points_field"] = points_field
        logger.info(f"[FieldDetector] [OK] Story points field: {points_field}")

    sprint_field = _detect_sprint_field(sampled_issues, field_defs)
    if sprint_field:
        detections["sprint_field"] = sprint_field
        logger.info(f"[FieldDetector] [OK] Sprint field: {sprint_field}")

    parent_field = _detect_parent_field(sampled_issues, field_defs)
    if parent_field:
        detections["parent_field"] = parent_field
        logger.info(f"[FieldDetector] [OK] Parent/Epic Link field: {parent_field}")

    deployment_date = _detect_deployment_date_field(sampled_issues, field_defs)
    if deployment_date:
        detections["deployment_date"] = deployment_date
        logger.info(f"[FieldDetector] [OK] Deployment date field: {deployment_date}")
    else:
        logger.info(
            "[FieldDetector] No deployment_date field found. "
            "Fallback: Will use resolutiondate + status transitions from changelog"
        )

    environment_field = _detect_environment_field(sampled_issues, field_defs)
    if environment_field:
        detections["target_environment"] = environment_field
        logger.info(f"[FieldDetector] [OK] Environment field: {environment_field}")
    else:
        logger.info(
            "[FieldDetector] No environment field found. "
            "Configure manually if you need environment-specific DORA metrics"
        )

    change_failure = _detect_change_failure_field(sampled_issues, field_defs)
    if change_failure:
        detections["change_failure"] = change_failure
        logger.info(f"[FieldDetector] [OK] Change failure field: {change_failure}")

    deployment_successful = _detect_deployment_successful_field(
        sampled_issues, field_defs
    )
    if deployment_successful:
        detections["deployment_successful"] = deployment_successful
        logger.info(
            f"[FieldDetector] [OK] Deployment successful field: {deployment_successful}"
        )

    incident_fields = _detect_incident_related_fields(sampled_issues, field_defs)
    if incident_fields["incident_detected_at"]:
        detections["incident_detected_at"] = incident_fields["incident_detected_at"]
        detected_at_field = incident_fields["incident_detected_at"]
        logger.info(
            f"[FieldDetector] [OK] Incident detection field: {detected_at_field}"
        )
    if incident_fields["incident_resolved_at"]:
        detections["incident_resolved_at"] = incident_fields["incident_resolved_at"]
        resolved_at_field = incident_fields["incident_resolved_at"]
        logger.info(
            f"[FieldDetector] [OK] Incident resolution field: {resolved_at_field}"
        )

    severity_field = _detect_priority_severity_field(sampled_issues, field_defs)
    if severity_field:
        detections["severity_level"] = severity_field
        logger.info(f"[FieldDetector] [OK] Severity/Priority field: {severity_field}")
    else:
        logger.info(
            "[FieldDetector] No custom severity field found. "
            "Fallback: Will use standard priority field"
        )

    effort_category = _detect_effort_category_field(sampled_issues, field_defs)
    if effort_category:
        detections["effort_category"] = effort_category
        logger.info(f"[FieldDetector] [OK] Effort category field: {effort_category}")
    else:
        logger.info(
            "[FieldDetector] No effort category field found. "
            "Fallback: Will use issue type classification (Bug/Story/Task)"
        )

    code_commit_date = _detect_code_commit_date_field(sampled_issues, field_defs)
    if code_commit_date:
        detections["code_commit_date"] = code_commit_date
        logger.info(f"[FieldDetector] [OK] Code commit date field: {code_commit_date}")
    else:
        logger.info(
            "[FieldDetector] No code commit date field found. "
            "Fallback: Will use created date or changelog transitions"
        )

    logger.info(f"[FieldDetector] Detected {len(detections)} custom fields total")
    logger.info(
        "[FieldDetector] Fallback strategies active for fields not detected. "
        "Variable extraction will use standard fields + changelog data."
    )
    return detections


def _get_common_issue_types(issues: list[dict]) -> Counter:
    type_counter = Counter()
    for issue in issues:
        issue_type = issue.get("fields", {}).get("issuetype", {}).get("name")
        if issue_type:
            type_counter[issue_type] += 1
    return type_counter
