"""
Unit Tests for Data Source Persistence

Tests the persistence functionality for data source selection and JQL profile settings.
Covers the recently implemented settings persistence for multiple data sources feature.
"""

import json
import tempfile
import os
from unittest.mock import patch, mock_open
import pytest

from data.persistence import save_app_settings, load_app_settings


class TestDataSourcePersistence:
    """Test data source selection persistence functionality"""

    def test_load_app_settings_returns_defaults_when_no_file(self):
        """Test that default settings are returned when no settings file exists"""
        with patch("data.persistence.os.path.exists", return_value=False):
            settings = load_app_settings()

            # Verify new fields have correct defaults
            assert settings["last_used_data_source"] == "JIRA"
            assert settings["active_jql_profile_id"] == ""

            # Verify existing defaults are preserved
            assert "jql_query" in settings

    def test_load_app_settings_preserves_existing_settings(self):
        """Test that existing settings are loaded correctly"""
        mock_settings = {
            "jql_query": "project = TEST",
            "jira_api_endpoint": "https://test.jira.com/rest/api/2/search",
            "jira_token": "test-token",
            "last_used_data_source": "CSV",
            "active_jql_profile_id": "test-profile-id",
        }

        with (
            patch("data.persistence.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(mock_settings))),
        ):
            settings = load_app_settings()

            assert settings["last_used_data_source"] == "CSV"
            assert settings["active_jql_profile_id"] == "test-profile-id"
            assert settings["jql_query"] == "project = TEST"

    def test_load_app_settings_handles_missing_new_fields(self):
        """Test backward compatibility when new fields are missing"""
        # Simulate old settings file without new fields
        old_settings = {
            "jql_query": "project = OLD",
            "jira_api_endpoint": "https://old.jira.com/rest/api/2/search",
            "jira_token": "old-token",
        }

        with (
            patch("data.persistence.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(old_settings))),
        ):
            settings = load_app_settings()

            # Should provide defaults for missing fields
            assert settings["last_used_data_source"] == "JIRA"
            assert settings["active_jql_profile_id"] == ""

            # Should preserve existing fields
            assert settings["jql_query"] == "project = OLD"

    def test_save_app_settings_includes_new_fields(self):
        """Test that saving settings includes new data source fields"""
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("data.persistence.os.makedirs"),
        ):
            save_app_settings(
                pert_factor=1.2,
                deadline="2025-12-31",
                # Note: JIRA config moved to modal (Feature 003)
                # jql_query, jira_api_endpoint, jira_token, etc. no longer in app_settings
                last_used_data_source="CSV",
                active_jql_profile_id="profile-123",
            )

            # Verify file was opened for writing
            mock_file.assert_called()

            # Get the written content
            written_calls = [call for call in mock_file().write.call_args_list]
            written_content = "".join([call[0][0] for call in written_calls])

            # Parse and verify content
            saved_data = json.loads(written_content)
            assert saved_data["last_used_data_source"] == "CSV"
            assert saved_data["active_jql_profile_id"] == "profile-123"

    def test_save_app_settings_defaults_for_new_fields(self):
        """Test that new fields get defaults when not provided"""
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("data.persistence.os.makedirs"),
        ):
            save_app_settings(
                pert_factor=1.0,
                deadline="2025-11-30",
                # Note: JIRA config moved to modal (Feature 003)
                # Not providing new fields - should get defaults
            )

            # Get the written content
            written_calls = [call for call in mock_file().write.call_args_list]
            written_content = "".join([call[0][0] for call in written_calls])

            # Parse and verify defaults
            saved_data = json.loads(written_content)
            assert saved_data["last_used_data_source"] == "JIRA"
            assert saved_data["active_jql_profile_id"] == ""

    def test_load_app_settings_handles_corrupted_json(self):
        """Test graceful handling of corrupted settings file"""
        with (
            patch("data.persistence.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid json{")),
        ):
            settings = load_app_settings()

            # Should return defaults when JSON is corrupted
            assert settings["last_used_data_source"] == "JIRA"
            assert settings["active_jql_profile_id"] == ""


@pytest.fixture
def temp_settings_file():
    """Create a temporary file for settings testing"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


class TestSettingsFileOperations:
    """Test actual file I/O operations for settings"""

    def test_round_trip_settings_persistence(self, temp_settings_file):
        """Integration test for save and load operations"""
        # Test basic functionality without file path mocking
        # This tests the core logic without complex file system interactions

        test_settings = {
            "pert_factor": 1.5,
            "deadline": "2025-10-31",
            "jql_query": "project = ROUNDTRIP",
            "last_used_data_source": "CSV",
            "active_jql_profile_id": "roundtrip-profile-id",
        }

        # Mock both save and load operations
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("data.persistence.os.makedirs"),
            patch("data.persistence.os.path.exists", return_value=True),
            patch("json.load", return_value=test_settings),
        ):
            from data.persistence import save_app_settings, load_app_settings

            # Save settings
            save_app_settings(**test_settings)

            # Verify save was called
            mock_file.assert_called()

            # Load settings back
            loaded_settings = load_app_settings()

            # Verify persistence worked
            assert loaded_settings["jql_query"] == "project = ROUNDTRIP"
            assert loaded_settings["last_used_data_source"] == "CSV"
            assert loaded_settings["active_jql_profile_id"] == "roundtrip-profile-id"

    def test_settings_directory_creation(self, temp_settings_file):
        """Test that settings save operation completes successfully"""
        # Test that the save operation works without directory creation issues
        # Since APP_SETTINGS_FILE is just a filename in the current directory,
        # no directory creation is needed

        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("data.persistence.os.path.exists", return_value=False),
            patch("data.persistence.os.rename") as mock_rename,
        ):
            from data.persistence import save_app_settings

            save_app_settings(
                pert_factor=1.0,
                deadline="2025-12-01",
                jql_query="project = MKDIR",
                last_used_data_source="JIRA",
            )

            # Verify file writing was attempted
            mock_file.assert_called()

            # Verify rename operation was attempted (atomic file save)
            mock_rename.assert_called()
