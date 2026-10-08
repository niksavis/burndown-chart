import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from data.types import SprintSnapshot

logger = logging.getLogger(__name__)


def calculate_daily_sprint_snapshots(
    sprint_data: dict,
    issues: list[dict],
    changelog_entries: list[dict],
    sprint_start_date: str,
    sprint_end_date: str,
    flow_end_statuses: list[str] | None = None,
) -> list[SprintSnapshot]:

    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed"]

    try:
        start_dt = datetime.fromisoformat(sprint_start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(sprint_end_date.replace("Z", "+00:00"))

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=UTC)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=UTC)
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse sprint dates: {e}")
        return []

    current_issues = sprint_data.get("current_issues", [])
    if not current_issues:
        logger.warning("No issues in sprint")
        return []

    issue_map = {}
    for issue in issues:
        issue_key = issue.get("key") or issue.get("issue_key")
        if issue_key and issue_key in current_issues:
            issue_map[issue_key] = issue

    changelog_by_issue = defaultdict(list)
    for entry in changelog_entries:
        issue_key = entry.get("issue_key")
        if issue_key in current_issues:
            changelog_by_issue[issue_key].append(entry)

    added_issues = sprint_data.get("added_issues", [])
    removed_issues = sprint_data.get("removed_issues", [])

    scope_timeline = []
    for item in added_issues:
        try:
            ts = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            scope_timeline.append(
                {"timestamp": ts, "issue_key": item["issue_key"], "action": "add"}
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse added issue timestamp: {e}")

    for item in removed_issues:
        try:
            ts = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            scope_timeline.append(
                {"timestamp": ts, "issue_key": item["issue_key"], "action": "remove"}
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse removed issue timestamp: {e}")

    scope_timeline.sort(key=lambda x: x["timestamp"])

    snapshots = []
    current_date = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    issues_in_scope = set(current_issues)

    for change in scope_timeline:
        if change["timestamp"] < start_dt:
            if change["action"] == "add":
                issues_in_scope.add(change["issue_key"])
            elif change["action"] == "remove":
                issues_in_scope.discard(change["issue_key"])

    scope_change_idx = 0

    while current_date <= end_date:
        day_end = current_date + timedelta(days=1)
        while scope_change_idx < len(scope_timeline):
            change = scope_timeline[scope_change_idx]
            if change["timestamp"] >= day_end:
                break

            if change["action"] == "add":
                issues_in_scope.add(change["issue_key"])
            elif change["action"] == "remove":
                issues_in_scope.discard(change["issue_key"])

            scope_change_idx += 1

        completed_points = 0
        completed_count = 0
        total_points = 0
        total_count = 0
        status_breakdown = defaultdict(lambda: {"count": 0, "points": 0})

        for issue_key in issues_in_scope:
            issue = issue_map.get(issue_key)
            if not issue:
                continue

            issue_changelog = changelog_by_issue.get(issue_key, [])
            status_at_time = get_status_at_timestamp(
                issue, current_date, issue_changelog
            )

            if not status_at_time:
                status_at_time = issue.get("status", "Unknown")

            points = issue.get("points", 0) or 0

            if total_count == 0:
                logger.info(f"Sample issue structure - Keys: {list(issue.keys())[:15]}")
                logger.info(
                    "Issue has 'points' column: "
                    f"{'points' in issue}, value: {issue.get('points')}"
                )
                if "custom_fields" in issue:
                    cf = issue.get("custom_fields", {})
                    sample_cf_keys = (
                        list(cf.keys())[:5] if isinstance(cf, dict) else "not a dict"
                    )
                    logger.info(f"Sample custom_fields keys: {sample_cf_keys}")

            total_count += 1
            total_points += points

            status_breakdown[status_at_time]["count"] += 1
            status_breakdown[status_at_time]["points"] += points

            if status_at_time in flow_end_statuses:
                completed_count += 1
                completed_points += points

        snapshot = {
            "date": current_date.date().isoformat(),
            "completed_points": completed_points,
            "total_scope": total_points,
            "status_breakdown": dict(status_breakdown),
            "completed_count": completed_count,
            "total_count": total_count,
        }
        snapshots.append(snapshot)

        current_date += timedelta(days=1)

    logger.info(f"Generated {len(snapshots)} daily snapshots for sprint")
    return snapshots


def get_status_at_timestamp(
    issue: dict, timestamp: datetime, changelog: list[dict]
) -> str | None:

    if not changelog:
        return issue.get("status")

    sorted_changelog = sorted(
        changelog,
        key=lambda x: datetime.fromisoformat(
            x.get("change_date", "1970-01-01").replace("Z", "+00:00")
        ),
    )

    last_status = None

    for entry in sorted_changelog:
        try:
            entry_time = datetime.fromisoformat(
                entry.get("change_date", "").replace("Z", "+00:00")
            )
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=UTC)

            if entry_time > timestamp:
                break

            to_status = entry.get("new_value")
            if to_status:
                last_status = to_status
        except ValueError, AttributeError:
            continue

    if last_status:
        return last_status

    if sorted_changelog:
        first_from = sorted_changelog[0].get("old_value")
        if first_from:
            return first_from

    return issue.get("status")


def filter_sprint_data(
    sprint_data: dict, issue_type_filter: str = "all", status_filter: str = "all"
) -> dict:

    if issue_type_filter == "all" and status_filter == "all":
        return sprint_data

    filtered_data: dict = {
        "name": sprint_data.get("name"),
        "current_issues": [],
        "added_issues": sprint_data.get("added_issues", []),
        "removed_issues": sprint_data.get("removed_issues", []),
        "issue_states": {},
    }

    issue_states = sprint_data.get("issue_states", {})
    for issue_key, state in issue_states.items():
        if issue_type_filter != "all" and state.get("issue_type") != issue_type_filter:
            continue
        if status_filter != "all" and state.get("status") != status_filter:
            continue
        filtered_data["issue_states"][issue_key] = state
        filtered_data["current_issues"].append(issue_key)

    return filtered_data
