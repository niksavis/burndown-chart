"""Active Work Timeline UI Components

This module provides UI components for the Active Work Timeline tab showing
active epics/features with recent activity (last 7 days + current week).

Follows Sprint Tracker pattern for consistent layout and behavior.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Dict


def create_active_work_timeline_tab() -> html.Div:
    """Create Active Work Timeline tab container.

    This is an empty placeholder - content is rendered dynamically
    by visualization callback following Sprint Tracker pattern.

    Returns:
        Empty div that will be populated by callback
    """
    return html.Div(id="active-work-timeline-tab-content", children=html.Div())


def create_no_epics_state() -> html.Div:
    """Create empty state when no active epics found.

    Returns:
        Div with informational message and setup instructions
    """
    return html.Div(
        [
            dbc.Container(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-project-diagram fa-4x text-muted mb-3"
                            ),
                            html.H4(
                                "No Active Epics Found", className="text-muted mb-3"
                            ),
                            html.P(
                                [
                                    "Active Work Timeline shows epics/features with recent activity. ",
                                    "No active work detected in the last 7 days.",
                                ],
                                className="text-muted",
                            ),
                            html.Hr(className="my-4"),
                            html.H6("Requirements:", className="text-muted mb-2"),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            "Configure ",
                                            html.Strong("Parent/Epic Link"),
                                            " field in Settings → Fields tab → General Fields",
                                        ]
                                    ),
                                    html.Li(
                                        "Issues must have parent epic/feature assigned"
                                    ),
                                    html.Li(
                                        "Issues must have activity in last 7 days or current week"
                                    ),
                                ],
                                className="text-muted text-start",
                                style={"maxWidth": "500px", "margin": "0 auto"},
                            ),
                        ],
                        className="d-flex flex-column align-items-center justify-content-center",
                        style={"minHeight": "400px"},
                    )
                ],
                className="container-fluid",
            )
        ],
        className="container-fluid",
    )


def create_epic_card(epic_data: Dict, show_points: bool = False) -> dbc.Card:
    """Create card for a single epic showing progress and metrics.

    Args:
        epic_data: Epic data from get_active_epics()
        show_points: Whether to show story points metrics

    Returns:
        Bootstrap card component with epic details and progress
    """
    epic_key = epic_data.get("epic_key", "Unknown")
    epic_summary = epic_data.get("epic_summary", "Unknown Epic")
    total_issues = epic_data.get("total_issues", 0)
    completed_issues = epic_data.get("completed_issues", 0)
    in_progress_issues = epic_data.get("in_progress_issues", 0)
    todo_issues = epic_data.get("todo_issues", 0)
    completion_pct = epic_data.get("completion_pct", 0.0)
    total_points = epic_data.get("total_points", 0.0)
    completed_points = epic_data.get("completed_points", 0.0)
    last_updated = epic_data.get("last_updated", "")

    # Progress bar color based on completion
    if completion_pct >= 80:
        progress_color = "success"
    elif completion_pct >= 50:
        progress_color = "info"
    elif completion_pct >= 20:
        progress_color = "warning"
    else:
        progress_color = "danger"

    # Format last updated
    last_updated_display = last_updated.split("T")[0] if last_updated else "Unknown"

    # Build card header with epic key and completion
    header = dbc.CardHeader(
        [
            html.Div(
                [
                    html.Span(
                        epic_key,
                        className="badge bg-primary me-2",
                        style={"fontSize": "0.9rem"},
                    ),
                    html.Span(
                        f"{completion_pct:.0f}% Complete",
                        className=f"badge bg-{progress_color}",
                        style={"fontSize": "0.8rem"},
                    ),
                ],
                className="d-flex justify-content-between align-items-center",
            )
        ]
    )

    # Build card body with metrics
    metrics_row = dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-tasks text-info me-2"),
                            html.Strong(f"{total_issues}"),
                            html.Span(" Total", className="text-muted ms-1"),
                        ],
                        className="mb-2",
                    ),
                ],
                xs=6,
                md=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-check-circle text-success me-2"),
                            html.Strong(f"{completed_issues}"),
                            html.Span(" Done", className="text-muted ms-1"),
                        ],
                        className="mb-2",
                    ),
                ],
                xs=6,
                md=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-spinner text-warning me-2"),
                            html.Strong(f"{in_progress_issues}"),
                            html.Span(" In Progress", className="text-muted ms-1"),
                        ],
                        className="mb-2",
                    ),
                ],
                xs=6,
                md=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-circle text-secondary me-2"),
                            html.Strong(f"{todo_issues}"),
                            html.Span(" To Do", className="text-muted ms-1"),
                        ],
                        className="mb-2",
                    ),
                ],
                xs=6,
                md=3,
            ),
        ],
        className="mb-3",
    )

    # Points row (if enabled)
    points_row = None
    if show_points and total_points > 0:
        points_row = dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.I(className="fas fa-chart-bar text-primary me-2"),
                                html.Strong(
                                    f"{completed_points:.0f} / {total_points:.0f}"
                                ),
                                html.Span(" Story Points", className="text-muted ms-1"),
                            ]
                        ),
                    ],
                    xs=12,
                ),
            ],
            className="mb-3",
        )

    # Progress bar
    progress_bar = dbc.Progress(
        value=completion_pct,
        color=progress_color,
        className="mb-2",
        style={"height": "20px"},
    )

    # Last updated footer
    footer = dbc.CardFooter(
        [
            html.Small(
                [
                    html.I(className="fas fa-clock text-muted me-1"),
                    f"Last updated: {last_updated_display}",
                ],
                className="text-muted",
            )
        ]
    )

    # Assemble card body
    body_children = [
        html.H5(epic_summary, className="card-title mb-3"),
        metrics_row,
    ]
    if points_row:
        body_children.append(points_row)
    body_children.append(progress_bar)

    return dbc.Card(
        [
            header,
            dbc.CardBody(body_children),
            footer,
        ],
        className="mb-3 shadow-sm",
    )


def create_timeline_controls(days_back: int = 7) -> html.Div:
    """Create controls for timeline filtering.

    Args:
        days_back: Number of days to look back (default: 7)

    Returns:
        Div with filter controls
    """
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(
                                "Activity Timeframe:", html_for="days-back-slider"
                            ),
                            dcc.Slider(
                                id="timeline-days-back-slider",
                                min=1,
                                max=30,
                                step=1,
                                value=days_back,
                                marks={
                                    1: "1d",
                                    7: "7d",
                                    14: "14d",
                                    21: "21d",
                                    30: "30d",
                                },
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": False,
                                },
                            ),
                        ],
                        xs=12,
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("\u00a0"),  # Spacer
                            dbc.Checklist(
                                options=[
                                    {
                                        "label": "Include entire current week",
                                        "value": "include_current_week",
                                    }
                                ],
                                value=["include_current_week"],
                                id="timeline-include-week-checkbox",
                                switch=True,
                            ),
                        ],
                        xs=12,
                        md=6,
                    ),
                ],
                className="g-3",
            )
        ],
        className="mb-4 p-3 bg-light rounded",
    )
