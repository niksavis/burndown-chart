from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
class TestProfileEmptyState:
    def test_refresh_profile_selector_with_no_profiles_shows_empty_state(self):
        from callbacks.profile_management import refresh_profile_selector

        with patch("callbacks.profile_management.list_profiles", return_value=[]):
            with patch(
                "callbacks.profile_management.get_active_profile", return_value=None
            ):
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

                assert options == []
                assert dropdown_value is None

                assert rename_disabled is True
                assert duplicate_disabled is True
                assert delete_disabled is True

                assert new_button_class == "me-1"

    def test_refresh_profile_selector_with_profiles_hides_empty_state(self):
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

                assert len(options) == 1
                assert options[0]["value"] == "test-id"
                assert dropdown_value == "test-id"

                assert rename_disabled is False
                assert duplicate_disabled is False
                assert delete_disabled is False

                assert new_button_class == "me-1"

    def test_load_statistics_returns_empty_when_no_active_profile(self):
        from data.persistence.adapters import load_statistics

        with patch(
            "data.persistence.adapters.statistics.get_backend"
        ) as mock_backend_factory:
            mock_backend = Mock()
            mock_backend.get_app_state.side_effect = lambda key: (
                "" if key == "active_profile_id" else None
            )
            mock_backend_factory.return_value = mock_backend

            data, is_sample = load_statistics()

            assert data == []
            assert is_sample is False

    def test_load_statistics_returns_empty_when_no_active_query(self):
        from data.persistence.adapters import load_statistics

        with patch(
            "data.persistence.adapters.statistics.get_backend"
        ) as mock_backend_factory:
            mock_backend = Mock()

            def get_state(key):
                if key == "active_profile_id":
                    return "test-profile-id"
                elif key == "active_query_id":
                    return ""
                return None

            mock_backend.get_app_state.side_effect = get_state
            mock_backend_factory.return_value = mock_backend

            data, is_sample = load_statistics()

            assert data == []
            assert is_sample is False

    def test_handle_profile_switch_with_empty_profile_id(self):
        from dash import no_update

        from callbacks.profile_management import handle_profile_switch

        result = handle_profile_switch(None)
        assert result == (no_update, no_update)

        result = handle_profile_switch("")
        assert result == (no_update, no_update)
