from __future__ import annotations

from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from configuration import COLOR_PALETTE
from configuration.settings import PROJECT_HELP_TEXTS
from ui.styles import create_metric_card_header
from ui.tooltip_utils import create_info_tooltip


def create_project_summary_card(
    statistics_df, settings, pert_data=None, show_points=True
) -> dbc.Card:

    try:
        statistics_df = (
            statistics_df.copy() if not statistics_df.empty else pd.DataFrame()
        )

        if not statistics_df.empty and "date" in statistics_df.columns:
            statistics_df["date"] = pd.to_datetime(
                statistics_df["date"], format="mixed", errors="coerce"
            )

        if not statistics_df.empty:
            recent_df = statistics_df.tail(10).copy()
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year  # type: ignore[attr-defined]

            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"completed_items": "sum", "completed_points": "sum"})
                .reset_index()
            )

            avg_weekly_items = weekly_data["completed_items"].mean()
            avg_weekly_points = weekly_data["completed_points"].mean()
        else:
            avg_weekly_items = 0
            avg_weekly_points = 0

        deadline_date = settings.get("deadline")
        deadline_obj = None
        if deadline_date:
            deadline_str = deadline_date
            try:
                deadline_obj = datetime.strptime(deadline_date, "%Y-%m-%d")
                days_to_deadline = (deadline_obj - datetime.now()).days
            except ValueError, TypeError:
                days_to_deadline = None
        else:
            deadline_str = "Not set"
            days_to_deadline = None

        if pert_data:
            try:
                pert_time_items = pert_data.get("pert_time_items")
                pert_time_points = pert_data.get("pert_time_points")

                if pert_time_items is None and pert_time_points is None:
                    pert_info_content = html.Div(
                        "Forecast available after data processing",
                        className="text-muted text-center py-2",
                        style={"fontSize": "1rem"},
                    )
                else:
                    current_date = datetime.now()

                    if pert_time_items is not None:
                        items_completion_date = current_date + timedelta(
                            days=pert_time_items
                        )
                        items_completion_str = items_completion_date.strftime(
                            "%Y-%m-%d"
                        )
                        items_days = round(pert_time_items)
                        items_weeks = round(pert_time_items / 7, 1)
                    else:
                        items_completion_str = "Unknown"
                        items_days = "--"
                        items_weeks = "--"

                    if pert_time_points is not None:
                        points_completion_date = current_date + timedelta(
                            days=pert_time_points
                        )
                        points_completion_str = points_completion_date.strftime(
                            "%Y-%m-%d"
                        )
                        points_days = round(pert_time_points)
                        points_weeks = round(pert_time_points / 7, 1)
                        points_duration_text = f"{points_days}d ({points_weeks}w)"
                    else:
                        points_completion_str = "Unknown"
                        points_days = "--"
                        points_weeks = "--"
                        points_duration_text = "--"

                    pert_info_content = html.Div(
                        [
                            html.H6(
                                [
                                    "Project Completion Forecast",
                                    create_info_tooltip(
                                        id_suffix="project-completion-forecast",
                                        help_text=PROJECT_HELP_TEXTS[
                                            "completion_timeline"
                                        ],
                                    ),
                                ],
                                className=(
                                    "legacy-section-title border-bottom pb-1 mb-3"
                                ),
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                            "fontSize": "1rem",
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Items Completion:",
                                                        style={
                                                            "fontSize": "0.95rem",
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                    create_info_tooltip(
                                                        id_suffix="items-completion-forecast",
                                                        help_text=PROJECT_HELP_TEXTS[
                                                            "completion_timeline"
                                                        ],
                                                    ),
                                                ],
                                                className="mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        f"{items_completion_str}",
                                                        className="fw-bold",
                                                        style={
                                                            "fontSize": "1rem",
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                        },
                                                    ),
                                                ],
                                                className="ms-3 mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        (
                                                            f"{items_days} days "
                                                            f"({items_weeks} weeks)"
                                                        ),
                                                        style={"fontSize": "0.9rem"},
                                                    ),
                                                ],
                                                className="ms-3",
                                            ),
                                        ],
                                        width=6 if show_points else 12,
                                        className="px-2",
                                    ),
                                ]
                                + (
                                    [
                                        dbc.Col(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className=(
                                                                "fas fa-chart-line me-1"
                                                            ),
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ],
                                                                "fontSize": "1rem",
                                                            },
                                                        ),
                                                        html.Span(
                                                            "Points Completion:",
                                                            style={
                                                                "fontSize": "0.95rem",
                                                                "fontWeight": "bold",
                                                            },
                                                        ),
                                                        create_info_tooltip(
                                                            id_suffix="points-completion-forecast",
                                                            help_text=PROJECT_HELP_TEXTS[
                                                                "completion_timeline"
                                                            ],
                                                        ),
                                                    ],
                                                    className="mb-1",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            f"{points_completion_str}",
                                                            className="fw-bold",
                                                            style={
                                                                "fontSize": "1rem",
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ],
                                                            },
                                                        ),
                                                    ],
                                                    className="ms-3 mb-1",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            points_duration_text,
                                                            style={
                                                                "fontSize": "0.9rem"
                                                            },
                                                        ),
                                                    ],
                                                    className="ms-3",
                                                ),
                                            ],
                                            width=6,
                                            className="px-2",
                                        ),
                                    ]
                                    if show_points
                                    else []
                                ),
                                className="mb-4",
                            ),
                            html.H6(
                                [
                                    "Weekly Velocity",
                                    create_info_tooltip(
                                        id_suffix="weekly-velocity-summary",
                                        help_text=PROJECT_HELP_TEXTS["weekly_averages"],
                                    ),
                                ],
                                className=(
                                    "legacy-section-title border-bottom pb-1 mb-3"
                                ),
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                            "fontSize": "1rem",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f"{float(avg_weekly_items):.2f}",
                                                        className="fw-bold",
                                                        style={
                                                            "fontSize": "1.1rem",
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                        },
                                                    ),
                                                    html.Small(
                                                        " items/week",
                                                        style={"fontSize": "0.9rem"},
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                        ],
                                        width=6 if show_points else 12,
                                        className="px-2",
                                    ),
                                ]
                                + (
                                    [
                                        dbc.Col(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className=(
                                                                "fas fa-chart-line me-1"
                                                            ),
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ],
                                                                "fontSize": "1rem",
                                                            },
                                                        ),
                                                        html.Span(
                                                            f"{float(avg_weekly_points):.1f}",
                                                            className="fw-bold",
                                                            style={
                                                                "fontSize": "1.1rem",
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ],
                                                            },
                                                        ),
                                                        html.Small(
                                                            " points/week",
                                                            style={
                                                                "fontSize": "0.9rem"
                                                            },
                                                        ),
                                                    ],
                                                    className="mb-2",
                                                ),
                                            ],
                                            width=6,
                                            className="px-2",
                                        ),
                                    ]
                                    if show_points
                                    else []
                                ),
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className=(
                                                    "fas fa-calendar-alt "
                                                    "me-1 text-secondary"
                                                ),
                                                style={"fontSize": "1rem"},
                                            ),
                                            html.Span(
                                                "Deadline: ",
                                                style={
                                                    "fontSize": "0.95rem",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            html.Span(
                                                deadline_str,
                                                style={"fontSize": "0.95rem"},
                                            ),
                                            html.Span(
                                                f" ({days_to_deadline} days remaining)"
                                                if days_to_deadline is not None
                                                else "",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "marginLeft": "8px",
                                                },
                                            ),
                                        ],
                                        className="mt-2",
                                    ),
                                ]
                            )
                            if deadline_date
                            else html.Div(),
                        ],
                        className="mb-2",
                    )
            except Exception as pert_error:
                pert_info_content = html.P(
                    f"Error: {str(pert_error)}",
                    className="text-danger p-2",
                    style={"fontSize": "1rem"},
                )
        else:
            pert_info_content = html.Div(
                "Project forecast will display here once data is available",
                className="text-muted text-center py-3",
                style={"fontSize": "1rem"},
            )

        return dbc.Card(
            [
                create_metric_card_header(
                    title="Project Dashboard",
                    tooltip_text="Project analysis based on your historical data.",
                    tooltip_id="project-dashboard",
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            pert_info_content,
                            id="project-dashboard-pert-content",
                            className="pt-1 pb-2",
                        ),
                    ],
                    className="p-3",
                ),
            ],
            className="mb-3 shadow-sm h-100",
        )
    except Exception as e:
        return dbc.Card(
            [
                create_metric_card_header(
                    title="Project Dashboard",
                ),
                dbc.CardBody(
                    [
                        html.P(
                            "Unable to display project information. "
                            "Please ensure you have valid project data.",
                            className="text-danger mb-1",
                            style={"fontSize": "1rem"},
                        ),
                        html.Small(f"Error: {str(e)}", className="text-muted"),
                    ],
                    className="p-3",
                ),
            ],
            className="mb-3 shadow-sm h-100",
        )
