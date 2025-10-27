"""
Integration test for callback state management bug.

Tests that the render_tab_content callback correctly handles stale active_tab values
when triggered by non-tab-change inputs.

Critical Bug Scenario:
1. User visits Scope Change tab
2. User switches back to Burndown tab
3. User clicks ANYWHERE on the page (triggers callback via other inputs)
4. Bug: Scope Change content appears even though Burndown tab is still selected
5. Root Cause: Callback receives stale active_tab value pointing to Scope Change

Expected Fix:
- Callback should detect trigger source using callback_context
- If trigger is NOT chart-tabs, use ui_state["last_tab"] instead of active_tab parameter
- This ensures the correct tab content is displayed regardless of Input trigger source
"""

import pytest
from playwright.sync_api import sync_playwright


@pytest.mark.requires_app
@pytest.mark.browser
@pytest.mark.slow
class TestCallbackStateBug:
    """Test callback state management for render_tab_content"""

    def test_tab_content_stable_after_settings_change(self, live_server):
        """
        Test that changing settings doesn't cause tab content to switch.

        This tests the critical bug where ANY callback trigger (like settings changes)
        would cause the wrong tab content to display due to stale active_tab values.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to app
            page.goto(live_server)
            page.wait_for_selector("#chart-tabs", timeout=10000)

            # Step 1: Click Scope Change tab
            tab_links = page.locator("#chart-tabs .nav-link")
            # Use text that matches mobile navigation label
            scope_tab = tab_links.filter(has_text="Scope")

            # Wait for tabs to be visible and clickable
            page.wait_for_selector("#chart-tabs .nav-link", state="visible")

            # Click the Scope Change tab
            scope_tab.click()
            page.wait_for_timeout(2000)

            # Verify Scope Change content is displayed by checking tab-content div
            # Just verify SOMETHING loaded in tab-content
            tab_content = page.locator("#tab-content")
            assert tab_content.is_visible(), "Tab content area should be visible"

            # Step 2: Switch back to Burndown tab
            burndown_tab = tab_links.filter(has_text="Burndown")
            burndown_tab.click()
            page.wait_for_timeout(2000)

            # Verify Burndown content is displayed (use specific selector to avoid duplicates)
            burndown_chart = page.locator("#tab-content #forecast-graph").first
            assert burndown_chart.is_visible(), (
                "Burndown chart should be visible after tab switch"
            )

            # Step 3: Trigger a non-tab callback (e.g., toggle points display)
            # This triggers render_tab_content via points-toggle input
            points_toggle = page.locator("#points-toggle")
            if points_toggle.is_visible():
                points_toggle.click()
                page.wait_for_timeout(2000)

                # CRITICAL: Verify Burndown content is STILL displayed (not Scope Change)
                burndown_chart_after = page.locator(
                    "#tab-content #forecast-graph"
                ).first
                assert burndown_chart_after.is_visible(), (
                    "Burndown chart should remain visible after settings change"
                )

                # Verify Scope Change content is NOT displayed in tab-content
                # The bug would cause "Scope Change Analysis" text to appear in tab-content
                scope_content_after = page.locator("#tab-content").filter(
                    has_text="Scope Change Analysis"
                )
                # Use count() to check if element exists, as is_visible() can timeout
                scope_count = scope_content_after.count()
                assert scope_count == 0, (
                    "Scope Change content should NOT appear when Burndown tab is active"
                )

            browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
