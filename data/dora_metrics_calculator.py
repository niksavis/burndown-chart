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

from data.persistence import load_app_settings
from data.dora_calculator import (
    calculate_deployment_frequency_v2,
    calculate_lead_time_for_changes_v2,
    calculate_change_failure_rate_v2,
    calculate_mttr_v2,
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
    field_mappings: Dict[str, str],
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
        field_mappings: JIRA field mappings from settings
        production_value: Production environment identifier

    Returns:
        Tuple of (success, message)
    """
    try:
        # Convert date to datetime with timezone
        start_date = datetime.combine(monday, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        end_date = datetime.combine(sunday, datetime.max.time()).replace(
            tzinfo=timezone.utc
        )

        # Calculate Deployment Frequency
        logger.info(
            f"Week {week_label}: Calculating deployment frequency with {len(operational_tasks)} "
            f"operational tasks from {start_date.date()} to {end_date.date()}"
        )
        deployment_freq = calculate_deployment_frequency_v2(
            operational_tasks,
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(
            f"Week {week_label}: Deployment frequency result: {deployment_freq.get('deployment_count', 0)} deployments"
        )

        # Calculate Lead Time for Changes
        lead_time = calculate_lead_time_for_changes_v2(
            development_issues,
            operational_tasks,
            start_date=start_date,
            end_date=end_date,
        )

        if lead_time.get("median_hours") is None:
            logger.info(
                f"Week {week_label}: No lead time data (checked {len(development_issues)} dev issues, "
                f"{len(operational_tasks)} operational tasks)"
            )

        # Calculate Change Failure Rate
        change_failure_field = field_mappings.get("change_failure")
        if not change_failure_field:
            logger.warning("change_failure field not configured, using placeholder")
            change_failure_field = "customfield_XXXXX"

        cfr = calculate_change_failure_rate_v2(
            operational_tasks,
            change_failure_field_id=change_failure_field,
            start_date=start_date,
            end_date=end_date,
        )

        # Calculate MTTR
        affected_env_field = field_mappings.get("affected_environment")
        if not affected_env_field:
            logger.warning(
                "affected_environment field not configured, using placeholder"
            )
            affected_env_field = "customfield_XXXXX"

        mttr = calculate_mttr_v2(
            production_bugs,
            operational_tasks,
            affected_environment_field_id=affected_env_field,
            production_value=production_value,
            start_date=start_date,
            end_date=end_date,
        )

        # Save each metric to snapshots
        save_metric_snapshot(
            week_label,
            "dora_deployment_frequency",
            {
                "deployment_count": deployment_freq.get("deployment_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        save_metric_snapshot(
            week_label,
            "dora_lead_time",
            {
                "median_hours": lead_time.get("median_hours"),
                "mean_hours": lead_time.get("mean_hours"),
                "p95_hours": lead_time.get("p95_hours"),
                "issues_with_lead_time": lead_time.get("issues_with_lead_time", 0),
                "week_label": week_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        save_metric_snapshot(
            week_label,
            "dora_change_failure_rate",
            {
                "change_failure_rate_percent": cfr.get(
                    "change_failure_rate_percent", 0
                ),
                "total_deployments": cfr.get("total_deployments", 0),
                "failed_deployments": cfr.get("failed_deployments", 0),
                "week_label": week_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        save_metric_snapshot(
            week_label,
            "dora_mttr",
            {
                "median_hours": mttr.get("median_hours"),
                "mean_hours": mttr.get("mean_hours"),
                "p95_hours": mttr.get("p95_hours"),
                "bugs_with_mttr": mttr.get("bugs_with_mttr", 0),
                "week_label": week_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        return True, f"Week {week_label} calculated successfully"

    except Exception as e:
        error_msg = f"Error calculating DORA metrics for {week_label}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def calculate_dora_metrics_for_last_n_weeks(
    n_weeks: int = 12, progress_callback=None
) -> Tuple[bool, str]:
    """Calculate DORA metrics for the last N weeks and save to cache.

    Similar to calculate_metrics_for_last_n_weeks but for DORA metrics.
    Loads JIRA data once and processes all weeks efficiently.

    Args:
        n_weeks: Number of weeks to calculate (default: 12)
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (success: bool, summary_message: str)
    """
    try:
        logger.info(f"Starting DORA metrics calculation for last {n_weeks} weeks")

        # Load app settings
        app_settings = load_app_settings()
        if not app_settings:
            return False, "Failed to load app settings"

        # Load JIRA issues from cache file
        import json
        import os

        cache_file = "jira_cache.json"
        if not os.path.exists(cache_file):
            return False, "No JIRA data available. Please update data first."

        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        all_issues = cache_data.get("issues", [])
        if not all_issues:
            return False, "No JIRA issues found in cache."

        logger.info(f"Loaded {len(all_issues)} JIRA issues from cache")

        # Get configuration
        devops_projects = app_settings.get("devops_projects", [])
        dev_projects = app_settings.get("development_projects", [])
        field_mappings = app_settings.get("field_mappings", {})

        # Get production environment values (backward compatible)
        production_environment_values = app_settings.get(
            "production_environment_values"
        )
        if production_environment_values is None:
            # Fallback to legacy singular value
            legacy_value = app_settings.get("production_environment_value", "PROD")
            production_environment_values = [legacy_value]
        production_value = (
            production_environment_values[0]
            if production_environment_values
            else "PROD"
        )

        # Get issue type configuration (backward compatible)
        devops_task_types = app_settings.get("devops_task_types", ["Operational Task"])
        bug_types = app_settings.get("bug_types", ["Bug"])

        if not devops_projects:
            return False, "No DevOps projects configured in settings"

        # Filter issues by project type (do this once)
        development_issues = [
            issue
            for issue in all_issues
            if issue.get("fields", {}).get("project", {}).get("key") in dev_projects
        ]

        # Filter to specific issue types (do this once)
        # Step 1: Extract all fixVersions from development project issues
        from data.project_filter import (
            extract_all_fixversions,
            filter_operational_tasks,
        )

        development_fixversions = extract_all_fixversions(development_issues)
        logger.info(
            f"Extracted {len(development_fixversions)} unique fixVersions from development issues"
        )

        # Step 2: Filter operational tasks to ONLY those matching development fixVersions
        # This ensures we only count deployments related to the development project
        operational_tasks = filter_operational_tasks(
            all_issues, devops_projects, development_fixversions, devops_task_types
        )

        # Step 3: Filter production incidents using configurable incident types
        production_bugs = [
            issue
            for issue in development_issues
            if issue.get("fields", {}).get("issuetype", {}).get("name") in bug_types
        ]

        logger.info(
            f"Filtered to {len(operational_tasks)} DevOps tasks ({', '.join(devops_task_types)}) "
            f"(matching development fixVersions) and {len(production_bugs)} production incidents ({', '.join(bug_types)})"
        )

        # Get week ranges
        weeks = get_last_n_weeks(n_weeks)

        successful_weeks = []
        failed_weeks = []

        for week_label, monday, sunday in weeks:
            if progress_callback:
                progress_callback(
                    f"📊 Calculating DORA metrics for week {week_label} ({monday} to {sunday})..."
                )

            success, message = calculate_and_save_dora_weekly_metrics(
                week_label=week_label,
                monday=monday,
                sunday=sunday,
                operational_tasks=operational_tasks,
                development_issues=development_issues,
                production_bugs=production_bugs,
                field_mappings=field_mappings,
                production_value=production_value,
            )

            if success:
                successful_weeks.append(week_label)
            else:
                failed_weeks.append((week_label, message))

        # Summary
        if failed_weeks:
            summary = f"⚠️ Calculated DORA metrics for {len(successful_weeks)}/{n_weeks} weeks. Failures:\n"
            for week, msg in failed_weeks[:3]:
                summary += f"  {week}: {msg[:100]}...\n"
        else:
            summary = f"✅ Successfully calculated DORA metrics for all {n_weeks} weeks"

        logger.info(summary)
        return len(failed_weeks) == 0, summary

    except Exception as e:
        error_msg = f"Error calculating DORA metrics: {str(e)}"
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
            lt_days = round(lt_hours / 24, 1) if lt_hours else 0
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
            weekly_cfr.append(round(cfr_percent, 1))
            # NEW: Track release-based CFR
            cfr_release_percent = (
                cfr_data.get("release_failure_rate_percent", 0) if cfr_data else 0
            )
            weekly_cfr_releases.append(round(cfr_release_percent, 1))

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
            weekly_mttr.append(round(mttr_hours, 1) if mttr_hours else 0)

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
        overall_lead_time = (
            sum(all_lead_times) / len(all_lead_times) if all_lead_times else None
        )
        # NEW: Calculate P95 and mean for lead time
        overall_lead_time_p95 = (
            sum(all_lead_times_p95) / len(all_lead_times_p95)
            if all_lead_times_p95
            else None
        )
        overall_lead_time_mean = (
            sum(all_lead_times_mean) / len(all_lead_times_mean)
            if all_lead_times_mean
            else None
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
        overall_mttr = (
            sum(all_mttr_values) / len(all_mttr_values) if all_mttr_values else None
        )
        # NEW: Calculate P95 and mean for MTTR
        overall_mttr_p95 = (
            sum(all_mttr_p95) / len(all_mttr_p95) if all_mttr_p95 else None
        )
        overall_mttr_mean = (
            sum(all_mttr_mean) / len(all_mttr_mean) if all_mttr_mean else None
        )

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
                "value": round(overall_lead_time / 24, 1)
                if overall_lead_time is not None
                else None,
                "p95_value": round(overall_lead_time_p95 / 24, 1)
                if overall_lead_time_p95 is not None
                else None,  # NEW: P95 in days
                "mean_value": round(overall_lead_time_mean / 24, 1)
                if overall_lead_time_mean is not None
                else None,  # NEW: Mean in days
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_lead_time,
                "total_issue_count": total_lead_time_issues,
            },
            "change_failure_rate": {
                "value": round(overall_cfr, 1),
                "release_value": round(
                    overall_cfr_releases, 1
                ),  # NEW: Release-based CFR
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_cfr,
                "weekly_release_values": weekly_cfr_releases,  # NEW: Release CFR per week
                "total_issue_count": total_cfr_issues,
            },
            "mean_time_to_recovery": {
                "value": round(overall_mttr, 1) if overall_mttr else None,
                "p95_value": round(overall_mttr_p95, 1)
                if overall_mttr_p95 is not None
                else None,  # NEW: P95 MTTR
                "mean_value": round(overall_mttr_mean, 1)
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
