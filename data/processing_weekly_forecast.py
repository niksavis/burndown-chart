"""Weekly PERT forecast generator.

Produces next-week optimistic / most-likely / pessimistic item and
point forecasts using agile-adapted PERT methodology.
"""

from datetime import timedelta

import pandas as pd

from utils.caching import memoize


@memoize(max_age_seconds=300)
def generate_weekly_forecast(
    statistics_data: list[dict] | pd.DataFrame,
    pert_factor: int = 3,
    forecast_weeks: int = 1,
    data_points_count: int | None = None,  # NEW PARAMETER
) -> dict:
    """
    Generate a weekly forecast for items and points per week using PERT methodology.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        forecast_weeks: Number of weeks to forecast (default: 1)
        data_points_count: Optional parameter to limit data to most recent N data points

    Returns:
        Dictionary containing forecast data for items and points
    """
    # Ensure data_points_count is an integer (could be float from UI slider)
    if data_points_count is not None:
        data_points_count = int(data_points_count)

    # CRITICAL FIX: Apply data points filtering by DATE RANGE, not row count
    # data_points_count represents WEEKS, not rows. With sparse data,
    # filtering by row count gives incorrect results.
    if data_points_count is not None and data_points_count > 0:
        if isinstance(statistics_data, list):
            df_temp = pd.DataFrame(statistics_data)
            if not df_temp.empty and "date" in df_temp.columns:
                df_temp["date"] = pd.to_datetime(
                    df_temp["date"], format="mixed", errors="coerce"
                )
                df_temp = df_temp.dropna(subset=["date"])
                df_temp = df_temp.sort_values("date", ascending=True)

                latest_date = df_temp["date"].max()
                cutoff_date = latest_date - timedelta(weeks=data_points_count)
                df_temp = df_temp[df_temp["date"] > cutoff_date]

                statistics_data = df_temp.to_dict("records")
        elif isinstance(statistics_data, pd.DataFrame):
            df_temp = statistics_data.copy()
            if not df_temp.empty and "date" in df_temp.columns:
                df_temp["date"] = pd.to_datetime(
                    df_temp["date"], format="mixed", errors="coerce"
                )
                df_temp = df_temp.dropna(subset=["date"])
                df_temp = df_temp.sort_values("date", ascending=True)

                latest_date = df_temp["date"].max()
                cutoff_date = latest_date - timedelta(weeks=data_points_count)
                statistics_data = df_temp[df_temp["date"] > cutoff_date]

    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
    if df.empty:
        # Return empty forecast data if no historical data
        return {
            "items": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
            "points": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
        }

    # Handle both "date" and "stat_date" column names
    if "stat_date" in df.columns and "date" not in df.columns:
        df["date"] = df["stat_date"]

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Ensure data is sorted chronologically
    df = df.sort_values("date", ascending=True)

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    # Use vectorized string formatting to avoid DataFrame return issues
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(
            items=("completed_items", "sum"),
            points=("completed_points", "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Calculate PERT estimates for weekly items
    if len(weekly_df) > 0:
        valid_data_count = len(weekly_df)

        # Special handling for very small datasets
        if valid_data_count <= 3:
            # With very few data points, just use the mean for all estimates
            # This prevents crashes when pert_factor is 3 but we only
            # have 1-3 data points.
            most_likely_items = weekly_df["items"].mean()
            most_likely_points = weekly_df["points"].mean()

            # Use the same values for optimistic and pessimistic
            # to avoid erratic forecasts.
            # with tiny datasets
            optimistic_items = most_likely_items * 1.2  # Slightly optimistic
            pessimistic_items = max(
                0.1, most_likely_items * 0.8
            )  # Slightly pessimistic but positive

            optimistic_points = most_likely_points * 1.2  # Slightly optimistic
            pessimistic_points = max(
                0.1, most_likely_points * 0.8
            )  # Slightly pessimistic but positive
        else:
            # Adjust PERT factor to be at most 1/3 of available data for stable results
            # CRITICAL: Ensure valid_pert_factor is integer for
            # .nlargest()/.nsmallest() operations.
            valid_pert_factor = int(min(pert_factor, max(1, valid_data_count // 3)))
            valid_pert_factor = max(valid_pert_factor, 1)  # Ensure at least 1

            # Most likely: average of all data
            most_likely_items = weekly_df["items"].mean()

            # Optimistic: average of best performing weeks
            optimistic_items = weekly_df["items"].nlargest(valid_pert_factor).mean()

            # Pessimistic: average of worst performing weeks (excluding zeros)
            non_zero_items = weekly_df[weekly_df["items"] > 0]["items"]
            if len(non_zero_items) >= valid_pert_factor:
                pessimistic_items = non_zero_items.nsmallest(valid_pert_factor).mean()
            else:
                # If we don't have enough non-zero values, use min value
                # or a percentage of most_likely.
                pessimistic_items = (
                    non_zero_items.min()
                    if len(non_zero_items) > 0
                    else max(0.1, most_likely_items * 0.5)
                )

            # Same calculations for points
            most_likely_points = weekly_df["points"].mean()
            optimistic_points = weekly_df["points"].nlargest(valid_pert_factor).mean()

            non_zero_points = weekly_df[weekly_df["points"] > 0]["points"]
            if len(non_zero_points) >= valid_pert_factor:
                pessimistic_points = non_zero_points.nsmallest(valid_pert_factor).mean()
            else:
                # If we don't have enough non-zero values, use min value
                # or a percentage of most_likely.
                pessimistic_points = (
                    non_zero_points.min()
                    if len(non_zero_points) > 0
                    else max(0.1, most_likely_points * 0.5)
                )

        # Get the last date from historical data as starting point
        last_date = weekly_df["start_date"].max()

        # Generate the next week forecast date (ensuring proper progression)
        next_date = last_date + timedelta(weeks=1)

        # Format date for display using ISO week format (2026-W07)
        # to match historical data.
        # Protect against NaT values
        if pd.notna(next_date):
            year, week, _ = next_date.isocalendar()
            formatted_date = f"{year}-W{week:02d}"
        else:
            formatted_date = "Next Week"

        # Create forecast values for items (single week)
        most_likely_items_forecast = [most_likely_items]
        optimistic_items_forecast = [optimistic_items]
        pessimistic_items_forecast = [pessimistic_items]

        # Create forecast values for points (single week)
        most_likely_points_forecast = [most_likely_points]
        optimistic_points_forecast = [optimistic_points]
        pessimistic_points_forecast = [pessimistic_points]

        return {
            "items": {
                "dates": [formatted_date],
                "most_likely": most_likely_items_forecast,
                "optimistic": optimistic_items_forecast,
                "pessimistic": pessimistic_items_forecast,
                "most_likely_value": most_likely_items,
                "optimistic_value": optimistic_items,
                "pessimistic_value": pessimistic_items,
                "next_date": next_date,
            },
            "points": {
                "dates": [formatted_date],
                "most_likely": most_likely_points_forecast,
                "optimistic": optimistic_points_forecast,
                "pessimistic": pessimistic_points_forecast,
                "most_likely_value": most_likely_points,
                "optimistic_value": optimistic_points,
                "pessimistic_value": pessimistic_points,
                "next_date": next_date,
            },
        }
    else:
        return {
            "items": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
            "points": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
        }
