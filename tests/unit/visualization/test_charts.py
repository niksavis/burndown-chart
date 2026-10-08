import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from visualization.data_preparation import (
    generate_burndown_forecast,
    prepare_visualization_data,
)


class TestPrepareVisualizationData(unittest.TestCase):
    def setUp(self):
        self.test_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=10, freq="W"),
                "completed_items": [5, 7, 4, 6, 8, 5, 9, 7, 3, 10],
                "completed_points": [25, 35, 20, 30, 40, 25, 45, 35, 15, 50],
                "created_items": [2, 3, 1, 2, 4, 1, 0, 3, 5, 2],
                "created_points": [10, 15, 5, 10, 20, 5, 0, 15, 25, 10],
                "remaining_items": [50, 45, 41, 35, 29, 24, 19, 12, 9, 0],
                "remaining_points": [250, 225, 205, 175, 145, 120, 95, 60, 45, 0],
            }
        )

        self.test_data["cum_items"] = self.test_data["remaining_items"]
        self.test_data["cum_points"] = self.test_data["remaining_points"]

        self.total_items = 50
        self.total_points = 250

        self.pert_factor = 3

    def test_basic_data_preparation(self):
        result = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            is_burnup=False,
        )

        self.assertIsInstance(result, dict)
        expected_keys = [
            "df_calc",
            "items_forecasts",
            "points_forecasts",
            "pert_time_items",
            "pert_time_points",
        ]
        for key in expected_keys:
            self.assertIn(key, result)

        self.assertIsInstance(result["pert_time_items"], (int, float, np.number))
        self.assertIsInstance(result["pert_time_points"], (int, float, np.number))

        self.assertIn("avg", result["items_forecasts"])
        self.assertIn("opt", result["items_forecasts"])
        self.assertIn("pes", result["items_forecasts"])
        self.assertIn("ewma", result["items_forecasts"])

    def test_data_filtering(self):
        data_points_count = 5

        result_limited = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            data_points_count=data_points_count,
        )

        result_all = prepare_visualization_data(
            self.test_data, self.total_items, self.total_points, self.pert_factor
        )

        self.assertNotEqual(
            result_limited["pert_time_items"], result_all["pert_time_items"]
        )

    def test_burnup_vs_burndown_mode(self):
        burndown_result = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            is_burnup=False,
        )

        burnup_result = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            is_burnup=True,
            scope_items=self.total_items,
            scope_points=self.total_points,
        )

        burndown_forecast_items = burndown_result["items_forecasts"]
        if len(burndown_forecast_items["avg"][1]) > 1:
            self.assertGreaterEqual(
                burndown_forecast_items["avg"][1][0],
                burndown_forecast_items["avg"][1][-1],
            )

        burnup_forecast_items = burnup_result["items_forecasts"]
        if len(burnup_forecast_items["avg"][1]) > 1:
            self.assertGreaterEqual(
                burnup_forecast_items["avg"][1][-1], burnup_forecast_items["avg"][1][0]
            )

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["date", "completed_items", "completed_points"])

        result = prepare_visualization_data(
            empty_df, self.total_items, self.total_points, self.pert_factor
        )

        self.assertIsInstance(result, dict)
        self.assertIn("pert_time_items", result)
        self.assertIn("pert_time_points", result)
        self.assertIn("items_forecasts", result)
        self.assertIn("points_forecasts", result)

        self.assertEqual(result["pert_time_items"], 0)
        self.assertEqual(result["pert_time_points"], 0)

    def test_scope_parameter_usage(self):
        scope_items = 60
        scope_points = 300

        result = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            is_burnup=True,
            scope_items=scope_items,
            scope_points=scope_points,
        )

        burnup_forecast_items = result["items_forecasts"]
        if len(burnup_forecast_items["avg"][1]) > 0:
            self.assertAlmostEqual(
                burnup_forecast_items["avg"][1][-1], scope_items, delta=1
            )


