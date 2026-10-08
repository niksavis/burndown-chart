from __future__ import annotations

from typing import Any, cast

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table, html

from configuration.settings import STATISTICS_HELP_TEXTS
from ui.button_utils import create_button
from ui.styles import (
    NEUTRAL_COLORS,
    create_card_header_with_tooltip,
    create_standardized_card,
    get_vertical_rhythm,
)
from ui.tooltip_utils import create_info_tooltip

StyleCellConditional = dict[str, Any]


def create_statistics_data_card(current_statistics) -> dbc.Card:

    statistics_df = pd.DataFrame(current_statistics)

    header_content = create_card_header_with_tooltip(
        title="Weekly Progress Data",
        tooltip_text=(
            "Weekly tracking of completed and newly created work items "
            "and story points. Each Monday date represents work done "
            "during that week (Monday through Sunday). This data drives "
            "all velocity calculations and forecasting."
        ),
        tooltip_id="statistics-data",
    )

    if statistics_df.empty:
        statistics_df = pd.DataFrame(
            columns=[
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
        )

    def create_responsive_table_wrapper(table_component):
        return html.Div(
            table_component,
            className="table-responsive",
            style={
                "overflowX": "auto",
                "WebkitOverflowScrolling": "touch",
                "width": "100%",
            },
        )

    def detect_column_alignment(dataframe, column_name):
        if pd.api.types.is_numeric_dtype(dataframe[column_name]):
            return "right"
        elif pd.api.types.is_datetime64_any_dtype(dataframe[column_name]):
            return "center"
        else:
            return "left"

    def generate_column_alignments(dataframe):
        alignments = {}
        for column in dataframe.columns:
            alignments[column] = detect_column_alignment(dataframe, column)
        return alignments

    def create_standardized_table_style(stripe_color=None, mobile_optimized=True):
        if stripe_color is None:
            stripe_color = NEUTRAL_COLORS.get("gray-100", "#f8f9fa")

        cell_padding_v = "0.5rem"
        cell_padding_h = "0.75rem"
        border_color = NEUTRAL_COLORS.get("gray-400", "#ced4da")
        font_family = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"

        style_dict = {
            "style_table": {
                "overflowX": "auto",
                "borderRadius": "4px",
                "border": f"1px solid {NEUTRAL_COLORS.get('gray-300', '#dee2e6')}",
                "marginBottom": get_vertical_rhythm("section"),
                "WebkitOverflowScrolling": "touch",
            },
            "style_header": {
                "backgroundColor": NEUTRAL_COLORS.get("gray-200", "#e9ecef"),
                "fontWeight": "bold",
                "textAlign": "center",
                "padding": f"{cell_padding_v} {cell_padding_h}",
                "borderBottom": f"2px solid {border_color}",
            },
            "style_cell": {
                "padding": f"{cell_padding_v} {cell_padding_h}",
                "fontFamily": font_family,
                "textAlign": "left",
                "whiteSpace": "normal",
                "height": "auto",
                "lineHeight": "1.5",
                "minWidth": "100px",
                "maxWidth": "500px",
            },
            "style_data": {
                "border": f"1px solid {NEUTRAL_COLORS.get('gray-200', '#e9ecef')}",
            },
            "style_data_conditional": [
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": stripe_color,
                }
            ],
        }

        if mobile_optimized:
            style_dict["css"] = [
                {
                    "selector": ".dash-spreadsheet-container",
                    "rule": "touch-action: pan-y; -webkit-overflow-scrolling: touch;",
                },
                {
                    "selector": ".dash-cell-value",
                    "rule": (
                        "white-space: normal !important; "
                        "word-break: break-word !important;"
                    ),
                },
                {
                    "selector": ".dash-filter",
                    "rule": (
                        "padding: 2px 5px; border-radius: 3px; "
                        "background-color: rgba(0, 0, 0, 0.05);"
                    ),
                },
                {"selector": ".dash-filter--case", "rule": "display: none;"},
                {
                    "selector": "td.cell--editable:hover",
                    "rule": "background-color: rgba(13, 110, 253, 0.08) !important;",
                },
                {
                    "selector": ".dash-header-cell .column-header--sort",
                    "rule": "opacity: 1 !important; color: #0d6efd !important;",
                },
                {
                    "selector": ".dash-cell-value:focus",
                    "rule": (
                        "outline: none !important; "
                        "box-shadow: inset 0 0 0 2px #0d6efd !important;"
                    ),
                },
            ]

        return style_dict

    def create_enhanced_data_table(
        data,
        columns,
        id,
        editable=False,
        row_selectable=False,
        page_size=None,
        include_pagination=False,
        sort_action=None,
        filter_action=None,
        column_alignments=None,
        sort_by=None,
        mobile_responsive=True,
        priority_columns=None,
    ):
        table_style = create_standardized_table_style(
            mobile_optimized=mobile_responsive
        )
        style_cell_conditional: list[StyleCellConditional] = []
        if column_alignments:
            style_cell_conditional = [
                cast(
                    StyleCellConditional,
                    {"if": {"column_id": col_id}, "textAlign": alignment},
                )
                for col_id, alignment in column_alignments.items()
            ]
        if mobile_responsive and priority_columns:
            for col in columns:
                if col["id"] not in priority_columns:
                    style_cell_conditional.append(
                        cast(
                            StyleCellConditional,
                            {
                                "if": {"column_id": col["id"]},
                                "className": "mobile-hidden",
                                "media": "screen and (max-width: 767px)",
                            },
                        )
                    )

        if editable:
            style_data_conditional = table_style["style_data_conditional"] + [
                {
                    "if": {"column_editable": True},
                    "backgroundColor": "rgba(0, 123, 255, 0.05)",
                    "cursor": "pointer",
                },
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "rgba(13, 110, 253, 0.15)",
                    "border": "1px solid #0d6efd",
                },
                *[
                    {
                        "if": {
                            "column_id": col["id"],
                            "filter_query": f"{{{col['id']}}} < 0",
                        },
                        "backgroundColor": "rgba(220, 53, 69, 0.1)",
                        "color": "#dc3545",
                    }
                    for col in columns
                    if col.get("type") == "numeric"
                ],
            ]
        else:
            style_data_conditional = table_style["style_data_conditional"]

        if include_pagination:
            pagination_settings = {
                "page_action": "native",
                "page_current": 0,
                "page_size": page_size if page_size else 10,
                "page_count": None,
            }
        else:
            pagination_settings = {}

        return dash_table.DataTable(
            id=id,
            data=data,
            columns=columns,
            editable=editable,
            row_selectable="multi" if row_selectable else None,
            row_deletable=editable,
            sort_action=sort_action,
            filter_action=filter_action,
            sort_by=sort_by,
            style_table=table_style["style_table"],
            style_header=table_style["style_header"],
            style_cell=table_style["style_cell"],
            style_cell_conditional=style_cell_conditional,  # type: ignore
            style_data=table_style["style_data"],
            style_data_conditional=style_data_conditional,
            css=table_style.get("css", []),
            tooltip_delay=0,
            tooltip_duration=None,
            **pagination_settings,
        )

    columns = [
        {
            "name": "Week Start (Monday)",
            "id": "date",
            "type": "text",
        },
        {
            "name": "Items Done This Week",
            "id": "completed_items",
            "type": "numeric",
        },
        {
            "name": "Points Done This Week",
            "id": "completed_points",
            "type": "numeric",
        },
        {
            "name": "New Items Added",
            "id": "created_items",
            "type": "numeric",
        },
        {
            "name": "New Points Added",
            "id": "created_points",
            "type": "numeric",
        },
    ]

    column_alignments = {
        "date": "center",
        "completed_items": "right",
        "completed_points": "right",
        "created_items": "right",
        "created_points": "right",
    }

    statistics_table = create_enhanced_data_table(
        data=statistics_df.to_dict("records"),
        columns=columns,
        id="statistics-table",
        editable=True,
        row_selectable=False,
        page_size=10,
        include_pagination=True,
        sort_action="native",
        filter_action="native",
        column_alignments=column_alignments,
        sort_by=[{"column_id": "date", "direction": "desc"}],
    )

    help_text = html.Div(
        [
            html.Small(
                [
                    html.I(className="fas fa-info-circle me-1 text-info"),
                    "Enter weekly data for work completed and created. "
                    "Each Monday date represents work done during that full "
                    "week (Monday through Sunday, inclusive).",
                ],
                className="text-muted",
            ),
            html.Small(
                [
                    html.I(className="fas fa-calendar-week me-1 text-info"),
                    html.Strong("Weekly Timeboxes: "),
                    "Monday date = work completed/created from that Monday "
                    "through the following Sunday (7-day period, inclusive). "
                    "Use the ",
                    html.Code("Add Row"),
                    " button to add new weekly entries.",
                ],
                className="text-muted d-block mt-1",
            ),
            html.Small(
                [
                    html.I(className="fas fa-plus-circle me-1 text-info"),
                    html.Strong("Scope Tracking: "),
                    "Include both completed work (finished items/points) "
                    "and created work (new items/points added to backlog) "
                    "to track scope changes.",
                ],
                className="text-muted d-block mt-1",
            ),
            html.Small(
                [
                    html.I(className="fas fa-calendar-alt me-1 text-info"),
                    html.Strong("Date Format: "),
                    "Always use Monday dates in ",
                    html.Code("YYYY-MM-DD"),
                    " format (e.g., 2025-09-22 for the week of Sept 22-28, inclusive).",
                ],
                className="text-muted d-block mt-1",
            ),
            html.Small(
                [
                    html.I(className="fas fa-exclamation-triangle me-1 text-warning"),
                    html.Strong("Important: ", style={"color": "#856404"}),
                    "Manual edits persist in the database. However, ",
                    html.Strong("Update Data"),
                    " will overwrite all edits with fresh JIRA data, and ",
                    html.Strong("Force Refresh"),
                    " will delete all data and reload from JIRA. "
                    "Save important manual changes elsewhere before updating.",
                ],
                className="d-block mt-2 p-2",
                style={
                    "backgroundColor": "#fff3cd",
                    "border": "1px solid #ffc107",
                    "borderRadius": "4px",
                    "color": "#856404",
                },
            ),
        ],
        className="mb-3",
    )

    responsive_table = create_responsive_table_wrapper(statistics_table)

    column_explanations = html.Div(
        [
            dbc.Button(
                [
                    html.I(className="fas fa-info-circle me-2 text-info"),
                    "Column Explanations",
                ],
                id="column-explanations-toggle",
                color="info",
                outline=True,
                size="sm",
                className="mb-2",
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Data Column Definitions", className="mb-3"),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-calendar-week "
                                                            "me-1 text-primary"
                                                        )
                                                    ),
                                                    "Week Start (Monday):",
                                                ]
                                            ),
                                            html.Span(
                                                " Data collection date "
                                                "(weekly snapshots). Each Monday "
                                                "represents work done during that "
                                                "full week (Monday-Sunday).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "date-field-column",
                                                STATISTICS_HELP_TEXTS["date_field"],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-check-circle "
                                                            "me-1 text-success"
                                                        )
                                                    ),
                                                    "Items Done This Week:",
                                                ]
                                            ),
                                            html.Span(
                                                " Number of work items "
                                                "(stories, tasks, tickets) "
                                                "completed during this weekly period.",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "completed-items-column",
                                                STATISTICS_HELP_TEXTS[
                                                    "completed_items"
                                                ],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-star "
                                                            "me-1 text-warning"
                                                        )
                                                    ),
                                                    "Points Done This Week:",
                                                ]
                                            ),
                                            html.Span(
                                                " Story points or effort units "
                                                "completed during this weekly period.",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "completed-points-column",
                                                STATISTICS_HELP_TEXTS[
                                                    "completed_points"
                                                ],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-plus-circle "
                                                            "me-1 text-info"
                                                        )
                                                    ),
                                                    "New Items Added:",
                                                ]
                                            ),
                                            html.Span(
                                                " Number of new work items added "
                                                "to the project during this period "
                                                "(scope growth).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "created-items-column",
                                                STATISTICS_HELP_TEXTS["created_items"],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-plus-square "
                                                            "me-1 text-secondary"
                                                        )
                                                    ),
                                                    "New Points Added:",
                                                ]
                                            ),
                                            html.Span(
                                                " Story points for new work items "
                                                "added during this period (scope "
                                                "change impact).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "created-points-column",
                                                STATISTICS_HELP_TEXTS["created_points"],
                                            ),
                                        ],
                                        className="mb-0",
                                    ),
                                ],
                                className="small",
                            ),
                        ]
                    ),
                    color="light",
                ),
                id="column-explanations-collapse",
                is_open=False,
            ),
        ],
        className="mb-3",
    )

    body_content = [
        help_text,
        column_explanations,
        html.Div(className="mb-3"),
        responsive_table,
        html.Div(
            [
                html.Div(
                    [
                        create_button(
                            text="Add Row",
                            id="add-row-button",
                            variant="primary",
                            icon_class="fas fa-plus",
                        ),
                        dbc.Tooltip(
                            "Adds a new weekly entry with Monday date 7 days "
                            "after the most recent entry. Enter work completed "
                            "and created during that week (Monday-Sunday).",
                            target="add-row-button",
                            placement="top",
                            trigger="click",
                            autohide=True,
                        ),
                    ],
                    className="mb-2 mb-sm-0",
                    style={"display": "inline-block"},
                ),
            ],
            className="d-flex flex-wrap justify-content-center align-items-center mt-4",
        ),
    ]

    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        body_className="p-3",
        shadow="sm",
    )
