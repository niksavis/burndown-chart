import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from data.active_work_sorting import get_epic_sort_key
from data.parent_filter import filter_parent_issues

logger = logging.getLogger(__name__)


def filter_active_issues(
    issues: list[dict],
    data_points_count: int = 30,
    flow_end_statuses: list[str] | None = None,
    flow_wip_statuses: list[str] | None = None,
) -> list[dict]:

    if not flow_end_statuses:
        flow_end_statuses = ["Done", "Closed", "Resolved"]
    if not flow_wip_statuses:
        flow_wip_statuses = ["In Progress", "In Review", "Testing", "To Do", "Backlog"]

    now = datetime.now(UTC)
    cutoff_date = now - timedelta(weeks=data_points_count)

    logger.info(
        "Filtering issues with activity since "
        f"{cutoff_date.date()} ({data_points_count} weeks)"
    )

    filtered_issues = []

    for issue in issues:
        created_str = issue.get("created")
        updated_str = issue.get("updated")

        try:
            created_dt = None
            if created_str:
                if created_str.endswith("Z"):
                    created_str = created_str[:-1] + "+00:00"
                created_dt = datetime.fromisoformat(created_str)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=UTC)

            updated_dt = None
            if updated_str:
                if updated_str.endswith("Z"):
                    updated_str = updated_str[:-1] + "+00:00"
                updated_dt = datetime.fromisoformat(updated_str)
                if updated_dt.tzinfo is None:
                    updated_dt = updated_dt.replace(tzinfo=UTC)

            if (created_dt and created_dt >= cutoff_date) or (
                updated_dt and updated_dt >= cutoff_date
            ):
                filtered_issues.append(issue)

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse date for {issue.get('issue_key')}: {e}")
            continue

    logger.info(
        f"Filtered to {len(filtered_issues)} issues within {data_points_count} weeks"
    )

    return filtered_issues


def get_active_work_data(
    issues: list[dict],
    backend=None,
    profile_id: str | None = None,
    query_id: str | None = None,
    data_points_count: int = 30,
    parent_field: str = "parent",
    flow_end_statuses: list[str] | None = None,
    flow_wip_statuses: list[str] | None = None,
    parent_issue_types: list[str] | None = None,
    filter_parents: bool = True,
) -> dict:

    logger.info(
        f"[ACTIVE WORK MGR] Building active work data from {len(issues)} issues"
    )
    logger.info(
        "[ACTIVE WORK MGR] "
        f"data_points_count={data_points_count}, parent_field={parent_field}"
    )

    filtered_all_issues = filter_active_issues(
        issues, data_points_count, flow_end_statuses, flow_wip_statuses
    )

    all_issues_unfiltered = filtered_all_issues

    filtered_issues = filtered_all_issues
    if filter_parents and parent_field:
        filtered_issues = filter_parent_issues(
            filtered_all_issues, parent_field, log_prefix="ACTIVE WORK MGR"
        )

    logger.info(
        "[ACTIVE WORK MGR] After filtering: "
        f"{len(filtered_issues)} issues within {data_points_count} weeks"
    )

    if not filtered_issues:
        logger.warning("[ACTIVE WORK MGR] No issues found after filtering")
        return {"timeline": []}

    issues_with_health = [
        _add_health_indicators(
            issue, backend, profile_id, query_id, flow_end_statuses, flow_wip_statuses
        )
        for issue in filtered_issues
    ]

    timeline = _build_epic_timeline(
        issues_with_health,
        backend,
        profile_id,
        query_id,
        parent_field,
        flow_end_statuses,
        flow_wip_statuses,
        all_issues_unfiltered,
        parent_issue_types,
    )

    return {"timeline": timeline}


def calculate_epic_progress(
    child_issues: list[dict],
    flow_end_statuses: list[str] | None = None,
    flow_wip_statuses: list[str] | None = None,
) -> dict:

    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]

    if flow_wip_statuses is None:
        flow_wip_statuses = [
            "In Progress",
            "In Development",
            "In Review",
            "Testing",
            "In Testing",
            "QA",
        ]

    total_issues = len(child_issues)
    completed_issues = 0
    in_progress_issues = 0
    todo_issues = 0

    total_points = 0.0
    completed_points = 0.0

    by_status = defaultdict(lambda: {"count": 0, "points": 0.0})

    for issue in child_issues:
        status = issue.get("status", "Unknown")
        points = issue.get("points", 0.0) or 0.0

        if status in flow_end_statuses:
            completed_issues += 1
            completed_points += points
        elif status in flow_wip_statuses:
            in_progress_issues += 1
        else:
            todo_issues += 1

        total_points += points

        by_status[status]["count"] += 1
        by_status[status]["points"] += points

    completion_pct = 0.0
    if total_points > 0:
        completion_pct = round(100.0 * completed_points / total_points, 1)
    elif completed_issues > 0:
        completion_pct = round(100.0 * completed_issues / total_issues, 1)

    return {
        "total_issues": total_issues,
        "completed_issues": completed_issues,
        "in_progress_issues": in_progress_issues,
        "todo_issues": todo_issues,
        "total_points": total_points,
        "completed_points": completed_points,
        "completion_pct": completion_pct,
        "by_status": dict(by_status),
    }


