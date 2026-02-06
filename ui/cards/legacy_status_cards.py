"""Legacy project status cards (deprecated).

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
    create_project_status_card: Legacy project status summary (deprecated)
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from configuration import COLOR_PALETTE
from ui.styles import create_metric_card_header
from ui.tooltip_utils import create_info_tooltip


def create_project_status_card(statistics_df, settings) -> dbc.Card:
    """
    [DEPRECATED] Create a comprehensive project status card with metrics and indicators.

    WARNING: This function is deprecated. For new features, use the unified metric card
    pattern from ui.cards.metric_cards.create_unified_metric_card() instead.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings

    Returns:
        A Dash card component for project status summary
    """
    try:
        # Extract key metrics from settings (these represent remaining work)
        remaining_items = settings.get("total_items", 0)
        remaining_points = settings.get("total_points", 0)

        # Calculate completed items and points from statistics
        completed_items = (
            int(statistics_df["completed_items"].sum())
            if not statistics_df.empty
            else 0
        )
        completed_points = (
            round(statistics_df["completed_points"].sum(), 1)
            if not statistics_df.empty
            else 0
        )

        # Calculate true project totals (completed + remaining)
        total_items = remaining_items + completed_items
        total_points = round(
            remaining_points + completed_points, 1
        )  # Round to 1 decimal place
        remaining_points = round(
            remaining_points, 1
        )  # Round remaining points to 1 decimal place

        # Calculate percentages based on true project totals
        items_percentage = (
            round((completed_items / total_items) * 100, 1) if total_items > 0 else 0
        )
        points_percentage = (
            round((completed_points / total_points) * 100, 1) if total_points > 0 else 0
        )

        # Calculate average weekly velocity and coefficient of variation (last 10 weeks)
        # Create a copy of the DataFrame to avoid SettingWithCopyWarning
        recent_df = statistics_df.copy() if not statistics_df.empty else pd.DataFrame()

        # Default values if no data is available
        avg_weekly_items = 0
        avg_weekly_points = 0
        stability_status = "Unknown"
        stability_color = "secondary"
        stability_icon = "fa-question-circle"

        # Convert to datetime to ensure proper week grouping
        if not recent_df.empty:
            # Use proper pandas assignment with .loc to avoid SettingWithCopyWarning
            recent_df.loc[:, "date"] = pd.to_datetime(
                recent_df["date"], format="mixed", errors="coerce"
            )

            # Add week and year columns
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year  # type: ignore[attr-defined]

            # Group by week to get weekly data
            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"completed_items": "sum", "completed_points": "sum"})
                .reset_index()
                .tail(10)  # Consider only the last 10 weeks
            )

            # Calculate average weekly velocity
            avg_weekly_items = weekly_data["completed_items"].mean()
            avg_weekly_points = weekly_data["completed_points"].mean()

            # Calculate standard deviation for coefficient of variation
            std_weekly_items = weekly_data["completed_items"].std()
            std_weekly_points = weekly_data["completed_points"].std()

            # Calculate coefficient of variation (CV = std/mean)
            cv_items = (
                (std_weekly_items / avg_weekly_items * 100)
                if avg_weekly_items > 0
                else 0
            )
            cv_points = (
                (std_weekly_points / avg_weekly_points * 100)
                if avg_weekly_points > 0
                else 0
            )

            # Count zero weeks and high weeks (outliers)
            zero_item_weeks = len(weekly_data[weekly_data["completed_items"] == 0])
            zero_point_weeks = len(weekly_data[weekly_data["completed_points"] == 0])
            high_item_weeks = len(
                weekly_data[weekly_data["completed_items"] > avg_weekly_items * 2]
            )
            high_point_weeks = len(
                weekly_data[weekly_data["completed_points"] > avg_weekly_points * 2]
            )

            # Calculate overall stability score (0-100)
            stability_score = max(
                0,
                100
                - cv_items * 0.5
                - cv_points * 0.5
                - zero_item_weeks * 10
                - zero_point_weeks * 10
                - high_item_weeks * 5
                - high_point_weeks * 5,
            )
            stability_score = min(100, max(0, stability_score))

            # Determine velocity consistency status
            if stability_score >= 80:
                stability_status = "Consistent"
                stability_color = "success"
                stability_icon = "fa-check-circle"
            elif stability_score >= 50:
                stability_status = "Moderate"
                stability_color = "warning"
                stability_icon = "fa-exclamation-circle"
            else:
                stability_status = "Variable"
                stability_color = "danger"
                stability_icon = "fa-times-circle"

        # Calculate days of data available
        if not statistics_df.empty:
            if "date" in statistics_df.columns:
                earliest_date = pd.to_datetime(
                    statistics_df["date"].min(), format="mixed", errors="coerce"
                )
                latest_date = pd.to_datetime(
                    statistics_df["date"].max(), format="mixed", errors="coerce"
                )
                days_of_data = (
                    (latest_date - earliest_date).days + 1
                    if earliest_date and latest_date
                    else 0
                )
            else:
                days_of_data = 0
        else:
            days_of_data = 0

        # Create the card component
        return dbc.Card(
            [
                create_metric_card_header(
                    title="Project Status Summary",
                    tooltip_text="Summary of your project's current progress and metrics.",
                    tooltip_id="project-status",
                ),
                dbc.CardBody(
                    [
                        # Project Completion Stats Row
                        dbc.Row(
                            [
                                # Items Completion
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                "Items Completion",
                                                create_info_tooltip(
                                                    "items-completion-status",
                                                    "Percentage of total work completed based on historical progress data. Items: (Completed Items ÷ Total Items) × 100%. Different percentages indicate varying complexity or estimation accuracy.",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"{items_percentage}%",
                                                    style={
                                                        "fontSize": "24px",
                                                        "fontWeight": "bold",
                                                        "color": COLOR_PALETTE["items"],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        f"Completed: {completed_items} of {total_items} items",
                                                    ],
                                                    className="text-muted small",
                                                ),
                                            ],
                                            className="text-center mb-2",
                                        ),
                                        # Progress bar for items
                                        dbc.Progress(
                                            value=items_percentage,
                                            color="info",
                                            className="mb-3",
                                            style={"height": "10px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                                # Points Completion
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                "Points Completion",
                                                create_info_tooltip(
                                                    "points-completion-status",
                                                    "Percentage of total work completed based on historical progress data. Points: (Completed Points ÷ Total Points) × 100%. Points typically reflect effort/complexity better than item count.",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"{points_percentage}%",
                                                    style={
                                                        "fontSize": "24px",
                                                        "fontWeight": "bold",
                                                        "color": COLOR_PALETTE[
                                                            "points"
                                                        ],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        f"Completed: {completed_points:.1f} of {total_points:.1f} points",
                                                    ],
                                                    className="text-muted small",
                                                ),
                                            ],
                                            className="text-center mb-2",
                                        ),
                                        # Progress bar for points
                                        dbc.Progress(
                                            value=points_percentage,
                                            color="warning",
                                            className="mb-3",
                                            style={"height": "10px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                            ],
                            className="mb-4",
                        ),
                        # Metrics Row
                        dbc.Row(
                            [
                                # Weekly Averages
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                "Weekly Averages",
                                                create_info_tooltip(
                                                    "weekly-averages-status",
                                                    "Average completion rates over recent weeks, showing sustainable team velocity. These metrics help predict future performance and identify capacity changes.",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-tasks me-2",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "items"
                                                                ]
                                                            },
                                                        ),
                                                        f"{float(avg_weekly_items):.2f}",
                                                        html.Small(" items/week"),
                                                    ],
                                                    className="d-flex align-items-center mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-2",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ]
                                                            },
                                                        ),
                                                        f"{float(avg_weekly_points):.1f}",
                                                        html.Small(" points/week"),
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                                # Velocity Stability
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                "Velocity Stability",
                                                create_info_tooltip(
                                                    "velocity-stability-status",
                                                    "Measure of how consistent your team's weekly completion rates are. Stable: Low variation (predictable). Variable: High week-to-week changes (less predictable).",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                html.I(
                                                    className=f"fas {stability_icon} me-2",
                                                    style={
                                                        "color": f"var(--bs-{stability_color})"
                                                    },
                                                ),
                                                html.Span(
                                                    stability_status,
                                                    style={
                                                        "color": f"var(--bs-{stability_color})",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                            ],
                                            className="d-flex align-items-center ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                                # Dataset Info
                                dbc.Col(
                                    [
                                        html.H6("Dataset Info", className="mb-3"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-calendar-alt me-2 text-secondary"
                                                        ),
                                                        f"{days_of_data} days of data",
                                                    ],
                                                    className="d-flex align-items-center mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-table me-2 text-secondary"
                                                        ),
                                                        f"{len(statistics_df) if not statistics_df.empty else 0} data points",
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                            ],
                        ),
                    ],
                    className="py-4",
                ),
            ],
            className="mb-4 shadow-sm",
        )

    except Exception as e:
        # Return an error card if something goes wrong
        return dbc.Card(
            [
                create_metric_card_header(
                    title="Project Status Summary",
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-exclamation-triangle text-danger me-2"
                                ),
                                html.Span(
                                    "Unable to display project information. Please ensure you have valid project data.",
                                    className="text-danger",
                                ),
                            ],
                            className="d-flex align-items-center mb-2",
                        ),
                        html.Small(f"Error: {str(e)}", className="text-muted"),
                    ]
                ),
            ],
            className="mb-4 shadow-sm",
        )
