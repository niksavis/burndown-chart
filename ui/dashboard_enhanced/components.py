"""
Dashboard Enhanced - Visual Primitive Components

Provides sparkline bar charts and progress bars used across dashboard cards.
"""

from __future__ import annotations

from dash import html


def _create_sparkline_bars(
    data_series: list, color: str = "#0d6efd", height: int = 35
) -> html.Div:
    """Create sparkline bar chart."""
    if not data_series or len(data_series) == 0:
        return html.Div(
            "No data",
            className="text-muted text-center",
            style={
                "height": f"{height}px",
                "lineHeight": f"{height}px",
                "fontSize": "0.75rem",
            },
        )

    recent_data = list(data_series)[-10:]
    max_val = max(recent_data) if max(recent_data) > 0 else 1
    normalized = [v / max_val for v in recent_data]

    bars = []
    for i, norm_val in enumerate(normalized):
        bar_height = max(norm_val * height, 3)
        opacity = 0.4 + (i / len(normalized)) * 0.6

        bars.append(
            html.Div(
                style={
                    "width": "7px",
                    "height": f"{bar_height}px",
                    "backgroundColor": color,
                    "opacity": opacity,
                    "borderRadius": "2px",
                    "transition": "all 0.3s ease",
                },
                className="sparkline-bar",
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center",
        style={"height": f"{height}px", "gap": "3px"},
    )


def _create_progress_bar(
    completed: float, total: float, color: str = "#0d6efd"
) -> html.Div:
    """Create animated progress bar."""
    if total == 0:
        percent = 0.0
    else:
        percent = min((completed / total) * 100, 100)

    return html.Div(
        [
            html.Div(
                f"{percent:.0f}%",
                className="progress-bar fw-semibold",
                style={
                    "width": f"{percent}%",
                    "backgroundColor": color,
                    "transition": "width 1s ease",
                },
            ),
        ],
        className="progress",
        style={
            "height": "22px",
            "borderRadius": "11px",
            "backgroundColor": "#e9ecef",
            "boxShadow": "inset 0 1px 2px rgba(0,0,0,0.1)",
        },
    )