def _add_health_indicators(
    issue: dict,
    backend,
    profile_id: str | None,
    query_id: str | None,
    flow_end_statuses: list[str] | None = None,
    flow_wip_statuses: list[str] | None = None,
) -> dict:

    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]
    if flow_wip_statuses is None:
        flow_wip_statuses = []

    now = datetime.now(UTC)
    status = issue.get("status", "Unknown")
    is_completed = status in flow_end_statuses

    is_in_wip_status = _is_wip_status_check(status, flow_wip_statuses)

    is_blocked = False
    is_aging = False
    is_wip = False
    days_since_status_change = None

    if backend and profile_id and query_id and not is_completed:
        try:
            issue_key = issue.get("issue_key")
            if issue_key:
                changelog = backend.get_changelog_entries(
                    profile_id=profile_id,
                    query_id=query_id,
                    issue_key=issue_key,
                    field_name="status",
                )

                if changelog:
                    latest_change = changelog[0]
                    change_date_str = latest_change.get("change_date")

                    if change_date_str:
                        try:
                            if change_date_str.endswith("Z"):
                                change_date_str = change_date_str[:-1] + "+00:00"
                            change_dt = datetime.fromisoformat(change_date_str)
                            if change_dt.tzinfo is None:
                                change_dt = change_dt.replace(tzinfo=UTC)

                            days_since_status_change = (now - change_dt).days

                            if is_in_wip_status and days_since_status_change >= 5:
                                is_blocked = True
                            elif is_in_wip_status and days_since_status_change >= 3:
                                is_aging = True
                            elif is_in_wip_status and days_since_status_change <= 2:
                                is_wip = True

                        except (ValueError, AttributeError) as e:
                            logger.debug(
                                "Could not parse status change date "
                                f"for {issue_key}: {e}"
                            )
                else:
                    created_str = issue.get("created")
                    if created_str:
                        try:
                            if created_str.endswith("Z"):
                                created_str = created_str[:-1] + "+00:00"
                            created_dt = datetime.fromisoformat(created_str)
                            if created_dt.tzinfo is None:
                                created_dt = created_dt.replace(tzinfo=UTC)
                            days_since_created = (now - created_dt).days

                            if is_in_wip_status and days_since_created >= 5:
                                is_blocked = True
                            elif is_in_wip_status and days_since_created >= 3:
                                is_aging = True
                        except ValueError, AttributeError:
                            pass

        except Exception as e:
            logger.warning(f"Failed to get changelog for {issue.get('issue_key')}: {e}")
            pass

    issue_with_health = {**issue}
    issue_with_health["health_indicators"] = {
        "is_blocked": is_blocked,
        "is_aging": is_aging,
        "is_wip": is_wip,
        "is_completed": is_completed,
    }

    return issue_with_health


def _is_wip_status_check(status: str, flow_wip_statuses: list[str]) -> bool:

    if flow_wip_statuses and status in flow_wip_statuses:
        return True

    status_lower = status.lower()
    wip_keywords = [
        "progress",
        "review",
        "testing",
        "development",
        "deployment",
        "deploying",
    ]
    return any(kw in status_lower for kw in wip_keywords)


