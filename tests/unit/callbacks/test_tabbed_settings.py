"""Unit tests for tabbed settings profile-first gating callbacks."""

from dash import no_update


class TestTabbedSettingsProfileGating:
    """Validate tab gating behavior when profiles are missing/present."""

    def test_tabs_disabled_without_profiles(self):
        """Connect/Queries should be disabled with guidance when no profiles exist."""
        from callbacks.tabbed_settings import enforce_profile_first_tab_access

        result = enforce_profile_first_tab_access([], "connect-tab")

        assert result[0] is True
        assert result[1] is True
        assert result[2] == "profile-tab"
        assert result[3] == {}
        assert result[4] == {}

    def test_tabs_enabled_with_profiles(self):
        """Connect/Queries should be enabled when at least one profile exists."""
        from callbacks.tabbed_settings import enforce_profile_first_tab_access

        profile_options = [{"label": "Demo", "value": "demo"}]
        result = enforce_profile_first_tab_access(profile_options, "profile-tab")

        assert result[0] is False
        assert result[1] is False
        assert result[2] is no_update
        assert result[3] == {"display": "none"}
        assert result[4] == {"display": "none"}
