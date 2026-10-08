from pathlib import Path

import pytest

from data.profile_manager import DEFAULT_PROFILE_ID, DEFAULT_QUERY_ID


@pytest.mark.unit
@pytest.mark.profile_tests
class TestPathResolutionFunctions:
    def test_get_profile_file_path_returns_correct_path(self, temp_profiles_dir):
        from data.profile_manager import get_profile_file_path

        result = get_profile_file_path("kafka")

        assert result == temp_profiles_dir / "kafka" / "profile.json"
        assert isinstance(result, Path)

    def test_get_query_file_path_returns_correct_path(self, temp_profiles_dir):
        from data.profile_manager import get_query_file_path

        result = get_query_file_path("kafka", "12w")

        assert result == temp_profiles_dir / "kafka" / "queries" / "12w" / "query.json"
        assert isinstance(result, Path)

    def test_get_jira_cache_path_returns_correct_path(self, temp_profiles_dir):
        from data.profile_manager import get_jira_cache_path

        result = get_jira_cache_path("kafka", "bugs")

        assert (
            result
            == temp_profiles_dir / "kafka" / "queries" / "bugs" / "jira_cache.json"
        )
        assert isinstance(result, Path)

    def test_get_active_profile_workspace_returns_active_profile_dir(
        self, temp_database
    ):
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_profile_workspace

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

        result = get_active_profile_workspace()

        assert result.name == "kafka"
        assert "profiles" in str(result)
        assert isinstance(result, Path)

    def test_get_active_profile_workspace_raises_if_no_profiles_file(
        self, temp_database
    ):
        from data.profile_manager import get_active_profile_workspace

        with pytest.raises(ValueError, match="No active_profile_id"):
            get_active_profile_workspace()

    def test_get_active_profile_workspace_raises_if_invalid_profile(
        self, temp_database
    ):
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_profile_workspace

        backend = get_backend()
        backend.set_app_state("active_profile_id", "nonexistent")

        with pytest.raises(ValueError, match="Profile.*not found"):
            get_active_profile_workspace()

    def test_get_active_query_workspace_returns_active_query_dir(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_query_workspace

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

        result = get_active_query_workspace()

        assert result.name == "bugs"
        assert "queries" in str(result)
        assert "kafka" in str(result)
        assert isinstance(result, Path)

    def test_get_active_query_workspace_raises_if_no_profiles_file(self, temp_database):
        from data.profile_manager import get_active_query_workspace

        with pytest.raises(ValueError, match="No active_profile_id"):
            get_active_query_workspace()

    def test_get_active_query_workspace_raises_if_invalid_query(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_query_workspace

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
        backend.set_app_state("active_query_id", "nonexistent")

        with pytest.raises(ValueError, match="Query.*not found"):
            get_active_query_workspace()

    def test_get_active_query_workspace_uses_default_profile_after_migration(
        self, temp_database
    ):
        from data.persistence.factory import get_backend
        from data.profile_manager import get_active_query_workspace

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

        result = get_active_query_workspace()

        assert result.name == DEFAULT_QUERY_ID
        assert DEFAULT_PROFILE_ID in str(result)
        assert isinstance(result, Path)


@pytest.mark.unit
@pytest.mark.profile_tests
class TestPathResolutionEdgeCases:
    def test_profile_id_with_special_characters(self, temp_profiles_dir):
        from data.profile_manager import get_profile_file_path

        result = get_profile_file_path("my-project_2025")

        assert result == temp_profiles_dir / "my-project_2025" / "profile.json"

    def test_query_id_with_numbers(self, temp_profiles_dir):
        from data.profile_manager import get_query_file_path

        result = get_query_file_path("kafka", "12w")

        assert result == temp_profiles_dir / "kafka" / "queries" / "12w" / "query.json"

    def test_deeply_nested_structure_integrity(self, temp_profiles_dir):
        from data.profile_manager import get_jira_cache_path

        cache_path = get_jira_cache_path("kafka", "bugs")

        expected_parts = ["profiles", "kafka", "queries", "bugs", "jira_cache.json"]
        assert all(part in str(cache_path) for part in expected_parts)
