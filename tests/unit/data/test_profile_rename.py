"""
Unit tests for profile rename functionality.

Tests the rename_profile function with various validation scenarios.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from data.profile_manager import (
    rename_profile,
    create_profile,
    list_profiles,
)


@pytest.fixture
def temp_profiles_dir():
    """Create temporary profiles directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_profiles_path = Path(temp_dir) / "profiles"
        temp_profiles_path.mkdir()

        # Create profiles.json registry
        profiles_file = temp_profiles_path / "profiles.json"
        profiles_data = {
            "active_profile_id": None,
            "profiles": {},
        }
        with open(profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f, indent=2)

        # Patch PROFILES_DIR to use temp directory
        with patch("data.profile_manager.PROFILES_DIR", temp_profiles_path):
            with patch("data.profile_manager.PROFILES_FILE", profiles_file):
                yield temp_profiles_path


class TestRenameProfile:
    """Test suite for rename_profile function."""

    def test_rename_profile_success(self, temp_profiles_dir):
        """Test successful profile rename."""
        # Create initial profile
        settings = {
            "description": "Original description",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }
        profile_id = create_profile("Original Name", settings)

        # Rename profile
        rename_profile(profile_id, "New Name")

        # Verify name changed in registry
        profiles = list_profiles()
        profile = next((p for p in profiles if p["id"] == profile_id), None)
        assert profile is not None
        assert profile["name"] == "New Name"

        # Verify name changed in profile.json
        profile_file = temp_profiles_dir / profile_id / "profile.json"
        with open(profile_file, "r", encoding="utf-8") as f:
            profile_data = json.load(f)
        assert profile_data["name"] == "New Name"

    def test_rename_profile_empty_name(self, temp_profiles_dir):
        """Test rename with empty name raises ValueError."""
        settings = {
            "description": "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }
        profile_id = create_profile("Test Profile", settings)

        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            rename_profile(profile_id, "")

        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            rename_profile(profile_id, "   ")

    def test_rename_profile_name_too_long(self, temp_profiles_dir):
        """Test rename with name exceeding 100 characters."""
        settings = {
            "description": "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }
        profile_id = create_profile("Test Profile", settings)

        long_name = "A" * 101
        with pytest.raises(
            ValueError, match="Profile name cannot exceed 100 characters"
        ):
            rename_profile(profile_id, long_name)

    def test_rename_profile_duplicate_name(self, temp_profiles_dir):
        """Test rename to existing profile name raises ValueError."""
        settings = {
            "description": "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }

        # Create two profiles
        profile_id_1 = create_profile("Profile One", settings)
        create_profile("Profile Two", settings)

        # Try to rename profile_1 to "Profile Two"
        with pytest.raises(
            ValueError, match="Profile name 'Profile Two' already exists"
        ):
            rename_profile(profile_id_1, "Profile Two")

    def test_rename_profile_duplicate_name_case_insensitive(self, temp_profiles_dir):
        """Test rename duplicate check is case-insensitive."""
        settings = {
            "description": "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }

        profile_id_1 = create_profile("Profile One", settings)
        create_profile("Profile Two", settings)

        # Try various case combinations
        with pytest.raises(ValueError, match="Profile name"):
            rename_profile(profile_id_1, "profile two")

        with pytest.raises(ValueError, match="Profile name"):
            rename_profile(profile_id_1, "PROFILE TWO")

        with pytest.raises(ValueError, match="Profile name"):
            rename_profile(profile_id_1, "Profile TWO")

    def test_rename_profile_same_name(self, temp_profiles_dir):
        """Test rename to same name (should skip operation)."""
        settings = {
            "description": "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }
        profile_id = create_profile("Test Profile", settings)

        # Rename to same name (case-insensitive match)
        rename_profile(profile_id, "Test Profile")
        rename_profile(profile_id, "test profile")
        rename_profile(profile_id, "TEST PROFILE")

        # Should complete without error (operation skipped)

    def test_rename_nonexistent_profile(self, temp_profiles_dir):
        """Test rename of nonexistent profile raises ValueError."""
        with pytest.raises(ValueError, match="Profile 'nonexistent_id' does not exist"):
            rename_profile("nonexistent_id", "New Name")

    def test_rename_preserves_other_metadata(self, temp_profiles_dir):
        """Test rename doesn't change other profile metadata."""
        settings = {
            "description": "Important description",
            "pert_factor": 1.5,
            "deadline": "2025-12-31",
            "data_points_count": 30,
            "jira_config": {"base_url": "https://jira.example.com"},
            "field_mappings": {"points_field": "customfield_10001"},
        }
        profile_id = create_profile("Original Name", settings)

        # Get original metadata
        profile_file = temp_profiles_dir / profile_id / "profile.json"
        with open(profile_file, "r", encoding="utf-8") as f:
            original_data = json.load(f)

        # Rename
        rename_profile(profile_id, "New Name")

        # Verify other fields unchanged
        with open(profile_file, "r", encoding="utf-8") as f:
            new_data = json.load(f)

        assert new_data["name"] == "New Name"
        assert new_data["description"] == original_data["description"]
        assert (
            new_data["forecast_settings"]["pert_factor"]
            == original_data["forecast_settings"]["pert_factor"]
        )
        assert (
            new_data["forecast_settings"]["deadline"]
            == original_data["forecast_settings"]["deadline"]
        )
        assert (
            new_data["forecast_settings"]["data_points_count"]
            == original_data["forecast_settings"]["data_points_count"]
        )
        assert new_data["jira_config"] == original_data["jira_config"]
        assert new_data["field_mappings"] == original_data["field_mappings"]

    def test_rename_profile_id_unchanged(self, temp_profiles_dir):
        """Test rename doesn't change profile ID or directory structure."""
        settings = {
            "description": "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }
        profile_id = create_profile("Original Name", settings)

        # Verify profile directory exists
        profile_dir = temp_profiles_dir / profile_id
        assert profile_dir.exists()

        # Rename
        rename_profile(profile_id, "New Name")

        # Verify profile ID unchanged
        profiles = list_profiles()
        profile = next((p for p in profiles if p["name"] == "New Name"), None)
        assert profile is not None
        assert profile["id"] == profile_id

        # Verify directory still exists at same location
        assert profile_dir.exists()

    def test_rename_whitespace_stripped(self, temp_profiles_dir):
        """Test rename strips leading/trailing whitespace."""
        settings = {
            "description": "",
            "pert_factor": 1.2,
            "deadline": "",
            "data_points_count": 20,
            "jira_config": {},
            "field_mappings": {},
        }
        profile_id = create_profile("Test Profile", settings)

        # Rename with whitespace
        rename_profile(profile_id, "  New Name  ")

        # Verify whitespace stripped
        profiles = list_profiles()
        profile = next((p for p in profiles if p["id"] == profile_id), None)
        assert profile is not None
        assert profile["name"] == "New Name"
