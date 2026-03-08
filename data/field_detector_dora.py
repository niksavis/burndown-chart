"""DORA-specific field detection for JIRA custom fields.

Contains heuristic detectors for deployment, environment, incident,
priority/severity, change-failure, effort-category, and related fields
used to compute DORA metrics.
"""

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
    """Detect deployment date field for DORA metrics.

    Heuristics:
    - Field name contains: "deploy", "release date", "production date"
    - Field type: datetime, date
    - Values: ISO date strings
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

            score = 0

            # Rule 1: Name matching
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

            # Rule 2: Field type MUST be datetime for deployment dates
            if field_type in ["datetime", "date"]:
                score += 40  # Strong boost for datetime fields
            else:
                score -= 30  # Heavily penalize non-datetime fields

            # Rule 2: Type is datetime
            if field_type in ["datetime", "date"]:
                score += 30

            # Rule 3: Check value format (ISO date)
            if field_value and isinstance(field_value, str):
                if re.match(r"\d{4}-\d{2}-\d{2}", field_value):  # ISO date format
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
    """Detect environment field for DORA metrics.

    Heuristics:
    - Field name contains: "environment", "env", "target"
    - Field type: select, string
    - Values: DEV, STAGING, PROD, QA, etc.
    - Fallback: Any field with environment-like values (production, staging, testing)
    - REJECT: Fields with Java class names (com.atlassian.*) or complex objects
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

            score = 0

            # CRITICAL: Reject fields containing Java class names or complex objects
            if _is_java_class_value(field_value):
                continue

            # Rule 1: Name matching (strongest signal)
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

            # Rule 2: Type should be select/option/string (NOT datetime)
            if field_type in ["option", "string", "array"]:
                score += 20  # Boost appropriate field types
            elif field_type in ["datetime", "date"]:
                score -= 40  # Heavily penalize datetime fields for environment

            # Rule 3: Check value content (common environment names) - FALLBACK strategy
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
                    score += 30  # Strong signal even without name match

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
    """Detect incident-related fields for DORA MTTR metric.

    Returns:
        Dict with 'incident_detected_at' and 'incident_resolved_at' fields

    Fallback strategy: Use status transitions for Bug/Defect types
    - incident_detected_at → created date (issues already have this)
    - incident_resolved_at → resolution date or status change to Done
    """
    # For incidents, we typically use standard fields:
    # - Detected: created date (always available)
    # - Resolved: resolutiondate or changelog transition to completion status
    # These are handled by variable extraction, not custom field detection
    #
    # However, check for explicit incident tracking fields
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

            # Detect incident start/detection time
            if not detected_field:
                if field_type in ["datetime", "date"] and any(
                    kw in field_name
                    for kw in ["incident start", "detected at", "failure time"]
                ):
                    detected_field = field_id

            # Detect incident resolution time
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
    """Detect priority/severity field for incident classification.

    Heuristics:
    - Field name contains: "priority", "severity", "criticality"
    - Field type: option, select, string
    - Values: Critical, High, Medium, Low, Blocker, etc.
    """
    # Priority is usually a standard Jira field, but check for custom severity
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

            # Name matching
            if any(
                kw in field_name
                for kw in ["severity", "priority", "criticality", "impact"]
            ):
                score += 50

            # Type should be option/select
            if field_type in ["option", "string"]:
                score += 20

            # Check values
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
