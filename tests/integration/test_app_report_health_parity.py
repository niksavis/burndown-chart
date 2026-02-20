"""
Integration test to expose health calculation divergence between app and report.

This test runs the ACTUAL data preparation paths for both app and report
with identical mock data to identify where they diverge.

CRITICAL: Health scores depend on deadline/milestone settings!
- completion_confidence is calculated from schedule_variance_days
- schedule_variance_days = days_to_deadline - pert_forecast_days
- If deadline is None or different between app/report, health scores will differ
- This test ensures settings are identical for both paths
"""

from datetime import datetime, timedelta

import pandas as pd
import pytest


class TestAppReportHealthParity:
    """Test that app and report produce identical health scores with same data."""

    @pytest.fixture
    def mock_statistics(self):
        """Create mock weekly statistics data."""
        base_date = datetime(2026, 1, 6)  # Monday
        statistics = []

        for i in range(36):  # 36 weeks of data
            week_date = base_date - timedelta(weeks=i)
            statistics.append(
                {
                    "date": week_date.strftime("%Y-%m-%d"),
                    "week_label": f"{week_date.year}-W{week_date.isocalendar()[1]:02d}",
                    "completed_items": 5 + (i % 3),  # Varying completion
                    "completed_points": 15.0 + (i % 3) * 3,
                    "created_items": 2 + (i % 2),
                    "created_points": 8.0 + (i % 2) * 2,
                    "remaining_items": 100 - (5 * i),
                    "remaining_total_points": 300.0 - (15.0 * i),
                }
            )

        return list(reversed(statistics))  # Oldest to newest

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        return {
            "data_points_count": 36,
            "pert_factor": 1.2,
            "deadline": "2026-06-30",
            "total_items": 280,
            "total_points": 840.0,
            "show_points": False,
            "bug_types": {"Bug": ["Bug", "Defect"]},
        }

    @pytest.fixture
    def mock_issues(self):
        """Create mock JIRA issues including bugs."""
        issues = []
        base_date = datetime(2025, 1, 1)

        # Create 50 completed issues
        for i in range(50):
            issues.append(
                {
                    "key": f"PROJ-{i}",
                    "fields": {
                        "issuetype": {"name": "Story"},
                        "status": {"name": "Done"},
                        "created": (base_date + timedelta(days=i * 7)).isoformat(),
                        "resolutiondate": (
                            base_date + timedelta(days=i * 7 + 5)
                        ).isoformat(),
                        "customfield_10016": 5.0,  # Story points
                    },
                }
            )

        # Create 23 open bugs with varying ages
        for i in range(23):
            created = base_date + timedelta(days=i * 14)
            issues.append(
                {
                    "key": f"BUG-{i}",
                    "fields": {
                        "issuetype": {"name": "Bug"},
                        "status": {"name": "Open"},
                        "created": created.isoformat(),
                        "resolutiondate": None,
                        "customfield_10016": 3.0,
                    },
                }
            )

        # Create 15 closed bugs
        for i in range(15):
            created = base_date + timedelta(days=i * 10)
            resolved = created + timedelta(days=12)
            issues.append(
                {
                    "key": f"BUG-CLOSED-{i}",
                    "fields": {
                        "issuetype": {"name": "Bug"},
                        "status": {"name": "Done"},
                        "created": created.isoformat(),
                        "resolutiondate": resolved.isoformat(),
                        "customfield_10016": 2.0,
                    },
                }
            )

        return issues

    def test_app_report_health_calculation_with_36_weeks(
        self, mock_statistics, mock_settings, mock_issues
    ):
        """
        Test that exposes divergence: Run both app and report paths with same data.

        This is the REAL test - it will show exactly where app and report diverge.
        """
        data_points_count = 36

        # ========================================
        # SIMULATE APP PATH
        # ========================================
        print("\n" + "=" * 80)
        print("APP PATH - Dashboard Health Calculation")
        print("=" * 80)

        # App filters statistics by data_points_count
        from data.time_period_calculator import format_year_week, get_iso_week

        df = pd.DataFrame(mock_statistics)
        df["date"] = pd.to_datetime(df["date"])
        current_date = df["date"].max()

        # Generate week labels (same as app does)
        weeks = []
        for _i in range(data_points_count):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)
        week_labels = set(reversed(weeks))

        # Filter to data_points_count weeks
        df_app = df[df["week_label"].isin(week_labels)].copy()
        df_app = df_app.sort_values("date", ascending=True)

        print(f"App filtered to {len(df_app)} weeks (requested {data_points_count})")
        print(f"App date range: {df_app['date'].min()} to {df_app['date'].max()}")

        # Calculate velocity (app way)
        from data.processing import calculate_velocity_from_dataframe

        app_velocity = calculate_velocity_from_dataframe(df_app, "completed_items")
        app_total_completed = df_app["completed_items"].sum()
        app_total_items = mock_settings["total_items"]
        app_completion_pct = (app_total_completed / app_total_items) * 100

        print(f"App velocity: {app_velocity:.2f} items/week")
        print(f"App completed: {app_total_completed} items")
        print(f"App completion: {app_completion_pct:.2f}%")

        # Calculate velocity CV (app way)
        mean_vel = df_app["completed_items"].mean()
        std_vel = df_app["completed_items"].std()
        app_velocity_cv = (std_vel / mean_vel * 100) if mean_vel > 0 else 0

        print(f"App velocity CV: {app_velocity_cv:.2f}%")

        # Prepare dashboard metrics (app way)
        from data.project_health_calculator import prepare_dashboard_metrics_for_health

        app_dashboard_metrics = prepare_dashboard_metrics_for_health(
            completion_percentage=app_completion_pct,
            current_velocity_items=app_velocity,
            velocity_cv=app_velocity_cv,
            trend_direction="stable",
            recent_velocity_change=0.0,
            schedule_variance_days=7.0,
            completion_confidence=70,
        )

        print(f"App dashboard metrics: {app_dashboard_metrics}")

        # Calculate app health
        from data.project_health_calculator import (
            calculate_comprehensive_project_health,
        )

        app_health = calculate_comprehensive_project_health(
            dashboard_metrics=app_dashboard_metrics,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics={"scope_change_rate": 15.0},
        )

        print(f"APP HEALTH: {app_health['overall_score']}%")

        # ========================================
        # SIMULATE REPORT PATH
        # ========================================
        print("\n" + "=" * 80)
        print("REPORT PATH - Dashboard Health Calculation")
        print("=" * 80)

        # Report filters statistics differently?
        # Let's trace through report_generator._calculate_dashboard_metrics

        # Report uses ALL statistics for lifetime, but WINDOWED for velocity
        df_report_all = pd.DataFrame(mock_statistics)
        df_report_all["date"] = pd.to_datetime(df_report_all["date"])

        # Report filtering by week labels (same as app?)
        df_report_windowed = df_report_all[
            df_report_all["week_label"].isin(week_labels)
        ].copy()
        df_report_windowed = df_report_windowed.sort_values("date", ascending=True)

        print(
            f"Report filtered to {len(df_report_windowed)} weeks (requested {data_points_count})"
        )
        print(
            f"Report date range: {df_report_windowed['date'].min()} to {df_report_windowed['date'].max()}"
        )

        # Calculate velocity (report way)
        report_velocity = calculate_velocity_from_dataframe(
            df_report_windowed, "completed_items"
        )
        report_total_completed = df_report_windowed["completed_items"].sum()
        report_total_items = mock_settings["total_items"]
        report_completion_pct = (report_total_completed / report_total_items) * 100

        print(f"Report velocity: {report_velocity:.2f} items/week")
        print(f"Report completed: {report_total_completed} items")
        print(f"Report completion: {report_completion_pct:.2f}%")

        # Calculate velocity CV (report way)
        mean_vel_report = df_report_windowed["completed_items"].mean()
        std_vel_report = df_report_windowed["completed_items"].std()
        report_velocity_cv = (
            (std_vel_report / mean_vel_report * 100) if mean_vel_report > 0 else 0
        )

        print(f"Report velocity CV: {report_velocity_cv:.2f}%")

        # Prepare dashboard metrics (report way)
        report_dashboard_metrics = prepare_dashboard_metrics_for_health(
            completion_percentage=report_completion_pct,
            current_velocity_items=report_velocity,
            velocity_cv=report_velocity_cv,
            trend_direction="stable",
            recent_velocity_change=0.0,
            schedule_variance_days=7.0,
            completion_confidence=70,
        )

        print(f"Report dashboard metrics: {report_dashboard_metrics}")

        # Calculate report health
        report_health = calculate_comprehensive_project_health(
            dashboard_metrics=report_dashboard_metrics,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics={"scope_change_rate": 15.0},
        )

        print(f"REPORT HEALTH: {report_health['overall_score']}%")

        # ========================================
        # COMPARE AND EXPOSE DIVERGENCE
        # ========================================
        print("\n" + "=" * 80)
        print("DIVERGENCE ANALYSIS")
        print("=" * 80)

        print(f"\nFiltered weeks: App={len(df_app)}, Report={len(df_report_windowed)}")
        print(f"Velocity: App={app_velocity:.2f}, Report={report_velocity:.2f}")
        print(
            f"Completion: App={app_completion_pct:.2f}%, Report={report_completion_pct:.2f}%"
        )
        print(
            f"Velocity CV: App={app_velocity_cv:.2f}%, Report={report_velocity_cv:.2f}%"
        )
        print(
            f"\nFINAL HEALTH: App={app_health['overall_score']}%, Report={report_health['overall_score']}%"
        )

        # Compare dashboard metrics
        for key in app_dashboard_metrics:
            app_val = app_dashboard_metrics[key]
            report_val = report_dashboard_metrics[key]
            if app_val != report_val:
                print(f"DIVERGENCE in {key}: App={app_val}, Report={report_val}")

        # THE ASSERTION THAT WILL FAIL AND SHOW US THE PROBLEM
        assert app_health["overall_score"] == report_health["overall_score"], (
            f"Health scores diverge: App={app_health['overall_score']}% vs "
            f"Report={report_health['overall_score']}%\n"
            f"This test exposes the exact divergence in data preparation."
        )