def _build_epic_timeline(
    issues: list[dict],
    backend,
    profile_id: str | None,
    query_id: str | None,
    parent_field: str,
    flow_end_statuses: list[str] | None,
    flow_wip_statuses: list[str] | None,
    all_issues_unfiltered: list[dict] | None = None,
    parent_issue_types: list[str] | None = None,
) -> list[dict]:

    if all_issues_unfiltered is None:
        all_issues_unfiltered = issues
    epics = defaultdict(list)
    standalone_parent_summaries: dict[str, str] = {}
    normalized_parent_issue_types = {
        issue_type.strip().lower()
        for issue_type in (parent_issue_types or [])
        if isinstance(issue_type, str)
    }

    for issue in issues:
        parent = issue.get(parent_field)
        if not parent and parent_field.startswith("customfield_"):
            custom_fields = issue.get("custom_fields", {})
            parent = custom_fields.get(parent_field)

        parent_key = None

        if parent:
            if isinstance(parent, dict):
                parent_key = parent.get("key")
            elif isinstance(parent, str):
                parent_key = parent

        if not parent_key:
            issue_type = issue.get("issue_type")
            if issue_type is None and isinstance(issue.get("fields"), dict):
                issue_type = issue.get("fields", {}).get("issuetype", {}).get("name")

            normalized_issue_type = (
                issue_type.strip().lower() if isinstance(issue_type, str) else ""
            )
            issue_key = issue.get("issue_key")

            if issue_key and normalized_issue_type in normalized_parent_issue_types:
                parent_key = issue_key
                standalone_parent_summaries[parent_key] = (
                    issue.get("summary") or issue_key
                )
                epics[parent_key]
                continue
            else:
                parent_key = "No Parent"

        epics[parent_key].append(issue)

    timeline = []
    for epic_key, child_issues in epics.items():
        if not child_issues and epic_key not in standalone_parent_summaries:
            continue

        progress = calculate_epic_progress(
            child_issues, flow_end_statuses, flow_wip_statuses
        )

        epic_summary = epic_key
        if epic_key in standalone_parent_summaries:
            epic_summary = standalone_parent_summaries[epic_key]
        elif epic_key != "No Parent":
            first_issue = child_issues[0]
            parent = first_issue.get(parent_field)
            if not parent and parent_field.startswith("customfield_"):
                custom_fields = first_issue.get("custom_fields", {})
                parent = custom_fields.get(parent_field)

            logger.debug(
                "[EPIC] "
                f"epic_key={epic_key}, parent type: {type(parent)}, value: {parent}"
            )

            if isinstance(parent, dict):
                epic_summary = (
                    parent.get("summary")
                    or parent.get("fields", {}).get("summary")
                    or parent.get("name")
                    or epic_key
                )
                logger.debug(f"[EPIC] From parent dict: {epic_summary}")
            elif isinstance(parent, str):
                logger.debug(
                    f"[EPIC] Parent is string '{parent}', looking up summary..."
                )

                epic_issue = next(
                    (
                        issue
                        for issue in all_issues_unfiltered
                        if issue.get("issue_key") == parent
                    ),
                    None,
                )
                if epic_issue:
                    epic_summary = epic_issue.get("summary", epic_key)
                    logger.info(
                        f"[EPIC] Found {parent} in unfiltered list: '{epic_summary}'"
                    )
                elif backend and profile_id and query_id:
                    try:
                        all_issues_db = backend.get_issues(profile_id, query_id)
                        logger.debug(
                            "[EPIC] Searching "
                            f"{len(all_issues_db)} issues in DB for parent {parent}"
                        )
                        epic_issue = next(
                            (
                                issue
                                for issue in all_issues_db
                                if issue.get("issue_key") == parent
                            ),
                            None,
                        )
                        if epic_issue:
                            epic_summary = epic_issue.get("summary", epic_key)
                            logger.info(
                                f"[EPIC] Found {parent} in database: '{epic_summary}'"
                            )
                        else:
                            logger.warning(
                                "[EPIC] Parent "
                                f"{parent} not found in database "
                                "(may need to run 'Update Data')"
                            )
                            epic_summary = epic_key
                    except Exception as e:
                        logger.error(
                            f"[EPIC] Failed to fetch parent {parent} from DB: {e}"
                        )
                        epic_summary = epic_key
                else:
                    logger.warning(f"[EPIC] No backend to fetch {parent}")
                    epic_summary = epic_key
            else:
                logger.warning(f"[EPIC] Unexpected parent type: {type(parent)}")
                epic_summary = epic_key

        def sort_priority(issue):
            status = issue.get("status", "Unknown")
            health = issue.get("health_indicators", {})

            if health.get("is_blocked"):
                return (1, status)
            elif health.get("is_aging"):
                return (2, status)
            elif flow_wip_statuses and status in flow_wip_statuses:
                return (3, status)
            elif not (flow_end_statuses and status in flow_end_statuses):
                return (4, status)
            else:
                return (5, status)

        sorted_child_issues = sorted(child_issues, key=sort_priority)

        timeline.append(
            {
                "epic_key": epic_key,
                "epic_summary": epic_summary,
                "total_issues": progress["total_issues"],
                "completed_issues": progress["completed_issues"],
                "in_progress_issues": progress["in_progress_issues"],
                "todo_issues": progress["todo_issues"],
                "total_points": progress["total_points"],
                "completed_points": progress["completed_points"],
                "completion_pct": progress["completion_pct"],
                "child_issues": sorted_child_issues,
            }
        )

    timeline.sort(key=get_epic_sort_key)

    logger.info(f"Built timeline with {len(timeline)} epics")
    return timeline
