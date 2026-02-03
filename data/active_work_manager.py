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
    data_points_count: int = 30,
    flow_end_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
) -> List[Dict]:
    """Filter issues to data points date range.

    Returns:
    - All issues with activity (created or updated) within data_points_count days
    - Includes both WIP and completed issues

    Args:
        issues: List of JIRA issues
        data_points_count: Number of days to look back (from Data Points slider)
        flow_end_statuses: Completion statuses
        flow_wip_statuses: WIP statuses

    Returns:
        List of filtered issues
    """
    from datetime import datetime, timedelta, timezone

    if not flow_end_statuses:
        flow_end_statuses = ["Done", "Closed", "Resolved"]
    if not flow_wip_statuses:
        flow_wip_statuses = ["In Progress", "In Review", "Testing", "To Do", "Backlog"]

    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=data_points_count)

    logger.info(
        f"Filtering issues with activity since {cutoff_date.date()} ({data_points_count} days)"
    )

    filtered_issues = []

    for issue in issues:
        # Check both created and updated dates
        created_str = issue.get("created")
        updated_str = issue.get("updated")

        try:
            # Parse created date
            created_dt = None
            if created_str:
                if created_str.endswith("Z"):
                    created_str = created_str[:-1] + "+00:00"
                created_dt = datetime.fromisoformat(created_str)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)

            # Parse updated date
            updated_dt = None
            if updated_str:
                if updated_str.endswith("Z"):
                    updated_str = updated_str[:-1] + "+00:00"
                updated_dt = datetime.fromisoformat(updated_str)
                if updated_dt.tzinfo is None:
                    updated_dt = updated_dt.replace(tzinfo=timezone.utc)

            # Include if created or updated within data points range
            if (created_dt and created_dt >= cutoff_date) or (updated_dt and updated_dt >= cutoff_date):
                filtered_issues.append(issue)

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse date for {issue.get('issue_key')}: {e}")
            continue

    logger.info(f"Filtered to {len(filtered_issues)} issues within {data_points_count} days")

    return filtered_issues


