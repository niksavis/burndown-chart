import logging
from collections import defaultdict
from datetime import UTC, datetime

from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


def _extract_issue_state(issue: dict) -> dict:
    status = issue.get("status", "Unknown")

    story_points = issue.get("points")
    if story_points is None:
        custom_fields = issue.get("custom_fields", {})
        if isinstance(custom_fields, dict):
            for field in [
                "customfield_10002",
                "customfield_10016",
                "customfield_10026",
            ]:
                story_points = custom_fields.get(field)
                if story_points is not None:
                    break

    issue_type = issue.get("issue_type", "Unknown")
    summary = issue.get("summary", "")

    return {
        "status": status,
        "story_points": story_points,
        "issue_type": issue_type,
        "summary": summary,
    }


def build_issue_state_lookup(issues: list[dict]) -> dict[str, dict]:
    return {
        issue_key: _extract_issue_state(issue)
        for issue in issues
        if isinstance((issue_key := issue.get("issue_key")), str) and issue_key
    }


def get_active_sprint_from_issues(
    issues: list[dict], sprint_field: str = "customfield_10005"
) -> dict | None:

    sprint_counts = {}

    for issue in issues:
        custom_fields = issue.get("custom_fields", {})
        sprint_value = custom_fields.get(sprint_field)

        if not sprint_value:
            continue

        sprint_list = sprint_value if isinstance(sprint_value, list) else [sprint_value]

        for sprint_str in sprint_list:
            if not isinstance(sprint_str, str):
                continue

            sprint_obj = _parse_sprint_object(sprint_str)
            if sprint_obj:
                name = sprint_obj["name"]
                state = sprint_obj["state"]
                start_date = sprint_obj.get("start_date")
                end_date = sprint_obj.get("end_date")

                if name not in sprint_counts:
                    sprint_counts[name] = {
                        "count": 0,
                        "state": state,
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                sprint_counts[name]["count"] += 1

    def _parse_or_default(iso_date: str | None, fallback: float) -> float:
        if not iso_date:
            return fallback
        try:
            return date_parser.parse(iso_date).timestamp()
        except Exception:
            return fallback

    active_candidates = [
        (name, data)
        for name, data in sprint_counts.items()
        if data.get("state") == "ACTIVE"
    ]
    future_candidates = [
        (name, data)
        for name, data in sprint_counts.items()
        if data.get("state") == "FUTURE"
    ]
    closed_candidates = [
        (name, data)
        for name, data in sprint_counts.items()
        if data.get("state") == "CLOSED"
    ]

    active_sprint_name = None
    active_sprint_data = None

    if active_candidates:
        active_sprint_name, active_sprint_data = max(
            active_candidates,
            key=lambda item: (
                item[1].get("count", 0),
                _parse_or_default(item[1].get("start_date"), float("-inf")),
            ),
        )
    elif future_candidates:
        active_sprint_name, active_sprint_data = min(
            future_candidates,
            key=lambda item: (
                _parse_or_default(item[1].get("start_date"), float("inf")),
                -item[1].get("count", 0),
            ),
        )
    elif closed_candidates:
        active_sprint_name, active_sprint_data = max(
            closed_candidates,
            key=lambda item: (
                _parse_or_default(item[1].get("end_date"), float("-inf")),
                item[1].get("count", 0),
            ),
        )
    elif sprint_counts:
        active_sprint_name, active_sprint_data = max(
            sprint_counts.items(), key=lambda item: item[1].get("count", 0)
        )

    if active_sprint_name and active_sprint_data:
        logger.info(
            "Determined preferred sprint: "
            f"{active_sprint_name} ({active_sprint_data.get('count', 0)} issues), "
            "dates: "
            f"{active_sprint_data['start_date']} to {active_sprint_data['end_date']}"
        )
        return {
            "name": active_sprint_name,
            "start_date": active_sprint_data["start_date"],
            "end_date": active_sprint_data["end_date"],
        }
    else:
        logger.warning("No active sprint found in issues")
        return None


def get_sprint_dates(
    sprint_name: str, issues: list[dict], sprint_field: str = "customfield_10005"
) -> dict | None:

    for issue in issues:
        custom_fields = issue.get("custom_fields", {})
        sprint_value = custom_fields.get(sprint_field)

        if not sprint_value:
            continue

        sprint_list = sprint_value if isinstance(sprint_value, list) else [sprint_value]

        for sprint_str in sprint_list:
            if not isinstance(sprint_str, str):
                continue

            sprint_obj = _parse_sprint_object(sprint_str)
            if sprint_obj and sprint_obj["name"] == sprint_name:
                start_date = sprint_obj.get("start_date")
                end_date = sprint_obj.get("end_date")
                state = sprint_obj.get("state")

                if start_date and end_date:
                    logger.info(
                        "Found dates for "
                        f"{sprint_name}: {start_date} to {end_date}, state: {state}"
                    )
                    return {
                        "start_date": start_date,
                        "end_date": end_date,
                        "state": state,
                    }

    logger.warning(f"No dates found for sprint: {sprint_name}")
    return None


def sort_sprint_ids_by_recency(
    sprint_snapshots: dict[str, dict], sprint_metadata: dict[str, dict] | None = None
) -> list[str]:

    sprint_metadata = sprint_metadata or {}

    def _parse_date(value: str | None) -> float:
        if not value:
            return float("-inf")
        try:
            return date_parser.parse(value).timestamp()
        except Exception:
            return float("-inf")

    def _sort_key(sprint_id: str) -> tuple[float, float, str]:
        metadata = sprint_metadata.get(sprint_id, {})
        return (
            _parse_date(metadata.get("end_date")),
            _parse_date(metadata.get("start_date")),
            sprint_id,
        )

    return sorted(sprint_snapshots.keys(), key=_sort_key, reverse=True)


def select_preferred_sprint(
    sprint_snapshots: dict[str, dict],
    sprint_metadata: dict[str, dict] | None = None,
    preferred_sprint: str | None = None,
) -> dict | None:

    if not sprint_snapshots:
        return None

    sprint_metadata = sprint_metadata or {}

    if preferred_sprint and preferred_sprint in sprint_snapshots:
        preferred_meta = sprint_metadata.get(preferred_sprint, {})
        return {
            "name": preferred_sprint,
            "start_date": preferred_meta.get("start_date"),
            "end_date": preferred_meta.get("end_date"),
            "state": preferred_meta.get("state"),
        }

    active_candidates: list[str] = []
    future_candidates: list[str] = []
    closed_candidates: list[str] = []
    for sprint_id in sprint_snapshots.keys():
        state = sprint_metadata.get(sprint_id, {}).get("state")
        if state == "ACTIVE":
            active_candidates.append(sprint_id)
        elif state == "FUTURE":
            future_candidates.append(sprint_id)
        elif state == "CLOSED":
            closed_candidates.append(sprint_id)

    if active_candidates:
        chosen = sort_sprint_ids_by_recency(
            {sid: sprint_snapshots[sid] for sid in active_candidates}, sprint_metadata
        )[0]
    elif future_candidates:

        def _future_key(sprint_id: str) -> float:
            value = sprint_metadata.get(sprint_id, {}).get("start_date")
            if not value:
                return float("inf")
            try:
                return date_parser.parse(value).timestamp()
            except Exception:
                return float("inf")

        chosen = min(future_candidates, key=_future_key)
    elif closed_candidates:
        chosen = sort_sprint_ids_by_recency(
            {sid: sprint_snapshots[sid] for sid in closed_candidates}, sprint_metadata
        )[0]
    else:
        chosen = sort_sprint_ids_by_recency(sprint_snapshots, sprint_metadata)[0]

    chosen_meta = sprint_metadata.get(chosen, {})
    return {
        "name": chosen,
        "start_date": chosen_meta.get("start_date"),
        "end_date": chosen_meta.get("end_date"),
        "state": chosen_meta.get("state"),
    }


def get_sprint_snapshots(
    issues: list[dict],
    changelog_entries: list[dict],
    sprint_field: str = "customfield_10020",
) -> dict[str, dict]:

    logger.info(
        f"Building sprint snapshots from {len(changelog_entries)} changelog entries"
    )

    sorted_entries = sorted(changelog_entries, key=lambda x: x.get("change_date", ""))

    sprint_snapshots: dict[str, dict] = {}
    issue_current_sprint = {}
    changelog_processed_pairs: set[tuple[str, str]] = set()
    issues_with_sprint_changelog: set[str] = set()

    def _get_or_create_snapshot(sprint_id: str) -> dict:
        if sprint_id not in sprint_snapshots:
            sprint_snapshots[sprint_id] = {
                "added_issues": [],
                "removed_issues": [],
                "current_issues": set(),
                "issue_states": {},
            }
        return sprint_snapshots[sprint_id]

    filtered_issue_keys = {issue.get("issue_key") for issue in issues}

    for entry in sorted_entries:
        issue_key = entry.get("issue_key")
        old_value = entry.get("old_value")
        new_value = entry.get("new_value")
        timestamp = entry.get("change_date")

        if not isinstance(issue_key, str) or not issue_key or not timestamp:
            continue
        issues_with_sprint_changelog.add(issue_key)

        if issue_key not in filtered_issue_keys:
            continue

        old_sprint = _parse_sprint_name(old_value)
        new_sprint = _parse_sprint_name(new_value)

        if not old_sprint and new_sprint:
            snapshot = _get_or_create_snapshot(new_sprint)
            snapshot["added_issues"].append(
                {"issue_key": issue_key, "timestamp": timestamp}
            )
            snapshot["current_issues"].add(issue_key)
            issue_current_sprint[issue_key] = new_sprint
            changelog_processed_pairs.add((issue_key, new_sprint))

        elif old_sprint and not new_sprint:
            snapshot = _get_or_create_snapshot(old_sprint)
            snapshot["removed_issues"].append(
                {"issue_key": issue_key, "timestamp": timestamp}
            )
            snapshot["current_issues"].discard(issue_key)
            issue_current_sprint[issue_key] = None
            changelog_processed_pairs.add((issue_key, old_sprint))

        elif old_sprint and new_sprint and old_sprint != new_sprint:
            old_snapshot = _get_or_create_snapshot(old_sprint)
            old_snapshot["removed_issues"].append(
                {"issue_key": issue_key, "timestamp": timestamp}
            )
            old_snapshot["current_issues"].discard(issue_key)
            changelog_processed_pairs.add((issue_key, old_sprint))

            new_snapshot = _get_or_create_snapshot(new_sprint)
            new_snapshot["added_issues"].append(
                {"issue_key": issue_key, "timestamp": timestamp}
            )
            new_snapshot["current_issues"].add(issue_key)
            changelog_processed_pairs.add((issue_key, new_sprint))

            issue_current_sprint[issue_key] = new_sprint

    logger.info(f"Checking {len(issues)} issues for missing sprint assignments")
    added_count = 0
    for issue in issues:
        issue_key = issue.get("issue_key")
        if not isinstance(issue_key, str) or not issue_key:
            continue

        if issue_key in issues_with_sprint_changelog:
            continue

        custom_fields = issue.get("custom_fields", {})
        sprint_value = custom_fields.get(sprint_field)

        if not sprint_value:
            continue

        inferred_current_sprints = _infer_current_sprints_from_field(sprint_value)
        for sprint_name in inferred_current_sprints:
            if (issue_key, sprint_name) in changelog_processed_pairs:
                continue

            logger.info(
                f"Adding issue {issue_key} to {sprint_name} (no changelog entry)"
            )
            snapshot = _get_or_create_snapshot(sprint_name)
            if issue_key not in snapshot["current_issues"]:
                snapshot["current_issues"].add(issue_key)
                changelog_processed_pairs.add((issue_key, sprint_name))
                issue_current_sprint[issue_key] = sprint_name
                added_count += 1

    logger.info(f"Added {added_count} issues with no changelog to sprint snapshots")

    all_issue_states = build_issue_state_lookup(issues)

    for sprint_id, snapshot in sprint_snapshots.items():
        snapshot["current_issues"] = list(snapshot["current_issues"])
        snapshot["name"] = sprint_id

        for issue_key in snapshot["current_issues"]:
            issue_state = all_issue_states.get(issue_key)
            if issue_state is not None:
                snapshot["issue_states"][issue_key] = issue_state

    logger.info(f"Built snapshots for {len(sprint_snapshots)} sprints")

    return sprint_snapshots


def _parse_sprint_name(sprint_value: str | None) -> str | None:

    if not sprint_value:
        return None

    if "name=" in sprint_value:
        try:
            name_start = sprint_value.index("name=") + 5
            name_end = sprint_value.index(",", name_start)
            return sprint_value[name_start:name_end]
        except ValueError:
            try:
                name_start = sprint_value.index("name=") + 5
                name_end = sprint_value.index("]", name_start)
                return sprint_value[name_start:name_end]
            except ValueError:
                pass

    if "," in sprint_value:
        sprints = [s.strip() for s in sprint_value.split(",")]
        return sprints[-1] if sprints else None

    return sprint_value.strip()


def _infer_current_sprints_from_field(sprint_value: str | list[str]) -> list[str]:

    sprint_tokens = sprint_value if isinstance(sprint_value, list) else [sprint_value]

    parsed_objects: list[dict] = []
    fallback_names: list[str] = []

    for token in sprint_tokens:
        if not isinstance(token, str) or not token:
            continue

        parsed = _parse_sprint_object(token)
        if parsed and parsed.get("name"):
            parsed_objects.append(parsed)
            continue

        parsed_name = _parse_sprint_name(token)
        if parsed_name:
            fallback_names.append(parsed_name)

    preferred_names = [
        obj["name"]
        for obj in parsed_objects
        if obj.get("state") in {"ACTIVE", "FUTURE"}
    ]

    if preferred_names:
        return list(dict.fromkeys(preferred_names))

    if parsed_objects:
        return [parsed_objects[-1]["name"]]

    if fallback_names:
        return [fallback_names[-1]]

    return []


def _parse_sprint_object(sprint_value: str) -> dict | None:

    if not sprint_value or "[" not in sprint_value:
        return None

    try:
        start = sprint_value.index("[") + 1
        end = sprint_value.rindex("]")
        properties = sprint_value[start:end]

        sprint_data = {}
        for prop in properties.split(","):
            if "=" in prop:
                key, value = prop.split("=", 1)
                sprint_data[key.strip()] = value.strip()

        name = sprint_data.get("name")
        state = sprint_data.get("state")
        start_date = sprint_data.get("startDate")
        end_date = sprint_data.get("endDate")

        if name and state:
            result = {
                "name": name,
                "state": state.upper(),
                "start_date": start_date
                if start_date and start_date != "<null>"
                else None,
                "end_date": end_date if end_date and end_date != "<null>" else None,
            }
            return result

    except (ValueError, IndexError) as e:
        logger.debug(f"Failed to parse sprint object: {e}")

    return None


def detect_sprint_changes(
    changelog_entries: list[dict],
) -> dict[str, dict[str, list[dict]]]:

    logger.info(f"Detecting sprint changes from {len(changelog_entries)} entries")

    sorted_entries = sorted(changelog_entries, key=lambda x: x.get("change_date", ""))

    sprint_changes = defaultdict(
        lambda: {"added": [], "removed": [], "moved_in": [], "moved_out": []}
    )

    for entry in sorted_entries:
        issue_key = entry.get("issue_key")
        old_value = entry.get("old_value")
        new_value = entry.get("new_value")
        timestamp = entry.get("change_date")

        if not issue_key or not timestamp:
            continue

        old_sprint = _parse_sprint_name(old_value)
        new_sprint = _parse_sprint_name(new_value)

        if not old_sprint and new_sprint:
            sprint_changes[new_sprint]["added"].append(
                {"issue_key": issue_key, "timestamp": timestamp, "from": None}
            )

        elif old_sprint and not new_sprint:
            sprint_changes[old_sprint]["removed"].append(
                {"issue_key": issue_key, "timestamp": timestamp, "to": None}
            )

        elif old_sprint and new_sprint and old_sprint != new_sprint:
            sprint_changes[old_sprint]["moved_out"].append(
                {"issue_key": issue_key, "timestamp": timestamp, "to": new_sprint}
            )
            sprint_changes[new_sprint]["moved_in"].append(
                {"issue_key": issue_key, "timestamp": timestamp, "from": old_sprint}
            )

    logger.info(f"Detected changes for {len(sprint_changes)} sprints")
    return dict(sprint_changes)


def calculate_sprint_scope_changes(
    sprint_snapshot: dict, sprint_start_date: str | None = None
) -> dict[str, int]:

    added_issues = sprint_snapshot.get("added_issues", [])
    removed_issues = sprint_snapshot.get("removed_issues", [])

    if sprint_start_date:
        try:
            start_dt = date_parser.parse(sprint_start_date)
            added_issues = [
                item
                for item in added_issues
                if date_parser.parse(item.get("timestamp", "")) > start_dt
            ]
            removed_issues = [
                item
                for item in removed_issues
                if date_parser.parse(item.get("timestamp", "")) > start_dt
            ]
        except Exception as e:
            logger.warning(f"Failed to parse sprint start date: {e}")

    added_count = len(added_issues)
    removed_count = len(removed_issues)

    return {
        "added": added_count,
        "removed": removed_count,
        "net_change": added_count - removed_count,
    }


def get_sprint_scope_change_issues(
    sprint_snapshot: dict,
    sprint_start_date: str | None = None,
    sprint_end_date: str | None = None,
) -> dict[str, list[str]]:

    start_dt = None
    end_dt = None

    if sprint_start_date:
        try:
            start_dt = date_parser.parse(sprint_start_date)
        except Exception as error:
            logger.warning(
                f"Failed to parse sprint start date for scope issues: {error}"
            )

    if sprint_end_date:
        try:
            end_dt = date_parser.parse(sprint_end_date)
        except Exception as error:
            logger.warning(f"Failed to parse sprint end date for scope issues: {error}")

    def _in_window(timestamp: str) -> bool:
        try:
            event_dt = date_parser.parse(timestamp)
        except Exception:
            return False

        if start_dt and event_dt <= start_dt:
            return False
        if end_dt and event_dt > end_dt:
            return False
        return True

    added_keys = {
        item.get("issue_key")
        for item in sprint_snapshot.get("added_issues", [])
        if item.get("issue_key") and _in_window(item.get("timestamp", ""))
    }
    removed_keys = {
        item.get("issue_key")
        for item in sprint_snapshot.get("removed_issues", [])
        if item.get("issue_key") and _in_window(item.get("timestamp", ""))
    }

    return {
        "added": sorted(added_keys),
        "removed": sorted(removed_keys),
    }


def calculate_sprint_scope_change_points(
    sprint_snapshot: dict,
    issues: list[dict],
    sprint_start_date: str | None = None,
    sprint_end_date: str | None = None,
) -> dict[str, float]:

    scope_change_issues = get_sprint_scope_change_issues(
        sprint_snapshot,
        sprint_start_date=sprint_start_date,
        sprint_end_date=sprint_end_date,
    )

    issues_by_key = {
        issue.get("issue_key"): issue
        for issue in issues
        if isinstance(issue.get("issue_key"), str)
    }

    def _extract_issue_points(issue: dict | None) -> float:
        if not isinstance(issue, dict):
            return 0.0

        points = issue.get("points")
        if points is None:
            custom_fields = issue.get("custom_fields", {})
            if isinstance(custom_fields, dict):
                for field in [
                    "customfield_10002",
                    "customfield_10016",
                    "customfield_10026",
                ]:
                    points = custom_fields.get(field)
                    if points is not None:
                        break

        try:
            return float(points) if points is not None else 0.0
        except TypeError, ValueError:
            return 0.0

    added_points = sum(
        _extract_issue_points(issues_by_key.get(issue_key))
        for issue_key in scope_change_issues.get("added", [])
    )
    removed_points = sum(
        _extract_issue_points(issues_by_key.get(issue_key))
        for issue_key in scope_change_issues.get("removed", [])
    )

    return {
        "added_points": added_points,
        "removed_points": removed_points,
        "net_points": added_points - removed_points,
    }


def reconcile_active_sprint_membership(
    sprint_snapshot: dict,
    issues: list[dict],
    sprint_name: str,
    sprint_field: str,
) -> dict:

    current_members: set[str] = set()
    issue_lookup: dict[str, dict] = {}

    for issue in issues:
        issue_key = issue.get("issue_key")
        if not isinstance(issue_key, str) or not issue_key:
            continue

        issue_lookup[issue_key] = issue

        custom_fields = issue.get("custom_fields", {})
        if not isinstance(custom_fields, dict):
            continue

        sprint_value = custom_fields.get(sprint_field)
        if not sprint_value:
            continue

        inferred_current_sprints = _infer_current_sprints_from_field(sprint_value)
        if sprint_name in inferred_current_sprints:
            current_members.add(issue_key)

    original_current = sprint_snapshot.get("current_issues", [])
    original_set = set(original_current)

    preserved_order = [
        issue_key for issue_key in original_current if issue_key in current_members
    ]
    newly_discovered = sorted(current_members - set(preserved_order))
    reconciled_current = preserved_order + newly_discovered
    reconciled_set = set(reconciled_current)

    original_issue_states = sprint_snapshot.get("issue_states", {})
    reconciled_issue_states: dict[str, dict] = {}
    for issue_key in reconciled_current:
        if issue_key in original_issue_states:
            reconciled_issue_states[issue_key] = original_issue_states[issue_key]
            continue

        issue = issue_lookup.get(issue_key, {})
        custom_fields = issue.get("custom_fields", {})

        story_points = issue.get("points")
        if story_points is None and isinstance(custom_fields, dict):
            for field in [
                "customfield_10002",
                "customfield_10016",
                "customfield_10026",
            ]:
                story_points = custom_fields.get(field)
                if story_points is not None:
                    break

        reconciled_issue_states[issue_key] = {
            "status": issue.get("status", "Unknown"),
            "story_points": story_points,
            "issue_type": issue.get("issue_type", "Unknown"),
            "summary": issue.get("summary", ""),
        }

    removed_count = len(original_set - reconciled_set)
    added_count = len(reconciled_set - original_set)
    if removed_count > 0 or added_count > 0:
        logger.info(
            "Reconciled active sprint membership for "
            f"{sprint_name}: removed {removed_count} stale issues, "
            f"added {added_count} missing current issues"
        )

    return {
        **sprint_snapshot,
        "current_issues": reconciled_current,
        "issue_states": reconciled_issue_states,
    }


def calculate_sprint_progress(
    sprint_snapshot: dict,
    flow_end_statuses: list[str] | None = None,
    flow_wip_statuses: list[str] | None = None,
) -> dict:

    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]
    if flow_wip_statuses is None:
        flow_wip_statuses = ["In Progress", "In Review", "Testing"]

    issue_states = sprint_snapshot.get("issue_states", {})

    total_issues = len(issue_states)
    completed_issues = 0
    wip_issues = 0
    total_points = 0.0
    completed_points = 0.0
    wip_points = 0.0

    by_status = defaultdict(lambda: {"count": 0, "points": 0.0})
    by_issue_type = defaultdict(lambda: {"count": 0, "points": 0.0})

    all_statuses_in_sprint = set()
    wip_status_set = set(flow_wip_statuses)

    for _issue_key, state in issue_states.items():
        status = state.get("status", "Unknown")
        story_points = state.get("story_points", 0) or 0
        issue_type = state.get("issue_type", "Unknown")

        all_statuses_in_sprint.add(status)

        if status in flow_end_statuses:
            completed_issues += 1
            completed_points += story_points
        elif status in flow_wip_statuses:
            wip_issues += 1
            wip_points += story_points

        total_points += story_points

        by_status[status]["count"] += 1
        by_status[status]["points"] += story_points

        by_issue_type[issue_type]["count"] += 1
        by_issue_type[issue_type]["points"] += story_points

    uncounted_wip_statuses = (
        all_statuses_in_sprint - wip_status_set - set(flow_end_statuses)
    )
    if uncounted_wip_statuses:
        logger.warning(
            f"Sprint has statuses not in WIP or End config: {uncounted_wip_statuses}. "
            f"WIP config: {flow_wip_statuses}, End config: {flow_end_statuses}"
        )

    completion_percentage = (
        (completed_issues / total_issues * 100.0) if total_issues > 0 else 0.0
    )
    points_completion_percentage = (
        (completed_points / total_points * 100.0) if total_points > 0 else 0.0
    )

    todo_issues = total_issues - wip_issues - completed_issues
    todo_points = total_points - wip_points - completed_points

    return {
        "total_issues": total_issues,
        "completed_issues": completed_issues,
        "wip_issues": wip_issues,
        "todo_issues": todo_issues,
        "completion_pct": round(completion_percentage, 1),
        "completion_percentage": round(completion_percentage, 1),
        "total_points": total_points,
        "completed_points": completed_points,
        "wip_points": wip_points,
        "todo_points": todo_points,
        "points_completion_pct": round(points_completion_percentage, 1),
        "points_completion_percentage": round(points_completion_percentage, 1),
        "by_status": dict(by_status),
        "by_issue_type": dict(by_issue_type),
    }


