"""
Tab Content Builders for Visualizations

This module contains functions for building tab content layouts
in the visualization callbacks.
"""

import logging

import pandas as pd
from dash import dcc, html

from callbacks.visualization_helpers.ui_builders import (
    create_trend_header_with_forecasts,
)
from configuration.chart_config import (
    get_burndown_chart_config,
    get_weekly_chart_config,
)
from data.persistence import load_unified_project_data
from data.schema import DEFAULT_SETTINGS
from data.scope_metrics import (
    calculate_scope_creep_rate,
    calculate_scope_stability_index,
    calculate_weekly_scope_growth,
)
from ui.scope_metrics import create_scope_metrics_dashboard

logger = logging.getLogger("burndown_chart")


def create_burndown_tab_content(
    df,
    items_trend: dict,
    points_trend: dict,
    burndown_fig,
    items_fig,
    points_fig,
    settings: dict,
    show_points: bool = True,
    has_points_data: bool = True,
):
    """
    Create content for the burndown tab with burndown, items, and points charts.

    Args:
        df: DataFrame with statistics data
        items_trend: Dictionary with items trend and forecast data
        points_trend: Dictionary with points trend and forecast data
        burndown_fig: Burndown chart figure
        items_fig: Weekly items chart figure
        points_fig: Weekly points chart figure (None if no data or disabled)
        settings: Settings dictionary
        show_points: Whether points tracking is enabled
        has_points_data: Whether points data exists in selected period

    Returns:
        html.Div: Burndown tab content with all three charts
    """
    chart_height = settings.get("chart_height", 700)

    # Build the content list starting with burndown chart
    content = [
        # Weekly trend indicators in a row
        html.Div(
            [
                # Items trend box
                create_trend_header_with_forecasts(
                    items_trend,
                    "Weekly Items Trend",
                    "fas fa-tasks",
                    "brand",
                ),
            ]
            + (
                [
                    # Points trend box - only show if points tracking is enabled
                    create_trend_header_with_forecasts(
                        points_trend,
                        "Weekly Items Trend",
                        "fas fa-chart-bar",
                        "points",
                    ),
                ]
                if show_points
                else []
            ),
            className="row mb-3",
        ),
        # Burndown chart with title
        html.H5(
            [
                html.I(className="fas fa-chart-line me-2 text-brand"),
                "Forecast Based On Historical Data",
            ],
            className="mb-3 mt-4",
        ),
        dcc.Graph(
            id="forecast-graph",
            figure=burndown_fig,
            config=get_burndown_chart_config(filename_prefix="burndown_chart"),  # type: ignore
            style={"height": f"{chart_height}px"},
        ),
    ]

    # Add Items per Week chart section
    content.extend(
        [
            # Items per Week section header (standardized H5 styling)
            html.H5(
                [
                    html.I(
                        className="fas fa-tasks me-2 text-brand",
                    ),
                    "Weekly Completed Items",
                ],
                className="mb-3 mt-4",
            ),
            # Items chart (trend header removed - already shown at top)
            dcc.Graph(
                id="items-chart",
                figure=items_fig,
                config=get_weekly_chart_config(filename_prefix="weekly_items"),  # type: ignore
                className="chart-height-700",
            ),
        ]
    )

    # Add Points per Week section
    content.extend(
        [
            # Points per Week section header (standardized H5 styling)
            html.H5(
                [
                    html.I(
                        className="fas fa-chart-bar me-2 text-points",
                    ),
                    "Weekly Completed Points",
                ],
                className="mb-3 mt-4",
            ),
        ]
    )

    # Determine which content to show for points section
    if not show_points:
        # Case 1: Points tracking disabled
        content.append(
            html.Div(
                [
                    html.I(className="fas fa-toggle-off fa-2x empty-state-icon mb-3"),
                    html.Div(
                        "Points Tracking Disabled",
                        className="empty-state-title mb-2",
                    ),
                    html.Small(
                        "Enable Points Tracking in Parameters panel "
                        "to view story points metrics.",
                        className="empty-state-lead empty-state-text",
                    ),
                ],
                className="empty-state-center",
            )
        )
    elif not has_points_data:
        # Case 2: Points tracking enabled but no data in period
        content.append(
            html.Div(
                [
                    html.I(className="fas fa-database fa-lg empty-state-icon mb-3"),
                    html.Div(
                        "No Points Data",
                        className="empty-state-title mb-2",
                    ),
                    html.Small(
                        "No story points data available in the selected time period. "
                        "Configure story points field in Settings or complete items "
                        "with point estimates.",
                        className="empty-state-lead empty-state-text",
                    ),
                ],
                className="empty-state-center",
            )
        )
    else:
        # Case 3: Points tracking enabled with data - show chart
        # Points trend header removed - already shown at top
        content.append(
            dcc.Graph(
                id="points-chart",
                figure=points_fig,
                config=get_weekly_chart_config(filename_prefix="weekly_points"),  # type: ignore
                className="chart-height-700",
            )
        )

    return html.Div(content)


