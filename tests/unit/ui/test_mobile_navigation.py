"""
Tests for Mobile Navigation Enhancement

This module tests the mobile navigation functionality including:
- Mobile drawer navigation
- Bottom navigation
- Swipe gesture support
- Touch interaction improvements
- Responsive navigation behavior
"""

import pytest


class TestMobileNavigation:
    """Test mobile navigation components and functionality."""

    def test_mobile_navigation_components_creation(self):
        """Test that mobile navigation components are created correctly."""
        from ui.mobile_navigation import (
            create_mobile_drawer_navigation,
            create_mobile_bottom_navigation,
            create_mobile_tab_controls,
            get_mobile_tabs_config,
        )

        # Test tab configuration
        tabs_config = get_mobile_tabs_config()
        assert (
            len(tabs_config) == 8
        )  # Updated: Now includes Dashboard, Bug Analysis, DORA, and Flow metrics
        assert all("id" in tab for tab in tabs_config)
        assert all("label" in tab for tab in tabs_config)
        assert all("icon" in tab for tab in tabs_config)

        # Test drawer navigation creation
        drawer = create_mobile_drawer_navigation(tabs_config)
        assert drawer is not None
        assert "mobile-drawer-container" in str(drawer)

        # Test bottom navigation creation
        bottom_nav = create_mobile_bottom_navigation(tabs_config)
        assert bottom_nav is not None
        assert "mobile-bottom-navigation" in str(bottom_nav)

        # Test mobile tab controls
        controls = create_mobile_tab_controls()
        assert controls is not None
        assert "mobile-menu-toggle" in str(controls)

    def test_mobile_tabs_config_structure(self):
        """Test mobile tab configuration structure."""
        from ui.mobile_navigation import get_mobile_tabs_config

        tabs_config = get_mobile_tabs_config()

        required_fields = ["id", "label", "short_label", "icon", "color"]
        for tab in tabs_config:
            for field in required_fields:
                assert field in tab, f"Tab {tab.get('id', 'unknown')} missing {field}"

        # Test specific tab IDs
        tab_ids = [tab["id"] for tab in tabs_config]
        expected_ids = [
            "tab-dashboard",  # Added in US2
            "tab-burndown",
            "tab-items",
            "tab-points",
            "tab-scope-tracking",
            "tab-bug-analysis",  # Added in Feature 004
            "tab-dora-metrics",  # Added in Feature 007
            "tab-flow-metrics",  # Added in Feature 007
        ]
        assert set(tab_ids) == set(expected_ids)

    def test_mobile_drawer_navigation_structure(self):
        """Test mobile drawer navigation structure and elements."""
        from ui.mobile_navigation import (
            create_mobile_drawer_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        drawer = create_mobile_drawer_navigation(tabs_config)

        # Convert to string for content checking
        drawer_str = str(drawer)

        # Check for essential drawer elements
        assert "mobile-drawer-overlay" in drawer_str
        assert "mobile-drawer" in drawer_str
        assert "mobile-drawer-header" in drawer_str
        assert "mobile-drawer-body" in drawer_str
        assert "mobile-drawer-close" in drawer_str

        # Check for drawer items
        for tab in tabs_config:
            assert f"drawer-{tab['id']}" in drawer_str

    def test_mobile_bottom_navigation_structure(self):
        """Test mobile bottom navigation structure and elements."""
        from ui.mobile_navigation import (
            create_mobile_bottom_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        bottom_nav = create_mobile_bottom_navigation(tabs_config, "tab-burndown")

        # Convert to string for content checking
        bottom_nav_str = str(bottom_nav)

        # Check for essential bottom navigation elements
        assert "mobile-bottom-navigation" in bottom_nav_str
        assert "d-md-none" in bottom_nav_str  # Hidden on desktop

        # Check for navigation items
        for tab in tabs_config:
            assert f"bottom-nav-{tab['id']}" in bottom_nav_str
            assert (
                tab["short_label"] in bottom_nav_str
                or tab["label"].split()[0] in bottom_nav_str
            )

    def test_mobile_tab_controls_elements(self):
        """Test mobile tab controls contain required elements."""
        from ui.mobile_navigation import create_mobile_tab_controls

        controls = create_mobile_tab_controls()
        controls_str = str(controls)

        # Check for essential control elements
        assert "mobile-menu-toggle" in controls_str
        assert "mobile-swipe-indicator" in controls_str
        assert "fas fa-bars" in controls_str  # Hamburger icon
        assert "Swipe to navigate" in controls_str

    def test_mobile_navigation_system_integration(self, temp_database):
        """Test complete mobile navigation system integration."""
        from ui.mobile_navigation import create_mobile_navigation_system
        from ui.layout import serve_layout

        # Check that navigation store exists in layout
        layout = serve_layout()
        layout_str = str(layout)
        assert "mobile-nav-state" in layout_str

        # Check that navigation system has core components
        nav_system = create_mobile_navigation_system()
        nav_system_str = str(nav_system)
        assert "mobile-drawer" in nav_system_str
        assert "mobile-bottom-navigation" in nav_system_str

    def test_mobile_navigation_css_classes(self):
        """Test that mobile navigation uses correct CSS classes."""
        from ui.mobile_navigation import (
            create_mobile_drawer_navigation,
            create_mobile_bottom_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()

        # Test drawer CSS classes
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

        # Test bottom navigation CSS classes
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
        """Test that mobile navigation elements meet touch target requirements."""
        from ui.mobile_navigation import create_mobile_tab_controls

        controls = create_mobile_tab_controls()
        controls_str = str(controls)

        # Check for touch target classes
        assert "mobile-touch-target-sm" in controls_str

        # Check for minimum dimensions in style attributes
        assert "minWidth" in controls_str or "min-width" in controls_str
        assert "minHeight" in controls_str or "min-height" in controls_str
        assert "44px" in controls_str  # Minimum touch target size

    def test_mobile_navigation_accessibility(self):
        """Test mobile navigation accessibility features."""
        from ui.mobile_navigation import (
            create_mobile_drawer_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        drawer = create_mobile_drawer_navigation(tabs_config)
        drawer_str = str(drawer)

        # Check for accessibility features
        # Note: Full aria-label testing would require rendering the actual components
        assert "Navigation" in drawer_str  # Drawer header text
        assert "fas fa-times" in drawer_str  # Close button icon

    def test_mobile_navigation_responsive_behavior(self):
        """Test mobile navigation responsive behavior indicators."""
        from ui.mobile_navigation import (
            create_mobile_bottom_navigation,
            get_mobile_tabs_config,
        )

        tabs_config = get_mobile_tabs_config()
        bottom_nav = create_mobile_bottom_navigation(tabs_config)
        bottom_nav_str = str(bottom_nav)

        # Check for responsive classes
        assert "d-md-none" in bottom_nav_str  # Hidden on medium screens and up


class TestMobileNavigationIntegration:
    """Test mobile navigation integration with the main application."""

    def test_mobile_navigation_in_tabs_module(self):
        """Test that tabs module properly imports mobile navigation."""
        from ui.tabs import create_tabs

        # Test that create_tabs can be called without errors
        tabs_component = create_tabs()
        assert tabs_component is not None

        # Check that mobile navigation is included
        tabs_str = str(tabs_component)
        assert "mobile-nav" in tabs_str or "mobile-drawer" in tabs_str

    def test_mobile_navigation_javascript_integration(self):
        """Test that mobile navigation JavaScript file exists and is properly structured."""
        import os

        js_file_path = "assets/mobile_navigation.js"
        assert os.path.exists(js_file_path), (
            "Mobile navigation JavaScript file not found"
        )

        # Read and check JavaScript content
        with open(js_file_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Check for essential JavaScript functions
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
        """Test that mobile navigation CSS is properly integrated."""
        import os

        css_file_path = "assets/custom.css"
        assert os.path.exists(css_file_path), "Custom CSS file not found"

        # Read and check CSS content
        with open(css_file_path, "r", encoding="utf-8") as f:
            css_content = f.read()

        # Check for mobile navigation CSS sections
        css_sections = [
            "MOBILE DRAWER NAVIGATION",
            "MOBILE BOTTOM NAVIGATION",
            "MOBILE TAB CONTROLS",
            "mobile-drawer",
            "mobile-bottom-navigation",
            "mobile-menu-toggle",
        ]

        for section in css_sections:
            assert section in css_content, f"Missing CSS section: {section}"


class TestMobileNavigationPerformance:
    """Test mobile navigation performance characteristics."""

    def test_mobile_component_creation_performance(self):
        """Test that mobile navigation components can be created quickly."""
        import time
        from ui.mobile_navigation import create_mobile_navigation_system

        start_time = time.time()
        nav_system = create_mobile_navigation_system()
        creation_time = time.time() - start_time

        # Should create components in under 100ms
        assert creation_time < 0.1, (
            f"Mobile navigation creation took {creation_time:.3f}s, should be < 0.1s"
        )
        assert nav_system is not None

    def test_mobile_navigation_memory_efficiency(self):
        """Test that mobile navigation doesn't create excessive components."""
        from ui.mobile_navigation import create_mobile_navigation_system
        import sys

        # Get initial memory usage
        initial_size = sys.getsizeof(str(create_mobile_navigation_system()))

        # Component should be reasonably sized (less than 50KB when serialized)
        assert initial_size < 50000, (
            f"Mobile navigation component size {initial_size} bytes is too large"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
