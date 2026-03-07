"""Lead Time for Changes DORA metric calculation."""

import logging
from datetime import UTC, datetime
from typing import Any

from data.performance_utils import log_performance

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
    """Calculate lead time for changes metric.

    Measures time from code commit (status:In Progress) to production deployment
    (fixVersion.releaseDate from matching Operational Task).

    IMPORTANT: Lead Time uses the SAME deployment date logic as Deployment Frequency:
    - Development issues link to Operational Tasks via shared fixVersions
    - Deployment date = fixVersion.releaseDate from the Operational Task
    - fixversion_release_map is built once and reused across metrics (DRY)

    Args:
        issues: List of development issues to analyze
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation
        fixversion_release_map: Map of fixVersion name -> releaseDate datetime
            Built from Operational Tasks via build_fixversion_release_map()

    Returns:
        Dictionary with lead time metrics:
        {
            "value": float,  # Average lead time in days
            "unit": "days" | "hours",
            "performance_tier": "elite" | "high" | "medium" | "low",
            "sample_count": int,
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
        if not issues:
            return {
                "error_state": "no_data",
                "error_message": "No issues provided for analysis",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Import shared fixversion lookup function
        from data.fixversion_matcher import get_deployment_date_for_issue

        # Extract lead times
        lead_times = []
        missing_start_count = 0
        missing_deployment_count = 0
        no_fixversion_match_count = 0

        # Get field mappings from profile configuration
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        field_mappings = app_settings.get("field_mappings", {})
        dora_mappings = field_mappings.get("dora", {})

        code_commit_field = dora_mappings.get("code_commit_date", "created")

        for issue in issues:
            issue_key = issue.get("key", "UNKNOWN")

            # Extract changelog if present
            changelog = issue.get("changelog", {}).get("histories", [])

            # Extract work start timestamp using field mapping
            # (e.g., status:In Progress.DateTime)
            work_start_value = _extract_datetime_from_field_mapping(
                issue, code_commit_field, changelog
            )
            if not work_start_value:
                missing_start_count += 1
                continue

            # Get deployment date from fixVersion release map
            # (shared with Deployment Frequency)
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
                # Fallback: Try to extract from issue's own fixVersions
                # (legacy behavior)
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
                except (ValueError, TypeError):
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

                # Calculate lead time in days
                lead_time_delta = deployment_datetime - start_time
                lead_time_days = (
                    lead_time_delta.total_seconds() / 86400
                )  # 86400 seconds per day

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
                # Backward compatibility fields for metrics_calculator
                "median_hours": 0,
                "mean_hours": 0,
                "p95_hours": 0,
                "issues_with_lead_time": 0,
            }

        # Calculate statistics in hours for backward compatibility
        import statistics

        lead_times_hours = [lt * 24 for lt in lead_times]
        median_hours = statistics.median(lead_times_hours)
        mean_hours = statistics.mean(lead_times_hours)
        p95_hours = (
            sorted(lead_times_hours)[int(len(lead_times_hours) * 0.95)]
            if len(lead_times_hours) >= 2
            else mean_hours
        )

        # Use MEDIAN per official DORA methodology (outlier resistant)
        median_lead_time_days = median_hours / 24

        # Determine display unit
        if median_lead_time_days < 1:
            unit = "hours"
            display_value = median_hours
        else:
            unit = "days"
            display_value = median_lead_time_days

        # Classify performance tier (lower is better)
        performance_tier = _classify_performance_tier(
            median_lead_time_days, LEAD_TIME_TIERS, higher_is_better=False
        )

        # Calculate trend
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
            # Additional statistics for analysis
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