def get_active_work_data(
    issues: List[Dict],
    backend=None,
    profile_id: Optional[str] = None,
    query_id: Optional[str] = None,
    data_points_count: int = 30,
    parent_field: str = "parent",
    flow_end_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
) -> Dict:
    """Get active work data with nested epic timeline.

    Returns:
    {
        "timeline": [
            {
                "epic_key": "A942-3407",
                "epic_summary": "Feature Name",
                "total_issues": 9,
                "completed_issues": 5,
                "completion_pct": 55.6,
                "child_issues": [issues sorted by priority],  # New: nested issues
            }
        ]
    }

    Args:
        issues: List of JIRA issues
        data_points_count: Number of days to look back (from Data Points slider)
        parent_field: Field name for parent/epic
        flow_end_statuses: Completion statuses
        flow_wip_statuses: WIP statuses

    Returns:
        Dict with nested epic timeline
    """
    logger.info(f"[ACTIVE WORK MGR] Building active work data from {len(issues)} issues")
    logger.info(f"[ACTIVE WORK MGR] data_points_count={data_points_count}, parent_field={parent_field}")

    # Filter to date range
    filtered_issues = filter_active_issues(
        issues, data_points_count, flow_end_statuses, flow_wip_statuses
    )
    
    logger.info(f"[ACTIVE WORK MGR] After filtering: {len(filtered_issues)} issues within {data_points_count} days")

    if not filtered_issues:
        logger.warning("[ACTIVE WORK MGR] No issues found after filtering")
        return {"timeline": []}

    # Add health indicators to each issue
    issues_with_health = [
        _add_health_indicators(
            issue, backend, profile_id, query_id, flow_end_statuses, flow_wip_statuses
        )
        for issue in filtered_issues
    ]

    # Build epic timeline with nested issues
    timeline = _build_epic_timeline(
        issues_with_health, backend, profile_id, query_id, parent_field, flow_end_statuses, flow_wip_statuses
    )

    return {"timeline": timeline}


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
    issue: Dict,
    backend,
    profile_id: Optional[str],
    query_id: Optional[str],
    flow_end_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
) -> Dict:
    """Add health indicators based on status change velocity.

    Health indicators:
    - is_blocked: Status unchanged for 5+ days (not done)
    - is_aging: Status unchanged for 3-5 days (not done, not blocked)
    - is_wip: In WIP status and status changed in last 2 days
    - is_completed: In completion status

    Args:
        issue: Issue dict
        backend: Database backend for changelog access
        profile_id: Profile ID
        query_id: Query ID
        flow_end_statuses: Completion statuses
        flow_wip_statuses: WIP statuses

    Returns:
        Issue dict with health_indicators added
    """
    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]
    if flow_wip_statuses is None:
        flow_wip_statuses = []

    now = datetime.now(timezone.utc)
    status = issue.get("status", "Unknown")
    is_completed = status in flow_end_statuses
    
    # Check if in WIP status
    is_in_wip_status = _is_wip_status_check(status, flow_wip_statuses)

    # Default values
    is_blocked = False
    is_aging = False
    is_wip = False
    days_since_status_change = None

    # Get last status change from changelog
    if backend and profile_id and query_id and not is_completed:
        try:
            issue_key = issue.get("issue_key")
            if issue_key:
                # Get status changes for this issue
                changelog = backend.get_changelog_entries(
                    profile_id=profile_id,
                    query_id=query_id,
                    issue_key=issue_key,
                    field_name="status",
                )
                
                if changelog:
                    # Get most recent status change
                    latest_change = changelog[0]  # Already ordered by change_date DESC
                    change_date_str = latest_change.get("change_date")
                    
                    if change_date_str:
                        try:
                            if change_date_str.endswith("Z"):
                                change_date_str = change_date_str[:-1] + "+00:00"
                            change_dt = datetime.fromisoformat(change_date_str)
                            if change_dt.tzinfo is None:
                                change_dt = change_dt.replace(tzinfo=timezone.utc)
                            
                            days_since_status_change = (now - change_dt).days
                            
                            # Apply new logic based on status change velocity
                            if days_since_status_change >= 5:
                                is_blocked = True  # Stuck for 5+ days
                            elif days_since_status_change >= 3:
                                is_aging = True  # Approaching blocked (3-5 days)
                            elif is_in_wip_status and days_since_status_change <= 2:
                                is_wip = True  # Active work (changed recently)
                                
                        except (ValueError, AttributeError) as e:
                            logger.debug(f"Could not parse status change date for {issue_key}: {e}")
                else:
                    # No status changes in changelog - use created date as fallback
                    created_str = issue.get("created")
                    if created_str:
                        try:
                            if created_str.endswith("Z"):
                                created_str = created_str[:-1] + "+00:00"
                            created_dt = datetime.fromisoformat(created_str)
                            if created_dt.tzinfo is None:
                                created_dt = created_dt.replace(tzinfo=timezone.utc)
                            days_since_created = (now - created_dt).days
                            
                            if days_since_created >= 5:
                                is_blocked = True
                            elif days_since_created >= 3:
                                is_aging = True
                        except (ValueError, AttributeError):
                            pass
                            
        except Exception as e:
            logger.warning(f"Failed to get changelog for {issue.get('issue_key')}: {e}")
            # Fallback to old logic if changelog fails
            pass

    # Add health indicators to issue (don't modify original)
    issue_with_health = {**issue}
    issue_with_health["health_indicators"] = {
        "is_blocked": is_blocked,
        "is_aging": is_aging,
        "is_wip": is_wip,
        "is_completed": is_completed,
    }

    return issue_with_health


def _is_wip_status_check(status: str, flow_wip_statuses: List[str]) -> bool:
    """Check if status is work-in-progress.
    
    Args:
        status: Issue status
        flow_wip_statuses: List of configured WIP statuses
        
    Returns:
        True if status is considered WIP
    """
    # First check configured WIP statuses
    if flow_wip_statuses and status in flow_wip_statuses:
        return True
    
    # Fallback: check for WIP keywords in status name
    status_lower = status.lower()
    wip_keywords = ["progress", "review", "testing", "development", "deployment", "deploying"]
    return any(kw in status_lower for kw in wip_keywords)


