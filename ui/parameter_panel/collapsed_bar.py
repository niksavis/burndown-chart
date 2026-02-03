"""Collapsed parameter bar component."""

import dash_bootstrap_components as dbc
from dash import html


def create_parameter_bar_collapsed(
    pert_factor: float,
    deadline: str,
    scope_items: int,
    scope_points: int,
    id_suffix: str = "",
    remaining_items: int | None = None,
    remaining_points: int | None = None,
    total_items: int | None = None,
    total_points: int | None = None,
    show_points: bool = True,
    data_points: int | None = None,
    profile_name: str | None = None,
    query_name: str | None = None,
) -> html.Div:
    """
    Create collapsed parameter bar showing key values and expand button.

    This component supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    When collapsed, it displays a compact summary of current parameter values with an
    expand button to show the full parameter panel.

    Args:
        pert_factor: Current PERT factor value
        deadline: Current deadline date string
        scope_items: Total number of items in scope (fallback)
        scope_points: Total story points in scope (fallback)
        id_suffix: Suffix for generating unique IDs
        remaining_items: Number of items remaining currently (displayed in bar)
        remaining_points: Number of points remaining currently (displayed in bar)
        total_items: Total remaining items (used for display)
        total_points: Total remaining points (used for display)
        show_points: Whether to show points data
        data_points: Number of weeks of data used for forecasting
        profile_name: Name of active profile (if in profiles mode)
        query_name: Name of active query (if in profiles mode)

    Returns:
        html.Div: Collapsed parameter bar component

    Example:
        >>> create_parameter_bar_collapsed(1.5, "2025-12-31", 100, 500, remaining_items=50)
    """
    from ui.style_constants import DESIGN_TOKENS

    bar_id = f"parameter-bar-collapsed{'-' + id_suffix if id_suffix else ''}"
    expand_btn_id = f"btn-expand-parameters{'-' + id_suffix if id_suffix else ''}"

    # Display the total items/points (remaining scope) for Remaining label
    # Use remaining values only if total values not available (fallback to current scope)
    display_items = (
        total_items
        if total_items is not None and total_items > 0
        else (remaining_items if remaining_items is not None else scope_items)
    )
    display_points = (
        total_points
        if total_points is not None and total_points > 0
        else (remaining_points if remaining_points is not None else scope_points)
    )

    # Determine label based on what we're showing
    items_label = (
        "Remaining" if (total_items is not None and total_items > 0) else "Scope"
    )

    # Create points display only if enabled
    points_display = []
    if show_points:
        # Round points to 1 decimal for display
        display_points_rounded = round(display_points, 1)
        points_display = [
            html.Span(
                [
                    html.I(className="fas fa-chart-bar me-1"),
                    html.Span(
                        f"{items_label}: ",
                        className="text-muted d-none d-xl-inline",
                        style={"fontSize": "0.85em"},
                    ),
                    html.Span(
                        f"{display_points_rounded:.1f}", style={"fontSize": "0.85em"}
                    ),
                ],
                className="param-summary-item",
                title=f"{items_label}: {display_points_rounded:.1f} points",
            ),
        ]

    # Detect initial icon state from task_progress.json to avoid flash on page load
    profile_icon_class = "fas fa-folder me-1"
    query_icon_class = "fas fa-search me-1"

    try:
        from pathlib import Path
        import json

        progress_file = Path("task_progress.json")
        if progress_file.exists():
            with open(progress_file, "r", encoding="utf-8") as f:
                progress_data = json.load(f)

            status = progress_data.get("status", "idle")
            phase = progress_data.get("phase", "fetch")
            cancelled = progress_data.get("cancelled", False)

            # Apply same logic as banner_status_icons callback
            if status == "in_progress" and not cancelled:
                profile_icon_class = "fas fa-folder me-1 text-warning"
                if phase == "fetch":
                    query_icon_class = "fas fa-spinner fa-spin me-1 text-warning"
                elif phase == "calculate":
                    query_icon_class = "fas fa-calculator fa-pulse me-1 text-success"
                else:
                    query_icon_class = "fas fa-search fa-pulse me-1 text-warning"
    except Exception:
        # Silently fail - will use defaults and callback will update shortly
        pass

    # Build profile/query display section if in profiles mode
    profile_query_display = []
    if profile_name and query_name:
        profile_query_display = [
            html.Span(
                [
                    html.I(
                        id="profile-status-icon",
                        className=profile_icon_class,
                    ),
                    html.Span(
                        profile_name,
                        className="text-muted d-none d-xl-inline",
                        style={"fontSize": "0.85em"},
                    ),
                ],
                className="param-summary-item me-2",
                title=f"Profile: {profile_name}",
            ),
            html.Span(
                [
                    html.I(
                        id="query-status-icon",
                        className=query_icon_class,
                    ),
                    html.Span(
                        query_name,
                        className="text-muted d-none d-xl-inline",
                        style={"fontSize": "0.85em"},
                    ),
                ],
                className="param-summary-item me-3",
                title=f"Query: {query_name}",
            ),
        ]

    return html.Div(
        [
            # Single row with all items on the same level
            html.Div(
                [
                    # Summary items (left side)
                    html.Div(
                        profile_query_display
                        + [
                            html.Span(
                                [
                                    html.I(className="fas fa-sliders-h me-1"),
                                    html.Span(
                                        "Range: ",
                                        className="text-muted d-none d-xl-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{pert_factor}w", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Forecast Range: {pert_factor} weeks (samples best/worst case velocity from your history)",
                            ),
                            html.Span(
                                [
                                    html.I(className="fas fa-chart-line me-1"),
                                    html.Span(
                                        "Data: ",
                                        className="text-muted d-none d-xl-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{data_points}w", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Data Points: {data_points} weeks of historical data used for forecasting",
                                style={"display": "inline" if data_points else "none"},
                            )
                            if data_points
                            else html.Span(),
                            html.Span(
                                [
                                    html.I(className="fas fa-calendar me-1"),
                                    html.Span(
                                        "Deadline: ",
                                        className="text-muted d-none d-xl-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{deadline}", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Project deadline: {deadline}",
                            ),
                            html.Span(
                                [
                                    html.I(className="fas fa-tasks me-1"),
                                    html.Span(
                                        f"{items_label}: ",
                                        className="text-muted d-none d-xl-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{display_items:,}",
                                        style={"fontSize": "0.85em"},
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"{items_label}: {display_items:,} items",
                            ),
                        ]
                        + points_display,
                        className="d-flex align-items-center flex-wrap flex-grow-1",
                    ),
                    # Buttons (right side)
                    html.Div(
                        [
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-cog",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Settings",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id="settings-button",
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                                title="Expand Settings",
                            ),
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-sliders-h",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Parameters",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id=expand_btn_id,
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "flexShrink": "0",
                                },
                                title="Adjust project parameters",
                            ),
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-exchange-alt",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Data",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id="toggle-import-export-panel",
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                                title="Expand Data",
                            ),
                        ],
                        className="d-flex justify-content-end align-items-center flex-nowrap flex-shrink-0",
                        style={"minWidth": "fit-content"},
                    ),
                ],
                className="d-flex align-items-center justify-content-between flex-wrap",
            ),
        ],
        className="parameter-bar-collapsed",
        id=bar_id,
        style={
            "padding": "6px 12px",  # Aligned with tabs row for visual consistency
            "backgroundColor": DESIGN_TOKENS["colors"]["gray-100"],
            "borderRadius": DESIGN_TOKENS["layout"]["borderRadius"]["md"],
            "marginBottom": "0",  # Compact: no margin
        },
    )
