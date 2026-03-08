"""Backward-compatible re-export shim for data.field_detector.

The implementation has been split into focused modules:
  - field_detector_core.py     -- public API + shared utilities
  - field_detector_basic.py    -- basic detection (points, sprint, parent, dates)
  - field_detector_dora.py     -- DORA deployment/environment/incident detection
  - field_detector_quality.py  -- DORA quality-gate field detection

All callers of ``data.field_detector`` continue to work unchanged.
"""

from data.field_detector_basic import (  # noqa: F401
    _detect_code_commit_date_field,
    _detect_completed_date_field,
    _detect_parent_field,
    _detect_points_field,
    _detect_sprint_field,
)
from data.field_detector_core import (  # noqa: F401
    DETECTION_THRESHOLDS,
    JAVA_CLASS_PATTERNS,
    _get_common_issue_types,
    _is_java_class_value,
    detect_fields_from_issues,
)
from data.field_detector_dora import (  # noqa: F401
    _detect_deployment_date_field,
    _detect_environment_field,
    _detect_incident_related_fields,
    _detect_priority_severity_field,
)
from data.field_detector_quality import (  # noqa: F401
    _detect_change_failure_field,
    _detect_deployment_successful_field,
    _detect_effort_category_field,
)

__all__ = [
    "DETECTION_THRESHOLDS",
    "JAVA_CLASS_PATTERNS",
    "_detect_change_failure_field",
    "_detect_code_commit_date_field",
    "_detect_completed_date_field",
    "_detect_deployment_date_field",
    "_detect_deployment_successful_field",
    "_detect_effort_category_field",
    "_detect_environment_field",
    "_detect_incident_related_fields",
    "_detect_parent_field",
    "_detect_points_field",
    "_detect_priority_severity_field",
    "_detect_sprint_field",
    "_get_common_issue_types",
    "_is_java_class_value",
    "detect_fields_from_issues",
]
