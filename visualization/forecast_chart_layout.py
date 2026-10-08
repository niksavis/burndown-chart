import pandas as pd

from configuration import COLOR_PALETTE


def configure_axes(fig, forecast_data):

    max_items = forecast_data["max_items"]
    max_points = forecast_data["max_points"]

    scale_factor = max_points / max_items if max_items > 0 else 1

    items_range = [0, max_items * 1.1]
    points_range = [0, max_items * scale_factor * 1.1]

    fig.update_xaxes(
        title="",
        tickmode="auto",
        nticks=20,
        tickformat="%Y-W%V",
        gridcolor="rgba(200, 200, 200, 0.2)",
        automargin=True,
        tickangle=45,
    )

    fig.update_yaxes(
        title="",
        range=items_range,
        gridcolor=COLOR_PALETTE["items_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=False,
    )

    fig.update_yaxes(
        title="",
        range=points_range,
        gridcolor=COLOR_PALETTE["points_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=True,
    )

    return fig


def apply_layout_settings(fig):
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            itemclick="toggle",
            itemdoubleclick=False,
        ),
        hovermode="x unified",
        margin=dict(l=60, r=60, t=80, b=50),
        height=700,
        template="plotly_white",
    )
    return fig


def add_metrics_annotations(fig, metrics_data, data_points_count=None):

    if metrics_data is None:
        metrics_data = {}
    base_y_position = -0.20
    font_color = "rgba(50, 50, 50, 0.9)"
    value_font_size = 12

    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=base_y_position - 0.15,
        x1=1,
        y1=base_y_position + 0.05,
        fillcolor="rgba(245, 245, 245, 0.8)",
        line=dict(color="rgba(200, 200, 200, 0.5)", width=1),
    )

    points_data_available = (
        metrics_data.get("completed_points", 0) > 0
        or metrics_data.get("avg_weekly_points", 0) > 0
        or (
            metrics_data.get("total_scope_points", 0) > 0
            and metrics_data.get("total_points", 0) > 0
        )
    )

    if (
        metrics_data.get("total_scope_points", 0) == metrics_data.get("total_points", 0)
        and metrics_data.get("completed_points", 0) == 0
    ):
        points_data_available = False

    metrics = [
        {
            "label": "Scope Items",
            "value": metrics_data.get("total_scope_items", 0),
            "format": "{:,.0f}",
        },
        {
            "label": "Scope Points",
            "value": metrics_data.get("total_scope_points", 0)
            if points_data_available
            else None,
            "format": "{:,.0f}" if points_data_available else "n/a",
        },
        {"label": "Deadline", "value": metrics_data["deadline"], "format": "{}"},
        {
            "label": "Completed Items",
            "value": metrics_data.get("completed_items", 0),
            "format": "{:,.0f} ({:.1f}%)",
            "extra_value": metrics_data.get("items_percent_complete", 0),
        },
        {
            "label": "Completed Points",
            "value": metrics_data.get("completed_points", 0)
            if points_data_available
            else None,
            "format": "{:,.0f} ({:.1f}%)" if points_data_available else "n/a",
            "extra_value": metrics_data.get("points_percent_complete", 0)
            if points_data_available
            else None,
        },
        {
            "label": "Deadline in",
            "value": metrics_data["days_to_deadline"],
            "format": "{:,} days",
        },
        {
            "label": "Remaining Items",
            "value": metrics_data["total_items"],
            "format": "{:,.0f}",
        },
        {
            "label": "Remaining Points",
            "value": metrics_data["total_points"] if points_data_available else None,
            "format": "{:,.0f}" if points_data_available else "n/a",
        },
        {
            "label": "Est. Days (Items)",
            "value": metrics_data["pert_time_items"],
            "format": "{:.1f} days",
        },
        {
            "label": f"Avg Weekly Items ({data_points_count or 'All'}W)",
            "value": metrics_data["avg_weekly_items"],
            "format": "{:.2f}",
        },
        {
            "label": f"Avg Weekly Points ({data_points_count or 'All'}W)",
            "value": metrics_data["avg_weekly_points"]
            if points_data_available
            else None,
            "format": "{:.2f}" if points_data_available else "n/a",
        },
        {
            "label": "Est. Days (Points)",
            "value": metrics_data["pert_time_points"]
            if points_data_available
            else None,
            "format": "{:.1f} days" if points_data_available else "n/a",
        },
    ]

    columns = 3

    for idx, metric in enumerate(metrics):
        row = idx // columns
        col = idx % columns

        x_pos = 0.02 + (col * (1.0 - 0.04) / columns)
        y_offset = -0.05 * row
        y_pos = base_y_position + y_offset

        if metric["value"] is None:
            formatted_value = metric["format"]
        elif "extra_value" in metric and metric["extra_value"] is not None:
            formatted_value = metric["format"].format(
                metric["value"], metric["extra_value"]
            )
        else:
            formatted_value = metric["format"].format(metric["value"])

        text_color = font_color
        if "Est. Days" in metric["label"]:
            if "Items" in metric["label"]:
                if metrics_data["pert_time_items"] > metrics_data["days_to_deadline"]:
                    text_color = "red"
                else:
                    text_color = "green"
            elif "Points" in metric["label"] and metric["value"] is not None:
                if metrics_data["pert_time_points"] > metrics_data["days_to_deadline"]:
                    text_color = "red"
                else:
                    text_color = "green"

        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=x_pos,
            y=y_pos,
            text=f"<b>{metric['label']}:</b> {formatted_value}",
            showarrow=False,
            font=dict(
                size=value_font_size, color=text_color, family="Arial, sans-serif"
            ),
            align="left",
            xanchor="left",
        )
    fig.update_layout(margin=dict(b=220))

    return fig


