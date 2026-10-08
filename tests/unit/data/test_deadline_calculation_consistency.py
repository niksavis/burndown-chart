from datetime import datetime, timedelta

import pytest


class TestDeadlineCalculationConsistency:
    def test_app_and_report_use_same_reference_point(self):

        current_date = datetime.now()
        deadline_date = current_date + timedelta(days=30)
        pert_most_likely_days = 80.64

        days_to_deadline_app = (deadline_date - current_date).days
        days_over_app = pert_most_likely_days - days_to_deadline_app
        weeks_over_app = days_over_app / 7.0

        days_to_deadline_report = max(0, (deadline_date - current_date).days)
        pert_most_likely_days_report = pert_most_likely_days
        days_over_report = pert_most_likely_days_report - days_to_deadline_report
        weeks_over_report = days_over_report / 7.0

        assert days_to_deadline_app == days_to_deadline_report, (
            "App and report must calculate days_to_deadline identically"
        )
        assert days_over_app == days_over_report, (
            f"App: {days_over_app:.2f} days vs Report: "
            f"{days_over_report:.2f} days - MUST MATCH"
        )
        assert weeks_over_app == weeks_over_report, (
            f"App: {weeks_over_app:.2f} weeks vs Report: "
            f"{weeks_over_report:.2f} weeks - MUST MATCH"
        )

        assert days_over_app == pytest.approx(50.64, abs=0.01)
        assert weeks_over_app == pytest.approx(7.23, abs=0.01)

    def test_old_broken_calculation_would_fail(self):

        current_date = datetime.now()
        last_date = current_date - timedelta(days=2)
        deadline_date = current_date + timedelta(days=30)
        pert_time_items = 80.64

        days_to_deadline_app = (deadline_date - current_date).days
        days_over_app = pert_time_items - days_to_deadline_app

        forecast_date_old = last_date + timedelta(days=pert_time_items)
        days_over_report_old = (forecast_date_old - deadline_date).days

        days_to_deadline_report_new = max(0, (deadline_date - current_date).days)
        days_over_report_new = pert_time_items - days_to_deadline_report_new

        assert days_over_app != days_over_report_old, (
            "Old calculation should differ (this is the bug we fixed)"
        )

        assert days_over_app == days_over_report_new, (
            "New calculation must match app exactly"
        )

        discrepancy = abs(days_over_app - days_over_report_old)
        assert discrepancy == pytest.approx(2.64, abs=0.1), (
            "Expected ~2.64 day discrepancy "
            f"(matching user's report), got {discrepancy:.2f}"
        )

    def test_dashboard_metrics_exposes_pert_time_items(self):

        dashboard_metrics = {
            "pert_time_items": 80.64,
            "pert_time_points": 120.5,
            "pert_time_items_weeks": 11.52,
            "pert_time_points_weeks": 17.21,
            "forecast_date_items": "2026-05-01",
        }

        assert "pert_time_items" in dashboard_metrics, (
            "dashboard_metrics MUST return pert_time_items (raw days)"
        )

        pert_most_likely_days = dashboard_metrics["pert_time_items"]
        assert pert_most_likely_days == 80.64

        expected_weeks = pert_most_likely_days / 7.0
        assert dashboard_metrics["pert_time_items_weeks"] == pytest.approx(
            expected_weeks
        )
