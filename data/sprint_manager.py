"""Sprint data manager for Sprint Tracker feature.

This module provides functions to construct sprint snapshots from changelog history,
track sprint changes (add/remove/move), and calculate sprint progress metrics.

Uses existing changelog infrastructure - no new JIRA API calls needed.
Sprint field changes are tracked via jira_changelog_entries table.

Key Functions:
    get_sprint_snapshots() -> Dict: Build sprint snapshots from changelog
    detect_sprint_changes() -> Dict: Detect add/remove/move events
    calculate_sprint_progress() -> Dict: Calculate sprint completion metrics
    filter_sprint_issues() -> List: Filter issues to Story/Task/Bug only
"""

import logging
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


def get_active_sprint_from_issues(
    issues: List[Dict], sprint_field: str = "customfield_10005"
) -> Optional[Dict]:
    """Determine the active sprint from current issue sprint field data.

    JIRA stores full sprint objects with state in issue fields.
    This function finds the sprint with state="ACTIVE" which is
    more reliable than using changelog timestamps.

    Args:
        issues: List of JIRA issues (from backend.get_issues())
        sprint_field: Sprint custom field ID (default: customfield_10005)

    Returns:
        Dict with {"name": str, "start_date": str, "end_date": str} or None
        Dates are ISO strings from JIRA sprint object
    """
    sprint_counts = {}  # sprint_name -> {count, state, start_date, end_date}

    for issue in issues:
        custom_fields = issue.get("custom_fields", {})
        sprint_value = custom_fields.get(sprint_field)

        if not sprint_value:
            continue

        # Sprint field is typically a list of sprint objects
        sprint_list = sprint_value if isinstance(sprint_value, list) else [sprint_value]

        for sprint_str in sprint_list:
            if not isinstance(sprint_str, str):
                continue

            # Parse serialized JIRA sprint object
            sprint_obj = _parse_sprint_object(sprint_str)
            if sprint_obj:
                name = sprint_obj["name"]
                state = sprint_obj["state"]
                start_date = sprint_obj.get("start_date")
                end_date = sprint_obj.get("end_date")

                # Track sprint counts and their states
                if name not in sprint_counts:
                    sprint_counts[name] = {
                        "count": 0,
                        "state": state,
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                sprint_counts[name]["count"] += 1

    # Find sprint with state=ACTIVE (highest priority)
    active_sprint_name = None
    active_sprint_data = None
    max_count = 0

    for sprint_name, data in sprint_counts.items():
        if data["state"] == "ACTIVE" and data["count"] > max_count:
            active_sprint_name = sprint_name
            active_sprint_data = data
            max_count = data["count"]

    # If no active sprint, fall back to the sprint with most issues
    if not active_sprint_name:
        for sprint_name, data in sprint_counts.items():
            if data["count"] > max_count:
                active_sprint_name = sprint_name
                active_sprint_data = data
                max_count = data["count"]

    if active_sprint_name and active_sprint_data:
        logger.info(
            f"Determined active sprint: {active_sprint_name} ({max_count} issues), "
            f"dates: {active_sprint_data['start_date']} to {active_sprint_data['end_date']}"
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
    sprint_name: str, issues: List[Dict], sprint_field: str = "customfield_10005"
) -> Optional[Dict]:
    """Get start and end dates for a specific sprint from issue data.

    Args:
        sprint_name: Name of the sprint (e.g., "Sprint 256", "Gravity Sprint 256")
        issues: List of JIRA issues (from backend.get_issues())
        sprint_field: Sprint custom field ID

    Returns:
        Dict with {"start_date": str, "end_date": str, "state": str} or None if sprint not found
        Dates are ISO strings from JIRA sprint object
        State is "ACTIVE", "CLOSED", or "FUTURE"
    """
    for issue in issues:
        custom_fields = issue.get("custom_fields", {})
        sprint_value = custom_fields.get(sprint_field)

        if not sprint_value:
            continue

        # Sprint field is typically a list of sprint objects
        sprint_list = sprint_value if isinstance(sprint_value, list) else [sprint_value]

        for sprint_str in sprint_list:
            if not isinstance(sprint_str, str):
                continue

            # Parse serialized JIRA sprint object
            sprint_obj = _parse_sprint_object(sprint_str)
            if sprint_obj and sprint_obj["name"] == sprint_name:
                start_date = sprint_obj.get("start_date")
                end_date = sprint_obj.get("end_date")
                state = sprint_obj.get("state")

                if start_date and end_date:
                    logger.info(
                        f"Found dates for {sprint_name}: {start_date} to {end_date}, state: {state}"
                    )
                    return {
                        "start_date": start_date,
                        "end_date": end_date,
                        "state": state,
                    }

    logger.warning(f"No dates found for sprint: {sprint_name}")
    return None


def get_sprint_snapshots(
    issues: List[Dict],
    changelog_entries: List[Dict],
    sprint_field: str = "customfield_10020",
) -> Dict[str, Dict]:
    """Build sprint snapshots from changelog history.

    Reconstructs current and historical sprint composition by analyzing
    sprint field changes in changelog entries.

    Args:
        issues: List of JIRA issues (from backend.get_issues())
        changelog_entries: Changelog entries filtered to sprint field changes
        sprint_field: Sprint custom field ID (default: customfield_10020)

    Returns:
        Dict of sprint_id -> snapshot:
        {
            "Sprint 23": {
                "name": "Sprint 23",
                "current_issues": ["PROJ-1", "PROJ-3"],
                "added_issues": [
                    {"issue_key": "PROJ-1", "timestamp": "2025-01-10T10:00:00Z"}
                ],
                "removed_issues": [
                    {"issue_key": "PROJ-2", "timestamp": "2025-01-15T14:00:00Z"}
                ],
                "issue_states": {
                    "PROJ-1": {"status": "Done", "story_points": 5}
                }
            }
        }
    """
    logger.info(
        f"Building sprint snapshots from {len(changelog_entries)} changelog entries"
    )

    # Sort changelog by date to process in chronological order
    sorted_entries = sorted(changelog_entries, key=lambda x: x.get("change_date", ""))

    # Track sprint events and current state
    sprint_snapshots: Dict[str, Dict] = {}
    issue_current_sprint = {}  # issue_key -> current sprint_id

    def _get_or_create_snapshot(sprint_id: str) -> Dict:
        """Helper to create sprint snapshot structure if not exists."""
        if sprint_id not in sprint_snapshots:
            sprint_snapshots[sprint_id] = {
                "added_issues": [],
                "removed_issues": [],
                "current_issues": set(),
                "issue_states": {},
            }
        return sprint_snapshots[sprint_id]

    # Create set of issue keys from filtered issues (for O(1) lookup)
    filtered_issue_keys = {issue.get("issue_key") for issue in issues}

    # Process changelog to detect sprint changes
    for entry in sorted_entries:
        issue_key = entry.get("issue_key")
        old_value = entry.get("old_value")
        new_value = entry.get("new_value")
        timestamp = entry.get("change_date")

        if not issue_key or not timestamp:
            continue

        # CRITICAL: Only process changelog entries for issues in the filtered list
        # This ensures issue type filtering works correctly
        if issue_key not in filtered_issue_keys:
            continue

        # Parse sprint name from JIRA sprint format
        # Format: "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23,...]"
        old_sprint = _parse_sprint_name(old_value)
        new_sprint = _parse_sprint_name(new_value)

        # Case 1: Issue added to sprint (null -> Sprint X)
        if not old_sprint and new_sprint:
            snapshot = _get_or_create_snapshot(new_sprint)
            snapshot["added_issues"].append(
                {"issue_key": issue_key, "timestamp": timestamp}
            )
            snapshot["current_issues"].add(issue_key)
            issue_current_sprint[issue_key] = new_sprint

        # Case 2: Issue removed from sprint (Sprint X -> null)
        elif old_sprint and not new_sprint:
            snapshot = _get_or_create_snapshot(old_sprint)
            snapshot["removed_issues"].append(
                {"issue_key": issue_key, "timestamp": timestamp}
            )
            snapshot["current_issues"].discard(issue_key)
            issue_current_sprint[issue_key] = None

        # Case 3: Issue moved between sprints (Sprint X -> Sprint Y)
        elif old_sprint and new_sprint and old_sprint != new_sprint:
            old_snapshot = _get_or_create_snapshot(old_sprint)
            old_snapshot["removed_issues"].append(
                {"issue_key": issue_key, "timestamp": timestamp}
            )
            old_snapshot["current_issues"].discard(issue_key)

            new_snapshot = _get_or_create_snapshot(new_sprint)
            new_snapshot["added_issues"].append(
                {"issue_key": issue_key, "timestamp": timestamp}
            )
            new_snapshot["current_issues"].add(issue_key)

            issue_current_sprint[issue_key] = new_sprint

    # CRITICAL FIX: Add issues that are currently in sprint but have no changelog
    # This handles cases where issues were created directly in a sprint or bulk-added
    # without generating changelog entries
    logger.info(f"Checking {len(issues)} issues for missing sprint assignments")
    added_count = 0
    for issue in issues:
        issue_key = issue.get("issue_key")
        if not issue_key:
            continue

        # Get current sprint value from issue
        custom_fields = issue.get("custom_fields", {})
        sprint_value = custom_fields.get(sprint_field)

        if not sprint_value:
            continue

        # Parse sprint name from field value
        sprint_list = sprint_value if isinstance(sprint_value, list) else [sprint_value]
        for sprint_obj in sprint_list:
            sprint_name = _parse_sprint_name(sprint_obj)
            if not sprint_name:
                continue

            # Check if issue is already tracked in this sprint
            if issue_current_sprint.get(issue_key) != sprint_name:
                # Issue is in sprint but not in snapshot - add it
                logger.info(
                    f"Adding issue {issue_key} to {sprint_name} (no changelog entry)"
                )
                snapshot = _get_or_create_snapshot(sprint_name)
                if issue_key not in snapshot["current_issues"]:
                    snapshot["current_issues"].add(issue_key)
                    issue_current_sprint[issue_key] = sprint_name
                    added_count += 1

    logger.info(f"Added {added_count} issues with no changelog to sprint snapshots")

    # Enrich snapshots with current issue states from issues list
    # Backend returns flattened structure with 'issue_key' (not 'key')
    issues_by_key = {issue.get("issue_key"): issue for issue in issues}

    for sprint_id, snapshot in sprint_snapshots.items():
        # Convert set to list for JSON serialization
        snapshot["current_issues"] = list(snapshot["current_issues"])
        snapshot["name"] = sprint_id

        # Add current state for each issue in sprint
        for issue_key in snapshot["current_issues"]:
            if issue_key in issues_by_key:
                issue = issues_by_key[issue_key]

                # Backend returns flattened structure, not nested fields
                status = issue.get("status", "Unknown")

                # Extract story points from custom_fields or direct 'points' field
                story_points = issue.get("points")  # Backend stores normalized points

                # If points is None, try custom_fields as fallback
                if story_points is None:
                    custom_fields = issue.get("custom_fields", {})
                    if isinstance(custom_fields, dict):
                        # Try common story points field IDs
                        for field in [
                            "customfield_10002",
                            "customfield_10016",
                            "customfield_10026",
                        ]:
                            story_points = custom_fields.get(field)
                            if story_points is not None:
                                break

                # Extract issue type (backend returns flattened)
                issue_type = issue.get("issue_type", "Unknown")

                # Extract summary (backend returns flattened)
                summary = issue.get("summary", "")

                snapshot["issue_states"][issue_key] = {
                    "status": status,
                    "story_points": story_points,
                    "issue_type": issue_type,
                    "summary": summary,
                }

    logger.info(f"Built snapshots for {len(sprint_snapshots)} sprints")

    return sprint_snapshots


def _parse_sprint_name(sprint_value: Optional[str]) -> Optional[str]:
    """Parse sprint name from JIRA sprint field value.

    JIRA returns sprint in different formats:
    1. Serialized object: "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23,...]"
    2. Simple name: "Gravity Sprint 256"
    3. Multiple sprints: "Gravity Sprint 254, Gravity Sprint 255, Gravity Sprint 256"

    For multiple sprints, returns the LAST sprint (typically the active/current one).

    Args:
        sprint_value: Raw sprint value from JIRA

    Returns:
        Sprint name (e.g., "Sprint 23") or None
    """
    if not sprint_value:
        return None

    # Handle JIRA sprint object format
    if "name=" in sprint_value:
        # Extract name value between "name=" and next comma
        try:
            name_start = sprint_value.index("name=") + 5
            name_end = sprint_value.index(",", name_start)
            return sprint_value[name_start:name_end]
        except ValueError:
            # Fallback: try to extract until closing bracket
            try:
                name_start = sprint_value.index("name=") + 5
                name_end = sprint_value.index("]", name_start)
                return sprint_value[name_start:name_end]
            except ValueError:
                pass

    # Handle comma-separated multiple sprints (e.g., "Sprint 254, Sprint 255, Sprint 256")
    # Return the LAST sprint as it's typically the active/current one
    if "," in sprint_value:
        sprints = [s.strip() for s in sprint_value.split(",")]
        return sprints[-1] if sprints else None

    # Fallback: return as-is if simple string
    return sprint_value.strip()


def _parse_sprint_object(sprint_value: str) -> Optional[Dict]:
    """Parse JIRA sprint object string to extract name, state, and dates.

    JIRA returns serialized sprint objects like:
    "com.atlassian.greenhopper.service.sprint.Sprint@44f88702[activatedDate=<null>,
    autoStartStop=false,completeDate=<null>,endDate=2026-02-24T19:19:00.000+01:00,
    goal=<null>,id=50477,name=Gravity Sprint 257,startDate=2026-02-10T09:00:00.000+01:00,
    state=FUTURE,...]"

    Args:
        sprint_value: Serialized JIRA sprint object string

    Returns:
        Dict with {"name": str, "state": str, "start_date": str, "end_date": str} or None
        State is one of: "ACTIVE", "FUTURE", "CLOSED"
        Dates are ISO strings or None if <null>
    """
    if not sprint_value or "[" not in sprint_value:
        return None

    try:
        # Extract the part inside brackets
        start = sprint_value.index("[") + 1
        end = sprint_value.rindex("]")
        properties = sprint_value[start:end]

        # Parse key=value pairs
        sprint_data = {}
        for prop in properties.split(","):
            if "=" in prop:
                key, value = prop.split("=", 1)
                sprint_data[key.strip()] = value.strip()

        # Extract name, state, and dates
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
    changelog_entries: List[Dict],
) -> Dict[str, Dict[str, List[Dict]]]:
    """Detect sprint lifecycle events from changelog.

    Analyzes changelog to identify when issues were added, removed, or moved
    between sprints.

    Args:
        changelog_entries: Changelog entries filtered to sprint field changes

    Returns:
        Dict of event types per sprint:
        {
            "Sprint 23": {
                "added": [{"issue_key": "PROJ-1", "timestamp": "...", "from": null}],
                "removed": [{"issue_key": "PROJ-2", "timestamp": "...", "to": null}],
                "moved_in": [{"issue_key": "PROJ-3", "timestamp": "...", "from": "Sprint 22"}],
                "moved_out": [{"issue_key": "PROJ-4", "timestamp": "...", "to": "Sprint 24"}]
            }
        }
    """
    logger.info(f"Detecting sprint changes from {len(changelog_entries)} entries")

    # Sort by change date
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

        # Case 1: Issue added to sprint (null -> Sprint X)
        if not old_sprint and new_sprint:
            sprint_changes[new_sprint]["added"].append(
                {"issue_key": issue_key, "timestamp": timestamp, "from": None}
            )

        # Case 2: Issue removed from sprint (Sprint X -> null)
        elif old_sprint and not new_sprint:
            sprint_changes[old_sprint]["removed"].append(
                {"issue_key": issue_key, "timestamp": timestamp, "to": None}
            )

        # Case 3: Issue moved between sprints (Sprint X -> Sprint Y)
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
    sprint_snapshot: Dict, sprint_start_date: Optional[str] = None
) -> Dict[str, int]:
    """Calculate sprint scope changes using snapshot data.

    Compares issues added/removed from sprint changelog to determine scope changes.
    More reliable than changelog-based detection as it uses actual snapshot data.

    Args:
        sprint_snapshot: Sprint snapshot from get_sprint_snapshots()
        sprint_start_date: Sprint start date (ISO format) - if provided, only counts
                          changes after this date

    Returns:
        Dict with scope change metrics:
        {
            "added": 3,      # Issues added after sprint started
            "removed": 2,    # Issues removed after sprint started
            "net_change": 1  # Net change (added - removed)
        }
    """
    added_issues = sprint_snapshot.get("added_issues", [])
    removed_issues = sprint_snapshot.get("removed_issues", [])

    # If sprint start date provided, filter to only changes after start
    if sprint_start_date:
        from dateutil import parser as date_parser

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


