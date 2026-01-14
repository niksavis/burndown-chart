"""DORA Metrics Calculation and Caching.

Similar to metrics_calculator.py for Flow metrics, this module handles:
- Calculating DORA metrics for multiple weeks
- Saving results to metrics_snapshots.json
- Loading cached results for display

Uses the same caching architecture as Flow metrics for consistent UX.
"""

import logging
from datetime import datetime, timezone
from typing import Tuple, Optional, List, Dict, Any

from data.dora_metrics import (
    calculate_deployment_frequency,
    calculate_lead_time_for_changes,
    calculate_change_failure_rate,
    calculate_mean_time_to_recovery,
)
from data.metrics_snapshots import save_metric_snapshot, get_metric_snapshot
from data.iso_week_bucketing import get_last_n_weeks

logger = logging.getLogger(__name__)


def calculate_and_save_dora_weekly_metrics(
    week_label: str,
    monday,  # date object from get_last_n_weeks
    sunday,  # date object from get_last_n_weeks
    operational_tasks: List[Dict],
    development_issues: List[Dict],
    production_bugs: List[Dict],
    production_value: str,
) -> Tuple[bool, str]:
    """Calculate DORA metrics for a single week and save to cache.

    Args:
        week_label: ISO week label (e.g., "2025-45")
        monday: Week start date (date object)
        sunday: Week end date (date object)
        operational_tasks: Filtered operational task issues
        development_issues: Filtered development issues
        production_bugs: Filtered production bug issues
        production_value: Production environment identifier

    Returns:
        Tuple of (success, message)
    """
    try:
        # Combine all issues for calculation
        all_issues = operational_tasks + development_issues + production_bugs

        # Calculate Deployment Frequency
        logger.info(
            f"Week {week_label}: Calculating deployment frequency with {len(all_issues)} issues"
        )
        deployment_freq = calculate_deployment_frequency(
            all_issues,
            time_period_days=7,  # Weekly calculation
        )
        logger.info(
            f"Week {week_label}: Deployment frequency result: {deployment_freq.get('deployment_count', 0)} deployments"
        )

        # Calculate Lead Time for Changes
        lead_time = calculate_lead_time_for_changes(
            all_issues,
            time_period_days=7,  # Weekly calculation
        )

        if lead_time.get("value") is None:
            logger.info(
                f"Week {week_label}: No lead time data (checked {len(all_issues)} issues)"
            )

        # Calculate Change Failure Rate
        cfr = calculate_change_failure_rate(
            operational_tasks,
            production_bugs,
            time_period_days=7,  # Weekly calculation
        )

        # Calculate MTTR
        mttr = calculate_mean_time_to_recovery(
            production_bugs,
            time_period_days=7,  # Weekly calculation
        )

        # Save each metric to snapshots (convert to legacy format for compatibility)
        save_metric_snapshot(
            week_label,
            "dora_deployment_frequency",
            {
                "deployment_count": deployment_freq.get("deployment_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Convert lead time days to hours for legacy compatibility
        lead_time_value = lead_time.get("value")
        lead_time_hours = lead_time_value * 24 if lead_time_value is not None else None

        save_metric_snapshot(
            week_label,
            "dora_lead_time",
            {
                "median_hours": lead_time_hours,
                "mean_hours": lead_time_hours,  # Using same value for now
                "p95_hours": lead_time_hours,  # Using same value for now
                "issues_with_lead_time": lead_time.get("sample_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        save_metric_snapshot(
            week_label,
            "dora_change_failure_rate",
            {
                "change_failure_rate_percent": cfr.get("value", 0),
                "total_deployments": cfr.get("deployment_count", 0),
                "failed_deployments": cfr.get("incident_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        save_metric_snapshot(
            week_label,
            "dora_mttr",
            {
                "median_hours": mttr.get("value"),
                "mean_hours": mttr.get("value"),  # Using same value for now
                "p95_hours": mttr.get("value"),  # Using same value for now
                "bugs_with_mttr": mttr.get("incident_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        return True, f"Week {week_label} calculated successfully"

    except Exception as e:
        error_msg = f"Error calculating DORA metrics for {week_label}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def load_dora_metrics_from_cache(n_weeks: int = 12) -> Optional[Dict[str, Any]]:
    """Load DORA metrics from cache for the last N weeks.

    Args:
        n_weeks: Number of weeks to load

    Returns:
        Dictionary with aggregated metrics and weekly trends, or None if no cache
    """
    try:
        weeks = get_last_n_weeks(n_weeks)

        weekly_labels = []
        weekly_deployment_freq = []
        weekly_release_freq = []  # NEW: Track release counts per week
        weekly_lead_time = []
        weekly_cfr = []
        weekly_cfr_releases = []  # NEW: Track CFR for releases
        weekly_mttr = []

        # Aggregate metrics across all weeks
        total_deployments = 0
        total_releases = 0  # NEW: Track unique releases
        all_lead_times = []
        all_lead_times_p95 = []  # NEW: Track P95 values
        all_lead_times_mean = []  # NEW: Track mean values
        total_cfr_numerator = 0
        total_cfr_denominator = 0
        # NEW: CFR release tracking
        total_cfr_failed_releases = 0
        total_cfr_total_releases = 0
        all_mttr_values = []
        all_mttr_p95 = []  # NEW: Track P95 MTTR values
        all_mttr_mean = []  # NEW: Track mean MTTR values

        # Track issue counts for "Based on X issues" display
        total_lead_time_issues = 0
        total_deployment_issues = 0
        total_cfr_issues = 0
        total_mttr_issues = 0

        # Track if any data exists in cache
        has_any_data = False

        for week_label, _, _ in weeks:
            weekly_labels.append(week_label)

            # Load each metric from cache
            df_data = get_metric_snapshot(week_label, "dora_deployment_frequency")
            lt_data = get_metric_snapshot(week_label, "dora_lead_time")
            cfr_data = get_metric_snapshot(week_label, "dora_change_failure_rate")
            mttr_data = get_metric_snapshot(week_label, "dora_mttr")

            # Check if any data exists
            if df_data or lt_data or cfr_data or mttr_data:
                has_any_data = True

            # Deployment Frequency - with release count
            df_count = df_data.get("deployment_count", 0) if df_data else 0
            release_count = df_data.get("release_count", 0) if df_data else 0  # NEW
            weekly_deployment_freq.append(df_count)
            weekly_release_freq.append(release_count)  # NEW: Track releases per week
            total_deployments += df_count
            total_releases += release_count  # NEW: Accumulate unique releases
            if df_count > 0:
                total_deployment_issues += df_count  # Count actual deployments

            # Lead Time (convert to days for display)
            lt_hours = lt_data.get("median_hours") if lt_data else None
            lt_p95_hours = lt_data.get("p95_hours") if lt_data else None  # NEW
            lt_mean_hours = lt_data.get("mean_hours") if lt_data else None  # NEW
            lt_count = (
                lt_data.get("issues_with_lead_time", 0) if lt_data else 0
            )  # FIX: Use correct field name
            logger.info(
                f"[LOAD_CACHE] Week {week_label}: lt_data={lt_data}, lt_hours={lt_hours}"
            )
            lt_days = lt_hours / 24 if lt_hours else 0
            weekly_lead_time.append(lt_days)

            # Accumulate issue count regardless of whether we have hours
            if lt_count > 0:
                total_lead_time_issues += lt_count

            if (
                lt_hours is not None and lt_hours > 0
            ):  # Fixed: check for None, not falsiness
                all_lead_times.append(lt_hours)
                if lt_p95_hours is not None:
                    all_lead_times_p95.append(lt_p95_hours)
                if lt_mean_hours is not None:
                    all_lead_times_mean.append(lt_mean_hours)
                logger.info(
                    f"[LOAD_CACHE] Week {week_label}: Added {lt_hours}h to all_lead_times (total: {len(all_lead_times)})"
                )

            # Change Failure Rate
            cfr_percent = (
                cfr_data.get("change_failure_rate_percent", 0) if cfr_data else 0
            )
            weekly_cfr.append(cfr_percent)
            # NEW: Track release-based CFR
            cfr_release_percent = (
                cfr_data.get("release_failure_rate_percent", 0) if cfr_data else 0
            )
            weekly_cfr_releases.append(cfr_release_percent)

            if cfr_data:
                total_cfr_numerator += cfr_data.get("failed_deployments", 0)
                total_cfr_denominator += cfr_data.get("total_deployments", 0)
                total_cfr_issues += cfr_data.get(
                    "total_deployments", 0
                )  # Count total deployments analyzed
                # NEW: Accumulate release-based CFR
                total_cfr_failed_releases += cfr_data.get("failed_releases", 0)
                total_cfr_total_releases += cfr_data.get("total_releases", 0)

            # MTTR
            mttr_hours = mttr_data.get("median_hours") if mttr_data else None
            mttr_p95_hours = mttr_data.get("p95_hours") if mttr_data else None  # NEW
            mttr_mean_hours = mttr_data.get("mean_hours") if mttr_data else None  # NEW
            mttr_count = (
                mttr_data.get("bugs_with_mttr", 0) if mttr_data else 0
            )  # FIX: Use correct field name
            weekly_mttr.append(mttr_hours if mttr_hours else 0)

            # Accumulate issue count regardless of whether we have hours
            if mttr_count > 0:
                total_mttr_issues += mttr_count

            if mttr_hours:
                all_mttr_values.append(mttr_hours)
                if mttr_p95_hours is not None:
                    all_mttr_p95.append(mttr_p95_hours)
                if mttr_mean_hours is not None:
                    all_mttr_mean.append(mttr_mean_hours)

        # Calculate overall metrics
        # Deployment Frequency: average deployments and releases per week
        deployment_freq_per_week = (
            total_deployments / len(weeks) if len(weeks) > 0 else 0
        )
        release_freq_per_week = (
            total_releases / len(weeks) if len(weeks) > 0 else 0
        )  # NEW

        logger.info(f"[LOAD_CACHE] all_lead_times list: {all_lead_times}")
        # Use MEDIAN of weekly medians (more robust than mean of medians)
        import statistics

        overall_lead_time = (
            statistics.median(all_lead_times) if all_lead_times else None
        )
        # NEW: Calculate P95 and mean for lead time
        overall_lead_time_p95 = (
            statistics.median(all_lead_times_p95) if all_lead_times_p95 else None
        )
        overall_lead_time_mean = (
            statistics.median(all_lead_times_mean) if all_lead_times_mean else None
        )
        logger.info(f"[LOAD_CACHE] overall_lead_time (hours): {overall_lead_time}")
        overall_cfr = (
            (total_cfr_numerator / total_cfr_denominator * 100)
            if total_cfr_denominator > 0
            else 0
        )
        # NEW: Calculate release-based CFR
        overall_cfr_releases = (
            (total_cfr_failed_releases / total_cfr_total_releases * 100)
            if total_cfr_total_releases > 0
            else 0
        )
        # Use MEDIAN of weekly medians (more robust than mean of medians)
        overall_mttr = statistics.median(all_mttr_values) if all_mttr_values else None
        # NEW: Calculate P95 and mean for MTTR
        overall_mttr_p95 = statistics.median(all_mttr_p95) if all_mttr_p95 else None
        overall_mttr_mean = statistics.median(all_mttr_mean) if all_mttr_mean else None

        # If no cache data exists, return None
        if not has_any_data:
            logger.info("No DORA metrics found in cache")
            return None

        return {
            "deployment_frequency": {
                "value": round(deployment_freq_per_week, 2),
                "release_value": round(release_freq_per_week, 2),  # NEW
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_deployment_freq,
                "weekly_release_values": weekly_release_freq,  # NEW: Release counts per week
                "total_issue_count": total_deployment_issues,
            },
            "lead_time_for_changes": {
                "value": overall_lead_time / 24
                if overall_lead_time is not None
                else None,
                "value_hours": overall_lead_time
                if overall_lead_time is not None
                else None,  # Hours equivalent for secondary display
                "value_days": overall_lead_time / 24
                if overall_lead_time is not None
                else None,  # Days equivalent for secondary display
                "p95_value": overall_lead_time_p95 / 24
                if overall_lead_time_p95 is not None
                else None,  # NEW: P95 in days
                "mean_value": overall_lead_time_mean / 24
                if overall_lead_time_mean is not None
                else None,  # NEW: Mean in days
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_lead_time,
                "total_issue_count": total_lead_time_issues,
            },
            "change_failure_rate": {
                "value": overall_cfr,
                "release_value": overall_cfr_releases,  # NEW: Release-based CFR
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_cfr,
                "weekly_release_values": weekly_cfr_releases,  # NEW: Release CFR per week
                "total_issue_count": total_cfr_issues,
            },
            "mean_time_to_recovery": {
                "value": overall_mttr if overall_mttr else None,
                "value_hours": overall_mttr
                if overall_mttr is not None
                else None,  # Hours equivalent for secondary display
                "value_days": overall_mttr / 24
                if overall_mttr is not None
                else None,  # Days equivalent for secondary display
                "p95_value": overall_mttr_p95
                if overall_mttr_p95 is not None
                else None,  # NEW: P95 MTTR
                "mean_value": overall_mttr_mean
                if overall_mttr_mean is not None
                else None,  # NEW: Mean MTTR
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_mttr,
                "total_issue_count": total_mttr_issues,
            },
        }

    except Exception as e:
        logger.error(f"Error loading DORA metrics from cache: {e}", exc_info=True)
        return None


def calculate_and_save_dora_metrics_for_all_issues(
    week_label: str,
    monday,  # date object from get_last_n_weeks
    sunday,  # date object from get_last_n_weeks
    all_issues: List[Dict],
) -> Tuple[bool, str]:
    """Calculate DORA metrics from all issues.

    This function takes ALL issues and calculates DORA metrics using
    field mappings from the user profile configuration.

    Args:
        week_label: ISO week label (e.g., "2025-45")
        monday: Week start date (date object)
        sunday: Week end date (date object)
        all_issues: ALL JIRA issues (not pre-filtered)

    Returns:
        Tuple of (success, message)
    """
    try:
        # Convert date to datetime for time_period_days calculation
        start_date = datetime.combine(monday, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        end_date = datetime.combine(sunday, datetime.max.time()).replace(
            tzinfo=timezone.utc
        )
        time_period_days = (end_date - start_date).days

        logger.info(
            f"Week {week_label}: Calculating DORA metrics "
            f"({len(all_issues)} issues, {time_period_days} days)"
        )

        # Calculate all four DORA metrics
        deployment_freq = calculate_deployment_frequency(
            all_issues,
            time_period_days=time_period_days,
        )

        lead_time = calculate_lead_time_for_changes(
            all_issues,
            time_period_days=time_period_days,
        )

        # For CFR, we need to split issues into deployments and incidents
        # The extractor will handle identifying which is which
        cfr = calculate_change_failure_rate(
            all_issues,  # Deployments
            all_issues,  # Incidents
            time_period_days=time_period_days,
        )

        mttr = calculate_mean_time_to_recovery(
            all_issues,
            time_period_days=time_period_days,
        )

        # Save metrics to snapshots (convert to legacy format for compatibility)
        # CRITICAL: Only save if metric calculation succeeded (no error_state)
        if "error_state" not in deployment_freq:
            save_metric_snapshot(
                week_label,
                "dora_deployment_frequency",
                {
                    "deployment_count": deployment_freq.get("deployment_count", 0),
                    "release_count": deployment_freq.get("release_count", 0),
                    "week_label": week_label,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            logger.warning(
                f"Week {week_label}: Deployment frequency calculation failed - {deployment_freq.get('error_message', 'Unknown error')}"
            )

        # Convert lead time days to hours for legacy compatibility
        if "error_state" not in lead_time:
            lead_time_value = lead_time.get("value")
            lead_time_hours = (
                lead_time_value * 24 if lead_time_value is not None else None
            )
            lead_time_p95_value = lead_time.get("p95_value")
            lead_time_p95_hours = (
                lead_time_p95_value * 24 if lead_time_p95_value is not None else None
            )
            lead_time_mean_value = lead_time.get("mean_value")
            lead_time_mean_hours = (
                lead_time_mean_value * 24 if lead_time_mean_value is not None else None
            )

            save_metric_snapshot(
                week_label,
                "dora_lead_time",
                {
                    "median_hours": lead_time_hours,
                    "p95_hours": lead_time_p95_hours,
                    "mean_hours": lead_time_mean_hours,
                    "issues_with_lead_time": lead_time.get("sample_count", 0),
                    "week_label": week_label,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            logger.warning(
                f"Week {week_label}: Lead time calculation failed - {lead_time.get('error_message', 'Unknown error')}"
            )

        if "error_state" not in cfr:
            save_metric_snapshot(
                week_label,
                "dora_change_failure_rate",
                {
                    "change_failure_rate_percent": cfr.get("value", 0),
                    "release_failure_rate_percent": cfr.get("release_value", 0),
                    "total_deployments": cfr.get("deployment_count", 0),
                    "failed_deployments": cfr.get("incident_count", 0),
                    "total_releases": cfr.get("release_count", 0),
                    "failed_releases": cfr.get("failed_release_count", 0),
                    "week_label": week_label,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            logger.warning(
                f"Week {week_label}: Change failure rate calculation failed - {cfr.get('error_message', 'Unknown error')}"
            )

        if "error_state" not in mttr:
            mttr_value = mttr.get("value")
            mttr_p95_value = mttr.get("p95_value")
            mttr_mean_value = mttr.get("mean_value")

            save_metric_snapshot(
                week_label,
                "dora_mttr",
                {
                    "median_hours": mttr_value,
                    "p95_hours": mttr_p95_value,
                    "mean_hours": mttr_mean_value,
                    "bugs_with_mttr": mttr.get("incident_count", 0),
                    "week_label": week_label,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            logger.warning(
                f"Week {week_label}: MTTR calculation failed - {mttr.get('error_message', 'Unknown error')}"
            )

        return True, f"Week {week_label} calculated successfully (variable extraction)"

    except Exception as e:
        error_msg = f"Error calculating DORA metrics for {week_label}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg
