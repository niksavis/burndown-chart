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
    def test_navigation_state_type_exists(self):
        assert NavigationState is not None

    def test_get_default_navigation_state(self):
        state = get_default_navigation_state()

        assert isinstance(state, dict)
        assert "active_tab" in state
        assert "tab_history" in state
        assert "session_start_tab" in state

    def test_default_navigation_state_values(self):
        state = get_default_navigation_state()

        assert state["active_tab"] == "tab-dashboard"
        assert state["tab_history"] == []
        assert state["session_start_tab"] == "tab-dashboard"

    def test_default_navigation_state_dashboard_first(self):
        state = get_default_navigation_state()
        assert state["active_tab"] == "tab-dashboard"
        assert state["session_start_tab"] == "tab-dashboard"

    def test_navigation_state_with_history(self):
        state: NavigationState = {
            "active_tab": "tab-burndown",
            "tab_history": ["tab-dashboard", "tab-scope-tracking"],
            "previous_tab": "tab-scope-tracking",
            "session_start_tab": "tab-dashboard",
        }

        assert len(state["tab_history"]) == 2
        assert state["previous_tab"] == "tab-scope-tracking"


class TestParameterPanelStateSchema:
    def test_parameter_panel_state_type_exists(self):
        assert ParameterPanelState is not None

    def test_get_default_parameter_panel_state(self):
        state = get_default_parameter_panel_state()

        assert isinstance(state, dict)
        assert "is_open" in state
        assert "last_updated" in state
        assert "user_preference" in state

    def test_default_parameter_panel_state_values(self):
        state = get_default_parameter_panel_state()

        assert state["is_open"] is False
        assert state["user_preference"] is False
        assert isinstance(state["last_updated"], str)

    def test_default_parameter_panel_collapsed(self):
        state = get_default_parameter_panel_state()
        assert state["is_open"] is False

    def test_parameter_panel_state_timestamp(self):
        state = get_default_parameter_panel_state()

        try:
            datetime.fromisoformat(state["last_updated"])
            timestamp_valid = True
        except ValueError:
            timestamp_valid = False

        assert timestamp_valid is True

    def test_parameter_panel_state_expanded(self):
        state: ParameterPanelState = {
            "is_open": True,
            "last_updated": datetime.now().isoformat(),
            "user_preference": True,
        }

        assert state["is_open"] is True
        assert state["user_preference"] is True


class TestMobileNavigationStateSchema:
    def test_mobile_navigation_state_type_exists(self):
        assert MobileNavigationState is not None

    def test_get_default_mobile_navigation_state(self):
        state = get_default_mobile_navigation_state()

        assert isinstance(state, dict)
        assert "drawer_open" in state
        assert "bottom_sheet_visible" in state
        assert "swipe_enabled" in state
        assert "viewport_width" in state
        assert "is_mobile" in state

    def test_default_mobile_navigation_state_values(self):
        state = get_default_mobile_navigation_state()

        assert state["drawer_open"] is False
        assert state["bottom_sheet_visible"] is False
        assert state["swipe_enabled"] is True
        assert state["viewport_width"] == 1024
        assert state["is_mobile"] is False

    def test_default_mobile_state_desktop(self):
        state = get_default_mobile_navigation_state()
        assert state["is_mobile"] is False
        assert state["viewport_width"] >= 768

    def test_mobile_navigation_state_mobile_viewport(self):
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
        state: MobileNavigationState = {
            "drawer_open": True,
            "bottom_sheet_visible": False,
            "swipe_enabled": True,
            "viewport_width": 375,
            "is_mobile": True,
        }

        assert state["drawer_open"] is True


