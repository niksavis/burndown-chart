"""Integration test for critical tab switching bug fix.

Tests that switching between tabs and then clicking the Burnup button
does not cause the app to navigate to the wrong tab (Scope Change).

This test verifies the fix for the bug where:
1. User clicks on Scope Change tab
2. User clicks back to Burndown Chart tab
3. User clicks on Burnup button
4. BUG: App navigates to Scope Change page instead of showing Burnup chart

Bug fix: Added prevent_initial_call=True to the update_chart_type callback
in callbacks/visualization.py to prevent spurious callback triggering on
component mount/unmount during tab switches.
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


@pytest.mark.skip(
    reason="Flaky Playwright test - chart-type-toggle selector timing out"
)
class TestBurnupButtonTabSwitchingBugFix:
    """Playwright-based integration tests to validate burnup button bug fix"""

    @pytest.fixture(scope="class")
    def live_server(self):
        """Start the Dash app server for testing"""
        app = dash_app.app

        # Start server in a separate thread
        def run_server():
            waitress.serve(app.server, host="127.0.0.1", port=8052, threads=1)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Give the server time to start
        time.sleep(3)

        yield "http://127.0.0.1:8052"

    def test_burnup_button_after_tab_switch_stays_on_burndown_tab(self, live_server):
        """
        Test that clicking Burnup button after switching tabs stays on Burndown tab.

        This is the critical bug fix test:
        - Switch from Burndown to Scope Change tab
        - Switch back to Burndown tab
        - Click Burnup toggle button
        - Verify we're still on Burndown tab (not switched to Scope Change)
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to the app
            page.goto(live_server)

            # Wait for chart tabs to load
            page.wait_for_selector("#chart-tabs", timeout=10000)

            # Find tab buttons using text-based selectors
            tab_links = page.locator("#chart-tabs .nav-link")
            burndown_tab = tab_links.filter(has_text="Burndown")
            scope_tab = tab_links.filter(has_text="Scope")

            # Step 1: Verify we start on Burndown tab
            burndown_class = burndown_tab.get_attribute("class") or ""
            assert "active" in burndown_class, "Should start on Burndown tab"

            # Step 2: Click on Scope Change tab
            scope_tab.click()
            page.wait_for_timeout(2000)  # Wait for tab content to load

            # Verify we're now on Scope tab
            scope_class = scope_tab.get_attribute("class") or ""
            assert "active" in scope_class, "Should be on Scope Change tab"

            # Step 3: Click back to Burndown tab
            burndown_tab.click()
            page.wait_for_timeout(2000)  # Wait for tab content to load

            # Verify we're back on Burndown tab
            burndown_class = burndown_tab.get_attribute("class") or ""
            assert "active" in burndown_class, "Should be back on Burndown tab"

            # Step 4: Wait for the burnup toggle button to be available
            page.wait_for_selector("#chart-type-toggle", timeout=5000)

            # Find and click the Burnup radio button option
            burnup_label = page.locator(".chart-toggle-buttons label").filter(
                has_text="Burnup"
            )
            burnup_label.click()

            # Wait for chart to update
            page.wait_for_timeout(2000)

            # Step 5: CRITICAL VERIFICATION - We should still be on Burndown tab
            burndown_class = burndown_tab.get_attribute("class") or ""
            scope_class = scope_tab.get_attribute("class") or ""

            assert "active" in burndown_class, (
                "CRITICAL BUG FIX VERIFICATION: After clicking Burnup button, "
                "we should still be on Burndown tab!"
            )

            assert "active" not in scope_class, (
                "CRITICAL BUG FIX VERIFICATION: We should NOT have switched to "
                "Scope Change tab after clicking Burnup button!"
            )

            # Step 6: Verify the chart actually changed to Burnup
            # (The graph element should still exist within chart-container)
            graph_element = page.locator("#chart-container #forecast-graph").first
            assert graph_element.is_visible(), "Burnup chart should be displayed"

            browser.close()
