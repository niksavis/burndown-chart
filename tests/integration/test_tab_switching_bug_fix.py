"""
Test for Tab Switching Bug Fix

This test validates that the critical tab switching bug has been resolved
where tabs would automatically switch back to the first tab after being clicked.
"""

import pytest
import time
from dash.testing.application_runners import import_app


class TestTabSwitchingBugFix:
    """Test that the tab switching bug has been resolved."""

    def test_tab_switching_stability(self, dash_duo):
        """Test that tabs stay active after being clicked and don't auto-revert."""
        app = import_app("app")
        dash_duo.start_server(app)

        # Wait for app to load
        dash_duo.wait_for_element("#chart-tabs", timeout=10)

        # Get all tab elements
        tab_items = dash_duo.find_elements("#chart-tabs .nav-link")
        assert len(tab_items) >= 3, "Should have at least 3 tabs available"

        # Test clicking on "Items per Week" tab (second tab)
        items_tab = None
        for tab in tab_items:
            if "Items" in tab.text or "items" in tab.text.lower():
                items_tab = tab
                break

        assert items_tab is not None, "Could not find Items per Week tab"

        # Click on the Items tab
        items_tab.click()

        # Wait a moment for any potential auto-switching to occur
        time.sleep(2)

        # Check if the Items tab is still active
        assert "active" in items_tab.get_attribute("class"), (
            "Items tab should remain active after clicking"
        )

        # Test clicking on "Points per Week" tab (third tab)
        points_tab = None
        for tab in tab_items:
            if "Points" in tab.text or "points" in tab.text.lower():
                points_tab = tab
                break

        assert points_tab is not None, "Could not find Points per Week tab"

        # Click on the Points tab
        points_tab.click()

        # Wait a moment for any potential auto-switching to occur
        time.sleep(2)

        # Check if the Points tab is still active
        assert "active" in points_tab.get_attribute("class"), (
            "Points tab should remain active after clicking"
        )

        # Verify that the Items tab is no longer active
        assert "active" not in items_tab.get_attribute("class"), (
            "Items tab should not be active after switching to Points"
        )

    def test_mobile_navigation_does_not_interfere_with_desktop_tabs(self, dash_duo):
        """Test that mobile navigation callbacks don't interfere with desktop tab functionality."""
        app = import_app("app")
        dash_duo.start_server(app)

        # Set desktop viewport
        dash_duo.driver.set_window_size(1200, 800)

        # Wait for app to load
        dash_duo.wait_for_element("#chart-tabs", timeout=10)

        # Test rapid tab switching to ensure no callback conflicts
        tab_items = dash_duo.find_elements("#chart-tabs .nav-link")

        for i in range(min(3, len(tab_items))):
            tab_items[i].click()
            time.sleep(0.5)  # Brief pause between clicks

            # Verify the clicked tab becomes active
            assert "active" in tab_items[i].get_attribute("class"), (
                f"Tab {i} should be active after clicking"
            )

    def test_callback_conflict_resolution(self, dash_duo):
        """Test that there are no callback conflicts causing auto-switching."""
        app = import_app("app")
        dash_duo.start_server(app)

        # Wait for app to load
        dash_duo.wait_for_element("#chart-tabs", timeout=10)

        # Get the initial active tab
        initial_active = dash_duo.find_element("#chart-tabs .nav-link.active")
        initial_tab_text = initial_active.text

        # Click on a different tab
        all_tabs = dash_duo.find_elements("#chart-tabs .nav-link")
        target_tab = None

        for tab in all_tabs:
            if tab.text != initial_tab_text:
                target_tab = tab
                break

        assert target_tab is not None, (
            "Should have at least one alternative tab to click"
        )

        # Click the target tab
        target_tab.click()

        # Wait longer to catch any delayed auto-switching
        time.sleep(3)

        # Verify no auto-switching occurred
        current_active = dash_duo.find_element("#chart-tabs .nav-link.active")
        assert current_active.text == target_tab.text, (
            "Tab should not auto-switch back to original tab"
        )
        assert current_active.text != initial_tab_text, (
            "Should not have reverted to initial tab"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
