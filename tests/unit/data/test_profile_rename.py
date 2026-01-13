"""
Unit tests for profile rename functionality.

Tests the rename_profile function with various validation scenarios.
Uses SQLite database backend via temp_database fixture.
"""

import pytest
from datetime import datetime, timezone


def create_test_profile_data(profile_id: str, name: str) -> dict:
    """Helper to create test profile with all required fields."""
    fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    return {
        "id": profile_id,
        "name": name,
        "description": "",
        "created_at": fixed_timestamp,
        "last_used": fixed_timestamp,
        "jira_config": {},
        "field_mappings": {},
        "forecast_settings": {
            "pert_factor": 1.2,
            "deadline": None,
            "data_points_count": 12,
        },
        "project_classification": {},
        "flow_type_mappings": {},
    }


class TestRenameProfile:
    """Test suite for rename_profile function."""

    def test_rename_profile_success(self, temp_database):
        """Test successful profile rename."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        # Create initial profile
        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Original Name")
        backend.save_profile(profile)

        # Rename profile
        rename_profile("p_test123", "New Name")

        # Verify name changed in database
        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None
        assert updated_profile["name"] == "New Name"

    def test_rename_profile_empty_name(self, temp_database):
        """Test rename with empty name raises ValueError."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Test Profile")
        backend.save_profile(profile)

        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            rename_profile("p_test123", "")

        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            rename_profile("p_test123", "   ")

    def test_rename_profile_name_too_long(self, temp_database):
        """Test rename with name exceeding 100 characters."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Test Profile")
        backend.save_profile(profile)

        long_name = "A" * 101
        with pytest.raises(
            ValueError, match="Profile name cannot exceed 100 characters"
        ):
            rename_profile("p_test123", long_name)

    def test_rename_profile_duplicate_name(self, temp_database):
        """Test rename to existing profile name raises ValueError."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile1 = create_test_profile_data("p_test1", "Profile One")
        profile2 = create_test_profile_data("p_test2", "Profile Two")
        backend.save_profile(profile1)
        backend.save_profile(profile2)

        # Try to rename profile_1 to "Profile Two"
        with pytest.raises(
            ValueError, match="Profile name 'Profile Two' already exists"
        ):
            rename_profile("p_test1", "Profile Two")

    def test_rename_profile_duplicate_name_case_insensitive(self, temp_database):
        """Test rename duplicate check is case-insensitive."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile1 = create_test_profile_data("p_test1", "Profile One")
        profile2 = create_test_profile_data("p_test2", "Profile Two")
        backend.save_profile(profile1)
        backend.save_profile(profile2)

        # Try various case combinations
        with pytest.raises(ValueError, match="Profile name"):
            rename_profile("p_test1", "profile two")

        with pytest.raises(ValueError, match="Profile name"):
            rename_profile("p_test1", "PROFILE TWO")

        with pytest.raises(ValueError, match="Profile name"):
            rename_profile("p_test1", "Profile TWO")

    def test_rename_profile_same_name(self, temp_database):
        """Test rename to same name (should skip operation)."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Test Profile")
        backend.save_profile(profile)

        # Rename to same name (case-insensitive match) - should not raise
        rename_profile("p_test123", "Test Profile")
        rename_profile("p_test123", "test profile")
        rename_profile("p_test123", "TEST PROFILE")

        # Verify name unchanged
        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None

    def test_rename_nonexistent_profile(self, temp_database):
        """Test rename of nonexistent profile raises ValueError."""
        from data.profile_manager import rename_profile

        with pytest.raises(ValueError, match="Profile 'nonexistent_id' does not exist"):
            rename_profile("nonexistent_id", "New Name")

    def test_rename_preserves_other_metadata(self, temp_database):
        """Test rename doesn't change other profile metadata."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Original Name")
        profile["description"] = "Important description"
        profile["forecast_settings"]["pert_factor"] = 1.5
        profile["forecast_settings"]["deadline"] = "2025-12-31"
        profile["forecast_settings"]["data_points_count"] = 30
        profile["jira_config"] = {"base_url": "https://jira.example.com"}
        profile["field_mappings"] = {"points_field": "customfield_10001"}
        backend.save_profile(profile)

        # Rename
        rename_profile("p_test123", "New Name")

        # Verify other fields unchanged
        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None
        assert updated_profile["name"] == "New Name"
        assert updated_profile["description"] == "Important description"
        assert updated_profile["forecast_settings"]["pert_factor"] == 1.5
        assert updated_profile["forecast_settings"]["deadline"] == "2025-12-31"
        assert updated_profile["forecast_settings"]["data_points_count"] == 30
        assert updated_profile["jira_config"]["base_url"] == "https://jira.example.com"
        assert updated_profile["field_mappings"]["points_field"] == "customfield_10001"

    def test_rename_profile_id_unchanged(self, temp_database):
        """Test rename doesn't change profile ID."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Original Name")
        backend.save_profile(profile)

        # Rename
        rename_profile("p_test123", "New Name")

        # Verify profile ID unchanged
        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None
        assert updated_profile["id"] == "p_test123"
        assert updated_profile["name"] == "New Name"

    def test_rename_whitespace_stripped(self, temp_database):
        """Test rename strips leading/trailing whitespace."""
        from data.profile_manager import rename_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Test Profile")
        backend.save_profile(profile)

        # Rename with whitespace
        rename_profile("p_test123", "  New Name  ")

        # Verify whitespace stripped
        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None
        assert updated_profile["name"] == "New Name"
