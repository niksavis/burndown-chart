from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go

from configuration import COLOR_PALETTE
from data import generate_weekly_forecast
from utils.chart_tooltip_utils import create_hoverlabel_config, format_hover_template
from visualization.helpers import fill_missing_weeks


def create_weekly_points_forecast_chart(
    statistics_data, pert_factor=3, date_range_weeks=12, data_points_count=None
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
            title="Weekly Points Forecast (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Points Completed",
        )
        return fig

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    weeks = 12
    if (
        date_range_weeks is not None
        and isinstance(date_range_weeks, (int, float))
        and date_range_weeks > 0
    ):
        weeks = int(date_range_weeks)

    latest_date = df["date"].max()
    start_date = latest_date - timedelta(weeks=weeks)
    df = df[df["date"] >= start_date]

    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    weekly_df = (
        df.groupby("year_week")
        .agg(points=("completed_points", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    if not weekly_df.empty:
        weekly_start = weekly_df["start_date"].min()
        weekly_end = weekly_df["start_date"].max()
        weekly_df = fill_missing_weeks(weekly_df, weekly_start, weekly_end, ["points"])
    else:
        weekly_df = fill_missing_weeks(weekly_df, start_date, latest_date, ["points"])

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
        values = weekly_df["points"].values
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

    forecast_data = generate_weekly_forecast(
        filtered_statistics_data, pert_factor, data_points_count=data_points_count
    )

    fig = go.Figure()

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

    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#FF6347",
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df["week_label"],
                hovertemplate=format_hover_template(
                    title="Weekly Average",
                    fields={
                        "Week of": "%{customdata}",
                        "Weighted Avg": "%{y:.1f}",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
                hoverinfo="all",
            )
        )

    if forecast_data["points"]["dates"]:
        most_likely = forecast_data["points"]["most_likely"]
        optimistic = forecast_data["points"]["optimistic"]
        pessimistic = forecast_data["points"]["pessimistic"]

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
                x=forecast_data["points"]["dates"],
                y=most_likely,
                marker_color=COLOR_PALETTE["points"],
                marker_pattern_shape="x",
                opacity=0.7,
                name="Most Likely Forecast",
                text=[round(val, 1) for val in most_likely],
                textposition="outside",
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[
                        u - ml for u, ml in zip(upper_bound, most_likely, strict=False)
                    ],
                    arrayminus=[
                        ml - lb
                        for ml, lb in zip(most_likely, lower_bound, strict=False)
                    ],
                    color="rgba(0, 0, 0, 0.3)",
                ),
                hovertemplate=format_hover_template(
                    title="Points Forecast",
                    fields={
                        "Week": "%{x}",
                        "Points": "%{y:.1f}",
                        "Range": "[%{error_y.arrayminus:.1f}, %{error_y.array:.1f}]",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
            )
        )

        fig.add_trace(
            go.Bar(
                x=forecast_data["points"]["dates"],
                y=optimistic,
                marker_color=COLOR_PALETTE["optimistic"],
                marker_pattern_shape="x",
                opacity=0.6,
                name="Optimistic Forecast",
                text=[round(val, 1) for val in optimistic],
                textposition="outside",
                hovertemplate=format_hover_template(
                    title="Points Forecast",
                    fields={"Week": "%{x}", "Points": "%{y:.1f}", "Type": "Optimistic"},
                ),
                hoverlabel=create_hoverlabel_config("success"),
            )
        )

        fig.add_trace(
            go.Bar(
                x=forecast_data["points"]["dates"],
                y=pessimistic,
                marker_color=COLOR_PALETTE["pessimistic"],
                marker_pattern_shape="x",
                opacity=0.6,
                name="Pessimistic Forecast",
                text=[round(val, 1) for val in pessimistic],
                textposition="outside",
                hovertemplate=format_hover_template(
                    title="Points Forecast",
                    fields={
                        "Week": "%{x}",
                        "Points": "%{y:.1f}",
                        "Type": "Pessimistic",
                    },
                ),
                hoverlabel=create_hoverlabel_config("warning"),
            )
        )

    if weekly_df["week_label"].any() and forecast_data["points"]["dates"]:
        fig.add_vline(
            x=len(weekly_df["week_label"]) - 0.5,
            line_dash="dash",
            line_color="rgba(0, 0, 0, 0.5)",
            annotation_text="Forecast starts",
            annotation_position="top",
        )

    fig.update_layout(
        title="Weekly Points Forecast (Next 4 Weeks)",
        xaxis_title="Week Starting",
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        annotations=[
            dict(
                x=0.5,
                y=-0.25,
                xref="paper",
                yref="paper",
                text=(
                    "<b>Forecast Methodology:</b> "
                    "Based on PERT analysis using historical data.<br>"
                    "<b>Most Likely:</b> "
                    f"{forecast_data['points'].get('most_likely_value', 0):.1f} "
                    "points/week (historical average)<br>"
                    "<b>Optimistic:</b> "
                    f"{forecast_data['points'].get('optimistic_value', 0):.1f} "
                    "points/week<br>"
                    "<b>Pessimistic:</b> "
                    f"{forecast_data['points'].get('pessimistic_value', 0):.1f} "
                    "points/week<br>"
                    "<b>Weighted Average:</b> "
                    "More weight given to recent data "
                    "(40% for most recent week, 30%, 20%, 10% for earlier weeks)"
                ),
                showarrow=False,
                font=dict(size=12),
                align="center",
                bordercolor="rgba(200, 200, 200, 0.5)",
                borderwidth=1,
                borderpad=8,
                bgcolor="rgba(250, 250, 250, 0.8)",
            )
        ],
        margin=dict(b=70),
    )

    return fig
