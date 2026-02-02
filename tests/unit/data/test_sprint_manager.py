"""Unit tests for sprint_manager module.

Tests sprint snapshot building, change detection, progress calculation,
and issue filtering for Sprint Tracker feature.
"""

from data.sprint_manager import (
    get_sprint_snapshots,
    detect_sprint_changes,
    calculate_sprint_progress,
    filter_sprint_issues,
    _parse_sprint_name,
    get_sprint_field_from_config,
)


class TestParseSprintName:
    """Test suite for _parse_sprint_name helper function."""

    def test_parse_jira_sprint_object_format(self):
        """Test parsing JIRA sprint object serialization format."""
        sprint_value = "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23,state=ACTIVE]"
        assert _parse_sprint_name(sprint_value) == "Sprint 23"

    def test_parse_sprint_name_with_closing_bracket(self):
        """Test parsing when comma not found (use closing bracket)."""
        sprint_value = "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=42,name=Sprint 42]"
        assert _parse_sprint_name(sprint_value) == "Sprint 42"

    def test_parse_simple_string(self):
        """Test parsing simple sprint name string."""
        assert _parse_sprint_name("Sprint 15") == "Sprint 15"

    def test_parse_null_value(self):
        """Test parsing null/None value."""
        assert _parse_sprint_name(None) is None
        assert _parse_sprint_name("") is None

    def test_parse_invalid_format(self):
        """Test parsing invalid format returns as-is."""
        assert _parse_sprint_name("Invalid Format") == "Invalid Format"


