"""
Unit tests for navigation state schemas.

Tests the UI state TypedDict classes and validation functions.
"""

from datetime import datetime

from data.schema import (
    LayoutPreferences,
    MobileNavigationState,
    NavigationState,
    ParameterPanelState,
    get_default_layout_preferences,
    get_default_mobile_navigation_state,
    get_default_navigation_state,
    get_default_parameter_panel_state,
    validate_layout_preferences,
    validate_mobile_navigation_state,
    validate_navigation_state,
    validate_parameter_panel_state,
)


class TestNavigationStateSchema:
    """Test NavigationState TypedDict and defaults."""

    def test_navigation_state_type_exists(self):
        """Test that NavigationState type is defined."""
        # This will fail at import time if type doesn't exist
        assert NavigationState is not None

    def test_get_default_navigation_state(self):
        """Test default navigation state structure."""
        state = get_default_navigation_state()

        assert isinstance(state, dict)
        assert "active_tab" in state
        assert "tab_history" in state
        assert "session_start_tab" in state

    def test_default_navigation_state_values(self):
        """Test default navigation state has correct values."""
        state = get_default_navigation_state()

        assert state["active_tab"] == "tab-dashboard"
        assert state["tab_history"] == []
        assert state["session_start_tab"] == "tab-dashboard"

    def test_default_navigation_state_dashboard_first(self):
        """Test that default state loads Dashboard tab first."""
        state = get_default_navigation_state()
        assert state["active_tab"] == "tab-dashboard"
        assert state["session_start_tab"] == "tab-dashboard"

    def test_navigation_state_with_history(self):
        """Test navigation state with tab history."""
        state: NavigationState = {
            "active_tab": "tab-burndown",
            "tab_history": ["tab-dashboard", "tab-scope-tracking"],
            "previous_tab": "tab-scope-tracking",
            "session_start_tab": "tab-dashboard",
        }

        assert len(state["tab_history"]) == 2
        assert state["previous_tab"] == "tab-scope-tracking"


class TestParameterPanelStateSchema:
    """Test ParameterPanelState TypedDict and defaults."""

    def test_parameter_panel_state_type_exists(self):
        """Test that ParameterPanelState type is defined."""
        assert ParameterPanelState is not None

    def test_get_default_parameter_panel_state(self):
        """Test default parameter panel state structure."""
        state = get_default_parameter_panel_state()

        assert isinstance(state, dict)
        assert "is_open" in state
        assert "last_updated" in state
        assert "user_preference" in state

    def test_default_parameter_panel_state_values(self):
        """Test default parameter panel state has correct values."""
        state = get_default_parameter_panel_state()

        assert state["is_open"] is False
        assert state["user_preference"] is False
        assert isinstance(state["last_updated"], str)

    def test_default_parameter_panel_collapsed(self):
        """Test that default state has panel collapsed."""
        state = get_default_parameter_panel_state()
        assert state["is_open"] is False

    def test_parameter_panel_state_timestamp(self):
        """Test that default state includes valid timestamp."""
        state = get_default_parameter_panel_state()

        # Should be valid ISO format timestamp
        try:
            datetime.fromisoformat(state["last_updated"])
            timestamp_valid = True
        except ValueError:
            timestamp_valid = False

        assert timestamp_valid is True

    def test_parameter_panel_state_expanded(self):
        """Test parameter panel state when expanded."""
        state: ParameterPanelState = {
            "is_open": True,
            "last_updated": datetime.now().isoformat(),
            "user_preference": True,
        }

        assert state["is_open"] is True
        assert state["user_preference"] is True


