"""
Integration tests to verify the velocity metrics filtering fix.

This test suite specifically addresses the issue where velocity metrics
were not updating when 10 or more data points were selected.
"""

import pytest
import pandas as pd
from data.processing import calculate_weekly_averages
from visualization.charts import (
    _get_weekly_metrics,
    create_forecast_plot,
    # create_burnup_chart,  # Function doesn't exist in visualization.charts
)


class TestVelocityMetricsFilteringFix:
    """Test that velocity metrics properly use data_points_count filtering."""

    def setup_method(self):
        """Set up test data with enough weeks to test filtering."""
        # Create 20 weeks of test data with proper weekly intervals
        self.test_data = []
        for week in range(20):
            # Use weekly intervals (7 days apart) starting from 2024-01-01
            date_str = (pd.Timestamp("2024-01-01") + pd.Timedelta(weeks=week)).strftime(
                "%Y-%m-%d"
            )
            # Create pattern where older weeks have different values than recent weeks
            if week < 10:
                # Older weeks (0-9): lower values
                items = 3 + (week % 2)  # Varies between 3-4
                points = 15 + (week % 3) * 2  # Varies between 15-19
            else:
                # Recent weeks (10-19): higher values
                items = 7 + (week % 2)  # Varies between 7-8
                points = 25 + (week % 3) * 2  # Varies between 25-29

            self.test_data.append(
                {
                    "date": date_str,
                    "completed_items": items,
                    "completed_points": points,
                    "created_items": 1,
                    "created_points": 5,
                }
            )

        self.df = pd.DataFrame(self.test_data)
        self.statistics_list = self.test_data

    def test_calculate_weekly_averages_uses_filtering(self):
        """Test that calculate_weekly_averages properly applies data_points_count filtering."""
        # Calculate averages with legacy behavior (None = last 10 weeks)
        avg_items_legacy, avg_points_legacy, med_items_legacy, med_points_legacy = (
            calculate_weekly_averages(self.statistics_list)
        )

        # Calculate averages with all 20 weeks specified explicitly
        (
            avg_items_all,
            avg_points_all,
            med_items_all,
            med_points_all,
        ) = calculate_weekly_averages(self.statistics_list, data_points_count=20)

        # They should be different because legacy uses 10 weeks, explicit uses all 20
        assert avg_items_legacy != avg_items_all, (
            "Legacy (10-week) should differ from explicit all-data filtering"
        )

        # Calculate averages with only last 10 weeks explicitly
        (
            avg_items_10,
            avg_points_10,
            med_items_10,
            med_points_10,
        ) = calculate_weekly_averages(self.statistics_list, data_points_count=10)

        # Legacy behavior and explicit 10-week should be the same
        assert abs(avg_items_legacy - avg_items_10) < 0.01, (
            f"Legacy and explicit 10-week should match: {avg_items_legacy} vs {avg_items_10}"
        )

        # Verify the all-data calculation includes older weeks with lower values
        # Expected: (10 weeks * 3.5 avg + 10 weeks * 7.5 avg) / 20 = 5.5
        expected_all_avg_items = 5.5
        assert abs(avg_items_all - expected_all_avg_items) < 0.1, (
            f"All-data average should be ~5.5, got {avg_items_all}"
        )

    def test_get_weekly_metrics_uses_filtering(self):
        """Test that _get_weekly_metrics helper function uses data_points_count."""
        # Test with legacy behavior (None = last 10 weeks)
        avg_items_legacy, avg_points_legacy, med_items_legacy, med_points_legacy = (
            _get_weekly_metrics(self.df)
        )

        # Test with all data explicitly
        (
            avg_items_all,
            avg_points_all,
            med_items_all,
            med_points_all,
        ) = _get_weekly_metrics(self.df, data_points_count=20)

        # Results should be different when using all data vs legacy 10-week limit
        assert avg_items_legacy != avg_items_all, (
            "Legacy 10-week should differ from explicit all-data"
        )
        assert avg_points_legacy != avg_points_all, (
            "Legacy 10-week should differ from explicit all-data"
        )

    def test_create_forecast_plot_uses_filtering_for_velocity(self):
        """Test that create_forecast_plot uses filtered data for velocity calculations."""
        # Create a cumulative DataFrame for the forecast plot
        df_cumulative = self.df.copy()
        df_cumulative["completed_items_cumulative"] = df_cumulative[
            "completed_items"
        ].cumsum()
        df_cumulative["completed_points_cumulative"] = df_cumulative[
            "completed_points"
        ].cumsum()
        df_cumulative["created_items_cumulative"] = df_cumulative[
            "created_items"
        ].cumsum()
        df_cumulative["created_points_cumulative"] = df_cumulative[
            "created_points"
        ].cumsum()

        # Test with different data_points_count values
        fig_all, pert_data_all = create_forecast_plot(
            df=df_cumulative,
            total_items=100,
            total_points=400,
            pert_factor=3,
            deadline_str="2024-12-31",
            data_points_count=None,  # Use all data
        )

        fig_filtered, pert_data_filtered = create_forecast_plot(
            df=df_cumulative,
            total_items=100,
            total_points=400,
            pert_factor=3,
            deadline_str="2024-12-31",
            data_points_count=10,  # Use only last 10 weeks
        )

        # The PERT data should be different when using filtered data
        assert pert_data_all != pert_data_filtered, (
            "PERT calculations should differ when filtering is applied"
        )

    @pytest.mark.skip(
        reason="create_burnup_chart function does not exist in visualization.charts"
    )
    def test_create_burnup_chart_uses_filtering_for_velocity(self):
        """Test that create_burnup_chart uses filtered data for velocity calculations."""
        # Test with different data_points_count values
        # Note: This function doesn't exist - test needs to be updated or removed
        pass

    def test_velocity_metrics_change_with_10_plus_data_points(self):
        """Test the specific scenario: velocity metrics should change when 10+ data points are selected."""
        # This directly tests the reported issue

        # Calculate metrics with all 20 weeks (explicit)
        metrics_20_weeks = _get_weekly_metrics(self.df, data_points_count=20)

        # Calculate metrics with 12 weeks
        metrics_12_weeks = _get_weekly_metrics(self.df, data_points_count=12)

        # Calculate metrics with 10 weeks
        metrics_10_weeks = _get_weekly_metrics(self.df, data_points_count=10)

        # Calculate metrics with 8 weeks
        metrics_8_weeks = _get_weekly_metrics(self.df, data_points_count=8)

        # All should be different from each other
        assert metrics_20_weeks != metrics_12_weeks, (
            "20 weeks vs 12 weeks should be different"
        )
        assert metrics_12_weeks != metrics_10_weeks, (
            "12 weeks vs 10 weeks should be different"
        )
        assert metrics_10_weeks != metrics_8_weeks, (
            "10 weeks vs 8 weeks should be different"
        )

        # Specifically test that 10+ weeks filtering works
        assert metrics_20_weeks[0] != metrics_10_weeks[0], (
            "Average items should change with all data vs 10 week filtering"
        )
        assert metrics_20_weeks[1] != metrics_10_weeks[1], (
            "Average points should change with all data vs 10 week filtering"
        )

    def test_progressive_filtering_consistency(self):
        """Test that progressive filtering (20 -> 15 -> 12 -> 10 -> 8 weeks) shows consistent changes."""
        data_points_counts = [
            20,
            15,
            12,
            10,
            8,
            5,
        ]  # Include explicit 20-week (all data)
        results = []

        for count in data_points_counts:
            avg_items, avg_points, med_items, med_points = _get_weekly_metrics(
                self.df, data_points_count=count
            )
            results.append((avg_items, avg_points, med_items, med_points))

        # Each result should be different as we filter more aggressively
        unique_results = set(results)
        assert len(unique_results) >= 4, (
            f"Expected at least 4 different results, got {len(unique_results)}"
        )

        # Specifically check that 10-week filtering produces different results than all-data
        all_data_result = results[0]  # 20 weeks (all data)
        ten_week_result = results[3]  # 10 weeks

        assert all_data_result != ten_week_result, (
            "10-week filtering should produce different results than all data"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