def add_deadline_marker(fig, deadline, milestone=None):

    if deadline is None or (isinstance(deadline, pd.Timestamp) and pd.isna(deadline)):
        return fig

    if isinstance(deadline, pd.Timestamp):
        deadline_datetime = deadline.to_pydatetime()
    else:
        deadline_datetime = deadline

    fig.add_shape(
        type="line",
        x0=deadline_datetime,
        x1=deadline_datetime,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="#FF0000", width=2, dash="dash"),
        layer="above",
    )

    fig.add_annotation(
        x=deadline_datetime,
        y=1.03,
        xref="x",
        yref="paper",
        text="Deadline",
        showarrow=False,
        font=dict(color="#FF0000", size=14),
        xanchor="center",
        yanchor="bottom",
    )

    current_date = pd.Timestamp.now()

    if current_date < deadline:
        critical_start = deadline - pd.Timedelta(days=14)

        if isinstance(critical_start, pd.Timestamp):
            critical_start_datetime = critical_start.to_pydatetime()
        else:
            critical_start_datetime = critical_start

        fig.add_shape(
            type="rect",
            x0=critical_start_datetime,
            x1=deadline_datetime,
            y0=0,
            y1=1,
            yref="paper",
            fillcolor="rgba(255, 0, 0, 0.15)",
            line=dict(width=0),
            layer="below",
        )
    else:
        if isinstance(current_date, pd.Timestamp):
            current_datetime = current_date.to_pydatetime()
        else:
            current_datetime = current_date

        fig.add_shape(
            type="rect",
            x0=deadline_datetime,
            x1=current_datetime,
            y0=0,
            y1=1,
            yref="paper",
            fillcolor="rgba(255, 0, 0, 0.15)",
            line=dict(width=0),
            layer="below",
        )

    if milestone is not None:
        if isinstance(milestone, pd.Timestamp):
            milestone_datetime = milestone.to_pydatetime()
        else:
            milestone_datetime = milestone

        milestone_color = COLOR_PALETTE.get("optimistic", "#5E35B1")

        fig.add_shape(
            type="line",
            x0=milestone_datetime,
            x1=milestone_datetime,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color=milestone_color, width=2, dash="dot"),
            layer="above",
        )

        fig.add_annotation(
            x=milestone_datetime,
            y=0.99,
            xref="x",
            yref="paper",
            text=f"MS-{milestone_datetime.strftime('%Y-%m-%d')}",
            showarrow=False,
            font=dict(color=milestone_color, size=14),
            xanchor="center",
            yanchor="bottom",
        )

    return fig
