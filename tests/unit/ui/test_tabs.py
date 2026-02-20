"""
Unit tests for tab navigation module.

Tests the TAB_CONFIG registry and helper functions.
"""

from ui.style_constants import get_color
from ui.tabs import (
    TAB_CONFIG,
    get_tab_by_id,
    get_tabs_sorted,
    validate_tab_id,
)


class TestTabConfigRegistry:
    """Test the TAB_CONFIG registry structure and contents."""

    def test_tab_config_exists(self):
        """Test that TAB_CONFIG registry exists and is not empty."""
        assert TAB_CONFIG is not None
        assert len(TAB_CONFIG) > 0

    def test_tab_config_has_seven_tabs(self):
        """Test that TAB_CONFIG contains exactly 9 tabs."""
        assert len(TAB_CONFIG) == 9

    def test_tab_config_structure(self):
        """Test that each tab has required fields."""
        required_fields = [
            "id",
            "label",
            "icon",
            "color",
            "order",
            "requires_data",
            "help_content_id",
        ]

        for tab in TAB_CONFIG:
            for field in required_fields:
                assert field in tab, f"Tab missing required field: {field}"

    def test_tab_ids_are_unique(self):
        """Test that all tab IDs are unique."""
        tab_ids = [tab["id"] for tab in TAB_CONFIG]
        assert len(tab_ids) == len(set(tab_ids)), "Tab IDs must be unique"

    def test_tab_orders_are_unique(self):
        """Test that all tab orders are unique."""
        orders = [tab["order"] for tab in TAB_CONFIG]
        assert len(orders) == len(set(orders)), "Tab orders must be unique"

    def test_tab_orders_are_sequential(self):
        """Test that tab orders start at 0 and are sequential."""
        orders = sorted([tab["order"] for tab in TAB_CONFIG])
        expected_orders = list(range(len(TAB_CONFIG)))
        assert orders == expected_orders, (
            f"Orders should be {expected_orders}, got {orders}"
        )

    def test_dashboard_is_first_tab(self):
        """Test that Dashboard tab has order 0 (first position)."""
        dashboard_tab = next(
            (t for t in TAB_CONFIG if t["id"] == "tab-dashboard"), None
        )
        assert dashboard_tab is not None, "Dashboard tab must exist"
        assert dashboard_tab["order"] == 0, "Dashboard must be first tab (order 0)"

    def test_tab_id_pattern(self):
        """Test that all tab IDs follow the pattern 'tab-{name}'."""
        import re

        pattern = re.compile(r"^tab-[a-z-]+$")

        for tab in TAB_CONFIG:
            assert pattern.match(tab["id"]), (
                f"Tab ID '{tab['id']}' doesn't match pattern 'tab-{{name}}'"
            )

    def test_tab_labels_not_empty(self):
        """Test that all tab labels are non-empty strings."""
        for tab in TAB_CONFIG:
            assert isinstance(tab["label"], str)
            assert len(tab["label"]) > 0
            assert len(tab["label"]) <= 50, f"Tab label too long: {tab['label']}"

    def test_tab_icons_are_font_awesome(self):
        """Test that all tab icons use Font Awesome class format."""
        for tab in TAB_CONFIG:
            icon = tab["icon"]
            assert isinstance(icon, str)
            # Should be like "fa-chart-line" (without "fas" prefix)
            assert icon.startswith("fa-"), f"Icon should start with 'fa-': {icon}"

    def test_tab_colors_are_valid(self):
        """Test that all tab colors are valid hex codes."""
        import re

        hex_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")

        for tab in TAB_CONFIG:
            color = tab["color"]
            assert isinstance(color, str)
            assert hex_pattern.match(color), f"Invalid color hex code: {color}"

    def test_tab_requires_data_is_boolean(self):
        """Test that requires_data field is boolean for all tabs."""
        for tab in TAB_CONFIG:
            assert isinstance(tab["requires_data"], bool)

    def test_tab_help_content_ids_not_empty(self):
        """Test that all help content IDs are non-empty strings."""
        for tab in TAB_CONFIG:
            help_id = tab["help_content_id"]
            assert isinstance(help_id, str)
            assert len(help_id) > 0

    def test_expected_tab_ids_present(self):
        """Test that all expected tabs are present in the registry."""
        expected_tab_ids = [
            "tab-dashboard",
            "tab-burndown",
            "tab-scope-tracking",
            "tab-bug-analysis",
        ]

        actual_tab_ids = [tab["id"] for tab in TAB_CONFIG]

        for expected_id in expected_tab_ids:
            assert expected_id in actual_tab_ids, (
                f"Expected tab '{expected_id}' not found in registry"
            )

    def test_tab_colors_use_design_tokens(self):
        """Test that tab colors match design token colors."""
        # Map expected tab colors to design token colors
        expected_colors = {
            "tab-dashboard": get_color("primary"),
            "tab-burndown": get_color("info"),
            "tab-scope-tracking": get_color("secondary"),
            "tab-bug-analysis": get_color("danger"),
        }

        for tab in TAB_CONFIG:
            expected_color = expected_colors.get(tab["id"])
            if expected_color:
                assert tab["color"] == expected_color, (
                    f"Tab {tab['id']} color should be {expected_color}, got {tab['color']}"
                )


