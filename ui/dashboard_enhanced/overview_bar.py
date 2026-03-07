"""
Dashboard Enhanced - Overview Bar Widget

Provides the compact top-level overview bar showing health, progress,
deadline, and success probability at a glance.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from ui.style_constants import COLOR_PALETTE


def _create_overview_bar(
    health: dict,
    completed_items: float,
    actual_total_items: float,
    progress_pct_text: str,
    days_to_deadline: float,
    deadline_str: str,
    items_probability: float,
) -> dbc.Card:
    """Build the compact overview bar card with key project metrics."""
    prob_color = (
        "#28a745"
        if items_probability >= 70
        else "#ffc107"
        if items_probability >= 40
        else "#dc3545"
    )

    return dbc.Card(
        dbc.CardBody(
            [
                # Top row: Main metrics (wraps on mobile)
                html.Div(
                    [
                        # Health Status
                        html.Div(
                            [
                                html.Span(
                                    health["overall"]["emoji"],
                                    style={
                                        "fontSize": "1.35rem",
                                        "marginRight": "0.4rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Health",
                                            className="text-muted d-block",
                                            style={
                                                "fontSize": "0.7rem",
                                                "lineHeight": "1",
                                            },
                                        ),
                                        html.Strong(
                                            health["overall"]["label"],
                                            style={
                                                "fontSize": "0.85rem",
                                                "color": health["overall"]["color"],
                                            },
                                        ),
                                    ],
                                ),
                            ],
                            className="d-flex align-items-center px-2 py-1",
                            style={"minWidth": "100px"},
                        ),
                        # Divider (hidden on mobile)
                        html.Div(
                            style={
                                "width": "1px",
                                "height": "35px",
                                "backgroundColor": "#dee2e6",
                                "margin": "0 0.5rem",
                            },
                            className="d-none d-md-block",
                        ),
                        # Progress
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-tasks",
                                    style={
                                        "fontSize": "1.35rem",
                                        "color": COLOR_PALETTE["items"],
                                        "marginRight": "0.4rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Progress",
                                            className="text-muted d-block",
                                            style={
                                                "fontSize": "0.7rem",
                                                "lineHeight": "1",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Strong(
                                                    f"{completed_items:,}",
                                                    style={
                                                        "fontSize": "0.85rem",
                                                        "color": COLOR_PALETTE["items"],
                                                    },
                                                ),
                                                html.Span(
                                                    f"/{actual_total_items:,}",
                                                    className="text-muted",
                                                    style={"fontSize": "0.8rem"},
                                                ),
                                                html.Span(
                                                    f" • {progress_pct_text}",
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "fontWeight": "600",
                                                        "color": COLOR_PALETTE["items"],
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            className="d-flex align-items-center px-2 py-1",
                            style={"minWidth": "140px"},
                        ),
                        # Divider (hidden on mobile)
                        html.Div(
                            style={
                                "width": "1px",
                                "height": "35px",
                                "backgroundColor": "#dee2e6",
                                "margin": "0 0.5rem",
                            },
                            className="d-none d-md-block",
                        ),
                        # Deadline
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-calendar-day",
                                    style={
                                        "fontSize": "1.35rem",
                                        "color": "#6610f2",
                                        "marginRight": "0.4rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Deadline",
                                            className="text-muted d-block",
                                            style={
                                                "fontSize": "0.7rem",
                                                "lineHeight": "1",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Strong(
                                                    pd.to_datetime(
                                                        deadline_str
                                                    ).strftime("%b %d"),
                                                    style={"fontSize": "0.85rem"},
                                                ),
                                                html.Span(
                                                    f" • {days_to_deadline}d",
                                                    className="text-muted",
                                                    style={"fontSize": "0.8rem"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            className="d-flex align-items-center px-2 py-1",
                            style={"minWidth": "120px"},
                        ),
                        # Divider (hidden on mobile)
                        html.Div(
                            style={
                                "width": "1px",
                                "height": "35px",
                                "backgroundColor": "#dee2e6",
                                "margin": "0 0.5rem",
                            },
                            className="d-none d-lg-block",
                        ),
                        # Success Probability
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-percentage",
                                    style={
                                        "fontSize": "1.35rem",
                                        "color": prob_color,
                                        "marginRight": "0.4rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Success",
                                            className="text-muted d-block",
                                            style={
                                                "fontSize": "0.7rem",
                                                "lineHeight": "1",
                                            },
                                        ),
                                        html.Strong(
                                            f"{items_probability:.0f}%",
                                            style={
                                                "fontSize": "0.95rem",
                                                "color": prob_color,
                                            },
                                        ),
                                    ],
                                ),
                            ],
                            className="d-flex align-items-center px-2 py-1",
                            style={"minWidth": "90px"},
                        ),
                    ],
                    className=(
                        "d-flex align-items-center flex-wrap justify-content-start"
                    ),
                    style={"gap": "0.25rem"},
                ),
                # Divider line (on mobile)
                html.Hr(className="my-2 d-md-none", style={"margin": "0.5rem 0"}),
                # Bottom row: Key Indicators (wraps on mobile)
                html.Div(
                    [
                        html.Span(
                            [
                                html.Span(
                                    f["icon"],
                                    className="me-1",
                                    style={"fontSize": "0.8rem"},
                                ),
                                html.Span(f["name"], style={"fontSize": "0.7rem"}),
                            ],
                            className="badge me-1 mb-1",
                            style={
                                "backgroundColor": "rgba(40, 167, 69, 0.15)"
                                if f["status"] == "good"
                                else "rgba(255, 193, 7, 0.2)"
                                if f["status"] == "warning"
                                else "rgba(220, 53, 69, 0.15)",
                                "border": (
                                    "1.5px solid #28a745"
                                    if f["status"] == "good"
                                    else "1.5px solid #d39e00"
                                    if f["status"] == "warning"
                                    else "1.5px solid #dc3545"
                                ),
                                "color": "#28a745"
                                if f["status"] == "good"
                                else "#856404"
                                if f["status"] == "warning"
                                else "#dc3545",
                                "fontWeight": "600",
                                "fontSize": "0.7rem",
                                "padding": "0.25rem 0.45rem",
                                "whiteSpace": "nowrap",
                            },
                        )
                        for f in health["factors"]
                    ],
                    className=(
                        "d-flex flex-wrap align-items-center "
                        "justify-content-center justify-content-md-start "
                        "pt-2 pt-md-0 mt-md-0"
                    ),
                    style={"gap": "0.2rem"},
                ),
            ],
            className="py-2 px-2",
        ),
        className="shadow-sm mb-3",
        style={"border": "none", "borderRadius": "8px"},
    )
