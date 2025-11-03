"""
Metrics Calculator for Flow and DORA Metrics

This module calculates Flow and DORA metrics from JIRA data and saves them
as weekly snapshots. This approach avoids recalculating metrics on every page load,
reducing calculation cost to once per week.

Key Functions:
- calculate_and_save_weekly_metrics(): Main entry point for metric calculation

Created: October 31, 2025
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple

logger = logging.getLogger(__name__)


def get_current_iso_week() -> str:
    """
    Get current ISO week label in format YYYY-WW (without "W" prefix).

    Returns:
        str: ISO week label (e.g., "2025-44")
    """
    now = datetime.now()
    iso_calendar = now.isocalendar()
    # Format without "W" prefix to match dashboard format
    return f"{iso_calendar.year}-{iso_calendar.week:02d}"


def calculate_and_save_weekly_metrics(
    week_label: str = "", progress_callback=None
) -> Tuple[bool, str]:
    """
    Calculate all Flow/DORA metrics for current week and save to snapshots.

    Automatically downloads changelog data if not available. Uses existing v2
    calculator functions from flow_calculator.py to calculate metrics, then
    saves them to metrics_snapshots.json for instant retrieval.

    Args:
        week_label: ISO week (e.g., "2025-44"). Defaults to current week.
        progress_callback: Optional callback function(message: str) for progress updates

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

        # Load configuration
        from data.persistence import load_app_settings

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

        all_issues_raw = cache_data.get("issues", [])
        if not all_issues_raw:
            return False, "No JIRA issues found in cache."
        logger.info(f"Loaded {len(all_issues_raw)} issues from cache")

        # CRITICAL: Filter out DevOps project issues and Operational Tasks
        # Flow metrics should ONLY include development project issues
        # DevOps issues (Operational Tasks) are ONLY for DORA metadata
        devops_projects = app_settings.get("devops_projects", [])

        if devops_projects:
            from data.project_filter import filter_development_issues

            all_issues = filter_development_issues(all_issues_raw, devops_projects)
            filtered_count = len(all_issues_raw) - len(all_issues)
            logger.info(
                f"Filtered out {filtered_count} DevOps project issues. "
                f"Using {len(all_issues)} development project issues for Flow metrics."
            )
        else:
            all_issues = all_issues_raw
            logger.info("No DevOps projects configured, using all issues")

        # Check if changelog cache exists
        changelog_cache_file = "jira_changelog_cache.json"
        changelog_available = os.path.exists(changelog_cache_file)

        if not changelog_available:
            report_progress("⏳ Changelog data not found. Downloading from JIRA...")

            # Load JIRA configuration
            from data.jira_simple import get_jira_config, fetch_changelog_on_demand

            config = get_jira_config()
            if not config:
                return (
                    False,
                    "Failed to load JIRA configuration. Please configure JIRA settings first.",
                )

            # Download changelog (this can take 1-2 minutes)
            # Pass progress callback to get real-time updates
            changelog_success, changelog_message = fetch_changelog_on_demand(
                config, progress_callback=report_progress
            )

            if not changelog_success:
                return (
                    False,
                    f"Failed to download changelog: {changelog_message}. Flow Time and Efficiency metrics require changelog data.",
                )

            report_progress(f"✅ {changelog_message}")
        else:
            logger.info("Changelog cache found, using existing data")

        # Load changelog data and merge into issues
        report_progress("📊 Loading changelog data...")
        if os.path.exists(changelog_cache_file):
            with open(changelog_cache_file, "r", encoding="utf-8") as f:
                changelog_cache = json.load(f)

            # Merge changelog into issues
            merged_count = 0
            for issue in all_issues:
                issue_key = issue.get("key", "")
                if issue_key in changelog_cache:
                    issue["changelog"] = changelog_cache[issue_key].get("changelog", {})
                    merged_count += 1

            logger.info(f"Merged changelog data into {merged_count} issues")
        else:
            logger.warning("Changelog cache file not found after download attempt")

        # Get configuration
        completion_statuses = app_settings.get(
            "completion_statuses", ["Done", "Resolved", "Closed"]
        )
        active_statuses = app_settings.get(
            "active_statuses", ["In Progress", "In Review", "In Testing"]
        )
        start_statuses = app_settings.get("flow_start_statuses", ["In Progress"])
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

        # Get week boundaries for filtering
        from data.changelog_processor import get_first_status_transition_timestamp

        week_label_clean = week_label.replace("W", "").replace("-W", "-")
        try:
            year, week_num = map(int, week_label_clean.split("-"))
            jan_4 = datetime(year, 1, 4)
            week_1_monday = jan_4 - timedelta(days=jan_4.weekday())
            target_week_monday = week_1_monday + timedelta(weeks=week_num - 1)
            week_start = target_week_monday
            week_end = week_start + timedelta(days=7)
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse week label '{week_label}': {e}")
            return False, f"Invalid week label format: {week_label}"

        # For current week, use running metrics (completions up to NOW)
        # For historical weeks, use full week period
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        is_current_week = now < week_end
        completion_cutoff = min(week_end, now) if is_current_week else week_end

        # Filter issues completed in this specific week (up to cutoff time)
        report_progress(
            f"🔍 Filtering issues completed in week {week_label}"
            + (" (running total)" if is_current_week else "")
            + "..."
        )
        issues_completed_this_week = []
        for issue in all_issues:
            completion_timestamp = None
            for status in completion_statuses:
                timestamp = get_first_status_transition_timestamp(issue, status)
                if timestamp:
                    # Convert to UTC before stripping timezone (don't just strip!)
                    timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
                    if completion_timestamp is None or timestamp < completion_timestamp:
                        completion_timestamp = timestamp

            if (
                completion_timestamp
                and week_start <= completion_timestamp < completion_cutoff
            ):
                issues_completed_this_week.append(issue)

        logger.info(
            f"Found {len(issues_completed_this_week)} issues completed in week {week_label}"
            + (" (running total)" if is_current_week else " (full week)")
        )

        # Calculate Flow Time using existing v2 function (for issues completed this week)
        report_progress("📊 Calculating Flow Time metric...")
        from data.flow_calculator import calculate_flow_time_v2

        flow_time_result = calculate_flow_time_v2(
            issues_completed_this_week,  # Only issues completed this week
            start_statuses,
            completion_statuses,
            active_statuses,
        )

        # Calculate Flow Efficiency using existing v2 function (for issues completed this week)
        report_progress("📊 Calculating Flow Efficiency metric...")
        from data.flow_calculator import calculate_flow_efficiency_v2

        efficiency_result = calculate_flow_efficiency_v2(
            issues_completed_this_week,  # Only issues completed this week
            start_statuses,
            completion_statuses,
            active_statuses,
        )

        # Calculate Flow Load with historical WIP reconstruction
        # For historical weeks, we need WIP as-of that week's end
        report_progress("📊 Calculating Flow Load metric...")
        from data.changelog_processor import get_status_at_point_in_time

        # Calculate historical WIP (issues in active work at end of this week)
        # For current/future weeks, check WIP as of NOW instead of future date
        # Reuse the same 'now' and 'is_current_week' from completion filtering above
        issues_in_wip_at_week_end = []
        week_end_check_time = completion_cutoff  # Use same cutoff time as completions

        for issue in all_issues:
            # For current week, use current status directly (more accurate, includes issues without changelog)
            if is_current_week:
                current_status = (
                    issue.get("fields", {}).get("status", {}).get("name", "")
                )
                is_in_wip_now = current_status in wip_statuses
                is_completed = current_status in completion_statuses

                if is_in_wip_now and not is_completed:
                    issues_in_wip_at_week_end.append(issue)
                # Don't continue - we need to fall through to breakdown calculation

            else:
                # For historical weeks, reconstruct status at that point in time
                # This includes issues sitting in same status for long periods (e.g., "Selected", "Analysis")
                status_at_week_end = get_status_at_point_in_time(
                    issue, week_end_check_time
                )

                # If issue existed and was in WIP status at week end, count it
                if status_at_week_end and status_at_week_end in wip_statuses:
                    issues_in_wip_at_week_end.append(issue)

        # Calculate breakdowns for WIP
        by_status = {}
        by_issue_type = {}
        for issue in issues_in_wip_at_week_end:
            # For current week, use current status directly
            if is_current_week:
                issue_wip_status = (
                    issue.get("fields", {}).get("status", {}).get("name", "")
                )
            else:
                # For historical weeks, get the WIP status at week end
                # (the most recent WIP status before week end)
                issue_wip_status = None
                latest_wip_time = None
                for wip_status in wip_statuses:
                    timestamp = get_first_status_transition_timestamp(issue, wip_status)
                    if timestamp:
                        # Convert to UTC before stripping timezone
                        timestamp = timestamp.astimezone(timezone.utc).replace(
                            tzinfo=None
                        )
                        if timestamp < week_end_check_time:
                            if latest_wip_time is None or timestamp > latest_wip_time:
                                latest_wip_time = timestamp
                                issue_wip_status = wip_status

            if issue_wip_status:
                by_status[issue_wip_status] = by_status.get(issue_wip_status, 0) + 1

            # Get issue type (same for both current and historical)
            issue_type = (
                issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown")
            )
            by_issue_type[issue_type] = by_issue_type.get(issue_type, 0) + 1

        wip_time_desc = (
            "now (running)" if is_current_week else f"at {week_end_check_time.date()}"
        )
        logger.info(
            f"{'Current' if is_current_week else 'Historical'} WIP for week {week_label}: "
            f"{len(issues_in_wip_at_week_end)} items were in active work {wip_time_desc}"
        )
        logger.info(f"WIP breakdown by status: {by_status}")
        logger.info(f"WIP breakdown by issue type: {by_issue_type}")

        # Build flow load result manually from historical data
        load_result = {
            "metric_name": "flow_load",
            "wip_count": len(issues_in_wip_at_week_end),
            "by_status": by_status,
            "by_issue_type": by_issue_type,
            "unit": "items",
            "error_state": "success",
            "error_message": None,
        }

        # Calculate Flow Velocity (already have issues_completed_this_week)
        report_progress("📊 Calculating Flow Velocity...")
        velocity_count = len(issues_completed_this_week)

        logger.info(
            f"Flow Velocity: {velocity_count} items completed in week {week_label} "
            f"({week_start.date()} to {week_end.date()})"
        )

        # Extract metrics from results
        metrics_saved = 0
        metrics_details = []
        from data.metrics_snapshots import save_metric_snapshot

        # Save Flow Time (always save, even with 0 completed issues for UI consistency)
        flow_time_error = flow_time_result.get("error_state")
        if flow_time_error == "success":
            # Convert hours to days for consistency
            total_flow_time = flow_time_result.get("total_flow_time", {})
            median_hours = total_flow_time.get("median_hours", 0)
            mean_hours = total_flow_time.get("mean_hours", 0)
            completed = total_flow_time.get("count", 0)

            flow_time_snapshot = {
                "median_days": (median_hours / 24) if median_hours else 0,
                "avg_days": (mean_hours / 24) if mean_hours else 0,
                "p85_days": (total_flow_time.get("p95_hours", 0) / 24)
                if total_flow_time.get("p95_hours")
                else 0,
                "completed_count": completed,
            }
            save_metric_snapshot(week_label, "flow_time", flow_time_snapshot)
            metrics_saved += 1
            metrics_details.append(
                f"Flow Time: {flow_time_snapshot['median_days']:.1f} days median ({completed} issues)"
            )
            logger.info(
                f"Saved Flow Time: median {flow_time_snapshot['median_days']:.1f} days, {completed} issues"
            )
        else:
            # Save empty snapshot for weeks with no completed issues (UI needs this)
            flow_time_snapshot = {
                "median_days": 0,
                "avg_days": 0,
                "p85_days": 0,
                "completed_count": 0,
            }
            save_metric_snapshot(week_label, "flow_time", flow_time_snapshot)
            metrics_saved += 1
            error_msg = flow_time_result.get("error_message", "Unknown error")
            metrics_details.append("Flow Time: N/A (0 completed issues)")
            logger.warning(
                f"Flow Time calculation failed: {flow_time_error} - {error_msg}"
            )

        # Save Flow Efficiency (use MEAN instead of median for more representative value)
        # Always save, even with 0 completed issues for UI consistency
        efficiency_error = efficiency_result.get("error_state")
        if efficiency_error == "success":
            completed = efficiency_result.get("count", 0)
            mean_pct = efficiency_result.get(
                "mean_percent", 0
            )  # Use mean instead of median
            median_pct = efficiency_result.get("median_percent", 0)

            efficiency_snapshot = {
                "overall_pct": mean_pct,  # Changed to mean for more representative value
                "median_pct": median_pct,  # Keep median for reference
                "avg_active_days": 0,  # Not directly available
                "avg_waiting_days": 0,  # Not directly available
                "completed_count": completed,
            }
            save_metric_snapshot(week_label, "flow_efficiency", efficiency_snapshot)
            metrics_saved += 1
            metrics_details.append(
                f"Flow Efficiency: {mean_pct:.1f}% mean, {median_pct:.1f}% median ({completed} issues)"
            )
            logger.info(
                f"Saved Flow Efficiency: mean={mean_pct:.1f}%, median={median_pct:.1f}%, {completed} issues"
            )
        else:
            # Save empty snapshot for weeks with no completed issues (UI needs this)
            efficiency_snapshot = {
                "overall_pct": 0,
                "median_pct": 0,
                "avg_active_days": 0,
                "avg_waiting_days": 0,
                "completed_count": 0,
            }
            save_metric_snapshot(week_label, "flow_efficiency", efficiency_snapshot)
            metrics_saved += 1
            error_msg = efficiency_result.get("error_message", "Unknown error")
            metrics_details.append("Flow Efficiency: N/A (0 completed issues)")
            logger.warning(
                f"Flow Efficiency calculation failed: {efficiency_error} - {error_msg}"
            )

        # Save Flow Load
        load_error = load_result.get("error_state")
        if load_error == "success":
            wip = load_result.get("wip_count", 0)

            load_snapshot = {
                "wip_count": wip,
                "by_status": load_result.get("by_status", {}),
                "by_issue_type": load_result.get("by_issue_type", {}),
            }
            save_metric_snapshot(week_label, "flow_load", load_snapshot)
            metrics_saved += 1
            metrics_details.append(f"Flow Load: {wip} items in progress")
            logger.info(f"Saved Flow Load: {wip} items")
        else:
            error_msg = load_result.get("error_message", "Unknown error")
            metrics_details.append(f"Flow Load: ⚠️ {error_msg}")
            logger.warning(f"Flow Load calculation failed: {load_error} - {error_msg}")

        # Calculate work distribution using flow_type_classifier with effort categories
        report_progress("📊 Categorizing work distribution...")
        from data.flow_type_classifier import get_flow_type

        # Get effort category field from configuration
        field_mappings = app_settings.get("field_mappings", {})
        effort_category_field = field_mappings.get("effort_category")

        if not effort_category_field:
            logger.warning(
                "effort_category field not configured, work distribution may be inaccurate"
            )
            # Use a placeholder that won't match any field
            effort_category_field = "customfield_XXXXX"

        distribution = {
            "feature": 0,
            "defect": 0,
            "risk": 0,
            "tech_debt": 0,
        }

        for issue in issues_completed_this_week:
            flow_type = get_flow_type(issue, effort_category_field)
            # Map flow types to distribution keys
            if flow_type == "Feature":
                distribution["feature"] += 1
            elif flow_type == "Defect":
                distribution["defect"] += 1
            elif flow_type == "Risk":
                distribution["risk"] += 1
            elif flow_type == "Technical Debt":
                distribution["tech_debt"] += 1
            else:
                # Unknown types go to tech_debt as catchall
                distribution["tech_debt"] += 1

        logger.info(
            f"Work distribution for week {week_label}: "
            f"Features={distribution['feature']}, Defects={distribution['defect']}, "
            f"Tech Debt={distribution['tech_debt']}, Risk={distribution['risk']}"
        )

        # Save Flow Velocity with distribution
        velocity_snapshot = {
            "completed_count": velocity_count,
            "week": week_label,
            "distribution": distribution,
        }
        save_metric_snapshot(week_label, "flow_velocity", velocity_snapshot)
        metrics_saved += 1
        metrics_details.append(f"Flow Velocity: {velocity_count} items completed")
        logger.info(
            f"Saved Flow Velocity: {velocity_count} items completed in week {week_label}"
        )

        # Save metadata
        trends = {
            "flow_time_trend": "stable",
            "flow_efficiency_trend": "stable",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        save_metric_snapshot(week_label, "trends", trends)

        # Create detailed message
        if metrics_saved == 0:
            message = (
                f"⚠️ No metrics calculated for week {week_label}. Details:\n"
                + "\n".join(metrics_details)
            )
            logger.warning(message)
            return False, message

        message = (
            f"✅ Saved {metrics_saved} metrics for week {week_label}:\n"
            + "\n".join(metrics_details)
        )
        logger.info(f"Successfully saved {metrics_saved} metrics for week {week_label}")
        return True, message

    except Exception as e:
        error_msg = f"Error calculating metrics: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def calculate_metrics_for_last_n_weeks(
    n_weeks: int = 12, progress_callback=None
) -> Tuple[bool, str]:
    """
    Calculate metrics for the last N weeks (including current week).

    This is useful for populating historical data and ensuring sparklines/trends
    have enough data points.

    Args:
        n_weeks: Number of weeks to calculate (default: 12)
        progress_callback: Optional callback function(message: str) for progress updates

    Returns:
        Tuple of (success: bool, summary_message: str)
    """
    from data.iso_week_bucketing import get_last_n_weeks

    try:
        # Get week labels for last N weeks
        weeks = get_last_n_weeks(n_weeks)

        logger.info(f"Calculating metrics for last {n_weeks} weeks")

        successful_weeks = []
        failed_weeks = []

        for week_label, monday, sunday in weeks:
            # Normalize week label format (remove "W" prefix if present)
            week_label_normalized = week_label.replace("W", "").replace("-W", "-")

            logger.info(
                f"Processing week {week_label_normalized} ({monday} to {sunday})"
            )

            if progress_callback:
                progress_callback(
                    f"📅 Calculating metrics for week {week_label_normalized} ({monday} to {sunday})..."
                )

            success, message = calculate_and_save_weekly_metrics(
                week_label=week_label_normalized, progress_callback=progress_callback
            )

            if success:
                successful_weeks.append(week_label)
            else:
                failed_weeks.append((week_label, message))

        # Summary
        if failed_weeks:
            summary = f"⚠️ Calculated metrics for {len(successful_weeks)}/{n_weeks} weeks. Failures:\n"
            for week, msg in failed_weeks[:3]:  # Show first 3 failures
                summary += f"  {week}: {msg[:100]}...\n"
        else:
            summary = f"✅ Successfully calculated metrics for all {n_weeks} weeks ({successful_weeks[0]} to {successful_weeks[-1]})"

        logger.info(summary)
        return len(failed_weeks) == 0, summary

    except Exception as e:
        error_msg = f"Error calculating multi-week metrics: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg
