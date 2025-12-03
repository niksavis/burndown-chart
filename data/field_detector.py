"""Smart field detection for JIRA custom fields.

Analyzes actual issue data to detect which custom fields are used for:
- Story points / effort estimation
- Sprint information
- Deployment tracking
- Environment values
"""

import logging
from typing import Dict, List, Any, Optional
from collections import Counter
import re

logger = logging.getLogger(__name__)

# Detection confidence thresholds (minimum scores required)
# Lower thresholds = more lenient detection (catches sparse data)
# Higher thresholds = stricter detection (reduces false positives)
#
# These thresholds are calibrated for typical JIRA instances where:
# - 30-50% of issues have the field populated
# - Field names follow common naming conventions
# - Values match expected patterns
#
# For sparse JIRA instances (e.g., Apache JIRA, open-source projects):
# - Fields may exist but have <30% population
# - Fallback to manual configuration recommended
# - Future enhancement: Make thresholds configurable per installation
DETECTION_THRESHOLDS = {
    "deployment_date": 40,  # Datetime fields - strict to avoid false positives
    "deployment_successful": 40,  # Boolean fields - strict to avoid false positives
    "sprint": 40,  # Sprint fields - strict due to many custom fields
    "environment": 30,  # Environment fields - lenient to catch variants
    "change_failure": 30,  # Boolean/select fields - lenient for sparse data
    "effort_category": 30,  # Classification fields - lenient for new setups
}

# Java class patterns to filter out from field detection
# These are typically JIRA's internal plugin fields (Development panel, etc.)
# that contain complex Java object references instead of user-facing values
JAVA_CLASS_PATTERNS = [
    "com.atlassian",
    "java.lang",
    "beans.",
    "Summary/ItemBean",
    "BranchOverall",
    "DeploymentOverall",
    "PullRequestOverall",
    "RepositoryOverall",
]


def _is_java_class_value(field_value: Any) -> bool:
    """Check if a field value contains Java class names (internal JIRA plugin data).

    Args:
        field_value: The value to check (can be any type)

    Returns:
        True if the value contains Java class patterns, False otherwise
    """
    if not field_value:
        return False
    value_str = str(field_value)
    return any(pattern in value_str for pattern in JAVA_CLASS_PATTERNS)


