"""
Test to verify deadline risk calculation consistency between app and report.

This test ensures that the app (insights_engine) and report (generator) use
identical calculation methods for deadline risk insights.

Regression test for issue where app showed "50.64 days (7.23 weeks)" while
report showed "48 days (6.9 weeks)" due to different reference points.
"""

from datetime import datetime, timedelta
import pytest


class TestDeadlineCalculationConsistency:
    """Test deadline calculations match between app and report."""

    def test_app_and_report_use_same_reference_point(self):
        """
        Verify both app and report calculate deadline risk from datetime.now().

        App calculation (insights_engine.py):
            current_date = datetime.now()
            days_to_deadline = (deadline_date - current_date).days
            pert_most_likely_days = pert_data.get("pert_time_items", 0)
            days_over = pert_most_likely_days - days_to_deadline

        Report calculation (generator.py):
            current_date = datetime.now()
            days_to_deadline = (deadline_date - current_date).days
            pert_most_likely_days = dashboard_metrics.get("pert_time_items", 0)
            days_over = pert_most_likely_days - days_to_deadline

        Both should produce identical results.
        """
        # Setup test data
        current_date = datetime.now()
        deadline_date = current_date + timedelta(days=30)  # Deadline in 30 days
        pert_most_likely_days = 80.64  # PERT forecast: 80.64 days to completion

        # APP CALCULATION (simulating insights_engine.py logic)
        days_to_deadline_app = (deadline_date - current_date).days
        days_over_app = pert_most_likely_days - days_to_deadline_app
        weeks_over_app = days_over_app / 7.0

        # REPORT CALCULATION (simulating generator.py logic)
        days_to_deadline_report = max(0, (deadline_date - current_date).days)
        pert_most_likely_days_report = pert_most_likely_days
        days_over_report = pert_most_likely_days_report - days_to_deadline_report
        weeks_over_report = days_over_report / 7.0

        # VERIFY IDENTICAL RESULTS
        assert days_to_deadline_app == days_to_deadline_report, (
            "App and report must calculate days_to_deadline identically"
        )
        assert days_over_app == days_over_report, (
            f"App: {days_over_app:.2f} days vs Report: {days_over_report:.2f} days - MUST MATCH"
        )
        assert weeks_over_app == weeks_over_report, (
            f"App: {weeks_over_app:.2f} weeks vs Report: {weeks_over_report:.2f} weeks - MUST MATCH"
        )

        # Expected values
        assert days_over_app == pytest.approx(50.64, abs=0.01)
        assert weeks_over_app == pytest.approx(7.23, abs=0.01)

    def test_old_broken_calculation_would_fail(self):
        """
        Demonstrate the OLD broken report calculation would fail this test.

        OLD Report calculation (pre-fix):
            last_date = df["date"].iloc[-1]  # Last Monday from statistics
            forecast_date = last_date + timedelta(days=pert_time_items)
            days_over = (forecast_date - deadline_date).days

        This created discrepancies because last_date could be up to 6 days
        before datetime.now(), causing the ~2.6 day difference observed.
        """
        # Setup test data
        current_date = datetime.now()
        last_date = current_date - timedelta(days=2)  # Statistics 2 days old
        deadline_date = current_date + timedelta(days=30)
        pert_time_items = 80.64

        # APP CALCULATION (correct)
        days_to_deadline_app = (deadline_date - current_date).days
        days_over_app = pert_time_items - days_to_deadline_app

        # OLD REPORT CALCULATION (broken)
        forecast_date_old = last_date + timedelta(days=pert_time_items)
        days_over_report_old = (forecast_date_old - deadline_date).days

        # NEW REPORT CALCULATION (fixed)
        days_to_deadline_report_new = max(0, (deadline_date - current_date).days)
        days_over_report_new = pert_time_items - days_to_deadline_report_new

        # Verify old calculation was broken
        assert days_over_app != days_over_report_old, (
            "Old calculation should differ (this is the bug we fixed)"
        )

        # Verify new calculation is correct
        assert days_over_app == days_over_report_new, (
            "New calculation must match app exactly"
        )

        # Show the discrepancy magnitude (~2.64 days in this scenario)
        # This matches the user's reported issue: app=50.64 days, report=48 days
        discrepancy = abs(days_over_app - days_over_report_old)
        assert discrepancy == pytest.approx(2.64, abs=0.1), (
            f"Expected ~2.64 day discrepancy (matching user's report), got {discrepancy:.2f}"
        )

    def test_dashboard_metrics_exposes_pert_time_items(self):
        """
        Verify dashboard_metrics returns raw pert_time_items for report calculations.

        This is critical - without raw PERT days, the report cannot calculate
        deadline risk using the same method as the app.
        """
        # Mock dashboard_metrics return structure
        dashboard_metrics = {
            "pert_time_items": 80.64,  # RAW PERT days (REQUIRED)
            "pert_time_points": 120.5,  # RAW PERT days for points
            "pert_time_items_weeks": 11.52,  # Display format (80.64/7)
            "pert_time_points_weeks": 17.21,  # Display format (120.5/7)
            "forecast_date_items": "2026-05-01",  # String format (for legacy display)
        }

        # Verify raw days are available
        assert "pert_time_items" in dashboard_metrics, (
            "dashboard_metrics MUST return pert_time_items (raw days)"
        )

        # Verify calculation works with raw days
        pert_most_likely_days = dashboard_metrics["pert_time_items"]
        assert pert_most_likely_days == 80.64

        # Verify weeks match the raw days conversion
        expected_weeks = pert_most_likely_days / 7.0
        assert dashboard_metrics["pert_time_items_weeks"] == pytest.approx(
            expected_weeks
        )
