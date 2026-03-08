"""Shared constants and utilities for field detection.

No local imports — this module is the base of the field_detector import chain.
All other field_detector_* modules may import from here without circular issues.
"""

from typing import Any

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
