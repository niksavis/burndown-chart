from datetime import datetime, timedelta

import pandas as pd
import pytest


class TestAppReportHealthParity:
    @pytest.fixture
    def mock_statistics(self):
        base_date = datetime(2026, 1, 6)
        statistics = []

        for i in range(36):
            week_date = base_date - timedelta(weeks=i)
            statistics.append(
                {
                    "date": week_date.strftime("%Y-%m-%d"),
                    "week_label": f"{week_date.year}-W{week_date.isocalendar()[1]:02d}",
                    "completed_items": 5 + (i % 3),
                    "completed_points": 15.0 + (i % 3) * 3,
                    "created_items": 2 + (i % 2),
                    "created_points": 8.0 + (i % 2) * 2,
                    "remaining_items": 100 - (5 * i),
                    "remaining_total_points": 300.0 - (15.0 * i),
                }
            )

        return list(reversed(statistics))

    @pytest.fixture
    def mock_settings(self):
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
        issues = []
        base_date = datetime(2025, 1, 1)

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
                        "customfield_10016": 5.0,
                    },
                }
            )

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

        data_points_count = 36

        print("\n" + "=" * 80)
        print("APP PATH - Dashboard Health Calculation")
        print("=" * 80)

        from data.time_period_calculator import format_year_week, get_iso_week

        df = pd.DataFrame(mock_statistics)
        df["date"] = pd.to_datetime(df["date"])
        current_date = df["date"].max()

        weeks = []
        for _i in range(data_points_count):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)
        week_labels = set(reversed(weeks))

        df_app = df[df["week_label"].isin(week_labels)].copy()
        df_app = df_app.sort_values("date", ascending=True)

        print(f"App filtered to {len(df_app)} weeks (requested {data_points_count})")
        print(f"App date range: {df_app['date'].min()} to {df_app['date'].max()}")

        from data.processing import calculate_velocity_from_dataframe

        app_velocity = calculate_velocity_from_dataframe(df_app, "completed_items")
        app_total_completed = df_app["completed_items"].sum()
        app_total_items = mock_settings["total_items"]
        app_completion_pct = (app_total_completed / app_total_items) * 100

        print(f"App velocity: {app_velocity:.2f} items/week")
        print(f"App completed: {app_total_completed} items")
        print(f"App completion: {app_completion_pct:.2f}%")

        mean_vel = df_app["completed_items"].mean()
        std_vel = df_app["completed_items"].std()
        app_velocity_cv = (std_vel / mean_vel * 100) if mean_vel > 0 else 0

        print(f"App velocity CV: {app_velocity_cv:.2f}%")

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

        print("\n" + "=" * 80)
        print("REPORT PATH - Dashboard Health Calculation")
        print("=" * 80)

        df_report_all = pd.DataFrame(mock_statistics)
        df_report_all["date"] = pd.to_datetime(df_report_all["date"])

        df_report_windowed = df_report_all[
            df_report_all["week_label"].isin(week_labels)
        ].copy()
        df_report_windowed = df_report_windowed.sort_values("date", ascending=True)

        print(
            "Report filtered to "
            f"{len(df_report_windowed)} weeks "
            f"(requested {data_points_count})"
        )
        print(
            "Report date range: "
            f"{df_report_windowed['date'].min()} "
            f"to {df_report_windowed['date'].max()}"
        )

        report_velocity = calculate_velocity_from_dataframe(
            df_report_windowed, "completed_items"
        )
        report_total_completed = df_report_windowed["completed_items"].sum()
        report_total_items = mock_settings["total_items"]
        report_completion_pct = (report_total_completed / report_total_items) * 100

        print(f"Report velocity: {report_velocity:.2f} items/week")
        print(f"Report completed: {report_total_completed} items")
        print(f"Report completion: {report_completion_pct:.2f}%")

        mean_vel_report = df_report_windowed["completed_items"].mean()
        std_vel_report = df_report_windowed["completed_items"].std()
        report_velocity_cv = (
            (std_vel_report / mean_vel_report * 100) if mean_vel_report > 0 else 0
        )

        print(f"Report velocity CV: {report_velocity_cv:.2f}%")

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

        report_health = calculate_comprehensive_project_health(
            dashboard_metrics=report_dashboard_metrics,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics={"scope_change_rate": 15.0},
        )

        print(f"REPORT HEALTH: {report_health['overall_score']}%")

        print("\n" + "=" * 80)
        print("DIVERGENCE ANALYSIS")
        print("=" * 80)

        print(f"\nFiltered weeks: App={len(df_app)}, Report={len(df_report_windowed)}")
        print(f"Velocity: App={app_velocity:.2f}, Report={report_velocity:.2f}")
        print(
            "Completion: "
            f"App={app_completion_pct:.2f}%, "
            f"Report={report_completion_pct:.2f}%"
        )
        print(
            f"Velocity CV: App={app_velocity_cv:.2f}%, Report={report_velocity_cv:.2f}%"
        )
        print(
            "\nFINAL HEALTH: "
            f"App={app_health['overall_score']}%, "
            f"Report={report_health['overall_score']}%"
        )

        for key in app_dashboard_metrics:
            app_val = app_dashboard_metrics[key]
            report_val = report_dashboard_metrics[key]
            if app_val != report_val:
                print(f"DIVERGENCE in {key}: App={app_val}, Report={report_val}")

        assert app_health["overall_score"] == report_health["overall_score"], (
            f"Health scores diverge: App={app_health['overall_score']}% vs "
            f"Report={report_health['overall_score']}%\n"
            f"This test exposes the exact divergence in data preparation."
        )
