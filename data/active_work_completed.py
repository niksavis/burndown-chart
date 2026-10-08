import logging
from collections import OrderedDict

from data.iso_week_bucketing import bucket_issues_by_week, get_last_n_weeks
from data.parent_filter import extract_parent_keys

logger = logging.getLogger(__name__)


def get_completed_items_by_week(
    issues: list[dict],
    n_weeks: int = 2,
    flow_end_statuses: list[str] | None = None,
    parent_field: str | None = None,
) -> dict[str, dict]:

    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]

    logger.info(
        f"[COMPLETED ITEMS] Filtering completed issues for last {n_weeks} weeks, "
        f"using flow_end_statuses={flow_end_statuses}, parent_field={parent_field}"
    )

    completed_issues = []
    sampled_debug_logs = 0
    for issue in issues:
        status = issue.get("status")
        if not status:
            status = issue.get("fields", {}).get("status", {}).get("name", "")

        resolutiondate = issue.get("resolutiondate")
        if not resolutiondate:
            resolutiondate = issue.get("resolved")
        if not resolutiondate:
            resolutiondate = issue.get("fields", {}).get("resolutiondate")

        if sampled_debug_logs < 3:
            issue_key = issue.get("key", issue.get("issue_key", "unknown"))
            logger.debug(
                f"[COMPLETED ITEMS DEBUG] Issue {issue_key}: status={status}, "
                f"resolutiondate={resolutiondate}, "
                f"in flow_end_statuses={status in flow_end_statuses}"
            )
            sampled_debug_logs += 1

        if status in flow_end_statuses and resolutiondate:
            completed_issues.append(issue)

    logger.info(
        f"[COMPLETED ITEMS] Found {len(completed_issues)} completed issues "
        f"with resolutiondate (out of {len(issues)} total)"
    )

    if not completed_issues:
        logger.warning(
            "[COMPLETED ITEMS] No completed issues found - returning empty structure"
        )
        return _create_empty_week_structure(n_weeks)

    logger.info(
        f"[COMPLETED ITEMS] Bucketing {len(completed_issues)} completed issues by week"
    )
    buckets = bucket_issues_by_week(
        issues=completed_issues, date_field="resolutiondate", n_weeks=n_weeks
    )

    for week_label, week_issues in buckets.items():
        logger.info(f"[COMPLETED ITEMS] Week {week_label}: {len(week_issues)} issues")

    weeks = get_last_n_weeks(n_weeks)

    current_week_label = weeks[-1][0] if weeks else None

    result = OrderedDict()

    for week_label, monday, sunday in reversed(weeks):
        week_issues = buckets.get(week_label, [])

        parent_keys = set()
        closed_epic_keys = set()
        display_issues = week_issues
        epic_groups = []
        if parent_field:
            all_parent_keys = extract_parent_keys(issues, parent_field)
            parent_keys = extract_parent_keys(week_issues, parent_field)
            closed_epic_keys = _get_closed_epic_keys(week_issues, all_parent_keys)
            display_issues = [
                i for i in week_issues if i.get("issue_key") not in all_parent_keys
            ]
            epic_groups = _group_issues_by_epic(display_issues, parent_field, issues)

        total_issues = len(display_issues)
        total_epics_linked = len(parent_keys)
        total_epics_closed = len(closed_epic_keys)
        total_points = sum(issue.get("points", 0.0) or 0.0 for issue in display_issues)

        display_label = _format_week_label(
            week_label=week_label,
            monday=monday,
            sunday=sunday,
            is_current=(week_label == current_week_label),
        )

        result[week_label] = {
            "display_label": display_label,
            "issues": display_issues,
            "is_current": week_label == current_week_label,
            "total_issues": total_issues,
            "total_epics_closed": total_epics_closed,
            "total_epics_linked": total_epics_linked,
            "total_points": total_points,
            "epic_groups": epic_groups,
        }

        logger.info(
            f"[COMPLETED ITEMS] {display_label}: {total_issues} issues, "
            f"{total_epics_closed} closed epics, {total_epics_linked} linked epics, "
            f"{total_points:.1f} points"
        )

    return result


def _format_week_label(
    week_label: str, monday, sunday, is_current: bool = False
) -> str:

    monday_str = f"{monday.strftime('%b')} {monday.day}"
    sunday_str = f"{sunday.strftime('%b')} {sunday.day}"

    if monday.month == sunday.month:
        date_range = f"{monday.strftime('%b')} {monday.day}-{sunday.day}"
    else:
        date_range = f"{monday_str} - {sunday_str}"

    prefix = "Current Week" if is_current else "Last Week"

    return f"{prefix} ({date_range})"


def _create_empty_week_structure(n_weeks: int = 2) -> dict[str, dict]:

    weeks = get_last_n_weeks(n_weeks)
    current_week_label = weeks[-1][0] if weeks else None

    result = OrderedDict()

    for week_label, monday, sunday in reversed(weeks):
        display_label = _format_week_label(
            week_label=week_label,
            monday=monday,
            sunday=sunday,
            is_current=(week_label == current_week_label),
        )

        result[week_label] = {
            "display_label": display_label,
            "issues": [],
            "is_current": week_label == current_week_label,
            "total_issues": 0,
            "total_epics_closed": 0,
            "total_epics_linked": 0,
            "total_points": 0.0,
            "epic_groups": [],
        }

    return result


def _get_closed_epic_keys(issues: list[dict], parent_keys: set[str]) -> set[str]:

    closed_epics = set()
    for issue in issues:
        issue_key = issue.get("issue_key", issue.get("key"))
        if issue_key and issue_key in parent_keys:
            closed_epics.add(issue_key)
    return closed_epics


def _group_issues_by_epic(
    issues: list[dict], parent_field: str, all_issues: list[dict]
) -> list[dict]:

    grouped = OrderedDict()

    for issue in issues:
        issue_type = issue.get("issue_type", "").lower()
        issue_key = issue.get("issue_key") or issue.get("key")

        if "epic" in issue_type and issue_key:
            if issue_key not in grouped:
                grouped[issue_key] = {
                    "epic_key": issue_key,
                    "epic_summary": issue.get("summary", issue_key),
                    "issues": [],
                }
            continue

        epic_key, epic_summary = _get_parent_info(issue, parent_field, all_issues)
        if not epic_key:
            epic_key = "No Parent"
            epic_summary = "Other"

        if epic_key not in grouped:
            grouped[epic_key] = {
                "epic_key": epic_key,
                "epic_summary": epic_summary,
                "issues": [],
            }

        grouped[epic_key]["issues"].append(issue)

    return list(grouped.values())


def _get_parent_info(
    issue: dict, parent_field: str, all_issues: list[dict]
) -> tuple[str | None, str | None]:

    parent = issue.get(parent_field)
    if not parent and parent_field.startswith("customfield_"):
        custom_fields = issue.get("custom_fields", {})
        parent = custom_fields.get(parent_field)

    if not parent:
        return None, None

    if isinstance(parent, dict):
        parent_key = parent.get("key")
        parent_summary = parent.get("summary") or parent.get("fields", {}).get(
            "summary"
        )
        return parent_key, parent_summary

    if isinstance(parent, str):
        parent_key = parent
        epic_issue = next(
            (
                item
                for item in all_issues
                if item.get("issue_key") == parent_key or item.get("key") == parent_key
            ),
            None,
        )
        if epic_issue:
            epic_summary = epic_issue.get("summary", parent_key)
            return parent_key, epic_summary
        return parent_key, parent_key

    return None, None
