import logging
from typing import Any

from data.performance_utils import log_performance

from ._common import (
    CHANGE_FAILURE_RATE_TIERS,
    _calculate_trend,
    _classify_performance_tier,
    _get_field_mappings,
    _is_issue_completed,
)

logger = logging.getLogger(__name__)


@log_performance
def calculate_change_failure_rate(
    deployment_issues: list[dict[str, Any]],
    incident_issues: list[dict[str, Any]],
    time_period_days: int = 30,
    previous_period_value: float | None = None,
    valid_fix_versions: set | None = None,
) -> dict[str, Any]:

    try:
        if not deployment_issues:
            return {
                "error_state": "no_data",
                "error_message": "No deployment issues provided",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        dora_mappings, project_classification = _get_field_mappings()

        change_failure_mapping = dora_mappings.get("change_failure")
        if not change_failure_mapping:
            return {
                "error_state": "missing_mapping",
                "error_message": (
                    "change_failure field not configured in profile.json "
                    "field_mappings.dora"
                ),
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        change_failure_field = change_failure_mapping
        configured_failure_values = {"yes", "true", "1"}

        if "=" in change_failure_mapping:
            field_part, value_part = change_failure_mapping.split("=", 1)
            change_failure_field = field_part.strip()
            configured_failure_values = {
                v.strip().lower() for v in value_part.split("|") if v.strip()
            }
            logger.info(
                "[DORA CFR] Using configured failure values: "
                f"{configured_failure_values}"
            )

        flow_end_statuses = project_classification.get(
            "flow_end_statuses", ["Done", "Resolved", "Closed"]
        )

        total_deployments = 0
        failed_deployments = 0
        all_releases = set()
        failed_releases = set()

        for issue in deployment_issues:
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                fields = issue["fields"]
                fix_versions = fields.get("fixVersions", [])
            else:
                fields = issue
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

            if not _is_issue_completed(issue, flow_end_statuses):
                continue

            has_valid_release = False
            issue_releases = []

            for fv in fix_versions:
                if fv.get("releaseDate"):
                    release_name = fv.get("name", "")
                    if release_name:
                        if (
                            valid_fix_versions
                            and release_name not in valid_fix_versions
                        ):
                            continue
                        has_valid_release = True
                        issue_releases.append(release_name)
                        all_releases.add(release_name)

            if not has_valid_release:
                continue

            total_deployments += 1

            change_failure_value = fields.get(change_failure_field)

            if change_failure_value is None and "customfield" in change_failure_field:
                custom_fields = fields.get("custom_fields") or issue.get(
                    "custom_fields", {}
                )
                if isinstance(custom_fields, dict):
                    change_failure_value = custom_fields.get(change_failure_field)

            is_failure = False

            if change_failure_value is not None:
                if isinstance(change_failure_value, bool):
                    is_failure = change_failure_value
                elif isinstance(change_failure_value, dict):
                    val = change_failure_value.get("value", "")
                    is_failure = str(val).lower() in configured_failure_values
                elif isinstance(change_failure_value, str):
                    is_failure = (
                        change_failure_value.lower() in configured_failure_values
                    )
                elif isinstance(change_failure_value, (int, float)):
                    is_failure = str(
                        int(change_failure_value)
                    ) in configured_failure_values or bool(change_failure_value)

            if is_failure:
                failed_deployments += 1
                for release_name in issue_releases:
                    failed_releases.add(release_name)

                logger.debug(
                    f"[DORA] Issue {issue.get('key')} "
                    "marked as causing production issue "
                    f"(change_failure={change_failure_value})"
                )

        if total_deployments == 0:
            return {
                "error_state": "no_data",
                "error_message": (
                    "No completed deployments with fixVersion.releaseDate found"
                ),
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        change_failure_rate = (failed_deployments / total_deployments) * 100

        total_releases_count = len(all_releases)
        failed_releases_count = len(failed_releases)
        release_failure_rate = (
            (failed_releases_count / total_releases_count) * 100
            if total_releases_count > 0
            else 0
        )

        performance_tier = _classify_performance_tier(
            change_failure_rate, CHANGE_FAILURE_RATE_TIERS, higher_is_better=False
        )

        trend = _calculate_trend(change_failure_rate, previous_period_value)

        logger.info(
            f"[DORA] Change Failure Rate: {change_failure_rate:.1f}% "
            f"({failed_deployments}/{total_deployments} deployments, "
            f"{failed_releases_count}/{total_releases_count} releases) "
            f"- {performance_tier}"
        )

        return {
            "value": change_failure_rate,
            "change_failure_rate_percent": change_failure_rate,
            "unit": "%",
            "performance_tier": performance_tier,
            "total_deployments": total_deployments,
            "failed_deployments": failed_deployments,
            "total_releases": total_releases_count,
            "failed_releases": failed_releases_count,
            "release_failure_rate_percent": release_failure_rate,
            "release_names": sorted(list(all_releases)),
            "failed_release_names": sorted(list(failed_releases)),
            "period_days": time_period_days,
            **trend,
        }

    except Exception as e:
        logger.error(
            f"[DORA] Change failure rate calculation failed: {e}", exc_info=True
        )
        return {
            "error_state": "calculation_error",
            "error_message": str(e),
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }
