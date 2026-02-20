"""Main parameter panel controller component."""


import dash_bootstrap_components as dbc
from dash import html

from ui.parameter_panel.collapsed_bar import create_parameter_bar_collapsed
from ui.parameter_panel.expanded_panel import create_parameter_panel_expanded


def create_parameter_panel(
    settings: dict,
    is_open: bool = False,
    id_suffix: str = "",
    statistics: list | None = None,
) -> html.Div:
    """
    Create complete collapsible parameter panel combining collapsed bar and expanded section.

    This component supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    It combines the collapsed bar (always visible) with the expanded panel (toggleable)
    using Bootstrap's Collapse component for smooth transitions.

    Args:
        settings: Dictionary containing current parameter values
        is_open: Whether panel should start in expanded state
        id_suffix: Suffix for generating unique IDs
        statistics: Optional list of statistics data points for calculating max data points

    Returns:
        html.Div: Complete parameter panel with collapse functionality
    """
    panel_id = f"parameter-panel{'-' + id_suffix if id_suffix else ''}"
    collapse_id = f"parameter-collapse{'-' + id_suffix if id_suffix else ''}"

    # Extract key values for collapsed bar
    pert_factor = settings.get("pert_factor", 3)
    deadline = (
        settings.get("deadline", "2025-12-31") or "2025-12-31"
    )  # Ensure valid default for display
    total_items = settings.get("total_items", 0)
    total_points = settings.get("total_points", 0)
    data_points = settings.get("data_points_count")
    show_points = settings.get("show_points", True)

    # CRITICAL FIX: Pass total_items/total_points as BOTH scope AND remaining values
    # The serve_layout() calculates these as remaining work at START of window,
    # so we should display them as "Remaining" not "Scope"
    # This ensures the initial banner matches the callback-updated banner

    # Get active profile and query names for display
    from data.profile_manager import get_active_profile_and_query_display_names

    display_names = get_active_profile_and_query_display_names()
    profile_name = display_names.get("profile_name")
    query_name = display_names.get("query_name")

    return html.Div(
        [
            # Collapsed bar (always visible)
            create_parameter_bar_collapsed(
                pert_factor=pert_factor,
                deadline=deadline,
                scope_items=total_items,
                scope_points=total_points,
                remaining_items=total_items
                if total_items > 0
                else None,  # Display as Remaining
                remaining_points=total_points
                if total_points > 0
                else None,  # Display as Remaining
                total_items=total_items if total_items > 0 else None,  # Remaining Items
                total_points=total_points
                if total_points > 0
                else None,  # Remaining Points
                show_points=show_points,  # Respect Points Tracking toggle
                id_suffix=id_suffix,
                data_points=data_points,
                profile_name=profile_name,
                query_name=query_name,
            ),
            # Expanded panel (toggleable)
            dbc.Collapse(
                create_parameter_panel_expanded(
                    settings, id_suffix=id_suffix, statistics=statistics
                ),
                id=collapse_id,
                is_open=is_open,
            ),
        ],
        id=panel_id,
        className="parameter-panel-container",
    )
