"""Issue preparation utilities for weekly metrics calculation."""

import logging
from datetime import UTC, datetime, timedelta

from data.flow_metrics import _find_first_transition_to_statuses
from data.jira.parent_filter import filter_out_parent_types
from data.jira.query_builder import extract_parent_types_from_config
from data.metrics.helpers import get_current_iso_week
from data.metrics_snapshots import get_metric_snapshot
from data.parent_filter import filter_parent_issues
from data.project_filter import filter_development_issues

logger = logging.getLogger(__name__)


def check_metrics_cached(week_label: str) -> bool:
    """Return True if both Flow and DORA metrics already exist for this week.

    Historical weeks only - current week always recalculates as a running total.
    """

    if week_label == get_current_iso_week():
        logger.info(
            f"[Stats] Week {week_label} is current week - "
            "will recalculate (running total)"
        )
        return False

    flow_snapshot = get_metric_snapshot(week_label, "flow_velocity")
    dora_snapshot = get_metric_snapshot(week_label, "dora_deployment_frequency")

    if flow_snapshot and dora_snapshot:
        try:
            if flow_snapshot.get("timestamp") and dora_snapshot.get("timestamp"):
                logger.info(
                    f"[OK] Metrics (Flow + DORA) for week {week_label} already exist. "
                    "Skipping recalculation."
                )
                return True
        except Exception as opt_error:
            logger.debug(f"[Metrics] Optimization check failed: {opt_error}")
    elif flow_snapshot and not dora_snapshot:
        logger.warning(
            f"[!] Week {week_label} has Flow metrics but missing DORA metrics. "
            "Recalculating..."
        )

    return False


def load_and_filter_issues(
    backend,
    active_profile_id: str,
    active_query_id: str,
    app_settings: dict,
) -> tuple[list, list]:
    """Load issues from database and apply parent/project/type filters.

    Returns (all_issues, all_issues_raw) where all_issues_raw is unfiltered
    by project (needed for DORA operational task classification).

    Raises ValueError if no JIRA data is available.
    """
    all_issues_raw = backend.get_issues(active_profile_id, active_query_id)
    if not all_issues_raw:
        raise ValueError("No JIRA data available. Please update data first.")

    logger.info(f"Loaded {len(all_issues_raw)} issues from database")

    parent_field = (
        app_settings.get("field_mappings", {}).get("general", {}).get("parent_field")
    )
    if parent_field:
        all_issues_raw = filter_parent_issues(
            all_issues_raw, parent_field, log_prefix="WEEKLY CALC"
        )

    development_projects = app_settings.get("development_projects", [])
    devops_projects = app_settings.get("devops_projects", [])

    if development_projects or devops_projects:
        all_issues = filter_development_issues(
            all_issues_raw, development_projects, devops_projects
        )
        filtered_count = len(all_issues_raw) - len(all_issues)
        logger.info(
            f"Filtered to {len(all_issues)} development project issues "
            f"(excluded {filtered_count} other issues)"
        )
    else:
        all_issues = all_issues_raw
        logger.info("No project classification configured, using all issues")

    parent_types = extract_parent_types_from_config(app_settings)
    if parent_types:
        total_before_parent_filter = len(all_issues)
        all_issues = filter_out_parent_types(all_issues, parent_types)
        parent_filtered_count = total_before_parent_filter - len(all_issues)
        if parent_filtered_count > 0:
            logger.info(
                f"Excluded {parent_filtered_count} parent issue(s) from metrics "
                f"(types: {', '.join(parent_types)})"
            )

    return all_issues, all_issues_raw


def _build_changelog_map(changelog_entries: list) -> dict:
    """Convert flat changelog records to JIRA format keyed by issue_key."""  # noqa: E501
    changelog_map: dict = {}
    for entry in changelog_entries:
        issue_key = entry.get("issue_key")
        if not issue_key:
            continue
        if issue_key not in changelog_map:
            changelog_map[issue_key] = {"histories": []}
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
    return changelog_map