def _build_epic_timeline(
    issues: List[Dict],
    backend,
    profile_id: Optional[str],
    query_id: Optional[str],
    parent_field: str,
    flow_end_statuses: Optional[List[str]],
    flow_wip_statuses: Optional[List[str]],
) -> List[Dict]:
    """Build epic timeline aggregation from issues.

    Args:
        issues: All active issues
        backend: Database backend for fetching epic details
        profile_id: Profile ID
        query_id: Query ID
        parent_field: Field name for parent/epic
        flow_end_statuses: Completion statuses
        flow_wip_statuses: WIP statuses

    Returns:
        List of epic summaries for timeline visualization
    """
    epics = defaultdict(list)

    # Group by parent
    for issue in issues:
        # Parent field can be at top level or in custom_fields
        parent = issue.get(parent_field)
        if not parent and parent_field.startswith("customfield_"):
            # Check in custom_fields dict for JIRA custom fields
            custom_fields = issue.get("custom_fields", {})
            parent = custom_fields.get(parent_field)
        
        parent_key = None
        
        if parent:
            if isinstance(parent, dict):
                # Parent is dict like {"key": "PROJ-123", "summary": "Epic Name"}
                parent_key = parent.get("key")
            elif isinstance(parent, str):
                # Parent is string like "PROJ-123"
                parent_key = parent
        
        if not parent_key:
            parent_key = "No Parent"

        epics[parent_key].append(issue)

    # Build epic summaries with sorted child issues
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
            if not parent and parent_field.startswith("customfield_"):
                custom_fields = first_issue.get("custom_fields", {})
                parent = custom_fields.get(parent_field)
            
            if isinstance(parent, dict):
                # Extract summary from parent dict
                epic_summary = parent.get("summary", parent.get("fields", {}).get("summary", epic_key))
            elif isinstance(parent, str):
                # Parent is just a key string - try to find the epic in our issues list
                epic_issue = next((issue for issue in issues if issue.get("issue_key") == parent), None)
                if epic_issue:
                    epic_summary = epic_issue.get("summary", epic_key)
                else:
                    # Epic not in filtered issues - fetch from backend
                    if backend and profile_id and query_id:
                        try:
                            all_issues = backend.get_issues(profile_id, query_id)
                            epic_issue = next((issue for issue in all_issues if issue.get("issue_key") == parent), None)
                            if epic_issue:
                                epic_summary = epic_issue.get("summary", epic_key)
                            else:
                                logger.warning(f"Epic {parent} not found in database")
                                epic_summary = epic_key  # Use key as last resort
                        except Exception as e:
                            logger.error(f"Failed to fetch epic {parent}: {e}")
                            epic_summary = epic_key
                    else:
                        epic_summary = epic_key
            else:
                epic_summary = epic_key

        # Sort child issues: Blocked → Aging → WIP → To Do → Completed
        def sort_priority(issue):
            status = issue.get("status", "Unknown")
            health = issue.get("health_indicators", {})
            
            # Priority 1: Blocked (highest alert)
            if health.get("is_blocked"):
                return (1, status)
            # Priority 2: Aging (needs attention)
            elif health.get("is_aging"):
                return (2, status)
            # Priority 3: WIP statuses
            elif flow_wip_statuses and status in flow_wip_statuses:
                return (3, status)
            # Priority 4: To Do (not WIP, not completed)
            elif not (flow_end_statuses and status in flow_end_statuses):
                return (4, status)
            # Priority 5: Completed (lowest priority)
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
                "child_issues": sorted_child_issues,  # Include sorted child issues
            }
        )

    # Sort epics by completion % (active first)
    timeline.sort(key=lambda x: x["completion_pct"])

    logger.info(f"Built timeline with {len(timeline)} epics")
    return timeline