class TestLayoutPreferencesSchema:
    def test_layout_preferences_type_exists(self):
        assert LayoutPreferences is not None

    def test_get_default_layout_preferences(self):
        prefs = get_default_layout_preferences()

        assert isinstance(prefs, dict)
        assert "theme" in prefs
        assert "compact_mode" in prefs
        assert "show_help_icons" in prefs
        assert "animation_enabled" in prefs
        assert "preferred_chart_height" in prefs

    def test_default_layout_preferences_values(self):
        prefs = get_default_layout_preferences()

        assert prefs["theme"] == "light"
        assert prefs["compact_mode"] is False
        assert prefs["show_help_icons"] is True
        assert prefs["animation_enabled"] is True
        assert prefs["preferred_chart_height"] == 600

    def test_default_layout_light_theme(self):
        prefs = get_default_layout_preferences()
        assert prefs["theme"] == "light"

    def test_default_chart_height_in_range(self):
        prefs = get_default_layout_preferences()
        assert 300 <= prefs["preferred_chart_height"] <= 1200

    def test_layout_preferences_custom_values(self):
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
    def test_validate_valid_navigation_state(self):
        state = get_default_navigation_state()
        assert validate_navigation_state(state) is True  # type: ignore[arg-type]

    def test_validate_navigation_state_with_history(self):
        state = {
            "active_tab": "tab-burndown",
            "tab_history": ["tab-dashboard", "tab-scope-tracking"],
            "session_start_tab": "tab-dashboard",
        }
        assert validate_navigation_state(state) is True

    def test_validate_navigation_state_missing_active_tab(self):
        state = {"tab_history": [], "session_start_tab": "tab-dashboard"}
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_invalid_tab_id(self):
        state = {"active_tab": "invalid-id", "tab_history": []}
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_uppercase_tab_id(self):
        state = {"active_tab": "TAB-DASHBOARD"}
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_history_too_long(self):
        state = {
            "active_tab": "tab-dashboard",
            "tab_history": [f"tab-item-{i}" for i in range(11)],
        }
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_invalid_history_item(self):
        state = {
            "active_tab": "tab-dashboard",
            "tab_history": ["tab-burndown", "INVALID-ID"],
        }
        assert validate_navigation_state(state) is False

    def test_validate_navigation_state_empty_history(self):
        state = {"active_tab": "tab-dashboard", "tab_history": []}
        assert validate_navigation_state(state) is True


class TestValidateParameterPanelState:
    def test_validate_valid_parameter_panel_state(self):
        state = get_default_parameter_panel_state()
        assert validate_parameter_panel_state(state) is True  # type: ignore[arg-type]

    def test_validate_parameter_panel_state_expanded(self):
        state = {
            "is_open": True,
            "last_updated": datetime.now().isoformat(),
            "user_preference": True,
        }
        assert validate_parameter_panel_state(state) is True  # type: ignore[arg-type]

    def test_validate_parameter_panel_state_missing_is_open(self):
        state = {"user_preference": False}
        assert validate_parameter_panel_state(state) is False

    def test_validate_parameter_panel_state_invalid_is_open_type(self):
        state = {"is_open": "true"}
        assert validate_parameter_panel_state(state) is False

    def test_validate_parameter_panel_state_invalid_user_preference_type(self):
        state = {"is_open": True, "user_preference": "yes"}
        assert validate_parameter_panel_state(state) is False

    def test_validate_parameter_panel_state_minimal(self):
        state = {"is_open": False}
        assert validate_parameter_panel_state(state) is True


class TestValidateMobileNavigationState:
    def test_validate_valid_mobile_navigation_state(self):
        state = get_default_mobile_navigation_state()
        assert validate_mobile_navigation_state(state) is True  # type: ignore[arg-type]

    def test_validate_mobile_navigation_state_mobile_viewport(self):
        state = {
            "drawer_open": False,
            "bottom_sheet_visible": False,
            "swipe_enabled": True,
            "viewport_width": 375,
            "is_mobile": True,
        }
        assert validate_mobile_navigation_state(state) is True  # type: ignore[arg-type]

    def test_validate_mobile_navigation_state_invalid_bool_field(self):
        state = {"drawer_open": "false"}
        assert validate_mobile_navigation_state(state) is False

    def test_validate_mobile_navigation_state_invalid_viewport_width(self):
        state = {"viewport_width": -100}
        assert validate_mobile_navigation_state(state) is False

    def test_validate_mobile_navigation_state_zero_viewport_width(self):
        state = {"viewport_width": 0}
        assert validate_mobile_navigation_state(state) is False

    def test_validate_mobile_navigation_state_non_integer_viewport(self):
        state = {"viewport_width": 375.5}
        assert validate_mobile_navigation_state(state) is False

    def test_validate_mobile_navigation_state_empty(self):
        state = {}
        assert validate_mobile_navigation_state(state) is True


class TestValidateLayoutPreferences:
    def test_validate_valid_layout_preferences(self):
        prefs = get_default_layout_preferences()
        assert validate_layout_preferences(prefs) is True  # type: ignore[arg-type]

    def test_validate_layout_preferences_dark_theme(self):
        prefs = {
            "theme": "dark",
            "compact_mode": False,
            "show_help_icons": True,
            "animation_enabled": True,
            "preferred_chart_height": 600,
        }
        assert validate_layout_preferences(prefs) is True  # type: ignore[arg-type]

    def test_validate_layout_preferences_invalid_theme(self):
        prefs = {"theme": "blue"}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_invalid_bool_field(self):
        prefs = {"compact_mode": "yes"}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_chart_height_too_small(self):
        prefs = {"preferred_chart_height": 200}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_chart_height_too_large(self):
        prefs = {"preferred_chart_height": 1500}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_chart_height_boundary_min(self):
        prefs = {"preferred_chart_height": 300}
        assert validate_layout_preferences(prefs) is True

    def test_validate_layout_preferences_chart_height_boundary_max(self):
        prefs = {"preferred_chart_height": 1200}
        assert validate_layout_preferences(prefs) is True

    def test_validate_layout_preferences_non_integer_chart_height(self):
        prefs = {"preferred_chart_height": 600.5}
        assert validate_layout_preferences(prefs) is False

    def test_validate_layout_preferences_empty(self):
        prefs = {}
        assert validate_layout_preferences(prefs) is True


class TestNavigationStateIntegration:
    def test_all_defaults_are_valid(self):
        nav_state = get_default_navigation_state()
        panel_state = get_default_parameter_panel_state()
        mobile_state = get_default_mobile_navigation_state()
        layout_prefs = get_default_layout_preferences()

        assert validate_navigation_state(nav_state) is True  # type: ignore[arg-type]
        assert validate_parameter_panel_state(panel_state) is True  # type: ignore[arg-type]
        assert validate_mobile_navigation_state(mobile_state) is True  # type: ignore[arg-type]
        assert validate_layout_preferences(layout_prefs) is True  # type: ignore[arg-type]

    def test_navigation_flow_scenario(self):
        state = get_default_navigation_state()
        assert state["active_tab"] == "tab-dashboard"

        state["previous_tab"] = state["active_tab"]
        state["active_tab"] = "tab-burndown"
        state["tab_history"] = [state["previous_tab"]]

        assert validate_navigation_state(state) is True  # type: ignore[arg-type]
        assert state["active_tab"] == "tab-burndown"
        assert len(state["tab_history"]) == 1

    def test_parameter_panel_toggle_scenario(self):
        state = get_default_parameter_panel_state()
        assert state["is_open"] is False

        state["is_open"] = True
        state["user_preference"] = True
        state["last_updated"] = datetime.now().isoformat()

        assert validate_parameter_panel_state(state) is True  # type: ignore[arg-type]
        assert state["is_open"] is True

    def test_mobile_to_desktop_transition(self):
        state: MobileNavigationState = {
            "drawer_open": False,
            "bottom_sheet_visible": False,
            "swipe_enabled": True,
            "viewport_width": 375,
            "is_mobile": True,
        }
        assert validate_mobile_navigation_state(state) is True  # type: ignore[arg-type]

        state["viewport_width"] = 1024
        state["is_mobile"] = False
        state["drawer_open"] = False

        assert validate_mobile_navigation_state(state) is True  # type: ignore[arg-type]
        assert state["is_mobile"] is False
