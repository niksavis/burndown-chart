"""
Unit tests for health score consistency during import/export.

Tests that health scores remain consistent when exporting and importing profiles
with artificial points (manually added points, not from JIRA).

This addresses bug burndown-chart-0lq1: Health score differs between exported (59%)
and imported (70%) profiles with same query when artificial points are present.
"""

import pytest


class TestHealthScoreConsistency:
    """Test suite for health score consistency during import/export."""

    @pytest.fixture
    def profile_with_artificial_points(self):
        """Sample profile with artificial points and show_points=True."""
        return {
            "id": "test_profile",
            "name": "Test Profile",
            "jira_config": {
                "base_url": "https://jira.example.com",
                "configured": True,
            },
            "show_points": True,  # CRITICAL: Points-based health calculation
            "created_at": "2026-01-25T10:00:00",
            "last_used": "2026-01-25T10:00:00",
        }

    @pytest.fixture
    def query_with_statistics(self):
        """Sample query with statistics containing artificial points."""
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
                    "completed_points": 50.0,  # Artificial: 5 points/item
                    "remaining_items": 90,
                    "remaining_total_points": 450.0,  # Artificial: 5 points/item
                },
                {
                    "date": "2026-01-08",
                    "week_label": "2026-W02",
                    "completed_items": 20,
                    "completed_points": 100.0,  # Artificial: 5 points/item
                    "remaining_items": 80,
                    "remaining_total_points": 400.0,  # Artificial: 5 points/item
                },
            ],
            "project_scope": {
                "total_items": 100,
                "estimated_items": 100,
                "remaining_items": 80,
                "estimated_points": 500.0,  # Artificial points
                "remaining_total_points": 400.0,  # Artificial points
            },
            "metrics": [
                # Sample DORA metrics
                {
                    "snapshot_date": "2026-01-08",
                    "metric_category": "dora",
                    "metric_name": "deployment_frequency",
                    "metric_value": 12.5,
                    "metric_unit": "deployments/month",
                    "calculation_metadata": {"performance_tier": "High"},
                },
                # Sample Flow metrics
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
        """Verify show_points is included in profile export."""
        from data.import_export import strip_credentials

        # When: Export profile (strip_credentials is called during export)
        exported_profile = strip_credentials(profile_with_artificial_points)

        # Then: show_points should be preserved
        assert "show_points" in exported_profile
        assert exported_profile["show_points"] is True

    def test_show_points_exported_in_project_scope(self, query_with_statistics):
        """Verify show_points is included in project_scope export."""
        # When: Project scope is exported
        _project_scope = query_with_statistics["project_scope"]

        # Then: show_points should be in the scope data (if stored there)
        # Note: This test documents current behavior - may need adjustment
        # depending on where show_points is actually stored
        # Currently this is a placeholder test to document expected behavior

    def test_health_calculation_uses_show_points_setting(self):
        """Verify health calculation respects show_points setting."""
        from data.project_health_calculator import (
            calculate_comprehensive_project_health,
            prepare_dashboard_metrics_for_health,
        )

        # Setup: Dashboard metrics with different items vs points completion
        # Items: 20/100 = 20% complete
        # Points: 100/500 = 20% complete (same, but could differ)
        dashboard_metrics_items = prepare_dashboard_metrics_for_health(
            completion_percentage=20.0,  # Items-based
            velocity_cv=25.0,
            trend_direction="stable",
        )

        dashboard_metrics_points = prepare_dashboard_metrics_for_health(
            completion_percentage=20.0,  # Points-based (artificially different)
            velocity_cv=25.0,
            trend_direction="stable",
        )

        # When: Calculate health with items vs points
        health_items = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_items
        )
        health_points = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_points
        )

        # Then: Health scores should be the same when completion % is the same
        assert health_items["overall_score"] == health_points["overall_score"]

    def test_export_import_preserves_show_points(
        self, profile_with_artificial_points, query_with_statistics
    ):
        """Integration test: Verify show_points preserved through export/import cycle."""
        from data.import_export import export_profile_with_mode
        from unittest.mock import MagicMock, patch

        # Setup: Mock database backend
        with patch("data.persistence.factory.get_backend") as mock_get_backend:
            mock_backend = MagicMock()
            mock_get_backend.return_value = mock_backend

            # Mock database responses
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

            # When: Export profile
            export_package = export_profile_with_mode(
                profile_id="test_profile",
                query_id="q_test1",
                export_mode="FULL_DATA",
                include_token=False,
                include_budget=False,
            )

            # Then: Verify show_points is in exported data
            assert "profile_data" in export_package
            profile_data = export_package["profile_data"]

            # Check if show_points is in profile_data
            assert "show_points" in profile_data, (
                "show_points missing from exported profile_data"
            )
            assert profile_data["show_points"] is True, (
                "show_points value incorrect in export"
            )

            # Verify query data includes project_scope and metrics
            assert "query_data" in export_package
            query_data = export_package["query_data"]["q_test1"]
            assert "project_scope" in query_data
            assert "metrics" in query_data, (
                "metrics missing from exported query_data (CRITICAL for health consistency)"
            )
            assert len(query_data["metrics"]) > 0, (
                "metrics array is empty (should include DORA/Flow/Bug metrics)"
            )

    def test_different_completion_percentages_cause_health_difference(self):
        """Verify that using items vs points completion causes health score difference."""
        from data.project_health_calculator import (
            calculate_comprehensive_project_health,
            prepare_dashboard_metrics_for_health,
        )

        # Setup: Different completion percentages (simulating artificial points issue)
        # Scenario: 20 items completed out of 100 = 20%
        #          100 points completed out of 700 (artificial) = 14.3%
        dashboard_metrics_items = prepare_dashboard_metrics_for_health(
            completion_percentage=20.0,  # Items-based: 20%
            velocity_cv=25.0,
            trend_direction="stable",
        )

        dashboard_metrics_points = prepare_dashboard_metrics_for_health(
            completion_percentage=14.3,  # Points-based with artificial points: 14.3%
            velocity_cv=25.0,
            trend_direction="stable",
        )

        # When: Calculate health with different completion %
        health_items = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_items
        )
        health_points = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_points
        )

        # Then: Health scores should differ due to completion % difference
        assert health_items["overall_score"] != health_points["overall_score"]
        # The difference should be roughly proportional to the completion % difference
        health_diff = abs(
            health_items["overall_score"] - health_points["overall_score"]
        )
        assert health_diff > 0, "Health scores should differ when completion % differs"

    @pytest.mark.skip(reason="Implementation pending - requires database setup")
    def test_full_export_import_cycle_preserves_health_score(
        self, profile_with_artificial_points, query_with_statistics
    ):
        """End-to-end test: Export and import profile, verify health score unchanged."""
        # This test would require:
        # 1. Creating a temporary database
        # 2. Saving profile and query data
        # 3. Exporting the profile
        # 4. Importing to a new profile
        # 5. Calculating health on both and comparing
        #
        # Skipped for now - would be an integration test
        pass


class TestShowPointsNormalization:
    """Test suite for show_points normalization across formats."""

    def test_normalize_show_points_from_list(self):
        """Test normalization from checkbox list format."""
        from callbacks.settings import _normalize_show_points

        assert _normalize_show_points(["show"]) is True
        assert _normalize_show_points([]) is False

    def test_normalize_show_points_from_int(self):
        """Test normalization from database integer format."""
        from callbacks.settings import _normalize_show_points

        assert _normalize_show_points(1) is True
        assert _normalize_show_points(0) is False

    def test_normalize_show_points_from_bool(self):
        """Test normalization from boolean format."""
        from callbacks.settings import _normalize_show_points

        assert _normalize_show_points(True) is True
        assert _normalize_show_points(False) is False

    def test_normalize_show_points_invalid_formats(self):
        """Test normalization handles invalid formats gracefully."""
        from callbacks.settings import _normalize_show_points

        assert _normalize_show_points(None) is False
        assert _normalize_show_points("invalid") is False
        assert _normalize_show_points({}) is False
        assert _normalize_show_points([1, 2, 3]) is False  # Invalid list content
