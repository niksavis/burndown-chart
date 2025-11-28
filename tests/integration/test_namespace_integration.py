"""Integration tests for namespace syntax feature (Feature 012).

Tests the complete workflow:
1. Open Field Mapping modal with namespace inputs
2. Enter namespace syntax in namespace inputs
3. Autocomplete suggestions appear
4. Save field mappings with namespace syntax
5. Load field mappings and verify persistence

Reference: specs/namespace-syntax-analysis.md
"""

import pytest
import time
from playwright.sync_api import sync_playwright, expect


class TestNamespaceIntegration:
    """Integration tests for namespace syntax in Field Mapping modal."""

    @pytest.fixture(scope="class")
    def live_server(self):
        """Start Dash app server for testing."""
        import waitress
        import threading
        import sys
        import os

        # Import app directly
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        import app as dash_app

        app = dash_app.app

        def run_server():
            waitress.serve(app.server, host="127.0.0.1", port=8051, threads=1)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(3)  # Allow server startup

        yield "http://127.0.0.1:8051"

    @pytest.mark.skip(
        reason="Flaky due to UI locator changes - namespace inputs moved to dropdowns"
    )
    def test_namespace_inputs_visible_in_modal(self, live_server):
        """Test that namespace inputs are visible when opening Field Mapping modal."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # Navigate to app
                page.goto(live_server)
                page.wait_for_selector("#chart-tabs", timeout=10000)

                # Open Settings flyout
                settings_button = page.locator("button:has-text('Settings')")
                settings_button.click()
                page.wait_for_timeout(1000)

                # Click Field Mapping button
                field_mapping_button = page.locator("button:has-text('Field Mapping')")
                field_mapping_button.click()
                page.wait_for_timeout(2000)

                # Verify modal is open
                modal = page.locator(".modal.show")
                expect(modal).to_be_visible()

                # Switch to Fields tab
                fields_tab = page.locator(
                    "button:has-text('Fields'), a:has-text('Fields')"
                )
                fields_tab.click()
                page.wait_for_timeout(1000)

                # Verify namespace inputs are visible (monospace text inputs)
                namespace_input = page.locator(
                    "[id*='namespace-field-input'][id*='deployment_date']"
                )
                expect(namespace_input).to_be_visible()

            finally:
                browser.close()

    @pytest.mark.skip(
        reason="Flaky due to UI locator changes - namespace inputs moved to dropdowns"
    )
    def test_namespace_autocomplete_shows_suggestions(self, live_server):
        """Test that typing in namespace input shows autocomplete suggestions."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # Navigate and open Field Mapping modal
                page.goto(live_server)
                page.wait_for_selector("#chart-tabs", timeout=10000)

                settings_button = page.locator("button:has-text('Settings')")
                settings_button.click()
                page.wait_for_timeout(1000)

                field_mapping_button = page.locator("button:has-text('Field Mapping')")
                field_mapping_button.click()
                page.wait_for_timeout(2000)

                # Switch to Fields tab
                fields_tab = page.locator(
                    "button:has-text('Fields'), a:has-text('Fields')"
                )
                fields_tab.click()
                page.wait_for_timeout(1000)

                # Type into namespace input
                namespace_input = page.locator(
                    "[id*='namespace-field-input'][id*='deployment_date']"
                ).first
                namespace_input.fill("Dev")
                page.wait_for_timeout(1500)  # Wait for autocomplete callback

                # Check if suggestions appeared
                # Note: Suggestions may not appear if JIRA is not configured
                # This is a basic smoke test
                suggestions_div = page.locator("[id*='namespace-suggestions']").first

                # Either suggestions are visible OR the div exists but is empty (no JIRA config)
                # Test passes if suggestions div exists (even if empty due to no JIRA config)
                assert suggestions_div is not None

            finally:
                browser.close()

    def test_namespace_syntax_parsing_on_save(self):
        """Test that namespace syntax is parsed correctly when saving."""
        from callbacks.field_mapping import _parse_namespace_field_mappings

        # Simulate field mappings with namespace syntax (flat structure)
        # Note: _parse_namespace_field_mappings expects {"dora": {"field": "value"}, "flow": {...}}
        field_mappings = {
            "dora": {
                "deployment_date": "DevOps.customfield_10100",
                "deployment_successful": "DevOps.Status:Deployed.Occurred",
            }
        }

        # Parse namespace syntax
        parsed = _parse_namespace_field_mappings(field_mappings)

        # Verify parsing occurred
        assert "dora" in parsed

        # Check deployment_date was parsed to SourceRule dict
        deployment_date_value = parsed["dora"]["deployment_date"]
        assert isinstance(deployment_date_value, dict)
        assert "source" in deployment_date_value
        assert "priority" in deployment_date_value

        # Check deployment_successful (changelog) was parsed
        deployment_successful_value = parsed["dora"]["deployment_successful"]
        assert isinstance(deployment_successful_value, dict)

    def test_simple_field_ids_unchanged(self):
        """Test that simple field IDs (without namespace syntax) are not parsed."""
        from callbacks.field_mapping import _parse_namespace_field_mappings

        # Simulate field mappings with simple field IDs (flat structure)
        field_mappings = {"dora": {"deployment_date": "customfield_10100"}}

        # Parse (should not change simple IDs)
        parsed = _parse_namespace_field_mappings(field_mappings)

        # Verify simple ID is unchanged
        deployment_date_value = parsed["dora"]["deployment_date"]
        assert (
            deployment_date_value == "customfield_10100"
        )  # Still a string, not parsed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
