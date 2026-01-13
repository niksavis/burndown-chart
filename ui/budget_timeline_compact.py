"""
Compact Budget Timeline Card - Horizontal visualization

Replaces create_budget_timeline_card() in budget_cards.py
Designed to be compact, show temporal relationships clearly,
and provide actionable insights at a glance.
"""

from typing import Any, Dict, Optional
import logging
import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)


def create_budget_timeline_card(
    baseline_data: Dict[str, Any],
    pert_forecast_weeks: Optional[float] = None,
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create compact Budget Timeline card with horizontal timeline visualization.

    Shows temporal relationships between all critical dates:
    - Purple filled bar: elapsed time (start → today)
    - Yellow outlined bar: remaining baseline time (today → baseline end)
    - Vertical markers: TODAY (blue), BASELINE (yellow), FORECAST (green), RUNWAY (green/red)
    - Compact metrics: elapsed, to baseline, runway gaps

    Args:
        baseline_data: Dict from get_budget_baseline_vs_actual()
        pert_forecast_weeks: Optional PERT forecast weeks for completion date
        card_id: Optional HTML ID for the card

    Returns:
        Compact Dash Bootstrap Card component

    Example:
        >>> card = create_budget_timeline_card(baseline_data, 15.0)
    """
    from datetime import datetime
    from ui.budget_cards import _create_card_footer

    # Extract dates
    start_date_str = baseline_data["baseline"]["start_date"]
    allocated_end_str = baseline_data["baseline"]["allocated_end_date"]
    runway_end_str = baseline_data["actual"]["runway_end_date"]

    # Parse dates
    try:
        start_date = datetime.fromisoformat(start_date_str)
        allocated_end = datetime.fromisoformat(allocated_end_str)
        current_date = datetime.now()

        # Parse runway end (handle special cases)
        if runway_end_str and runway_end_str not in [
            "N/A (no consumption)",
            "Over budget",
        ]:
            runway_end = datetime.fromisoformat(runway_end_str)
        else:
            runway_end = None

    except Exception as e:
        logger.error(f"Failed to parse timeline dates: {e}")
        # Return error card
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

    # Calculate timeline positions
    elapsed_weeks = baseline_data["actual"]["elapsed_weeks"]
    runway_vs_baseline_weeks = baseline_data["variance"]["runway_vs_baseline_weeks"]

    # Calculate weeks from start for each milestone
    weeks_elapsed = (current_date - start_date).days / 7.0
    weeks_to_baseline = (allocated_end - start_date).days / 7.0
    weeks_to_forecast = (
        weeks_elapsed + pert_forecast_weeks if pert_forecast_weeks else None
    )
    weeks_to_runway = (runway_end - start_date).days / 7.0 if runway_end else None

    # Determine timeline range
    timeline_dates = [weeks_elapsed, weeks_to_baseline]
    if weeks_to_forecast:
        timeline_dates.append(weeks_to_forecast)
    if weeks_to_runway:
        timeline_dates.append(weeks_to_runway)
    timeline_max = max(timeline_dates) * 1.05  # Add 5% padding

    # Helper to calculate position percentage
    def calc_pos(weeks: float) -> float:
        return (weeks / timeline_max * 100) if timeline_max > 0 else 0

    # Build compact horizontal timeline bar
    timeline_bar = html.Div(
        [
            # Elapsed portion (filled purple)
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
            # Baseline portion (outlined yellow)
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
            # TODAY marker
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
            # BASELINE marker
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
                # FORECAST marker (if available)
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
                # RUNWAY marker (if available)
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
                                className=f"fas fa-caret-up {'text-success' if weeks_to_runway > weeks_to_baseline else 'text-danger'}",
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

    # Compact metrics row
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

    # Build card
    card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div(
                    [
                        html.I(className="fas fa-timeline me-2"),
                        html.Span("Budget Timeline", className="fw-bold"),
                    ]
                )
            ),
            dbc.CardBody([timeline_bar, metrics_row], className="pb-3"),
            _create_card_footer(
                "Purple: elapsed • Yellow: baseline remaining • Green/Red: forecast/runway markers",
                "fa-clock",
            ),
        ],
        id=card_id,
        className="metric-card mb-3 h-100",
    )

    return card
