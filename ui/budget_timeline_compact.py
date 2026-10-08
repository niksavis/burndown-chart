import logging
from datetime import datetime
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui import budget_cards
from ui.styles import create_metric_card_header

logger = logging.getLogger(__name__)


def create_budget_timeline_card(
    baseline_data: dict[str, Any],
    pert_forecast_weeks: float | None = None,
    card_id: str | None = None,
) -> dbc.Card:

    def _fallback_card_footer(text: str, icon: str) -> dbc.CardFooter:
        return dbc.CardFooter(
            [html.I(className=f"fas {icon} me-1"), html.Span(text)],
            className="text-muted small",
        )

    _create_card_footer = getattr(
        budget_cards, "_create_card_footer", _fallback_card_footer
    )

    start_date_str = baseline_data["baseline"]["start_date"]
    allocated_end_str = baseline_data["baseline"]["allocated_end_date"]
    runway_end_str = baseline_data["actual"]["runway_end_date"]

    try:
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

    elapsed_weeks = baseline_data["actual"]["elapsed_weeks"]
    runway_vs_baseline_weeks = baseline_data["variance"]["runway_vs_baseline_weeks"]

    weeks_elapsed = (current_date - start_date).days / 7.0
    weeks_to_baseline = (allocated_end - start_date).days / 7.0
    weeks_to_forecast = (
        weeks_elapsed + pert_forecast_weeks if pert_forecast_weeks else None
    )
    weeks_to_runway = (runway_end - start_date).days / 7.0 if runway_end else None
    runway_caret_class = (
        "text-success"
        if weeks_to_runway is not None and weeks_to_runway > weeks_to_baseline
        else "text-danger"
    )

    timeline_dates = [weeks_elapsed, weeks_to_baseline]
    if weeks_to_forecast:
        timeline_dates.append(weeks_to_forecast)
    if weeks_to_runway:
        timeline_dates.append(weeks_to_runway)
    timeline_max = max(timeline_dates) * 1.05

    def calc_pos(weeks: float) -> float:
        return (weeks / timeline_max * 100) if timeline_max > 0 else 0

    timeline_bar = html.Div(
        [
            html.Div(
                style={
                    "position": "absolute",
                    "left": "0",
                    "width": f"{calc_pos(weeks_elapsed)}%",
                    "height": "12px",
                    "backgroundColor": "#6f42c1",
                    "borderRadius": "6px 0 0 6px",
                    "zIndex": "1",
                }
            ),
            html.Div(
                style={
                    "position": "absolute",
                    "left": f"{calc_pos(weeks_elapsed)}%",
                    "width": f"{calc_pos(weeks_to_baseline - weeks_elapsed)}%",
                    "height": "12px",
                    "backgroundColor": "transparent",
                    "border": "2px solid #ffc107",
                    "borderLeft": "none",
                    "borderRadius": "0 6px 6px 0",
                    "zIndex": "1",
                }
            ),
            html.Div(
                [
                    html.Div(
                        style={
                            "position": "absolute",
                            "top": "-8px",
                            "left": "-1px",
                            "width": "2px",
                            "height": "28px",
                            "backgroundColor": "#0d6efd",
                            "zIndex": "3",
                        }
                    ),
                    html.Div(
                        html.I(
                            className="fas fa-caret-down text-primary",
                            style={"fontSize": "1.2rem"},
                        ),
                        style={
                            "position": "absolute",
                            "top": "-28px",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "zIndex": "4",
                        },
                    ),
                    html.Div(
                        "TODAY",
                        style={
                            "position": "absolute",
                            "top": "-48px",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "fontSize": "0.7rem",
                            "fontWeight": "bold",
                            "color": "#0d6efd",
                            "whiteSpace": "nowrap",
                        },
                    ),
                ],
                style={
                    "position": "absolute",
                    "left": f"{calc_pos(weeks_elapsed)}%",
                    "top": "0",
                    "height": "100%",
                },
            ),
            html.Div(
                [
                    html.Div(
                        style={
                            "position": "absolute",
                            "top": "8px",
                            "left": "-1px",
                            "width": "2px",
                            "height": "20px",
                            "backgroundColor": "#ffc107",
                            "zIndex": "2",
                        }
                    ),
                    html.Div(
                        html.I(
                            className="fas fa-caret-up text-warning",
                            style={"fontSize": "1.2rem"},
                        ),
                        style={
                            "position": "absolute",
                            "top": "28px",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "zIndex": "4",
                        },
                    ),
                    html.Div(
                        "BASELINE",
                        style={
                            "position": "absolute",
                            "top": "40px",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "fontSize": "0.7rem",
                            "fontWeight": "bold",
                            "color": "#ffc107",
                            "whiteSpace": "nowrap",
                        },
                    ),
                ],
                style={
                    "position": "absolute",
                    "left": f"{calc_pos(weeks_to_baseline)}%",
                    "top": "0",
                    "height": "100%",
                },
            ),
        ]
        + (
            [
                html.Div(
                    [
                        html.Div(
                            style={
                                "position": "absolute",
                                "top": "-8px",
                                "left": "-1px",
                                "width": "2px",
                                "height": "28px",
                                "backgroundColor": "#198754",
                                "zIndex": "2",
                            }
                        ),
                        html.Div(
                            html.I(
                                className="fas fa-caret-down text-success",
                                style={"fontSize": "1rem"},
                            ),
                            style={
                                "position": "absolute",
                                "top": "-24px",
                                "left": "50%",
                                "transform": "translateX(-50%)",
                                "zIndex": "4",
                            },
                        ),
                        html.Div(
                            "FORECAST",
                            style={
                                "position": "absolute",
                                "top": "-44px",
                                "left": "50%",
                                "transform": "translateX(-50%)",
                                "fontSize": "0.65rem",
                                "fontWeight": "bold",
                                "color": "#198754",
                                "whiteSpace": "nowrap",
                            },
                        ),
                    ],
                    style={
                        "position": "absolute",
                        "left": f"{calc_pos(weeks_to_forecast)}%",
                        "top": "0",
                        "height": "100%",
                    },
                ),
            ]
            if weeks_to_forecast
            else []
        )
        + (
            [
                html.Div(
                    [
                        html.Div(
                            style={
                                "position": "absolute",
                                "top": "8px",
                                "left": "-1px",
                                "width": "2px",
                                "height": "20px",
                                "backgroundColor": "#198754"
                                if weeks_to_runway > weeks_to_baseline
                                else "#dc3545",
                                "zIndex": "2",
                            }
                        ),
                        html.Div(
                            html.I(
                                className=(f"fas fa-caret-up {runway_caret_class}"),
                                style={"fontSize": "1rem"},
                            ),
                            style={
                                "position": "absolute",
                                "top": "28px",
                                "left": "50%",
                                "transform": "translateX(-50%)",
                                "zIndex": "4",
                            },
                        ),
                        html.Div(
                            "RUNWAY",
                            style={
                                "position": "absolute",
                                "top": "40px",
                                "left": "50%",
                                "transform": "translateX(-50%)",
                                "fontSize": "0.65rem",
                                "fontWeight": "bold",
                                "color": "#198754"
                                if weeks_to_runway > weeks_to_baseline
                                else "#dc3545",
                                "whiteSpace": "nowrap",
                            },
                        ),
                    ],
                    style={
                        "position": "absolute",
                        "left": f"{calc_pos(weeks_to_runway)}%",
                        "top": "0",
                        "height": "100%",
                    },
                ),
            ]
            if weeks_to_runway
            else []
        ),
        style={
            "position": "relative",
            "height": "12px",
            "margin": "60px 20px 50px 20px",
            "backgroundColor": "#e9ecef",
            "borderRadius": "6px",
        },
        className="budget-timeline-bar",
    )

    baseline_weeks_remaining = (allocated_end - current_date).days / 7.0
    metrics_cols = [
        dbc.Col(
            [
                html.Small(
                    "Elapsed",
                    className="text-muted d-block text-center",
                    style={"fontSize": "0.7rem"},
                ),
                html.Strong(
                    f"{elapsed_weeks:.1f}w",
                    className="d-block text-center",
                    style={"fontSize": "0.9rem"},
                ),
            ],
            width="auto",
        ),
        dbc.Col(
            [
                html.Small(
                    "To Baseline",
                    className="text-muted d-block text-center",
                    style={"fontSize": "0.7rem"},
                ),
                html.Strong(
                    f"{baseline_weeks_remaining:+.1f}w",
                    className="d-block text-center",
                    style={
                        "fontSize": "0.9rem",
                        "color": "#198754"
                        if baseline_weeks_remaining > 0
                        else "#dc3545",
                    },
                ),
            ],
            width="auto",
        ),
    ]

    if weeks_to_forecast and weeks_to_runway:
        forecast_gap = weeks_to_runway - weeks_to_forecast
        metrics_cols.append(
            dbc.Col(
                [
                    html.Small(
                        "Runway vs Forecast",
                        className="text-muted d-block text-center",
                        style={"fontSize": "0.7rem"},
                    ),
                    html.Strong(
                        f"{forecast_gap:+.1f}w",
                        className="d-block text-center",
                        style={
                            "fontSize": "0.9rem",
                            "color": "#198754" if forecast_gap >= 0 else "#dc3545",
                        },
                    ),
                ],
                width="auto",
            )
        )

    if weeks_to_runway:
        metrics_cols.append(
            dbc.Col(
                [
                    html.Small(
                        "Runway vs Baseline",
                        className="text-muted d-block text-center",
                        style={"fontSize": "0.7rem"},
                    ),
                    html.Strong(
                        f"{runway_vs_baseline_weeks:+.1f}w",
                        className="d-block text-center",
                        style={
                            "fontSize": "0.9rem",
                            "color": "#198754"
                            if runway_vs_baseline_weeks >= 0
                            else "#dc3545",
                        },
                    ),
                ],
                width="auto",
            )
        )

    metrics_row = dbc.Row(metrics_cols, className="g-3 justify-content-center")

    card = dbc.Card(
        [
            create_metric_card_header(title="Budget Timeline"),
            dbc.CardBody([timeline_bar, metrics_row], className="pb-3"),
            _create_card_footer(
                (
                    "Purple: elapsed • Yellow: baseline remaining • "
                    "Green/Red: forecast/runway markers"
                ),
                "fa-clock",
            ),
        ],
        id=card_id,
        className="metric-card metric-card-large mb-3 h-100",
    )

    return card
