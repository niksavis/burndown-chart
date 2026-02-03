"""Sprint Snapshot Calculator for daily sprint metrics.

This module generates daily sprint snapshots from changelog data to support
burnup charts and cumulative flow diagrams.

For each day in sprint:
- Calculate cumulative points completed (status in flow_end_statuses)
- Track current sprint scope (total points including adds/removes)
- Status distribution (count/points per status)

Reuses existing changelog_processor functions for state transitions.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


def calculate_daily_sprint_snapshots(
    sprint_data: Dict,
    issues: List[Dict],
    changelog_entries: List[Dict],
    sprint_start_date: str,
    sprint_end_date: str,
    flow_end_statuses: Optional[List[str]] = None,
    points_field: str = "story_points",
) -> List[Dict]:
    """Generate daily snapshots of sprint progress.

    Args:
        sprint_data: Sprint snapshot from sprint_manager.get_sprint_snapshots()
        issues: List of all JIRA issues
        changelog_entries: Changelog entries for status transitions
        sprint_start_date: ISO format sprint start date
        sprint_end_date: ISO format sprint end date
        flow_end_statuses: Statuses considered "completed" (default: ["Done", "Closed"])
        points_field: Field name for story points (default: "story_points")

    Returns:
        List of daily snapshots with structure:
        [
            {
                "date": "2026-02-03",
                "completed_points": 15,
                "total_scope": 45,
                "status_breakdown": {
                    "To Do": {"count": 3, "points": 10},
                    "In Progress": {"count": 2, "points": 8},
                    "Done": {"count": 5, "points": 15}
                },
                "completed_count": 5,
                "total_count": 10
            },
            ...
        ]
    """
    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed"]

    # Parse sprint dates
    try:
        start_dt = datetime.fromisoformat(sprint_start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(sprint_end_date.replace("Z", "+00:00"))

        # Ensure timezone aware
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse sprint dates: {e}")
        return []

    # Get current sprint issues
    current_issues = sprint_data.get("current_issues", [])
    if not current_issues:
        logger.warning("No issues in sprint")
        return []

    # Build issue lookup
    issue_map = {
        issue["key"]: issue for issue in issues if issue["key"] in current_issues
    }

    # Build changelog lookup by issue key
    changelog_by_issue = defaultdict(list)
    for entry in changelog_entries:
        issue_key = entry.get("issue_key")
        if issue_key in current_issues:
            changelog_by_issue[issue_key].append(entry)

    # Track sprint scope changes (issues added/removed during sprint)
    added_issues = sprint_data.get("added_issues", [])
    removed_issues = sprint_data.get("removed_issues", [])

    # Build timeline of scope changes
    scope_timeline = []
    for item in added_issues:
        try:
            ts = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            scope_timeline.append(
                {"timestamp": ts, "issue_key": item["issue_key"], "action": "add"}
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse added issue timestamp: {e}")

    for item in removed_issues:
        try:
            ts = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            scope_timeline.append(
                {"timestamp": ts, "issue_key": item["issue_key"], "action": "remove"}
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse removed issue timestamp: {e}")

    # Sort scope timeline by timestamp
    scope_timeline.sort(key=lambda x: x["timestamp"])

    # Generate daily snapshots
    snapshots = []
    current_date = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Track which issues are in scope on each day
    issues_in_scope = set(current_issues)

    # Apply scope changes before sprint start
    for change in scope_timeline:
        if change["timestamp"] < start_dt:
            if change["action"] == "add":
                issues_in_scope.add(change["issue_key"])
            elif change["action"] == "remove":
                issues_in_scope.discard(change["issue_key"])

    scope_change_idx = 0

    while current_date <= end_date:
        # Apply scope changes for this day
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

        # Calculate metrics for this day
        completed_points = 0
        completed_count = 0
        total_points = 0
        total_count = 0
        status_breakdown = defaultdict(lambda: {"count": 0, "points": 0})

        for issue_key in issues_in_scope:
            issue = issue_map.get(issue_key)
            if not issue:
                continue

            # Get issue status at this timestamp
            issue_changelog = changelog_by_issue.get(issue_key, [])
            status_at_time = get_status_at_timestamp(
                issue, current_date, issue_changelog
            )

            if not status_at_time:
                # Use current status if no changelog
                status_at_time = issue.get("status", "Unknown")

            # Get story points
            points = issue.get(points_field, 0) or 0

            # Update totals
            total_count += 1
            total_points += points

            # Update status breakdown
            status_breakdown[status_at_time]["count"] += 1
            status_breakdown[status_at_time]["points"] += points

            # Check if completed
            if status_at_time in flow_end_statuses:
                completed_count += 1
                completed_points += points

        # Create snapshot
        snapshot = {
            "date": current_date.date().isoformat(),
            "completed_points": completed_points,
            "total_scope": total_points,
            "status_breakdown": dict(status_breakdown),
            "completed_count": completed_count,
            "total_count": total_count,
        }
        snapshots.append(snapshot)

        # Move to next day
        current_date += timedelta(days=1)

    logger.info(f"Generated {len(snapshots)} daily snapshots for sprint")
    return snapshots


def get_status_at_timestamp(
    issue: Dict, timestamp: datetime, changelog: List[Dict]
) -> Optional[str]:
    """Get issue status at a specific timestamp.

    Args:
        issue: JIRA issue dictionary
        timestamp: Datetime to check status at
        changelog: Issue's changelog entries (sorted chronologically)

    Returns:
        Status name at the given timestamp, or current status if timestamp is after all changes
    """
    if not changelog:
        # No changelog, return current status
        return issue.get("status")

    # Sort changelog by timestamp (should already be sorted)
    sorted_changelog = sorted(
        changelog,
        key=lambda x: datetime.fromisoformat(
            x.get("timestamp", "1970-01-01").replace("Z", "+00:00")
        ),
    )

    # Find the last status change before or at the target timestamp
    last_status = None

    for entry in sorted_changelog:
        try:
            entry_time = datetime.fromisoformat(
                entry.get("timestamp", "").replace("Z", "+00:00")
            )
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)

            if entry_time > timestamp:
                # This change happened after our target time
                break

            # Get the status AFTER this change
            to_status = entry.get("to_value")
            if to_status:
                last_status = to_status
        except (ValueError, AttributeError):
            continue

    # If we found a status change before the timestamp, return it
    if last_status:
        return last_status

    # Otherwise, check if there's a "from" status in the first entry
    # (this would be the status before any changes)
    if sorted_changelog:
        first_from = sorted_changelog[0].get("from_value")
        if first_from:
            return first_from

    # Fallback to current status
    return issue.get("status")
