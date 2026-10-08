import logging
from datetime import UTC, datetime
from typing import Any

from data.fixversion_matcher import get_deployment_date_for_issue
from data.performance_utils import log_performance
from data.persistence import load_app_settings

from ._common import (
    LEAD_TIME_TIERS,
    _calculate_trend,
    _classify_performance_tier,
    _extract_datetime_from_field_mapping,
)

logger = logging.getLogger(__name__)


@log_performance
def calculate_lead_time_for_changes(
    issues: list[dict[str, Any]],
    time_period_days: int = 30,
    previous_period_value: float | None = None,
    fixversion_release_map: dict[str, datetime] | None = None,
) -> dict[str, Any]:

    try:
        if not issues:
            return {
                "error_state": "no_data",
                "error_message": "No issues provided for analysis",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        lead_times = []
        missing_start_count = 0
        missing_deployment_count = 0
        no_fixversion_match_count = 0

        app_settings = load_app_settings()
        field_mappings = app_settings.get("field_mappings", {})
        dora_mappings = field_mappings.get("dora", {})

        code_commit_field = dora_mappings.get("code_commit_date", "created")

        for issue in issues:
            issue_key = issue.get("key", "UNKNOWN")

            changelog = issue.get("changelog", {}).get("histories", [])

            work_start_value = _extract_datetime_from_field_mapping(
                issue, code_commit_field, changelog
            )
            if not work_start_value:
                missing_start_count += 1
                continue

            if fixversion_release_map:
                deployment_datetime = get_deployment_date_for_issue(
                    issue, fixversion_release_map
                )
                if not deployment_datetime:
                    no_fixversion_match_count += 1
                    logger.debug(
                        f"[Lead Time] {issue_key}: "
                        "No matching fixVersion in release map"
                    )
                    continue
            else:
                deployment_value = _extract_datetime_from_field_mapping(
                    issue, "fixVersions", changelog
                )
                if not deployment_value:
                    missing_deployment_count += 1
                    continue
                try:
                    deployment_datetime = datetime.fromisoformat(
                        deployment_value.replace("Z", "+00:00")
                    )
                except ValueError, TypeError:
                    missing_deployment_count += 1
                    continue

            try:
                start_time = datetime.fromisoformat(
                    work_start_value.replace("Z", "+00:00")
                )

                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=UTC)
                if deployment_datetime.tzinfo is None:
                    deployment_datetime = deployment_datetime.replace(tzinfo=UTC)

                lead_time_delta = deployment_datetime - start_time
                lead_time_days = lead_time_delta.total_seconds() / 86400

                if lead_time_days < 0:
                    logger.warning(
                        f"[DORA] Negative lead time for {issue_key}: "
                        f"start={start_time}, deployment={deployment_datetime}"
                    )
                    continue

                lead_times.append(lead_time_days)
                logger.debug(
                    f"[Lead Time] {issue_key}: {lead_time_days:.1f} days "
                    f"(start={start_time.date()}, deploy={deployment_datetime.date()})"
                )

            except (ValueError, TypeError) as e:
                logger.warning(f"[DORA] Invalid timestamp for {issue_key}: {e}")
                continue

        if not lead_times:
            error_details = []
            if missing_start_count:
                error_details.append(f"missing start: {missing_start_count}")
            if no_fixversion_match_count:
                error_details.append(
                    f"no fixVersion match: {no_fixversion_match_count}"
                )
            if missing_deployment_count:
                error_details.append(f"missing deployment: {missing_deployment_count}")

            return {
                "error_state": "no_data",
                "error_message": f"No valid lead times from {len(issues)} issues "
                f"({', '.join(error_details)})",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
                "median_hours": 0,
                "mean_hours": 0,
                "p95_hours": 0,
                "issues_with_lead_time": 0,
            }

        import statistics  # noqa: PLC0415

        lead_times_hours = [lt * 24 for lt in lead_times]
        median_hours = statistics.median(lead_times_hours)
        mean_hours = statistics.mean(lead_times_hours)
        p95_hours = (
            sorted(lead_times_hours)[int(len(lead_times_hours) * 0.95)]
            if len(lead_times_hours) >= 2
            else mean_hours
        )

        median_lead_time_days = median_hours / 24

        if median_lead_time_days < 1:
            unit = "hours"
            display_value = median_hours
        else:
            unit = "days"
            display_value = median_lead_time_days

        performance_tier = _classify_performance_tier(
            median_lead_time_days, LEAD_TIME_TIERS, higher_is_better=False
        )

        trend = _calculate_trend(median_lead_time_days, previous_period_value)

        logger.info(
            f"[DORA] Lead Time for Changes: {display_value:.1f} {unit} "
            f"({len(lead_times)} issues) - {performance_tier}"
        )

        return {
            "value": display_value,
            "unit": unit,
            "value_hours": median_hours,
            "value_days": median_lead_time_days,
            "performance_tier": performance_tier,
            "sample_count": len(lead_times),
            "period_days": time_period_days,
            "median_hours": median_hours,
            "mean_hours": mean_hours,
            "p95_hours": p95_hours,
            "issues_with_lead_time": len(lead_times),
            **trend,
        }

    except Exception as e:
        logger.error(f"[DORA] Lead time calculation failed: {e}", exc_info=True)
        return {
            "error_state": "calculation_error",
            "error_message": str(e),
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }
