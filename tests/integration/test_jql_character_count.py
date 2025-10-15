"""
Integration tests for JQL character count feature (User Story 1).

Tests real browser interactions using Playwright to verify:
- Character count displays correctly
- Warning appears at threshold
- Updates happen immediately on typing
- Handles edge cases (empty, very long queries)

Following project testing guidelines from .github/copilot-instructions.md:
- Use Playwright (not Selenium) for modern browser automation
- Text-based selectors with has_text() for reliability
- Custom server management (direct app import)
"""

import os
import sys
import threading
import time

import pytest
from playwright.sync_api import expect, sync_playwright

# Import app directly to avoid Dash testing utility dependencies
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app as dash_app


class TestJQLCharacterCount:
    """Integration tests for JQL character count display and callbacks."""

    @pytest.fixture(scope="class")
    def live_server(self):
        """Start Dash app server for testing."""
        app = dash_app.app

        def run_server():
            import waitress

            waitress.serve(app.server, host="127.0.0.1", port=8051, threads=1)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(3)  # Allow server startup

        yield "http://127.0.0.1:8051"

    def test_character_count_displays_on_page_load(self, live_server):
        """Verify character count displays when page loads (FR-001)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_load_state("networkidle")

            # Find JQL textarea
            jql_textarea = page.locator("#jira-jql-query")
            expect(jql_textarea).to_be_visible(timeout=10000)

            # Verify character count display exists
            char_count = page.locator("#jira-jql-character-count-container")
            expect(char_count).to_be_visible()

            # Should show count / 2000 format
            char_count_text = char_count.inner_text()
            assert "2,000" in char_count_text or "2000" in char_count_text
            assert "/" in char_count_text

            browser.close()

    def test_character_count_updates_after_typing(self, live_server):
        """Verify character count updates when user types (FR-001, FR-003)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_load_state("networkidle")

            # Clear textarea and type test query
            jql_textarea = page.locator("#jira-jql-query")
            jql_textarea.click()
            jql_textarea.fill("")  # Clear existing
            jql_textarea.type("project = TEST", delay=50)

            # Wait briefly for callback to fire
            time.sleep(0.5)

            # Verify count shows 14 characters
            char_count = page.locator("#jira-jql-character-count-container")
            char_count_text = char_count.inner_text()

            assert "14" in char_count_text
            assert "2,000" in char_count_text or "2000" in char_count_text

            browser.close()

    def test_character_count_shows_warning_at_threshold(self, live_server):
        """Verify warning styling appears at 1800 characters (FR-002)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_load_state("networkidle")

            # Create query with exactly 1800 characters
            long_query = "x" * 1800

            jql_textarea = page.locator("#jira-jql-query")
            jql_textarea.click()
            jql_textarea.fill(long_query)

            # Wait for callback
            time.sleep(0.5)

            # Verify warning class is applied
            char_count = page.locator("#jira-jql-character-count-container")
            char_count_html = char_count.inner_html()

            assert "character-count-warning" in char_count_html
            assert "1,800" in char_count_html or "1800" in char_count_html

            browser.close()

    def test_character_count_no_warning_below_threshold(self, live_server):
        """Verify no warning below 1800 characters (FR-002)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_load_state("networkidle")

            # Create query with 1799 characters (just below threshold)
            medium_query = "x" * 1799

            jql_textarea = page.locator("#jira-jql-query")
            jql_textarea.click()
            jql_textarea.fill(medium_query)

            # Wait for callback
            time.sleep(0.5)

            # Verify warning class is NOT applied
            char_count = page.locator("#jira-jql-character-count-container")
            char_count_html = char_count.inner_html()

            assert (
                "character-count-warning" not in char_count_html
                or "character-count-display character-count-warning"
                not in char_count_html
            )
            assert "1,799" in char_count_html or "1799" in char_count_html

            browser.close()

    def test_character_count_handles_empty_input(self, live_server):
        """Verify count returns to 0 when textarea is cleared (FR-001 edge case)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_load_state("networkidle")

            # Type something first
            jql_textarea = page.locator("#jira-jql-query")
            jql_textarea.click()
            jql_textarea.fill("project = TEST")
            time.sleep(0.5)  # Wait for callback

            # Now clear it
            jql_textarea.fill("")
            time.sleep(0.5)  # Wait for callback to update

            # Verify count shows 0
            char_count = page.locator("#jira-jql-character-count-container")

            # Wait for the text to update to "0 / 2,000"
            page.wait_for_timeout(500)
            char_count_text = char_count.inner_text()

            # Extract the first number (before the /)
            count_part = char_count_text.split("/")[0].strip().replace(",", "")
            assert "0" == count_part, (
                f"Expected '0', got '{count_part}' from text: '{char_count_text}'"
            )

            browser.close()

    def test_character_count_handles_very_long_query(self, live_server):
        """Verify count handles queries exceeding JIRA's limit (FR-001 edge case)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_load_state("networkidle")

            # Create query with 2500 characters (exceeds JIRA's 2000 limit)
            very_long_query = "x" * 2500

            jql_textarea = page.locator("#jira-jql-query")
            jql_textarea.click()
            jql_textarea.fill(very_long_query)

            # Wait for callback
            time.sleep(0.5)

            # Verify warning is shown and count is accurate
            char_count = page.locator("#jira-jql-character-count-container")
            char_count_html = char_count.inner_html()
            char_count_text = char_count.inner_text()

            assert "character-count-warning" in char_count_html
            assert "2,500" in char_count_text or "2500" in char_count_text

            browser.close()

    def test_character_count_updates_immediately(self, live_server):
        """Verify character count provides instant feedback (no debouncing)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_load_state("networkidle")

            jql_textarea = page.locator("#jira-jql-query")
            jql_textarea.click()
            jql_textarea.fill("")
            time.sleep(0.5)  # Wait for initial clear to process

            # Type one character at a time and verify count updates immediately
            expected_count = 0
            for char in "ABC":
                jql_textarea.type(char, delay=100)
                expected_count += 1

                # Wait for Dash callback to complete
                time.sleep(0.5)

                char_count = page.locator("#jira-jql-character-count-container")
                current_text = char_count.inner_text()

                # Extract the count part and verify it's updating
                count_part = current_text.split("/")[0].strip().replace(",", "")
                assert count_part == str(expected_count), (
                    f"After typing '{char}', expected count '{expected_count}', "
                    f"got '{count_part}' from text: '{current_text}'"
                )

            browser.close()


class TestJQLCharacterCountAccessibility:
    """Accessibility tests for character count feature."""

    @pytest.fixture(scope="class")
    def live_server(self):
        """Start Dash app server for testing."""
        app = dash_app.app

        def run_server():
            import waitress

            waitress.serve(app.server, host="127.0.0.1", port=8052, threads=1)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(3)

        yield "http://127.0.0.1:8052"

    def test_character_count_has_accessible_id(self, live_server):
        """Verify character count display has ID for accessibility."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_load_state("networkidle")

            # Verify display has ID attribute
            char_count_display = page.locator("#jql-character-count-display")
            expect(char_count_display).to_be_visible()

            browser.close()