class TestMobileNavigationStateSchema:
    """Test MobileNavigationState TypedDict and defaults."""

    def test_mobile_navigation_state_type_exists(self):
        """Test that MobileNavigationState type is defined."""
        assert MobileNavigationState is not None

    def test_get_default_mobile_navigation_state(self):
        """Test default mobile navigation state structure."""
        state = get_default_mobile_navigation_state()

        assert isinstance(state, dict)
        assert "drawer_open" in state
        assert "bottom_sheet_visible" in state
        assert "swipe_enabled" in state
        assert "viewport_width" in state
        assert "is_mobile" in state

    def test_default_mobile_navigation_state_values(self):
        """Test default mobile navigation state has correct values."""
        state = get_default_mobile_navigation_state()

        assert state["drawer_open"] is False
        assert state["bottom_sheet_visible"] is False
        assert state["swipe_enabled"] is True
        assert state["viewport_width"] == 1024
        assert state["is_mobile"] is False

    def test_default_mobile_state_desktop(self):
        """Test that default state is for desktop viewport."""
        state = get_default_mobile_navigation_state()
        assert state["is_mobile"] is False
        assert state["viewport_width"] >= 768

    def test_mobile_navigation_state_mobile_viewport(self):
        """Test mobile navigation state for mobile viewport."""
        state: MobileNavigationState = {
            "drawer_open": False,
            "bottom_sheet_visible": False,
            "swipe_enabled": True,
            "viewport_width": 375,
            "is_mobile": True,
        }

        assert state["viewport_width"] < 768
        assert state["is_mobile"] is True

    def test_mobile_navigation_state_drawer_open(self):
        """Test mobile navigation state with drawer open."""
        state: MobileNavigationState = {
            "drawer_open": True,
            "bottom_sheet_visible": False,
            "swipe_enabled": True,
            "viewport_width": 375,
            "is_mobile": True,
        }

        assert state["drawer_open"] is True


class TestLayoutPreferencesSchema:
    """Test LayoutPreferences TypedDict and defaults."""

    def test_layout_preferences_type_exists(self):
        """Test that LayoutPreferences type is defined."""
        assert LayoutPreferences is not None

    def test_get_default_layout_preferences(self):
        """Test default layout preferences structure."""
        prefs = get_default_layout_preferences()

        assert isinstance(prefs, dict)
        assert "theme" in prefs
        assert "compact_mode" in prefs
        assert "show_help_icons" in prefs
        assert "animation_enabled" in prefs
        assert "preferred_chart_height" in prefs

    def test_default_layout_preferences_values(self):
        """Test default layout preferences has correct values."""
        prefs = get_default_layout_preferences()

        assert prefs["theme"] == "light"
        assert prefs["compact_mode"] is False
        assert prefs["show_help_icons"] is True
        assert prefs["animation_enabled"] is True
        assert prefs["preferred_chart_height"] == 600

    def test_default_layout_light_theme(self):
        """Test that default theme is light."""
        prefs = get_default_layout_preferences()
        assert prefs["theme"] == "light"

    def test_default_chart_height_in_range(self):
        """Test that default chart height is in valid range."""
        prefs = get_default_layout_preferences()
        assert 300 <= prefs["preferred_chart_height"] <= 1200

    def test_layout_preferences_custom_values(self):
        """Test layout preferences with custom values."""
        prefs: LayoutPreferences = {
            "theme": "dark",
            "compact_mode": True,
            "show_help_icons": False,
            "animation_enabled": False,
            "preferred_chart_height": 800,
        }

        assert prefs["theme"] == "dark"
        assert prefs["compact_mode"] is True
        assert prefs["preferred_chart_height"] == 800


class TestValidateNavigationState:
    """Test validate_navigation_state function."""

    def test_validate_valid_navigation_state(self):
        """Test validation of valid navigation state."""
        state = get_default_navigation_state()
        assert validate_navigation_state(state) is True  # type: ignore[arg-type]

    def test_validate_navigation_state_with_history(self):
        """Test validation with tab history."""
        state = {
            "active_tab": "tab-burndown",
            "tab_history": ["tab-dashboard", "tab-scope-tracking"],
            "session_start_tab": "tab-dashboard",
        }
        assert validate_navigation_state(state) is True

    def test_validate_navigation_state_missing_active_tab(self):
        """Test validation fails without active_tab."""
        state = {"tab_history": [], "session_start_tab": "tab-dashboard"}
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_invalid_tab_id(self):
        """Test validation fails with invalid tab ID pattern."""
        state = {"active_tab": "invalid-id", "tab_history": []}
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_uppercase_tab_id(self):
        """Test validation fails with uppercase tab ID."""
        state = {"active_tab": "TAB-DASHBOARD"}
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_history_too_long(self):
        """Test validation fails with history > 10 items."""
        state = {
            "active_tab": "tab-dashboard",
            "tab_history": [f"tab-item-{i}" for i in range(11)],
        }
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_invalid_history_item(self):
        """Test validation fails with invalid tab ID in history."""
        state = {
            "active_tab": "tab-dashboard",
            "tab_history": ["tab-burndown", "INVALID-ID"],
        }
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_empty_history(self):
        """Test validation passes with empty history."""
        state = {"active_tab": "tab-dashboard", "tab_history": []}
        assert validate_navigation_state(state) is True


