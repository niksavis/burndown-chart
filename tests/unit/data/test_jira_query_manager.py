import json
import os
import tempfile
import uuid
from unittest.mock import mock_open, patch

import pytest

from data.jira.query_profiles import (
    delete_query_profile,
    get_query_profile_by_id,
    load_query_profiles,
    save_query_profile,
    update_profile_last_used,
    validate_profile_name_unique,
)


class TestQueryProfileManager:
    def test_load_query_profiles_returns_empty_when_no_file(self):
        with patch("data.jira.query_profiles.os.path.exists", return_value=False):
            profiles = load_query_profiles()

            assert len(profiles) == 0
            assert profiles == []

    def test_load_query_profiles_returns_user_profiles(self):
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
            patch("data.jira.query_profiles.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(mock_user_profiles))),
        ):
            profiles = load_query_profiles()

            assert len(profiles) == 1

            assert not profiles[0].get("is_default")
            assert profiles[0]["name"] == "Custom Query"

    def test_save_query_profile_creates_new_profile(self):
        with (
            patch("data.jira.query_profiles._load_profiles_from_disk", return_value=[]),
            patch(
                "data.jira.query_profiles._save_profiles_to_disk", return_value=True
            ) as mock_save,
            patch("data.jira.query_profiles.validate_query_profile", return_value=True),
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

            mock_save.assert_called_once()

    def test_save_query_profile_prevents_duplicate_names(self):
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
            "data.jira.query_profiles._load_profiles_from_disk",
            return_value=existing_profiles,
        ):
            profile = save_query_profile(
                name="Existing Query",
                jql="project = NEW",
                description="Should fail",
            )

            assert profile is None

    def test_save_query_profile_validates_inputs(self):
        profile = save_query_profile(name="", jql="project = TEST")
        assert profile is None

        profile = save_query_profile(name="   ", jql="project = TEST")
        assert profile is None

    def test_delete_query_profile_prevents_default_deletion(self):
        result = delete_query_profile("default-all-issues")
        assert result is False

    def test_delete_query_profile_removes_user_profile(self):
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
                "data.jira.query_profiles._load_profiles_from_disk",
                return_value=existing_profiles,
            ),
            patch(
                "data.jira.query_profiles._save_profiles_to_disk", return_value=True
            ) as mock_save,
        ):
            result = delete_query_profile(profile_id)

            assert result is True
            mock_save.assert_called_once_with([])

    def test_get_query_profile_by_id_returns_correct_profile(self):
        with patch("data.jira.query_profiles.load_query_profiles") as mock_load:
            test_profile = {
                "id": "test-id",
                "name": "Test Profile",
                "jql": "project = TEST",
            }
            mock_load.return_value = [test_profile]

            result = get_query_profile_by_id("test-id")

            assert result == test_profile

    def test_get_query_profile_by_id_returns_none_if_not_found(self):
        with patch("data.jira.query_profiles.load_query_profiles", return_value=[]):
            result = get_query_profile_by_id("nonexistent-id")
            assert result is None

    def test_validate_profile_name_unique_with_existing_name(self):
        with patch("data.jira.query_profiles.load_query_profiles") as mock_load:
            mock_load.return_value = [{"id": "existing-id", "name": "Existing Name"}]

            assert not validate_profile_name_unique("Existing Name")

            assert validate_profile_name_unique("New Name")

            assert validate_profile_name_unique(
                "Existing Name", exclude_id="existing-id"
            )

    def test_update_profile_last_used_skips_defaults(self):
        result = update_profile_last_used("default-all-issues")
        assert result is True

    def test_update_profile_last_used_updates_user_profile(self):
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
                "data.jira.query_profiles._load_profiles_from_disk",
                return_value=existing_profiles,
            ),
            patch(
                "data.jira.query_profiles._save_profiles_to_disk", return_value=True
            ) as mock_save,
        ):
            result = update_profile_last_used(profile_id)

            assert result is True
            mock_save.assert_called_once()

            saved_profiles = mock_save.call_args[0][0]
            assert saved_profiles[0]["last_used"] != "2025-01-01T00:00:00"


@pytest.fixture
def temp_query_profiles_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name

    yield temp_file

    if os.path.exists(temp_file):
        os.unlink(temp_file)


class TestQueryProfileFileOperations:
    def test_file_operations_with_real_file(self, temp_query_profiles_file):
        with patch(
            "data.jira.query_profiles.QUERY_PROFILES_FILE", temp_query_profiles_file
        ):
            profile = save_query_profile(
                name="File Test Query",
                jql="project = FILETEST",
                description="Testing file operations",
            )

            assert profile is not None

            assert os.path.exists(temp_query_profiles_file)

            with open(temp_query_profiles_file) as f:
                saved_data = json.load(f)

            assert len(saved_data) == 1
            assert saved_data[0]["name"] == "File Test Query"
