"""Legacy project summary/dashboard cards (deprecated).

WARNING: This module contains legacy card functions that are deprecated.
Avoid using these for new features. Use atomic card builders instead
(see ui.cards.atomic_cards, ui.cards.metric_cards).

DEPRECATION NOTICE:
These cards predate the unified dashboard design (Feature 010 - Bug Analysis Dashboard).
They remain for backward compatibility but should be migrated to use:
- create_unified_metric_card() for individual metrics
- create_unified_metric_row() for metric groups
- Standardized design tokens from ui.style_constants

Functions:
    create_project_summary_card: Legacy project dashboard (deprecated)
"""

from __future__ import annotations

from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from configuration import COLOR_PALETTE
from configuration.settings import PROJECT_HELP_TEXTS
from ui.tooltip_utils import create_info_tooltip


def create_project_summary_card(
    statistics_df, settings, pert_data=None, show_points=True
) -> dbc.Card:
    """
    [DEPRECATED] Create a card with project dashboard information optimized for side-by-side layout.

    WARNING: This function is deprecated. For new features, use the unified metric card
    pattern from ui.cards.metric_cards.create_unified_metric_card() instead.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings
        pert_data: Dictionary containing PERT analysis data (optional)
        show_points: Whether points tracking is enabled

    Returns:
        A Dash card component with project dashboard information
    """
    try:
        # Make a copy of statistics_df to avoid modifying the original
        statistics_df = (
            statistics_df.copy() if not statistics_df.empty else pd.DataFrame()
        )

        # Convert 'date' column to datetime right at the beginning
        if not statistics_df.empty and "date" in statistics_df.columns:
            statistics_df["date"] = pd.to_datetime(
                statistics_df["date"], format="mixed", errors="coerce"
            )

        # Calculate values needed for the dashboard
        if not statistics_df.empty:
            # Add week and year columns
            recent_df = statistics_df.tail(10).copy()
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year  # type: ignore[attr-defined]

            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"completed_items": "sum", "completed_points": "sum"})
                .reset_index()
            )

            # Calculate metrics needed for PERT table
            avg_weekly_items = weekly_data["completed_items"].mean()
            avg_weekly_points = weekly_data["completed_points"].mean()
        else:
            avg_weekly_items = 0
            avg_weekly_points = 0

        # Format deadline string for display
        deadline_date = settings.get("deadline")
        deadline_obj = None
        if deadline_date:
            deadline_str = deadline_date
            try:
                deadline_obj = datetime.strptime(deadline_date, "%Y-%m-%d")
                days_to_deadline = (deadline_obj - datetime.now()).days
            except (ValueError, TypeError):
                days_to_deadline = None
        else:
            deadline_str = "Not set"
            days_to_deadline = None

        # Create the pert_info content
        if pert_data:
            try:
                pert_time_items = pert_data.get("pert_time_items")
                pert_time_points = pert_data.get("pert_time_points")

                # If both PERT values are None, provide a placeholder message
                if pert_time_items is None and pert_time_points is None:
                    pert_info_content = html.Div(
                        "Forecast available after data processing",
                        className="text-muted text-center py-2",
                        style={"fontSize": "1rem"},
                    )
                else:
                    # Format PERT data for compact display
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
                    else:
                        points_completion_str = "Unknown"
                        points_days = "--"
                        points_weeks = "--"

                    # Create compact PERT info content with optimized spacing
                    pert_info_content = html.Div(
                        [
                            # Title
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
                                className="border-bottom pb-1 mb-3",
                                style={"fontSize": "1.1rem", "fontWeight": "bold"},
                            ),
                            # PERT Forecast in compact table format
                            dbc.Row(
                                [
                                    # Items Forecast Column
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
                                                        f"{items_days} days ({items_weeks} weeks)",
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
                                        # Points Forecast Column - only show if points tracking is enabled
                                        dbc.Col(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-1",
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
                                                            f"{points_days} days ({points_weeks} weeks)",
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
                                className="mb-4",  # Increased bottom margin for better spacing
                            ),
                            # Weekly velocity section
                            html.H6(
                                [
                                    "Weekly Velocity",
                                    create_info_tooltip(
                                        id_suffix="weekly-velocity-summary",
                                        help_text=PROJECT_HELP_TEXTS["weekly_averages"],
                                    ),
                                ],
                                className="border-bottom pb-1 mb-3",
                                style={"fontSize": "1.1rem", "fontWeight": "bold"},
                            ),
                            dbc.Row(
                                [
                                    # Items velocity
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
                                        # Points velocity - only show if points tracking is enabled
                                        dbc.Col(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-1",
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
                                className="mb-3",  # Added bottom margin to prevent overlap
                            ),
                            # Deadline section if available
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-calendar-alt me-1 text-secondary",
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
                        className="mb-2",  # Added bottom margin to prevent overlap with card border
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
                dbc.CardHeader(
                    [
                        html.H4(
                            "Project Dashboard",
                            className="d-inline",
                        ),
                        create_info_tooltip(
                            "project-dashboard",
                            "Project analysis based on your historical data.",
                        ),
                    ],
                    className="py-2",
                ),
                dbc.CardBody(
                    [
                        # The content is directly placed here without any header or section dividers
                        html.Div(
                            pert_info_content,
                            id="project-dashboard-pert-content",
                            className="pt-1 pb-2",  # Added padding at top and bottom
                        ),
                    ],
                    className="p-3",  # Increased padding for better spacing
                ),
            ],
            className="mb-3 shadow-sm h-100",
        )
    except Exception as e:
        # Fallback card in case of errors
        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H4(
                        "Project Dashboard",
                        className="d-inline",
                        style={"fontSize": "1.4rem"},  # Increased heading size
                    )
                ),
                dbc.CardBody(
                    [
                        html.P(
                            "Unable to display project information. Please ensure you have valid project data.",
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
