import pytest


class TestMobileNavigation:
    def test_mobile_navigation_components_creation(self):
        from ui.mobile_navigation import (
            create_mobile_bottom_navigation,
            create_mobile_drawer_navigation,
            create_mobile_tab_controls,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        assert len(tabs_config) == 9
        assert all("id" in tab for tab in tabs_config)
        assert all("label" in tab for tab in tabs_config)
        assert all("icon" in tab for tab in tabs_config)

        drawer = create_mobile_drawer_navigation(tabs_config)
        assert drawer is not None
        assert "mobile-drawer-container" in str(drawer)

        bottom_nav = create_mobile_bottom_navigation(tabs_config)
        assert bottom_nav is not None
        assert "mobile-bottom-navigation" in str(bottom_nav)

        controls = create_mobile_tab_controls()
        assert controls is not None
        assert "mobile-menu-toggle" in str(controls)

    def test_mobile_tabs_config_structure(self):
        from ui.mobile_navigation import get_mobile_tabs_config

        tabs_config = get_mobile_tabs_config()

        required_fields = ["id", "label", "short_label", "icon", "color"]
        for tab in tabs_config:
            for field in required_fields:
                assert field in tab, f"Tab {tab.get('id', 'unknown')} missing {field}"

        tab_ids = [tab["id"] for tab in tabs_config]
        expected_ids = [
            "tab-dashboard",
            "tab-burndown",
            "tab-scope-tracking",
            "tab-bug-analysis",
            "tab-dora-metrics",
            "tab-flow-metrics",
            "tab-active-work-timeline",
            "tab-sprint-tracker",
            "tab-statistics-data",
        ]
        assert set(tab_ids) == set(expected_ids)

    def test_mobile_drawer_navigation_structure(self):
        from ui.mobile_navigation import (
            create_mobile_drawer_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        drawer = create_mobile_drawer_navigation(tabs_config)

        drawer_str = str(drawer)

        assert "mobile-drawer-overlay" in drawer_str
        assert "mobile-drawer" in drawer_str
        assert "mobile-drawer-header" in drawer_str
        assert "mobile-drawer-body" in drawer_str
        assert "mobile-drawer-close" in drawer_str

        for tab in tabs_config:
            assert f"drawer-{tab['id']}" in drawer_str

    def test_mobile_bottom_navigation_structure(self):
        from ui.mobile_navigation import (
            create_mobile_bottom_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        bottom_nav = create_mobile_bottom_navigation(tabs_config, "tab-burndown")

        bottom_nav_str = str(bottom_nav)

        assert "mobile-bottom-navigation" in bottom_nav_str
        assert "d-md-none" in bottom_nav_str

        primary_tabs = [
            tab for tab in tabs_config if tab.get("show_in_bottom_nav", True)
        ]
        for tab in primary_tabs:
            assert f"bottom-nav-{tab['id']}" in bottom_nav_str
            assert (
                tab["short_label"] in bottom_nav_str
                or tab["label"].split()[0] in bottom_nav_str
            )

        assert "bottom-nav-more-menu" in bottom_nav_str
        assert "More" in bottom_nav_str

        overflow_tabs = [
            tab for tab in tabs_config if not tab.get("show_in_bottom_nav", True)
        ]
        for tab in overflow_tabs:
            assert f"bottom-nav-{tab['id']}" not in bottom_nav_str

    def test_mobile_overflow_menu_structure(self):
        from ui.mobile_navigation import (
            create_mobile_overflow_menu,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        overflow_menu = create_mobile_overflow_menu(tabs_config)

        overflow_str = str(overflow_menu)

        assert "mobile-overflow-container" in overflow_str
        assert "mobile-overflow-overlay" in overflow_str
        assert "mobile-overflow-menu" in overflow_str
        assert "mobile-overflow-header" in overflow_str
        assert "mobile-overflow-body" in overflow_str

        overflow_tabs = [
            tab for tab in tabs_config if not tab.get("show_in_bottom_nav", True)
        ]
        for tab in overflow_tabs:
            assert f"overflow-menu-{tab['id']}" in overflow_str
            assert tab["label"] in overflow_str

        assert len(overflow_tabs) == 3

        primary_tabs = [
            tab for tab in tabs_config if tab.get("show_in_bottom_nav", True)
        ]
        for tab in primary_tabs:
            assert f"overflow-menu-{tab['id']}" not in overflow_str

    def test_mobile_tab_controls_elements(self):
        from ui.mobile_navigation import create_mobile_tab_controls

        controls = create_mobile_tab_controls()
        controls_str = str(controls)

        assert "mobile-menu-toggle" in controls_str
        assert "mobile-swipe-indicator" in controls_str
        assert "fas fa-bars" in controls_str
        assert "Swipe to navigate" in controls_str

    def test_mobile_navigation_system_integration(self, temp_database):
        from ui.layout import serve_layout
        from ui.mobile_navigation import create_mobile_navigation_system

        layout = serve_layout()
        layout_str = str(layout)
        assert "mobile-nav-state" in layout_str

        nav_system = create_mobile_navigation_system()
        nav_system_str = str(nav_system)
        assert "mobile-drawer" in nav_system_str
        assert "mobile-bottom-navigation" in nav_system_str
        assert "mobile-overflow-menu" in nav_system_str

    def test_mobile_navigation_css_classes(self):
        from ui.mobile_navigation import (
            create_mobile_bottom_navigation,
            create_mobile_drawer_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()

        drawer = create_mobile_drawer_navigation(tabs_config)
        drawer_str = str(drawer)

        mobile_classes = [
            "mobile-drawer-overlay",
            "mobile-drawer",
            "mobile-drawer-header",
            "mobile-drawer-body",
            "mobile-drawer-item",
        ]

        for css_class in mobile_classes:
            assert css_class in drawer_str, f"Missing CSS class: {css_class}"

        bottom_nav = create_mobile_bottom_navigation(tabs_config)
        bottom_nav_str = str(bottom_nav)

        bottom_nav_classes = [
            "mobile-bottom-navigation",
            "mobile-bottom-nav-wrapper",
            "mobile-bottom-nav-item",
            "mobile-bottom-nav-label",
        ]

        for css_class in bottom_nav_classes:
            assert css_class in bottom_nav_str, f"Missing CSS class: {css_class}"

    def test_mobile_navigation_touch_targets(self):
        from ui.mobile_navigation import create_mobile_tab_controls

        controls = create_mobile_tab_controls()
        controls_str = str(controls)

        assert "mobile-touch-target-sm" in controls_str

        assert "minWidth" in controls_str or "min-width" in controls_str
        assert "minHeight" in controls_str or "min-height" in controls_str
        assert "44px" in controls_str

    def test_mobile_navigation_accessibility(self):
        from ui.mobile_navigation import (
            create_mobile_drawer_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        drawer = create_mobile_drawer_navigation(tabs_config)
        drawer_str = str(drawer)

        assert "Navigation" in drawer_str
        assert "fas fa-times" in drawer_str

    def test_mobile_navigation_responsive_behavior(self):
        from ui.mobile_navigation import (
            create_mobile_bottom_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        bottom_nav = create_mobile_bottom_navigation(tabs_config)
        bottom_nav_str = str(bottom_nav)

        assert "d-md-none" in bottom_nav_str


class TestMobileNavigationIntegration:
    def test_mobile_navigation_in_tabs_module(self):
        from ui.tabs import create_tabs

        tabs_component = create_tabs()
        assert tabs_component is not None

        tabs_str = str(tabs_component)
        assert "tab-content-container" in tabs_str

    def test_mobile_navigation_javascript_integration(self):

        import os

        js_file_path = "assets/mobile_navigation.js"
        assert os.path.exists(js_file_path), (
            "Mobile navigation JavaScript file not found"
        )

        with open(js_file_path, encoding="utf-8") as f:
            js_content = f.read()

        essential_functions = [
            "initializeMobileNavigation",
            "initializeDrawerNavigation",
            "initializeSwipeGestures",
            "handleSwipeGesture",
            "switchToTab",
            "openMobileDrawer",
            "closeMobileDrawer",
        ]

        for function in essential_functions:
            assert function in js_content, f"Missing JavaScript function: {function}"

    def test_mobile_navigation_css_integration(self):
        import os

        css_file_path = "assets/custom.css"
        assert os.path.exists(css_file_path), "Custom CSS file not found"

        with open(css_file_path, encoding="utf-8") as f:
            css_content = f.read()

        import_lines = [
            "@import url('layout/mobile-navigation.css');",
            "@import url('components/drawer.css');",
            "@import url('components/bottom-nav.css');",
            "@import url('components/mobile-tabs.css');",
        ]

        for import_line in import_lines:
            assert import_line in css_content, f"Missing CSS import: {import_line}"

        component_files = [
            "assets/components/drawer.css",
            "assets/components/bottom-nav.css",
            "assets/components/mobile-tabs.css",
        ]
        section_markers = [
            ".mobile-drawer-overlay",
            ".mobile-bottom-navigation",
            ".mobile-tab-controls",
        ]

        for file_path, marker in zip(component_files, section_markers, strict=True):
            assert os.path.exists(file_path), f"Missing CSS file: {file_path}"
            with open(file_path, encoding="utf-8") as f:
                component_content = f.read()
            assert marker in component_content, f"Missing CSS section: {marker}"


class TestMobileNavigationPerformance:
    def test_mobile_component_creation_performance(self):
        import time

        from ui.mobile_navigation import create_mobile_navigation_system

        start_time = time.time()
        nav_system = create_mobile_navigation_system()
        creation_time = time.time() - start_time

        assert creation_time < 0.25, (
            f"Mobile navigation creation took {creation_time:.3f}s, should be < 0.25s"
        )
        assert nav_system is not None

    def test_mobile_navigation_memory_efficiency(self):
        import sys

        from ui.mobile_navigation import create_mobile_navigation_system

        initial_size = sys.getsizeof(str(create_mobile_navigation_system()))

        assert initial_size < 50000, (
            f"Mobile navigation component size {initial_size} bytes is too large"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
