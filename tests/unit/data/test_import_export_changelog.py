"""Unit tests for changelog import/export helpers."""

from data.import_export_changelog import (
    collect_changelog_entries,
    normalize_imported_changelog_entries,
)


class _MockBackend:
    def __init__(self, data_by_field):
        self._data_by_field = data_by_field

    def get_changelog_entries(self, profile_id, query_id, field_name=None, **_kwargs):
        return self._data_by_field.get(field_name, [])


def test_collect_changelog_entries_filters_and_dedupes():
    status_entry = {
        "issue_key": "TEST-1",
        "change_date": "2026-01-01T10:00:00Z",
        "field_name": "status",
        "old_value": "To Do",
        "new_value": "Done",
    }
    sprint_entry = {
        "issue_key": "TEST-1",
        "change_date": "2026-01-02T10:00:00Z",
        "field_name": "customfield_10020",
        "old_value": "Sprint 1",
        "new_value": "Sprint 2",
    }

    backend = _MockBackend(
        {
            "status": [status_entry, status_entry.copy()],
            "Sprint": [],
            "customfield_10020": [sprint_entry],
        }
    )

    entries = collect_changelog_entries(
        backend, "profile", "query", "customfield_10020"
    )

    assert len(entries) == 2
    assert any(entry["field_name"] == "status" for entry in entries)
    assert any(entry["field_name"] == "customfield_10020" for entry in entries)


def test_normalize_imported_changelog_entries_maps_sprint_fields():
    entries = [
        {
            "issue_key": "TEST-1",
            "change_date": "2026-01-01T10:00:00Z",
            "field_name": "customfield_10020",
            "old_value": "Sprint 1",
            "new_value": "Sprint 2",
        },
        {
            "issue_key": "TEST-1",
            "change_date": "2026-01-01T11:00:00Z",
            "field_name": "status",
            "old_value": "To Do",
            "new_value": "In Progress",
        },
        {
            "issue_key": "TEST-2",
            "change_date": "2026-01-03T10:00:00Z",
            "field_name": "Sprint",
            "old_value": "Sprint 1",
            "new_value": "Sprint 3",
            "field_type": "jira",
        },
    ]

    normalized = normalize_imported_changelog_entries(entries)

    sprint_fields = [
        entry["field_name"] for entry in normalized if entry["field_name"] != "status"
    ]
    assert sprint_fields
    assert all(field == "Sprint" for field in sprint_fields)

    status_entry = next(
        entry for entry in normalized if entry["field_name"] == "status"
    )
    assert status_entry["new_value"] == "In Progress"

    for entry in normalized:
        assert entry.get("field_type") == "jira"
