"""
Unit tests for profile_manager path resolution functions.

Tests the critical path abstraction layer that enables profile-based data organization.
These functions BLOCK all user stories and must be implemented first.

Note: Imports are done inside tests to ensure mocked paths take effect.
The temp_profiles_dir fixture patches PROFILES_DIR, but it must be active
before imports resolve the Path.absolute() calls.
"""

import json
import pytest
from pathlib import Path

# Import constants that don't need patching
from data.profile_manager import DEFAULT_PROFILE_ID, DEFAULT_QUERY_ID


@pytest.mark.unit
@pytest.mark.profile_tests
class TestPathResolutionFunctions:
    """Test path resolution functions (T006-T007)."""

    def test_get_profile_file_path_returns_correct_path(self, temp_profiles_dir):
        """Verify get_profile_file_path constructs correct path."""
        # Import inside test where patch is active
        from data.profile_manager import get_profile_file_path

        # Act
        result = get_profile_file_path("kafka")

        # Assert
        assert result == temp_profiles_dir / "kafka" / "profile.json"
        assert isinstance(result, Path)

    def test_get_query_file_path_returns_correct_path(self, temp_profiles_dir):
        """Verify get_query_file_path constructs correct path."""
        from data.profile_manager import get_query_file_path

        # Act
        result = get_query_file_path("kafka", "12w")

        # Assert
        assert result == temp_profiles_dir / "kafka" / "queries" / "12w" / "query.json"
        assert isinstance(result, Path)

    def test_get_jira_cache_path_returns_correct_path(self, temp_profiles_dir):
        """Verify get_jira_cache_path constructs correct path."""
        from data.profile_manager import get_jira_cache_path

        # Act
        result = get_jira_cache_path("kafka", "bugs")

        # Assert
        assert (
            result
            == temp_profiles_dir / "kafka" / "queries" / "bugs" / "jira_cache.json"
        )
        assert isinstance(result, Path)

    def test_get_active_profile_workspace_returns_active_profile_dir(
        self, temp_profiles_dir_with_default
    ):
        """Verify get_active_profile_workspace returns active profile directory."""
        from data.profile_manager import get_active_profile_workspace

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "12w",
            "profiles": {
                "kafka": {"name": "Apache Kafka", "created_at": "2025-11-13T10:00:00Z"}
            },
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act
        result = get_active_profile_workspace()

        # Assert
        assert result == temp_profiles_dir_with_default / "kafka"
        assert isinstance(result, Path)

    def test_get_active_profile_workspace_raises_if_no_profiles_file(
        self, temp_profiles_dir
    ):
        """Verify get_active_profile_workspace raises if profiles.json missing."""
        from data.profile_manager import get_active_profile_workspace

        # Act & Assert
        with pytest.raises(ValueError, match="profiles.json not found"):
            get_active_profile_workspace()

    def test_get_active_profile_workspace_raises_if_invalid_profile(
        self, temp_profiles_dir_with_default
    ):
        """Verify get_active_profile_workspace raises if active_profile_id invalid."""
        from data.profile_manager import get_active_profile_workspace

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "nonexistent",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act & Assert
        with pytest.raises(ValueError, match="Profile.*not found"):
            get_active_profile_workspace()

    def test_get_active_query_workspace_returns_active_query_dir(
        self, temp_profiles_dir_with_default
    ):
        """Verify get_active_query_workspace returns active query directory."""
        from data.profile_manager import get_active_query_workspace

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "bugs",
            "profiles": {"kafka": {"name": "Apache Kafka", "queries": ["12w", "bugs"]}},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act
        result = get_active_query_workspace()

        # Assert
        assert result == temp_profiles_dir_with_default / "kafka" / "queries" / "bugs"
        assert isinstance(result, Path)

    def test_get_active_query_workspace_raises_if_no_profiles_file(
        self, temp_profiles_dir
    ):
        """Verify get_active_query_workspace raises if profiles.json missing."""
        from data.profile_manager import get_active_query_workspace

        # Act & Assert
        with pytest.raises(ValueError, match="profiles.json not found"):
            get_active_query_workspace()

    def test_get_active_query_workspace_raises_if_invalid_query(
        self, temp_profiles_dir_with_default
    ):
        """Verify get_active_query_workspace raises if active_query_id invalid."""
        from data.profile_manager import get_active_query_workspace

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "nonexistent",
            "profiles": {"kafka": {"name": "Apache Kafka", "queries": ["12w"]}},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act & Assert
        with pytest.raises(ValueError, match="Query.*not found"):
            get_active_query_workspace()

    def test_get_active_query_workspace_uses_default_profile_after_migration(
        self, temp_profiles_dir_with_default
    ):
        """Verify get_active_query_workspace works with default profile."""
        from data.profile_manager import get_active_query_workspace

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": DEFAULT_PROFILE_ID,
            "active_query_id": DEFAULT_QUERY_ID,
            "profiles": {
                DEFAULT_PROFILE_ID: {
                    "name": "Default",
                    "queries": [DEFAULT_QUERY_ID],
                }
            },
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act
        result = get_active_query_workspace()

        # Assert
        assert (
            result
            == temp_profiles_dir_with_default
            / DEFAULT_PROFILE_ID
            / "queries"
            / DEFAULT_QUERY_ID
        )
        assert isinstance(result, Path)


@pytest.mark.unit
@pytest.mark.profile_tests
class TestPathResolutionEdgeCases:
    """Test edge cases for path resolution."""

    def test_profile_id_with_special_characters(self, temp_profiles_dir):
        """Verify path construction handles profile IDs with dashes/underscores."""
        from data.profile_manager import get_profile_file_path

        # Act
        result = get_profile_file_path("my-project_2025")

        # Assert
        assert result == temp_profiles_dir / "my-project_2025" / "profile.json"

    def test_query_id_with_numbers(self, temp_profiles_dir):
        """Verify path construction handles query IDs with numbers."""
        from data.profile_manager import get_query_file_path

        # Act
        result = get_query_file_path("kafka", "12w")

        # Assert
        assert result == temp_profiles_dir / "kafka" / "queries" / "12w" / "query.json"

    def test_deeply_nested_structure_integrity(self, temp_profiles_dir):
        """Verify correct nesting: profile/queries/query/cache."""
        from data.profile_manager import get_jira_cache_path

        # Act
        cache_path = get_jira_cache_path("kafka", "bugs")

        # Assert
        expected_parts = ["profiles", "kafka", "queries", "bugs", "jira_cache.json"]
        assert all(part in str(cache_path) for part in expected_parts)
