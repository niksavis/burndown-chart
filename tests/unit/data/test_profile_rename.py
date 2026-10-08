from datetime import UTC, datetime

import pytest


def create_test_profile_data(profile_id: str, name: str) -> dict:
    fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()
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
    def test_rename_profile_success(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Original Name")
        backend.save_profile(profile)

        rename_profile("p_test123", "New Name")

        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None
        assert updated_profile["name"] == "New Name"

    def test_rename_profile_empty_name(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Test Profile")
        backend.save_profile(profile)

        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            rename_profile("p_test123", "")

        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            rename_profile("p_test123", "   ")

    def test_rename_profile_name_too_long(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Test Profile")
        backend.save_profile(profile)

        long_name = "A" * 101
        with pytest.raises(
            ValueError, match="Profile name cannot exceed 100 characters"
        ):
            rename_profile("p_test123", long_name)

    def test_rename_profile_duplicate_name(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile1 = create_test_profile_data("p_test1", "Profile One")
        profile2 = create_test_profile_data("p_test2", "Profile Two")
        backend.save_profile(profile1)
        backend.save_profile(profile2)

        with pytest.raises(
            ValueError, match="Profile name 'Profile Two' already exists"
        ):
            rename_profile("p_test1", "Profile Two")

    def test_rename_profile_duplicate_name_case_insensitive(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile1 = create_test_profile_data("p_test1", "Profile One")
        profile2 = create_test_profile_data("p_test2", "Profile Two")
        backend.save_profile(profile1)
        backend.save_profile(profile2)

        with pytest.raises(ValueError, match="Profile name"):
            rename_profile("p_test1", "profile two")

        with pytest.raises(ValueError, match="Profile name"):
            rename_profile("p_test1", "PROFILE TWO")

        with pytest.raises(ValueError, match="Profile name"):
            rename_profile("p_test1", "Profile TWO")

    def test_rename_profile_same_name(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Test Profile")
        backend.save_profile(profile)

        rename_profile("p_test123", "Test Profile")
        rename_profile("p_test123", "test profile")
        rename_profile("p_test123", "TEST PROFILE")

        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None

    def test_rename_nonexistent_profile(self, temp_database):
        from data.profile_manager import rename_profile

        with pytest.raises(ValueError, match="Profile 'nonexistent_id' does not exist"):
            rename_profile("nonexistent_id", "New Name")

    def test_rename_preserves_other_metadata(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Original Name")
        profile["description"] = "Important description"
        profile["forecast_settings"]["pert_factor"] = 1.5
        profile["forecast_settings"]["deadline"] = "2025-12-31"
        profile["forecast_settings"]["data_points_count"] = 30
        profile["jira_config"] = {"base_url": "https://jira.example.com"}
        profile["field_mappings"] = {"points_field": "customfield_10001"}
        backend.save_profile(profile)

        rename_profile("p_test123", "New Name")

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
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Original Name")
        backend.save_profile(profile)

        rename_profile("p_test123", "New Name")

        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None
        assert updated_profile["id"] == "p_test123"
        assert updated_profile["name"] == "New Name"

    def test_rename_whitespace_stripped(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import rename_profile

        backend = get_backend()
        profile = create_test_profile_data("p_test123", "Test Profile")
        backend.save_profile(profile)

        rename_profile("p_test123", "  New Name  ")

        updated_profile = backend.get_profile("p_test123")
        assert updated_profile is not None
        assert updated_profile["name"] == "New Name"