def create_items_tab_content(items_trend: dict, items_fig):
    """
    Create content for the items tab.

    Args:
        items_trend: Dictionary with items trend and forecast data
        items_fig: Weekly items chart figure

    Returns:
        html.Div: Items tab content
    """
    return html.Div(
        [
            # Enhanced header with trend indicator and forecast pills
            html.Div(
                [
                    # Column for items trend
                    create_trend_header_with_forecasts(
                        items_trend,
                        "Weekly Items Trend",
                        "fas fa-tasks",
                        "brand",
                    ),
                ],
                className="mb-4",
            ),
            # Consolidated items weekly chart with forecast
            dcc.Graph(
                id="items-chart",
                figure=items_fig,
                config=get_weekly_chart_config(),  # type: ignore
                className="chart-height-700",
            ),
        ]
    )


def create_points_tab_content(points_trend: dict, points_fig):
    """
    Create content for the points tab.

    Args:
        points_trend: Dictionary with points trend and forecast data
        points_fig: Weekly points chart figure

    Returns:
        html.Div: Points tab content
    """
    return html.Div(
        [
            # Enhanced header with trend indicator and forecast pills
            html.Div(
                [
                    # Column for points trend
                    create_trend_header_with_forecasts(
                        points_trend,
                        "Weekly Points Trend",
                        "fas fa-chart-bar",
                        "points",
                    ),
                ],
                className="mb-4",
            ),
            # Consolidated points weekly chart with forecast
            dcc.Graph(
                id="points-chart",
                figure=points_fig,
                config=get_weekly_chart_config(),  # type: ignore
                className="chart-height-700",
            ),
        ]
    )


