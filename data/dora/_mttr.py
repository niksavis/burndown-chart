import logging
from datetime import UTC, datetime
from typing import Any

from data.fixversion_matcher import get_deployment_date_for_issue
from data.performance_utils import log_performance
from data.persistence import load_app_settings

from ._common import (
    MTTR_TIERS,
    _calculate_trend,
    _classify_performance_tier,
    _extract_datetime_from_field_mapping,
)

logger = logging.getLogger(__name__)


@log_performance
def calculate_mean_time_to_recovery(
    incident_issues: list[dict[str, Any]],
    time_period_days: int = 30,
    previous_period_value: float | None = None,
    fixversion_release_map: dict[str, datetime] | None = None,
) -> dict[str, Any]:

    try:
        if not incident_issues:
            return {
                "error_state": "no_data",
                "error_message": "No incident issues provided for analysis",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        recovery_times = []
        missing_start_count = 0
        missing_end_count = 0
        no_fixversion_match_count = 0

        app_settings = load_app_settings()
        field_mappings = app_settings.get("field_mappings", {})
        dora_mappings = field_mappings.get("dora", {})

        incident_detected_field = dora_mappings.get("incident_detected_at", "created")
        incident_resolved_field = dora_mappings.get(
            "incident_resolved_at", "resolutiondate"
        )

        use_deployment_date = incident_resolved_field.lower() == "fixversions"

        for issue in incident_issues:
            issue_key = issue.get("key", "UNKNOWN")

            changelog = issue.get("changelog", {}).get("histories", [])

            incident_start_value = _extract_datetime_from_field_mapping(
                issue, incident_detected_field, changelog
            )
            if not incident_start_value:
                missing_start_count += 1
                continue

            if use_deployment_date and fixversion_release_map:
                end_datetime = get_deployment_date_for_issue(
                    issue, fixversion_release_map
                )
                if not end_datetime:
                    no_fixversion_match_count += 1
                    logger.debug(
                        f"[MTTR] {issue_key}: No matching fixVersion in release map"
                    )
                    continue
            else:
                incident_resolved_value = _extract_datetime_from_field_mapping(
                    issue, incident_resolved_field, changelog
                )
                if not incident_resolved_value:
                    missing_end_count += 1
                    continue
                try:
                    end_datetime = datetime.fromisoformat(
                        incident_resolved_value.replace("Z", "+00:00")
                    )
                except ValueError, TypeError:
                    missing_end_count += 1
                    continue

            try:
                start_time = datetime.fromisoformat(
                    incident_start_value.replace("Z", "+00:00")
                )

                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=UTC)
                if end_datetime.tzinfo is None:
                    end_datetime = end_datetime.replace(tzinfo=UTC)

                recovery_delta = end_datetime - start_time
                recovery_hours = recovery_delta.total_seconds() / 3600

                if recovery_hours < 0:
                    logger.warning(
                        f"[DORA] Negative recovery time for {issue_key}: "
                        f"start={start_time}, end={end_datetime}"
                    )
                    continue

                recovery_times.append(recovery_hours)
                logger.debug(
                    f"[MTTR] {issue_key}: {recovery_hours:.1f} hours "
                    f"(start={start_time.date()}, end={end_datetime.date()})"
                )

            except (ValueError, TypeError) as e:
                logger.warning(f"[DORA] Invalid timestamp for {issue_key}: {e}")
                continue

        if not recovery_times:
            error_details = []
            if missing_start_count:
                error_details.append(f"missing start: {missing_start_count}")
            if no_fixversion_match_count:
                error_details.append(
                    f"no fixVersion match: {no_fixversion_match_count}"
                )
            if missing_end_count:
                error_details.append(f"missing end: {missing_end_count}")

            return {
                "error_state": "no_data",
                "error_message": (
                    f"No valid recovery times from {len(incident_issues)} incidents "
                    f"({', '.join(error_details)})"
                ),
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        import statistics  # noqa: PLC0415

        median_mttr_hours = statistics.median(recovery_times)
        median_mttr_days = median_mttr_hours / 24
        mean_mttr_hours = sum(recovery_times) / len(recovery_times)

        if median_mttr_hours >= 24:
            unit = "days"
            display_value = median_mttr_days
        else:
            unit = "hours"
            display_value = median_mttr_hours

        performance_tier = _classify_performance_tier(
            median_mttr_hours, MTTR_TIERS, higher_is_better=False
        )

        trend = _calculate_trend(median_mttr_hours, previous_period_value)

        logger.info(
            f"[DORA] Mean Time to Recovery (median): {display_value:.1f} {unit} "
            f"({len(recovery_times)} incidents) - {performance_tier}"
        )

        return {
            "value": display_value,
            "unit": unit,
            "value_hours": median_mttr_hours,
            "value_days": median_mttr_days,
            "performance_tier": performance_tier,
            "incident_count": len(recovery_times),
            "period_days": time_period_days,
            "mean_hours": mean_mttr_hours,
            **trend,
        }

    except Exception as e:
        logger.error(f"[DORA] MTTR calculation failed: {e}", exc_info=True)
        return {
            "error_state": "calculation_error",
            "error_message": str(e),
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }
