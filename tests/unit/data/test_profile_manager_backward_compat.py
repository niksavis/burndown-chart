"""
Unit tests for profile_manager backward compatibility layer.

Tests the path abstraction functions that enable transparent operation
in both legacy mode (no profiles.json) and profiles mode (with profiles.json).

CRITICAL: All imports from data.profile_manager must happen INSIDE test methods
where fixture patches are active. Module-level imports resolve paths at import
time based on os.getcwd(), before fixtures can override PROFILES_DIR.
"""

import json
import pytest

# NO module-level imports from data.profile_manager - they must be inside tests
# where temp_profiles_dir fixture patches are active


@pytest.mark.unit
@pytest.mark.profile_tests
class TestBackwardCompatibility:
    """Test backward compatibility layer (T010)."""

    def test_is_profiles_mode_disabled_when_no_profiles_json(self, temp_profiles_dir):
        """Verify legacy mode detected when profiles.json missing."""
        from data.profile_manager import PROFILES_FILE, is_profiles_mode_enabled

        # Arrange: profiles.json doesn't exist
        assert not PROFILES_FILE.exists()

        # Act
        result = is_profiles_mode_enabled()

        # Assert
        assert result is False

    def test_is_profiles_mode_enabled_when_profiles_json_exists(
        self, temp_profiles_dir_with_default
    ):
        """Verify profiles mode detected when profiles.json exists."""
        from data.profile_manager import is_profiles_mode_enabled

        # Arrange: Create profiles.json
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "default",
            "active_query_id": "main",
            "profiles": {"default": {"name": "Default", "queries": ["main"]}},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act
        result = is_profiles_mode_enabled()

        # Assert
        assert result is True

    def test_get_data_file_path_returns_root_in_legacy_mode(self, temp_profiles_dir):
        """Verify data files resolve to root directory when profiles.json missing."""
        from data.profile_manager import PROFILES_FILE, get_data_file_path

        # Arrange: No profiles.json (legacy mode)
        assert not PROFILES_FILE.exists()

        # Act
        result = get_data_file_path("jira_cache.json")

        # Assert
        assert result.name == "jira_cache.json"
        assert "profiles" not in str(result)  # Not in profiles directory

    def test_get_data_file_path_returns_query_workspace_in_profiles_mode(
        self, temp_profiles_dir_with_default
    ):
        """Verify data files resolve to active query workspace in profiles mode."""
        from data.profile_manager import get_data_file_path

        # Arrange: Create valid profiles.json
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "default",
            "active_query_id": "main",
            "profiles": {"default": {"name": "Default", "queries": ["main"]}},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act
        result = get_data_file_path("jira_cache.json")

        # Assert
        assert result.name == "jira_cache.json"
        assert "profiles" in str(result)
        assert "default" in str(result)
        assert "queries" in str(result)
        assert "main" in str(result)

    def test_get_data_file_path_falls_back_to_legacy_if_profiles_malformed(
        self, temp_profiles_dir_with_default
    ):
        """Verify fallback to legacy mode if profiles.json is malformed."""
        from data.profile_manager import get_data_file_path

        # Arrange: Create malformed profiles.json (missing active_query_id)
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "default",
            # Missing active_query_id
            "profiles": {"default": {"name": "Default"}},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act
        result = get_data_file_path("jira_cache.json")

        # Assert: Should fall back to legacy mode
        assert result.name == "jira_cache.json"
        # Gracefully handle malformed config by returning root-level path

    def test_get_settings_file_path_uses_same_logic_as_data_files(
        self, temp_profiles_dir
    ):
        """Verify settings files use same path resolution as data files."""
        from data.profile_manager import (
            PROFILES_FILE,
            get_data_file_path,
            get_settings_file_path,
        )

        # Arrange: Legacy mode
        assert not PROFILES_FILE.exists()

        # Act
        data_path = get_data_file_path("app_settings.json")
        settings_path = get_settings_file_path("app_settings.json")

        # Assert: Should return same path
        assert data_path == settings_path

    def test_get_data_file_path_handles_different_filenames(
        self, temp_profiles_dir_with_default
    ):
        """Verify path resolution works for various data files."""
        from data.profile_manager import get_data_file_path

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "12w",
            "profiles": {"kafka": {"name": "Apache Kafka", "queries": ["12w"]}},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act
        cache_path = get_data_file_path("jira_cache.json")
        changelog_path = get_data_file_path("jira_changelog_cache.json")
        snapshots_path = get_data_file_path("metrics_snapshots.json")

        # Assert: All resolve to same query workspace
        assert cache_path.parent == changelog_path.parent == snapshots_path.parent
        assert "kafka" in str(cache_path)
        assert "12w" in str(cache_path)


@pytest.mark.unit
@pytest.mark.profile_tests
class TestLegacyModeCompatibility:
    """Test that existing code continues to work without profiles.json."""

    def test_legacy_mode_uses_root_directory(self, temp_profiles_dir):
        """Verify legacy installations (no profiles/) work unchanged."""
        from data.profile_manager import (
            PROFILES_FILE,
            get_settings_file_path,
            get_data_file_path,
        )

        # Arrange: No profiles.json exists (simulates existing installation)
        assert not PROFILES_FILE.exists()

        # Act: Get paths for all data files
        app_settings = get_settings_file_path("app_settings.json")
        project_data = get_settings_file_path("project_data.json")
        jira_cache = get_data_file_path("jira_cache.json")

        # Assert: All paths point to root directory
        assert app_settings.name == "app_settings.json"
        assert project_data.name == "project_data.json"
        assert jira_cache.name == "jira_cache.json"
        # Verify NOT in profiles directory
        for path in [app_settings, project_data, jira_cache]:
            assert "profiles" not in str(path)

    def test_profiles_mode_isolates_data_to_query_workspace(
        self, temp_profiles_dir_with_default
    ):
        """Verify profiles mode isolates data to query-specific directories."""
        from data.profile_manager import get_data_file_path

        # Arrange: profiles.json exists with two queries
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "bugs",
            "profiles": {"kafka": {"name": "Apache Kafka", "queries": ["12w", "bugs"]}},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act
        cache_path = get_data_file_path("jira_cache.json")

        # Assert: Path includes active query workspace
        assert (
            cache_path
            == temp_profiles_dir_with_default
            / "kafka"
            / "queries"
            / "bugs"
            / "jira_cache.json"
        )