class TestGetTabById:
    """Test the get_tab_by_id helper function."""

    def test_get_existing_tab(self):
        """Test retrieving an existing tab by ID."""
        tab = get_tab_by_id("tab-dashboard")
        assert tab is not None
        assert tab["id"] == "tab-dashboard"  # type: ignore[index]
        assert tab["label"] == "Dashboard"  # type: ignore[index]

    def test_get_all_tabs_by_id(self):
        """Test retrieving all tabs by their IDs."""
        for expected_tab in TAB_CONFIG:
            tab = get_tab_by_id(expected_tab["id"])
            assert tab is not None
            assert tab["id"] == expected_tab["id"]  # type: ignore[index]

    def test_get_nonexistent_tab(self):
        """Test retrieving a non-existent tab returns None."""
        tab = get_tab_by_id("tab-nonexistent")
        assert tab is None

    def test_get_tab_empty_string(self):
        """Test retrieving tab with empty string ID returns None."""
        tab = get_tab_by_id("")
        assert tab is None

    def test_get_tab_returns_correct_structure(self):
        """Test that retrieved tab has all required fields."""
        tab = get_tab_by_id("tab-burndown")
        assert tab is not None
        assert "id" in tab  # type: ignore[operator]
        assert "label" in tab  # type: ignore[operator]
        assert "icon" in tab  # type: ignore[operator]
        assert "color" in tab  # type: ignore[operator]
        assert "order" in tab  # type: ignore[operator]
        assert "requires_data" in tab  # type: ignore[operator]
        assert "help_content_id" in tab  # type: ignore[operator]


class TestGetTabsSorted:
    """Test the get_tabs_sorted helper function."""

    def test_get_tabs_sorted_returns_list(self):
        """Test that function returns a list."""
        tabs = get_tabs_sorted()
        assert isinstance(tabs, list)

    def test_get_tabs_sorted_returns_all_tabs(self):
        """Test that function returns all tabs."""
        tabs = get_tabs_sorted()
        assert len(tabs) == len(TAB_CONFIG)

    def test_get_tabs_sorted_order(self):
        """Test that tabs are sorted by order field."""
        tabs = get_tabs_sorted()

        for i in range(len(tabs) - 1):
            assert tabs[i]["order"] < tabs[i + 1]["order"], (
                "Tabs should be sorted by order"
            )

    def test_get_tabs_sorted_dashboard_first(self):
        """Test that Dashboard tab is first after sorting."""
        tabs = get_tabs_sorted()
        assert tabs[0]["id"] == "tab-dashboard"
        assert tabs[0]["order"] == 0

    def test_get_tabs_sorted_maintains_structure(self):
        """Test that sorting doesn't modify tab structure."""
        tabs = get_tabs_sorted()

        for tab in tabs:
            assert "id" in tab
            assert "label" in tab
            assert "order" in tab


class TestValidateTabId:
    """Test the validate_tab_id helper function."""

    def test_validate_existing_tab_ids(self):
        """Test that all existing tab IDs validate as True."""
        for tab in TAB_CONFIG:
            assert validate_tab_id(tab["id"]) is True

    def test_validate_nonexistent_tab_id(self):
        """Test that non-existent tab ID validates as False."""
        assert validate_tab_id("tab-nonexistent") is False

    def test_validate_empty_string(self):
        """Test that empty string validates as False."""
        assert validate_tab_id("") is False

    def test_validate_invalid_pattern(self):
        """Test that invalid tab ID pattern validates as False."""
        assert validate_tab_id("not-a-tab-id") is False
        assert validate_tab_id("TAB-UPPERCASE") is False
        assert validate_tab_id("tab_underscore") is False

    def test_validate_dashboard_tab(self):
        """Test that dashboard tab ID validates correctly."""
        assert validate_tab_id("tab-dashboard") is True

    def test_validate_case_sensitive(self):
        """Test that validation is case-sensitive."""
        assert validate_tab_id("tab-dashboard") is True
        assert validate_tab_id("tab-Dashboard") is False
        assert validate_tab_id("TAB-DASHBOARD") is False


class TestTabConfigIntegration:
    """Integration tests for tab configuration."""

    def test_tab_order_matches_retrieval(self):
        """Test that sorted tabs match expected order."""
        sorted_tabs = get_tabs_sorted()

        expected_order = [
            "tab-dashboard",
            "tab-burndown",
            "tab-scope-tracking",
            "tab-bug-analysis",
            "tab-flow-metrics",  # Flow before DORA - better workflow
            "tab-dora-metrics",
            "tab-active-work-timeline",
            "tab-sprint-tracker",
            "tab-statistics-data",  # Last position - specialized manual data entry
        ]

        actual_order = [tab["id"] for tab in sorted_tabs]
        assert actual_order == expected_order

    def test_all_tabs_retrievable_and_valid(self):
        """Test that all tabs can be retrieved and validated."""
        for tab in TAB_CONFIG:
            # Validate ID
            assert validate_tab_id(tab["id"]) is True

            # Retrieve by ID
            retrieved = get_tab_by_id(tab["id"])
            assert retrieved is not None
            assert retrieved["id"] == tab["id"]  # type: ignore[index]

    def test_tab_colors_consistent_with_design_tokens(self):
        """Test that tab colors are consistent across registry."""
        # Get dashboard color (should be primary)
        dashboard = get_tab_by_id("tab-dashboard")
        assert dashboard is not None
        assert dashboard["color"] == get_color("primary")  # type: ignore[index]

        # Get bug analysis color (should be danger)
        bugs = get_tab_by_id("tab-bug-analysis")
        assert bugs is not None
        assert bugs["color"] == get_color("danger")  # type: ignore[index]
