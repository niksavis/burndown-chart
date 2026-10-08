import plotly.graph_objects as go

from configuration import COLOR_PALETTE
from utils.chart_tooltip_utils import create_hoverlabel_config, format_hover_template


def create_empty_figure(message="No data available"):

    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="#505050"),
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor="rgba(240, 240, 240, 0.1)",
        height=400,
    )
    return fig


def create_historical_trace(df, column_name, name, color, secondary_y=False):

    return {
        "data": go.Scatter(
            x=df["date"],
            y=df[column_name],
            mode="lines+markers",
            name=name,
            line=dict(color=color, width=3),
            marker=dict(size=8, color=color),
            hovertemplate=format_hover_template(
                title=name,
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    name.split()[0]: "%{y}",
                },
                extra_info=name.split()[0],
            ),
            hoverlabel=create_hoverlabel_config("default"),
        ),
        "secondary_y": secondary_y,
    }


def create_forecast_trace(
    x_vals, y_vals, name, color, dash_style="dash", secondary_y=False
):

    variant = "default"
    if "Optimistic" in name:
        variant = "success"
    elif "Pessimistic" in name:
        variant = "warning"
    elif "Most Likely" in name or "Average" in name:
        variant = "info"

    forecast_type = name.split("(")[-1].strip(")") if "(" in name else "Forecast"
    data_type = "Items" if "Items" in name else "Points"

    return {
        "data": go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            name=name,
            line=dict(color=color, dash=dash_style, width=2),
            hovertemplate=format_hover_template(
                title=f"{data_type} Forecast",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    data_type: "%{y:.1f}",
                    "Type": forecast_type,
                },
            ),
            hoverlabel=create_hoverlabel_config(variant),
        ),
        "secondary_y": secondary_y,
    }


def create_items_traces(df_calc, items_forecasts):

    traces = []

    traces.append(
        create_historical_trace(
            df_calc, "cum_items", "Items History", COLOR_PALETTE["items"], False
        )
    )

    traces.append(
        create_forecast_trace(
            items_forecasts["avg"][0],
            items_forecasts["avg"][1],
            "Items Forecast (Most Likely)",
            COLOR_PALETTE["items"],
            "dash",
            False,
        )
    )

    traces.append(
        create_forecast_trace(
            items_forecasts["opt"][0],
            items_forecasts["opt"][1],
            "Items Forecast (Optimistic)",
            COLOR_PALETTE["optimistic"],
            "dot",
            False,
        )
    )

    traces.append(
        create_forecast_trace(
            items_forecasts["pes"][0],
            items_forecasts["pes"][1],
            "Items Forecast (Pessimistic)",
            COLOR_PALETTE["pessimistic"],
            "dot",
            False,
        )
    )

    return traces


def create_points_traces(df_calc, points_forecasts):

    traces = []

    traces.append(
        create_historical_trace(
            df_calc, "cum_points", "Points History", COLOR_PALETTE["points"], True
        )
    )

    traces.append(
        create_forecast_trace(
            points_forecasts["avg"][0],
            points_forecasts["avg"][1],
            "Points Forecast (Most Likely)",
            COLOR_PALETTE["points"],
            "dash",
            True,
        )
    )

    traces.append(
        create_forecast_trace(
            points_forecasts["opt"][0],
            points_forecasts["opt"][1],
            "Points Forecast (Optimistic)",
            "rgb(184, 134, 11)",
            "dot",
            True,
        )
    )

    traces.append(
        create_forecast_trace(
            points_forecasts["pes"][0],
            points_forecasts["pes"][1],
            "Points Forecast (Pessimistic)",
            "rgb(165, 42, 42)",
            "dot",
            True,
        )
    )

    return traces


def configure_x_axis(fig):

    fig.update_xaxes(
        title={"text": "Date", "font": {"size": 16}},
        tickmode="auto",
        nticks=20,
        gridcolor="rgba(200, 200, 200, 0.2)",
        automargin=True,
    )
    return fig


def configure_y_axes(fig, items_range, points_range):

    fig.update_yaxes(
        title={"text": "Remaining Items", "font": {"size": 16}},
        range=items_range,
        gridcolor=COLOR_PALETTE["items_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=False,
    )

    fig.update_yaxes(
        title={"text": "Remaining Points", "font": {"size": 16}},
        range=points_range,
        gridcolor=COLOR_PALETTE["points_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=True,
    )

    return fig


def calculate_axis_ranges(max_items, max_points):

    scale_factor = max_points / max_items if max_items > 0 else 1

    items_range = [0, max_items * 1.1]
    points_range = [0, max_items * scale_factor * 1.1]

    return items_range, points_range


def add_deadline_marker(fig, deadline_date):

    fig.add_shape(
        type="rect",
        x0=deadline_date,
        x1=deadline_date,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(
            color=COLOR_PALETTE["deadline"],
            dash="dash",
            width=3,
        ),
        fillcolor="rgba(0,0,0,0)",
    )

    fig.add_annotation(
        x=deadline_date,
        y=1,
        yref="paper",
        text="Deadline",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40,
        font=dict(color=COLOR_PALETTE["deadline"], size=14, family="Arial, sans-serif"),
    )

    return fig


def create_metrics_background(fig, y_position=-0.2):

    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=y_position - 0.13,
        x1=1,
        y1=y_position + 0.03,
        fillcolor="rgba(245, 245, 245, 0.8)",
        line=dict(color="rgba(200, 200, 200, 0.5)", width=1),
    )

    return fig


def apply_legend_styling(fig):

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.0,
            xanchor="center",
            x=0.5,
            font={"size": 12},
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="lightgray",
            borderwidth=1,
        ),
    )
    return fig


def apply_base_layout_styling(fig):

    fig.update_layout(
        hovermode="closest",
        margin=dict(r=70, l=70, t=80, b=70),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif"},
    )
    return fig


def adjust_margins_for_metrics(fig, bottom_margin=180):

    fig.update_layout(margin=dict(b=bottom_margin))
    return fig
