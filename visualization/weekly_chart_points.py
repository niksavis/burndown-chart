"""Weekly completion chart for points (story points).

Contains the weekly points completion chart with optional next-week PERT forecast.
"""

from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go

from configuration import COLOR_PALETTE
from data import generate_weekly_forecast
from utils.chart_tooltip_utils import create_hoverlabel_config, format_hover_template
from visualization.helpers import fill_missing_weeks
from visualization.weekly_chart_items import _add_required_velocity_line


def create_weekly_points_chart(
    statistics_data,
    pert_factor=3,
    include_forecast=True,
    data_points_count=None,
    required_velocity=None,
):
    """
    Create a bar chart showing weekly completed points
    with a weighted moving average line
    and optional forecast for next week.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: PERT factor for calculations (for forecast)
        include_forecast: Whether to include forecast data (default: True)
        data_points_count: Number of data points to use for calculations
            (default: None, uses all data)
        required_velocity: Optional required velocity to display
            as reference line (points/week)

    Returns:
        Plotly figure object with the weekly points chart
    """
    # CRITICAL FIX: Apply data points filtering by DATE RANGE, not row count
    # data_points_count represents WEEKS, not rows. With sparse data,
    # filtering by row count gives incorrect results.
    filtered_statistics_data = statistics_data
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
                df_temp = df_temp[df_temp["date"] >= cutoff_date]

                filtered_statistics_data = df_temp.to_dict("records")
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
                filtered_statistics_data = df_temp[df_temp["date"] >= cutoff_date]

    # Create DataFrame from filtered statistics data
    df = pd.DataFrame(filtered_statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Completed Points (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Points Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Date filtering already applied via data_points_count above
    # No additional filtering needed to avoid double-filtering bug

    # Calculate date range for filling missing weeks
    latest_date = df["date"].max()
    start_date = df["date"].min()

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
        .agg(points=("completed_points", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Fill in missing weeks with zeros to show complete time range
    # Use date range from aggregated data to respect data_points_count filtering
    if not weekly_df.empty:
        weekly_start = weekly_df["start_date"].min()
        weekly_end = weekly_df["start_date"].max()
        weekly_df = fill_missing_weeks(weekly_df, weekly_start, weekly_end, ["points"])
    else:
        weekly_df = fill_missing_weeks(weekly_df, start_date, latest_date, ["points"])

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Ensure start_date is datetime for type safety
    weekly_df["start_date"] = pd.to_datetime(
        weekly_df["start_date"], format="mixed", errors="coerce"
    )

    # Format date for display using ISO week format (2026-W07)
    weekly_df["week_label"] = (
        weekly_df["start_date"].dt.isocalendar().year.astype(str)  # type: ignore[attr-defined]
        + "-W"
        + weekly_df["start_date"].dt.isocalendar().week.astype(str).str.zfill(2)  # type: ignore[attr-defined]
    )

    # Calculate weighted moving average (last 4 weeks)
    # More weight given to recent weeks using exponential weights
    if len(weekly_df) >= 4:
        # Create a copy of points column for calculation
        values = weekly_df["points"].values
        weighted_avg = []

        for i in range(len(weekly_df)):
            if i < 3:  # First 3 weeks don't have enough prior data
                weighted_avg.append(None)
            else:
                # Get last 4 weeks of data
                window = values[i - 3 : i + 1]
                # Apply exponential weights (more weight to recent weeks)
                weights = [0.1, 0.2, 0.3, 0.4]  # Weights sum to 1.0
                w_avg = sum(w * v for w, v in zip(weights, window, strict=False))
                weighted_avg.append(w_avg)

        weekly_df["weighted_avg"] = weighted_avg

    # Create the figure
    fig = go.Figure()

    # Add bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["points"],
            marker_color=COLOR_PALETTE["points"],
            name="Completed Points",
            text=weekly_df["points"],
            textposition="outside",
            customdata=weekly_df["week_label"],
            hovertemplate=format_hover_template(
                title="Weekly Points",
                fields={
                    "Week of": "%{customdata}",
                    "Points": "%{y}",
                },
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )
    )

    # Add weighted moving average line if we have enough data
    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        # Filter out None values for display
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        # Create a separate trace for the weighted average line
        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#FF6347",  # Tomato color
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df["week_label"],
                hovertemplate=format_hover_template(
                    title="Weighted Moving Average",
                    fields={
                        "Week of": "%{customdata}",
                        "Weighted Avg": "%{y:.1f} points",
                        "Method": "Exponential weights (0.1, 0.2, 0.3, 0.4)",
                        "Purpose": "Recent weeks have 4x more influence",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
                hoverinfo="all",  # Ensure hover info shows
            )
        )

    # Add adjusted line for current week (progressive blending)
    adjusted_points = None
    if len(weekly_df) >= 2:
        from data.metrics.blending import calculate_current_week_blend
        from data.metrics_calculator import calculate_forecast

        point_values = weekly_df["points"].tolist()
        prior_weeks = point_values[:-1]
        forecast_weeks = prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks

        if len(forecast_weeks) >= 2:
            forecast_data = calculate_forecast(forecast_weeks)
            forecast_value = (
                forecast_data.get("forecast_value", 0) if forecast_data else 0
            )

            if forecast_value > 0:
                adjusted_points = list(point_values)
                adjusted_points[-1] = calculate_current_week_blend(
                    point_values[-1], forecast_value
                )

    if adjusted_points:
        fig.add_trace(
            go.Scatter(
                x=weekly_df["week_label"],
                y=adjusted_points,
                mode="lines+markers",
                name="Adjusted",
                line=dict(color="#198754", width=2, dash="dot"),
                marker=dict(size=5, color="#198754", symbol="circle-open"),
                customdata=weekly_df["week_label"],
                hovertemplate=format_hover_template(
                    title="Adjusted Points",
                    fields={
                        "Week of": "%{customdata}",
                        "Adjusted": "%{y:.1f} points",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
            )
        )

    # Add forecast data if requested
    if include_forecast and len(weekly_df) > 0:
        # Generate forecast data using filtered statistics data
        forecast_data = generate_weekly_forecast(
            filtered_statistics_data, pert_factor, data_points_count=data_points_count
        )

        if forecast_data["points"]["dates"]:
            # Get points forecast for next week
            most_likely = forecast_data["points"]["most_likely"]
            optimistic = forecast_data["points"]["optimistic"]
            pessimistic = forecast_data["points"]["pessimistic"]

            # Calculate confidence interval bounds (25% of difference)
            upper_bound = [
                ml + 0.25 * (opt - ml)
                for ml, opt in zip(most_likely, optimistic, strict=False)
            ]
            lower_bound = [
                ml - 0.25 * (ml - pes)
                for ml, pes in zip(most_likely, pessimistic, strict=False)
            ]

            # Single next week forecast with confidence interval
            fig.add_trace(
                go.Bar(
                    x=forecast_data["points"]["dates"],
                    y=most_likely,
                    marker_color=COLOR_PALETTE["points"],
                    marker_pattern_shape="x",  # Add pattern to distinguish forecast
                    opacity=0.7,
                    name="PERT Forecast",
                    text=[round(val, 1) for val in most_likely],
                    textposition="outside",
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[
                            u - ml
                            for u, ml in zip(upper_bound, most_likely, strict=False)
                        ],
                        arrayminus=[
                            ml - lb
                            for ml, lb in zip(most_likely, lower_bound, strict=False)
                        ],
                        color="rgba(0, 0, 0, 0.3)",
                    ),
                    hovertemplate=format_hover_template(
                        title="PERT Points Forecast",
                        fields={
                            "Week": "%{x}",
                            "Predicted Points": "%{y:.1f}",
                            "Confidence Range": "±25% of PERT variance",
                            "Method": "PERT 3-point estimation",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("info"),
                )
            )

            from data.metrics.forecast_calculator import calculate_ewma_forecast

            ewma_data = calculate_ewma_forecast(weekly_df["points"].tolist(), alpha=0.3)
            if ewma_data:
                ewma_value = ewma_data.get("forecast_value")
                if ewma_value is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=forecast_data["points"]["dates"],
                            y=[ewma_value],
                            mode="markers+text",
                            name="EWMA Forecast",
                            marker=dict(
                                color="#6c757d",
                                size=10,
                                symbol="diamond",
                            ),
                            text=[round(ewma_value, 1)],
                            textposition="top center",
                            hovertemplate=format_hover_template(
                                title="EWMA Points Forecast",
                                fields={
                                    "Week": "%{x}",
                                    "Predicted Points": "%{y:.1f}",
                                    "Method": "EWMA (alpha=0.3)",
                                },
                            ),
                            hoverlabel=create_hoverlabel_config("info"),
                        )
                    )

            # Add vertical line between historical and forecast data
            fig.add_vline(
                x=len(weekly_df["week_label"])
                - 0.5,  # Position between last historical and first forecast
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.5)",
                annotation_text="Forecast starts",
                annotation_position="top",
            )

    # Update layout with grid lines and styling
    fig.update_layout(
        title=None,  # Remove chart title
        xaxis_title="Week",
        yaxis_title="Points Completed",
        hovermode="x unified",
        hoverlabel=dict(
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.18,
            xanchor="center",
            x=0.5,
            tracegroupgap=6,
        ),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        margin=dict(
            b=60  # Reduced from 130 to 60
        ),
    )

    # Add required velocity reference line if provided
    if required_velocity is not None:
        # Get current velocity (latest weighted average if available)
        current_velocity = None
        if "weighted_avg" in weekly_df.columns:
            weighted_values = weekly_df["weighted_avg"].dropna()
            if len(weighted_values) > 0:
                current_velocity = weighted_values.iloc[-1]

        _add_required_velocity_line(
            fig,
            required_velocity,
            chart_type="points",
            current_velocity=current_velocity,
        )

    return fig


#######################################################################
# WEEKLY FORECAST CHARTS (4-WEEK AHEAD)
#######################################################################
