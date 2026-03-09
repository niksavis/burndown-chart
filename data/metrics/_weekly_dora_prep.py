"""DORA issue classification and filter helpers for weekly snapshots."""

import logging
from datetime import datetime

from data.dora_metrics import is_production_environment

logger = logging.getLogger(__name__)


def count_deployments_for_week(
    issues: list,
    flow_end_statuses: list[str],
    week_label: str,
    week_start: datetime,
    week_end: datetime,
    valid_fix_versions: set | None = None,
) -> dict:
    """Count deployment issues with releaseDate in the specified week.

    Filters issues by completed status and fixVersion.releaseDate within range.
    If valid_fix_versions is provided, only counts matching fixVersion names.

    Returns a dict keyed by week_label with deployment/release counts.
    """
    deployment_count = 0
    releases: set[str] = set()

    for issue in issues:
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            status = issue.get("fields", {}).get("status", {}).get("name", "")
            fix_versions = issue.get("fields", {}).get("fixVersions", [])
        else:
            status = issue.get("status", "")
            fix_versions = issue.get("fixVersions", [])

        if status not in flow_end_statuses:
            continue

        for fv in fix_versions:
            release_date_str = fv.get("releaseDate")
            release_name = fv.get("name")
            if not release_date_str or not release_name:
                continue
            if valid_fix_versions and release_name not in valid_fix_versions:
                continue
            try:
                release_date = datetime.fromisoformat(release_date_str)
                if week_start <= release_date < week_end:
                    deployment_count += 1
                    releases.add(release_name)
                    break
            except (ValueError, TypeError):
                continue

    return {
        week_label: {
            "deployments": deployment_count,
            "releases": len(releases),
            "release_names": sorted(list(releases)),
        }
    }


def filter_issues_by_deployment_week(
    issues: list, week_start: datetime, week_end: datetime
) -> list:
    """Filter issues where fixVersions.releaseDate falls within the week."""
    filtered = []
    for issue in issues:
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            fix_versions = issue.get("fields", {}).get("fixVersions", [])
        else:
            fix_versions = issue.get("fixVersions", [])

        for fv in fix_versions:
            release_date_str = fv.get("releaseDate")
            if not release_date_str:
                continue
            try:
                release_date = datetime.fromisoformat(release_date_str)
                if week_start <= release_date < week_end:
                    filtered.append(issue)
                    break
            except (ValueError, TypeError):
                continue

    return filtered


def filter_bugs_by_resolution_week(
    bugs: list, week_start: datetime, week_end: datetime
) -> list:
    """Filter bugs where resolutiondate falls within the week."""
    filtered = []
    for bug in bugs:
        if "fields" in bug and isinstance(bug.get("fields"), dict):
            resolution_str = bug.get("fields", {}).get("resolutiondate")
        else:
            resolution_str = bug.get("resolutiondate")

        if not resolution_str:
            continue
        try:
            resolution_date = datetime.fromisoformat(
                resolution_str.replace("Z", "+00:00")
            )
            if resolution_date.tzinfo and week_start.tzinfo is None:
                resolution_date = resolution_date.replace(tzinfo=None)
            if week_start <= resolution_date < week_end:
                filtered.append(bug)
        except (ValueError, TypeError):
            continue

    return filtered


def classify_dora_issues(
    all_issues: list,
    all_issues_raw: list,
    app_settings: dict,
) -> tuple[list, list, list]:
    """Classify issues into operational tasks, development issues, and production bugs.

    Returns (operational_tasks, development_issues, production_bugs).
    """

    devops_task_types = app_settings.get("devops_task_types", [])
    bug_types = app_settings.get("bug_types", ["Bug"])
    production_env_values = app_settings.get("production_environment_values", [])
    dora_mappings = app_settings.get("field_mappings", {}).get("dora", {})
    affected_environment_mapping = dora_mappings.get("affected_environment", "")

    operational_tasks = []
    for issue in all_issues_raw:
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            issue_type = issue["fields"].get("issuetype", {}).get("name", "")
        else:
            issue_type = issue.get("issue_type", "")
        if issue_type in devops_task_types:
            operational_tasks.append(issue)

    logger.info(
        f"[DORA] Found {len(operational_tasks)} Operational Tasks "
        f"(types: {devops_task_types}) from {len(all_issues_raw)} total issues"
    )

    development_issues: list = []
    production_bugs: list = []

    for issue in all_issues:
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            issue_type = issue["fields"].get("issuetype", {}).get("name", "")
        else:
            issue_type = issue.get("issue_type", "")

        if issue_type in bug_types:
            if is_production_environment(
                issue,
                affected_environment_mapping,
                fallback_values=production_env_values,
            ):
                production_bugs.append(issue)
            else:
                development_issues.append(issue)
        else:
            development_issues.append(issue)

    filter_info = affected_environment_mapping or str(production_env_values)
    logger.info(
        f"[DORA] Classification (env_filter={filter_info}): "
        f"{len(development_issues)} development issues, "
        f"{len(production_bugs)} production bugs"
    )

    return operational_tasks, development_issues, production_bugs


def collect_development_fix_versions(all_issues: list) -> set:
    """Collect unique fixVersion names from development project issues."""
    development_fix_versions: set[str] = set()

    for issue in all_issues:
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            fix_versions = issue.get("fields", {}).get("fixVersions", [])
        else:
            fix_versions = issue.get("fixVersions", [])

        if fix_versions is None:
            fix_versions = []

        for fv in fix_versions:
            fv_name = fv.get("name")
            if fv_name:
                development_fix_versions.add(fv_name)

    logger.info(
        f"[DORA] Found {len(development_fix_versions)} unique fixVersions "
        "in development projects (used to filter Operational Tasks)"
    )
    if development_fix_versions:
        sample = sorted(list(development_fix_versions))[:5]
        logger.info(f"[DORA] Sample development fixVersions: {sample}")

    return development_fix_versions
