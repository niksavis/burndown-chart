"""
Unit tests for profile_manager path resolution functions.

Tests the critical path abstraction layer that enables profile-based data organization.
Uses SQLite database backend via temp_database fixture.
"""

from pathlib import Path

import pytest

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
        self, temp_database
    ):
        """Verify get_active_profile_workspace returns active profile directory."""
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_profile_workspace

        # Arrange
        backend = get_backend()
        profile_data = {
            "id": "kafka",
            "name": "Apache Kafka",
            "description": "",
            "created_at": "2025-11-13T10:00:00Z",
            "last_used": "2025-11-13T10:00:00Z",
            "jira_config": {},
            "field_mappings": {},
            "forecast_settings": {},
            "project_classification": {},
            "flow_type_mappings": {},
        }
        backend.save_profile(profile_data)
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "12w")

        # Act
        result = get_active_profile_workspace()

        # Assert
        # Result should be profiles/kafka
        assert result.name == "kafka"
        assert "profiles" in str(result)
        assert isinstance(result, Path)

    def test_get_active_profile_workspace_raises_if_no_profiles_file(
        self, temp_database
    ):
        """Verify get_active_profile_workspace raises if no active profile set."""
        from data.profile_manager import get_active_profile_workspace

        # Act & Assert - no app_state set
        with pytest.raises(ValueError, match="No active_profile_id"):
            get_active_profile_workspace()

    def test_get_active_profile_workspace_raises_if_invalid_profile(
        self, temp_database
    ):
        """Verify get_active_profile_workspace raises if active_profile_id invalid."""
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_profile_workspace

        # Arrange - set active_profile_id but don't create profile
        backend = get_backend()
        backend.set_app_state("active_profile_id", "nonexistent")

        # Act & Assert
        with pytest.raises(ValueError, match="Profile.*not found"):
            get_active_profile_workspace()

    def test_get_active_query_workspace_returns_active_query_dir(self, temp_database):
        """Verify get_active_query_workspace returns active query directory."""
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_query_workspace

        # Arrange
        backend = get_backend()
        profile_data = {
            "id": "kafka",
            "name": "Apache Kafka",
            "description": "",
            "created_at": "2025-11-13T10:00:00Z",
            "last_used": "2025-11-13T10:00:00Z",
            "jira_config": {},
            "field_mappings": {},
            "forecast_settings": {},
            "project_classification": {},
            "flow_type_mappings": {},
        }
        backend.save_profile(profile_data)
        query_data = {
            "id": "bugs",
            "name": "Bugs Query",
            "jql": "type = Bug",
            "created_at": "2025-11-13T10:00:00Z",
            "last_used": "2025-11-13T10:00:00Z",
        }
        backend.save_query("kafka", query_data)
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "bugs")

        # Act
        result = get_active_query_workspace()

        # Assert
        # Result should be profiles/kafka/queries/bugs
        assert result.name == "bugs"
        assert "queries" in str(result)
        assert "kafka" in str(result)
        assert isinstance(result, Path)

    def test_get_active_query_workspace_raises_if_no_profiles_file(self, temp_database):
        """Verify get_active_query_workspace raises if no active profile set."""
        from data.profile_manager import get_active_query_workspace

        # Act & Assert - no app_state set
        with pytest.raises(ValueError, match="No active_profile_id"):
            get_active_query_workspace()

    def test_get_active_query_workspace_raises_if_invalid_query(self, temp_database):
        """Verify get_active_query_workspace raises if active_query_id invalid."""
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_query_workspace

        # Arrange
        backend = get_backend()
        profile_data = {
            "id": "kafka",
            "name": "Apache Kafka",
            "description": "",
            "created_at": "2025-11-13T10:00:00Z",
            "last_used": "2025-11-13T10:00:00Z",
            "jira_config": {},
            "field_mappings": {},
            "forecast_settings": {},
            "project_classification": {},
            "flow_type_mappings": {},
        }
        backend.save_profile(profile_data)
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "nonexistent")  # Query doesn't exist

        # Act & Assert
        with pytest.raises(ValueError, match="Query.*not found"):
            get_active_query_workspace()

    def test_get_active_query_workspace_uses_default_profile_after_migration(
        self, temp_database
    ):
        """Verify get_active_query_workspace works with default profile."""
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_query_workspace

        # Arrange
        backend = get_backend()
        profile_data = {
            "id": DEFAULT_PROFILE_ID,
            "name": "Default",
            "description": "",
            "created_at": "2025-11-13T10:00:00Z",
            "last_used": "2025-11-13T10:00:00Z",
            "jira_config": {},
            "field_mappings": {},
            "forecast_settings": {},
            "project_classification": {},
            "flow_type_mappings": {},
        }
        backend.save_profile(profile_data)
        query_data = {
            "id": DEFAULT_QUERY_ID,
            "name": "Default Query",
            "jql": "project = DEFAULT",
            "created_at": "2025-11-13T10:00:00Z",
            "last_used": "2025-11-13T10:00:00Z",
        }
        backend.save_query(DEFAULT_PROFILE_ID, query_data)
        backend.set_app_state("active_profile_id", DEFAULT_PROFILE_ID)
        backend.set_app_state("active_query_id", DEFAULT_QUERY_ID)

        # Act
        result = get_active_query_workspace()

        # Assert
        assert result.name == DEFAULT_QUERY_ID
        assert DEFAULT_PROFILE_ID in str(result)
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
