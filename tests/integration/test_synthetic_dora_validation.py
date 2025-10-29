"""
Integration test for DORA/Flow metrics with JIRA dataset.

This test verifies that:
1. App loads successfully with JIRA data (Apache Kafka project)
2. DORA & Flow Metrics tab displays without errors
3. Metrics calculate successfully (may use Issue Tracker mode with proxy fields)
4. Metric cards display with values or appropriate error states
"""

import time
import pytest
from playwright.sync_api import sync_playwright


class TestSyntheticDoraValidation:
    """Test DORA/Flow metrics with JIRA data (Apache Kafka project)."""

    @pytest.fixture(scope="class")
    def live_server(self):
        """App should already be running on port 8050."""
        # Wait a moment for server to be fully ready
        time.sleep(2)
        yield "http://127.0.0.1:8050"

    def test_dora_metrics_with_synthetic_data(self, live_server):
        """Test DORA metrics calculation with JIRA data (may use Issue Tracker mode)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Show browser for debugging
            page = browser.new_page()

            try:
                # Navigate to app
                page.goto(live_server, timeout=15000)
                print("[OK] App loaded successfully")

                # Wait for main content to load
                page.wait_for_selector("#chart-tabs", timeout=10000)
                print("[OK] Main tabs loaded")

                # Find DORA Metrics tab
                dora_tab = page.locator("#chart-tabs .nav-link").filter(
                    has_text="DORA Metrics"
                )
                print("[OK] Found DORA Metrics tab")

                # Click the tab
                dora_tab.click()
                time.sleep(3)  # Wait for content to load

                # Verify tab is active
                dora_class = dora_tab.get_attribute("class") or ""
                assert "active" in dora_class, "DORA tab should be active"
                print("[X] DORA Metrics tab is active")

                # Wait for DORA metrics section to load
                page.wait_for_selector("#dora-metrics-cards-container", timeout=10000)
                print("[X] DORA metrics section loaded")

                # Click "Calculate DORA Metrics" button
                calculate_button = page.locator("#dora-refresh-button")
                calculate_button.click()
                print("[X] Clicked Calculate DORA Metrics button")

                # Wait for metrics to calculate (show loading then results)
                time.sleep(5)

                # Check for validation alerts
                alert_divs = page.locator(".alert").all()
                alert_texts = []
                for alert in alert_divs:
                    try:
                        text = alert.inner_text()
                        alert_texts.append(text)
                    except Exception as e:
                        print(f"Could not read alert text: {e}")
                        alert_texts.append("")
                
                print(f"Alert messages found: {len(alert_texts)}")
                for i, text in enumerate(alert_texts, 1):
                    try:
                        # Remove emoji and special characters for printing
                        clean_text = text.encode('ascii', 'ignore').decode('ascii')
                        print(f"  Alert {i}: {clean_text[:100]}...")
                    except Exception:
                        print(f"  Alert {i}: [encoding error]")

                # Skip test if field mappings not configured
                field_mapping_alerts = [
                    alert for alert in alert_texts if "Field Mappings Not Configured" in alert
                ]
                if len(field_mapping_alerts) > 0:
                    pytest.skip("Field mappings not configured - test requires field mapping setup")

                # Accept either DevOps mode or Issue Tracker mode
                # Issue Tracker mode is expected when using Apache Kafka JIRA data
                # (which uses resolutiondate/issuetype as proxy fields)
                issue_tracker_alerts = [
                    alert for alert in alert_texts if "Issue Tracker Mode" in alert
                ]
                if len(issue_tracker_alerts) > 0:
                    print(f"Issue Tracker Mode active (using proxy fields): {issue_tracker_alerts[0][:80]}...")
                else:
                    print("DevOps mode active (using custom fields)")

                # Wait for metrics to calculate (show loading then results)
                time.sleep(5)

                # Verify metric cards are displayed
                metric_cards = page.locator(".metric-card-modern").all()
                assert len(metric_cards) >= 4, (
                    f"Should show at least 4 DORA metrics, found {len(metric_cards)}"
                )
                print(f"[X] Found {len(metric_cards)} DORA metric cards")

                # Extract metric values for verification
                print("\n[X][X] DORA Metrics Values:")
                for card in metric_cards:
                    try:
                        # Get metric name (may have alternative name with info icon)
                        name_elem = card.locator(".metric-name").first
                        metric_name = (
                            name_elem.inner_text()
                            if name_elem.count() > 0
                            else "Unknown"
                        )

                        # Get metric value
                        value_elem = card.locator(".metric-value").first
                        metric_value = (
                            value_elem.inner_text() if value_elem.count() > 0 else "N/A"
                        )

                        print(f"  {metric_name}: {metric_value}")
                    except Exception as e:
                        print(f"  [X][X] Could not extract metric: {e}")

                # Test Flow metrics as well
                print("\n[X]� Testing Flow Metrics...")
                flow_tab = page.locator("#dora-flow-tabs .nav-link").filter(
                    has_text="Flow Metrics"
                )
                flow_tab.click()
                time.sleep(3)

                # Calculate Flow metrics
                calculate_flow_button = page.locator("#calculate-flow-metrics")
                calculate_flow_button.click()
                print("[X] Clicked Calculate Flow Metrics button")

                time.sleep(5)

                # Verify Flow metric cards
                flow_cards = page.locator(".metric-card-modern").all()
                assert len(flow_cards) >= 5, (
                    f"Should show at least 5 Flow metrics, found {len(flow_cards)}"
                )
                print(f"[X] Found {len(flow_cards)} Flow metric cards")

                print("\n[X][X] Flow Metrics Values:")
                for card in flow_cards:
                    try:
                        name_elem = card.locator(".metric-name").first
                        metric_name = (
                            name_elem.inner_text()
                            if name_elem.count() > 0
                            else "Unknown"
                        )

                        value_elem = card.locator(".metric-value").first
                        metric_value = (
                            value_elem.inner_text() if value_elem.count() > 0 else "N/A"
                        )

                        print(f"  {metric_name}: {metric_value}")
                    except Exception as e:
                        print(f"  [X][X] Could not extract metric: {e}")

                print("\n[X] All tests passed!")

            except Exception as e:
                print(f"\n[X] Test failed: {e}")
                # Take screenshot for debugging
                page.screenshot(path="test_synthetic_dora_error.png")
                print("[X][X] Screenshot saved to test_synthetic_dora_error.png")
                raise

            finally:
                # Keep browser open for 5 seconds to see results
                time.sleep(5)
                browser.close()


if __name__ == "__main__":
    # Run test manually for debugging
    test = TestSyntheticDoraValidation()
    test.test_dora_metrics_with_synthetic_data("http://127.0.0.1:8050")
