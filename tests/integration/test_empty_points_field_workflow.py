"""
Test for empty points field caching scenarios - reproduces and tests user reported bug.

User Reported Bug:
- Points Field is empty but Remaining Total Points shows 1394 instead of 0
- Remaining Total Items shows 295 instead of expected value
- This happens before clicking "Calculate Scope" - suggests caching issue with "Update Data"

Root Cause Analysis:
The bug was NOT in cache invalidation (which works correctly) but in user workflow:
1. User has old project_data.json with votes calculation
2. User changes UI to empty Points Field
3. User expects immediate change but needs to click "Update Data" to recalculate
4. Browser/UI might show stale values until refresh

This test verifies the fix works correctly.

MIGRATED: Uses SQLite database backend via temp_database fixture (from conftest.py).
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

# Add parent to path to import data.persistence module directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import from data module - persistence.py is a MODULE, not the package
import data.persistence as persistence_module

from data.query_manager import create_query


class TestEmptyPointsFieldCachingWorkflow:
    """Test empty points field caching workflow scenarios using database backend."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, temp_database):
        """Set up test profile and query using database backend."""
        from data.persistence.factory import get_backend

        self.backend = get_backend()

        # Create test profile with JIRA configured
        self.test_profile_id = "test_profile"
        profile_data = {
            "id": self.test_profile_id,
            "name": "Empty Points Test Profile",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {
                "base_url": "https://test.jira.com",
                "configured": True,
            },
            "field_mappings": {},
        }
        self.backend.save_profile(profile_data)

        # Create test query
        self.test_query_id = create_query(
            self.test_profile_id, "Main Query", "project = TEST"
        )

        # Set as active profile/query
        self.backend.set_app_state("active_profile_id", self.test_profile_id)
        self.backend.set_app_state("active_query_id", self.test_query_id)

        yield

        # Cleanup handled by temp_database fixture

    def test_empty_points_field_workflow_fix(self):
        """
        Test the complete workflow fix for empty points field:
        1. Start with cached votes calculation (user's state)
        2. Change points field to empty and run Update Data
        3. Verify all values are correctly recalculated to 0/False
        """
        # Step 1: Simulate user's current problematic state (from project_data.json)
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
                "remaining_total_points": 1930.2469135802469,  # Should become 0
                "points_field_available": True,  # Should become False
                "status_breakdown": {
                    "Closed": {"items": 67, "points": 326},
                    "Gathering Interest": {"items": 173, "points": 302},
                },
                "calculation_metadata": {
                    "method": "status_category",
                    "calculated_at": "2025-07-20T14:16:22.989077",
                    "total_issues_processed": 364,
                    "points_field": "votes",  # Should become ""
                    "points_field_valid": True,  # Should become False
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

        # Save the problematic state
        persistence_module.save_unified_project_data(problematic_state)

        # Verify we start with the problematic values
        initial_scope = persistence_module.get_project_scope()
        assert initial_scope.get("remaining_total_points") == 1930.2469135802469
        assert initial_scope.get("points_field_available") is True
        assert (
            initial_scope.get("calculation_metadata", {}).get("points_field") == "votes"
        )

        # Step 2: Mock JIRA response (simulate what would come from their actual query)
        mock_issues = []

        # Add completed issues (matching their actual data)
        for i in range(69):
            mock_issues.append(
                {
                    "key": f"JRASERVER-{i + 1}",
                    "fields": {
                        "status": {"name": "Closed", "statusCategory": {"key": "done"}},
                        "votes": {
                            "votes": 5
                        },  # Has votes but should be ignored when empty field
                        "created": "2025-02-01T10:00:00.000Z",
                        "resolutiondate": "2025-02-05T10:00:00.000Z",
                    },
                }
            )

        # Add remaining issues
        statuses = [
            ("Gathering Interest", "new"),
            ("Gathering Impact", "new"),
            ("In Progress", "indeterminate"),
            ("Needs Triage", "new"),
        ]

        remaining_count = 295
        for i in range(remaining_count):
            status_name, category = statuses[i % len(statuses)]
            mock_issues.append(
                {
                    "key": f"JRASERVER-{i + 70}",
                    "fields": {
                        "status": {
                            "name": status_name,
                            "statusCategory": {"key": category},
                        },
                        "votes": {
                            "votes": 3
                        },  # Should be ignored when points field empty
                        "created": "2025-01-15T10:00:00.000Z",
                        "resolutiondate": None,
                    },
                }
            )

        # Step 3: Simulate user clicking "Update Data" with EMPTY points field
        with patch("data.jira_simple.fetch_jira_issues") as mock_fetch:
            mock_fetch.return_value = (True, mock_issues)

            # User's actual configuration with EMPTY points field
            ui_config = {
                "jql_query": "project = JRASERVER AND created > endOfMonth(-6)",
                "api_endpoint": "https://jira.atlassian.com/rest/api/2/search",
                "token": "",
                "story_points_field": "",  # EMPTY - the key fix!
                "cache_max_size_mb": 100,
            }

            # This should completely recalculate and fix the issue
            success, message = persistence_module.update_project_scope_from_jira(
                ui_config["jql_query"], ui_config
            )

            # Verify operation succeeded
            assert success, f"Update Data should succeed: {message}"

            # Step 4: Verify the fix - all point values should be 0/False
            updated_scope = persistence_module.get_project_scope()

            # THE FIX: These should all be corrected now
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

            # Metadata should reflect empty field
            metadata = updated_scope.get("calculation_metadata", {})
            assert metadata.get("points_field") == "", (
                "metadata points_field should be empty string"
            )

            assert metadata.get("points_field_valid", True) is False, (
                "metadata points_field_valid should be False"
            )

            # Item counts should be recalculated correctly
            assert updated_scope.get("total_items") == 364, (
                "total_items should match issue count"
            )

            assert updated_scope.get("completed_items") == 69, (
                "completed_items should be recalculated"
            )

            assert updated_scope.get("remaining_items") == 295, (
                "remaining_items should be recalculated"
            )

            # All point-related fields should be 0
            assert updated_scope.get("total_points") == 0
            assert updated_scope.get("completed_points") == 0
            assert updated_scope.get("remaining_points") == 0

    def test_cache_invalidation_votes_to_empty(self):
        """Test that cache is properly invalidated when switching from votes to empty."""

        # This test verifies the cache invalidation logic works correctly
        # (which it does based on our previous tests)

        initial_data = {
            "project_scope": {
                "remaining_total_points": 1000.0,
                "points_field_available": True,
            },
            "statistics": [],
            "metadata": {"version": "2.0"},
        }

        persistence_module.save_unified_project_data(initial_data)

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

        with patch("data.jira_simple.fetch_jira_issues") as mock_fetch:
            mock_fetch.return_value = (True, mock_issues)

            # Empty points field should trigger recalculation
            ui_config = {
                "jql_query": "project = TEST",
                "api_endpoint": "https://test.com/rest/api/2/search",
                "token": "",
                "story_points_field": "",  # Empty!
                "cache_max_size_mb": 50,
            }

            success, message = persistence_module.update_project_scope_from_jira(
                ui_config["jql_query"], ui_config
            )
            assert success

            # Should be completely recalculated
            scope = persistence_module.get_project_scope()
            assert scope.get("remaining_total_points") == 0
            assert scope.get("points_field_available") is False
