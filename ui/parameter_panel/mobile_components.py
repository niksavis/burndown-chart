import math

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.style_constants import DESIGN_TOKENS


def create_mobile_parameter_fab() -> html.Div:

    return html.Div(
        [
            dbc.Button(
                html.I(className="fas fa-sliders-h", style={"fontSize": "1.25rem"}),
                id="mobile-param-fab",
                color="primary",
                className="mobile-param-fab",
                style={
                    "position": "fixed",
                    "bottom": "80px",
                    "right": DESIGN_TOKENS["mobile"]["fabPosition"],
                    "width": DESIGN_TOKENS["mobile"]["fabSize"],
                    "height": DESIGN_TOKENS["mobile"]["fabSize"],
                    "borderRadius": "50%",
                    "boxShadow": DESIGN_TOKENS["layout"]["shadow"]["lg"],
                    "zIndex": DESIGN_TOKENS["layout"]["zIndex"]["fixed"],
                    "display": "none",
                },
                title="Adjust Parameters",
            ),
        ],
        className="d-md-none",
    )


def create_mobile_parameter_bottom_sheet(
    settings: dict, statistics: list | None = None
) -> dbc.Offcanvas:

    pert_factor = settings.get("pert_factor", 3)
    total_items = settings.get("total_items", 0)
    estimated_items = settings.get("estimated_items", 0)
    total_points = settings.get("total_points", 0)
    estimated_points = settings.get("estimated_points", 0)
    show_points = settings.get("show_points", False)
    data_points_count = settings.get("data_points_count", 10)

    max_data_points = 52
    if statistics and len(statistics) > 0:
        unique_dates = set(
            stat.get("date") or stat.get("stat_date") for stat in statistics
        )
        max_data_points = len(unique_dates) if unique_dates else len(statistics)

    max_data_points = max(4, max_data_points)

    min_data_points = 4
    range_size = max_data_points - min_data_points
    quarter_point = math.ceil(min_data_points + range_size / 4)
    middle_point = math.ceil(min_data_points + range_size / 2)
    three_quarter_point = math.ceil(min_data_points + 3 * range_size / 4)

    data_points_marks: dict[int, dict[str, str]] = {
        min_data_points: {"label": str(min_data_points)},
        quarter_point: {"label": str(quarter_point)},
        middle_point: {"label": str(middle_point)},
        three_quarter_point: {"label": str(three_quarter_point)},
        max_data_points: {"label": str(max_data_points)},
    }

    return dbc.Offcanvas(
        [
            html.Div(
                [
                    html.H5(
                        [
                            html.I(className="fas fa-sliders-h me-2"),
                            "Parameters",
                        ],
                        className="mb-0",
                    ),
                ],
                className=(
                    "d-flex justify-content-between align-items-center "
                    "mb-3 pb-3 border-bottom"
                ),
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Forecast Settings",
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    html.Label(
                                        "Confidence Window",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dcc.Slider(
                                        id="mobile-pert-factor-slider",
                                        min=3,
                                        max=12,
                                        value=pert_factor,
                                        marks={
                                            3: {"label": "3"},
                                            4: {"label": "4"},
                                            5: {"label": "5"},
                                            6: {"label": "6 (rec)"},
                                            7: {"label": "7"},
                                            8: {"label": "8"},
                                            9: {"label": "9"},
                                            10: {"label": "10"},
                                            11: {"label": "11"},
                                            12: {"label": "12"},
                                        },
                                        step=1,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": False,
                                        },
                                        className="mb-2",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    html.Label(
                                        "Data Points (weeks)",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dcc.Slider(
                                        id="mobile-data-points-input",
                                        min=4,
                                        max=max_data_points,
                                        value=data_points_count,
                                        marks=data_points_marks,  # type: ignore[arg-type]
                                        step=1,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": False,
                                        },
                                        className="mb-2",
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        className="mb-4 pb-3 border-bottom",
                    ),
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(className="fas fa-tasks me-2"),
                                    "Work Scope",
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                _create_mobile_input_field(
                                    "Remaining Items",
                                    "mobile-total-items-input",
                                    total_items,
                                    DESIGN_TOKENS,
                                )
                            ),
                            html.Div(
                                _create_mobile_input_field(
                                    "Estimated Items",
                                    "mobile-estimated-items-input",
                                    estimated_items,
                                    DESIGN_TOKENS,
                                )
                            ),
                            html.Div(
                                [
                                    dbc.Checkbox(
                                        id="mobile-points-toggle",
                                        label="Enable Points Tracking",
                                        value=show_points,
                                        className="mb-3",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                _create_mobile_input_field(
                                    "Remaining Points",
                                    "mobile-total-points-input",
                                    total_points,
                                    DESIGN_TOKENS,
                                    disabled=not show_points,
                                ),
                                className="mb-3",
                                style={"display": "block" if show_points else "none"},
                                id="mobile-total-points-container",
                            ),
                            html.Div(
                                _create_mobile_input_field(
                                    "Estimated Points",
                                    "mobile-estimated-points-input",
                                    estimated_points,
                                    DESIGN_TOKENS,
                                    disabled=not show_points,
                                ),
                                className="mb-3",
                                style={"display": "block" if show_points else "none"},
                                id="mobile-estimated-points-container",
                            ),
                        ],
                        className="mb-4",
                    ),
                ],
                style={
                    "maxHeight": DESIGN_TOKENS["mobile"]["bottomSheetMaxHeight"],
                    "overflowY": "auto",
                },
            ),
        ],
        id="mobile-parameter-sheet",
        is_open=False,
        placement="bottom",
        backdrop=True,
        scrollable=True,
        style={
            "maxHeight": DESIGN_TOKENS["mobile"]["bottomSheetMaxHeight"],
        },
        className="mobile-parameter-sheet",
    )


def _create_mobile_input_field(
    label: str,
    input_id: str,
    value: int | float,
    design_tokens: dict,
    disabled: bool = False,
) -> list:
    return [
        html.Label(
            label,
            className="form-label fw-medium",
            style={"fontSize": "0.875rem"},
        ),
        dbc.Input(
            id=input_id,
            type="number",
            value=value,
            min=0,
            disabled=disabled,
            className="mb-3",
            style={"minHeight": design_tokens["mobile"]["touchTargetMin"]},
        ),
    ]
