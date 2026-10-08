import logging
from datetime import datetime
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.budget_cards._forecast_alignment_card import _create_card_footer
from ui.styles import create_metric_card_header

logger = logging.getLogger(__name__)


def create_budget_timeline_card(
    baseline_data: dict[str, Any],
    pert_forecast_weeks: float | None = None,
    last_date: datetime | None = None,
    card_id: str | None = None,
) -> dbc.Card:

    start_date_str = baseline_data["baseline"]["start_date"]
    allocated_end_str = baseline_data["baseline"]["allocated_end_date"]
    runway_end_str = baseline_data["actual"]["runway_end_date"]
    elapsed_weeks = baseline_data["actual"]["elapsed_weeks"]
    allocated_weeks = baseline_data["baseline"]["time_allocated_weeks"]
    runway_vs_baseline_weeks = baseline_data["variance"]["runway_vs_baseline_weeks"]

    try:
        if not start_date_str or not allocated_end_str:
            logger.error(
                "Missing required timeline dates: "
                f"start_date='{start_date_str}', "
                f"allocated_end='{allocated_end_str}'"
            )
            raise ValueError("Missing required timeline dates")

        start_date = datetime.fromisoformat(start_date_str)
        allocated_end = datetime.fromisoformat(allocated_end_str)
        current_date = datetime.now()

        if runway_end_str and runway_end_str not in [
            "N/A (no consumption)",
            "Over budget",
        ]:
            runway_end = datetime.fromisoformat(runway_end_str)
        else:
            runway_end = None

    except Exception as e:
        logger.error(f"Failed to parse timeline dates: {e}")
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Budget Timeline", className="card-title"),
                    html.P(
                        "Unable to calculate timeline dates", className="text-muted"
                    ),
                ]
            ),
            id=card_id,
            className="metric-card mb-3 h-100",
        )

    baseline_weeks_remaining = (allocated_end - current_date).days / 7.0

    timeline_markers = [
        {
            "date": start_date,
            "label": "Budget Start",
            "color": "#6610f2",
            "icon": "fa-play",
        },
        {
            "date": current_date,
            "label": "Today",
            "color": "#6f42c1",
            "icon": "fa-calendar-day",
        },
        {
            "date": allocated_end,
            "label": "Baseline End",
            "color": "#d4a017",
            "icon": "fa-flag-checkered",
        },
    ]

    if runway_end:
        runway_color = "#20c997" if runway_vs_baseline_weeks >= 0 else "#e83e8c"
        timeline_markers.append(
            {
                "date": runway_end,
                "label": "Runway End",
                "color": runway_color,
                "icon": "fa-money-bill-wave",
            }
        )

    timeline_markers.sort(key=lambda x: x["date"])
    min_date = timeline_markers[0]["date"]
    max_date = timeline_markers[-1]["date"]
    date_range = (max_date - min_date).days

    if date_range > 0:
        for marker in timeline_markers:
            days_from_start = (marker["date"] - min_date).days
            marker["raw_position"] = (days_from_start / date_range) * 100
    else:
        spacing = 100 / (len(timeline_markers) + 1)
        for i, marker in enumerate(timeline_markers):
            marker["raw_position"] = spacing * (i + 1)

    min_spacing = 12

    adjusted_positions = []
    for i, marker in enumerate(timeline_markers):
        if i == 0:
            pos = max(8, marker["raw_position"])
        else:
            prev_pos = adjusted_positions[-1]
            desired_pos = marker["raw_position"]

            if desired_pos - prev_pos < min_spacing:
                pos = prev_pos + min_spacing
            else:
                pos = desired_pos

        adjusted_positions.append(pos)
        marker["position"] = pos

    if any(pos > 92 for pos in adjusted_positions):
        spacing = 84 / (len(timeline_markers) + 1)
        for i, marker in enumerate(timeline_markers):
            marker["position"] = 8 + spacing * (i + 1)
    else:
        for _i, marker in enumerate(timeline_markers):
            marker["position"] = min(marker["position"], 92)

    def calc_position(date):
        if date_range > 0:
            days_from_start = (date - min_date).days
            return (days_from_start / date_range) * 100
        return 50

    timeline_visual = html.Div(
        [
            html.Div(
                style={
                    "position": "absolute",
                    "top": "30px",
                    "left": "30px",
                    "right": "30px",
                    "height": "4px",
                    "backgroundColor": "#e9ecef",
                    "borderRadius": "2px",
                    "zIndex": "1",
                }
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                marker["label"],
                                style={
                                    "position": "absolute",
                                    "top": "10px",
                                    "left": "50%",
                                    "transform": "translateX(-50%)",
                                    "fontSize": "0.75rem",
                                    "fontWeight": "600",
                                    "color": marker["color"],
                                    "whiteSpace": "nowrap",
                                    "zIndex": "3",
                                },
                            ),
                            html.Div(
                                style={
                                    "position": "absolute",
                                    "top": "29px",
                                    "left": "50%",
                                    "transform": "translateX(-50%)",
                                    "width": "8px",
                                    "height": "8px",
                                    "borderRadius": "50%",
                                    "backgroundColor": marker["color"],
                                    "border": "2px solid white",
                                    "zIndex": "3",
                                }
                            ),
                            html.Div(
                                html.I(
                                    className=f"fas {marker['icon']}",
                                    style={"fontSize": "0.85rem"},
                                ),
                                style={
                                    "position": "absolute",
                                    "top": "36px",
                                    "left": "50%",
                                    "transform": "translateX(-50%)",
                                    "color": marker["color"],
                                    "zIndex": "3",
                                },
                            ),
                            html.Div(
                                marker["date"].strftime("%Y-%m-%d"),
                                style={
                                    "position": "absolute",
                                    "top": "55px",
                                    "left": "50%",
                                    "transform": "translateX(-50%)",
                                    "fontSize": "0.7rem",
                                    "color": "#6c757d",
                                    "whiteSpace": "nowrap",
                                    "zIndex": "3",
                                },
                            ),
                        ],
                        style={
                            "position": "absolute",
                            "left": f"{marker['position']}%",
                            "top": "0",
                            "height": "100%",
                        },
                    )
                    for marker in timeline_markers
                ],
                style={
                    "position": "absolute",
                    "top": "0",
                    "left": "0",
                    "right": "0",
                    "height": "100%",
                },
            ),
        ],
        style={
            "position": "relative",
            "height": "90px",
            "margin": "20px 0",
        },
    )

    timeline_rows = [
        html.Tr(
            [
                html.Td(
                    [
                        html.I(
                            className="fas fa-play me-2", style={"color": "#6610f2"}
                        ),
                        "Budget Start",
                    ],
                    style={"width": "40%"},
                ),
                html.Td(start_date.strftime("%Y-%m-%d"), className="fw-bold"),
                html.Td(
                    f"{allocated_weeks:.0f} weeks allocated",
                    className="text-muted text-end",
                ),
            ]
        ),
        html.Tr(
            [
                html.Td(
                    [
                        html.I(
                            className="fas fa-calendar-day me-2",
                            style={"color": "#6f42c1"},
                        ),
                        "Today",
                    ]
                ),
                html.Td(
                    current_date.strftime("%Y-%m-%d"),
                    className="fw-bold",
                    style={"color": "#6f42c1"},
                ),
                html.Td(
                    f"{elapsed_weeks:.1f} weeks elapsed",
                    className="text-muted text-end",
                ),
            ],
            className="table-active",
        ),
        html.Tr(
            [
                html.Td(
                    [
                        html.I(
                            className="fas fa-flag-checkered me-2",
                            style={"color": "#d4a017"},
                        ),
                        "Baseline End",
                    ]
                ),
                html.Td(allocated_end.strftime("%Y-%m-%d"), className="fw-bold"),
                html.Td(
                    (
                        f"{abs(baseline_weeks_remaining):.1f} weeks "
                        f"{'remaining' if baseline_weeks_remaining > 0 else 'overdue'}"
                    ),
                    className="text-end",
                    style={
                        "color": "#198754"
                        if baseline_weeks_remaining > 0
                        else "#dc3545"
                    },
                ),
            ]
        ),
    ]

    if runway_end:
        runway_color = "#20c997" if runway_vs_baseline_weeks >= 0 else "#e83e8c"
        runway_text_color = "#198754" if runway_vs_baseline_weeks >= 0 else "#dc3545"
        timeline_rows.append(
            html.Tr(
                [
                    html.Td(
                        [
                            html.I(
                                className="fas fa-money-bill-wave me-2",
                                style={"color": runway_color},
                            ),
                            "Runway End",
                        ]
                    ),
                    html.Td(
                        runway_end.strftime("%Y-%m-%d"),
                        className="fw-bold",
                        style={"color": runway_text_color},
                    ),
                    html.Td(
                        f"{runway_vs_baseline_weeks:+.1f} weeks vs baseline",
                        className="text-end",
                        style={"color": runway_text_color},
                    ),
                ],
                style={"borderTop": "2px solid #dee2e6"},
            )
        )
    elif runway_end_str:
        timeline_rows.append(
            html.Tr(
                [
                    html.Td(
                        [
                            html.I(
                                className="fas fa-money-bill-wave text-secondary me-2"
                            ),
                            "Runway End",
                        ]
                    ),
                    html.Td(
                        runway_end_str,
                        className="text-secondary",
                        colSpan=2,
                        style={"fontStyle": "italic"},
                    ),
                ],
                style={"borderTop": "2px solid #dee2e6"},
            )
        )

    timeline_table = dbc.Table(
        html.Tbody(timeline_rows),
        bordered=False,
        hover=True,
        size="sm",
        className="mb-0",
    )

    card = dbc.Card(
        [
            create_metric_card_header(title="Budget Timeline"),
            dbc.CardBody(
                [timeline_visual, html.Hr(className="my-3"), timeline_table],
                className="p-3",
            ),
            _create_card_footer(
                "Key project milestones • Colors indicate schedule health",
                "fa-clock",
            ),
        ],
        id=card_id,
        className="metric-card metric-card-large mb-3 h-100",
    )

    return card
