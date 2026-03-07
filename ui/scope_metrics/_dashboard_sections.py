"""Private section builder helpers for create_scope_metrics_dashboard."""

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from configuration import SCOPE_HELP_TEXTS
from ui.tooltip_utils import create_info_tooltip

from ._charts import create_cumulative_scope_chart, create_scope_growth_chart
from ._gauge import create_enhanced_stability_gauge


def _build_backlog_chart_section(
    weekly_growth_data: pd.DataFrame,
    baseline_items: float,
    baseline_points: float,
    show_points: bool,
) -> html.Div:
    """Build the cumulative backlog size over time chart section."""
    return html.Div(
        [
            html.Div(
                [
                    html.H5(
                        [
                            html.I(
                                className="fas fa-chart-area me-2 text-purple",
                            ),
                            "Backlog Size Over Time (Remaining Work)",
                            html.Span(" "),
                            create_info_tooltip(
                                "cumulative_scope_chart",
                                SCOPE_HELP_TEXTS["cumulative_chart"],
                            ),
                        ],
                        className="mb-3 mt-4",
                    ),
                    create_cumulative_scope_chart(
                        weekly_growth_data,
                        baseline_items,
                        baseline_points,
                        show_points,
                    ),
                ]
            )
        ],
        className="mb-3",
    )


def _build_throughput_section(
    items_throughput_ratio: float,
    points_throughput_ratio: float,
    total_created_items: float,
    total_completed_items: float,
    total_created_points: float,
    total_completed_points: float,
    show_points: bool,
) -> html.Div:
    """Build the scope change vs team throughput comparison section."""
    muted_small_class = "text-muted ms-1 text-size-sm"
    points_created_completed_label = (
        f" ({total_created_points} created vs {total_completed_points} completed)"
    )
    throughput_note = (
        "A ratio greater than 1.0 indicates scope is growing faster than "
        "the team can deliver. This may affect delivery timelines."
    )
    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-balance-scale me-2 text-purple",
                    ),
                    "Scope Change vs Team Throughput",
                    html.Span(" "),
                    create_info_tooltip(
                        "throughput_comparison",
                        SCOPE_HELP_TEXTS["throughput_ratio"],
                    ),
                ],
                className="mb-3 mt-4",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.P(
                            [
                                "Items: ",
                                html.Span(
                                    (
                                        "For every completed item, "
                                        f"{items_throughput_ratio:.2f} "
                                        "new items are being created"
                                    ),
                                    className=(
                                        "fw-medium text-danger"
                                        if items_throughput_ratio > 1
                                        else "fw-medium text-accent"
                                    ),
                                ),
                                html.Span(
                                    (
                                        f" ({total_created_items} created vs "
                                        f"{total_completed_items} completed)"
                                    ),
                                    className="text-muted ms-1 text-size-sm",
                                ),
                            ]
                        ),
                    ]
                    + (
                        [
                            html.P(
                                [
                                    "Points: ",
                                    html.Span(
                                        (
                                            "For every completed point, "
                                            f"{points_throughput_ratio:.2f} "
                                            "new points are being created"
                                        ),
                                        className=(
                                            "fw-medium text-danger"
                                            if points_throughput_ratio > 1
                                            else "fw-medium text-accent"
                                        ),
                                    ),
                                    html.Span(
                                        points_created_completed_label,
                                        className=muted_small_class,
                                    ),
                                ]
                            ),
                        ]
                        if show_points
                        else []
                    )
                    + [
                        html.P(
                            throughput_note,
                            className="text-muted small mb-0 mt-2 fst-italic",
                        ),
                    ]
                ),
                className="mb-3",
            ),
        ]
    )


def _build_growth_patterns_section(
    weekly_growth_data: pd.DataFrame,
    show_points: bool,
) -> html.Div:
    """Build the weekly scope growth chart and agile footnote section."""
    growth_patterns_note = (
        "Growth Patterns: Positive spikes show scope additions from new "
        "requirements or discoveries. Negative values indicate backlog "
        "refinement or completion focus."
    )
    return html.Div(
        [
            # Weekly Scope Growth Chart with Tooltip
            html.Div(
                [
                    html.Div(
                        [
                            html.H5(
                                [
                                    html.I(
                                        className="fas fa-chart-bar me-2 text-points",
                                    ),
                                    "Weekly Scope Growth Patterns",
                                    html.Span(" "),
                                    create_info_tooltip(
                                        "weekly_growth_chart",
                                        SCOPE_HELP_TEXTS["weekly_growth"],
                                    ),
                                ],
                                className="mb-3 mt-4",
                            ),
                            create_scope_growth_chart(weekly_growth_data, show_points),
                        ]
                    )
                ],
                className="mb-2",
            ),
            # Enhanced Footnote with Agile Context
            html.Div(
                className="text-muted fst-italic small text-center mb-5 pb-3",
                children=[
                    html.I(
                        className="fas fa-seedling me-1 text-muted",
                    ),
                    growth_patterns_note,
                ],
            ),
        ]
    )


def _build_adaptability_section(
    stability_index: dict,
    show_points: bool,
) -> html.Div:
    """Build the adaptability gauges and agile context footer section."""
    adaptability_points_help = (
        SCOPE_HELP_TEXTS["adaptability_index"]
        + " This version measures adaptability based on story points rather "
        "than item counts."
    )
    agile_context_intro = (
        "In agile projects, scope changes are normal and healthy—"
        "these metrics help you understand patterns, not problems. "
    )
    agile_context_detail = (
        "Lower stability values (0.3-0.6) indicate dynamic, evolving "
        "scope (typical for responsive agile teams). Higher values (0.7+) "
        "indicate more predictable, stable scope."
    )
    return html.Div(
        [
            # Adaptability section with title
            html.H5(
                [
                    html.I(className="fas fa-chart-pie me-2 text-accent"),
                    "Adaptability",
                ],
                className="mb-3 mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                [
                                                    "Items Adaptability Index ",
                                                    create_info_tooltip(
                                                        "adaptability_index",
                                                        SCOPE_HELP_TEXTS[
                                                            "adaptability_index"
                                                        ],
                                                    ),
                                                ],
                                                className="mb-3 text-center",
                                            ),
                                            create_enhanced_stability_gauge(
                                                stability_index["items_stability"],
                                                "",
                                                # Empty title since we have header above
                                                height=280,
                                                show_toolbar=False,
                                                # Hide toolbar for cleaner UI
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=12,
                        md=6,
                    ),
                ]
                + (
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H6(
                                                    [
                                                        "Points Adaptability Index ",
                                                        create_info_tooltip(
                                                            "points_adaptability_index",
                                                            adaptability_points_help,
                                                        ),
                                                    ],
                                                    className="mb-3 text-center",
                                                ),
                                                create_enhanced_stability_gauge(
                                                    stability_index["points_stability"],
                                                    "",
                                                    # Empty title (header above)
                                                    height=280,
                                                    show_toolbar=False,
                                                    # Hide toolbar for cleaner UI
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width=12,
                            md=6,
                        ),
                    ]
                    if show_points
                    else []
                ),
            ),
            # Enhanced Footer with Agile Context
            html.Div(
                className="text-muted fst-italic small text-center mt-3",
                children=[
                    html.I(
                        className="fas fa-lightbulb me-1",
                    ),
                    html.Strong("Agile Context: ", className="fw-semibold"),
                    agile_context_intro,
                    agile_context_detail,
                ],
            ),
        ]
    )
