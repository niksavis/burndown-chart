"""Weekly metrics calculation orchestrator.

Delegates to focused sub-modules:
- _weekly_issue_prep: issue loading, filtering, changelog, week boundaries
- _weekly_flow: Flow metric family (Time, Efficiency, Load, Velocity)
- _weekly_dora_prep: DORA issue classification and filter helpers
- _weekly_dora_calc: DORA metric family (Lead Time, Deploy Freq, CFR, MTTR)
"""

import logging
from datetime import UTC, datetime

from data.metrics.helpers import get_current_iso_week

logger = logging.getLogger(__name__)


def calculate_and_save_weekly_metrics(
    week_label: str = "",
    progress_callback=None,
    profile_id: str | None = None,
) -> tuple[bool, str]:
    """Calculate all Flow/DORA metrics for a week and save to snapshots.

    Args:
        week_label: ISO week (e.g., "2025-44"). Defaults to current week.
        progress_callback: Optional callback(message: str) for progress updates.
        profile_id: Optional profile ID; defaults to active profile.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Default to current week
        if not week_label:
            week_label = get_current_iso_week()

        logger.info(f"Starting metric calculation for week {week_label}")

        # Helper function for progress updates
        def report_progress(message: str):
            logger.info(message)
            if progress_callback:
                progress_callback(message)

        # Load profile configuration for status lists and field mappings
        report_progress("Loading profile configuration...")
        from configuration.metrics_config import MetricsConfig

        try:
            # Load active profile or use specified profile_id
            metrics_config = MetricsConfig(profile_id=profile_id)
            logger.info(f"Loaded profile: {metrics_config.profile_id}")

        except Exception as e:
            logger.error(f"Failed to load profile configuration: {e}")
            return (
                False,
                f"Failed to load profile configuration: {str(e)}. "
                "Please configure JIRA mappings in the UI.",
            )

        # Load configuration
        from data.persistence import load_app_settings

        app_settings = load_app_settings()

        if not app_settings:
            return False, "Failed to load app settings"

        # Check if JIRA data exists in database
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return False, "No active profile/query selected."

        # Check cache - skip recalculation for up-to-date historical weeks
        from data.metrics._weekly_issue_prep import check_metrics_cached

        if check_metrics_cached(week_label):
            report_progress(
                f"[OK] Week {week_label} already calculated - using cached metrics"
            )
            return True, f"[OK] Metrics for week {week_label} already up-to-date"

        # Load and filter issues from database
        from data.metrics._weekly_issue_prep import load_and_filter_issues

        try:
            all_issues, all_issues_raw = load_and_filter_issues(
                backend, active_profile_id, active_query_id, app_settings
            )
        except ValueError as e:
            return False, str(e)

        # Load changelog and merge into issues in-place
        from data.metrics._weekly_issue_prep import load_and_merge_changelog

        all_issues, changelog_available = load_and_merge_changelog(
            backend, all_issues, active_profile_id, active_query_id
        )

        # Compute week date boundaries
        from data.metrics._weekly_issue_prep import compute_week_boundaries

        try:
            week_start, week_end, is_current_week, completion_cutoff = (
                compute_week_boundaries(week_label)
            )
        except ValueError as e:
            logger.error(f"Failed to parse week label '{week_label}': {e}")
            return False, str(e)

        flow_end_statuses = app_settings.get(
            "flow_end_statuses", ["Done", "Resolved", "Closed"]
        )
        wip_statuses = app_settings.get(
            "wip_statuses",
            [
                "In Progress",
                "In Review",
                "Testing",
                "Ready for Testing",
                "In Deployment",
            ],
        )

        # Filter issues completed within this week
        report_progress(
            f"[Filter] Filtering issues completed in week {week_label}"
            + (" (running total)" if is_current_week else "")
            + "..."
        )
        from data.metrics._weekly_issue_prep import filter_completed_in_week

        issues_completed = filter_completed_in_week(
            all_issues, flow_end_statuses, week_start, completion_cutoff
        )
        logger.info(
            f"Found {len(issues_completed)} issues completed in week {week_label}"
            + (" (running total)" if is_current_week else " (full week)")
        )

        # Calculate and save Flow metrics
        from data.metrics._weekly_flow import calculate_flow_metrics

        flow_saved, flow_details = calculate_flow_metrics(
            issues_completed,
            all_issues,
            changelog_available,
            wip_statuses,
            flow_end_statuses,
            week_start,
            week_end,
            is_current_week,
            completion_cutoff,
            app_settings,
            week_label,
            report_progress,
        )

        metrics_saved = flow_saved
        metrics_details = flow_details

        # Calculate and save DORA metrics
        report_progress(
            "[Stats] Calculating DORA metrics (Lead Time, Deployment Frequency)..."
        )

        from data.metrics._weekly_dora_prep import (
            classify_dora_issues,
            collect_development_fix_versions,
        )

        operational_tasks, development_issues, production_bugs = classify_dora_issues(
            all_issues, all_issues_raw, app_settings
        )
        logger.info(f"Week {week_label} boundaries: {week_start} to {week_end}")

        development_fix_versions = collect_development_fix_versions(all_issues)

        from data.fixversion_matcher import build_fixversion_release_map

        fixversion_release_map = build_fixversion_release_map(
            operational_tasks,
            valid_fix_versions=development_fix_versions,
            flow_end_statuses=flow_end_statuses,
        )
        logger.info(
            f"[DORA] Built fixVersion release map: "
            f"{len(fixversion_release_map)} versions "
            "(filtered to development project fixVersions)"
        )

        dora_mappings = app_settings.get("field_mappings", {}).get("dora", {})

        from data.metrics._weekly_dora_calc import calculate_dora_metrics

        dora_saved, dora_details = calculate_dora_metrics(
            operational_tasks,
            development_issues,
            production_bugs,
            development_fix_versions,
            fixversion_release_map,
            flow_end_statuses,
            dora_mappings,
            week_label,
            week_start,
            week_end,
            report_progress,
        )

        metrics_saved += dora_saved
        metrics_details.extend(dora_details)

        # Save trend metadata
        from data.metrics_snapshots import save_metric_snapshot

        trends = {
            "flow_time_trend": "stable",
            "flow_efficiency_trend": "stable",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        save_metric_snapshot(week_label, "trends", trends)

        # Build result message
        if metrics_saved == 0:
            message = (
                f"[!] No metrics calculated for week {week_label}. Details:\n"
                + "\n".join(metrics_details)
            )
            logger.warning(message)
            return False, message

        message = (
            f"[OK] Saved {metrics_saved} metrics for week {week_label}:\n"
            + "\n".join(metrics_details)
        )
        logger.info(f"Successfully saved {metrics_saved} metrics for week {week_label}")
        return True, message

    except Exception as e:
        error_msg = f"Error calculating metrics: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg
