"""
Unit tests for profile management empty state handling.

Tests verify that:
1. UI properly handles empty profile state after deletion
2. Empty state alert is shown when no profiles exist
3. Data loading returns empty gracefully when no active profile
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestProfileEmptyState:
    """Test UI and data handling when no profiles exist."""

    def test_refresh_profile_selector_with_no_profiles_shows_empty_state(self):
        """Verify New button gets highlight class when no profiles exist."""
        from callbacks.profile_management import refresh_profile_selector

        with patch("callbacks.profile_management.list_profiles", return_value=[]):
            with patch(
                "callbacks.profile_management.get_active_profile", return_value=None
            ):
                # Call the callback
                (
                    options,
                    dropdown_value,
                    rename_disabled,
                    duplicate_disabled,
                    delete_disabled,
                    new_button_class,
                ) = refresh_profile_selector(
                    form_modal_open=False,
                    delete_modal_open=False,
                    switch_trigger=0,
                    metrics_refresh=None,
                )

                # Verify dropdown is empty
                assert options == []
                assert dropdown_value is None

                # Verify all buttons are disabled
                assert rename_disabled is True
                assert duplicate_disabled is True
                assert delete_disabled is True

                # Verify New button has highlight class
                assert "highlight-first-action" in new_button_class

    def test_refresh_profile_selector_with_profiles_hides_empty_state(self):
        """Verify New button does NOT get highlight class when profiles exist."""
        from callbacks.profile_management import refresh_profile_selector

        mock_profiles = [
            {
                "id": "test-id",
                "name": "Test Profile",
                "jira_url": "https://test.atlassian.net",
            }
        ]

        mock_active_profile = Mock()
        mock_active_profile.id = "test-id"

        with patch(
            "callbacks.profile_management.list_profiles", return_value=mock_profiles
        ):
            with patch(
                "callbacks.profile_management.get_active_profile",
                return_value=mock_active_profile,
            ):
                # Call the callback
                (
                    options,
                    dropdown_value,
                    rename_disabled,
                    duplicate_disabled,
                    delete_disabled,
                    new_button_class,
                ) = refresh_profile_selector(
                    form_modal_open=False,
                    delete_modal_open=False,
                    switch_trigger=0,
                    metrics_refresh=None,
                )

                # Verify dropdown has options
                assert len(options) == 1
                assert options[0]["value"] == "test-id"
                assert dropdown_value == "test-id"

                # Verify buttons are enabled
                assert rename_disabled is False
                assert duplicate_disabled is False
                assert delete_disabled is False

                # Verify New button does NOT have highlight class
                assert "highlight-first-action" not in new_button_class

    def test_load_statistics_returns_empty_when_no_active_profile(self):
        """Verify load_statistics gracefully returns empty list when no active profile."""
        from data.persistence.adapters import load_statistics

        with patch("data.persistence.factory.get_backend") as mock_backend_factory:
            mock_backend = Mock()
            mock_backend.get_app_state.side_effect = lambda key: (
                "" if key == "active_profile_id" else None
            )
            mock_backend_factory.return_value = mock_backend

            # Call load_statistics
            data, is_sample = load_statistics()

            # Verify returns empty
            assert data == []
            assert is_sample is False

    def test_load_statistics_returns_empty_when_no_active_query(self):
        """Verify load_statistics gracefully returns empty list when no active query."""
        from data.persistence.adapters import load_statistics

        with patch("data.persistence.factory.get_backend") as mock_backend_factory:
            mock_backend = Mock()

            def get_state(key):
                if key == "active_profile_id":
                    return "test-profile-id"
                elif key == "active_query_id":
                    return ""  # No active query
                return None

            mock_backend.get_app_state.side_effect = get_state
            mock_backend_factory.return_value = mock_backend

            # Call load_statistics
            data, is_sample = load_statistics()

            # Verify returns empty
            assert data == []
            assert is_sample is False

    def test_handle_profile_switch_with_empty_profile_id(self):
        """Verify handle_profile_switch handles None/empty profile ID gracefully."""
        from callbacks.profile_management import handle_profile_switch
        from dash import no_update

        # Test with None
        result = handle_profile_switch(None)
        assert result == (no_update, no_update)

        # Test with empty string
        result = handle_profile_switch("")
        assert result == (no_update, no_update)