def create_scope_tracking_tab_content(
    df: pd.DataFrame,
    settings: dict,
    show_points: bool = True,
) -> html.Div:
    """
    Create content for the scope tracking tab.

    Args:
        df: DataFrame with statistics data (already filtered by data_points_count).
        settings: Settings dictionary.
        show_points: Whether points tracking is enabled.

    Returns:
        html.Div: Scope tracking tab content.
    """

    scope_creep_threshold = settings.get(
        "scope_creep_threshold", DEFAULT_SETTINGS["scope_creep_threshold"]
    )
    data_points_count = int(settings.get("data_points_count", len(df)))

    if df.empty:
        return html.Div(
            [
                html.Div(
                    className="alert alert-info",
                    children=[
                        html.I(className="fas fa-info-circle me-2"),
                        "No data available to display scope metrics.",
                    ],
                )
            ]
        )

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # CRITICAL FIX: Do NOT re-filter here — data is already filtered in the callback
    # to ensure consistency with Dashboard's Actionable Insights (T073 fix).
    df_filtered = df

    current_remaining_items = settings.get("total_items", 0)
    current_remaining_points = settings.get("total_points", 0)

    try:
        project_scope = load_unified_project_data().get("project_scope", {})
        scope_remaining_items = project_scope.get("remaining_items")
        scope_remaining_points = project_scope.get("remaining_total_points")

        if scope_remaining_items is not None and scope_remaining_points is not None:
            items_mismatch = scope_remaining_items != current_remaining_items
            points_mismatch = (
                abs(scope_remaining_points - current_remaining_points) > 0.1
            )
            if items_mismatch or points_mismatch:
                logger.warning(
                    "[SCOPE BASELINE] Remaining mismatch: "
                    "settings=%s/%s, scope=%s/%s. "
                    "Using project_scope remaining values.",
                    current_remaining_items,
                    current_remaining_points,
                    scope_remaining_items,
                    scope_remaining_points,
                )
                current_remaining_items = scope_remaining_items
                current_remaining_points = scope_remaining_points
    except Exception as e:
        logger.warning("[SCOPE BASELINE] Failed to validate remaining values: %s", e)

    total_completed_items = df_filtered["completed_items"].sum()
    total_completed_points = df_filtered["completed_points"].sum()
    total_created_items = df_filtered["created_items"].sum()
    total_created_points = df_filtered["created_points"].sum()

    baseline_items = int(
        current_remaining_items + total_completed_items - total_created_items
    )
    baseline_points = (
        current_remaining_points + total_completed_points - total_created_points
    )

    logger.debug(
        f"[SCOPE BASELINE] data_points_count={data_points_count}, "
        f"filtered_rows={len(df_filtered)}, "
        f"current_remaining={current_remaining_items}/{current_remaining_points}, "
        f"completed_sum={total_completed_items}/{total_completed_points}, "
        f"created_sum={total_created_items}/{total_created_points}, "
        f"calculated_baseline={baseline_items}/{baseline_points}"
    )

    if "created_items" not in df.columns:
        df["created_items"] = 0
    if "created_points" not in df.columns:
        df["created_points"] = 0

    df["completed_items"] = pd.to_numeric(
        df["completed_items"], errors="coerce"
    ).fillna(0)
    df["completed_points"] = pd.to_numeric(
        df["completed_points"], errors="coerce"
    ).fillna(0)
    df["created_items"] = pd.to_numeric(df["created_items"], errors="coerce").fillna(0)
    df["created_points"] = pd.to_numeric(df["created_points"], errors="coerce").fillna(
        0
    )

    scope_creep_rate = calculate_scope_creep_rate(
        df, baseline_items, baseline_points, data_points_count=None
    )

    try:
        weekly_growth_data = calculate_weekly_scope_growth(df, data_points_count=None)
        if not isinstance(weekly_growth_data, pd.DataFrame):
            logger.warning(
                f"weekly_growth_data is not a DataFrame: {type(weekly_growth_data)}"
            )
            weekly_growth_data = pd.DataFrame(
                columns=["week_label", "items_growth", "points_growth", "start_date"]
            )
    except Exception as e:
        logger.error(f"Error calculating weekly scope growth: {str(e)}")
        weekly_growth_data = pd.DataFrame(
            columns=["week_label", "items_growth", "points_growth", "start_date"]
        )

    stability_index = calculate_scope_stability_index(
        df, baseline_items, baseline_points, data_points_count=None
    )

    if not weekly_growth_data.empty:
        cumulative_items_growth = weekly_growth_data["items_growth"].sum()
        cumulative_points_growth = weekly_growth_data["points_growth"].sum()
        reconstructed_items = baseline_items + cumulative_items_growth
        reconstructed_points = baseline_points + cumulative_points_growth

        logger.info(
            "[SCOPE VALIDATION] Baseline: "
            f"{baseline_items} items, {baseline_points:.1f} points | "
            "Cumulative growth: "
            f"{cumulative_items_growth:+d} items, "
            f"{cumulative_points_growth:+.1f} points | "
            f"Reconstructed: {reconstructed_items} items, "
            f"{reconstructed_points:.1f} points | "
            f"Current actual: {current_remaining_items} items, "
            f"{current_remaining_points:.1f} points | "
            "Match: "
            f"{reconstructed_items == current_remaining_items} items, "
            f"{abs(reconstructed_points - current_remaining_points) < 0.1} points"
        )

        if reconstructed_items != current_remaining_items:
            logger.error(
                "[SCOPE ERROR] Chart reconstruction FAILED! "
                f"Reconstructed {reconstructed_items} items != Current "
                f"{current_remaining_items} items "
                f"(off by {reconstructed_items - current_remaining_items})"
            )

    return create_scope_metrics_dashboard(
        scope_creep_rate,
        weekly_growth_data,
        stability_index,
        scope_creep_threshold,
        total_items_scope=baseline_items,
        total_points_scope=baseline_points,
        show_points=show_points,
    )
