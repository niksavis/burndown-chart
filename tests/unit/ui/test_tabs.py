from ui.style_constants import get_color
from ui.tabs import (
    TAB_CONFIG,
    get_tab_by_id,
    get_tabs_sorted,
    validate_tab_id,
)


class TestTabConfigRegistry:
    def test_tab_config_exists(self):
        assert TAB_CONFIG is not None
        assert len(TAB_CONFIG) > 0

    def test_tab_config_has_seven_tabs(self):
        assert len(TAB_CONFIG) == 9

    def test_tab_config_structure(self):
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
        tab_ids = [tab["id"] for tab in TAB_CONFIG]
        assert len(tab_ids) == len(set(tab_ids)), "Tab IDs must be unique"

    def test_tab_orders_are_unique(self):
        orders = [tab["order"] for tab in TAB_CONFIG]
        assert len(orders) == len(set(orders)), "Tab orders must be unique"

    def test_tab_orders_are_sequential(self):
        orders = sorted([tab["order"] for tab in TAB_CONFIG])
        expected_orders = list(range(len(TAB_CONFIG)))
        assert orders == expected_orders, (
            f"Orders should be {expected_orders}, got {orders}"
        )

    def test_dashboard_is_first_tab(self):
        dashboard_tab = next(
            (t for t in TAB_CONFIG if t["id"] == "tab-dashboard"), None
        )
        assert dashboard_tab is not None, "Dashboard tab must exist"
        assert dashboard_tab["order"] == 0, "Dashboard must be first tab (order 0)"

    def test_tab_id_pattern(self):
        import re

        pattern = re.compile(r"^tab-[a-z-]+$")

        for tab in TAB_CONFIG:
            assert pattern.match(tab["id"]), (
                f"Tab ID '{tab['id']}' doesn't match pattern 'tab-{{name}}'"
            )

    def test_tab_labels_not_empty(self):
        for tab in TAB_CONFIG:
            assert isinstance(tab["label"], str)
            assert len(tab["label"]) > 0
            assert len(tab["label"]) <= 50, f"Tab label too long: {tab['label']}"

    def test_tab_icons_are_font_awesome(self):
        for tab in TAB_CONFIG:
            icon = tab["icon"]
            assert isinstance(icon, str)
            assert icon.startswith("fa-"), f"Icon should start with 'fa-': {icon}"

    def test_tab_colors_are_valid(self):
        import re

        hex_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")

        for tab in TAB_CONFIG:
            color = tab["color"]
            assert isinstance(color, str)
            assert hex_pattern.match(color), f"Invalid color hex code: {color}"

    def test_tab_requires_data_is_boolean(self):
        for tab in TAB_CONFIG:
            assert isinstance(tab["requires_data"], bool)

    def test_tab_help_content_ids_not_empty(self):
        for tab in TAB_CONFIG:
            help_id = tab["help_content_id"]
            assert isinstance(help_id, str)
            assert len(help_id) > 0

    def test_expected_tab_ids_present(self):
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
                    f"Tab {tab['id']} color should be {expected_color}, "
                    f"got {tab['color']}"
                )


class TestGetTabById:
    def test_get_existing_tab(self):
        tab = get_tab_by_id("tab-dashboard")
        assert tab is not None
        assert tab["id"] == "tab-dashboard"  # type: ignore[index]
        assert tab["label"] == "Dashboard"  # type: ignore[index]

    def test_get_all_tabs_by_id(self):
        for expected_tab in TAB_CONFIG:
            tab = get_tab_by_id(expected_tab["id"])
            assert tab is not None
            assert tab["id"] == expected_tab["id"]  # type: ignore[index]

    def test_get_nonexistent_tab(self):
        tab = get_tab_by_id("tab-nonexistent")
        assert tab is None

    def test_get_tab_empty_string(self):
        tab = get_tab_by_id("")
        assert tab is None

    def test_get_tab_returns_correct_structure(self):
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
    def test_get_tabs_sorted_returns_list(self):
        tabs = get_tabs_sorted()
        assert isinstance(tabs, list)

    def test_get_tabs_sorted_returns_all_tabs(self):
        tabs = get_tabs_sorted()
        assert len(tabs) == len(TAB_CONFIG)

    def test_get_tabs_sorted_order(self):
        tabs = get_tabs_sorted()

        for i in range(len(tabs) - 1):
            assert tabs[i]["order"] < tabs[i + 1]["order"], (
                "Tabs should be sorted by order"
            )

    def test_get_tabs_sorted_dashboard_first(self):
        tabs = get_tabs_sorted()
        assert tabs[0]["id"] == "tab-dashboard"
        assert tabs[0]["order"] == 0

    def test_get_tabs_sorted_maintains_structure(self):
        tabs = get_tabs_sorted()

        for tab in tabs:
            assert "id" in tab
            assert "label" in tab
            assert "order" in tab


class TestValidateTabId:
    def test_validate_existing_tab_ids(self):
        for tab in TAB_CONFIG:
            assert validate_tab_id(tab["id"]) is True

    def test_validate_nonexistent_tab_id(self):
        assert validate_tab_id("tab-nonexistent") is False

    def test_validate_empty_string(self):
        assert validate_tab_id("") is False

    def test_validate_invalid_pattern(self):
        assert validate_tab_id("not-a-tab-id") is False
        assert validate_tab_id("TAB-UPPERCASE") is False
        assert validate_tab_id("tab_underscore") is False

    def test_validate_dashboard_tab(self):
        assert validate_tab_id("tab-dashboard") is True

    def test_validate_case_sensitive(self):
        assert validate_tab_id("tab-dashboard") is True
        assert validate_tab_id("tab-Dashboard") is False
        assert validate_tab_id("TAB-DASHBOARD") is False


class TestTabConfigIntegration:
    def test_tab_order_matches_retrieval(self):
        sorted_tabs = get_tabs_sorted()

        expected_order = [
            "tab-dashboard",
            "tab-burndown",
            "tab-scope-tracking",
            "tab-bug-analysis",
            "tab-flow-metrics",
            "tab-dora-metrics",
            "tab-active-work-timeline",
            "tab-sprint-tracker",
            "tab-statistics-data",
        ]

        actual_order = [tab["id"] for tab in sorted_tabs]
        assert actual_order == expected_order

    def test_all_tabs_retrievable_and_valid(self):
        for tab in TAB_CONFIG:
            assert validate_tab_id(tab["id"]) is True

            retrieved = get_tab_by_id(tab["id"])
            assert retrieved is not None
            assert retrieved["id"] == tab["id"]  # type: ignore[index]

    def test_tab_colors_consistent_with_design_tokens(self):
        dashboard = get_tab_by_id("tab-dashboard")
        assert dashboard is not None
        assert dashboard["color"] == get_color("primary")  # type: ignore[index]

        bugs = get_tab_by_id("tab-bug-analysis")
        assert bugs is not None
        assert bugs["color"] == get_color("danger")  # type: ignore[index]
