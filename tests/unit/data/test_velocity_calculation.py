from datetime import datetime, timedelta

import pandas as pd
import pytest

from data.processing import calculate_velocity_from_dataframe


class TestVelocityCalculationCorrectness:
    def test_continuous_weekly_data(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-01-06", "2025-01-13", "2025-01-20", "2025-01-27"]
                ),
                "completed_items": [10, 10, 10, 10],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 10.0

    def test_sparse_data_with_gaps(self):

        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-03-10"]),
                "completed_items": [10, 10],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 10.0

    def test_multiple_entries_same_week(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-01-06", "2025-01-07", "2025-01-08", "2025-01-09"]
                ),
                "completed_items": [5, 5, 5, 5],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 20.0

    def test_irregular_spacing(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-01-06", "2025-01-20", "2025-01-27", "2025-02-24"]
                ),
                "completed_items": [12, 15, 18, 20],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 16.25

    def test_single_data_point(self):
        df = pd.DataFrame(
            {"date": pd.to_datetime(["2025-01-06"]), "completed_items": [15]}
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 15.0

    def test_story_points_column(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-01-13"]),
                "completed_items": [10, 10],
                "completed_points": [50, 60],
            }
        )

        velocity_points = calculate_velocity_from_dataframe(df, "completed_points")

        assert velocity_points == 55.0


class TestVelocityCalculationEdgeCases:
    def test_empty_dataframe(self):
        df = pd.DataFrame({"date": [], "completed_items": []})

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 0.0

    def test_zero_completed_items(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-01-13"]),
                "completed_items": [0, 0],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 0.0

    def test_missing_date_column(self):
        df = pd.DataFrame({"completed_items": [10, 10]})

        with pytest.raises(KeyError, match="must have 'date' column"):
            calculate_velocity_from_dataframe(df, "completed_items")

    def test_missing_data_column(self):
        df = pd.DataFrame(
            {"date": pd.to_datetime(["2025-01-06", "2025-01-13"]), "items": [10, 10]}
        )

        with pytest.raises(KeyError, match="must have 'completed_items' column"):
            calculate_velocity_from_dataframe(df, "completed_items")

    def test_rounding_behavior(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-01-13", "2025-01-20"]),
                "completed_items": [10, 10, 11],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == pytest.approx(10.333333, rel=1e-5)


class TestVelocityCalculationComparisonWithOldMethod:
    def _calculate_velocity_old_method(
        self, df: pd.DataFrame, column: str = "completed_items"
    ) -> float:
        if df.empty or len(df) == 0:
            return 0.0

        date_range = (df["date"].max() - df["date"].min()).days
        weeks = max(1, date_range / 7.0)
        total = df[column].sum()
        return round(total / weeks, 1)

    def test_continuous_data_both_methods_agree(self):

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

        assert velocity_new == 10.0

        assert velocity_old == 13.3

    def test_sparse_data_methods_differ(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-06", "2025-03-10"]),
                "completed_items": [10, 10],
            }
        )

        velocity_new = calculate_velocity_from_dataframe(df, "completed_items")
        velocity_old = self._calculate_velocity_old_method(df, "completed_items")

        assert velocity_new == 10.0

        assert velocity_old == 2.2

        assert velocity_new > velocity_old

    def test_single_point_both_methods_agree(self):
        df = pd.DataFrame(
            {"date": pd.to_datetime(["2025-01-06"]), "completed_items": [15]}
        )

        velocity_new = calculate_velocity_from_dataframe(df, "completed_items")
        velocity_old = self._calculate_velocity_old_method(df, "completed_items")

        assert velocity_new == velocity_old == 15.0


class TestVelocityCalculationRealWorldScenarios:
    def test_typical_project_with_weekly_reporting(self):
        dates = []
        base_date = datetime(2025, 1, 6)
        for i in range(10):
            if i != 5:
                dates.append(base_date + timedelta(weeks=i))

        df = pd.DataFrame(
            {
                "date": pd.to_datetime(dates),
                "completed_items": [8, 12, 10, 9, 11, 10, 9, 13, 12],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == pytest.approx(10.444444, rel=1e-5)

    def test_project_with_irregular_updates(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2025-01-06",
                        "2025-01-20",
                        "2025-02-03",
                        "2025-02-24",
                        "2025-03-17",
                    ]
                ),
                "completed_items": [15, 20, 18, 22, 25],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 20.0

    def test_sprint_based_project(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2025-01-17",
                        "2025-01-31",
                        "2025-02-14",
                        "2025-02-28",
                    ]
                ),
                "completed_items": [20, 24, 22, 26],
            }
        )

        velocity = calculate_velocity_from_dataframe(df, "completed_items")

        assert velocity == 23.0
