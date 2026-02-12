"""Changelog helpers for import/export flows."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def collect_changelog_entries(
    backend: Any,
    profile_id: str,
    query_id: str,
    sprint_field: Optional[str],
) -> List[Dict]:
    """Collect changelog entries for export, filtered to tracked fields."""
    tracked_fields = ["status", "Sprint"]
    if sprint_field:
        tracked_fields.append(sprint_field)

    entries: List[Dict] = []
    seen: set[
        Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]
    ] = set()

    for field_name in dict.fromkeys(tracked_fields):
        field_entries = backend.get_changelog_entries(
            profile_id, query_id, field_name=field_name
        )
        for entry in field_entries:
            if not isinstance(entry, dict):
                continue
            dedupe_key = (
                entry.get("issue_key"),
                entry.get("change_date"),
                entry.get("field_name"),
                entry.get("old_value"),
                entry.get("new_value"),
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            entries.append(entry)

    return entries


def normalize_imported_changelog_entries(entries: List[Dict]) -> List[Dict]:
    """Normalize changelog entries for import.

    Maps sprint field changes to the display name to avoid instance-specific IDs.
    """
    normalized: List[Dict] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        field_name = entry.get("field_name")
        if not field_name:
            continue

        normalized_entry = entry.copy()
        if field_name != "status":
            normalized_entry["field_name"] = "Sprint"

        if not normalized_entry.get("field_type"):
            normalized_entry["field_type"] = "jira"

        normalized.append(normalized_entry)

    return normalized
