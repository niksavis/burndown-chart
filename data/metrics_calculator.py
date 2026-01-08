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
    week_label: str = "",
    progress_callback=None,
    profile_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Calculate all Flow/DORA metrics for current week and save to snapshots.

    Automatically downloads changelog data if not available. Uses existing v2
    calculator functions from flow_calculator.py to calculate metrics, then
    saves them to metrics_snapshots.json for instant retrieval.

    Args:
        week_label: ISO week (e.g., "2025-44"). Defaults to current week.
        progress_callback: Optional callback function(message: str) for progress updates
        profile_id: Optional profile ID. Defaults to active profile from profiles/profiles.json.
        affected_weeks: Optional set of week labels affected by delta fetch. None = check all weeks.

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
                f"Failed to load profile configuration: {str(e)}. Please configure JIRA mappings in the UI.",
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

        # Query database for JIRA issues
        all_issues_raw = backend.get_issues(active_profile_id, active_query_id)
        if not all_issues_raw:
            return False, "No JIRA data available. Please update data first."

        # OPTIMIZATION: Check if metrics already exist and are up-to-date
        # Skip recalculation if:
        # 1. Metrics snapshot exists for this week
        # 2. This is NOT the current week (current week is a running total that changes)
        # 3. Week is not affected by delta fetch changes (if delta fetch was used)
        from data.metrics_snapshots import get_metric_snapshot

        # Determine if this is the current week
        current_week_label = get_current_iso_week()
        is_current_week_check = week_label == current_week_label

        # Only use cached metrics for historical weeks
        # CRITICAL: Check for BOTH Flow AND DORA metrics to avoid partial calculation
        if not is_current_week_check:
            flow_snapshot = get_metric_snapshot(week_label, "flow_velocity")
            dora_snapshot = get_metric_snapshot(week_label, "dora_deployment_frequency")

            # Only skip if BOTH Flow and DORA metrics exist
            if flow_snapshot and dora_snapshot:
                # Check if snapshot is still up-to-date by comparing timestamps
                # For historical weeks, if metrics exist, they're usually still valid
                # (historical data doesn't change unless full refetch)
                try:
                    flow_timestamp = flow_snapshot.get("timestamp")
                    dora_timestamp = dora_snapshot.get("timestamp")
                    if flow_timestamp and dora_timestamp:
                        # Both Flow and DORA metrics exist - skip recalculation
                        logger.info(
                            f"[OK] Metrics (Flow + DORA) for week {week_label} already exist. Skipping recalculation."
                        )
                        report_progress(
                            f"[OK] Week {week_label} already calculated - using cached metrics"
                        )
                        return (
                            True,
                            f"[OK] Metrics for week {week_label} already up-to-date",
                        )
                except Exception as opt_error:
                    # If optimization check fails, fall through to recalculation
                    logger.debug(f"[Metrics] Optimization check failed: {opt_error}")
            elif flow_snapshot and not dora_snapshot:
                # Flow metrics exist but DORA missing - recalculate all
                logger.warning(
                    f"[!] Week {week_label} has Flow metrics but missing DORA metrics. Recalculating..."
                )
        else:
            logger.info(
                f"[Stats] Week {week_label} is current week - will recalculate (running total)"
            )

        # all_issues_raw already loaded at the beginning of function
        logger.info(f"Loaded {len(all_issues_raw)} issues from database")

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

        # Check if changelog data exists in database
        # NOTE: Changelog is OPTIONAL - only needed for Flow Time and Flow Efficiency
        # All other metrics (Flow Velocity, Load, Distribution, ALL DORA metrics) work without it
        changelog_entries = backend.get_changelog_entries(
            active_profile_id, active_query_id
        )
        changelog_available = (
            changelog_entries is not None and len(changelog_entries) > 0
        )

        if not changelog_available:
            report_progress(
                "[Pending] Changelog data not found. Downloading from JIRA..."
            )

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
                        "[!] Changelog download failed. Continuing with available data..."
                    )
                    changelog_available = False
                else:
                    report_progress(f"[OK] {changelog_message}")
                    changelog_available = True
        else:
            logger.info("Changelog cache found, using existing data")

        # Load changelog data from database and merge into issues (if available)
        if changelog_available:
            report_progress("[Stats] Loading changelog data from database...")
            try:
                logger.info(
                    f"[DEBUG] Converting {len(changelog_entries)} changelog entries to JIRA format"
                )

                # Build changelog lookup map by issue_key
                # Convert flat database records to JIRA changelog format
                changelog_map = {}
                for entry in changelog_entries:
                    issue_key = entry.get("issue_key")
                    if issue_key:
                        if issue_key not in changelog_map:
                            changelog_map[issue_key] = {"histories": []}

                        # Convert database entry to JIRA changelog history format
                        # Database: {issue_key, change_date, field_name, old_value, new_value, ...}
                        # JIRA format: {created: date, items: [{field, fromString, toString}]}
                        history_entry = {
                            "created": entry.get("change_date"),
                            "items": [
                                {
                                    "field": entry.get("field_name"),
                                    "fromString": entry.get("old_value"),
                                    "toString": entry.get("new_value"),
                                }
                            ],
                        }
                        changelog_map[issue_key]["histories"].append(history_entry)

                logger.info(
                    f"[DEBUG] Converted changelog for {len(changelog_map)} unique issues"
                )

                # DEBUG: Log sample keys from both sides
                if changelog_map:
                    sample_changelog_keys = list(changelog_map.keys())[:3]
                    logger.info(
                        f"[DEBUG] Sample changelog keys: {sample_changelog_keys}"
                    )
                if all_issues:
                    sample_issue_keys = [i.get("issue_key") for i in all_issues[:3]]
                    logger.info(f"[DEBUG] Sample issue keys: {sample_issue_keys}")

                # Merge changelog into issues
                # NOTE: Database uses 'issue_key' column for both issues and changelog
                merged_count = 0
                for issue in all_issues:
                    issue_key = issue.get("issue_key", "")
                    if issue_key in changelog_map:
                        issue["changelog"] = changelog_map[issue_key]
                        merged_count += 1

                logger.info(f"Merged changelog data into {merged_count} issues")

                # DEBUG: Log sample issue with changelog to verify format
                if merged_count > 0:
                    sample_issue = next(
                        (i for i in all_issues if "changelog" in i), None
                    )
                    if sample_issue:
                        sample_key = sample_issue.get("issue_key")
                        sample_histories = sample_issue.get("changelog", {}).get(
                            "histories", []
                        )
                        logger.info(
                            f"[DEBUG] Sample issue {sample_key} has {len(sample_histories)} history entries"
                        )
                        if sample_histories:
                            first_history = sample_histories[0]
                            logger.info(
                                f"[DEBUG] First history: created={first_history.get('created')}, "
                                f"items={len(first_history.get('items', []))}, "
                                f"first_item={first_history.get('items', [{}])[0] if first_history.get('items') else 'none'}"
                            )
            except Exception as e:
                logger.warning(
                    f"Failed to load changelog from database: {e}. Continuing without it."
                )
                changelog_available = False
        else:
            logger.info(
                "Changelog not available in database. Flow Time and Efficiency metrics will be skipped."
            )

        # Get configuration
        flow_end_statuses = app_settings.get(
            "flow_end_statuses", ["Done", "Resolved", "Closed"]
        )
        # Note: active_statuses and start_statuses were removed as unused
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
            jan_4 = datetime(year, 1, 4, tzinfo=timezone.utc)  # Make timezone-aware UTC
            week_1_monday = jan_4 - timedelta(days=jan_4.weekday())
            target_week_monday = week_1_monday + timedelta(weeks=week_num - 1)
            week_start = target_week_monday.replace(
                tzinfo=None
            )  # Convert to naive UTC for comparison
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
            f"[Filter] Filtering issues completed in week {week_label}"
            + (" (running total)" if is_current_week else "")
            + "..."
        )

        # Find completed issues using simple changelog scanning
        # Uses flow_end_statuses from profile config (Done, Resolved, Closed, etc.)
        from data.flow_metrics import _find_first_transition_to_statuses

        issues_completed_this_week = []

        # DEBUG: Log extraction configuration
        logger.info(
            f"[DEBUG] Starting completion timestamp extraction for {len(all_issues)} issues"
        )
        logger.info(f"[DEBUG] Flow end statuses: {flow_end_statuses}")

        # Check first few issues for changelog data
        issues_with_changelog = [i for i in all_issues if i.get("changelog")]
        logger.info(f"[DEBUG] {len(issues_with_changelog)} issues have changelog data")

        extraction_stats = {"found": 0, "not_found": 0, "parse_errors": 0}

        for idx, issue in enumerate(all_issues):
            issue_key = issue.get("issue_key", "unknown")
            # Find completion timestamp from changelog - when issue first transitioned
            # to a completion status (Done, Resolved, Closed, etc.)
            changelog = issue.get("changelog", {}).get("histories", [])

            # DEBUG: Log first 3 issues with changelog
            if idx < 3 and changelog:
                logger.info(
                    f"[DEBUG] Issue {issue_key} has {len(changelog)} history entries"
                )
                # Check if any are status transitions
                status_transitions = [
                    h
                    for h in changelog
                    if any(item.get("field") == "status" for item in h.get("items", []))
                ]
                logger.info(
                    f"[DEBUG] Issue {issue_key} has {len(status_transitions)} status transitions"
                )

            timestamp_str = _find_first_transition_to_statuses(
                changelog, flow_end_statuses
            )

            if not timestamp_str:
                # Fallback: try resolutiondate field (handle both formats)
                if "fields" in issue and isinstance(issue.get("fields"), dict):
                    timestamp_str = issue["fields"].get("resolutiondate")
                else:
                    # Flat format: resolutiondate at top level
                    timestamp_str = issue.get("resolutiondate")

            if not timestamp_str:
                extraction_stats["not_found"] += 1
                continue

            extraction_stats["found"] += 1

            # Parse completion timestamp
            try:
                # Handle different timestamp formats from JIRA changelog
                # Format: "2025-11-24T01:54:33.997+0000" (from changelog)
                # Need to convert +0000 to +00:00 for Python's fromisoformat
                if timestamp_str.endswith("+0000"):
                    timestamp_str = timestamp_str[:-5] + "+00:00"
                elif timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"

                completion_timestamp = datetime.fromisoformat(timestamp_str)

                # Normalize to naive UTC for comparison
                if completion_timestamp.tzinfo is not None:
                    completion_timestamp = completion_timestamp.astimezone(
                        timezone.utc
                    ).replace(tzinfo=None)
            except (ValueError, AttributeError, TypeError) as e:
                extraction_stats["parse_errors"] += 1
                logger.warning(
                    f"[DEBUG] Failed to parse timestamp '{timestamp_str}' for {issue.get('key')}: {e}"
                )
                continue

            # Check if completion falls within this week's boundaries
            if week_start <= completion_timestamp < completion_cutoff:
                issues_completed_this_week.append(issue)

        # Log extraction statistics
        logger.info(
            f"[DEBUG] Extraction stats: found={extraction_stats['found']}, "
            f"not_found={extraction_stats['not_found']}, parse_errors={extraction_stats['parse_errors']}"
        )
        logger.info(
            f"Found {len(issues_completed_this_week)} issues completed in week {week_label}"
            + (" (running total)" if is_current_week else " (full week)")
        )

        # Calculate Flow Time using variable extraction (Feature 012)
        # REQUIRES CHANGELOG DATA - skip if not available
        if changelog_available:
            report_progress("[Stats] Calculating Flow Time metric...")
            from data.flow_metrics import calculate_flow_time

            flow_time_result = calculate_flow_time(
                issues_completed_this_week,  # Only issues completed this week
                time_period_days=7,  # Weekly calculation
            )
        else:
            logger.info("Skipping Flow Time (requires changelog data)")
            flow_time_result = None

        # Calculate Flow Efficiency using variable extraction (Feature 012)
        # REQUIRES CHANGELOG DATA - skip if not available
        if changelog_available:
            report_progress("[Stats] Calculating Flow Efficiency metric...")
            from data.flow_metrics import calculate_flow_efficiency

            efficiency_result = calculate_flow_efficiency(
                issues_completed_this_week,  # Only issues completed this week
                time_period_days=7,  # Weekly calculation
            )
        else:
            logger.info("Skipping Flow Efficiency (requires changelog data)")
            efficiency_result = None

        # Calculate Flow Load with historical WIP reconstruction
        # For historical weeks, we need WIP as-of that week's end
        report_progress("[Stats] Calculating Flow Load metric...")
        logger.info(
            f"[Flow Load] Starting calculation for week {week_label}: "
            f"wip_statuses={wip_statuses}, is_current_week={is_current_week}"
        )
        from data.changelog_processor import get_status_at_point_in_time

        # Calculate historical WIP (issues in active work at end of this week)
        # For current/future weeks, check WIP as of NOW instead of future date
        # Reuse the same 'now' and 'is_current_week' from completion filtering above
        issues_in_wip_at_week_end = []
        week_end_check_time = completion_cutoff  # Use same cutoff time as completions

        for issue in all_issues:
            # For current week, use current status directly (more accurate, includes issues without changelog)
            if is_current_week:
                # Handle both nested JIRA API format and flat database format
                if "fields" in issue and isinstance(issue.get("fields"), dict):
                    # Nested format: issue["fields"]["status"]["name"]
                    current_status = issue["fields"].get("status", {}).get("name", "")
                else:
                    # Flat format: issue["status"] (database schema)
                    current_status = issue.get("status", "")

                is_in_wip_now = current_status in wip_statuses
                is_completed = current_status in flow_end_statuses

                if is_in_wip_now and not is_completed:
                    issues_in_wip_at_week_end.append(issue)
                    logger.debug(
                        f"[WIP Current Week] {issue.get('key', issue.get('issue_key'))}: "
                        f"status='{current_status}', is_in_wip={is_in_wip_now}, is_completed={is_completed}"
                    )
                # Don't continue - we need to fall through to breakdown calculation

            else:
                # For historical weeks, reconstruct status at that point in time
                # This includes issues sitting in same status for long periods (e.g., "Selected", "Analysis")
                status_at_week_end = get_status_at_point_in_time(
                    issue, week_end_check_time
                )

                logger.debug(
                    f"[WIP Historical] {issue.get('key', issue.get('issue_key'))}: "
                    f"status_at_week_end='{status_at_week_end}', week_end={week_end_check_time.date()}"
                )

                # If issue existed and was in WIP status at week end, count it
                # CRITICAL: Exclude completion statuses even if they're in wip_statuses configuration
                is_completed_at_week_end = status_at_week_end in flow_end_statuses
                if (
                    status_at_week_end
                    and status_at_week_end in wip_statuses
                    and not is_completed_at_week_end
                ):
                    issues_in_wip_at_week_end.append(issue)
                    logger.debug(
                        f"[WIP Historical] ✓ {issue.get('key', issue.get('issue_key'))}: "
                        f"IN WIP at week end (status='{status_at_week_end}')"
                    )

        # Calculate breakdowns for WIP
        by_status = {}
        by_issue_type = {}
        for issue in issues_in_wip_at_week_end:
            # For current week, use current status directly
            if is_current_week:
                # Handle both nested JIRA API format and flat database format
                if "fields" in issue and isinstance(issue.get("fields"), dict):
                    issue_wip_status = issue["fields"].get("status", {}).get("name", "")
                else:
                    issue_wip_status = issue.get("status", "")
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

            # Get issue type (handle both nested and flat formats)
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                issue_type = issue["fields"].get("issuetype", {}).get("name", "Unknown")
            else:
                issue_type = issue.get("issue_type", issue.get("issuetype", "Unknown"))

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
        report_progress("[Stats] Calculating Flow Velocity...")
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
            if flow_time_error is None:  # Success (new format)
                # New flow_metrics format: {"value": days, "unit": "days", "error_state": None}
                avg_days = flow_time_result.get("value", 0)
                # Note: New format doesn't track completed count separately, estimate from issues list
                completed = len(issues_completed_this_week)

                flow_time_snapshot = {
                    "median_days": avg_days,  # Use avg as median (new format only has average)
                    "avg_days": avg_days,
                    "p85_days": 0,  # Not calculated in new format
                    "completed_count": completed,
                }
                save_metric_snapshot(week_label, "flow_time", flow_time_snapshot)
                metrics_saved += 1
                metrics_details.append(
                    f"Flow Time: {flow_time_snapshot['avg_days']:.1f} days avg ({completed} issues)"
                )
                logger.info(
                    f"Saved Flow Time: avg {flow_time_snapshot['avg_days']:.1f} days, {completed} issues"
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

        # Save Flow Efficiency (always save, even with 0 completed issues for UI consistency)
        # Skip if changelog not available (efficiency_result will be None)
        if efficiency_result is not None:
            efficiency_error = efficiency_result.get("error_state")
            if efficiency_error is None:  # Success (new format)
                # New flow_metrics format: {"value": percentage, "unit": "%", "error_state": None}
                efficiency_pct = efficiency_result.get("value", 0)
                # Note: New format doesn't track completed count separately, estimate from issues list
                completed = len(issues_completed_this_week)

                efficiency_snapshot = {
                    "overall_pct": efficiency_pct,  # Use value as overall percentage
                    "median_pct": efficiency_pct,  # Use same value for median (new format only has average)
                    "avg_active_days": 0,  # Not directly available in new format
                    "avg_waiting_days": 0,  # Not directly available in new format
                    "completed_count": completed,
                }
                save_metric_snapshot(week_label, "flow_efficiency", efficiency_snapshot)
                metrics_saved += 1
                metrics_details.append(
                    f"Flow Efficiency: {efficiency_pct:.1f}% ({completed} issues)"
                )
                logger.info(
                    f"Saved Flow Efficiency: {efficiency_pct:.1f}%, {completed} issues"
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
            metrics_details.append(f"Flow Load: [!] {error_msg}")
            logger.warning(f"Flow Load calculation failed: {load_error} - {error_msg}")

        # Calculate work distribution using user-configured flow_type_mappings
        report_progress("[Stats] Categorizing work distribution...")
        from configuration.metrics_config import get_metrics_config

        logger.info(
            f"[Work Distribution] Starting calculation for week {week_label}: "
            f"{len(issues_completed_this_week)} completed issues"
        )

        # Get field mappings from configuration (nested under 'flow')
        field_mappings = app_settings.get("field_mappings", {})
        flow_mappings = field_mappings.get("flow", {})
        flow_type_field = flow_mappings.get("flow_item_type", "issuetype")
        effort_category_field = flow_mappings.get("effort_category")

        logger.info(
            f"[Work Distribution] Configuration: flow_type_field='{flow_type_field}', "
            f"effort_category_field='{effort_category_field}'"
        )

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
            # Handle both nested JIRA API format and flat database format
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                fields = issue.get("fields", {})
            else:
                # Flat format: fields are at top level
                fields = issue

            # Extract issue type
            issue_type_value = fields.get(flow_type_field)

            # Fallback: database uses 'issue_type' (with underscore)
            if not issue_type_value and flow_type_field == "issuetype":
                issue_type_value = fields.get("issue_type")

            if isinstance(issue_type_value, dict):
                issue_type = issue_type_value.get("name") or issue_type_value.get(
                    "value", ""
                )
            else:
                issue_type = str(issue_type_value) if issue_type_value else ""

            logger.info(
                f"[Work Distribution] {issue.get('key', issue.get('issue_key'))}: "
                f"type_field={flow_type_field}, raw_value={repr(issue_type_value)}, issue_type='{issue_type}'"
            )

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
            flow_type = config.get_flow_type_for_issue(issue_type, effort_category)

            logger.info(
                f"[Work Distribution] {issue.get('key', issue.get('issue_key'))}: "
                f"issue_type='{issue_type}' -> flow_type='{flow_type}'"
            )

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
                # Unknown types - don't count (or could default to feature)
                logger.warning(
                    f"[Work Distribution] Issue {issue.get('key', issue.get('issue_key'))} has unknown flow type: '{flow_type}' (from issue_type='{issue_type}')"
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
            "[Stats] Calculating DORA metrics (Lead Time, Deployment Frequency)..."
        )

        from data.dora_metrics import calculate_lead_time_for_changes

        # Helper: Count deployments per week (filters by releaseDate within week)
        def count_deployments_for_week(
            issues,
            flow_end_statuses,
            week_label,
            week_start,
            week_end,
            valid_fix_versions=None,
        ):
            """Count deployment issues with releaseDate in specified week.

            Filters issues by:
            1. Status is in flow_end_statuses (Done, Resolved, etc.)
            2. fixVersion.releaseDate falls within week_start to week_end
            3. fixVersion.name is in valid_fix_versions (if provided)

            Args:
                issues: List of Operational Task issues
                flow_end_statuses: List of completed status names
                week_label: Week identifier (e.g., "2025-W49")
                week_start: Start of week (datetime)
                week_end: End of week (datetime)
                valid_fix_versions: Set of fixVersion names from development projects.
                    If provided, only count Operational Tasks with matching fixVersions.

            Returns deployment count and unique release names.
            """
            deployment_count = 0
            releases = set()

            for issue in issues:
                # Handle both nested (JIRA API) and flat (database) formats
                if "fields" in issue and isinstance(issue.get("fields"), dict):
                    status = issue.get("fields", {}).get("status", {}).get("name", "")
                    fix_versions = issue.get("fields", {}).get("fixVersions", [])
                else:
                    # Flat format: status and fixVersions at root level
                    status = issue.get("status", "")
                    fix_versions = issue.get("fixVersions", [])

                if status not in flow_end_statuses:
                    continue
                for fv in fix_versions:
                    release_date_str = fv.get("releaseDate")
                    release_name = fv.get("name")
                    if not release_date_str or not release_name:
                        continue

                    # Filter: Only count if fixVersion exists in development projects
                    if valid_fix_versions and release_name not in valid_fix_versions:
                        continue

                    try:
                        # Parse releaseDate and check if in week range
                        release_date = datetime.fromisoformat(release_date_str)
                        if week_start <= release_date < week_end:
                            deployment_count += 1
                            releases.add(release_name)
                            break  # Count issue once per release week
                    except (ValueError, TypeError):
                        continue

            return {
                week_label: {
                    "deployments": deployment_count,
                    "releases": len(releases),
                    "release_names": sorted(list(releases)),
                }
            }

        # Helper: Filter issues by deployment date (fixVersions.releaseDate) within week
        def filter_issues_by_deployment_week(issues, week_start, week_end):
            """Filter issues where fixVersions.releaseDate falls within the week.

            This ensures Lead Time and other metrics only include issues
            deployed during the specific week being calculated.
            """
            filtered = []
            for issue in issues:
                # Handle both nested (JIRA API) and flat (database) formats
                if "fields" in issue and isinstance(issue.get("fields"), dict):
                    fix_versions = issue.get("fields", {}).get("fixVersions", [])
                else:
                    # Flat format: fixVersions at root level
                    fix_versions = issue.get("fixVersions", [])

                for fv in fix_versions:
                    release_date_str = fv.get("releaseDate")
                    if not release_date_str:
                        continue
                    try:
                        release_date = datetime.fromisoformat(release_date_str)
                        if week_start <= release_date < week_end:
                            filtered.append(issue)
                            break  # Include once even if multiple fixVersions
                    except (ValueError, TypeError):
                        continue
            return filtered

        # Helper: Filter bugs by resolution date within week
        def filter_bugs_by_resolution_week(bugs, week_start, week_end):
            """Filter bugs where resolutiondate falls within the week.

            This ensures MTTR only includes bugs resolved during the specific week.
            """
            filtered = []
            for bug in bugs:
                # Handle both nested (JIRA API) and flat (database) formats
                if "fields" in bug and isinstance(bug.get("fields"), dict):
                    resolution_str = bug.get("fields", {}).get("resolutiondate")
                else:
                    # Flat format: resolutiondate at root level
                    resolution_str = bug.get("resolutiondate")

                if not resolution_str:
                    continue
                try:
                    resolution_date = datetime.fromisoformat(
                        resolution_str.replace("Z", "+00:00")
                    )
                    # Remove timezone for comparison if week_start is naive
                    if resolution_date.tzinfo and week_start.tzinfo is None:
                        resolution_date = resolution_date.replace(tzinfo=None)
                    if week_start <= resolution_date < week_end:
                        filtered.append(bug)
                except (ValueError, TypeError):
                    continue
            return filtered

        # ========================================================================
        # UNIFIED DORA METRICS: Classify issues for DORA calculations
        # ========================================================================

        # Get configuration from app_settings
        devops_task_types = app_settings.get("devops_task_types", [])
        bug_types = app_settings.get("bug_types", ["Bug"])
        production_env_values = app_settings.get("production_environment_values", [])
        flow_end_statuses = app_settings.get(
            "flow_end_statuses", ["Done", "Resolved", "Closed"]
        )

        # Get field mappings for DORA metrics
        field_mappings = app_settings.get("field_mappings", {})
        dora_mappings = field_mappings.get("dora", {})

        # ========================================================================
        # OPERATIONAL TASKS: Get from all_issues_raw (includes DevOps projects)
        # These are used for Deployment Frequency calculation
        # Criteria: issue_type in devops_task_types (e.g., "Operational Task")
        # ========================================================================
        operational_tasks = []
        for issue in all_issues_raw:
            # Handle both nested (JIRA API) and flat (database) formats
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                fields = issue["fields"]
                issue_type = fields.get("issuetype", {}).get("name", "")
            else:
                # Flat format: issue_type at root level
                issue_type = issue.get("issue_type", "")

            if issue_type in devops_task_types:
                operational_tasks.append(issue)

        logger.info(
            f"[DORA] Found {len(operational_tasks)} Operational Tasks "
            f"(types: {devops_task_types}) from {len(all_issues_raw)} total issues"
        )

        # ========================================================================
        # DEVELOPMENT ISSUES & PRODUCTION BUGS: From filtered all_issues
        # (excludes DevOps projects, used for Lead Time and MTTR)
        # Uses is_production_environment() with =Value syntax support
        # ========================================================================
        from data.dora_metrics import is_production_environment

        development_issues = []
        production_bugs = []

        # Get affected_environment mapping (may include =Value filter)
        affected_environment_mapping = dora_mappings.get("affected_environment", "")

        for issue in all_issues:
            # Handle both nested (JIRA API) and flat (database) formats
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                fields = issue["fields"]
                issue_type = fields.get("issuetype", {}).get("name", "")
            else:
                # Flat format: issue_type at root level
                fields = issue
                issue_type = issue.get("issue_type", "")

            # Production bugs: issue type matches bug_types
            if issue_type in bug_types:
                # Check production environment using =Value syntax or fallback
                if is_production_environment(
                    issue,
                    affected_environment_mapping,
                    fallback_values=production_env_values,
                ):
                    production_bugs.append(issue)
                else:
                    development_issues.append(issue)
            else:
                # All non-bug issues are development work
                development_issues.append(issue)

        # Log filter info
        filter_info = affected_environment_mapping or str(production_env_values)
        logger.info(
            f"[DORA] Classification (env_filter={filter_info}): "
            f"{len(development_issues)} development issues, {len(production_bugs)} production bugs"
        )
        logger.info(f"Week {week_label} boundaries: {week_start} to {week_end}")

        # ========================================================================
        # COLLECT VALID FIX VERSIONS FROM DEVELOPMENT PROJECTS
        # Only Operational Tasks with fixVersions that match development project
        # fixVersions should be counted as deployments
        # ========================================================================
        development_fix_versions = set()
        for issue in all_issues:  # all_issues = development project issues only
            # Handle both nested (JIRA API) and flat (database) formats
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                fix_versions = issue.get("fields", {}).get("fixVersions", [])
            else:
                # Flat format: fixVersions at root level
                fix_versions = issue.get("fixVersions", [])

            for fv in fix_versions:
                fv_name = fv.get("name")
                if fv_name:
                    development_fix_versions.add(fv_name)

        logger.info(
            f"[DORA] Found {len(development_fix_versions)} unique fixVersions "
            f"in development projects (used to filter Operational Tasks)"
        )
        if development_fix_versions:
            # Log a sample of the versions for debugging
            sample = sorted(list(development_fix_versions))[:5]
            logger.info(f"[DORA] Sample development fixVersions: {sample}")

        # ========================================================================
        # BUILD SHARED FIXVERSION RELEASE MAP (DRY - reused by all DORA metrics)
        # Maps fixVersion name → releaseDate from Operational Tasks
        # This is the shared "deployment date" lookup for Lead Time, MTTR, etc.
        # ========================================================================
        from data.fixversion_matcher import (
            build_fixversion_release_map,
            filter_issues_deployed_in_week,
        )

        fixversion_release_map = build_fixversion_release_map(
            operational_tasks,
            valid_fix_versions=development_fix_versions,
            flow_end_statuses=flow_end_statuses,
        )
        logger.info(
            f"[DORA] Built fixVersion release map: {len(fixversion_release_map)} versions "
            f"(filtered to development project fixVersions)"
        )

        # ========================================================================
        # Calculate DORA Metrics using field-based filtering
        # ========================================================================

        # Calculate Lead Time for Changes
        # Uses development issues + shared fixversion_release_map for deployment dates
        try:
            # Filter development issues to those deployed in this specific week
            # (using shared fixversion_release_map, not each issue's own fixVersions)
            week_dev_issues = filter_issues_deployed_in_week(
                development_issues, fixversion_release_map, week_start, week_end
            )
            logger.info(
                f"Week {week_label}: {len(week_dev_issues)} development issues deployed "
                f"(from {len(development_issues)} total)"
            )

            lead_time_result = calculate_lead_time_for_changes(
                week_dev_issues,
                time_period_days=7,
                fixversion_release_map=fixversion_release_map,
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
                save_metric_snapshot(week_label, "dora_lead_time", lead_time_snapshot)
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
                save_metric_snapshot(week_label, "dora_lead_time", lead_time_snapshot)
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
            flow_end_statuses = app_settings.get(
                "flow_end_statuses", ["Done", "Resolved", "Closed"]
            )

            weekly_deployments = count_deployments_for_week(
                operational_tasks,
                flow_end_statuses,
                week_label,
                week_start,
                week_end,
                valid_fix_versions=development_fix_versions,
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
            metrics_details.append(f"DORA Deployment Frequency: Error ({str(e)[:50]})")

        # Calculate Change Failure Rate
        try:
            from data.dora_metrics import calculate_change_failure_rate

            # Filter operational tasks to only those with fixVersions deployed in this week
            # (same approach as Lead Time and Deployment Frequency)
            week_operational_tasks = filter_issues_deployed_in_week(
                operational_tasks, fixversion_release_map, week_start, week_end
            )
            logger.info(
                f"Week {week_label}: {len(week_operational_tasks)} operational tasks deployed "
                f"(from {len(operational_tasks)} total) for CFR calculation"
            )

            # CFR calculation filters Operational Tasks by matching fixVersions from dev projects
            cfr_result = calculate_change_failure_rate(
                week_operational_tasks,  # NOW FILTERED BY WEEK
                production_bugs,  # Also pass bugs for incident correlation
                time_period_days=7,  # Weekly calculation
                valid_fix_versions=development_fix_versions,  # Filter by dev project fixVersions
            )

            cfr_percent = cfr_result.get("change_failure_rate_percent", 0)
            total_deps = cfr_result.get("total_deployments", 0)
            failed_deps = cfr_result.get("failed_deployments", 0)
            total_releases = cfr_result.get("total_releases", 0)
            failed_releases = cfr_result.get("failed_releases", 0)
            release_names = cfr_result.get("release_names", [])
            failed_release_names = cfr_result.get("failed_release_names", [])
            release_failure_rate = cfr_result.get("release_failure_rate_percent", 0)

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
            save_metric_snapshot(week_label, "dora_change_failure_rate", cfr_snapshot)
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
            save_metric_snapshot(week_label, "dora_change_failure_rate", cfr_snapshot)
            metrics_saved += 1
            metrics_details.append(f"DORA CFR: Error ({str(e)[:50]})")

        # Calculate Mean Time To Recovery (MTTR)
        # MTTR can use either:
        # - "resolutiondate": Bug created → Bug resolved (team fix time)
        # - "fixVersions": Bug created → Bug deployed (true production MTTR)
        try:
            from data.dora_metrics import calculate_mean_time_to_recovery

            # Check which end state is configured
            incident_resolved_field = dora_mappings.get(
                "incident_resolved_at", "resolutiondate"
            )
            use_deployment_date = incident_resolved_field.lower() == "fixversions"

            if use_deployment_date:
                # Filter bugs to those deployed in this specific week
                # Uses same fixversion_release_map as Lead Time (DRY)
                week_bugs = filter_issues_deployed_in_week(
                    production_bugs, fixversion_release_map, week_start, week_end
                )
                logger.info(
                    f"Week {week_label}: {len(week_bugs)} bugs deployed for MTTR "
                    f"(from {len(production_bugs)} total, using fixVersion deployment)"
                )
            else:
                # Filter bugs to those resolved in this specific week (legacy behavior)
                week_bugs = filter_bugs_by_resolution_week(
                    production_bugs, week_start, week_end
                )
                logger.info(
                    f"Week {week_label}: Filtered {len(week_bugs)} bugs for MTTR "
                    f"(from {len(production_bugs)} total, using resolutiondate)"
                )

            # MTTR calculation - pass fixversion_release_map for deployment date lookup
            mttr_result = calculate_mean_time_to_recovery(
                week_bugs,
                time_period_days=7,  # Weekly calculation
                fixversion_release_map=fixversion_release_map,
            )

            # The function returns 'value' (in hours or days) and 'unit'
            # Convert to hours for consistent storage
            mttr_value = mttr_result.get("value")
            mttr_unit = mttr_result.get("unit", "hours")
            bugs_count = mttr_result.get("incident_count", 0)

            # Convert to hours for storage consistency
            if mttr_value is not None:
                if mttr_unit == "days":
                    mttr_hours = mttr_value * 24
                else:
                    mttr_hours = mttr_value
            else:
                mttr_hours = None

            mttr_snapshot = {
                "median_hours": mttr_hours,  # Store as hours for compatibility
                "mean_hours": mttr_hours,
                "value": mttr_value,
                "unit": mttr_unit,
                "bugs_with_mttr": bugs_count,
                "performance_tier": mttr_result.get("performance_tier"),
                "week": week_label,
            }
            save_metric_snapshot(week_label, "dora_mttr", mttr_snapshot)
            metrics_saved += 1

            if mttr_value is not None:
                metrics_details.append(
                    f"DORA MTTR: {mttr_value:.1f} {mttr_unit} ({bugs_count} incidents)"
                )
                logger.info(
                    f"Saved DORA MTTR: {mttr_value:.1f} {mttr_unit} ({bugs_count} incidents)"
                )
            else:
                error_msg = mttr_result.get("error_message", "No data")
                metrics_details.append(f"DORA MTTR: {error_msg}")
                logger.info(f"DORA MTTR: {error_msg} for week {week_label}")

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
    from data.metrics_snapshots import batch_write_mode

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
        skipped_weeks = []

        # Note: Legacy delta optimization removed - database timestamps provide sufficient tracking

        # Use batch write mode to accumulate all changes and write once
        # Import TaskProgress once before loop for progress updates
        from data.task_progress import TaskProgress

        with batch_write_mode():
            week_number = 0
            for week_label, monday, sunday in weeks:
                # Use ISO week format (YYYY-Wxx) consistently - DO NOT normalize/strip the 'W'
                # This ensures saved data keys match what loaders expect

                logger.info(f"Processing week {week_label} ({monday} to {sunday})")

                # Check for cancellation request BEFORE processing
                week_number += 1
                try:
                    # Check if task was cancelled
                    is_cancelled = TaskProgress.is_task_cancelled()
                    logger.debug(
                        f"[Metrics] Cancellation check: is_cancelled={is_cancelled}"
                    )
                    if is_cancelled:
                        logger.info(
                            f"[Metrics] Calculation cancelled by user at week {week_number}/{n_weeks}"
                        )
                        TaskProgress.fail_task(
                            "update_data", "Operation cancelled by user"
                        )
                        return (
                            False,
                            f"Cancelled after calculating {week_number - 1}/{n_weeks} weeks",
                        )
                except Exception as e:
                    logger.warning(
                        f"[Progress] Failed to check cancellation for week {week_label}: {e}"
                    )

                if progress_callback:
                    progress_callback(
                        f"[Date] Calculating metrics for week {week_label} ({monday} to {sunday})..."
                    )

                success, message = calculate_and_save_weekly_metrics(
                    week_label=week_label,
                    progress_callback=progress_callback,
                )

                # Report calculation progress AFTER week is calculated (not before)
                # This ensures 100% means "all work done", not "starting last week"
                try:
                    TaskProgress.update_progress(
                        "update_data",
                        "calculate",
                        current=week_number,
                        total=n_weeks,
                        message=f"Week {week_label}",
                    )
                    # Log every 10th week to avoid log spam
                    if week_number % 10 == 0 or week_number == n_weeks:
                        logger.info(
                            f"[Progress] Calculation progress: {week_number}/{n_weeks} weeks ({week_number / n_weeks * 100:.0f}%)"
                        )
                except Exception as e:
                    logger.warning(
                        f"[Progress] Failed to update progress for week {week_label}: {e}"
                    )

                # Yield control to allow other Dash callbacks (like progress bar polling) to execute
                # This prevents the long-running calculation from blocking the UI
                import time

                time.sleep(0.001)  # 1ms sleep to yield to event loop

                if success:
                    # Check if it was actually calculated or skipped
                    if "not affected" in message:
                        skipped_weeks.append(week_label)
                    else:
                        successful_weeks.append(week_label)
                else:
                    failed_weeks.append((week_label, message))

        # Summary
        if skipped_weeks:
            summary = f"[Delta] Calculated {len(successful_weeks)} weeks, skipped {len(skipped_weeks)} unaffected weeks"
            if failed_weeks:
                summary += f", {len(failed_weeks)} failures"
            logger.info(summary)
        elif failed_weeks:
            summary = f"[!] Calculated metrics for {len(successful_weeks)}/{n_weeks} weeks. Failures:\n"
            for week, msg in failed_weeks[:3]:  # Show first 3 failures
                summary += f"  {week}: {msg[:100]}...\n"
            logger.info(summary)
        else:
            if successful_weeks:
                summary = f"[OK] Successfully calculated metrics for all {n_weeks} weeks ({successful_weeks[0]} to {successful_weeks[-1]})"
            else:
                summary = (
                    f"[OK] All {n_weeks} weeks up-to-date (no recalculation needed)"
                )
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