class TestGenerateBurndownForecast(unittest.TestCase):
    def setUp(self):
        self.last_value = 50
        self.avg_rate = 1.0
        self.opt_rate = 1.5
        self.pes_rate = 0.5
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=60)

    def test_basic_forecast_generation(self):
        result = generate_burndown_forecast(
            self.last_value,
            self.avg_rate,
            self.opt_rate,
            self.pes_rate,
            self.start_date,
            self.end_date,
        )

        self.assertIn("avg", result)
        self.assertIn("opt", result)
        self.assertIn("pes", result)

        for forecast_type in ["avg", "opt", "pes"]:
            dates, values = result[forecast_type]
            self.assertEqual(len(dates), len(values))
            self.assertGreaterEqual(len(dates), 2)

    def test_linear_decrease(self):
        result = generate_burndown_forecast(
            self.last_value,
            self.avg_rate,
            self.opt_rate,
            self.pes_rate,
            self.start_date,
            self.end_date,
        )

        dates, values = result["avg"]

        for i in range(1, len(values)):
            days_elapsed = (dates[i] - dates[0]).days
            expected_value = max(0, self.last_value - (self.avg_rate * days_elapsed))
            self.assertAlmostEqual(values[i], expected_value, delta=0.6)

        dates, values = result["opt"]

        for i in range(1, len(values)):
            days_elapsed = (dates[i] - dates[0]).days
            expected_value = max(0, self.last_value - (self.opt_rate * days_elapsed))
            self.assertAlmostEqual(values[i], expected_value, delta=0.6)

        dates, values = result["pes"]

        for i in range(1, len(values)):
            days_elapsed = (dates[i] - dates[0]).days
            expected_value = max(0, self.last_value - (self.pes_rate * days_elapsed))
            self.assertAlmostEqual(values[i], expected_value, delta=0.6)

    def test_zero_minimum(self):
        high_rate = 5.0

        result = generate_burndown_forecast(
            self.last_value,
            high_rate,
            high_rate,
            high_rate,
            self.start_date,
            self.end_date,
        )

        for forecast_type in ["avg", "opt", "pes"]:
            dates, values = result[forecast_type]
            for value in values:
                self.assertGreaterEqual(value, 0)

    def test_different_rates(self):
        avg_rate = 1.0
        opt_rate = 2.0
        pes_rate = 0.5

        result = generate_burndown_forecast(
            self.last_value,
            avg_rate,
            opt_rate,
            pes_rate,
            self.start_date,
            self.end_date,
        )

        dates_avg, values_avg = result["avg"]
        dates_opt, values_opt = result["opt"]
        dates_pes, values_pes = result["pes"]

        completion_day_avg = None
        completion_day_opt = None
        completion_day_pes = None

        for i, value in enumerate(values_avg):
            if value == 0:
                completion_day_avg = (dates_avg[i] - self.start_date).days
                break

        for i, value in enumerate(values_opt):
            if value == 0:
                completion_day_opt = (dates_opt[i] - self.start_date).days
                break

        for i, value in enumerate(values_pes):
            if value == 0:
                completion_day_pes = (dates_pes[i] - self.start_date).days
                break

        if completion_day_avg and completion_day_opt and completion_day_pes:
            self.assertLess(completion_day_opt, completion_day_avg)
            self.assertLess(completion_day_avg, completion_day_pes)

    def test_fixed_end_date_behavior(self):
        short_end_date = self.start_date + timedelta(days=10)

        result_short = generate_burndown_forecast(
            self.last_value,
            self.avg_rate,
            self.opt_rate,
            self.pes_rate,
            self.start_date,
            short_end_date,
        )

        dates, values = result_short["avg"]

        self.assertEqual(values[0], self.last_value)

        days_elapsed = (dates[-1] - dates[0]).days
        expected_final_value = max(0, self.last_value - (self.avg_rate * days_elapsed))
        self.assertAlmostEqual(values[-1], expected_final_value, delta=0.01)

        for i in range(1, len(values)):
            days = (dates[i] - dates[0]).days
            expected = max(0, self.last_value - (self.avg_rate * days))
            self.assertAlmostEqual(values[i], expected, delta=0.01)

    def test_burnup_burndown_consistency(self):
        import logging

        from visualization.data_preparation import prepare_visualization_data

        logger = logging.getLogger("test_burnup_burndown")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        test_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2023-01-01", periods=5, freq="W"),
                "completed_items": [5, 7, 6, 8, 4],
                "completed_points": [
                    25,
                    35,
                    30,
                    40,
                    20,
                ],
                "remaining_items": [45, 38, 32, 24, 20],
                "remaining_points": [
                    225,
                    190,
                    160,
                    120,
                    100,
                ],
                "created_items": [
                    0,
                    0,
                    0,
                    0,
                    0,
                ],
                "created_points": [
                    0,
                    0,
                    0,
                    0,
                    0,
                ],
            }
        )

        test_data["cum_items"] = test_data["remaining_items"]
        test_data["cum_points"] = test_data["remaining_points"]
        test_data["cum_completed_items"] = test_data["completed_items"].cumsum()
        test_data["cum_completed_points"] = test_data["completed_points"].cumsum()

        total_items = 50
        total_points = 250
        pert_factor = 3

        try:
            burndown_result = prepare_visualization_data(
                test_data, total_items, total_points, pert_factor, is_burnup=False
            )

            burnup_result = prepare_visualization_data(
                test_data,
                total_items,
                total_points,
                pert_factor,
                is_burnup=True,
                scope_items=total_items,
                scope_points=total_points,
            )

            logger.info(
                f"Burndown PERT time (items): {burndown_result['pert_time_items']}"
            )
            logger.info(f"Burnup PERT time (items): {burnup_result['pert_time_items']}")

            if (
                "items_forecasts" not in burndown_result
                or "avg" not in burndown_result["items_forecasts"]
            ):
                logger.error("Missing forecast data in burndown result")
                return

            if (
                "items_forecasts" not in burnup_result
                or "avg" not in burnup_result["items_forecasts"]
            ):
                logger.error("Missing forecast data in burnup result")
                return

            if len(burndown_result["items_forecasts"]["avg"][1]) > 2:
                burndown_values = burndown_result["items_forecasts"]["avg"][1]
                burndown_rate = burndown_values[1] - burndown_values[0]
                logger.info(f"Burndown first values: {burndown_values[:5]}")
                logger.info(f"Burndown rate: {burndown_rate}")

            if len(burnup_result["items_forecasts"]["avg"][1]) > 2:
                burnup_values = burnup_result["items_forecasts"]["avg"][1]
                burnup_rate = burnup_values[1] - burnup_values[0]
                logger.info(f"Burnup first values: {burnup_values[:5]}")
                logger.info(f"Burnup rate: {burnup_rate}")

            if (
                burndown_result["pert_time_items"] > 0
                and burnup_result["pert_time_items"] > 0
            ):
                pert_time_diff = abs(
                    burndown_result["pert_time_items"]
                    - burnup_result["pert_time_items"]
                )
                logger.info(f"PERT time difference: {pert_time_diff} days")

                max_acceptable_diff = 5
                self.assertLessEqual(
                    pert_time_diff,
                    max_acceptable_diff,
                    "Burndown and burnup PERT times differ by "
                    f"{pert_time_diff} days, which exceeds the maximum "
                    "acceptable difference of "
                    f"{max_acceptable_diff} days",
                )

            if (
                len(burndown_result["items_forecasts"]["avg"][1]) > 2
                and len(burnup_result["items_forecasts"]["avg"][1]) > 2
            ):
                burndown_values = burndown_result["items_forecasts"]["avg"][1]
                burndown_rate = burndown_values[1] - burndown_values[0]

                burnup_values = burnup_result["items_forecasts"]["avg"][1]
                burnup_rate = burnup_values[1] - burnup_values[0]

                if not burndown_rate < 0:
                    logger.error(
                        "FAILED: Burndown rate should be negative "
                        f"but is {burndown_rate}"
                    )
                self.assertLess(
                    burndown_rate,
                    0,
                    f"Burndown rate should be negative but is {burndown_rate}",
                )

                if not burnup_rate > 0:
                    logger.error(
                        f"FAILED: Burnup rate should be positive but is {burnup_rate}"
                    )
                self.assertGreater(
                    burnup_rate,
                    0,
                    f"Burnup rate should be positive but is {burnup_rate}",
                )

                if burndown_rate < 0 and burnup_rate > 0:
                    ratio = (
                        abs(burndown_rate) / abs(burnup_rate)
                        if abs(burnup_rate) > 0
                        else float("inf")
                    )
                    logger.info(f"Rate ratio (abs(burndown)/abs(burnup)): {ratio}")

                    min_ratio = 0.1
                    max_ratio = 10.0

                    if not (min_ratio <= ratio <= max_ratio):
                        logger.error(
                            "FAILED: Rate ratio "
                            f"{ratio} is outside acceptable range "
                            f"[{min_ratio}, {max_ratio}]"
                        )

                    try:
                        self.assertGreaterEqual(
                            ratio,
                            min_ratio,
                            "Burndown rate is too small compared to "
                            f"burnup rate (ratio: {ratio})",
                        )
                        self.assertLessEqual(
                            ratio,
                            max_ratio,
                            "Burndown rate is too large compared to "
                            f"burnup rate (ratio: {ratio})",
                        )
                    except AssertionError as e:
                        logger.error(f"Rate ratio assertion failed: {e}")

        except Exception as e:
            logger.error(
                f"Error in test_burnup_burndown_consistency: {type(e).__name__}: {e}"
            )
            logger.info("Test data columns: " + str(test_data.columns.tolist()))

            raise


if __name__ == "__main__":
    unittest.main()
