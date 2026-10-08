import logging

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

from ui.styles import create_metric_card_header

logger = logging.getLogger(__name__)


def _create_card_footer(text: str, icon: str = "fa-info-circle") -> dbc.CardFooter:

    return dbc.CardFooter(
        html.Div(
            [
                html.I(className=f"fas {icon} me-1"),
                text,
            ],
            className="text-center text-muted py-2 px-3",
            style={"fontSize": "0.85rem", "lineHeight": "1.4"},
        ),
        className="bg-light border-top",
    )


def create_cost_breakdown_card(
    breakdown: dict[str, dict[str, float]],
    weekly_breakdowns: list[dict[str, dict[str, float]]] | None = None,
    weekly_labels: list[str] | None = None,
    currency_symbol: str = "€",
    data_points_count: int = 4,
    card_id: str | None = None,
) -> dbc.Card:

    total_cost = sum(cat["cost"] for cat in breakdown.values())

    category_rows = []
    for flow_type in ["Feature", "Defect", "Technical Debt", "Risk"]:
        cat_data = breakdown.get(flow_type, {"cost": 0, "count": 0, "percentage": 0})
        cost = cat_data["cost"]
        count = cat_data["count"]
        pct = cat_data["percentage"]

        sparkline_values = []
        if weekly_breakdowns and weekly_labels:
            sparkline_values = [
                wb.get(flow_type, {}).get("cost", 0)
                for wb in weekly_breakdowns[-data_points_count:]
            ]

        sparkline = (
            _create_inline_sparkline(sparkline_values, flow_type)
            if sparkline_values
            else html.Div("—", className="text-muted")
        )

        category_rows.append(
            html.Tr(
                [
                    html.Td(flow_type, className="text-start", style={"width": "20%"}),
                    html.Td(
                        f"{currency_symbol}{cost:,.2f}",
                        className="text-end",
                        style={"width": "20%"},
                    ),
                    html.Td(f"{pct:.1f}%", className="text-end", style={"width": "8%"}),
                    html.Td(
                        f"{count} items",
                        className="text-end text-muted",
                        style={"width": "12%"},
                    ),
                    html.Td(sparkline, className="text-center", style={"width": "40%"}),
                ]
            )
        )

    breakdown_table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th(
                            "Work Type", className="text-start", style={"width": "20%"}
                        ),
                        html.Th("Cost", className="text-end", style={"width": "20%"}),
                        html.Th("%", className="text-end", style={"width": "8%"}),
                        html.Th("Count", className="text-end", style={"width": "12%"}),
                        html.Th(
                            "Trend", className="text-center", style={"width": "40%"}
                        ),
                    ]
                )
            ),
            html.Tbody(category_rows),
        ],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
    )

    card_content = dbc.Card(
        [
            create_metric_card_header(
                title="Cost Breakdown by Work Distribution",
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.H4(
                                f"{currency_symbol}{total_cost:,.2f}",
                                className="mb-1",
                                style={"color": "#6f42c1"},
                            ),
                            html.P("Total Project Cost", className="text-muted mb-3"),
                        ],
                        className="text-center",
                    ),
                    breakdown_table,
                ]
            ),
            _create_card_footer(
                (
                    f"Costs aggregated over {data_points_count} weeks • "
                    "Categorized by Flow Distribution types"
                ),
                "fa-chart-bar",
            ),
        ],
        id=card_id,
        className="metric-card metric-card-large mb-3 h-100",
    )

    return card_content


def _create_inline_sparkline(values: list[float], flow_type: str = ""):

    if not values or len(values) < 2:
        return html.Div("—", className="text-muted")

    flow_colors = {
        "Feature": "#6f42c1",
        "Defect": "#e83e8c",
        "Technical Debt": "#17a2b8",
        "Risk": "#6610f2",
    }
    color = flow_colors.get(flow_type, "#6c757d")

    recent_avg = sum(values[-3:]) / min(3, len(values[-3:]))
    older_avg = sum(values[:3]) / min(3, len(values[:3]))
    trend_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0

    if abs(trend_pct) < 5:
        trend_icon = "fa-minus"
        trend_color = "#6c757d"
        trend_title = "Stable"
    elif trend_pct > 0:
        trend_icon = "fa-arrow-up"
        trend_color = "#dc3545"
        trend_title = f"Up {trend_pct:.0f}%"
    else:
        trend_icon = "fa-arrow-down"
        trend_color = "#198754"
        trend_title = f"Down {abs(trend_pct):.0f}%"

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(range(len(values))),
            y=values,
            mode="lines+markers",
            line={"color": color, "width": 2},
            marker={"size": 4, "color": color},
            hovertemplate="€%{y:,.0f}<extra></extra>",
            showlegend=False,
        )
    )

    min_val = min(values)
    max_val = max(values)
    range_padding = (max_val - min_val) * 0.2 if max_val > min_val else max_val * 0.1
    y_min = max(0, min_val - range_padding)
    y_max = max_val + range_padding

    fig.update_layout(
        {
            "height": 40,
            "margin": {"t": 2, "r": 2, "b": 2, "l": 2},
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "xaxis": {
                "visible": False,
                "showgrid": False,
            },
            "yaxis": {
                "visible": False,
                "showgrid": False,
                "range": [y_min, y_max],
            },
            "hovermode": "closest",
        }
    )

    return html.Div(
        [
            dcc.Graph(
                figure=fig,
                config={
                    "displayModeBar": False,
                    "staticPlot": False,
                    "responsive": True,
                },
                style={"height": "40px", "width": "100%"},
                className="flex-grow-1",
            ),
            html.I(
                className=f"fas {trend_icon} ms-1 flex-shrink-0",
                style={"color": trend_color, "fontSize": "0.75rem"},
                title=trend_title,
            ),
        ],
        className="d-flex align-items-center justify-content-center w-100",
    )
