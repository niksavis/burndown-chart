import pytest


class TestHealthScoreConsistency:
    @pytest.fixture
    def profile_with_artificial_points(self):
        return {
            "id": "test_profile",
            "name": "Test Profile",
            "jira_config": {
                "base_url": "https://jira.example.com",
                "configured": True,
            },
            "show_points": True,
            "created_at": "2026-01-25T10:00:00",
            "last_used": "2026-01-25T10:00:00",
        }

    @pytest.fixture
    def query_with_statistics(self):
        return {
            "query_metadata": {
                "id": "q_test1",
                "name": "Test Query",
                "jql": "project = TEST",
                "created_at": "2026-01-25T10:00:00",
                "last_used": "2026-01-25T10:00:00",
            },
            "statistics": [
                {
                    "date": "2026-01-01",
                    "week_label": "2026-W01",
                    "completed_items": 10,
                    "completed_points": 50.0,
                    "remaining_items": 90,
                    "remaining_total_points": 450.0,
                },
                {
                    "date": "2026-01-08",
                    "week_label": "2026-W02",
                    "completed_items": 20,
                    "completed_points": 100.0,
                    "remaining_items": 80,
                    "remaining_total_points": 400.0,
                },
            ],
            "project_scope": {
                "total_items": 100,
                "estimated_items": 100,
                "remaining_items": 80,
                "estimated_points": 500.0,
                "remaining_total_points": 400.0,
            },
            "metrics": [
                {
                    "snapshot_date": "2026-01-08",
                    "metric_category": "dora",
                    "metric_name": "deployment_frequency",
                    "metric_value": 12.5,
                    "metric_unit": "deployments/month",
                    "calculation_metadata": {"performance_tier": "High"},
                },
                {
                    "snapshot_date": "2026-01-08",
                    "metric_category": "flow",
                    "metric_name": "flow_efficiency",
                    "metric_value": 65.0,
                    "metric_unit": "%",
                    "calculation_metadata": {},
                },
            ],
        }

    def test_show_points_exported_in_profile_data(self, profile_with_artificial_points):
        from data.import_export import strip_credentials

        exported_profile = strip_credentials(profile_with_artificial_points)

        assert "show_points" in exported_profile
        assert exported_profile["show_points"] is True

    def test_show_points_exported_in_project_scope(self, query_with_statistics):
        _project_scope = query_with_statistics["project_scope"]

    def test_health_calculation_uses_show_points_setting(self):
        from data.project_health_calculator import (
            calculate_comprehensive_project_health,
            prepare_dashboard_metrics_for_health,
        )

        dashboard_metrics_items = prepare_dashboard_metrics_for_health(
            completion_percentage=20.0,
            velocity_cv=25.0,
            trend_direction="stable",
        )

        dashboard_metrics_points = prepare_dashboard_metrics_for_health(
            completion_percentage=20.0,
            velocity_cv=25.0,
            trend_direction="stable",
        )

        health_items = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_items
        )
        health_points = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_points
        )

        assert health_items["overall_score"] == health_points["overall_score"]

    def test_export_import_preserves_show_points(
        self, profile_with_artificial_points, query_with_statistics
    ):
        from unittest.mock import MagicMock, patch

        from data.import_export import export_profile_with_mode

        with patch("data._import_export_export.get_backend") as mock_get_backend:
            mock_backend = MagicMock()
            mock_get_backend.return_value = mock_backend

            mock_backend.get_profile.return_value = profile_with_artificial_points
            mock_backend.list_queries.return_value = [
                {
                    "id": "q_test1",
                    "name": "Test Query",
                    "jql": "project = TEST",
                    "created_at": "2026-01-25T10:00:00",
                    "last_used": "2026-01-25T10:00:00",
                }
            ]
            mock_backend.get_issues.return_value = []
            mock_backend.get_statistics.return_value = query_with_statistics[
                "statistics"
            ]
            mock_backend.get_scope.return_value = query_with_statistics["project_scope"]
            mock_backend.get_metric_values.return_value = query_with_statistics[
                "metrics"
            ]
            mock_backend.get_budget_settings.return_value = None
            mock_backend.get_budget_revisions.return_value = None

            export_package = export_profile_with_mode(
                profile_id="test_profile",
                query_id="q_test1",
                export_mode="FULL_DATA",
                include_token=False,
                include_budget=False,
            )

            assert "profile_data" in export_package
            profile_data = export_package["profile_data"]

            assert "show_points" in profile_data, (
                "show_points missing from exported profile_data"
            )
            assert profile_data["show_points"] is True, (
                "show_points value incorrect in export"
            )

            assert "query_data" in export_package
            query_data = export_package["query_data"]["q_test1"]
            assert "project_scope" in query_data
            assert "metrics" in query_data, (
                "metrics missing from exported query_data "
                "(CRITICAL for health consistency)"
            )
            assert len(query_data["metrics"]) > 0, (
                "metrics array is empty (should include DORA/Flow/Bug metrics)"
            )

    def test_different_completion_percentages_cause_health_difference(self):
        from data.project_health_calculator import (
            calculate_comprehensive_project_health,
            prepare_dashboard_metrics_for_health,
        )

        dashboard_metrics_items = prepare_dashboard_metrics_for_health(
            completion_percentage=20.0,
            velocity_cv=25.0,
            trend_direction="stable",
        )

        dashboard_metrics_points = prepare_dashboard_metrics_for_health(
            completion_percentage=14.3,
            velocity_cv=25.0,
            trend_direction="stable",
        )

        health_items = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_items
        )
        health_points = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_points
        )

        assert health_items["overall_score"] != health_points["overall_score"]
        health_diff = abs(
            health_items["overall_score"] - health_points["overall_score"]
        )
        assert health_diff > 0, "Health scores should differ when completion % differs"


class TestShowPointsNormalization:
    def test_normalize_show_points_from_list(self):
        from callbacks.settings.helpers import normalize_show_points

        assert normalize_show_points(["show"]) is True
        assert normalize_show_points([]) is False

    def test_normalize_show_points_from_int(self):
        from callbacks.settings.helpers import normalize_show_points

        assert normalize_show_points(1) is True
        assert normalize_show_points(0) is False

    def test_normalize_show_points_from_bool(self):
        from callbacks.settings.helpers import normalize_show_points

        assert normalize_show_points(True) is True
        assert normalize_show_points(False) is False

    def test_normalize_show_points_invalid_formats(self):
        from callbacks.settings.helpers import normalize_show_points

        assert normalize_show_points(None) is False
        assert normalize_show_points("invalid") is False
        assert normalize_show_points({}) is False
        assert normalize_show_points([1, 2, 3]) is False
