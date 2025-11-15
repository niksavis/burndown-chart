"""
Unit Tests for Data Source Persistence - DEPRECATED

⚠️ DEPRECATION NOTICE:
These tests verified the old app_settings.json storage pattern that was replaced
by the profile-based architecture (profiles/{profile_id}/profile.json).

New tests for profile-based storage are in test_profile_settings_integration.py,
which all pass successfully.

Keeping these tests marked as skipped for historical reference and potential
migration validation if needed.
"""

import json
import tempfile
import os
from unittest.mock import patch, mock_open
import pytest

from data.persistence import save_app_settings, load_app_settings


@pytest.mark.skip(
    reason="Obsolete: Tests old app_settings.json pattern. Profile-based storage tested in test_profile_settings_integration.py"
)
class TestDataSourcePersistence:
    """Test data source selection persistence functionality - DEPRECATED"""

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
        import tempfile
        from pathlib import Path

        mock_settings = {
            "jql_query": "project = TEST",
            "jira_api_endpoint": "https://test.jira.com/rest/api/2/search",
            "jira_token": "test-token",
            "last_used_data_source": "CSV",
            "active_jql_profile_id": "test-profile-id",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = Path(tmpdir) / "app_settings.json"
            settings_file.write_text(json.dumps(mock_settings))

            with patch(
                "data.persistence.get_active_query_workspace", return_value=Path(tmpdir)
            ):
                settings = load_app_settings()

                assert settings["last_used_data_source"] == "CSV"
                assert settings["active_jql_profile_id"] == "test-profile-id"
                assert settings["jql_query"] == "project = TEST"

    def test_load_app_settings_handles_missing_new_fields(self):
        """Test backward compatibility when new fields are missing"""
        import tempfile
        from pathlib import Path

        # Simulate old settings file without new fields
        old_settings = {
            "jql_query": "project = OLD",
            "jira_api_endpoint": "https://old.jira.com/rest/api/2/search",
            "jira_token": "old-token",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = Path(tmpdir) / "app_settings.json"
            settings_file.write_text(json.dumps(old_settings))

            with patch(
                "data.persistence.get_active_query_workspace", return_value=Path(tmpdir)
            ):
                settings = load_app_settings()

                # Should provide defaults for missing fields
                assert settings["last_used_data_source"] == "JIRA"
                assert settings["active_jql_profile_id"] == ""

                # Should preserve existing fields
                assert settings["jql_query"] == "project = OLD"

    def test_save_app_settings_includes_new_fields(self):
        """Test that saving settings includes new data source fields"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "data.persistence.get_active_query_workspace", return_value=Path(tmpdir)
            ):
                save_app_settings(
                    pert_factor=1.2,
                    deadline="2025-12-31",
                    # Note: JIRA config moved to modal (Feature 003)
                    # jql_query, jira_api_endpoint, jira_token, etc. no longer in app_settings
                    last_used_data_source="CSV",
                    active_jql_profile_id="profile-123",
                )

                # Read the written file
                settings_file = Path(tmpdir) / "app_settings.json"
                assert settings_file.exists()

                saved_data = json.loads(settings_file.read_text())
                assert saved_data["last_used_data_source"] == "CSV"
                assert saved_data["active_jql_profile_id"] == "profile-123"

    def test_save_app_settings_defaults_for_new_fields(self):
        """Test that new fields get defaults when not provided"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "data.persistence.get_active_query_workspace", return_value=Path(tmpdir)
            ):
                save_app_settings(
                    pert_factor=1.0,
                    deadline="2025-11-30",
                    # Note: JIRA config moved to modal (Feature 003)
                    # Not providing new fields - should get defaults
                )

                # Read the written file
                settings_file = Path(tmpdir) / "app_settings.json"
                saved_data = json.loads(settings_file.read_text())
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
    """Create a temporary file for settings testing - DEPRECATED"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.mark.skip(
    reason="Obsolete: Tests old app_settings.json pattern. Profile-based storage tested in test_profile_settings_integration.py"
)
class TestSettingsFileOperations:
    """Test actual file I/O operations for settings - DEPRECATED"""

    def test_round_trip_settings_persistence(self, temp_settings_file):
        """Integration test for save and load operations"""
        import tempfile
        from pathlib import Path

        test_settings = {
            "pert_factor": 1.5,
            "deadline": "2025-10-31",
            "jql_query": "project = ROUNDTRIP",
            "last_used_data_source": "CSV",
            "active_jql_profile_id": "roundtrip-profile-id",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "data.persistence.get_active_query_workspace", return_value=Path(tmpdir)
            ):
                from data.persistence import save_app_settings, load_app_settings

                # Save settings
                save_app_settings(**test_settings)

                # Load settings back
                loaded_settings = load_app_settings()

                # Verify persistence worked
                assert loaded_settings["jql_query"] == "project = ROUNDTRIP"
                assert loaded_settings["last_used_data_source"] == "CSV"
                assert (
                    loaded_settings["active_jql_profile_id"] == "roundtrip-profile-id"
                )

    def test_settings_directory_creation(self, temp_settings_file):
        """Test that settings save operation completes successfully"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "data.persistence.get_active_query_workspace", return_value=Path(tmpdir)
            ):
                from data.persistence import save_app_settings

                save_app_settings(
                    pert_factor=1.0,
                    deadline="2025-12-01",
                    jql_query="project = MKDIR",
                    last_used_data_source="JIRA",
                )

                # Verify file was created
                settings_file = Path(tmpdir) / "app_settings.json"
                assert settings_file.exists()

                # Verify content is valid JSON
                saved_data = json.loads(settings_file.read_text())
                assert saved_data["jql_query"] == "project = MKDIR"
