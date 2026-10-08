import logging

from data.field_detector_utils import (
    DETECTION_THRESHOLDS,
    _is_java_class_value,
)

logger = logging.getLogger(__name__)


def _detect_change_failure_field(
    issues: list[dict], field_defs: dict[str, dict]
) -> str | None:

    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            if _is_java_class_value(field_value):
                continue

            score = 0

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

            if field_type in ["option", "string", "array"]:
                score += 20

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

    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            if _is_java_class_value(field_value):
                continue

            score = 0

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
                score += 60

            if any(kw in field_name for kw in ["fail", "failure", "rollback"]):
                score -= 100

            if field_type in ["string", "option"]:
                score += 30

            if field_value:
                if isinstance(field_value, bool):
                    score += 20
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

    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            if _is_java_class_value(field_value):
                continue

            score = 0

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

            if field_type in ["option", "string", "array"]:
                score += 20

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
