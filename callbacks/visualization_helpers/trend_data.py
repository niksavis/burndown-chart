import pandas as pd

from data import (
    calculate_performance_trend,
    generate_weekly_forecast,
)


def prepare_trend_data(
    statistics: list | pd.DataFrame,
    pert_factor: int | float,
    data_points_count: int | None = None,
) -> tuple[dict, dict]:

    items_trend = calculate_performance_trend(
        statistics, "completed_items", 4, data_points_count=data_points_count
    )
    points_trend = calculate_performance_trend(
        statistics, "completed_points", 4, data_points_count=data_points_count
    )

    if statistics is not None and (
        isinstance(statistics, pd.DataFrame)
        and not statistics.empty
        or isinstance(statistics, list)
        and len(statistics) > 0
    ):
        forecast_data = generate_weekly_forecast(
            statistics, int(pert_factor), data_points_count=data_points_count
        )

        if forecast_data:
            if "items" in forecast_data:
                if "optimistic_value" in forecast_data["items"]:
                    items_trend["optimistic_forecast"] = forecast_data["items"][
                        "optimistic_value"
                    ]
                if "most_likely_value" in forecast_data["items"]:
                    items_trend["most_likely_forecast"] = forecast_data["items"][
                        "most_likely_value"
                    ]
                if "pessimistic_value" in forecast_data["items"]:
                    items_trend["pessimistic_forecast"] = forecast_data["items"][
                        "pessimistic_value"
                    ]

            if "points" in forecast_data:
                if "optimistic_value" in forecast_data["points"]:
                    points_trend["optimistic_forecast"] = forecast_data["points"][
                        "optimistic_value"
                    ]
                if "most_likely_value" in forecast_data["points"]:
                    points_trend["most_likely_forecast"] = forecast_data["points"][
                        "most_likely_value"
                    ]
                if "pessimistic_value" in forecast_data["points"]:
                    points_trend["pessimistic_forecast"] = forecast_data["points"][
                        "pessimistic_value"
                    ]

    return items_trend, points_trend
