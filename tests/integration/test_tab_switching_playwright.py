"""
Playwright-based integration test to validate that the critical tab switching bug has been resolved.

This test specifically addresses the issue where clicking on any tab (like 'Items per week'
or 'Points per week') would briefly switch to that tab but then automatically revert
to the first tab ('Burndown Chart') due to callback conflicts.

The bug was caused by both the mobile navigation callback and regular tab functionality
trying to control the same output ("chart-tabs", "active_tab"), creating a race condition.

Bug fix: Removed the conflicting Output("chart-tabs", "active_tab") from the mobile
navigation callback in callbacks/mobile_navigation.py
"""

import pytest
import time
import threading
from playwright.sync_api import sync_playwright
import waitress
import sys
import os

# Add the project root to the path to import the app directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app as dash_app


class TestTabSwitchingBugFixPlaywright:
    """Playwright-based integration tests to validate tab switching bug fix"""

    @pytest.fixture(scope="class")
    def live_server(self):
        """Start the Dash app server for testing"""
        app = dash_app.app

        # Start server in a separate thread
        def run_server():
            waitress.serve(app.server, host="127.0.0.1", port=8051, threads=1)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Give the server time to start
        time.sleep(3)

        yield "http://127.0.0.1:8051"

    def test_tab_switching_stability_playwright(self, live_server):
        """Test that tab switching works correctly without auto-reverting"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to the app
            page.goto(live_server)

            # Wait for chart tabs to load
            page.wait_for_selector("#chart-tabs", timeout=10000)

            # Find tab buttons using text-based selectors (more reliable than dynamic IDs)
            tab_links = page.locator("#chart-tabs .nav-link")
            burndown_tab = tab_links.filter(has_text="Burndown Chart")
            items_tab = tab_links.filter(has_text="Items per Week")
            points_tab = tab_links.filter(has_text="Points per Week")

            # Test clicking on "Items per Week" tab
            items_tab.click()
            page.wait_for_timeout(2000)  # Wait for any potential race conditions

            # Verify the tab stays active (no auto-revert to burndown)
            items_class = items_tab.get_attribute("class") or ""
            burndown_class = burndown_tab.get_attribute("class") or ""

            assert "active" in items_class, (
                "Items per Week tab should remain active after clicking"
            )

            assert "active" not in burndown_class, (
                "Burndown Chart tab should not be active when Items tab is selected"
            )

            # Test clicking on "Points per Week" tab
            points_tab.click()
            page.wait_for_timeout(2000)  # Wait for any potential race conditions

            # Verify the tab stays active
            points_class = points_tab.get_attribute("class") or ""
            items_class = items_tab.get_attribute("class") or ""
            burndown_class = burndown_tab.get_attribute("class") or ""

            assert "active" in points_class, (
                "Points per Week tab should remain active after clicking"
            )

            assert "active" not in items_class, (
                "Items per Week tab should not be active when Points tab is selected"
            )

            assert "active" not in burndown_class, (
                "Burndown Chart tab should not be active when Points tab is selected"
            )

            browser.close()

    def test_mobile_navigation_no_interference_playwright(self, live_server):
        """Test that mobile navigation doesn't interfere with tab switching"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Set mobile viewport
            page.set_viewport_size({"width": 375, "height": 667})  # iPhone size

            # Navigate to the app
            page.goto(live_server)

            # Wait for mobile navigation to be visible
            page.wait_for_selector("#mobile-bottom-navigation", timeout=10000)

            # Find tab buttons using mobile-specific selectors
            items_tab = page.locator("#bottom-nav-tab-items")
            points_tab = page.locator("#bottom-nav-tab-points")

            # Click on Items tab in mobile view
            items_tab.click()
            page.wait_for_timeout(2000)

            # Verify tab remains active in mobile
            items_class = items_tab.get_attribute("class") or ""
            assert "active" in items_class, (
                "Items tab should remain active in mobile view"
            )

            # Click on Points tab in mobile view
            points_tab.click()
            page.wait_for_timeout(2000)

            # Verify tab remains active in mobile
            points_class = points_tab.get_attribute("class") or ""
            assert "active" in points_class, (
                "Points tab should remain active in mobile view"
            )

            browser.close()

    def test_callback_conflict_resolution_playwright(self, live_server):
        """Test that callback conflicts have been resolved"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to the app
            page.goto(live_server)

            # Wait for page load
            page.wait_for_selector("#chart-tabs", timeout=10000)

            # Perform rapid tab switching to test for race conditions
            tab_links = page.locator("#chart-tabs .nav-link")
            burndown_tab = tab_links.filter(has_text="Burndown Chart")
            items_tab = tab_links.filter(has_text="Items per Week")
            points_tab = tab_links.filter(has_text="Points per Week")

            # Rapid switching test
            for _ in range(3):
                items_tab.click()
                page.wait_for_timeout(500)
                points_tab.click()
                page.wait_for_timeout(500)
                burndown_tab.click()
                page.wait_for_timeout(500)

            # Final click on Items tab
            items_tab.click()
            page.wait_for_timeout(2000)  # Wait for any delayed callbacks

            # Verify the final state is correct
            items_class = items_tab.get_attribute("class") or ""
            burndown_class = burndown_tab.get_attribute("class") or ""
            points_class = points_tab.get_attribute("class") or ""

            assert "active" in items_class, (
                "Items tab should be active after rapid switching test"
            )

            # Verify no other tabs are accidentally active
            assert "active" not in burndown_class, "Burndown tab should not be active"
            assert "active" not in points_class, "Points tab should not be active"

            browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
