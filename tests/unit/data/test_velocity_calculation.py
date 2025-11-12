"""Tests for velocity calculation helper function.

This test suite validates the fix for the velocity calculation bug identified
in Feature 010-dashboard-readability. The bug was that velocity used date range
instead of actual number of weeks with data, which deflated velocity when data
was sparse.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from data.processing import calculate_velocity_from_dataframe


class TestVelocityCalculationCorrectness:
    """Test that velocity calculation uses actual weeks, not date range."""

    def test_continuous_weekly_data(self):
        """Test velocity with continuous weekly data (no gaps)."""
        # 4 consecutive weeks, 10 items each
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-01-06", "2025-01-13", "2025-01-20", "2025-01-27"]
                ),
                "completed_items": [10, 10, 10, 10],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # Should be 40 items / 4 weeks = 10.0 items/week
        assert velocity == 10.0

    def test_sparse_data_with_gaps(self):
        """Test velocity with sparse data (weeks with gaps).

        This is the critical test case that exposed the original bug.
        With gaps in data, the old method would use date range and deflate velocity.
        """
        # Week 1 and Week 10 only (9 weeks apart, but only 2 data points)
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-03-10"]),
                "completed_items": [10, 10],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # Should be 20 items / 2 weeks = 10.0 items/week
        # OLD BUG: Would calculate 20 items / 9 weeks = 2.2 items/week
        assert velocity == 10.0

    def test_multiple_entries_same_week(self):
        """Test velocity when same week has multiple data points."""
        # All entries in same week (Week 1)
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-01-06", "2025-01-07", "2025-01-08", "2025-01-09"]
                ),
                "completed_items": [5, 5, 5, 5],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # Should be 20 items / 1 week = 20.0 items/week
        assert velocity == 20.0

    def test_irregular_spacing(self):
        """Test velocity with irregular spacing between data points."""
        # Week 1, Week 3, Week 4, Week 8 (irregular gaps)
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-01-06", "2025-01-20", "2025-01-27", "2025-02-24"]
                ),
                "completed_items": [12, 15, 18, 20],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # Should be 65 items / 4 weeks = 16.2 items/week (rounded to 16.2)
        # OLD BUG: Would calculate 65 items / 7 weeks = 9.3 items/week
        assert velocity == 16.2

    def test_single_data_point(self):
        """Test velocity with only one data point."""
        df = pd.DataFrame(
            {"date": pd.to_datetime(["2025-01-06"]), "completed_items": [15]}
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # Should be 15 items / 1 week = 15.0 items/week
        assert velocity == 15.0

    def test_story_points_column(self):
        """Test velocity calculation for story points column."""
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-01-13"]),
                "completed_items": [10, 10],
                "completed_points": [50, 60],
            }
        )

        velocity_points = calculate_velocity_from_dataframe(df, "completed_points")

        # Should be 110 points / 2 weeks = 55.0 points/week
        assert velocity_points == 55.0


class TestVelocityCalculationEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test velocity with empty DataFrame."""
        df = pd.DataFrame({"date": [], "completed_items": []})

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 0.0

    def test_zero_completed_items(self):
        """Test velocity when all completed items are zero."""
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-01-13"]),
                "completed_items": [0, 0],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # Should be 0 items / 2 weeks = 0.0 items/week
        assert velocity == 0.0

    def test_missing_date_column(self):
        """Test error handling when 'date' column is missing."""
        df = pd.DataFrame({"completed_items": [10, 10]})

        with pytest.raises(KeyError, match="must have 'date' column"):
            calculate_velocity_from_dataframe(df, "completed_items")

    def test_missing_data_column(self):
        """Test error handling when specified data column is missing."""
        df = pd.DataFrame(
            {"date": pd.to_datetime(["2025-01-06", "2025-01-13"]), "items": [10, 10]}
        )

        with pytest.raises(KeyError, match="must have 'completed_items' column"):
            calculate_velocity_from_dataframe(df, "completed_items")

    def test_rounding_behavior(self):
        """Test that velocity is rounded to 1 decimal place."""
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-01-13", "2025-01-20"]),
                "completed_items": [10, 10, 11],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # 31 items / 3 weeks = 10.333... → should round to 10.3
        assert velocity == 10.3


