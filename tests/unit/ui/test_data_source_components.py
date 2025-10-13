"""
Unit Tests for UI Components Data Source Changes

Tests the UI components for data source radio button order and persistence functionality.
Covers the recently implemented UI changes for JIRA API prioritization.
"""

import pytest
from unittest.mock import patch

from ui.cards import _get_default_data_source, _get_default_jql_profile_id


class TestDataSourceUIComponents:
    """Test UI components related to data source selection"""

    def test_get_default_data_source_returns_jira_when_no_settings(self):
        """Test that JIRA is returned as default when no settings exist"""
        with patch("data.persistence.load_app_settings", return_value={}):
            result = _get_default_data_source()
            assert result == "JIRA"

    def test_get_default_data_source_returns_persisted_value(self):
        """Test that persisted data source value is returned"""
        with patch(
            "data.persistence.load_app_settings",
            return_value={"last_used_data_source": "CSV"},
        ):
            result = _get_default_data_source()
            assert result == "CSV"

    def test_get_default_data_source_handles_import_error(self):
        """Test graceful handling when persistence module import fails"""
        # Mock an exception to trigger the error handling
        with patch(
            "data.persistence.load_app_settings", side_effect=Exception("Mock error")
        ):
            result = _get_default_data_source()
            # Should return "JIRA" as default when error occurs
            assert result == "JIRA"

    def test_get_default_jql_profile_id_returns_empty_when_no_settings(self):
        """Test that empty string is returned when no profile ID is stored"""
        with patch("data.persistence.load_app_settings", return_value={}):
            result = _get_default_jql_profile_id()
            assert result == ""

    def test_get_default_jql_profile_id_returns_persisted_value(self):
        """Test that persisted JQL profile ID is returned"""
        with patch(
            "data.persistence.load_app_settings",
            return_value={"active_jql_profile_id": "profile-123"},
        ):
            result = _get_default_jql_profile_id()
            assert result == "profile-123"

    def test_get_default_jql_profile_id_handles_import_error(self):
        """Test graceful handling when persistence module import fails"""
        # Mock an exception to trigger the error handling
        with patch(
            "data.persistence.load_app_settings", side_effect=Exception("Mock error")
        ):
            result = _get_default_jql_profile_id()
            # Should return "" as default when error occurs
            assert result == ""


class TestDataSourceHelperFunctions:
    """Test the core helper functions used by UI components"""

    def test_data_source_persistence_integration(self):
        """Test integration of data source persistence with UI components"""
        mock_settings = {
            "last_used_data_source": "CSV",
            "active_jql_profile_id": "test-profile-123",
        }

        with patch("data.persistence.load_app_settings", return_value=mock_settings):
            data_source = _get_default_data_source()
            profile_id = _get_default_jql_profile_id()

            assert data_source == "CSV"
            assert profile_id == "test-profile-123"

    def test_backward_compatibility_with_old_settings(self):
        """Test that UI components work with old settings format"""
        old_settings = {
            "jql_query": "project = OLD",
            "jira_api_endpoint": "https://old.jira.com",
            # Missing: last_used_data_source, active_jql_profile_id
        }

        with patch("data.persistence.load_app_settings", return_value=old_settings):
            data_source = _get_default_data_source()
            profile_id = _get_default_jql_profile_id()

            # Should use defaults for missing fields
            assert data_source == "JIRA"
            assert profile_id == ""


@pytest.mark.parametrize(
    "data_source,expected",
    [
        ("JIRA", "JIRA"),
        ("CSV", "CSV"),
        ("", "JIRA"),  # Empty string should default to JIRA
        (None, "JIRA"),  # None should default to JIRA
    ],
)
def test_data_source_default_variations(data_source, expected):
    """Test various data source values and their default behavior"""
    mock_settings = (
        {"last_used_data_source": data_source} if data_source is not None else {}
    )

    with patch("data.persistence.load_app_settings", return_value=mock_settings):
        result = _get_default_data_source()
        assert result == expected


@pytest.mark.parametrize(
    "profile_id,expected",
    [
        ("profile-123", "profile-123"),
        ("default-all-issues", "default-all-issues"),
        ("", ""),
        (None, ""),  # None should default to empty string
    ],
)
def test_jql_profile_id_variations(profile_id, expected):
    """Test various JQL profile ID values and their default behavior"""
    mock_settings = (
        {"active_jql_profile_id": profile_id} if profile_id is not None else {}
    )

    with patch("data.persistence.load_app_settings", return_value=mock_settings):
        result = _get_default_jql_profile_id()
        assert result == expected
