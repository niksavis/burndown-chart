"""PERT Project Overview Components

Components for the project overview and deadline sections.
"""

from dash import html

from configuration import COLOR_PALETTE
from configuration.settings import PROJECT_HELP_TEXTS
from ui.tooltip_utils import create_info_tooltip


def _create_project_overview_section(
    items_percentage,
    points_percentage,
    completed_items,
    completed_points,
    actual_total_items,
    actual_total_points,
    total_items,
    remaining_points,
    similar_percentages=False,
    show_points=True,
):
    """
    Create the project overview section with progress bars.

    Args:
        items_percentage: Percentage of items completed
        points_percentage: Percentage of points completed
        completed_items: Number of completed items
        completed_points: Number of completed points
        actual_total_items: Total items (completed + remaining)
        actual_total_points: Total points (completed + remaining)
        total_items: Number of remaining items
        remaining_points: Number of remaining points
        similar_percentages: Whether items and points percentages are similar
        show_points: Whether points tracking is enabled

    Returns:
        dash.html.Div: Project overview section
    """
    return html.Div(
        [
            # Project progress section
            html.Div(
                [
                    # Combined progress for similar percentages
                    html.Div(
                        [
                            html.Div(
                                className="progress-container",
                                children=[
                                    html.Div(
                                        className="progress-bar bg-primary",
                                        style={
                                            "width": f"{items_percentage}%",
                                            "height": "100%",
                                            "transition": "width 1s ease",
                                        },
                                    ),
                                    html.Span(
                                        [
                                            f"{items_percentage}% Complete",
                                            create_info_tooltip(
                                                "combined-completion-percentage",
                                                "Percentage of total work completed "
                                                "based on historical progress data. "
                                                "Items vs Points comparison shows "
                                                "estimation accuracy.",
                                            ),
                                        ],
                                        className=(
                                            "progress-label dark-text"
                                            if items_percentage > 40
                                            else "progress-label light-text"
                                        ),
                                    ),
                                ],
                            ),
                            html.Div(
                                [
                                    html.Small(
                                        [
                                            html.Span(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    html.Strong(f"{completed_items}"),
                                                    f" of {actual_total_items} items",
                                                    create_info_tooltip(
                                                        id_suffix="items-progress-combined",
                                                        help_text=PROJECT_HELP_TEXTS[
                                                            "items_vs_points"
                                                        ],
                                                    ),
                                                ],
                                                className="me-3",
                                            ),
                                        ]
                                        + (
                                            [
                                                html.Span(
                                                    [
                                                        html.I(
                                                            className=(
                                                                "fas fa-chart-line me-1"
                                                            ),
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ]
                                                            },
                                                        ),
                                                        html.Strong(
                                                            f"{completed_points:.1f}"
                                                        ),
                                                        " of ",
                                                        f"{actual_total_points:.1f}",
                                                        " points",
                                                        create_info_tooltip(
                                                            "points-progress-combined",
                                                            "Comparison between "
                                                            "item-based and "
                                                            "point-based progress "
                                                            "tracking. "
                                                            "Similar percentages "
                                                            "indicate consistent "
                                                            "estimation accuracy.",
                                                        ),
                                                    ]
                                                ),
                                            ]
                                            if show_points
                                            else []
                                        ),
                                        className="text-muted mt-2 d-block",
                                    ),
                                ],
                                className="d-flex justify-content-center",
                            ),
                        ],
                        style={"display": "block" if similar_percentages else "none"},
                        className="mb-3",
                    ),
                    # Separate progress bars for different percentages
                    html.Div(
                        [
                            # Items progress
                            html.Div(
                                [
                                    html.Div(
                                        className=(
                                            "d-flex justify-content-between "
                                            "align-items-center mb-1"
                                        ),
                                        children=[
                                            html.Small(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    "Items Progress",
                                                    create_info_tooltip(
                                                        "items-progress-separate",
                                                        "Progress tracking by "
                                                        "item count. "
                                                        "Shows (Completed Items ÷ "
                                                        "Total Items) × 100%",
                                                    ),
                                                ],
                                                className="fw-medium",
                                            ),
                                            html.Small(
                                                [
                                                    f"{items_percentage}% Complete",
                                                    create_info_tooltip(
                                                        "items-completion-separate",
                                                        "Percentage completion "
                                                        "based on "
                                                        "item count progress tracking",
                                                    ),
                                                ],
                                                className="text-muted",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="progress",
                                        style={
                                            "height": "16px",
                                            "borderRadius": "4px",
                                            "overflow": "hidden",
                                            "boxShadow": (
                                                "inset 0 1px 2px rgba(0,0,0,.1)"
                                            ),
                                        },
                                        children=[
                                            html.Div(
                                                className="progress-bar bg-info",
                                                style={
                                                    "width": f"{items_percentage}%",
                                                    "height": "100%",
                                                    "transition": "width 1s ease",
                                                },
                                            ),
                                        ],
                                    ),
                                    html.Small(
                                        f"{completed_items} of "
                                        f"{actual_total_items} items "
                                        f"({total_items} remaining)",
                                        className="text-muted mt-1 d-block",
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ]
                        + (
                            [
                                # Points progress shown when tracking is enabled.
                                html.Div(
                                    [
                                        html.Div(
                                            className=(
                                                "d-flex justify-content-between "
                                                "align-items-center mb-1"
                                            ),
                                            children=[
                                                html.Small(
                                                    [
                                                        html.I(
                                                            className=(
                                                                "fas fa-chart-line me-1"
                                                            ),
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ]
                                                            },
                                                        ),
                                                        "Points Progress",
                                                        create_info_tooltip(
                                                            id_suffix="points-progress-separate",
                                                            help_text=PROJECT_HELP_TEXTS[
                                                                "completion_percentage"
                                                            ],
                                                        ),
                                                    ],
                                                    className="fw-medium",
                                                ),
                                                html.Small(
                                                    [
                                                        f"{points_percentage}%",
                                                        " Complete",
                                                        create_info_tooltip(
                                                            id_suffix="points-completion-separate",
                                                            help_text=PROJECT_HELP_TEXTS[
                                                                "completion_percentage"
                                                            ],
                                                        ),
                                                    ],
                                                    className="text-muted",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="progress",
                                            style={
                                                "height": "16px",
                                                "borderRadius": "4px",
                                                "overflow": "hidden",
                                                "boxShadow": (
                                                    "inset 0 1px 2px rgba(0,0,0,.1)"
                                                ),
                                            },
                                            children=[
                                                html.Div(
                                                    className="progress-bar bg-warning",
                                                    style={
                                                        "width": (
                                                            f"{points_percentage}%"
                                                        ),
                                                        "height": "100%",
                                                        "transition": "width 1s ease",
                                                    },
                                                ),
                                            ],
                                        ),
                                        html.Small(
                                            f"{completed_points:.1f} of "
                                            f"{actual_total_points:.1f} points "
                                            f"({remaining_points:.1f} remaining)",
                                            className="text-muted mt-1 d-block",
                                        ),
                                    ],
                                ),
                            ]
                            if show_points
                            else []
                        ),
                        style={
                            "display": "block" if not similar_percentages else "none"
                        },
                        className="mb-3",
                    ),
                ],
                className="mb-4",
            )
        ]
    )


def _create_deadline_section(deadline_date_str, days_to_deadline):
    """
    Create the project deadline visualization section.

    Args:
        deadline_date_str: Formatted deadline date
        days_to_deadline: Days remaining until deadline

    Returns:
        dash.html.Div: Deadline visualization section
    """
    deadline_pressure_percent = max(
        5,
        min(100, (100 - (days_to_deadline / (days_to_deadline + 30) * 100))),
    )

    return html.Div(
        [
            html.Div(
                className="d-flex align-items-center mb-2",
                children=[
                    html.I(
                        className="fas fa-calendar-day fs-3 me-3",
                        style={"color": COLOR_PALETTE["deadline"]},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Project Deadline",
                                className="text-muted small",
                            ),
                            html.Div(
                                deadline_date_str,
                                className="fs-5 fw-bold",
                            ),
                        ]
                    ),
                ],
            ),
            # Days remaining visualization
            html.Div(
                [
                    html.Div(
                        className="d-flex justify-content-between align-items-center",
                        children=[
                            html.Small("Today", className="text-muted"),
                            html.Small(
                                "Deadline",
                                className="text-muted",
                            ),
                        ],
                    ),
                    html.Div(
                        className="progress mt-1 mb-1",
                        style={
                            "height": "8px",
                            "borderRadius": "4px",
                        },
                        children=[
                            html.Div(
                                className="progress-bar bg-danger",
                                style={
                                    "width": f"{deadline_pressure_percent}%",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        html.Strong(
                            f"{days_to_deadline} days remaining",
                            style={
                                "color": "green"
                                if days_to_deadline > 30
                                else "orange"
                                if days_to_deadline > 14
                                else "red"
                            },
                        ),
                        className="text-center mt-1",
                    ),
                ],
                className="mt-2",
            ),
        ],
        className="p-3 border rounded",
        style={
            "background": (
                "linear-gradient(to bottom, rgba(220, 53, 69, 0.05), "
                "rgba(255, 255, 255, 1))"
            ),
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
        },
    )
