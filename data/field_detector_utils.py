from typing import Any

DETECTION_THRESHOLDS = {
    "deployment_date": 40,
    "deployment_successful": 40,
    "sprint": 40,
    "environment": 30,
    "change_failure": 30,
    "effort_category": 30,
}

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

    if not field_value:
        return False
    value_str = str(field_value)
    return any(pattern in value_str for pattern in JAVA_CLASS_PATTERNS)
