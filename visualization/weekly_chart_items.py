from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go

from configuration import COLOR_PALETTE
from data import generate_weekly_forecast
from data.metrics.blending import calculate_current_week_blend
from data.metrics.forecast_calculator import calculate_ewma_forecast
from data.metrics_calculator import calculate_forecast
from utils.chart_tooltip_utils import create_hoverlabel_config, format_hover_template
from visualization.helpers import fill_missing_weeks


def _add_required_velocity_line(
    fig: go.Figure,
    required_velocity: float,
    chart_type: str = "items",
    current_velocity: float | None = None,
) -> None:

    if required_velocity is None or required_velocity == float("inf"):
        return

    if current_velocity is not None and current_velocity >= required_velocity:
        color = "#28a745"
        status = "On Pace ✓"
    else:
        color = "#dc3545"
        status = "Behind Pace"

    fig.add_shape(
        type="line",
        x0=0,
        x1=1,
        y0=required_velocity,
        y1=required_velocity,
        xref="paper",
        yref="y",
        line=dict(
            color=color,
            width=3,
            dash="dash",
        ),
        layer="above",
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(
                color=color,
                width=3,
                dash="dash",
            ),
            name=f"Required: {required_velocity:.1f} {chart_type}/week",
            hovertemplate=(
                f"<b>Required Velocity</b><br>"
                f"{required_velocity:.1f} {chart_type}/week<br>"
                f"Status: {status}<extra></extra>"
            ),
            hoverinfo="skip",
            showlegend=True,
        )
    )


def create_weekly_items_chart(
    statistics_data,
    pert_factor=3,
    include_forecast=True,
    data_points_count=None,
    required_velocity=None,
):

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

    df = pd.DataFrame(filtered_statistics_data).copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Completed Items (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Items Completed",
        )
        return fig

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    latest_date = df["date"].max()
    start_date = df["date"].min()

    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    weekly_df = (
        df.groupby("year_week")
        .agg(items=("completed_items", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    if not weekly_df.empty:
        weekly_start = weekly_df["start_date"].min()
        weekly_end = weekly_df["start_date"].max()
        weekly_df = fill_missing_weeks(weekly_df, weekly_start, weekly_end, ["items"])
    else:
        weekly_df = fill_missing_weeks(weekly_df, start_date, latest_date, ["items"])

    weekly_df = weekly_df.sort_values("start_date")

    weekly_df["start_date"] = pd.to_datetime(
        weekly_df["start_date"], format="mixed", errors="coerce"
    )

    weekly_df["week_label"] = (
        weekly_df["start_date"].dt.isocalendar().year.astype(str)  # type: ignore[attr-defined]
        + "-W"
        + weekly_df["start_date"].dt.isocalendar().week.astype(str).str.zfill(2)  # type: ignore[attr-defined]
    )

    if len(weekly_df) >= 4:
        values = weekly_df["items"].values
        weighted_avg = []

        for i in range(len(weekly_df)):
            if i < 3:
                weighted_avg.append(None)
            else:
                window = values[i - 3 : i + 1]
                weights = [0.1, 0.2, 0.3, 0.4]
                w_avg = sum(w * v for w, v in zip(weights, window, strict=False))
                weighted_avg.append(w_avg)

        weekly_df["weighted_avg"] = weighted_avg

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["items"],
            marker_color=COLOR_PALETTE["items"],
            name="Completed Items",
            text=weekly_df["items"],
            textposition="outside",
            customdata=weekly_df["week_label"],
            hovertemplate=format_hover_template(
                title="Weekly Items",
                fields={
                    "Week of": "%{customdata}",
                    "Items": "%{y}",
                },
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )
    )

    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#0047AB",
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df["week_label"],
                hovertemplate=format_hover_template(
                    title="Weighted Moving Average",
                    fields={
                        "Week of": "%{customdata}",
                        "Weighted Avg": "%{y:.1f} items",
                        "Method": "Exponential weights (0.1, 0.2, 0.3, 0.4)",
                        "Purpose": "Recent weeks have 4x more influence",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
                hoverinfo="all",
            )
        )

    adjusted_items = None
    if len(weekly_df) >= 2:
        item_values = weekly_df["items"].tolist()
        prior_weeks = item_values[:-1]
        forecast_weeks = prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks

        if len(forecast_weeks) >= 2:
            forecast_data = calculate_forecast(forecast_weeks)
            forecast_value = (
                forecast_data.get("forecast_value", 0) if forecast_data else 0
            )

            if forecast_value > 0:
                adjusted_items = list(item_values)
                adjusted_items[-1] = calculate_current_week_blend(
                    item_values[-1], forecast_value
                )

    if adjusted_items:
        fig.add_trace(
            go.Scatter(
                x=weekly_df["week_label"],
                y=adjusted_items,
                mode="lines+markers",
                name="Adjusted",
                line=dict(color="#198754", width=2, dash="dot"),
                marker=dict(size=5, color="#198754", symbol="circle-open"),
                customdata=weekly_df["week_label"],
                hovertemplate=format_hover_template(
                    title="Adjusted Items",
                    fields={
                        "Week of": "%{customdata}",
                        "Adjusted": "%{y:.1f} items",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
            )
        )

    if include_forecast and len(weekly_df) > 0:
        forecast_data = generate_weekly_forecast(
            filtered_statistics_data, pert_factor, data_points_count=data_points_count
        )

        if forecast_data["items"]["dates"]:
            most_likely = forecast_data["items"]["most_likely"]
            optimistic = forecast_data["items"]["optimistic"]
            pessimistic = forecast_data["items"]["pessimistic"]

            upper_bound = [
                ml + 0.25 * (opt - ml)
                for ml, opt in zip(most_likely, optimistic, strict=False)
            ]
            lower_bound = [
                ml - 0.25 * (ml - pes)
                for ml, pes in zip(most_likely, pessimistic, strict=False)
            ]

            fig.add_trace(
                go.Bar(
                    x=forecast_data["items"]["dates"],
                    y=most_likely,
                    marker_color=COLOR_PALETTE["items"],
                    marker_pattern_shape="x",
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
                        title="PERT Items Forecast",
                        fields={
                            "Week": "%{x}",
                            "Predicted Items": "%{y:.1f}",
                            "Confidence Range": "±25% of PERT variance",
                            "Method": "PERT 3-point estimation",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("info"),
                )
            )

            ewma_data = calculate_ewma_forecast(weekly_df["items"].tolist(), alpha=0.3)
            if ewma_data:
                ewma_value = ewma_data.get("forecast_value")
                if ewma_value is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=forecast_data["items"]["dates"],
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
                                title="EWMA Items Forecast",
                                fields={
                                    "Week": "%{x}",
                                    "Predicted Items": "%{y:.1f}",
                                    "Method": "EWMA (alpha=0.3)",
                                },
                            ),
                            hoverlabel=create_hoverlabel_config("info"),
                        )
                    )

            fig.add_vline(
                x=len(weekly_df["week_label"]) - 0.5,
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.5)",
                annotation_text="Forecast starts",
                annotation_position="top",
            )

    fig.update_layout(
        title=None,
        xaxis_title="Week",
        yaxis_title="Items Completed",
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
        margin=dict(b=70),
    )

    if required_velocity is not None:
        current_velocity = None
        if "weighted_avg" in weekly_df.columns:
            weighted_values = weekly_df["weighted_avg"].dropna()
            if len(weighted_values) > 0:
                current_velocity = weighted_values.iloc[-1]

        _add_required_velocity_line(
            fig,
            required_velocity,
            chart_type="items",
            current_velocity=current_velocity,
        )

    return fig
