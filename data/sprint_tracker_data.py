"""Shared Sprint Tracker data loading with short-lived in-memory caching.

This module centralizes repeated Sprint Tracker reads used by callbacks to reduce
redundant backend calls during sprint/filters/chart interactions.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from data.issue_filtering import filter_issues_for_metrics
from data.persistence import load_app_settings
from data.persistence.factory import get_backend
from data.sprint_manager import (
    _parse_sprint_object,
    build_issue_state_lookup,
    filter_sprint_issues,
    get_sprint_snapshots,
)

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 10
_SPRINT_TRACKER_CACHE: dict[tuple[str, str, str], dict] = {}


def _cache_valid(cached_at: datetime) -> bool:
    return datetime.now(UTC) - cached_at <= timedelta(seconds=_CACHE_TTL_SECONDS)


def _extract_sprint_metadata(issues: list[dict], sprint_field: str) -> dict[str, dict]:
    metadata: dict[str, dict] = {}

    for issue in issues:
        custom_fields = issue.get("custom_fields", {})
        sprint_field_value = custom_fields.get(sprint_field)

        if not sprint_field_value:
            continue

        sprint_list = (
            sprint_field_value
            if isinstance(sprint_field_value, list)
            else [sprint_field_value]
        )

        for sprint_obj_str in sprint_list:
            if not sprint_obj_str or not isinstance(sprint_obj_str, str):
                continue

            sprint_obj = _parse_sprint_object(sprint_obj_str)
            if sprint_obj and sprint_obj.get("name"):
                sprint_name = sprint_obj["name"]
                metadata[sprint_name] = {
                    "state": sprint_obj.get("state", ""),
                    "start_date": sprint_obj.get("start_date"),
                    "end_date": sprint_obj.get("end_date"),
                }

    return metadata


def load_sprint_tracker_dataset(
    active_profile_id: str,
    active_query_id: str,
    issue_type_filter: str = "all",
    force_refresh: bool = False,
) -> dict:
    """Load sprint tracker dataset with short-lived caching.

    Args:
        active_profile_id: Active profile identifier
        active_query_id: Active query identifier
        issue_type_filter: all|Story|Task|Bug
        force_refresh: bypass cache when True

    Returns:
        Dict containing settings, issues, snapshots, and changelog payloads.
    """
    cache_key = (active_profile_id, active_query_id, issue_type_filter)
    cache_entry = _SPRINT_TRACKER_CACHE.get(cache_key)
    if (
        not force_refresh
        and cache_entry
        and _cache_valid(cache_entry.get("cached_at", datetime.min.replace(tzinfo=UTC)))
    ):
        return cache_entry["payload"]

    backend = get_backend()
    settings = load_app_settings()

    all_issues = backend.get_issues(active_profile_id, active_query_id)
    all_issues = filter_issues_for_metrics(
        all_issues,
        settings=settings,
        log_prefix="SPRINT DATASET",
    )

    tracked_types = ["Story", "Task", "Bug"]
    if issue_type_filter != "all":
        tracked_types = [issue_type_filter]

    tracked_issues = filter_sprint_issues(all_issues, tracked_issue_types=tracked_types)
    all_issue_states = build_issue_state_lookup(tracked_issues)

    field_mappings = settings.get("field_mappings", {})
    general_mappings = field_mappings.get("general", {})
    sprint_field = general_mappings.get("sprint_field")

    sprint_changelog: list[dict] = []
    status_changelog: list[dict] = []
    sprint_snapshots: dict[str, dict] = {}
    sprint_metadata: dict[str, dict] = {}

    if sprint_field and tracked_issues:
        sprint_changelog = backend.get_changelog_entries(
            active_profile_id,
            active_query_id,
            field_name=sprint_field,
        )
        if not sprint_changelog:
            sprint_changelog = backend.get_changelog_entries(
                active_profile_id,
                active_query_id,
                field_name="Sprint",
            )

        status_changelog = backend.get_changelog_entries(
            active_profile_id,
            active_query_id,
            field_name="status",
        )

        if sprint_changelog:
            sprint_snapshots = get_sprint_snapshots(
                tracked_issues,
                sprint_changelog,
                sprint_field,
            )

        sprint_metadata = _extract_sprint_metadata(tracked_issues, sprint_field)

    payload = {
        "settings": settings,
        "all_issues": all_issues,
        "tracked_issues": tracked_issues,
        "all_issue_states": all_issue_states,
        "sprint_field": sprint_field,
        "sprint_snapshots": sprint_snapshots,
        "sprint_metadata": sprint_metadata,
        "sprint_changelog": sprint_changelog,
        "status_changelog": status_changelog,
    }

    _SPRINT_TRACKER_CACHE[cache_key] = {
        "cached_at": datetime.now(UTC),
        "payload": payload,
    }

    return payload
