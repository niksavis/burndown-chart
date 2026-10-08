import logging
import re

from data.field_detector_utils import (
    DETECTION_THRESHOLDS,
    _is_java_class_value,
)

logger = logging.getLogger(__name__)


def _detect_deployment_date_field(
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

            score = 0

            if any(
                keyword in field_name
                for keyword in [
                    "deploy",
                    "deployment",
                    "release date",
                    "released",
                    "production date",
                    "prod date",
                    "go live",
                ]
            ):
                score += 50

            if field_type in ["datetime", "date"]:
                score += 40
            else:
                score -= 30

            if field_type in ["datetime", "date"]:
                score += 30

            if field_value and isinstance(field_value, str):
                if re.match(r"\d{4}-\d{2}-\d{2}", field_value):
                    score += 20

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
        if best[1]["score"] >= DETECTION_THRESHOLDS["deployment_date"]:
            return best[0]

    return None


def _detect_environment_field(
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

            score = 0

            if _is_java_class_value(field_value):
                continue

            if any(
                keyword in field_name
                for keyword in [
                    "environment",
                    "env",
                    "target env",
                    "deployment env",
                    "affected env",
                ]
            ):
                score += 50

            if field_type in ["option", "string", "array"]:
                score += 20
            elif field_type in ["datetime", "date"]:
                score -= 40

            if field_value:
                value_str = str(field_value).upper()
                if any(
                    env in value_str
                    for env in [
                        "PROD",
                        "PRODUCTION",
                        "STAGING",
                        "STAGE",
                        "DEV",
                        "DEVELOPMENT",
                        "QA",
                        "TEST",
                        "TESTING",
                        "UAT",
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
        if best[1]["score"] >= DETECTION_THRESHOLDS["change_failure"]:
            return best[0]

    return None


def _detect_incident_related_fields(
    issues: list[dict], field_defs: dict[str, dict]
) -> dict[str, str | None]:

    detected_field = None
    resolved_field = None

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, _field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            if not detected_field:
                if field_type in ["datetime", "date"] and any(
                    kw in field_name
                    for kw in ["incident start", "detected at", "failure time"]
                ):
                    detected_field = field_id

            if not resolved_field:
                if field_type in ["datetime", "date"] and any(
                    kw in field_name
                    for kw in ["incident resolved", "resolution time", "fixed at"]
                ):
                    resolved_field = field_id

    return {
        "incident_detected_at": detected_field,
        "incident_resolved_at": resolved_field,
    }


def _detect_priority_severity_field(
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

            score = 0

            if any(
                kw in field_name
                for kw in ["severity", "priority", "criticality", "impact"]
            ):
                score += 50

            if field_type in ["option", "string"]:
                score += 20

            if field_value:
                value_str = str(field_value).upper()
                if any(
                    level in value_str
                    for level in [
                        "CRITICAL",
                        "HIGH",
                        "MEDIUM",
                        "LOW",
                        "BLOCKER",
                        "MAJOR",
                        "MINOR",
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