def filter_sprint_issues(
    issues: list[dict],
    tracked_issue_types: list[str] | None = None,
) -> list[dict]:

    if tracked_issue_types is None:
        tracked_issue_types = ["Story", "Task", "Bug"]

    filtered = []

    for issue in issues:
        if "fields" in issue:
            issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "")
        else:
            issue_type = issue.get("issue_type", "")

        if issue_type in tracked_issue_types:
            filtered.append(issue)

    logger.info(
        f"Filtered {len(filtered)} issues from {len(issues)} total "
        f"(types: {tracked_issue_types})"
    )

    return filtered


def get_sprint_field_from_config(config: dict) -> str | None:

    field_mappings = config.get("field_mappings", {})
    sprint_tracker_mappings = field_mappings.get("sprint_tracker", {})
    return sprint_tracker_mappings.get("sprint_field")


def calculate_issue_status_timeline(
    issue_key: str,
    changelog_entries: list[dict],
    include_current: bool = True,
) -> list[dict]:

    issue_changes = [
        entry
        for entry in changelog_entries
        if entry.get("issue_key") == issue_key and entry.get("field_name") == "status"
    ]

    if not issue_changes:
        return []

    issue_changes.sort(key=lambda x: x.get("change_date", ""))

    segments = []
    for i, change in enumerate(issue_changes):
        status = change.get("new_value", "Unknown")
        change_date_str = change.get("change_date", "")

        try:
            start_time = datetime.fromisoformat(change_date_str.replace("Z", "+00:00"))
        except ValueError, AttributeError:
            logger.warning(
                f"Invalid date format for {issue_key}: {change_date_str}, skipping"
            )
            continue

        if i < len(issue_changes) - 1:
            next_change_date_str = issue_changes[i + 1].get("change_date", "")
            try:
                end_time = datetime.fromisoformat(
                    next_change_date_str.replace("Z", "+00:00")
                )
            except ValueError, AttributeError:
                logger.warning(
                    "Invalid next date format for "
                    f"{issue_key}: {next_change_date_str}, using now"
                )
                end_time = datetime.now(UTC)
        else:
            end_time = datetime.now(UTC) if include_current else start_time

        duration = end_time - start_time
        duration_hours = duration.total_seconds() / 3600

        segments.append(
            {
                "status": status,
                "start_time": start_time,
                "end_time": end_time,
                "duration_hours": duration_hours,
                "duration_pct": 0.0,
            }
        )

    total_hours = sum(seg["duration_hours"] for seg in segments)

    if total_hours > 0:
        for seg in segments:
            seg["duration_pct"] = (seg["duration_hours"] / total_hours) * 100.0

    return segments
