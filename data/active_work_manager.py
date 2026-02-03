"""Active Work Timeline Manager for Epic/Feature tracking.

This module provides functions for the Active Work tab showing:
- Timeline visualization of active epics/features
- Issue lists for last week and this week (2-week window)
- Health indicators on individual issues (blocked, aging, at-risk)

Focuses on items being actively worked on, not just updated.

Key Functions:
    get_active_work_data() -> Dict: Main function returning timeline + issue lists
    add_health_indicators() -> List[Dict]: Add health signals to issues
    filter_recent_activity() -> List[Dict]: Filter issues to recent updates
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict

logger = logging.getLogger(__name__)


def filter_active_issues(
    issues: List[Dict],
    flow_end_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
) -> Dict[str, List[Dict]]:
    """Filter to active WIP issues + completed from last 2 weeks.

    Returns issues grouped by timeframe:
    - All WIP issues (to do, in progress) regardless of age
    - Completed issues from last 2 weeks only
    - Grouped into: last_week, this_week

    Args:
        issues: List of JIRA issues
        flow_end_statuses: Completion statuses
        flow_wip_statuses: WIP statuses

    Returns:
        Dict with 'last_week' and 'this_week' issue lists
    """
    from datetime import datetime, timedelta, timezone

    if not flow_end_statuses:
        flow_end_statuses = ["Done", "Closed", "Resolved"]
    if not flow_wip_statuses:
        flow_wip_statuses = ["In Progress", "In Review", "Testing", "To Do", "Backlog"]

    now = datetime.now(timezone.utc)

    # Calculate week boundaries (Monday to Sunday)
    days_since_monday = now.weekday()  # 0=Monday, 6=Sunday
    this_week_start = (now - timedelta(days=days_since_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    last_week_start = this_week_start - timedelta(days=7)
    two_weeks_ago = this_week_start - timedelta(days=14)

    logger.info(
        f"Filtering issues: last_week={last_week_start.date()}, "
        f"this_week={this_week_start.date()}, two_weeks_ago={two_weeks_ago.date()}"
    )

    last_week_issues = []
    this_week_issues = []

    for issue in issues:
        status = issue.get("status", "Unknown")
        updated_str = issue.get("updated")

        if not updated_str:
            continue

        try:
            # Parse ISO format
            if updated_str.endswith("Z"):
                updated_str = updated_str[:-1] + "+00:00"
            updated_dt = datetime.fromisoformat(updated_str)
            if updated_dt.tzinfo is None:
                updated_dt = updated_dt.replace(tzinfo=timezone.utc)

            # Include if:
            # 1. WIP status (any age)
            # 2. Completed in last 2 weeks
            is_completed = status in flow_end_statuses
            is_wip = not is_completed  # Everything not done is WIP

            if is_completed and updated_dt < two_weeks_ago:
                # Completed too long ago, skip
                continue

            # Group by week based on update time
            if updated_dt >= this_week_start:
                this_week_issues.append(issue)
            elif updated_dt >= last_week_start:
                last_week_issues.append(issue)
            elif is_wip:
                # WIP but no recent update - put in this week
                this_week_issues.append(issue)

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse date for {issue.get('issue_key')}: {e}")
            continue

    logger.info(
        f"Filtered to {len(last_week_issues)} last week issues, "
        f"{len(this_week_issues)} this week issues"
    )

    return {"last_week": last_week_issues, "this_week": this_week_issues}


def get_active_work_data(
    issues: List[Dict],
    parent_field: str = "parent",
    flow_end_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
) -> Dict:
    """Get active work data with timeline and issue lists.

    Returns:
    {
        "timeline": [epic summaries for visualization],
        "last_week_issues": [issues with health indicators],
        "this_week_issues": [issues with health indicators],
    }

    Args:
        issues: List of JIRA issues
        parent_field: Field name for parent/epic
        flow_end_statuses: Completion statuses
        flow_wip_statuses: WIP statuses

    Returns:
        Dict with timeline and issue lists
    """
    logger.info(f"Building active work data from {len(issues)} issues")

    # Filter to WIP + recent completions
    filtered = filter_active_issues(issues, flow_end_statuses, flow_wip_statuses)
    last_week_issues = filtered["last_week"]
    this_week_issues = filtered["this_week"]

    all_active_issues = last_week_issues + this_week_issues

    if not all_active_issues:
        logger.info("No active issues found")
        return {
            "timeline": [],
            "last_week_issues": [],
            "this_week_issues": [],
        }

    # Add health indicators to each issue
    last_week_with_health = [
        _add_health_indicators(issue, flow_end_statuses) for issue in last_week_issues
    ]
    this_week_with_health = [
        _add_health_indicators(issue, flow_end_statuses) for issue in this_week_issues
    ]

    # Build epic timeline aggregation
    timeline = _build_epic_timeline(
        all_active_issues, parent_field, flow_end_statuses, flow_wip_statuses
    )

    return {
        "timeline": timeline,
        "last_week_issues": last_week_with_health,
        "this_week_issues": this_week_with_health,
    }


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


def _add_health_indicators(
    issue: Dict, flow_end_statuses: Optional[List[str]] = None
) -> Dict:
    """Add health indicators to individual issue.

    Health indicators:
    - is_blocked: No update in 5+ days (and not done)
    - is_aging: Issue is 14+ days old (and not done)
    - is_completed: In completion status

    Args:
        issue: Issue dict
        flow_end_statuses: Completion statuses

    Returns:
        Issue dict with health_indicators added
    """
    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]

    now = datetime.now(timezone.utc)
    status = issue.get("status", "Unknown")
    is_completed = status in flow_end_statuses

    # Check blocked (no update in 5+ days, not done)
    is_blocked = False
    if not is_completed:
        updated_str = issue.get("updated")
        if updated_str:
            try:
                if updated_str.endswith("Z"):
                    updated_str = updated_str[:-1] + "+00:00"
                updated_dt = datetime.fromisoformat(updated_str)
                if updated_dt.tzinfo is None:
                    updated_dt = updated_dt.replace(tzinfo=timezone.utc)
                days_since_update = (now - updated_dt).days
                is_blocked = days_since_update >= 5
            except (ValueError, AttributeError):
                pass

    # Check aging (14+ days old, not done)
    is_aging = False
    if not is_completed:
        created_str = issue.get("created")
        if created_str:
            try:
                if created_str.endswith("Z"):
                    created_str = created_str[:-1] + "+00:00"
                created_dt = datetime.fromisoformat(created_str)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                days_old = (now - created_dt).days
                is_aging = days_old >= 14
            except (ValueError, AttributeError):
                pass

    # Add health indicators to issue (don't modify original)
    issue_with_health = {**issue}
    issue_with_health["health_indicators"] = {
        "is_blocked": is_blocked,
        "is_aging": is_aging,
        "is_completed": is_completed,
    }

    return issue_with_health


def _build_epic_timeline(
    issues: List[Dict],
    parent_field: str,
    flow_end_statuses: Optional[List[str]],
    flow_wip_statuses: Optional[List[str]],
) -> List[Dict]:
    """Build epic timeline aggregation from issues.

    Args:
        issues: All active issues
        parent_field: Field name for parent/epic
        flow_end_statuses: Completion statuses
        flow_wip_statuses: WIP statuses

    Returns:
        List of epic summaries for timeline visualization
    """
    epics = defaultdict(list)

    # Group by parent
    for issue in issues:
        parent = issue.get(parent_field)
        if parent:
            if isinstance(parent, dict):
                parent_key = parent.get("key")
            else:
                parent_key = parent
        else:
            parent_key = "No Parent"

        epics[parent_key].append(issue)

    # Build epic summaries
    timeline = []
    for epic_key, child_issues in epics.items():
        if not child_issues:
            continue

        progress = calculate_epic_progress(
            child_issues, flow_end_statuses, flow_wip_statuses
        )

        # Get epic summary (from first child's parent field)
        epic_summary = "Unknown"
        if epic_key != "No Parent":
            first_issue = child_issues[0]
            parent = first_issue.get(parent_field)
            if isinstance(parent, dict):
                epic_summary = parent.get("summary", epic_key)
            else:
                epic_summary = epic_key

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
            }
        )

    # Sort by completion %
    timeline.sort(key=lambda x: x["completion_pct"], reverse=True)

    logger.info(f"Built timeline with {len(timeline)} epics")
    return timeline
