import logging
from typing import Any

from data.performance_utils import log_performance

from ._common import (
    DEPLOYMENT_FREQUENCY_TIERS,
    _calculate_trend,
    _classify_performance_tier,
    _get_field_mappings,
    _is_issue_completed,
)

logger = logging.getLogger(__name__)


@log_performance
def calculate_deployment_frequency(
    issues: list[dict[str, Any]],
    time_period_days: int = 30,
    previous_period_value: float | None = None,
) -> dict[str, Any]:

    try:
        if not issues:
            return {
                "error_state": "no_data",
                "error_message": "No issues provided for analysis",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        dora_mappings, project_classification = _get_field_mappings()
        flow_end_statuses = project_classification.get(
            "flow_end_statuses", ["Done", "Resolved", "Closed"]
        )

        from data.persistence import load_app_settings  # noqa: PLC0415

        app_settings = load_app_settings()
        devops_projects = app_settings.get("devops_projects", [])
        devops_task_types = project_classification.get("devops_task_types", [])

        logger.info(
            f"[DORA DF] Starting calculation: "
            f"devops_projects={devops_projects}, "
            f"devops_task_types={devops_task_types}, "
            f"flow_end_statuses={flow_end_statuses}, "
            f"analyzing {len(issues)} issues"
        )

        deployment_count = 0
        all_releases = set()

        total_checked = 0
        filtered_by_project = 0
        filtered_by_type = 0
        filtered_by_completion = 0
        filtered_by_no_fixversion = 0

        for issue in issues:
            total_checked += 1
            issue_key = issue.get("key", "UNKNOWN")

            if "fields" in issue and isinstance(issue.get("fields"), dict):
                fields = issue["fields"]
                project_key = fields.get("project", {}).get("key", "")
                issue_type = fields.get("issuetype", {}).get("name", "")
                status = fields.get("status", {}).get("name", "")
                fix_versions = fields.get("fixVersions", [])
            else:
                fields = issue
                project_key = issue.get("project", "")
                issue_type = issue.get("issue_type", "")
                status = issue.get("status", "")
                import json  # noqa: PLC0415

                fix_versions_raw = issue.get("fixVersions", "[]")
                try:
                    fix_versions = (
                        json.loads(fix_versions_raw)
                        if isinstance(fix_versions_raw, str)
                        else fix_versions_raw
                    )
                except json.JSONDecodeError, TypeError:
                    fix_versions = []

            if total_checked <= 3:
                logger.info(
                    f"[DORA DF] Sample issue {issue_key}: "
                    f"project={project_key}, type={issue_type}, status={status}, "
                    f"fixVersions={len(fix_versions)} versions"
                )

            if devops_projects and project_key not in devops_projects:
                filtered_by_project += 1
                continue

            if devops_task_types and issue_type not in devops_task_types:
                filtered_by_type += 1
                continue

            if not _is_issue_completed(issue, flow_end_statuses):
                filtered_by_completion += 1
                continue

            has_release_date = False

            for fv in fix_versions:
                if fv.get("releaseDate"):
                    has_release_date = True
                    release_name = fv.get("name", "")
                    if release_name:
                        all_releases.add(release_name)

            if has_release_date:
                deployment_count += 1
                release_names = [
                    version.get("name")
                    for version in fix_versions
                    if version.get("releaseDate")
                ]
                logger.info(
                    f"[DORA DF] Issue {issue_key} counted as deployment: "
                    f"project={project_key}, type={issue_type}, "
                    f"fixVersions={release_names}"
                )
            else:
                filtered_by_no_fixversion += 1

        logger.info(
            f"[DORA DF] Filtering results: "
            f"total={total_checked}, "
            f"filtered_by_project={filtered_by_project}, "
            f"filtered_by_type={filtered_by_type}, "
            f"filtered_by_completion={filtered_by_completion}, "
            f"filtered_by_no_fixversion={filtered_by_no_fixversion}, "
            f"deployment_count={deployment_count}"
        )

        if deployment_count == 0:
            return {
                "error_state": "no_data",
                "error_message": (
                    "No completed deployments with fixVersion.releaseDate found "
                    f"in {len(issues)} issues"
                ),
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        release_count = len(all_releases)
        weeks = time_period_days / 7.0

        deployments_per_week = deployment_count / weeks if weeks > 0 else 0
        releases_per_week = release_count / weeks if weeks > 0 else 0
        deployments_per_day = deployment_count / time_period_days

        if deployments_per_day >= 0.9:
            unit = "deployments/day"
            display_value = deployments_per_day
        elif deployments_per_day >= 0.13:
            unit = "deployments/week"
            display_value = deployments_per_week
        else:
            unit = "deployments/month"
            display_value = deployments_per_day * 30

        performance_tier = _classify_performance_tier(
            deployments_per_day, DEPLOYMENT_FREQUENCY_TIERS, higher_is_better=True
        )

        trend = _calculate_trend(deployments_per_day, previous_period_value)

        logger.info(
            f"[DORA] Deployment Frequency: {display_value:.1f} {unit} "
            f"({deployment_count} deployments, "
            f"{release_count} releases / {time_period_days} days) "
            f"- {performance_tier}"
        )
        logger.debug(f"[DORA] Releases: {sorted(all_releases)}")

        return {
            "value": display_value,
            "deployments_per_week": deployments_per_week,
            "releases_per_week": releases_per_week,
            "unit": unit,
            "performance_tier": performance_tier,
            "deployment_count": deployment_count,
            "release_count": release_count,
            "release_names": sorted(all_releases),
            "period_days": time_period_days,
            **trend,
        }

    except Exception as e:
        logger.error(
            f"[DORA] Deployment frequency calculation failed: {e}", exc_info=True
        )
        return {
            "error_state": "calculation_error",
            "error_message": str(e),
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }
