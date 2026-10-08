import logging
from typing import Any

from data.jira.parent_filter import filter_out_parent_types
from data.jira.query_builder import extract_parent_types_from_config
from data.parent_filter import filter_parent_issues
from data.persistence import load_app_settings
from data.project_filter import filter_development_issues

logger = logging.getLogger(__name__)


def filter_issues_for_metrics(
    issues: list[dict[str, Any]],
    settings: dict[str, Any] | None = None,
    log_prefix: str = "METRICS",
) -> list[dict[str, Any]]:

    if not issues:
        return issues

    if settings is None:
        settings = load_app_settings()

    parent_field = (
        settings.get("field_mappings", {}).get("general", {}).get("parent_field")
    )
    if parent_field:
        issues = filter_parent_issues(issues, parent_field, log_prefix=log_prefix)

    development_projects = settings.get("development_projects", [])
    devops_projects = settings.get("devops_projects", [])
    if development_projects or devops_projects:
        issues = filter_development_issues(
            issues, development_projects, devops_projects
        )

    parent_types = extract_parent_types_from_config(settings)
    if parent_types:
        issues = filter_out_parent_types(issues, parent_types)

    return issues
