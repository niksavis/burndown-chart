"""Active Work Timeline Manager for Epic/Feature tracking.

This module aggregates issues by their parent epic/feature and filters to
recent activity (last 7 days + current week) to show active work in progress.

Uses existing parent field data from JIRA fetch - no new API calls needed.
Parent field is populated via base_fields in main_fetch.py.

Key Functions:
    get_active_epics() -> List[Dict]: Get epics/features with recent activity
    calculate_epic_progress() -> Dict: Calculate completion metrics per epic
    filter_recent_activity() -> List[Dict]: Filter issues to recent updates
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict

logger = logging.getLogger(__name__)


def filter_recent_activity(
    issues: List[Dict], days_back: int = 7, include_current_week: bool = True
) -> List[Dict]:
    """Filter issues to those with recent activity.

    Recent activity includes:
    - Issues updated in last N days
    - Issues in current week (Mon-Sun) if include_current_week=True

    Args:
        issues: List of JIRA issues (from backend.get_issues())
        days_back: Number of days to look back (default: 7)
        include_current_week: Include all issues from current calendar week

    Returns:
        Filtered list of issues with recent activity
    """
    logger.info(
        f"Filtering {len(issues)} issues for recent activity "
        f"(days_back={days_back}, include_current_week={include_current_week})"
    )

    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=days_back)

    # Calculate start of current week (Monday 00:00)
    week_start = None
    if include_current_week:
        days_since_monday = now.weekday()  # Monday=0, Sunday=6
        week_start = now - timedelta(
            days=days_since_monday,
            hours=now.hour,
            minutes=now.minute,
            seconds=now.second,
            microseconds=now.microsecond,
        )

    recent_issues = []

    for issue in issues:
        # Get updated timestamp (backend stores as 'updated' field)
        updated_str = issue.get("updated")

        if not updated_str:
            continue

        try:
            # Parse ISO format timestamp
            # Handle both with and without timezone info
            if updated_str.endswith("Z"):
                updated_dt = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            elif "+" in updated_str or updated_str.count("-") > 2:
                updated_dt = datetime.fromisoformat(updated_str)
            else:
                # No timezone, assume UTC
                updated_dt = datetime.fromisoformat(updated_str).replace(
                    tzinfo=timezone.utc
                )

            # Check if within timeframe
            is_recent = updated_dt >= cutoff_date
            is_current_week = week_start and updated_dt >= week_start

            if is_recent or is_current_week:
                recent_issues.append(issue)

        except (ValueError, AttributeError) as e:
            logger.warning(
                f"Failed to parse updated date for issue {issue.get('issue_key')}: "
                f"{updated_str} - {e}"
            )
            continue

    logger.info(
        f"Found {len(recent_issues)} issues with recent activity "
        f"(cutoff: {cutoff_date.isoformat()})"
    )

    return recent_issues


def get_active_epics(
    issues: List[Dict],
    days_back: int = 7,
    include_current_week: bool = True,
    parent_field: str = "parent",
) -> List[Dict]:
    """Get epics/features with recent activity.

    Groups issues by parent epic/feature and calculates progress metrics.
    Only includes epics that have child issues with recent activity.

    Args:
        issues: List of JIRA issues (from backend.get_issues())
        days_back: Number of days to look back for activity (default: 7)
        include_current_week: Include issues from current calendar week
        parent_field: Field name for parent/epic (e.g., 'parent' or 'customfield_10006')

    Returns:
        List of epic dictionaries with structure:
        [
            {
                "epic_key": "PROJ-123",
                "epic_summary": "User Authentication Feature",
                "total_issues": 8,
                "completed_issues": 3,
                "in_progress_issues": 4,
                "todo_issues": 1,
                "total_points": 21.0,
                "completed_points": 8.0,
                "completion_pct": 38.1,
                "recent_activity_count": 5,
                "last_updated": "2026-02-03T15:30:00Z",
                "child_issues": [
                    {
                        "issue_key": "PROJ-124",
                        "summary": "Login API endpoint",
                        "status": "In Progress",
                        "points": 5.0,
                        "updated": "2026-02-03T15:30:00Z"
                    },
                    ...
                ]
            },
            ...
        ]
    """
    logger.info(
        f"Building active epic timeline from {len(issues)} issues "
        f"(days_back={days_back}, include_current_week={include_current_week})"
    )

    # Filter to issues with recent activity
    recent_issues = filter_recent_activity(
        issues, days_back=days_back, include_current_week=include_current_week
    )

    if not recent_issues:
        logger.info("No issues with recent activity found")
        return []

    # Group issues by parent epic/feature
    epics_map = defaultdict(list)
    orphan_issues = []  # Issues without parent

    for issue in recent_issues:
        # Extract parent from custom_fields using configurable parent_field
        custom_fields = issue.get("custom_fields", {})
        parent_value = custom_fields.get(parent_field)

        # Parent can be:
        # - Dict: {"key": "PROJ-123", "fields": {"summary": "..."}}
        # - String: "PROJ-123"
        # - None: no parent

        parent_key = None
        if isinstance(parent_value, dict):
            parent_key = parent_value.get("key")
        elif isinstance(parent_value, str):
            parent_key = parent_value

        if parent_key:
            epics_map[parent_key].append(issue)
        else:
            orphan_issues.append(issue)

    if orphan_issues:
        logger.info(
            f"Found {len(orphan_issues)} issues without parent epic "
            "(will not appear in timeline)"
        )

    # Build epic progress data
    active_epics = []

    for epic_key, child_issues in epics_map.items():
        # Calculate progress metrics
        progress = calculate_epic_progress(child_issues)

        # Get epic summary from first child's parent field
        # (JIRA parent field includes summary in nested structure)
        epic_summary = "Unknown Epic"
        first_issue = child_issues[0]
        parent_value = first_issue.get("custom_fields", {}).get(parent_field)
        if isinstance(parent_value, dict):
            epic_summary = parent_value.get("fields", {}).get("summary", epic_summary)

        # Find most recent update time
        last_updated = None
        for issue in child_issues:
            updated_str = issue.get("updated")
            if updated_str and (not last_updated or updated_str > last_updated):
                last_updated = updated_str

        # Build child issue summaries
        child_summaries = []
        for issue in child_issues:
            child_summaries.append(
                {
                    "issue_key": issue.get("issue_key"),
                    "summary": issue.get("summary", ""),
                    "status": issue.get("status", "Unknown"),
                    "points": issue.get("points", 0.0),
                    "updated": issue.get("updated"),
                }
            )

        active_epics.append(
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
                "recent_activity_count": len(child_issues),
                "last_updated": last_updated,
                "child_issues": child_summaries,
            }
        )

    # Sort by most recent activity
    active_epics.sort(key=lambda x: x["last_updated"] or "", reverse=True)

    logger.info(f"Found {len(active_epics)} active epics/features with recent activity")

    return active_epics


def calculate_epic_progress(
    child_issues: List[Dict],
    flow_end_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
) -> Dict:
    """Calculate progress metrics for an epic based on child issues.

    Args:
        child_issues: List of issues that belong to the epic
        flow_end_statuses: Statuses that indicate completion (default: ["Done"])
        flow_wip_statuses: Statuses that indicate work in progress

    Returns:
        Dict with progress metrics:
        {
            "total_issues": 8,
            "completed_issues": 3,
            "in_progress_issues": 4,
            "todo_issues": 1,
            "total_points": 21.0,
            "completed_points": 8.0,
            "completion_pct": 38.1,
            "by_status": {
                "Done": {"count": 3, "points": 8.0},
                "In Progress": {"count": 4, "points": 12.0},
                "To Do": {"count": 1, "points": 1.0}
            }
        }
    """
    # Default statuses if not provided
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

        # Categorize by status
        if status in flow_end_statuses:
            completed_issues += 1
            completed_points += points
        elif status in flow_wip_statuses:
            in_progress_issues += 1
        else:
            todo_issues += 1

        # Aggregate totals
        total_points += points

        # Breakdown by status
        by_status[status]["count"] += 1
        by_status[status]["points"] += points

    # Calculate completion percentage
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
