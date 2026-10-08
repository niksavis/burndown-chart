from typing import Any

from dash import dcc, html

from ui.metric_cards._helpers import _get_flow_performance_tier_color_hex
from visualization.flow_charts import (
    create_flow_efficiency_trend_chart,
    create_flow_load_trend_chart,
)
from visualization.metric_trends import (
    create_dual_line_trend,
    create_metric_trend_full,
    create_metric_trend_sparkline,
)


def _create_detailed_chart(
    metric_name: str,
    display_name: str,
    weekly_labels: list[str],
    weekly_values: list[float],
    weekly_values_adjusted: list[float] | None,
    metric_data: dict[str, Any],
    sparkline_color: str,
) -> Any:

    if metric_name == "deployment_frequency" and "weekly_release_values" in metric_data:
        weekly_release_values = metric_data.get("weekly_release_values", [])
        adjusted_deployment_values = weekly_values_adjusted

        tier_color = metric_data.get("performance_tier_color", "blue")

        tier_color_map = {
            "green": "#198754",
            "blue": "#0dcaf0",
            "yellow": "#ffc107",
            "orange": "#fd7e14",
        }
        primary_color = tier_color_map.get(tier_color, "#0d6efd")

        chart = create_dual_line_trend(
            week_labels=weekly_labels,
            deployment_values=weekly_values,
            release_values=weekly_release_values,
            adjusted_deployment_values=adjusted_deployment_values,
            height=250,
            show_axes=True,
            primary_color=primary_color,
            chart_title="Deployment Frequency",
        )

        return chart

    is_dora_metric = metric_name in [
        "deployment_frequency",
        "lead_time_for_changes",
        "change_failure_rate",
        "mean_time_to_recovery",
    ]

    if is_dora_metric:
        tier_color = metric_data.get("performance_tier_color", "blue")

        tier_color_map = {
            "green": "#198754",
            "blue": "#0dcaf0",
            "yellow": "#ffc107",
            "orange": "#fd7e14",
        }
        line_color = tier_color_map.get(tier_color, "#6c757d")

        return create_metric_trend_full(
            week_labels=weekly_labels,
            values=weekly_values,
            adjusted_values=weekly_values_adjusted,
            metric_name=metric_name,
            unit=metric_data.get("unit", ""),
            height=250,
            show_performance_zones=True,
            line_color=line_color,
        )
    elif metric_name == "flow_efficiency":
        trend_data = [
            {"date": week, "value": value}
            for week, value in zip(weekly_labels, weekly_values, strict=False)
        ]

        latest_value = weekly_values[-1] if weekly_values else 0
        tier_color = _get_flow_performance_tier_color_hex(
            "flow_efficiency", latest_value
        )

        figure = create_flow_efficiency_trend_chart(trend_data, line_color=tier_color)
        chart_height = int(getattr(figure.layout, "height", 300) or 300)

        return dcc.Graph(
            figure=figure,
            config={
                "displayModeBar": False,
                "staticPlot": False,
                "responsive": True,
            },
            style={"height": f"{chart_height}px"},
        )
    elif metric_name == "flow_load":
        trend_data = [
            {"date": week, "value": value}
            for week, value in zip(weekly_labels, weekly_values, strict=False)
        ]

        wip_thresholds = metric_data.get("wip_thresholds", None)

        latest_value = weekly_values[-1] if weekly_values else 0

        if wip_thresholds and "healthy" in wip_thresholds:
            if latest_value < wip_thresholds["healthy"]:
                tier_color = "#198754"
            elif latest_value < wip_thresholds["warning"]:
                tier_color = "#ffc107"
            elif latest_value < wip_thresholds["high"]:
                tier_color = "#fd7e14"
            else:
                tier_color = "#dc3545"
        else:
            tier_color = _get_flow_performance_tier_color_hex("flow_load", latest_value)

        figure = create_flow_load_trend_chart(
            trend_data, wip_thresholds=wip_thresholds, line_color=tier_color
        )
        chart_height = int(getattr(figure.layout, "height", 300) or 300)

        return dcc.Graph(
            figure=figure,
            config={
                "displayModeBar": False,
                "staticPlot": False,
                "responsive": True,
            },
            style={"height": f"{chart_height}px"},
        )
    else:
        latest_value = weekly_values[-1] if weekly_values else 0
        tier_color = _get_flow_performance_tier_color_hex(metric_name, latest_value)

        return create_metric_trend_sparkline(
            week_labels=weekly_labels,
            values=weekly_values,
            adjusted_values=weekly_values_adjusted,
            metric_name=display_name,
            unit=metric_data.get("unit", ""),
            height=200,
            show_axes=True,
            color=tier_color,
        )


def _create_deployment_details_table(
    metric_data: dict[str, Any],
    weekly_labels: list[str],
    weekly_deployments: list[float],
    weekly_releases: list[float],
) -> html.Div:

    total_deployments = sum(weekly_deployments)
    total_releases = sum(weekly_releases)
    ratio = total_deployments / total_releases if total_releases > 0 else 0

    summary = html.Div(
        [
            html.Hr(className="my-3"),
            html.H6("Deployment Details", className="text-center mb-2"),
            html.Div(
                [
                    html.Small(
                        [
                            f"Total: {int(total_deployments)} deployments \u2022 ",
                            f"{int(total_releases)} releases \u2022 ",
                            f"Ratio: {ratio:.2f}:1",
                        ],
                        className="text-muted",
                    ),
                ],
                className="text-center mb-3",
            ),
        ]
    )

    table_rows = []

    for i, week in enumerate(weekly_labels):
        if i < len(weekly_deployments) and i < len(weekly_releases):
            deployments = int(weekly_deployments[i])
            releases = int(weekly_releases[i])

            if deployments > 0 or releases > 0:
                week_ratio = deployments / releases if releases > 0 else deployments

                table_rows.append(
                    html.Tr(
                        [
                            html.Td(week, style={"fontSize": "0.85rem"}),
                            html.Td(
                                str(deployments),
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Td(
                                str(releases),
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Td(
                                f"{week_ratio:.2f}:1",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ]
                    )
                )

    if not table_rows:
        table_content = html.Div(
            html.Small(
                "No deployment activity in selected period", className="text-muted"
            ),
            className="text-center my-2",
        )
    else:
        table_content = html.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Week", style={"fontSize": "0.85rem"}),
                            html.Th(
                                "Deployments",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Th(
                                "Releases",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Th(
                                "Ratio",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ]
                    )
                ),
                html.Tbody(table_rows),
            ],
            className="table table-sm table-hover",
            style={"fontSize": "0.85rem"},
        )

    return html.Div([summary, table_content])