class TestValidateParameterPanelState:
    """Test validate_parameter_panel_state function."""

    def test_validate_valid_parameter_panel_state(self):
        """Test validation of valid parameter panel state."""
        state = get_default_parameter_panel_state()
        assert validate_parameter_panel_state(state) is True  # type: ignore[arg-type]

    def test_validate_parameter_panel_state_expanded(self):
        """Test validation of expanded panel state."""
        state = {
            "is_open": True,
            "last_updated": datetime.now().isoformat(),
            "user_preference": True,
        }
        assert validate_parameter_panel_state(state) is True  # type: ignore[arg-type]

    def test_validate_parameter_panel_state_missing_is_open(self):
        """Test validation fails without is_open field."""
        state = {"user_preference": False}
        assert validate_parameter_panel_state(state) is False

    def test_validate_parameter_panel_state_invalid_is_open_type(self):
        """Test validation fails with non-boolean is_open."""
        state = {"is_open": "true"}
        assert validate_parameter_panel_state(state) is False

    def test_validate_parameter_panel_state_invalid_user_preference_type(self):
        """Test validation fails with non-boolean user_preference."""
        state = {"is_open": True, "user_preference": "yes"}
        assert validate_parameter_panel_state(state) is False

    def test_validate_parameter_panel_state_minimal(self):
        """Test validation passes with minimal required fields."""
        state = {"is_open": False}
        assert validate_parameter_panel_state(state) is True


class TestValidateMobileNavigationState:
    """Test validate_mobile_navigation_state function."""

    def test_validate_valid_mobile_navigation_state(self):
        """Test validation of valid mobile navigation state."""
        state = get_default_mobile_navigation_state()
        assert validate_mobile_navigation_state(state) is True  # type: ignore[arg-type]

    def test_validate_mobile_navigation_state_mobile_viewport(self):
        """Test validation of mobile viewport state."""
        state = {
            "drawer_open": False,
            "bottom_sheet_visible": False,
            "swipe_enabled": True,
            "viewport_width": 375,
            "is_mobile": True,
        }
        assert validate_mobile_navigation_state(state) is True  # type: ignore[arg-type]

    def test_validate_mobile_navigation_state_invalid_bool_field(self):
        """Test validation fails with non-boolean field."""
        state = {"drawer_open": "false"}
        assert validate_mobile_navigation_state(state) is False

    def test_validate_mobile_navigation_state_invalid_viewport_width(self):
        """Test validation fails with negative viewport width."""
        state = {"viewport_width": -100}
        assert validate_mobile_navigation_state(state) is False

    def test_validate_mobile_navigation_state_zero_viewport_width(self):
        """Test validation fails with zero viewport width."""
        state = {"viewport_width": 0}
        assert validate_mobile_navigation_state(state) is False

    def test_validate_mobile_navigation_state_non_integer_viewport(self):
        """Test validation fails with non-integer viewport width."""
        state = {"viewport_width": 375.5}
        assert validate_mobile_navigation_state(state) is False

    def test_validate_mobile_navigation_state_empty(self):
        """Test validation passes with empty state."""
        state = {}
        assert validate_mobile_navigation_state(state) is True