def _detect_code_commit_date_field(
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
    """Detect code commit date field for DORA Lead Time.

    Heuristics:
    - Field name contains: "commit", "code", "merge", "push", "git"
    - Field type: datetime
    - Has date values in the past
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

            # Name matching
            if any(
                kw in field_name
                for kw in [
                    "commit",
                    "code commit",
                    "git",
                    "merge",
                    "push",
                    "source control",
                    "scm",
                ]
            ):
                score += 60

            # Type must be datetime
            if field_type == "datetime":
                score += 40
            elif field_type == "date":
                score += 30

            # Has timestamp value
            if field_value:
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
        if best[1]["score"] >= 60:
            return best[0]

    return None


def _detect_completed_date_field(
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
    """Detect completed date field for Flow metrics (alternative to resolutiondate).

    Heuristics:
    - Field name contains: "completed", "resolved", "resolution"
    - Field type: datetime
    - Has date values in the past
    - Different from work_completed_date (broader matching)
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

            # Name matching (broader than work_completed_date)
            if any(
                kw in field_name
                for kw in [
                    "completed",
                    "resolved",
                    "resolution",
                    "finish",
                    "done date",
                    "closed date",
                ]
            ):
                score += 60

            # Type must be datetime
            if field_type == "datetime":
                score += 40
            elif field_type == "date":
                score += 30

            # Has timestamp value
            if field_value:
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
        if best[1]["score"] >= 60:
            return best[0]

    return None


def detect_fields_from_issues(
    issues: List[Dict[str, Any]], metadata: Dict[str, Any]
) -> Dict[str, str]:
    """Detect custom field mappings by analyzing actual issue data.

    Strategy:
    1. Get sample of recent issues (last 100)
    2. Focus on common issue types (Story, Task, Bug)
    3. Analyze field names, types, and actual values
    4. Use fuzzy matching and heuristics to identify fields

    Args:
        issues: List of JIRA issues with full field data
        metadata: JIRA metadata with field definitions

    Returns:
        Dict of field mappings: {
            "points_field": "customfield_10016",
            "sprint_field": "customfield_10020",
            "deployment_date": "customfield_12345",
            "target_environment": "customfield_12346"
        }
    """
    logger.info(f"[FieldDetector] Analyzing {len(issues)} issues for field detection")

    if not issues:
        logger.warning("[FieldDetector] No issues provided, cannot detect fields")
        return {}

    # DEBUG: Check structure of first issue
    if issues:
        first_issue = issues[0]
        logger.info(
            f"[FieldDetector] DEBUG: First issue keys: {list(first_issue.keys())}"
        )
        logger.info(
            f"[FieldDetector] DEBUG: First issue sample: {str(first_issue)[:500]}"
        )

    # Get field definitions from metadata
    field_defs = {f["id"]: f for f in metadata.get("fields", [])}

    # Sample issues from common types (Story, Task, Bug, Epic, Feature, etc.)
    common_types = _get_common_issue_types(issues)
    logger.info(
        f"[FieldDetector] Common issue types: {', '.join(f'{k}={v}' for k, v in common_types.most_common(5))}"
    )

    # Focus on top issue types for analysis
    target_types = set(
        [
            itype
            for itype, count in common_types.most_common(10)
            if count > 1  # At least 2 issues
        ]
    )
    sampled_issues = [
        issue
        for issue in issues
        if issue.get("fields", {}).get("issuetype", {}).get("name") in target_types
    ]

    logger.info(
        f"[FieldDetector] Analyzing {len(sampled_issues)} issues from common types: {target_types}"
    )

    # Detect different field types with smart fallbacks
    detections = {}

    # === BASIC FIELDS ===
    # 1. Detect story points field
    points_field = _detect_points_field(sampled_issues, field_defs)
    if points_field:
        detections["points_field"] = points_field
        logger.info(f"[FieldDetector] [OK] Story points field: {points_field}")

    # 2. Detect sprint field
    sprint_field = _detect_sprint_field(sampled_issues, field_defs)
    if sprint_field:
        detections["sprint_field"] = sprint_field
        logger.info(f"[FieldDetector] [OK] Sprint field: {sprint_field}")

    # === DORA METRICS FIELDS ===
    # 3. Detect deployment date field
    # Fallback: Use resolutiondate (standard field) via variable extraction
    deployment_date = _detect_deployment_date_field(sampled_issues, field_defs)
    if deployment_date:
        detections["deployment_date"] = deployment_date
        logger.info(f"[FieldDetector] [OK] Deployment date field: {deployment_date}")
    else:
        logger.info(
            "[FieldDetector] No deployment_date field found. "
            "Fallback: Will use resolutiondate + status transitions from changelog"
        )

    # 4. Detect environment field
    # Fallback: Search for any field with production/staging/testing values
    environment_field = _detect_environment_field(sampled_issues, field_defs)
    if environment_field:
        detections["target_environment"] = environment_field
        logger.info(f"[FieldDetector] [OK] Environment field: {environment_field}")
    else:
        logger.info(
            "[FieldDetector] No environment field found. "
            "Configure manually if you need environment-specific DORA metrics"
        )

    # 5. Detect change failure field (optional)
    change_failure = _detect_change_failure_field(sampled_issues, field_defs)
    if change_failure:
        detections["change_failure"] = change_failure
        logger.info(f"[FieldDetector] [OK] Change failure field: {change_failure}")

    # 5b. Detect deployment successful field (checkbox variant of change_failure)
    deployment_successful = _detect_deployment_successful_field(
        sampled_issues, field_defs
    )
    if deployment_successful:
        detections["deployment_successful"] = deployment_successful
        logger.info(
            f"[FieldDetector] [OK] Deployment successful field: {deployment_successful}"
        )

    # 6. Detect incident fields
    # Fallback: Use created + resolutiondate for Bug/Defect issue types
    incident_fields = _detect_incident_related_fields(sampled_issues, field_defs)
    if incident_fields["incident_detected_at"]:
        detections["incident_detected_at"] = incident_fields["incident_detected_at"]
        logger.info(
            f"[FieldDetector] [OK] Incident detection field: {incident_fields['incident_detected_at']}"
        )
    if incident_fields["incident_resolved_at"]:
        detections["incident_resolved_at"] = incident_fields["incident_resolved_at"]
        logger.info(
            f"[FieldDetector] [OK] Incident resolution field: {incident_fields['incident_resolved_at']}"
        )

    # 7. Detect priority/severity field
    # Fallback: Use standard priority field (always available in Jira)
    severity_field = _detect_priority_severity_field(sampled_issues, field_defs)
    if severity_field:
        detections["severity_level"] = severity_field
        logger.info(f"[FieldDetector] [OK] Severity/Priority field: {severity_field}")
    else:
        logger.info(
            "[FieldDetector] No custom severity field found. "
            "Fallback: Will use standard priority field"
        )

    # === FLOW METRICS FIELDS ===
    # 8. Detect effort category field (for Flow Distribution)
    # Fallback: Use issue type classification
    effort_category = _detect_effort_category_field(sampled_issues, field_defs)
    if effort_category:
        detections["effort_category"] = effort_category
        logger.info(f"[FieldDetector] [OK] Effort category field: {effort_category}")
    else:
        logger.info(
            "[FieldDetector] No effort category field found. "
            "Fallback: Will use issue type classification (Bug/Story/Task)"
        )

    # 9. Detect code commit date field (for DORA Lead Time)
    # Fallback: Use created date or status transitions from changelog
    code_commit_date = _detect_code_commit_date_field(sampled_issues, field_defs)
    if code_commit_date:
        detections["code_commit_date"] = code_commit_date
        logger.info(f"[FieldDetector] [OK] Code commit date field: {code_commit_date}")
    else:
        logger.info(
            "[FieldDetector] No code commit date field found. "
            "Fallback: Will use created date or changelog transitions"
        )

    # Note: work_started_date and work_completed_date detection removed.
    # Flow Time now uses flow_start_statuses and completion_statuses lists
    # from project_classification to find status transitions in changelog.

    logger.info(f"[FieldDetector] Detected {len(detections)} custom fields total")
    logger.info(
        "[FieldDetector] Fallback strategies active for fields not detected. "
        "Variable extraction will use standard fields + changelog data."
    )
    return detections


def _get_common_issue_types(issues: List[Dict]) -> Counter:
    """Count issue types in the sample to identify most common."""
    type_counter = Counter()
    for issue in issues:
        issue_type = issue.get("fields", {}).get("issuetype", {}).get("name")
        if issue_type:
            type_counter[issue_type] += 1
    return type_counter


def _detect_points_field(
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
    """Detect story points field using fuzzy matching and data analysis.

    Heuristics:
    - Field name contains: "story point", "estimate", "effort", "size"
    - Field type: number
    - Values: Small positive numbers (typically 1-100)
    - Usage: Present in Story/Task issues, often missing in Bugs
    """
    candidates = {}

    # DEBUG: Track custom fields found
    custom_fields_seen = set()

    # Scan all custom fields in issues
    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            # Only check custom fields
            if not field_id.startswith("customfield_"):
                continue

            custom_fields_seen.add(field_id)

            # Skip if already ruled out
            if field_id in candidates and candidates[field_id]["score"] == 0:
                continue

            # Get field definition
            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            # Initialize candidate tracking
            if field_id not in candidates:
                candidates[field_id] = {
                    "score": 0,
                    "name": field_def.get("name", field_id),
                    "type": field_type,
                    "values": [],
                }

            # Scoring rules
            score = 0

            # Rule 1: Field name matching (strongest signal)
            if any(
                keyword in field_name
                for keyword in ["story point", "storypoint", "points", "estimate"]
            ):
                score += 50

            # Rule 2: Field type is number (CRITICAL for story points)
            if field_type in ["number", "float"]:
                score += 30  # Increased from 20 - numeric type is essential
            else:
                score -= 20  # Penalize non-numeric fields

            # Rule 3: Check actual value
            if field_value is not None:
                candidates[field_id]["values"].append(field_value)

                # Numeric values between 0-100 (typical story point range)
                if isinstance(field_value, (int, float)):
                    if 0 < field_value <= 100:
                        score += 15
                    elif field_value > 1000:  # Too large to be story points
                        score -= 30
                else:
                    # Non-numeric disqualifies as story points
                    score -= 50

            candidates[field_id]["score"] += score

    # DEBUG: Log what custom fields were found
    logger.info(
        f"[FieldDetector] DEBUG: Found {len(custom_fields_seen)} unique custom fields in {len(issues)} issues"
    )
    if custom_fields_seen:
        sample_fields = list(custom_fields_seen)[:10]
        logger.info(f"[FieldDetector] DEBUG: Sample custom fields: {sample_fields}")

    # Find best candidate
    if not candidates:
        logger.warning(
            f"[FieldDetector] No story points candidates found. Total custom fields scanned: {len(custom_fields_seen)}"
        )
        return None

    # Filter out negative scores
    candidates = {k: v for k, v in candidates.items() if v["score"] > 0}

    if not candidates:
        return None

    # Sort by score
    best_candidate = max(candidates.items(), key=lambda x: x[1]["score"])

    logger.info(
        f"[FieldDetector] Points field candidates: {[(k, v['score'], v['name']) for k, v in sorted(candidates.items(), key=lambda x: x[1]['score'], reverse=True)[:3]]}"
    )

    # Return if score is confident enough
    if best_candidate[1]["score"] >= 30:  # Minimum confidence threshold
        return best_candidate[0]

    return None


def _detect_sprint_field(
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
    """Detect sprint field.

    Heuristics:
    - Field name contains: "sprint"
    - Field type: array, string, or custom sprint type
    - Values: Sprint names/objects with sprint data
    - CRITICAL: Must have actual sprint data in at least 10% of sampled issues
    """
    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()

            # Strong signal: "sprint" in name
            if "sprint" in field_name:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": 0,
                        "name": field_def.get("name", field_id),
                        "populated_count": 0,
                        "total_count": 0,
                    }

                # Check if field has actual sprint data (not null/empty)
                candidates[field_id]["total_count"] += 1
                if field_value:  # Has sprint data
                    candidates[field_id]["score"] += 10
                    candidates[field_id]["populated_count"] += 1

    # Only return if field has sprint data in at least 10% of issues
    if candidates:
        for field_id, stats in candidates.items():
            if stats["total_count"] > 0:
                population_rate = stats["populated_count"] / stats["total_count"]
                if population_rate < 0.10:  # Less than 10% populated
                    logger.info(
                        f"[FieldDetector] Rejecting sprint field {field_id} - only {population_rate:.1%} populated"
                    )
                    candidates[field_id]["score"] = 0  # Reject

        # Get best candidate with score > 0
        valid_candidates = {k: v for k, v in candidates.items() if v["score"] > 0}
        if valid_candidates:
            best = max(valid_candidates.items(), key=lambda x: x[1]["score"])
            logger.info(
                f"[FieldDetector] [OK] Sprint field detected: {best[0]} "
                f"({best[1]['populated_count']}/{best[1]['total_count']} issues have sprint data)"
            )
            return best[0]

    logger.info(
        "[FieldDetector] No sprint field found with sufficient data. "
        "Scope calculations will use all issues without sprint filtering."
    )
    return None


def _detect_deployment_date_field(
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
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
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
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
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Dict[str, Optional[str]]:
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
        for field_id, field_value in fields_data.items():
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
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
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


def _detect_change_failure_field(
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
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
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
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
                score -= 100  # Disqualify - this is change_failure, not deployment_successful

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
                f"('{best[1]['name']}', type={best[1]['type']}, score={best[1]['score']})"
            )
            return best[0]

    return None


def _detect_effort_category_field(
    issues: List[Dict], field_defs: Dict[str, Dict]
) -> Optional[str]:
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
