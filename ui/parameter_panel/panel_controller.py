import dash_bootstrap_components as dbc
from dash import html

from data.profile_manager import get_active_profile_and_query_display_names
from ui.parameter_panel.collapsed_bar import create_parameter_bar_collapsed
from ui.parameter_panel.expanded_panel import create_parameter_panel_expanded


def create_parameter_panel(
    settings: dict,
    is_open: bool = False,
    id_suffix: str = "",
    statistics: list | None = None,
) -> html.Div:

    panel_id = f"parameter-panel{'-' + id_suffix if id_suffix else ''}"
    collapse_id = f"parameter-collapse{'-' + id_suffix if id_suffix else ''}"

    pert_factor = settings.get("pert_factor", 3)
    deadline = settings.get("deadline", "2025-12-31") or "2025-12-31"
    total_items = settings.get("total_items", 0)
    total_points = settings.get("total_points", 0)
    data_points = settings.get("data_points_count")
    show_points = settings.get("show_points", True)

    display_names = get_active_profile_and_query_display_names()
    profile_name = display_names.get("profile_name")
    query_name = display_names.get("query_name")

    return html.Div(
        [
            create_parameter_bar_collapsed(
                pert_factor=pert_factor,
                deadline=deadline,
                scope_items=total_items,
                scope_points=total_points,
                remaining_items=total_items if total_items > 0 else None,
                remaining_points=total_points if total_points > 0 else None,
                total_items=total_items if total_items > 0 else None,
                total_points=total_points if total_points > 0 else None,
                show_points=show_points,
                id_suffix=id_suffix,
                data_points=data_points,
                profile_name=profile_name,
                query_name=query_name,
            ),
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
