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
        """Verify empty state alert is shown when no profiles exist."""
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
                    empty_state_class,
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

                # Verify empty state alert is visible (no d-none class)
                assert "d-none" not in empty_state_class
                assert "mb-0 mt-2" in empty_state_class

    def test_refresh_profile_selector_with_profiles_hides_empty_state(self):
        """Verify empty state alert is hidden when profiles exist."""
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
                    empty_state_class,
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

                # Verify empty state alert is hidden (has d-none class)
                assert "d-none" in empty_state_class

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

    def test_empty_state_link_opens_create_profile_modal(self):
        """Verify clicking empty state link opens create profile modal."""
        from callbacks.profile_management import open_profile_form_modal

        # Mock ctx.triggered to simulate empty state link click
        with patch("callbacks.profile_management.ctx") as mock_ctx:
            mock_ctx.triggered = [
                {"prop_id": "empty-state-create-profile-link.n_clicks"}
            ]

            with patch("callbacks.profile_management.list_profiles", return_value=[]):
                # Call the callback
                (
                    is_open,
                    mode,
                    source_id,
                    modal_title,
                    name_label,
                    name_value,
                    description_value,
                    description_style,
                    context_info,
                    confirm_btn,
                ) = open_profile_form_modal(
                    create_clicks=None,
                    rename_clicks=None,
                    duplicate_clicks=None,
                    empty_state_clicks=1,
                    selected_profile_id=None,
                )

                # Verify modal opens in create mode
                assert is_open is True
                assert mode == "create"
                assert source_id is None
                assert modal_title == "Create New Profile"
                assert name_value == ""
                assert description_value == ""
