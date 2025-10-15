"""
Unit Tests for JIRA Query Profile Manager

Tests the core functionality of saving, loading, and managing JQL query profiles.
Covers the recently implemented data layer for multiple JQL queries feature.
"""

import json
import os
import tempfile
import uuid
from unittest.mock import mock_open, patch

import pytest

from data.jira_query_manager import (
    delete_query_profile,
    get_query_profile_by_id,
    load_query_profiles,
    save_query_profile,
    update_profile_last_used,
    validate_profile_name_unique,
)


class TestQueryProfileManager:
    """Test JIRA query profile management functionality"""

    def test_load_query_profiles_returns_empty_when_no_file(self):
        """Test that empty list is returned when no user profiles exist"""
        with patch("data.jira_query_manager.os.path.exists", return_value=False):
            profiles = load_query_profiles()

            # Should return empty list
            assert len(profiles) == 0
            assert profiles == []

    def test_load_query_profiles_returns_user_profiles(self):
        """Test that user profiles are loaded from file"""
        mock_user_profiles = [
            {
                "id": str(uuid.uuid4()),
                "name": "Custom Query",
                "jql": "project = TEST AND status = 'In Progress'",
                "description": "Test query",
                "is_default": False,
                "created_at": "2025-01-01T00:00:00",
                "last_used": "2025-01-01T00:00:00",
            }
        ]

        with (
            patch("data.jira_query_manager.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(mock_user_profiles))),
        ):
            profiles = load_query_profiles()

            # Should have only 1 user profile
            assert len(profiles) == 1

            # Should be the user profile
            assert not profiles[0]["is_default"]
            assert profiles[0]["name"] == "Custom Query"

    def test_save_query_profile_creates_new_profile(self):
        """Test saving a new query profile"""
        with (
            patch("data.jira_query_manager._load_profiles_from_disk", return_value=[]),
            patch(
                "data.jira_query_manager._save_profiles_to_disk", return_value=True
            ) as mock_save,
            patch("data.jira_query_manager.validate_query_profile", return_value=True),
        ):
            profile = save_query_profile(
                name="Test Query", jql="project = TEST", description="Test description"
            )

            assert profile is not None
            assert profile["name"] == "Test Query"
            assert profile["jql"] == "project = TEST"
            assert profile["description"] == "Test description"
            assert profile["is_default"] is False
            assert "id" in profile
            assert "created_at" in profile
            assert "last_used" in profile

            # Verify save was called
            mock_save.assert_called_once()

    def test_save_query_profile_prevents_duplicate_names(self):
        """Test that duplicate profile names are prevented"""
        existing_profiles = [
            {
                "id": str(uuid.uuid4()),
                "name": "Existing Query",
                "jql": "project = EXISTING",
                "description": "Existing",
                "is_default": False,
            }
        ]

        with patch(
            "data.jira_query_manager._load_profiles_from_disk",
            return_value=existing_profiles,
        ):
            profile = save_query_profile(
                name="Existing Query",  # Duplicate name
                jql="project = NEW",
                description="Should fail",
            )

            assert profile is None

    def test_save_query_profile_validates_inputs(self):
        """Test input validation for save_query_profile"""
        # Test empty name
        profile = save_query_profile(name="", jql="project = TEST")
        assert profile is None

        # Test whitespace-only name
        profile = save_query_profile(name="   ", jql="project = TEST")
        assert profile is None

    def test_delete_query_profile_prevents_default_deletion(self):
        """Test that default profiles cannot be deleted"""
        result = delete_query_profile("default-all-issues")
        assert result is False

    def test_delete_query_profile_removes_user_profile(self):
        """Test deleting a user-created profile"""
        profile_id = str(uuid.uuid4())
        existing_profiles = [
            {
                "id": profile_id,
                "name": "To Delete",
                "jql": "project = DELETE",
                "description": "Will be deleted",
                "is_default": False,
            }
        ]

        with (
            patch(
                "data.jira_query_manager._load_profiles_from_disk",
                return_value=existing_profiles,
            ),
            patch(
                "data.jira_query_manager._save_profiles_to_disk", return_value=True
            ) as mock_save,
        ):
            result = delete_query_profile(profile_id)

            assert result is True
            # Verify empty list was saved (profile removed)
            mock_save.assert_called_once_with([])

    def test_get_query_profile_by_id_returns_correct_profile(self):
        """Test retrieving a specific profile by ID"""
        with patch("data.jira_query_manager.load_query_profiles") as mock_load:
            test_profile = {
                "id": "test-id",
                "name": "Test Profile",
                "jql": "project = TEST",
            }
            mock_load.return_value = [test_profile]

            result = get_query_profile_by_id("test-id")

            assert result == test_profile

    def test_get_query_profile_by_id_returns_none_if_not_found(self):
        """Test that None is returned when profile ID is not found"""
        with patch("data.jira_query_manager.load_query_profiles", return_value=[]):
            result = get_query_profile_by_id("nonexistent-id")
            assert result is None

    def test_validate_profile_name_unique_with_existing_name(self):
        """Test name uniqueness validation"""
        with patch("data.jira_query_manager.load_query_profiles") as mock_load:
            mock_load.return_value = [{"id": "existing-id", "name": "Existing Name"}]

            # Should return False for duplicate name
            assert not validate_profile_name_unique("Existing Name")

            # Should return True for new name
            assert validate_profile_name_unique("New Name")

            # Should return True when excluding the existing profile
            assert validate_profile_name_unique(
                "Existing Name", exclude_id="existing-id"
            )

    def test_update_profile_last_used_skips_defaults(self):
        """Test that default profiles are not updated for last_used"""
        result = update_profile_last_used("default-all-issues")
        assert result is True  # Should succeed but do nothing

    def test_update_profile_last_used_updates_user_profile(self):
        """Test updating last_used timestamp for user profiles"""
        profile_id = str(uuid.uuid4())
        existing_profiles = [
            {
                "id": profile_id,
                "name": "User Profile",
                "jql": "project = USER",
                "last_used": "2025-01-01T00:00:00",
            }
        ]

        with (
            patch(
                "data.jira_query_manager._load_profiles_from_disk",
                return_value=existing_profiles,
            ),
            patch(
                "data.jira_query_manager._save_profiles_to_disk", return_value=True
            ) as mock_save,
        ):
            result = update_profile_last_used(profile_id)

            assert result is True
            mock_save.assert_called_once()

            # Verify timestamp was updated
            saved_profiles = mock_save.call_args[0][0]
            assert saved_profiles[0]["last_used"] != "2025-01-01T00:00:00"


@pytest.fixture
def temp_query_profiles_file():
    """Create a temporary file for query profiles testing"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


class TestQueryProfileFileOperations:
    """Test file I/O operations for query profiles"""

    def test_file_operations_with_real_file(self, temp_query_profiles_file):
        """Integration test with actual file operations"""
        # Mock the file path to use our temporary file
        with patch(
            "data.jira_query_manager.QUERY_PROFILES_FILE", temp_query_profiles_file
        ):
            # Save a profile
            profile = save_query_profile(
                name="File Test Query",
                jql="project = FILETEST",
                description="Testing file operations",
            )

            assert profile is not None

            # Verify file was created and contains data
            assert os.path.exists(temp_query_profiles_file)

            with open(temp_query_profiles_file, "r") as f:
                saved_data = json.load(f)

            assert len(saved_data) == 1
            assert saved_data[0]["name"] == "File Test Query"