class TestGetSprintSnapshots:
    """Test suite for get_sprint_snapshots function."""

    def test_get_sprint_snapshots_single_sprint(self):
        """Test building snapshot for single sprint."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "summary": "Test Story 1",
                },
                "custom_fields": {"customfield_10016": 5},
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {"name": "In Progress"},
                    "issuetype": {"name": "Bug"},
                    "summary": "Test Bug 1",
                },
                "custom_fields": {"customfield_10016": 3},
            },
        ]

        changelog_entries = [
            {
                "issue_key": "PROJ-1",
                "change_date": "2025-01-10T10:00:00Z",
                "field_name": "sprint",
                "old_value": None,
                "new_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23,state=ACTIVE]",
            },
            {
                "issue_key": "PROJ-2",
                "change_date": "2025-01-11T10:00:00Z",
                "field_name": "sprint",
                "old_value": None,
                "new_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23,state=ACTIVE]",
            },
        ]

        snapshots = get_sprint_snapshots(issues, changelog_entries)

        # Verify snapshot structure
        assert "Sprint 23" in snapshots
        snapshot = snapshots["Sprint 23"]

        # Verify current issues
        assert len(snapshot["current_issues"]) == 2
        assert "PROJ-1" in snapshot["current_issues"]
        assert "PROJ-2" in snapshot["current_issues"]

        # Verify added issues
        assert len(snapshot["added_issues"]) == 2
        assert snapshot["added_issues"][0]["issue_key"] == "PROJ-1"
        assert snapshot["added_issues"][1]["issue_key"] == "PROJ-2"

        # Verify removed issues (none)
        assert len(snapshot["removed_issues"]) == 0

        # Verify issue states enrichment
        assert "PROJ-1" in snapshot["issue_states"]
        assert snapshot["issue_states"]["PROJ-1"]["status"] == "Done"
        assert snapshot["issue_states"]["PROJ-1"]["story_points"] == 5
        assert snapshot["issue_states"]["PROJ-1"]["issue_type"] == "Story"

    def test_get_sprint_snapshots_issue_removed(self):
        """Test detecting issue removed from sprint."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "summary": "Test Story",
                },
                "custom_fields": {},
            }
        ]

        changelog_entries = [
            {
                "issue_key": "PROJ-1",
                "change_date": "2025-01-10T10:00:00Z",
                "field_name": "sprint",
                "old_value": None,
                "new_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23]",
            },
            {
                "issue_key": "PROJ-1",
                "change_date": "2025-01-15T10:00:00Z",
                "field_name": "sprint",
                "old_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23]",
                "new_value": None,
            },
        ]

        snapshots = get_sprint_snapshots(issues, changelog_entries)

        snapshot = snapshots["Sprint 23"]

        # Verify issue was removed
        assert len(snapshot["removed_issues"]) == 1
        assert snapshot["removed_issues"][0]["issue_key"] == "PROJ-1"

        # Verify issue not in current issues
        assert "PROJ-1" not in snapshot["current_issues"]

    def test_get_sprint_snapshots_issue_moved_between_sprints(self):
        """Test detecting issue moved from one sprint to another."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "summary": "Test Story",
                },
                "custom_fields": {},
            }
        ]

        changelog_entries = [
            {
                "issue_key": "PROJ-1",
                "change_date": "2025-01-10T10:00:00Z",
                "field_name": "sprint",
                "old_value": None,
                "new_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=22,name=Sprint 22]",
            },
            {
                "issue_key": "PROJ-1",
                "change_date": "2025-01-15T10:00:00Z",
                "field_name": "sprint",
                "old_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=22,name=Sprint 22]",
                "new_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23]",
            },
        ]

        snapshots = get_sprint_snapshots(issues, changelog_entries)

        # Verify Sprint 22 shows issue removed
        assert "Sprint 22" in snapshots
        assert len(snapshots["Sprint 22"]["removed_issues"]) == 1
        assert "PROJ-1" not in snapshots["Sprint 22"]["current_issues"]

        # Verify Sprint 23 shows issue added
        assert "Sprint 23" in snapshots
        assert len(snapshots["Sprint 23"]["added_issues"]) == 1
        assert "PROJ-1" in snapshots["Sprint 23"]["current_issues"]

    def test_get_sprint_snapshots_empty_changelog(self):
        """Test with empty changelog entries."""
        issues = [{"key": "PROJ-1", "fields": {}, "custom_fields": {}}]
        changelog_entries = []

        snapshots = get_sprint_snapshots(issues, changelog_entries)

        # Should return empty dict
        assert len(snapshots) == 0


class TestDetectSprintChanges:
    """Test suite for detect_sprint_changes function."""

    def test_detect_sprint_changes_added(self):
        """Test detecting issues added to sprint."""
        changelog_entries = [
            {
                "issue_key": "PROJ-1",
                "change_date": "2025-01-10T10:00:00Z",
                "field_name": "sprint",
                "old_value": None,
                "new_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23]",
            },
            {
                "issue_key": "PROJ-2",
                "change_date": "2025-01-11T10:00:00Z",
                "field_name": "sprint",
                "old_value": None,
                "new_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23]",
            },
        ]

        changes = detect_sprint_changes(changelog_entries)

        assert "Sprint 23" in changes
        assert len(changes["Sprint 23"]["added"]) == 2
        assert changes["Sprint 23"]["added"][0]["issue_key"] == "PROJ-1"
        assert changes["Sprint 23"]["added"][0]["from"] is None

    def test_detect_sprint_changes_removed(self):
        """Test detecting issues removed from sprint."""
        changelog_entries = [
            {
                "issue_key": "PROJ-1",
                "change_date": "2025-01-15T10:00:00Z",
                "field_name": "sprint",
                "old_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23]",
                "new_value": None,
            }
        ]

        changes = detect_sprint_changes(changelog_entries)

        assert "Sprint 23" in changes
        assert len(changes["Sprint 23"]["removed"]) == 1
        assert changes["Sprint 23"]["removed"][0]["issue_key"] == "PROJ-1"
        assert changes["Sprint 23"]["removed"][0]["to"] is None

    def test_detect_sprint_changes_moved(self):
        """Test detecting issues moved between sprints."""
        changelog_entries = [
            {
                "issue_key": "PROJ-1",
                "change_date": "2025-01-15T10:00:00Z",
                "field_name": "sprint",
                "old_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=22,name=Sprint 22]",
                "new_value": "com.atlassian.greenhopper.service.sprint.Sprint@14b3c[id=23,name=Sprint 23]",
            }
        ]

        changes = detect_sprint_changes(changelog_entries)

        # Verify moved_out from Sprint 22
        assert "Sprint 22" in changes
        assert len(changes["Sprint 22"]["moved_out"]) == 1
        assert changes["Sprint 22"]["moved_out"][0]["to"] == "Sprint 23"

        # Verify moved_in to Sprint 23
        assert "Sprint 23" in changes
        assert len(changes["Sprint 23"]["moved_in"]) == 1
        assert changes["Sprint 23"]["moved_in"][0]["from"] == "Sprint 22"


class TestCalculateSprintProgress:
    """Test suite for calculate_sprint_progress function."""

    def test_calculate_sprint_progress_basic(self):
        """Test basic progress calculation."""
        sprint_snapshot = {
            "name": "Sprint 23",
            "current_issues": ["PROJ-1", "PROJ-2", "PROJ-3"],
            "issue_states": {
                "PROJ-1": {
                    "status": "Done",
                    "story_points": 5,
                    "issue_type": "Story",
                },
                "PROJ-2": {
                    "status": "In Progress",
                    "story_points": 3,
                    "issue_type": "Bug",
                },
                "PROJ-3": {
                    "status": "To Do",
                    "story_points": 2,
                    "issue_type": "Task",
                },
            },
        }

        progress = calculate_sprint_progress(
            sprint_snapshot,
            flow_end_statuses=["Done", "Closed"],
            flow_wip_statuses=["In Progress", "In Review"],
        )

        # Verify totals
        assert progress["total_issues"] == 3
        assert progress["completed_issues"] == 1
        assert progress["wip_issues"] == 1
        assert progress["completion_percentage"] == 33.3
        assert progress["completion_pct"] == 33.3

        # Verify points
        assert progress["total_points"] == 10.0
        assert progress["completed_points"] == 5.0
        assert progress["wip_points"] == 3.0
        assert progress["points_completion_percentage"] == 50.0
        assert progress["points_completion_pct"] == 50.0

        # Verify by_status breakdown
        assert progress["by_status"]["Done"]["count"] == 1
        assert progress["by_status"]["Done"]["points"] == 5.0
        assert progress["by_status"]["In Progress"]["count"] == 1
        assert progress["by_status"]["In Progress"]["points"] == 3.0

        # Verify by_issue_type breakdown
        assert progress["by_issue_type"]["Story"]["count"] == 1
        assert progress["by_issue_type"]["Bug"]["count"] == 1
        assert progress["by_issue_type"]["Task"]["count"] == 1

    def test_calculate_sprint_progress_all_completed(self):
        """Test 100% completion."""
        sprint_snapshot = {
            "issue_states": {
                "PROJ-1": {"status": "Done", "story_points": 5, "issue_type": "Story"},
                "PROJ-2": {"status": "Closed", "story_points": 3, "issue_type": "Bug"},
            }
        }

        progress = calculate_sprint_progress(sprint_snapshot)

        assert progress["total_issues"] == 2
        assert progress["completed_issues"] == 2
        assert progress["wip_issues"] == 0
        assert progress["completion_percentage"] == 100.0
        assert progress["completion_pct"] == 100.0
        assert progress["points_completion_percentage"] == 100.0
        assert progress["points_completion_pct"] == 100.0

    def test_calculate_sprint_progress_empty_sprint(self):
        """Test with empty sprint."""
        sprint_snapshot = {"issue_states": {}}

        progress = calculate_sprint_progress(sprint_snapshot)

        assert progress["total_issues"] == 0
        assert progress["completed_issues"] == 0
        assert progress["wip_issues"] == 0
        assert progress["completion_percentage"] == 0.0
        assert progress["completion_pct"] == 0.0
        assert progress["total_points"] == 0.0


class TestFilterSprintIssues:
    """Test suite for filter_sprint_issues function."""

    def test_filter_sprint_issues_default_types(self):
        """Test filtering with default issue types (Story, Task, Bug)."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {"issuetype": {"name": "Story"}},
            },
            {
                "key": "PROJ-2",
                "fields": {"issuetype": {"name": "Bug"}},
            },
            {
                "key": "PROJ-3",
                "fields": {"issuetype": {"name": "Task"}},
            },
            {
                "key": "PROJ-4",
                "fields": {"issuetype": {"name": "Sub-task"}},
            },
            {
                "key": "PROJ-5",
                "fields": {"issuetype": {"name": "Epic"}},
            },
        ]

        filtered = filter_sprint_issues(issues)

        # Should include Story, Bug, Task - exclude Sub-task, Epic
        assert len(filtered) == 3
        assert any(issue["key"] == "PROJ-1" for issue in filtered)
        assert any(issue["key"] == "PROJ-2" for issue in filtered)
        assert any(issue["key"] == "PROJ-3" for issue in filtered)
        assert not any(issue["key"] == "PROJ-4" for issue in filtered)
        assert not any(issue["key"] == "PROJ-5" for issue in filtered)

    def test_filter_sprint_issues_custom_types(self):
        """Test filtering with custom issue types."""
        issues = [
            {"key": "PROJ-1", "fields": {"issuetype": {"name": "Story"}}},
            {"key": "PROJ-2", "fields": {"issuetype": {"name": "Bug"}}},
            {"key": "PROJ-3", "fields": {"issuetype": {"name": "Epic"}}},
        ]

        filtered = filter_sprint_issues(issues, tracked_issue_types=["Story", "Epic"])

        # Should include only Story and Epic
        assert len(filtered) == 2
        assert any(issue["key"] == "PROJ-1" for issue in filtered)
        assert any(issue["key"] == "PROJ-3" for issue in filtered)
        assert not any(issue["key"] == "PROJ-2" for issue in filtered)

    def test_filter_sprint_issues_flat_structure(self):
        """Test filtering with flat database structure (not nested fields)."""
        issues = [
            {"key": "PROJ-1", "issue_type": "Story"},
            {"key": "PROJ-2", "issue_type": "Sub-task"},
            {"key": "PROJ-3", "issue_type": "Bug"},
        ]

        filtered = filter_sprint_issues(issues)

        # Should work with flat structure
        assert len(filtered) == 2
        assert any(issue["key"] == "PROJ-1" for issue in filtered)
        assert any(issue["key"] == "PROJ-3" for issue in filtered)


class TestGetSprintFieldFromConfig:
    """Test suite for get_sprint_field_from_config function."""

    def test_get_sprint_field_configured(self):
        """Test extracting configured sprint field."""
        config = {
            "field_mappings": {"sprint_tracker": {"sprint_field": "customfield_10020"}}
        }

        field_id = get_sprint_field_from_config(config)
        assert field_id == "customfield_10020"

    def test_get_sprint_field_not_configured(self):
        """Test with no sprint field configured."""
        config = {"field_mappings": {}}

        field_id = get_sprint_field_from_config(config)
        assert field_id is None

    def test_get_sprint_field_empty_config(self):
        """Test with empty configuration."""
        config = {}

        field_id = get_sprint_field_from_config(config)
        assert field_id is None
