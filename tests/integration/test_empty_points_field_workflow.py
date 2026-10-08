import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.persistence.adapters.scope import (
    get_project_scope,
    update_project_scope_from_jira,
)
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)
from data.query_manager import create_query


class TestEmptyPointsFieldCachingWorkflow:
    @pytest.fixture(autouse=True)
    def setup_test_data(self, temp_database):
        from data.persistence.factory import get_backend

        self.backend = get_backend()

        self.test_profile_id = "test_profile"
        profile_data = {
            "id": self.test_profile_id,
            "name": "Empty Points Test Profile",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {
                "base_url": "https://test.jira.com",
                "configured": True,
            },
            "field_mappings": {},
        }
        self.backend.save_profile(profile_data)

        self.test_query_id = create_query(
            self.test_profile_id, "Main Query", "project = TEST"
        )

        self.backend.set_app_state("active_profile_id", self.test_profile_id)
        self.backend.set_app_state("active_query_id", self.test_query_id)

        yield

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "IMP-005: scope calculation reports total_items=161 (every issue in the "
            "store) where the test's query matched 30, so the filter is not reaching "
            "the count. Product bug, not a test bug -- the assertion is correct. "
            "Remove this marker with the fix."
        ),
    )
    def test_empty_points_field_workflow_fix(self):
        problematic_state = {
            "project_scope": {
                "total_items": 364,
                "total_points": 944,
                "completed_items": 69,
                "completed_points": 326,
                "remaining_items": 295,
                "remaining_points": 618,
                "estimated_items": 295,
                "estimated_points": 618,
                "remaining_total_points": 1930.2469135802469,
                "points_field_available": True,
                "status_breakdown": {
                    "Closed": {"items": 67, "points": 326},
                    "Gathering Interest": {"items": 173, "points": 302},
                },
                "calculation_metadata": {
                    "method": "status_category",
                    "calculated_at": "2025-07-20T14:16:22.989077",
                    "total_issues_processed": 364,
                    "points_field": "votes",
                    "points_field_valid": True,
                },
                "source": "jira",
                "last_jira_sync": "2025-07-20T14:16:23.018802",
            },
            "statistics": [],
            "metadata": {
                "source": "csv_import",
                "last_updated": "2025-07-20T14:19:44.329005",
                "version": "2.0",
            },
        }

        save_unified_project_data(problematic_state)

        loaded_data = load_unified_project_data()
        initial_scope = loaded_data["project_scope"]
        assert initial_scope.get("remaining_total_points") == 1930.2469135802469
        assert initial_scope.get("points_field_available") is True
        assert (
            initial_scope.get("calculation_metadata", {}).get("points_field") == "votes"
        )

        mock_issues = []

        for i in range(10):
            mock_issues.append(
                {
                    "key": f"JRASERVER-{i + 1}",
                    "fields": {
                        "status": {"name": "Closed", "statusCategory": {"key": "done"}},
                        "votes": {"votes": 5},
                        "created": "2025-02-01T10:00:00.000Z",
                        "resolutiondate": "2025-02-05T10:00:00.000Z",
                    },
                }
            )

        statuses = [
            ("Gathering Interest", "new"),
            ("Gathering Impact", "new"),
            ("In Progress", "indeterminate"),
            ("Needs Triage", "new"),
        ]

        for i in range(20):
            status_name, category = statuses[i % len(statuses)]
            mock_issues.append(
                {
                    "key": f"JRASERVER-{i + 11}",
                    "fields": {
                        "status": {
                            "name": status_name,
                            "statusCategory": {"key": category},
                        },
                        "votes": {"votes": 3},
                        "created": "2025-01-15T10:00:00.000Z",
                        "resolutiondate": None,
                    },
                }
            )

        with patch("data.jira.main_fetch.fetch_jira_issues") as mock_fetch:
            mock_fetch.return_value = (True, mock_issues)

            ui_config = {
                "jql_query": "project = JRASERVER AND created > endOfMonth(-6)",
                "api_endpoint": "https://jira.atlassian.com/rest/api/2/search",
                "token": "",
                "story_points_field": "",
                "cache_max_size_mb": 100,
            }

            success, message = update_project_scope_from_jira(
                ui_config["jql_query"], ui_config
            )

            assert success, f"Update Data should succeed: {message}"

            loaded_data = load_unified_project_data()
            updated_scope = loaded_data["project_scope"]

            assert updated_scope.get("remaining_total_points") == 0.0, (
                "remaining_total_points should be 0 when points field is empty"
            )

            assert updated_scope.get("points_field_available", True) is False, (
                "points_field_available should be False when points field is empty"
            )

            assert updated_scope.get("estimated_items", -1) == 0, (
                "estimated_items should be 0 when points field is empty"
            )

            assert updated_scope.get("estimated_points", -1) == 0, (
                "estimated_points should be 0 when points field is empty"
            )

            metadata = updated_scope.get("calculation_metadata", {})
            assert metadata.get("points_field") == "", (
                "metadata points_field should be empty string"
            )

            assert metadata.get("points_field_valid", True) is False, (
                "metadata points_field_valid should be False"
            )

            assert updated_scope.get("total_items") == 30, (
                "total_items should match issue count (30 issues)"
            )

            assert updated_scope.get("completed_items") == 10, (
                "completed_items should be recalculated (10 completed)"
            )

            assert updated_scope.get("remaining_items") == 20, (
                "remaining_items should be recalculated (20 remaining)"
            )

            assert updated_scope.get("total_points") == 0
            assert updated_scope.get("completed_points") == 0
            assert updated_scope.get("remaining_points") == 0

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "IMP-005: the Update Data call returns success=False when the points "
            "field is cleared, so cache invalidation never runs. Remove this marker "
            "with the fix."
        ),
    )
    def test_cache_invalidation_votes_to_empty(self):

        initial_data = {
            "project_scope": {
                "remaining_total_points": 1000.0,
                "points_field_available": True,
            },
            "statistics": [],
            "metadata": {"version": "2.0"},
        }

        save_unified_project_data(initial_data)

        mock_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "votes": {"votes": 5},
                    "created": "2025-01-01T10:00:00.000Z",
                },
            }
        ]

        with patch("data.jira.main_fetch.fetch_jira_issues") as mock_fetch:
            mock_fetch.return_value = (True, mock_issues)

            ui_config = {
                "jql_query": "project = TEST",
                "api_endpoint": "https://test.com/rest/api/2/search",
                "token": "",
                "story_points_field": "",
                "cache_max_size_mb": 50,
            }

            success, message = update_project_scope_from_jira(
                ui_config["jql_query"], ui_config
            )
            assert success

            scope = get_project_scope()
            assert scope.get("remaining_total_points") == 0
            assert scope.get("points_field_available") is False
