"""
Integration Tests for Data Source Switching Feature

Tests the complete workflow of switching between data sources and persistence.
Covers the recently implemented end-to-end functionality for multiple JQL queries.
"""

import json
import tempfile
import os
from unittest.mock import patch

# Note: Following the coding instructions to avoid dash.testing utilities
# These tests focus on data flow integration without browser automation


class TestDataSourceSwitchingIntegration:
    """Test end-to-end data source switching functionality"""

    def test_data_source_persistence_workflow(self):
        """Test complete workflow: save settings -> load settings -> UI components"""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = os.path.join(temp_dir, "app_settings.json")

            # Mock the settings file path
            with patch("data.persistence.SETTINGS_FILE", settings_file):
                # Step 1: Import and use save function
                from data.persistence import save_app_settings, load_app_settings

                # Save settings with CSV as data source
                save_app_settings(
                    pert_factor=1.2,
                    deadline="2025-12-31",
                    jql_query="project = INTEGRATION",
                    last_used_data_source="CSV",
                    active_jql_profile_id="integration-profile",
                )

                # Step 2: Load settings back
                loaded_settings = load_app_settings()
                assert loaded_settings["last_used_data_source"] == "CSV"
                assert loaded_settings["active_jql_profile_id"] == "integration-profile"

                # Step 3: Test UI components use persisted values
                with patch(
                    "data.persistence.load_app_settings", return_value=loaded_settings
                ):
                    from ui.cards import (
                        _get_default_data_source,
                        _get_default_jql_profile_id,
                    )

                    data_source = _get_default_data_source()
                    profile_id = _get_default_jql_profile_id()

                    assert data_source == "CSV"
                    assert profile_id == "integration-profile"

    def test_query_profile_and_settings_integration(self):
        """Test integration between query profiles and app settings"""
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_file = os.path.join(temp_dir, "jira_query_profiles.json")
            settings_file = os.path.join(temp_dir, "app_settings.json")

            with (
                patch("data.jira_query_manager.QUERY_PROFILES_FILE", profiles_file),
                patch("data.persistence.SETTINGS_FILE", settings_file),
            ):
                # Step 1: Create a query profile
                from data.jira_query_manager import (
                    save_query_profile,
                    get_query_profile_by_id,
                )
                from data.persistence import save_app_settings, load_app_settings

                profile = save_query_profile(
                    name="Integration Test Query",
                    jql="project = INTEGRATION AND status = 'To Do'",
                    description="Test query for integration",
                )

                assert profile is not None
                profile_id = profile["id"]

                # Step 2: Save app settings with this profile as active
                save_app_settings(
                    pert_factor=1.0,
                    deadline="2025-11-30",
                    last_used_data_source="JIRA",
                    active_jql_profile_id=profile_id,
                )

                # Step 3: Verify the integration works
                loaded_settings = load_app_settings()
                assert loaded_settings["active_jql_profile_id"] == profile_id

                # Step 4: Verify the profile can be retrieved
                retrieved_profile = get_query_profile_by_id(profile_id)
                assert retrieved_profile is not None
                assert retrieved_profile["name"] == "Integration Test Query"

                # Step 5: Test UI components work with integrated data
                with patch(
                    "data.persistence.load_app_settings", return_value=loaded_settings
                ):
                    from ui.cards import (
                        _get_default_jql_profile_id,
                        _get_default_data_source,
                    )

                    ui_profile_id = _get_default_jql_profile_id()
                    ui_data_source = _get_default_data_source()

                    assert ui_profile_id == profile_id
                    assert ui_data_source == "JIRA"

    def test_backward_compatibility_integration(self):
        """Test that new features work with existing data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = os.path.join(temp_dir, "app_settings.json")

            # Step 1: Create old-format settings file (simulating existing user data)
            old_settings = {
                "pert_factor": 1.5,
                "deadline": "2025-10-15",
                "jql_query": "project = OLD_PROJECT",
                "jira_api_endpoint": "https://old.atlassian.net/rest/api/2/search",
                "jira_token": "old-token",
                # Note: Missing new fields (last_used_data_source, active_jql_profile_id)
            }

            with open(settings_file, "w") as f:
                json.dump(old_settings, f)

            # Step 2: Test that loading provides defaults for new fields
            with patch("data.persistence.APP_SETTINGS_FILE", settings_file):
                from data.persistence import load_app_settings

                loaded_settings = load_app_settings()

                # Should preserve old fields
                assert loaded_settings["jql_query"] == "project = OLD_PROJECT"
                assert loaded_settings["jira_token"] == "old-token"

                # Should provide defaults for new fields
                assert loaded_settings["last_used_data_source"] == "JIRA"
                assert loaded_settings["active_jql_profile_id"] == ""

            # Step 3: Test UI components work with backward compatible data
            with patch(
                "data.persistence.load_app_settings", return_value=loaded_settings
            ):
                from ui.cards import (
                    _get_default_data_source,
                    _get_default_jql_profile_id,
                )

                data_source = _get_default_data_source()
                profile_id = _get_default_jql_profile_id()

                assert data_source == "JIRA"  # Default for missing field
                assert profile_id == ""  # Default for missing field

    def test_data_source_switch_simulation(self):
        """Test simulated user workflow of switching data sources"""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = os.path.join(temp_dir, "app_settings.json")

            with patch("data.persistence.SETTINGS_FILE", settings_file):
                from data.persistence import save_app_settings, load_app_settings

                # Step 1: Initial state - JIRA selected
                save_app_settings(
                    pert_factor=1.0, deadline="2025-12-01", last_used_data_source="JIRA"
                )

                settings1 = load_app_settings()
                assert settings1["last_used_data_source"] == "JIRA"

                # Step 2: User switches to CSV/JSON
                save_app_settings(
                    pert_factor=1.0, deadline="2025-12-01", last_used_data_source="CSV"
                )

                settings2 = load_app_settings()
                assert settings2["last_used_data_source"] == "CSV"

                # Step 3: User switches back to JIRA with a profile
                save_app_settings(
                    pert_factor=1.0,
                    deadline="2025-12-01",
                    last_used_data_source="JIRA",
                    active_jql_profile_id="default-all-issues",
                )

                settings3 = load_app_settings()
                assert settings3["last_used_data_source"] == "JIRA"
                assert settings3["active_jql_profile_id"] == "default-all-issues"

    def test_default_profiles_availability(self):
        """Test that default query profiles are always available"""
        # This test doesn't require file mocking as it tests the default behavior
        from data.jira_query_manager import load_query_profiles

        # Even with no user profiles file, should have defaults
        with patch("data.jira_query_manager.os.path.exists", return_value=False):
            profiles = load_query_profiles()

            assert len(profiles) == 3

            profile_names = [p["name"] for p in profiles]
            assert "All Open Issues" in profile_names
            assert "Recent Bugs (Last 2 Weeks)" in profile_names
            assert "Current Sprint" in profile_names

            # All should be marked as default
            assert all(p["is_default"] for p in profiles)

            # All should have required fields
            for profile in profiles:
                assert "id" in profile
                assert "jql" in profile
                assert "created_at" in profile
                assert "last_used" in profile

    def test_error_handling_integration(self):
        """Test error handling across the data source switching system"""
        # Test with corrupted settings file
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = os.path.join(temp_dir, "app_settings.json")

            # Create corrupted JSON file
            with open(settings_file, "w") as f:
                f.write("{ invalid json content")

            with patch("data.persistence.APP_SETTINGS_FILE", settings_file):
                from data.persistence import load_app_settings

                # Should handle corruption gracefully
                settings = load_app_settings()
                assert settings["last_used_data_source"] == "JIRA"  # Default
                assert settings["active_jql_profile_id"] == ""  # Default

            # Test UI components handle errors gracefully
            with patch(
                "data.persistence.load_app_settings",
                side_effect=Exception("Mock error"),
            ):
                from ui.cards import (
                    _get_default_data_source,
                    _get_default_jql_profile_id,
                )

                # Should fall back to safe defaults (due to ImportError handling)
                data_source = _get_default_data_source()
                profile_id = _get_default_jql_profile_id()

                assert data_source == "JIRA"
                assert profile_id == ""


class TestDataValidationIntegration:
    """Test validation across the integrated system"""

    def test_invalid_data_source_handling(self):
        """Test handling of invalid data source values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = os.path.join(temp_dir, "app_settings.json")

            # Create settings with invalid data source
            invalid_settings = {
                "last_used_data_source": "INVALID_SOURCE",
                "active_jql_profile_id": "nonexistent-profile",
            }

            with open(settings_file, "w") as f:
                json.dump(invalid_settings, f)

            with patch("data.persistence.APP_SETTINGS_FILE", settings_file):
                from data.persistence import load_app_settings

                settings = load_app_settings()

                # Should load the invalid values (validation happens in UI)
                assert settings["last_used_data_source"] == "INVALID_SOURCE"
                assert settings["active_jql_profile_id"] == "nonexistent-profile"

            # UI components should handle gracefully
            with patch("data.persistence.load_app_settings", return_value=settings):
                from ui.cards import (
                    _get_default_data_source,
                    _get_default_jql_profile_id,
                )

                # Should return the stored values (UI will validate)
                data_source = _get_default_data_source()
                profile_id = _get_default_jql_profile_id()

                assert data_source == "INVALID_SOURCE"
                assert profile_id == "nonexistent-profile"