def load_and_merge_changelog(
    backend,
    all_issues: list,
    active_profile_id: str,
    active_query_id: str,
) -> tuple[list, bool]:
    """Load changelog from database and merge into issues in-place.

    Returns (all_issues, changelog_available) where changelog_available is
    False if no changelog data exists or merging fails.
    """
    changelog_entries = backend.get_changelog_entries(
        active_profile_id, active_query_id
    )
    changelog_available = changelog_entries is not None and len(changelog_entries) > 0

    if not changelog_available:
        logger.info(
            "Changelog not available in database. "
            "Flow Time and Efficiency metrics will be skipped."
        )
        return all_issues, False

    logger.info(f"Changelog available: {len(changelog_entries)} entries from database")

    try:
        logger.info(
            f"[DEBUG] Converting {len(changelog_entries)} "
            "changelog entries to JIRA format"
        )
        changelog_map = _build_changelog_map(changelog_entries)
        logger.info(
            f"[DEBUG] Converted changelog for {len(changelog_map)} unique issues"
        )

        if changelog_map:
            sample_changelog_keys = list(changelog_map.keys())[:3]
            logger.info(f"[DEBUG] Sample changelog keys: {sample_changelog_keys}")
        if all_issues:
            sample_issue_keys = [i.get("issue_key") for i in all_issues[:3]]
            logger.info(f"[DEBUG] Sample issue keys: {sample_issue_keys}")

        merged_count = 0
        for issue in all_issues:
            issue_key = issue.get("issue_key", "")
            if issue_key in changelog_map:
                issue["changelog"] = changelog_map[issue_key]
                merged_count += 1

        logger.info(f"Merged changelog data into {merged_count} issues")

        if merged_count > 0:
            sample_issue = next((i for i in all_issues if "changelog" in i), None)
            if sample_issue:
                sample_key = sample_issue.get("issue_key")
                sample_histories = sample_issue.get("changelog", {}).get(
                    "histories", []
                )
                logger.info(
                    f"[DEBUG] Sample issue {sample_key} has "
                    f"{len(sample_histories)} history entries"
                )
                if sample_histories:
                    first_history = sample_histories[0]
                    first_item_display = (
                        first_history.get("items", [{}])[0]
                        if first_history.get("items")
                        else "none"
                    )
                    logger.info(
                        "[DEBUG] First history: "
                        f"created={first_history.get('created')}, "
                        f"items={len(first_history.get('items', []))}, "
                        f"first_item={first_item_display}"
                    )
    except Exception as e:
        logger.warning(
            f"Failed to load changelog from database: {e}. Continuing without it."
        )
        return all_issues, False

    return all_issues, True


def compute_week_boundaries(
    week_label: str,
) -> tuple[datetime, datetime, bool, datetime]:
    """Parse week_label and return (week_start, week_end, is_current_week, cutoff).

    Raises ValueError for invalid week label formats.
    """
    week_label_clean = week_label.replace("W", "").replace("-W", "-")
    try:
        year, week_num = map(int, week_label_clean.split("-"))
        jan_4 = datetime(year, 1, 4, tzinfo=UTC)
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())
        target_week_monday = week_1_monday + timedelta(weeks=week_num - 1)
        week_start = target_week_monday.replace(tzinfo=None)
        week_end = week_start + timedelta(days=7)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid week label format: {week_label}") from e

    now = datetime.now(UTC).replace(tzinfo=None)
    is_current_week = now < week_end
    completion_cutoff = min(week_end, now) if is_current_week else week_end

    return week_start, week_end, is_current_week, completion_cutoff


def filter_completed_in_week(
    all_issues: list,
    flow_end_statuses: list[str],
    week_start: datetime,
    completion_cutoff: datetime,
) -> list:
    """Return issues with completion timestamp in [week_start, completion_cutoff)."""

    issues_completed_this_week = []

    logger.info(
        f"[DEBUG] Starting completion timestamp extraction for {len(all_issues)} issues"
    )
    logger.info(f"[DEBUG] Flow end statuses: {flow_end_statuses}")

    issues_with_changelog = [i for i in all_issues if i.get("changelog")]
    logger.info(f"[DEBUG] {len(issues_with_changelog)} issues have changelog data")

    extraction_stats = {"found": 0, "not_found": 0, "parse_errors": 0}

    for idx, issue in enumerate(all_issues):
        issue_key = issue.get("issue_key", "unknown")
        changelog = issue.get("changelog", {}).get("histories", [])

        if idx < 3 and changelog:
            logger.info(
                f"[DEBUG] Issue {issue_key} has {len(changelog)} history entries"
            )
            status_transitions = [
                h
                for h in changelog
                if any(item.get("field") == "status" for item in h.get("items", []))
            ]
            logger.info(
                f"[DEBUG] Issue {issue_key} has "
                f"{len(status_transitions)} status transitions"
            )

        if "fields" in issue and isinstance(issue.get("fields"), dict):
            timestamp_str = issue["fields"].get("resolutiondate")
        else:
            timestamp_str = issue.get("resolved") or issue.get("resolutiondate")

        if not timestamp_str:
            timestamp_str = _find_first_transition_to_statuses(
                changelog, flow_end_statuses
            )

        if not timestamp_str:
            extraction_stats["not_found"] += 1
            continue

        extraction_stats["found"] += 1

        try:
            if timestamp_str.endswith("+0000"):
                timestamp_str = timestamp_str[:-5] + "+00:00"
            elif timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"

            completion_timestamp = datetime.fromisoformat(timestamp_str)
            if completion_timestamp.tzinfo is not None:
                completion_timestamp = completion_timestamp.astimezone(UTC).replace(
                    tzinfo=None
                )
        except (ValueError, AttributeError, TypeError) as e:
            extraction_stats["parse_errors"] += 1
            logger.warning(
                f"[DEBUG] Failed to parse timestamp '{timestamp_str}' "
                f"for {issue.get('key')}: {e}"
            )
            continue

        if week_start <= completion_timestamp < completion_cutoff:
            issues_completed_this_week.append(issue)

    logger.info(
        f"[DEBUG] Extraction stats: found={extraction_stats['found']}, "
        f"not_found={extraction_stats['not_found']}, "
        f"parse_errors={extraction_stats['parse_errors']}"
    )

    return issues_completed_this_week
