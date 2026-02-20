"""Issue filtering helpers for metrics calculations.

Centralizes filtering to:
- development project issues only
- exclude parent issues by parent field
- exclude configured parent issue types (Epic, Initiative, etc.)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def filter_issues_for_metrics(
    issues: list[dict[str, Any]],
    settings: dict[str, Any] | None = None,
    log_prefix: str = "METRICS",
) -> list[dict[str, Any]]:
    """Filter issues for metrics calculations.

    Args:
        issues: List of Jira issues (database or API format)
        settings: App settings dict; loads from persistence if not provided
        log_prefix: Prefix used by downstream filter logs

    Returns:
        Filtered issues for metrics calculations
    """
    if not issues:
        return issues

    if settings is None:
        from data.persistence import load_app_settings

        settings = load_app_settings()

    # Exclude parent issues based on parent field mapping
    parent_field = (
        settings.get("field_mappings", {}).get("general", {}).get("parent_field")
    )
    if parent_field:
        from data.parent_filter import filter_parent_issues

        issues = filter_parent_issues(issues, parent_field, log_prefix=log_prefix)

    # Filter to development projects only
    development_projects = settings.get("development_projects", [])
    devops_projects = settings.get("devops_projects", [])
    if development_projects or devops_projects:
        from data.project_filter import filter_development_issues

        issues = filter_development_issues(
            issues, development_projects, devops_projects
        )

    # Exclude configured parent issue types from calculations
    from data.jira.query_builder import extract_parent_types_from_config

    parent_types = extract_parent_types_from_config(settings)
    if parent_types:
        from data.jira.parent_filter import filter_out_parent_types

        issues = filter_out_parent_types(issues, parent_types)

    return issues