def calculate_sprint_progress(
    sprint_snapshot: Dict,
    flow_end_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
) -> Dict:
    """Calculate sprint progress metrics.

    Analyzes issue states to calculate completion percentage, story points
    progress, and issue breakdown by status.

    Args:
        sprint_snapshot: Sprint snapshot from get_sprint_snapshots()
        flow_end_statuses: List of statuses considered "done" (default: ["Done", "Closed"])
        flow_wip_statuses: List of statuses considered "in progress" (default: ["In Progress"])

    Returns:
        Progress metrics:
        {
            "total_issues": 10,
            "completed_issues": 7,
            "wip_issues": 2,
            "completion_pct": 70.0,
            "completion_percentage": 70.0,
            "total_points": 50.0,
            "completed_points": 35.0,
            "wip_points": 10.0,
            "points_completion_pct": 70.0,
            "points_completion_percentage": 70.0,
            "by_status": {
                "Done": {"count": 7, "points": 35.0},
                "In Progress": {"count": 2, "points": 10.0},
                "To Do": {"count": 1, "points": 5.0}
            },
            "by_issue_type": {
                "Story": {"count": 5, "points": 30.0},
                "Bug": {"count": 3, "points": 15.0},
                "Task": {"count": 2, "points": 5.0}
            }
        }
    """
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

    # Debug: Track which statuses are present but not counted as WIP
    all_statuses_in_sprint = set()
    wip_status_set = set(flow_wip_statuses)

    for issue_key, state in issue_states.items():
        status = state.get("status", "Unknown")
        story_points = state.get("story_points", 0) or 0
        issue_type = state.get("issue_type", "Unknown")

        all_statuses_in_sprint.add(status)

        # Count completion
        if status in flow_end_statuses:
            completed_issues += 1
            completed_points += story_points
        # Count WIP (in progress) - statuses between start and end
        elif status in flow_wip_statuses:
            wip_issues += 1
            wip_points += story_points

        # Aggregate totals
        total_points += story_points

        # Breakdown by status
        by_status[status]["count"] += 1
        by_status[status]["points"] += story_points

        # Breakdown by issue type
        by_issue_type[issue_type]["count"] += 1
        by_issue_type[issue_type]["points"] += story_points

    # Debug logging: Show statuses that exist but aren't in WIP config
    uncounted_wip_statuses = (
        all_statuses_in_sprint - wip_status_set - set(flow_end_statuses)
    )
    if uncounted_wip_statuses:
        logger.warning(
            f"Sprint has statuses not in WIP or End config: {uncounted_wip_statuses}. "
            f"WIP config: {flow_wip_statuses}, End config: {flow_end_statuses}"
        )

    # Calculate percentages
    completion_percentage = (
        (completed_issues / total_issues * 100.0) if total_issues > 0 else 0.0
    )
    points_completion_percentage = (
        (completed_points / total_points * 100.0) if total_points > 0 else 0.0
    )

    # Calculate to-do items (not started = total - wip - completed)
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
    issues: List[Dict],
    tracked_issue_types: Optional[List[str]] = None,
) -> List[Dict]:
    """Filter issues to tracked issue types (exclude sub-tasks).

    Args:
        issues: List of JIRA issues
        tracked_issue_types: Issue types to include (default: ["Story", "Task", "Bug"])

    Returns:
        Filtered list of issues excluding sub-tasks and other excluded types
    """
    if tracked_issue_types is None:
        tracked_issue_types = ["Story", "Task", "Bug"]

    filtered = []

    for issue in issues:
        # Extract issue type from nested fields or flat structure
        if "fields" in issue:
            issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "")
        else:
            issue_type = issue.get("issue_type", "")

        # Include only tracked issue types
        if issue_type in tracked_issue_types:
            filtered.append(issue)

    logger.info(
        f"Filtered {len(filtered)} issues from {len(issues)} total "
        f"(types: {tracked_issue_types})"
    )

    return filtered


