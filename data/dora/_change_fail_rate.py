"""Change Failure Rate DORA metric calculation."""

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
    """Calculate change failure rate metric.

    Measures percentage of deployments that cause incidents requiring remediation.
    Elite teams have failure rates under 15%, while low performers exceed 45%.

    Args:
        deployment_issues: List of deployment/operational task issues
        incident_issues: List of incident/bug issues
            (kept for backward compatibility, not used)
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation
        valid_fix_versions: Set of fixVersion names from development projects.
            If provided, only count Operational Tasks with matching fixVersions.

    Returns:
        Dictionary with change failure rate metrics:
        {
            "value": float,  # Failure rate percentage (0-100)
            "unit": "%",
            "performance_tier": "elite" | "high" | "medium" | "low",
            "total_deployments": int,
            "failed_deployments": int,
            "total_releases": int,
            "failed_releases": int,
            "release_names": List[str],
            "failed_release_names": List[str],
            "period_days": int,
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float
        }

        On error:
        {
            "error_state": "missing_mapping" | "no_data" | "calculation_error",
            "error_message": str,
            "trend_direction": "stable",
            "trend_percentage": 0.0
        }
    """
    try:
        # Check for empty input first (before configuration check)
        if not deployment_issues:
            return {
                "error_state": "no_data",
                "error_message": "No deployment issues provided",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Get field mappings from profile
        dora_mappings, project_classification = _get_field_mappings()

        # Get change_failure field from profile
        # (e.g., "customfield_12708" or "customfield_12708=Yes")
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

        # Parse field mapping.
        # Support "field=value" syntax for configurable failure values.
        # Default positive values if no specific value is configured
        change_failure_field = change_failure_mapping
        configured_failure_values = {"yes", "true", "1"}  # Default positive values

        if "=" in change_failure_mapping:
            # Configurable value syntax:
            # "customfield_12708=Yes" or "customfield_12708=Yes|Ja|Oui"
            field_part, value_part = change_failure_mapping.split("=", 1)
            change_failure_field = field_part.strip()
            # Support multiple values separated by pipe: "Yes|Ja|Oui"
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

        # Count deployments and track which have change_failure flag set
        # Also track releases (distinct fixVersions)
        total_deployments = 0
        failed_deployments = 0
        all_releases = set()  # Track all fixVersion names
        failed_releases = set()  # Track fixVersions that had failures

        for issue in deployment_issues:
            # Handle both nested (JIRA API) and flat (database) formats
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                fields = issue["fields"]
                fix_versions = fields.get("fixVersions", [])
            else:
                # Flat format: fields at root level
                fields = issue
                # fixVersions is JSON string in flat format
                # (mapped from fix_versions by sqlite_backend)
                import json  # noqa: PLC0415

                fix_versions_raw = issue.get("fixVersions", "[]")
                try:
                    fix_versions = (
                        json.loads(fix_versions_raw)
                        if isinstance(fix_versions_raw, str)
                        else fix_versions_raw
                    )
                except (json.JSONDecodeError, TypeError):
                    fix_versions = []

            # Check if issue is completed
            if not _is_issue_completed(issue, flow_end_statuses):
                continue

            # Check if issue has fixVersion with releaseDate (deployment date)
            has_valid_release = False
            issue_releases = []

            for fv in fix_versions:
                if fv.get("releaseDate"):
                    release_name = fv.get("name", "")
                    if release_name:
                        # Filter: Only count if fixVersion exists
                        # in development projects
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

            # Check change_failure field from profile mapping
            # First try to get from fields (root level or fields dict)
            change_failure_value = fields.get(change_failure_field)

            # If not found and it's a custom field, check custom_fields dict
            if change_failure_value is None and "customfield" in change_failure_field:
                custom_fields = fields.get("custom_fields") or issue.get(
                    "custom_fields", {}
                )
                if isinstance(custom_fields, dict):
                    change_failure_value = custom_fields.get(change_failure_field)

            is_failure = False

            if change_failure_value is not None:
                if isinstance(change_failure_value, bool):
                    # Boolean fields: true means failure
                    is_failure = change_failure_value
                elif isinstance(change_failure_value, dict):
                    # Handle JIRA custom field objects like
                    # {"value": "Yes", "id": "123"}
                    val = change_failure_value.get("value", "")
                    is_failure = str(val).lower() in configured_failure_values
                elif isinstance(change_failure_value, str):
                    is_failure = (
                        change_failure_value.lower() in configured_failure_values
                    )
                elif isinstance(change_failure_value, (int, float)):
                    # Numeric fields: non-zero means failure,
                    # or check if matches configured value
                    is_failure = str(
                        int(change_failure_value)
                    ) in configured_failure_values or bool(change_failure_value)

            if is_failure:
                failed_deployments += 1
                # Mark these releases as having failures
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

        # Calculate failure rates
        # CFR based on deployments (operational tasks)
        change_failure_rate = (failed_deployments / total_deployments) * 100

        # Also calculate release-level failure rate
        total_releases_count = len(all_releases)
        failed_releases_count = len(failed_releases)
        release_failure_rate = (
            (failed_releases_count / total_releases_count) * 100
            if total_releases_count > 0
            else 0
        )

        # Classify performance tier (lower is better)
        performance_tier = _classify_performance_tier(
            change_failure_rate, CHANGE_FAILURE_RATE_TIERS, higher_is_better=False
        )

        # Calculate trend
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
