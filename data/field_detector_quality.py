"""Quality-gate field detection for JIRA custom fields.

Contains heuristic detectors for change-failure, deployment-successful,
and effort-category fields used for DORA Change Failure Rate and
Flow Distribution metrics.
"""

import logging

from data.field_detector_utils import (
    DETECTION_THRESHOLDS,
    _is_java_class_value,
)

logger = logging.getLogger(__name__)


def _detect_change_failure_field(
    issues: list[dict], field_defs: dict[str, dict]
) -> str | None:
    """Detect change failure field (deployment success/failure indicator).

    Heuristics:
    - Field name contains: "deployment", "success", "failure", "result"
    - Field type: checkbox (boolean), option (Yes/No)
    - Values: true/false, Success/Failed, Yes/No

    Note: May need inversion logic if field is "deployment successful" (Yes=good)
    vs "deployment failed" (Yes=bad)
    """
    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            # CRITICAL: Reject fields containing Java class names or complex objects
            if _is_java_class_value(field_value):
                continue

            score = 0

            # Name matching for success/failure indicators
            if any(
                kw in field_name
                for kw in [
                    "deployment success",
                    "deployment fail",
                    "rollback",
                    "deployment result",
                ]
            ):
                score += 50

            # Type should be boolean or option
            if field_type in ["option", "string", "array"]:
                score += 20

            # Check values for success/failure indicators
            if field_value:
                value_str = str(field_value).upper()
                if any(
                    indicator in value_str
                    for indicator in ["SUCCESS", "FAILED", "ROLLBACK", "ERROR"]
                ):
                    score += 30

            if score > 0:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": score,
                        "name": field_def.get("name", field_id),
                    }
                else:
                    candidates[field_id]["score"] += score

    if candidates:
        best = max(candidates.items(), key=lambda x: x[1]["score"])
        if best[1]["score"] >= 40:
            return best[0]

    return None


def _detect_deployment_successful_field(
    issues: list[dict], field_defs: dict[str, dict]
) -> str | None:
    """Detect deployment successful checkbox field for DORA Change Failure Rate.

    This is a checkbox (boolean) field variant of change_failure. Typical usage:
    - Field name: "Deployment Successful", "Deploy Success", "Succeeded"
    - Field type: checkbox (boolean) or option
    - Values: true/false (checkbox) or Yes/No (option)
    - Logic: true = successful deployment, false = failed deployment

    Heuristics:
    - Field name contains: "deployment successful", "deploy success", "succeeded"
    - Field type: MUST be checkbox (string type in schema) or option
    - Values: boolean or Yes/No strings

    Args:
        issues: List of JIRA issues with full field data
        field_defs: Dictionary of field definitions from metadata

    Returns:
        Field ID of deployment successful checkbox, or None if not found
    """
    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            # CRITICAL: Reject fields containing Java class names or complex objects
            if _is_java_class_value(field_value):
                continue

            score = 0

            # Name matching - specifically for "successful" variant (not "failure")
            if any(
                kw in field_name
                for kw in [
                    "deployment successful",
                    "deployment success",
                    "deploy success",
                    "deployment succeeded",
                    "deploy succeeded",
                    "successful deployment",
                ]
            ):
                score += 60  # Strong signal for positive indicator

            # Exclude "failure" fields (those belong to change_failure field)
            if any(kw in field_name for kw in ["fail", "failure", "rollback"]):
                score -= 100
                # Disqualify: this is change_failure, not deployment_successful.

            # Type should be string (checkbox) or option
            # CRITICAL: JIRA checkboxes appear as type="string" in schema, not "boolean"
            if field_type in ["string", "option"]:
                score += 30

            # Check values for boolean indicators
            if field_value:
                # Handle both boolean and string values
                if isinstance(field_value, bool):
                    score += 20  # Direct boolean value
                else:
                    value_str = str(field_value).upper()
                    if any(
                        indicator in value_str
                        for indicator in ["TRUE", "FALSE", "YES", "NO"]
                    ):
                        score += 20

            if score > 0:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": score,
                        "name": field_def.get("name", field_id),
                        "type": field_type,
                    }
                else:
                    candidates[field_id]["score"] += score

    if candidates:
        best = max(candidates.items(), key=lambda x: x[1]["score"])
        if best[1]["score"] >= DETECTION_THRESHOLDS["deployment_successful"]:
            logger.info(
                f"[FieldDetector] Deployment successful field candidate: {best[0]} "
                f"('{best[1]['name']}', type={best[1]['type']}, "
                f"score={best[1]['score']})"
            )
            return best[0]

    return None


def _detect_effort_category_field(
    issues: list[dict], field_defs: dict[str, dict]
) -> str | None:
    """Detect effort category field for Flow Distribution.

    Heuristics:
    - Field name contains: "effort", "category", "work type", "classification"
    - Field type: option, select, string
    - Values: Feature, Improvement, Bug Fix, Tech Debt, Risk, Documentation
    """
    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            # CRITICAL: Reject fields containing Java class names or complex objects
            if _is_java_class_value(field_value):
                continue

            score = 0

            # Name matching
            if any(
                kw in field_name
                for kw in [
                    "effort",
                    "category",
                    "work type",
                    "work classification",
                    "item type",
                ]
            ):
                score += 50

            # Type should be option/select
            if field_type in ["option", "string", "array"]:
                score += 20

            # Check values for work categories
            if field_value:
                value_str = str(field_value).upper()
                if any(
                    category in value_str
                    for category in [
                        "FEATURE",
                        "IMPROVEMENT",
                        "BUG",
                        "TECH DEBT",
                        "TECHNICAL",
                        "RISK",
                        "DOCUMENTATION",
                        "DOC",
                        "REFACTOR",
                    ]
                ):
                    score += 30

            if score > 0:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": score,
                        "name": field_def.get("name", field_id),
                    }
                else:
                    candidates[field_id]["score"] += score

    if candidates:
        best = max(candidates.items(), key=lambda x: x[1]["score"])
        if best[1]["score"] >= 40:
            return best[0]

    return None
