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
from typing import Tuple, List, Optional, Dict, Any

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
        from data.profile_manager import get_active_query_workspace

        query_workspace = get_active_query_workspace()
        cache_file = str(query_workspace / "jira_cache.json")
        if not os.path.exists(cache_file):
            return False, "No JIRA data available. Please update data first."

        # OPTIMIZATION: Check if metrics already exist and are up-to-date
        # Skip recalculation if:
        # 1. Metrics snapshot exists for this week
        # 2. JIRA cache hasn't been updated since snapshot was created
        # 3. This is NOT the current week (current week is a running total that changes)
        from data.metrics_snapshots import get_metric_snapshot

        # Determine if this is the current week
        current_week_label = get_current_iso_week()
        is_current_week_check = week_label == current_week_label

        # Only use cached metrics for historical weeks
        if not is_current_week_check:
            existing_snapshot = get_metric_snapshot(week_label, "flow_velocity")
            if existing_snapshot:
                # Check if cache file is newer than snapshot
                cache_mtime = os.path.getmtime(cache_file)
                snapshot_timestamp_str = existing_snapshot.get("timestamp")

                if snapshot_timestamp_str:
                    snapshot_timestamp = datetime.fromisoformat(
                        snapshot_timestamp_str.replace("Z", "+00:00")
                    )
                    snapshot_mtime = snapshot_timestamp.timestamp()

                    if cache_mtime < snapshot_mtime:
                        # Cache is older than snapshot - metrics are up-to-date
                        logger.info(
                            f"✅ Metrics for week {week_label} already exist and are up-to-date. Skipping recalculation."
                        )
                        report_progress(
                            f"✅ Week {week_label} already calculated - using cached metrics"
                        )
                        return (
                            True,
                            f"✅ Metrics for week {week_label} already up-to-date",
                        )
        else:
            logger.info(
                f"📊 Week {week_label} is current week - will recalculate (running total)"
            )

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
        # NOTE: Changelog is OPTIONAL - only needed for Flow Time and Flow Efficiency
        # All other metrics (Flow Velocity, Load, Distribution, ALL DORA metrics) work without it
        changelog_cache_file = str(query_workspace / "jira_changelog_cache.json")
        changelog_available = os.path.exists(changelog_cache_file)

        if not changelog_available:
            report_progress("⏳ Changelog data not found. Downloading from JIRA...")

            # Load JIRA configuration
            from data.jira_simple import get_jira_config, fetch_changelog_on_demand

            config = get_jira_config()
            if not config:
                logger.warning(
                    "Failed to load JIRA configuration. Continuing without changelog (Flow Time/Efficiency will be unavailable)."
                )
                changelog_available = False
            else:
                # Download changelog (this can take 1-2 minutes)
                # Pass progress callback to get real-time updates
                changelog_success, changelog_message = fetch_changelog_on_demand(
                    config, progress_callback=report_progress
                )

                if not changelog_success:
                    # DON'T FAIL - just warn and continue without changelog
                    logger.warning(
                        f"Failed to download changelog: {changelog_message}. "
                        "Flow Time and Efficiency metrics will be unavailable. "
                        "All other metrics (Velocity, Load, Distribution, DORA) will still be calculated."
                    )
                    report_progress(
                        "⚠️ Changelog download failed. Continuing with available data..."
                    )
                    changelog_available = False
                else:
                    report_progress(f"✅ {changelog_message}")
                    changelog_available = True
        else:
            logger.info("Changelog cache found, using existing data")

        # Load changelog data and merge into issues (if available)
        if changelog_available and os.path.exists(changelog_cache_file):
            report_progress("📊 Loading changelog data...")
            try:
                with open(changelog_cache_file, "r", encoding="utf-8") as f:
                    changelog_cache = json.load(f)

                # Merge changelog into issues
                merged_count = 0
                for issue in all_issues:
                    issue_key = issue.get("key", "")
                    if issue_key in changelog_cache:
                        issue["changelog"] = changelog_cache[issue_key].get(
                            "changelog", {}
                        )
                        merged_count += 1

                logger.info(f"Merged changelog data into {merged_count} issues")
            except Exception as e:
                logger.warning(
                    f"Failed to load changelog cache: {e}. Continuing without it."
                )
                changelog_available = False
        elif not changelog_available:
            logger.info(
                "Changelog not available. Flow Time and Efficiency metrics will be skipped."
            )

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

        # Calculate Flow Time using dual-mode function (Feature 012 - variable extraction)
        # REQUIRES CHANGELOG DATA - skip if not available
        if changelog_available:
            report_progress("📊 Calculating Flow Time metric...")
            from data.flow_calculator import calculate_flow_time
            from data.field_mapper import get_field_mappings

            field_mappings = get_field_mappings()
            flow_time_result = calculate_flow_time(
                issues_completed_this_week,  # Only issues completed this week
                field_mappings=field_mappings,
                time_period_days=7,  # Weekly calculation
                # use_variable_extraction=True by default (Phase 3)
            )
        else:
            logger.info("Skipping Flow Time (requires changelog data)")
            flow_time_result = None

        # Calculate Flow Efficiency using dual-mode function (Feature 012 - variable extraction)
        # REQUIRES CHANGELOG DATA - skip if not available
        if changelog_available:
            report_progress("📊 Calculating Flow Efficiency metric...")
            from data.flow_calculator import calculate_flow_efficiency
            from data.field_mapper import get_field_mappings

            field_mappings = get_field_mappings()
            efficiency_result = calculate_flow_efficiency(
                issues_completed_this_week,  # Only issues completed this week
                field_mappings=field_mappings,
                time_period_days=7,  # Weekly calculation
                # use_variable_extraction=True by default (Phase 3)
            )
        else:
            logger.info("Skipping Flow Efficiency (requires changelog data)")
            efficiency_result = None

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
        # Skip if changelog not available (flow_time_result will be None)
        if flow_time_result is not None:
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
        else:
            # Changelog not available - save empty snapshot
            flow_time_snapshot = {
                "median_days": 0,
                "avg_days": 0,
                "p85_days": 0,
                "completed_count": 0,
            }
            save_metric_snapshot(week_label, "flow_time", flow_time_snapshot)
            metrics_saved += 1
            metrics_details.append("Flow Time: Skipped (no changelog data)")
            logger.info("Flow Time: Skipped (changelog not available)")

        # Save Flow Efficiency (use MEAN instead of median for more representative value)
        # Always save, even with 0 completed issues for UI consistency
        # Skip if changelog not available (efficiency_result will be None)
        if efficiency_result is not None:
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
        else:
            # Changelog not available - save empty snapshot
            efficiency_snapshot = {
                "overall_pct": 0,
                "median_pct": 0,
                "avg_active_days": 0,
                "avg_waiting_days": 0,
                "completed_count": 0,
            }
            save_metric_snapshot(week_label, "flow_efficiency", efficiency_snapshot)
            metrics_saved += 1
            metrics_details.append("Flow Efficiency: Skipped (no changelog data)")
            logger.info("Flow Efficiency: Skipped (changelog not available)")

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

        # Calculate work distribution using user-configured flow_type_mappings
        report_progress("📊 Categorizing work distribution...")
        from configuration.metrics_config import get_metrics_config

        # Get field mappings from configuration
        field_mappings = app_settings.get("field_mappings", {})
        flow_type_field = field_mappings.get("flow_item_type", "issuetype")
        effort_category_field = field_mappings.get("effort_category")

        if not effort_category_field:
            logger.warning(
                "effort_category field not configured, classification will use issue type only"
            )

        # Get metrics config for classification
        config = get_metrics_config()

        distribution = {
            "feature": 0,
            "defect": 0,
            "risk": 0,
            "tech_debt": 0,
        }

        for issue in issues_completed_this_week:
            fields = issue.get("fields", {})

            # Extract issue type
            issue_type_value = fields.get(flow_type_field)
            if isinstance(issue_type_value, dict):
                issue_type = issue_type_value.get("name") or issue_type_value.get(
                    "value", ""
                )
            else:
                issue_type = str(issue_type_value) if issue_type_value else ""

            # Extract effort category (optional)
            effort_category = None
            if effort_category_field:
                effort_value = fields.get(effort_category_field)
                if isinstance(effort_value, dict):
                    effort_category = effort_value.get("value") or effort_value.get(
                        "name"
                    )
                else:
                    effort_category = str(effort_value) if effort_value else None

            # Use configured classification
            flow_type = config.classify_issue_to_flow_type(issue_type, effort_category)

            # Map flow types to distribution keys
            if flow_type == "Feature":
                distribution["feature"] += 1
            elif flow_type == "Defect":
                distribution["defect"] += 1
            elif flow_type == "Risk":
                distribution["risk"] += 1
            elif flow_type == "Technical_Debt":
                distribution["tech_debt"] += 1
            else:
                # Unknown types - don't count (or could default to feature)
                logger.debug(
                    f"Issue {issue.get('key')} has unknown flow type: {flow_type}"
                )

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

        # ============================================================================
        # DORA METRICS CALCULATION
        # ============================================================================
        report_progress(
            "📊 Calculating DORA metrics (Lead Time, Deployment Frequency)..."
        )

        from data.dora_calculator import (
            calculate_lead_time_for_changes,  # Feature 012 - dual-mode with variable extraction
            aggregate_deployment_frequency_weekly,
        )
        from data.project_filter import (
            filter_development_issues,
            filter_operational_tasks,
            extract_all_fixversions,
        )

        # Get DevOps projects from configuration
        devops_projects = app_settings.get("devops_projects", [])

        # VALIDATION: Warn if same project appears in both lists (causes double-counting)
        development_projects = app_settings.get("development_projects", [])
        if devops_projects and development_projects:
            overlap = set(devops_projects) & set(development_projects)
            if overlap:
                logger.warning(
                    f"⚠️ CONFIGURATION WARNING: Projects {overlap} appear in BOTH devops_projects and development_projects. "
                    "This may cause issues to be counted twice. Please use EITHER project-based filtering (MODE 1) "
                    "OR field-based filtering (MODE 2), not both for the same project."
                )

        if devops_projects:
            logger.info(
                f"Calculating DORA metrics with DevOps projects: {devops_projects}"
            )

            # Filter issues by project type
            # NOTE: all_issues contains only development issues (DevOps filtered out)
            # For DORA, we need both dev issues AND operational tasks from DevOps projects
            development_issues = filter_development_issues(all_issues, devops_projects)

            # Filter bugs from development issues for CFR and MTTR
            bug_types = app_settings.get("bug_types", ["Bug"])
            production_bugs = [
                issue
                for issue in development_issues
                if issue.get("fields", {}).get("issuetype", {}).get("name") in bug_types
            ]

            # Extract fixVersions from development issues for operational task matching
            development_fixversions = extract_all_fixversions(development_issues)
            logger.info(
                f"Extracted {len(development_fixversions)} unique fixVersions from development issues"
            )

            # CRITICAL: Use all_issues_raw (not filtered all_issues) to get operational tasks
            # all_issues was filtered to EXCLUDE DevOps projects, but we need them for DORA
            operational_tasks = filter_operational_tasks(
                all_issues_raw,  # Use unfiltered data that includes RI project
                devops_projects,
                development_fixversions=development_fixversions,
            )

            logger.info(
                f"DORA Week {week_label}: {len(development_issues)} development issues, "
                f"{len(operational_tasks)} operational tasks (with matching fixVersions)"
            )
            logger.info(f"Week {week_label} boundaries: {week_start} to {week_end}")

            # Calculate Lead Time for Changes (Feature 012 - variable extraction)
            try:
                from data.field_mapper import get_field_mappings

                field_mappings = get_field_mappings()
                lead_time_result = calculate_lead_time_for_changes(
                    development_issues,
                    operational_tasks,  # Still pass for backward compatibility
                    field_mappings=field_mappings,
                    time_period_days=7,  # Weekly calculation
                    # use_variable_extraction=True by default (Phase 3)
                )

                # Log exclusion details
                if lead_time_result:
                    logger.info(
                        f"Week {week_label} Lead Time: {lead_time_result.get('issues_with_lead_time', 0)} issues matched, "
                        f"{lead_time_result.get('no_deployment_status_count', 0)} no status, "
                        f"{lead_time_result.get('no_operational_task_count', 0)} no op task, "
                        f"{lead_time_result.get('no_deployment_date_count', 0)} no date, "
                        f"{lead_time_result.get('excluded_count', 0)} excluded by time"
                    )

                if lead_time_result and lead_time_result.get("median_hours"):
                    median_hours = lead_time_result.get("median_hours", 0)
                    mean_hours = lead_time_result.get("mean_hours", 0)
                    p95_hours = lead_time_result.get("p95_hours", 0)
                    lead_time_count = lead_time_result.get(
                        "issues_with_lead_time", 0
                    )  # Use actual matched count, not total_issues

                    # Save Lead Time snapshot (keep hours for loader compatibility)
                    lead_time_snapshot = {
                        "median_hours": median_hours,
                        "mean_hours": mean_hours,
                        "p95_hours": p95_hours,
                        "issues_with_lead_time": lead_time_count,
                    }
                    save_metric_snapshot(
                        week_label, "dora_lead_time", lead_time_snapshot
                    )
                    metrics_saved += 1
                    metrics_details.append(
                        f"DORA Lead Time: {median_hours / 24:.1f} days median ({lead_time_count} issues)"
                    )
                    logger.info(
                        f"Saved DORA Lead Time: {median_hours / 24:.1f} days, {lead_time_count} issues"
                    )
                else:
                    # Save empty snapshot (use hours for loader compatibility)
                    lead_time_snapshot = {
                        "median_hours": 0,
                        "mean_hours": 0,
                        "p95_hours": 0,
                        "issues_with_lead_time": 0,
                    }
                    save_metric_snapshot(
                        week_label, "dora_lead_time", lead_time_snapshot
                    )
                    metrics_saved += 1
                    metrics_details.append(
                        "DORA Lead Time: No Data (no matching dev→ops linkage)"
                    )
                    logger.info(f"DORA Lead Time: No data for week {week_label}")

            except Exception as e:
                logger.error(f"Failed to calculate DORA Lead Time: {e}", exc_info=True)
                # Save empty snapshot on error (use hours for loader compatibility)
                lead_time_snapshot = {
                    "median_hours": 0,
                    "mean_hours": 0,
                    "p95_hours": 0,
                    "issues_with_lead_time": 0,
                }
                save_metric_snapshot(week_label, "dora_lead_time", lead_time_snapshot)
                metrics_saved += 1
                metrics_details.append(f"DORA Lead Time: Error ({str(e)[:50]})")

            # Calculate Deployment Frequency
            try:
                completion_statuses = app_settings.get(
                    "completion_statuses", ["Done", "Resolved", "Closed"]
                )

                # Get deployment count for this single week
                weekly_deployments = aggregate_deployment_frequency_weekly(
                    operational_tasks,
                    completion_statuses,
                    [week_label],  # Single week
                    case_sensitive=False,
                )

                week_data = weekly_deployments.get(week_label, {})
                deployment_count = week_data.get("deployments", 0)
                release_count = week_data.get("releases", 0)
                release_names = week_data.get("release_names", [])

                # Save Deployment Frequency snapshot with both deployments and releases
                deployment_snapshot = {
                    "deployment_count": deployment_count,
                    "release_count": release_count,  # NEW: Unique releases
                    "release_names": release_names,  # NEW: List of release names
                    "week": week_label,
                }
                save_metric_snapshot(
                    week_label, "dora_deployment_frequency", deployment_snapshot
                )
                metrics_saved += 1
                metrics_details.append(
                    f"DORA Deployment Frequency: {deployment_count} deployments, {release_count} releases"
                )
                logger.info(
                    f"Saved DORA Deployment Frequency: {deployment_count} deployments, {release_count} releases"
                )

            except Exception as e:
                logger.error(
                    f"Failed to calculate DORA Deployment Frequency: {e}", exc_info=True
                )
                # Save empty snapshot on error
                deployment_snapshot = {"deployments_count": 0, "week": week_label}
                save_metric_snapshot(
                    week_label, "dora_deployment_frequency", deployment_snapshot
                )
                metrics_saved += 1
                metrics_details.append(
                    f"DORA Deployment Frequency: Error ({str(e)[:50]})"
                )

            # Calculate Change Failure Rate
            try:
                from data.dora_calculator import calculate_change_failure_rate
                from data.field_mapper import get_field_mappings

                # Get required field mappings
                field_mappings = get_field_mappings()
                change_failure_field = field_mappings.get("change_failure")

                if not change_failure_field:
                    logger.warning(
                        "Change Failure or Affected Environment field not configured"
                    )
                    cfr_snapshot = {
                        "change_failure_rate_percent": 0,
                        "total_deployments": 0,
                        "failed_deployments": 0,
                        "week": week_label,
                    }
                    save_metric_snapshot(
                        week_label, "dora_change_failure_rate", cfr_snapshot
                    )
                    metrics_saved += 1
                    metrics_details.append("DORA CFR: Skipped (field not configured)")
                else:
                    cfr_result = calculate_change_failure_rate(
                        operational_tasks,
                        production_bugs,  # Also pass bugs for incident correlation
                        field_mappings=field_mappings,
                        time_period_days=7,  # Weekly calculation
                        # use_variable_extraction=True by default (Phase 3)
                    )

                    cfr_percent = cfr_result.get("change_failure_rate_percent", 0)
                    total_deps = cfr_result.get("total_deployments", 0)
                    failed_deps = cfr_result.get("failed_deployments", 0)
                    # NEW: Get release data
                    total_releases = cfr_result.get("total_releases", 0)
                    failed_releases = cfr_result.get("failed_releases", 0)
                    release_names = cfr_result.get("release_names", [])
                    failed_release_names = cfr_result.get("failed_release_names", [])
                    release_failure_rate = cfr_result.get(
                        "release_failure_rate_percent", 0
                    )

                    cfr_snapshot = {
                        "change_failure_rate_percent": cfr_percent,
                        "total_deployments": total_deps,
                        "failed_deployments": failed_deps,
                        # NEW: Release tracking
                        "total_releases": total_releases,
                        "failed_releases": failed_releases,
                        "release_failure_rate_percent": release_failure_rate,
                        "release_names": release_names,
                        "failed_release_names": failed_release_names,
                        "week": week_label,
                    }
                    save_metric_snapshot(
                        week_label, "dora_change_failure_rate", cfr_snapshot
                    )
                    metrics_saved += 1
                    metrics_details.append(
                        f"DORA CFR: {cfr_percent:.1f}% ({failed_deps}/{total_deps} deployments, "
                        f"{failed_releases}/{total_releases} releases)"
                    )
                    logger.info(
                        f"Saved DORA CFR: {cfr_percent:.1f}% ({failed_deps}/{total_deps} deployments, "
                        f"{failed_releases}/{total_releases} releases)"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to calculate DORA Change Failure Rate: {e}", exc_info=True
                )
                cfr_snapshot = {
                    "change_failure_rate_percent": 0,
                    "total_deployments": 0,
                    "failed_deployments": 0,
                    "week": week_label,
                }
                save_metric_snapshot(
                    week_label, "dora_change_failure_rate", cfr_snapshot
                )
                metrics_saved += 1
                metrics_details.append(f"DORA CFR: Error ({str(e)[:50]})")

            # Calculate Mean Time To Recovery (MTTR)
            try:
                from data.dora_calculator import calculate_mean_time_to_recovery
                from data.field_mapper import get_field_mappings

                # Get required field mappings
                field_mappings = get_field_mappings()
                affected_env_field = field_mappings.get("affected_environment")
                production_value = app_settings.get(
                    "production_environment_values", ["PROD"]
                )[0]

                if not affected_env_field:
                    logger.warning("Affected Environment field not configured for MTTR")
                    mttr_snapshot = {
                        "median_hours": None,
                        "bugs_with_mttr": 0,
                        "week": week_label,
                    }
                    save_metric_snapshot(week_label, "dora_mttr", mttr_snapshot)
                    metrics_saved += 1
                    metrics_details.append("DORA MTTR: Skipped (field not configured)")
                else:
                    mttr_result = calculate_mean_time_to_recovery(
                        production_bugs,
                        field_mappings=field_mappings,
                        time_period_days=7,  # Weekly calculation
                        # use_variable_extraction=True by default (Phase 3)
                    )

                    median_hours = mttr_result.get("median_hours")
                    mean_hours = mttr_result.get("mean_hours")
                    p95_hours = mttr_result.get("p95_hours")
                    bugs_count = mttr_result.get("bugs_with_mttr", 0)

                    mttr_snapshot = {
                        "median_hours": median_hours,
                        "mean_hours": mean_hours,
                        "p95_hours": p95_hours,
                        "bugs_with_mttr": bugs_count,
                        "week": week_label,
                    }
                    save_metric_snapshot(week_label, "dora_mttr", mttr_snapshot)
                    metrics_saved += 1

                    if median_hours:
                        mttr_days = median_hours / 24
                        metrics_details.append(
                            f"DORA MTTR: {mttr_days:.1f} days median ({bugs_count} bugs)"
                        )
                        logger.info(
                            f"Saved DORA MTTR: {mttr_days:.1f} days ({bugs_count} bugs)"
                        )
                    else:
                        metrics_details.append(
                            "DORA MTTR: No Data (no production bugs resolved)"
                        )
                        logger.info(f"DORA MTTR: No data for week {week_label}")

            except Exception as e:
                logger.error(f"Failed to calculate DORA MTTR: {e}", exc_info=True)
                mttr_snapshot = {
                    "median_hours": None,
                    "bugs_with_mttr": 0,
                    "week": week_label,
                }
                save_metric_snapshot(week_label, "dora_mttr", mttr_snapshot)
                metrics_saved += 1
                metrics_details.append(f"DORA MTTR: Error ({str(e)[:50]})")

        else:
            # MODE 2: Field-based detection (simple JIRA setup without DevOps projects)
            logger.info(
                f"🎯 DORA Mode: Field-based detection (scanning all {len(all_issues)} issues for DORA fields)"
            )

            # Use field-based detection to identify DORA-relevant issues
            from data.dora_calculator import filter_issues_by_dora_fields

            filtered_results = filter_issues_by_dora_fields(
                all_issues, field_mappings, app_settings
            )

            operational_tasks = filtered_results["operational_tasks"]
            development_issues = filtered_results["development_issues"]
            production_bugs = filtered_results["production_bugs"]

            logger.info(
                f"Field-based DORA: {len(operational_tasks)} operational tasks, "
                f"{len(development_issues)} development issues, {len(production_bugs)} production bugs"
            )
            logger.info(f"Week {week_label} boundaries: {week_start} to {week_end}")

            # ========================================================================
            # MODE 2: Calculate DORA Metrics using field-based filtering
            # ========================================================================

            # Calculate Lead Time for Changes (Feature 012 - variable extraction)
            try:
                from data.field_mapper import get_field_mappings

                field_mappings = get_field_mappings()
                lead_time_result = calculate_lead_time_for_changes(
                    development_issues,
                    operational_tasks,  # Still pass for backward compatibility
                    field_mappings=field_mappings,
                    time_period_days=7,  # Weekly calculation
                    # use_variable_extraction=True by default (Phase 3)
                )

                # Log exclusion details
                if lead_time_result:
                    logger.info(
                        f"Week {week_label} Lead Time: {lead_time_result.get('issues_with_lead_time', 0)} issues matched, "
                        f"{lead_time_result.get('no_deployment_status_count', 0)} no status, "
                        f"{lead_time_result.get('no_operational_task_count', 0)} no op task, "
                        f"{lead_time_result.get('no_deployment_date_count', 0)} no date, "
                        f"{lead_time_result.get('excluded_count', 0)} excluded by time"
                    )

                if lead_time_result and lead_time_result.get("median_hours"):
                    median_hours = lead_time_result.get("median_hours", 0)
                    mean_hours = lead_time_result.get("mean_hours", 0)
                    p95_hours = lead_time_result.get("p95_hours", 0)
                    lead_time_count = lead_time_result.get("issues_with_lead_time", 0)

                    lead_time_snapshot = {
                        "median_hours": median_hours,
                        "mean_hours": mean_hours,
                        "p95_hours": p95_hours,
                        "issues_with_lead_time": lead_time_count,
                    }
                    save_metric_snapshot(
                        week_label, "dora_lead_time", lead_time_snapshot
                    )
                    metrics_saved += 1
                    metrics_details.append(
                        f"DORA Lead Time: {median_hours / 24:.1f} days median ({lead_time_count} issues)"
                    )
                    logger.info(
                        f"Saved DORA Lead Time: {median_hours / 24:.1f} days, {lead_time_count} issues"
                    )
                else:
                    lead_time_snapshot = {
                        "median_hours": 0,
                        "mean_hours": 0,
                        "p95_hours": 0,
                        "issues_with_lead_time": 0,
                    }
                    save_metric_snapshot(
                        week_label, "dora_lead_time", lead_time_snapshot
                    )
                    metrics_saved += 1
                    metrics_details.append("DORA Lead Time: No Data")
                    logger.info(f"DORA Lead Time: No data for week {week_label}")

            except Exception as e:
                logger.error(f"Failed to calculate DORA Lead Time: {e}", exc_info=True)
                lead_time_snapshot = {
                    "median_hours": 0,
                    "mean_hours": 0,
                    "p95_hours": 0,
                    "issues_with_lead_time": 0,
                }
                save_metric_snapshot(week_label, "dora_lead_time", lead_time_snapshot)
                metrics_saved += 1
                metrics_details.append(f"DORA Lead Time: Error ({str(e)[:50]})")

            # Calculate Deployment Frequency
            try:
                completion_statuses = app_settings.get(
                    "completion_statuses", ["Done", "Resolved", "Closed"]
                )

                weekly_deployments = aggregate_deployment_frequency_weekly(
                    operational_tasks,
                    completion_statuses,
                    [week_label],
                    case_sensitive=False,
                )

                week_data = weekly_deployments.get(week_label, {})
                deployment_count = week_data.get("deployments", 0)
                release_count = week_data.get("releases", 0)
                release_names = week_data.get("release_names", [])

                deployment_snapshot = {
                    "deployment_count": deployment_count,
                    "release_count": release_count,
                    "release_names": release_names,
                    "week": week_label,
                }
                save_metric_snapshot(
                    week_label, "dora_deployment_frequency", deployment_snapshot
                )
                metrics_saved += 1
                metrics_details.append(
                    f"DORA Deployment Frequency: {deployment_count} deployments, {release_count} releases"
                )
                logger.info(
                    f"Saved DORA Deployment Frequency: {deployment_count} deployments, {release_count} releases"
                )

            except Exception as e:
                logger.error(
                    f"Failed to calculate DORA Deployment Frequency: {e}", exc_info=True
                )
                deployment_snapshot = {"deployment_count": 0, "week": week_label}
                save_metric_snapshot(
                    week_label, "dora_deployment_frequency", deployment_snapshot
                )
                metrics_saved += 1
                metrics_details.append(
                    f"DORA Deployment Frequency: Error ({str(e)[:50]})"
                )

            # Calculate Change Failure Rate (MODE 2)
            try:
                from data.dora_calculator import calculate_change_failure_rate
                from data.field_mapper import get_field_mappings

                field_mappings = get_field_mappings()
                change_failure_field = field_mappings.get("change_failure")

                if not change_failure_field:
                    logger.warning("Change Failure field not configured for CFR")
                    cfr_snapshot = {
                        "change_failure_rate_percent": 0,
                        "total_deployments": 0,
                        "failed_deployments": 0,
                        "week": week_label,
                    }
                    save_metric_snapshot(
                        week_label, "dora_change_failure_rate", cfr_snapshot
                    )
                    metrics_saved += 1
                    metrics_details.append("DORA CFR: Skipped (field not configured)")
                else:
                    cfr_result = calculate_change_failure_rate(
                        operational_tasks,
                        production_bugs,  # Also pass bugs for incident correlation
                        field_mappings=field_mappings,
                        time_period_days=7,  # Weekly calculation
                        # use_variable_extraction=True by default (Phase 3)
                    )

                    cfr_percent = cfr_result.get("change_failure_rate_percent", 0)
                    total_deps = cfr_result.get("total_deployments", 0)
                    failed_deps = cfr_result.get("failed_deployments", 0)
                    total_releases = cfr_result.get("total_releases", 0)
                    failed_releases = cfr_result.get("failed_releases", 0)
                    release_names = cfr_result.get("release_names", [])
                    failed_release_names = cfr_result.get("failed_release_names", [])
                    release_failure_rate = cfr_result.get(
                        "release_failure_rate_percent", 0
                    )

                    cfr_snapshot = {
                        "change_failure_rate_percent": cfr_percent,
                        "total_deployments": total_deps,
                        "failed_deployments": failed_deps,
                        "total_releases": total_releases,
                        "failed_releases": failed_releases,
                        "release_failure_rate_percent": release_failure_rate,
                        "release_names": release_names,
                        "failed_release_names": failed_release_names,
                        "week": week_label,
                    }
                    save_metric_snapshot(
                        week_label, "dora_change_failure_rate", cfr_snapshot
                    )
                    metrics_saved += 1
                    metrics_details.append(
                        f"DORA CFR: {cfr_percent:.1f}% ({failed_deps}/{total_deps} deployments)"
                    )
                    logger.info(
                        f"Saved DORA CFR: {cfr_percent:.1f}% ({failed_deps}/{total_deps})"
                    )

            except Exception as e:
                logger.error(f"Failed to calculate DORA CFR: {e}", exc_info=True)
                cfr_snapshot = {
                    "change_failure_rate_percent": 0,
                    "total_deployments": 0,
                    "failed_deployments": 0,
                    "week": week_label,
                }
                save_metric_snapshot(
                    week_label, "dora_change_failure_rate", cfr_snapshot
                )
                metrics_saved += 1
                metrics_details.append(f"DORA CFR: Error ({str(e)[:50]})")

            # Calculate Mean Time To Recovery (MTTR) (MODE 2)
            try:
                from data.dora_calculator import calculate_mean_time_to_recovery
                from data.field_mapper import get_field_mappings

                field_mappings = get_field_mappings()
                affected_env_field = field_mappings.get("affected_environment")
                production_values = app_settings.get(
                    "production_environment_values", ["PROD"]
                )
                production_value = production_values[0] if production_values else "PROD"

                if not affected_env_field:
                    logger.warning("Affected Environment field not configured for MTTR")
                    mttr_snapshot = {
                        "median_hours": None,
                        "bugs_with_mttr": 0,
                        "week": week_label,
                    }
                    save_metric_snapshot(week_label, "dora_mttr", mttr_snapshot)
                    metrics_saved += 1
                    metrics_details.append("DORA MTTR: Skipped (field not configured)")
                else:
                    mttr_result = calculate_mean_time_to_recovery(
                        production_bugs,
                        field_mappings=field_mappings,
                        time_period_days=7,  # Weekly calculation
                        # use_variable_extraction=True by default (Phase 3)
                    )

                    median_hours = mttr_result.get("median_hours")
                    mean_hours = mttr_result.get("mean_hours")
                    p95_hours = mttr_result.get("p95_hours")
                    bugs_count = mttr_result.get("bugs_with_mttr", 0)

                    mttr_snapshot = {
                        "median_hours": median_hours,
                        "mean_hours": mean_hours,
                        "p95_hours": p95_hours,
                        "bugs_with_mttr": bugs_count,
                        "week": week_label,
                    }
                    save_metric_snapshot(week_label, "dora_mttr", mttr_snapshot)
                    metrics_saved += 1

                    if median_hours:
                        mttr_days = median_hours / 24
                        metrics_details.append(
                            f"DORA MTTR: {mttr_days:.1f} days median ({bugs_count} bugs)"
                        )
                        logger.info(
                            f"Saved DORA MTTR: {mttr_days:.1f} days ({bugs_count} bugs)"
                        )
                    else:
                        metrics_details.append("DORA MTTR: No Data")
                        logger.info(f"DORA MTTR: No data for week {week_label}")

            except Exception as e:
                logger.error(f"Failed to calculate DORA MTTR: {e}", exc_info=True)
                mttr_snapshot = {
                    "median_hours": None,
                    "bugs_with_mttr": 0,
                    "week": week_label,
                }
                save_metric_snapshot(week_label, "dora_mttr", mttr_snapshot)
                metrics_saved += 1
                metrics_details.append(f"DORA MTTR: Error ({str(e)[:50]})")

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
    n_weeks: int = 12, progress_callback=None, custom_weeks=None
) -> Tuple[bool, str]:
    """
    Calculate metrics for the last N weeks (including current week).

    This is useful for populating historical data and ensuring sparklines/trends
    have enough data points.

    Args:
        n_weeks: Number of weeks to calculate (default: 12) - ignored if custom_weeks provided
        progress_callback: Optional callback function(message: str) for progress updates
        custom_weeks: Optional list of (week_label, monday, sunday) tuples based on actual data range

    Returns:
        Tuple of (success: bool, summary_message: str)
    """
    from data.iso_week_bucketing import get_last_n_weeks

    try:
        # Use custom weeks if provided, otherwise generate last N weeks from today
        if custom_weeks:
            weeks = custom_weeks
            n_weeks = len(weeks)
            logger.info(
                f"Calculating metrics for {n_weeks} custom weeks (based on actual data range)"
            )
        else:
            # Get week labels for last N weeks from today
            weeks = get_last_n_weeks(n_weeks)
            logger.info(f"Calculating metrics for last {n_weeks} weeks from today")

        successful_weeks = []
        failed_weeks = []

        for week_label, monday, sunday in weeks:
            # Use ISO week format (YYYY-Wxx) consistently - DO NOT normalize/strip the 'W'
            # This ensures saved data keys match what loaders expect

            logger.info(f"Processing week {week_label} ({monday} to {sunday})")

            if progress_callback:
                progress_callback(
                    f"📅 Calculating metrics for week {week_label} ({monday} to {sunday})..."
                )

            success, message = calculate_and_save_weekly_metrics(
                week_label=week_label, progress_callback=progress_callback
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


# ============================================================================
# FORECAST CALCULATION FUNCTIONS (Feature 009)
# ============================================================================


def calculate_forecast(
    historical_values: List[float],
    weights: Optional[List[float]] = None,
    min_weeks: int = 2,
    decimal_precision: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Calculate weighted forecast from historical metric values.

    Uses weighted average of most recent weeks, with more weight on recent data.
    Handles building baseline scenarios when fewer than 4 weeks of data available.

    Args:
        historical_values: List of metric values from recent weeks (oldest to newest)
        weights: Optional custom weights (must sum to 1.0). Defaults to [0.1, 0.2, 0.3, 0.4]
        min_weeks: Minimum weeks required for forecast (default: 2)
        decimal_precision: Number of decimal places to round forecast (default: 1)

    Returns:
        Dictionary with forecast data:
        {
            "forecast_value": float,           # Forecasted metric value
            "forecast_range": None,            # Reserved for Flow Load
            "historical_values": List[float],  # Echo of input
            "weights_applied": List[float],    # Actual weights used
            "weeks_available": int,            # Number of weeks used
            "confidence": str                  # "building" or "established"
        }

        Returns None if insufficient data (< min_weeks)

    Raises:
        ValueError: If negative values provided or weights invalid
        TypeError: If historical_values is not a list of numbers

    Examples:
        >>> calculate_forecast([10, 12, 15, 18])
        {"forecast_value": 15.2, "confidence": "established", "weeks_available": 4, ...}

        >>> calculate_forecast([10, 12])  # Building baseline
        {"forecast_value": 11.0, "confidence": "building", "weeks_available": 2, ...}

        >>> calculate_forecast([10])  # Insufficient data
        None
    """
    # Input validation
    if not isinstance(historical_values, list):
        raise TypeError("historical_values must be a list")

    if not historical_values:  # Empty list
        return None

    # Type check all values
    for v in historical_values:
        if not isinstance(v, (int, float)):
            raise TypeError(f"All historical values must be numbers, got {type(v)}")

    # Check for negative values
    if any(v < 0 for v in historical_values):
        negative_val = min(historical_values)
        raise ValueError(f"Historical values cannot be negative: {negative_val}")

    # Check minimum weeks requirement
    if len(historical_values) < min_weeks:
        return None  # Insufficient data

    # Determine weights to use
    if weights is not None:
        # Validate custom weights
        if len(weights) != len(historical_values):
            raise ValueError(
                f"Weights length ({len(weights)}) must match "
                f"historical_values length ({len(historical_values)})"
            )

        # Check weights sum to 1.0 (with tolerance for floating point)
        weight_sum = sum(weights)
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0 (got {weight_sum})")

        weights_to_use = weights
    else:
        # Auto-select weights based on data availability
        if len(historical_values) == 4:
            # Standard 4-week weighted average
            weights_to_use = [0.1, 0.2, 0.3, 0.4]
        else:
            # Equal weighting for 2-3 weeks (building baseline)
            equal_weight = 1.0 / len(historical_values)
            weights_to_use = [equal_weight] * len(historical_values)

    # Calculate weighted average
    forecast_value = sum(v * w for v, w in zip(historical_values, weights_to_use))

    # Round to specified precision
    forecast_value = round(forecast_value, decimal_precision)

    # Determine confidence level
    confidence = "established" if len(historical_values) == 4 else "building"

    return {
        "forecast_value": forecast_value,
        "forecast_range": None,  # Reserved for Flow Load
        "historical_values": historical_values.copy(),  # Defensive copy
        "weights_applied": weights_to_use.copy()
        if isinstance(weights_to_use, list)
        else list(weights_to_use),
        "weeks_available": len(historical_values),
        "confidence": confidence,
    }


def calculate_trend_vs_forecast(
    current_value: float,
    forecast_value: float,
    metric_type: str,
    threshold: float = 0.10,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate trend direction and deviation percentage vs forecast.

    Determines if current performance is on track, above, or below forecast based
    on metric type (higher_better vs lower_better) and threshold.

    Args:
        current_value: Current week's metric value
        forecast_value: Forecasted benchmark value
        metric_type: "higher_better" or "lower_better"
        threshold: Neutral zone percentage (default: 0.10 = ±10%)
        previous_period_value: Optional W-1 value for Monday morning scenario

    Returns:
        Dictionary with trend analysis:
        {
            "direction": str,         # "↗" (up), "→" (neutral), "↘" (down)
            "deviation_percent": float, # Percentage deviation from forecast
            "status_text": str,       # Human-readable status message
            "color_class": str,       # CSS class: "text-success", "text-secondary", "text-danger"
            "is_good": bool           # Directional interpretation
        }

    Examples:
        >>> calculate_trend_vs_forecast(16, 13, "higher_better")
        {"direction": "↗", "deviation_percent": 23.1, "status_text": "+23% above forecast", "color_class": "text-success", ...}

        >>> calculate_trend_vs_forecast(5, 13, "higher_better")
        {"direction": "↘", "deviation_percent": -61.5, "status_text": "-62% vs forecast", "color_class": "text-danger", ...}
    """
    # Input validation
    if not isinstance(current_value, (int, float)):
        raise TypeError(f"current_value must be numeric, got {type(current_value)}")

    if not isinstance(forecast_value, (int, float)):
        raise TypeError(f"forecast_value must be numeric, got {type(forecast_value)}")

    if forecast_value < 0:
        raise ValueError(f"forecast_value must be non-negative, got {forecast_value}")

    valid_types = ["higher_better", "lower_better"]
    if metric_type not in valid_types:
        raise ValueError(
            f"metric_type must be one of {valid_types}, got '{metric_type}'"
        )

    # Special case: Zero forecast value (perfect score for lower_better metrics like CFR, MTTR)
    # For metrics like Change Failure Rate or MTTR, a forecast of 0 means "no failures expected"
    if forecast_value == 0:
        if current_value == 0:
            # Both zero - perfect performance maintained
            direction = "→"
            status_text = "On track"
            color_class = "text-success"  # Zero failures/incidents is good!
            is_good = True
            deviation_percent = 0.0
        elif metric_type == "lower_better":
            # Forecast was 0 (perfect) but current > 0 (degradation)
            # Can't calculate percentage (division by zero), so use fixed messaging
            direction = "↗"
            status_text = "Above forecast"
            color_class = "text-danger"
            is_good = False
            deviation_percent = 100.0  # Arbitrary large value to indicate increase
        else:  # higher_better
            # Forecast was 0 but current > 0 (improvement)
            direction = "↗"
            status_text = "Above forecast"
            color_class = "text-success"
            is_good = True
            deviation_percent = 100.0  # Arbitrary large value to indicate increase

        return {
            "direction": direction,
            "deviation_percent": deviation_percent,
            "status_text": status_text,
            "color_class": color_class,
            "is_good": is_good,
        }

    # Calculate deviation percentage (forecast > 0 guaranteed here)
    deviation_percent = ((current_value - forecast_value) / forecast_value) * 100

    # Determine direction and status based on metric type
    abs_deviation = abs(deviation_percent)

    # Special case: Monday morning (week just started, no completions yet)
    # Feature 009 US2 T046
    if current_value == 0 and deviation_percent == -100.0:
        direction = "↘"
        status_text = "Week starting..."
        color_class = "text-secondary"
        is_good = True  # Week starting is not "bad"
    # Check if within threshold (neutral zone)
    elif abs_deviation <= (threshold * 100):
        direction = "→"
        status_text = "On track"
        color_class = "text-success"  # GREEN: "On track" means good performance
        is_good = True
    else:
        # Outside threshold - interpret based on metric type
        is_above = deviation_percent > 0

        if metric_type == "higher_better":
            # Higher is better (Velocity, Efficiency, Deployment Frequency)
            if is_above:
                direction = "↗"
                status_text = f"+{int(round(deviation_percent))}% above forecast"
                color_class = "text-success"
                is_good = True
            else:
                direction = "↘"
                status_text = f"{int(round(deviation_percent))}% vs forecast"
                color_class = "text-danger"
                is_good = False
        else:  # lower_better
            # Lower is better (Lead Time, CFR, MTTR)
            if is_above:
                direction = "↗"
                status_text = f"+{int(round(deviation_percent))}% vs forecast"
                color_class = "text-danger"
                is_good = False
            else:
                direction = "↘"
                status_text = f"{int(round(deviation_percent))}% vs forecast"
                color_class = "text-success"
                is_good = True

    return {
        "direction": direction,
        "deviation_percent": round(deviation_percent, 1),
        "status_text": status_text,
        "color_class": color_class,
        "is_good": is_good,
    }


def calculate_flow_load_range(
    forecast_value: float, range_percent: float = 0.20, decimal_precision: int = 0
) -> Dict[str, Any]:
    """
    Calculate acceptable WIP range for Flow Load forecast.

    Flow Load represents work in progress and has bidirectional health implications:
    - Too high = bottleneck, context switching
    - Too low = under-utilization, idle capacity

    Args:
        forecast_value: Forecasted Flow Load (items in progress)
        range_percent: Range percentage above/below forecast (default: 0.20 = ±20%)
        decimal_precision: Decimal places for range bounds (default: 0 for whole items)

    Returns:
        Dictionary with range data:
        {
            "lower": float,  # Minimum healthy WIP
            "upper": float   # Maximum healthy WIP
        }

    Raises:
        ValueError: If forecast_value is zero or negative
        ValueError: If range_percent is negative or > 1.0
        TypeError: If inputs are not numeric

    Examples:
        >>> calculate_flow_load_range(15.0)
        {"lower": 12.0, "upper": 18.0}

        >>> calculate_flow_load_range(10.0, range_percent=0.30)
        {"lower": 7.0, "upper": 13.0}
    """
    # Input validation
    if not isinstance(forecast_value, (int, float)):
        raise TypeError(f"forecast_value must be numeric, got {type(forecast_value)}")

    if not isinstance(range_percent, (int, float)):
        raise TypeError(f"range_percent must be numeric, got {type(range_percent)}")

    if forecast_value <= 0:
        raise ValueError(f"forecast_value must be positive, got {forecast_value}")

    if range_percent < 0 or range_percent > 1.0:
        raise ValueError(
            f"range_percent must be between 0 and 1.0, got {range_percent}"
        )

    # Calculate range bounds
    lower_bound = forecast_value * (1 - range_percent)
    upper_bound = forecast_value * (1 + range_percent)

    # Round to specified precision
    lower_bound = round(lower_bound, decimal_precision)
    upper_bound = round(upper_bound, decimal_precision)

    return {"lower": lower_bound, "upper": upper_bound}
