from unittest.mock import patch

import pytest

from ui.cards.settings_helpers import (
    _get_default_data_source,
    _get_default_jql_profile_id,
)


class TestDataSourceUIComponents:
    def test_get_default_data_source_returns_jira_when_no_settings(self):
        with patch("data.persistence.load_app_settings", return_value={}):
            result = _get_default_data_source()
            assert result == "JIRA"

    def test_get_default_data_source_returns_persisted_value(self):
        with patch(
            "ui.cards.settings_helpers.load_app_settings",
            return_value={"last_used_data_source": "CSV"},
        ):
            result = _get_default_data_source()
            assert result == "CSV"

    def test_get_default_data_source_handles_import_error(self):
        with patch(
            "ui.cards.settings_helpers.load_app_settings",
            side_effect=Exception("Mock error"),
        ):
            result = _get_default_data_source()
            assert result == "JIRA"

    def test_get_default_jql_profile_id_returns_empty_when_no_settings(self):
        with patch("ui.cards.settings_helpers.load_app_settings", return_value={}):
            result = _get_default_jql_profile_id()
            assert result == ""

    def test_get_default_jql_profile_id_returns_persisted_value(self):
        with patch(
            "ui.cards.settings_helpers.load_app_settings",
            return_value={"active_jql_profile_id": "profile-123"},
        ):
            result = _get_default_jql_profile_id()
            assert result == "profile-123"

    def test_get_default_jql_profile_id_handles_import_error(self):
        with patch(
            "ui.cards.settings_helpers.load_app_settings",
            side_effect=Exception("Mock error"),
        ):
            result = _get_default_jql_profile_id()
            assert result == ""


class TestDataSourceHelperFunctions:
    def test_data_source_persistence_integration(self):
        mock_settings = {
            "last_used_data_source": "CSV",
            "active_jql_profile_id": "test-profile-123",
        }

        with patch(
            "ui.cards.settings_helpers.load_app_settings", return_value=mock_settings
        ):
            data_source = _get_default_data_source()
            profile_id = _get_default_jql_profile_id()

            assert data_source == "CSV"
            assert profile_id == "test-profile-123"

    def test_backward_compatibility_with_old_settings(self):
        old_settings = {
            "jql_query": "project = OLD",
            "jira_api_endpoint": "https://old.jira.com",
        }

        with patch(
            "ui.cards.settings_helpers.load_app_settings", return_value=old_settings
        ):
            data_source = _get_default_data_source()
            profile_id = _get_default_jql_profile_id()

            assert data_source == "JIRA"
            assert profile_id == ""


@pytest.mark.parametrize(
    "data_source,expected",
    [
        ("JIRA", "JIRA"),
        ("CSV", "CSV"),
        ("", "JIRA"),
        (None, "JIRA"),
    ],
)
def test_data_source_default_variations(data_source, expected):
    mock_settings = (
        {"last_used_data_source": data_source} if data_source is not None else {}
    )

    with patch(
        "ui.cards.settings_helpers.load_app_settings", return_value=mock_settings
    ):
        result = _get_default_data_source()
        assert result == expected


@pytest.mark.parametrize(
    "profile_id,expected",
    [
        ("profile-123", "profile-123"),
        ("default-all-issues", "default-all-issues"),
        ("", ""),
        (None, ""),
    ],
)
def test_jql_profile_id_variations(profile_id, expected):
    mock_settings = (
        {"active_jql_profile_id": profile_id} if profile_id is not None else {}
    )

    with patch(
        "ui.cards.settings_helpers.load_app_settings", return_value=mock_settings
    ):
        result = _get_default_jql_profile_id()
        assert result == expected