class TestValidateLayoutPreferences:
    """Test validate_layout_preferences function."""

    def test_validate_valid_layout_preferences(self):
        """Test validation of valid layout preferences."""
        prefs = get_default_layout_preferences()
        assert validate_layout_preferences(prefs) is True  # type: ignore[arg-type]

    def test_validate_layout_preferences_dark_theme(self):
        """Test validation with dark theme."""
        prefs = {
            "theme": "dark",
            "compact_mode": False,
            "show_help_icons": True,
            "animation_enabled": True,
            "preferred_chart_height": 600,
        }
        assert validate_layout_preferences(prefs) is True  # type: ignore[arg-type]

    def test_validate_layout_preferences_invalid_theme(self):
        """Test validation fails with invalid theme."""
        prefs = {"theme": "blue"}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_invalid_bool_field(self):
        """Test validation fails with non-boolean field."""
        prefs = {"compact_mode": "yes"}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_chart_height_too_small(self):
        """Test validation fails with chart height < 300."""
        prefs = {"preferred_chart_height": 200}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_chart_height_too_large(self):
        """Test validation fails with chart height > 1200."""
        prefs = {"preferred_chart_height": 1500}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_chart_height_boundary_min(self):
        """Test validation passes with chart height = 300 (minimum)."""
        prefs = {"preferred_chart_height": 300}
        assert validate_layout_preferences(prefs) is True

    def test_validate_layout_preferences_chart_height_boundary_max(self):
        """Test validation passes with chart height = 1200 (maximum)."""
        prefs = {"preferred_chart_height": 1200}
        assert validate_layout_preferences(prefs) is True

    def test_validate_layout_preferences_non_integer_chart_height(self):
        """Test validation fails with non-integer chart height."""
        prefs = {"preferred_chart_height": 600.5}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_empty(self):
        """Test validation passes with empty preferences."""
        prefs = {}
        assert validate_layout_preferences(prefs) is True


class TestNavigationStateIntegration:
    """Integration tests for navigation state schemas."""

    def test_all_defaults_are_valid(self):
        """Test that all default states pass validation."""
        nav_state = get_default_navigation_state()
        panel_state = get_default_parameter_panel_state()
        mobile_state = get_default_mobile_navigation_state()
        layout_prefs = get_default_layout_preferences()

        assert validate_navigation_state(nav_state) is True  # type: ignore[arg-type]
        assert validate_parameter_panel_state(panel_state) is True  # type: ignore[arg-type]
        assert validate_mobile_navigation_state(mobile_state) is True  # type: ignore[arg-type]
        assert validate_layout_preferences(layout_prefs) is True  # type: ignore[arg-type]

    def test_navigation_flow_scenario(self):
        """Test realistic navigation flow scenario."""
        # Start with default
        state = get_default_navigation_state()
        assert state["active_tab"] == "tab-dashboard"

        # Navigate to burndown
        state["previous_tab"] = state["active_tab"]
        state["active_tab"] = "tab-burndown"
        state["tab_history"] = [state["previous_tab"]]

        assert validate_navigation_state(state) is True  # type: ignore[arg-type]
        assert state["active_tab"] == "tab-burndown"
        assert len(state["tab_history"]) == 1

    def test_parameter_panel_toggle_scenario(self):
        """Test realistic parameter panel toggle scenario."""
        # Start collapsed
        state = get_default_parameter_panel_state()
        assert state["is_open"] is False

        # User expands panel
        state["is_open"] = True
        state["user_preference"] = True
        state["last_updated"] = datetime.now().isoformat()

        assert validate_parameter_panel_state(state) is True  # type: ignore[arg-type]
        assert state["is_open"] is True

    def test_mobile_to_desktop_transition(self):
        """Test viewport transition from mobile to desktop."""
        # Start mobile
        state: MobileNavigationState = {
            "drawer_open": False,
            "bottom_sheet_visible": False,
            "swipe_enabled": True,
            "viewport_width": 375,
            "is_mobile": True,
        }
        assert validate_mobile_navigation_state(state) is True  # type: ignore[arg-type]

        # Transition to desktop
        state["viewport_width"] = 1024
        state["is_mobile"] = False
        state["drawer_open"] = False

        assert validate_mobile_navigation_state(state) is True  # type: ignore[arg-type]
        assert state["is_mobile"] is False
