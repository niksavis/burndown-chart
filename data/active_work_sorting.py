"""Sorting helpers for Active Work epics."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def is_epic_completed(epic: Dict[str, Any]) -> bool:
    """Return True when an epic is fully completed."""
    total_issues = int(epic.get("total_issues", 0) or 0)
    completed_issues = int(epic.get("completed_issues", 0) or 0)
    return total_issues > 0 and completed_issues == total_issues


def get_epic_health_priority(epic: Dict[str, Any]) -> int:
    """Return health priority for an epic based on child issue signals.

    Priority: 1=blocked, 2=aging, 3=wip, 4=none.
    """
    child_issues = epic.get("child_issues", [])
    if not isinstance(child_issues, list):
        return 4

    health_flags: List[Dict[str, Any]] = [
        issue.get("health_indicators", {}) for issue in child_issues
    ]

    if any(flags.get("is_blocked") for flags in health_flags):
        return 1
    if any(flags.get("is_aging") for flags in health_flags):
        return 2
    if any(flags.get("is_wip") for flags in health_flags):
        return 3
    return 4


def get_epic_sort_key(epic: Dict[str, Any]) -> Tuple[int, float, int]:
    """Sort non-completed epics first, then by completion %, then health."""
    completion_pct = float(epic.get("completion_pct", 0.0) or 0.0)
    completed_flag = 1 if is_epic_completed(epic) else 0
    health_priority = get_epic_health_priority(epic)
    return (completed_flag, -completion_pct, health_priority)