def get_sprint_field_from_config(config: Dict) -> Optional[str]:
    """Extract sprint field ID from configuration.

    Args:
        config: App settings configuration dict

    Returns:
        Sprint field ID (e.g., "customfield_10020") or None if not configured
    """
    field_mappings = config.get("field_mappings", {})
    sprint_tracker_mappings = field_mappings.get("sprint_tracker", {})
    return sprint_tracker_mappings.get("sprint_field")


def calculate_issue_status_timeline(
    issue_key: str,
    changelog_entries: List[Dict],
    include_current: bool = True,
) -> List[Dict]:
    """Calculate time spent in each status as percentages for timeline visualization.

    This function creates timeline segments showing how an issue moved through
    different statuses over time, with each segment representing a percentage
    of total time spent.

    Args:
        issue_key: JIRA issue key
        changelog_entries: List of status changelog entries from database
        include_current: Whether to calculate time up to now for current status

    Returns:
        List of timeline segments:
        [
            {
                "status": "To Do",
                "start_time": datetime,
                "end_time": datetime,
                "duration_hours": 24.5,
                "duration_pct": 10.0,  # Percentage of total time
            },
            ...
        ]
        Empty list if no status changes found
    """
    from datetime import datetime, timezone

    # Filter to this issue's status changes
    issue_changes = [
        entry
        for entry in changelog_entries
        if entry.get("issue_key") == issue_key and entry.get("field_name") == "status"
    ]

    if not issue_changes:
        return []

    # Sort chronologically
    issue_changes.sort(key=lambda x: x.get("change_date", ""))

    # Build timeline segments
    segments = []
    for i, change in enumerate(issue_changes):
        status = change.get("new_value", "Unknown")
        change_date_str = change.get("change_date", "")

        try:
            start_time = datetime.fromisoformat(change_date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(
                f"Invalid date format for {issue_key}: {change_date_str}, skipping"
            )
            continue

        # Determine end time - next change or now
        if i < len(issue_changes) - 1:
            next_change_date_str = issue_changes[i + 1].get("change_date", "")
            try:
                end_time = datetime.fromisoformat(
                    next_change_date_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                logger.warning(
                    f"Invalid next date format for {issue_key}: {next_change_date_str}, using now"
                )
                end_time = datetime.now(timezone.utc)
        else:
            # Last change - use current time if include_current
            end_time = datetime.now(timezone.utc) if include_current else start_time

        # Calculate duration
        duration = end_time - start_time
        duration_hours = duration.total_seconds() / 3600

        segments.append(
            {
                "status": status,
                "start_time": start_time,
                "end_time": end_time,
                "duration_hours": duration_hours,
                "duration_pct": 0.0,  # Will calculate after total known
            }
        )

    # Calculate total time
    total_hours = sum(seg["duration_hours"] for seg in segments)

    # Calculate percentages
    if total_hours > 0:
        for seg in segments:
            seg["duration_pct"] = (seg["duration_hours"] / total_hours) * 100.0

    return segments