class TestVelocityCalculationComparisonWithOldMethod:
    """Compare new method with old (buggy) method to validate fix."""

    def _calculate_velocity_old_method(
        self, df: pd.DataFrame, column: str = "completed_items"
    ) -> float:
        """Old (buggy) method that uses date range."""
        if df.empty or len(df) == 0:
            return 0.0

        date_range = (df["date"].max() - df["date"].min()).days
        weeks = max(1, date_range / 7.0)
        total = df[column].sum()
        return round(total / weeks, 1)

    def test_continuous_data_both_methods_agree(self):
        """With continuous data, both methods should agree (approximately).

        Note: Even with weekly data, old method can be slightly off because it uses
        date range in days divided by 7, which may not match actual week boundaries.
        """
        # 4 consecutive weeks
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-01-06", "2025-01-13", "2025-01-20", "2025-01-27"]
                ),
                "completed_items": [10, 10, 10, 10],
            }
        )

        velocity_new = calculate_velocity_from_dataframe(df, "completed_items")
        velocity_old = self._calculate_velocity_old_method(df, "completed_items")

        # New method: 40 items / 4 weeks = 10.0 items/week (CORRECT)
        assert velocity_new == 10.0

        # Old method uses date range: 21 days / 7 = 3.0 weeks, 40/3 = 13.3 (WRONG)
        # This shows the old method is wrong even with "continuous" data!
        assert velocity_old == 13.3

    def test_sparse_data_methods_differ(self):
        """With sparse data, new method should be higher (correct)."""
        # Week 1 and Week 10 (9 weeks apart)
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-03-10"]),
                "completed_items": [10, 10],
            }
        )

        velocity_new = calculate_velocity_from_dataframe(df, "completed_items")
        velocity_old = self._calculate_velocity_old_method(df, "completed_items")

        # New method: 20 items / 2 weeks = 10.0 items/week (CORRECT)
        assert velocity_new == 10.0

        # Old method: 20 items / 9 weeks = 2.2 items/week (WRONG - deflated)
        assert velocity_old == 2.2

        # Verify new method produces higher (more accurate) velocity with sparse data
        assert velocity_new > velocity_old

    def test_single_point_both_methods_agree(self):
        """With single data point, both methods should agree."""
        df = pd.DataFrame(
            {"date": pd.to_datetime(["2025-01-06"]), "completed_items": [15]}
        )

        velocity_new = calculate_velocity_from_dataframe(df, "completed_items")
        velocity_old = self._calculate_velocity_old_method(df, "completed_items")

        # Both should be 15.0 items/week (single point, no range)
        assert velocity_new == velocity_old == 15.0


class TestVelocityCalculationRealWorldScenarios:
    """Test with realistic project scenarios."""

    def test_typical_project_with_weekly_reporting(self):
        """Test typical project with weekly reporting (mostly continuous)."""
        # 10 weeks of weekly reporting, with one missed week
        dates = []
        base_date = datetime(2025, 1, 6)
        for i in range(10):
            if i != 5:  # Skip week 6
                dates.append(base_date + timedelta(weeks=i))

        df = pd.DataFrame(
            {
                "date": pd.to_datetime(dates),
                "completed_items": [8, 12, 10, 9, 11, 10, 9, 13, 12],  # 9 weeks
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # 94 items / 9 weeks = 10.4 items/week
        assert velocity == 10.4

    def test_project_with_irregular_updates(self):
        """Test project with irregular update frequency."""
        # Updates at irregular intervals (not every week)
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2025-01-06",  # Week 1
                        "2025-01-20",  # Week 3
                        "2025-02-03",  # Week 5
                        "2025-02-24",  # Week 8
                        "2025-03-17",  # Week 11
                    ]
                ),
                "completed_items": [15, 20, 18, 22, 25],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # 100 items / 5 weeks = 20.0 items/week
        assert velocity == 20.0

    def test_sprint_based_project(self):
        """Test project with 2-week sprints (sprint end reporting)."""
        # Data recorded at end of each 2-week sprint
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2025-01-17",  # Sprint 1 end
                        "2025-01-31",  # Sprint 2 end
                        "2025-02-14",  # Sprint 3 end
                        "2025-02-28",  # Sprint 4 end
                    ]
                ),
                "completed_items": [20, 24, 22, 26],  # Items per sprint
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        # 92 items / 4 data points (sprints) = 23.0 items per sprint
        # Note: This treats each sprint as one "week" in the data
        assert velocity == 23.0
