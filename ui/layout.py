import logging
from datetime import datetime
from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html

from configuration import __version__
from data import calculate_total_points
from data.persistence.adapters import (
    get_project_scope,
    load_app_settings,
    load_statistics,
)
from ui.about_dialog import create_about_dialog
from ui.delete_query_modal import create_delete_query_modal
from ui.field_mapping_modal import create_field_mapping_modal
from ui.grid_utils import create_full_width_layout
from ui.help_system import create_help_system_layout
from ui.import_export_panel import create_import_export_flyout
from ui.improved_settings_panel import create_improved_settings_panel
from ui.jira_config_modal import create_jira_config_modal
from ui.mobile_navigation import create_mobile_navigation_system
from ui.parameter_panel import create_parameter_panel
from ui.query_creation_modal import create_query_creation_modal
from ui.save_query_modal import create_save_query_modal
from ui.tabs import create_desktop_tabs_only
from ui.unsaved_changes_modal import create_unsaved_changes_modal

logger = logging.getLogger(__name__)

USE_ACCORDION_SETTINGS = False


def serve_layout():

    app_settings = load_app_settings()

    loaded_show_points = app_settings.get("show_points", "NOT_FOUND")
    logger.info(
        f"[LAYOUT DEBUG] show_points loaded from settings: {loaded_show_points}"
    )

    statistics, is_sample_data = load_statistics()

    project_scope = get_project_scope()

    settings = {**app_settings}
    if project_scope:
        settings.update(
            {
                "total_items": project_scope.get("remaining_items", 0),
                "total_points": project_scope.get("remaining_total_points", 0),
                "estimated_items": project_scope.get("estimated_items", 0),
                "estimated_points": project_scope.get("estimated_points", 0),
            }
        )

    app_layout = create_app_layout(settings, statistics, is_sample_data)
    return app_layout


def create_app_layout(settings, statistics, is_sample_data):

    estimated_total_points, avg_points_per_item = calculate_total_points(
        settings.get("total_items", 0),
        settings.get("estimated_items", 0),
        settings.get("estimated_points", 0),
        statistics,
    )

    import app  # noqa: PLC0415

    version_update_available = (
        hasattr(app, "VERSION_CHECK_RESULT")
        and isinstance(app.VERSION_CHECK_RESULT, dict)
        and app.VERSION_CHECK_RESULT.get("update_available", False)
    )

    if version_update_available and isinstance(app.VERSION_CHECK_RESULT, dict):
        version_info = {
            "current": app.VERSION_CHECK_RESULT.get("current_commit", "unknown"),
            "latest": app.VERSION_CHECK_RESULT.get("latest_commit", "unknown"),
        }
    else:
        version_info = None

    version_result: Any = getattr(app, "VERSION_CHECK_RESULT", None)
    has_update_state = version_result is not None and hasattr(version_result, "state")
    update_state: Any = version_result.state if has_update_state else None
    show_footer_update = has_update_state and update_state in [
        update_state.__class__.AVAILABLE,
        update_state.__class__.MANUAL_UPDATE_REQUIRED,
        update_state.__class__.READY,
    ]

    if show_footer_update:
        update_icon_class = (
            "fas fa-check-circle me-1"
            if update_state == update_state.__class__.READY
            else "fas fa-sync-alt me-1"
        )
        if update_state == update_state.__class__.AVAILABLE:
            update_text = (
                "Update Available: "
                f"{version_result.current_version} → "
                f"{version_result.available_version}"
            )
        elif update_state == update_state.__class__.READY:
            update_text = "Update Ready - Click to Install"
        else:
            update_text = (
                "Manual Update Available: "
                f"{version_result.current_version} → "
                f"{version_result.available_version}"
            )

        footer_update_children = html.Div(
            html.Button(
                [
                    html.I(
                        className=update_icon_class,
                        style={"fontSize": "0.7rem"},
                    ),
                    update_text,
                ],
                id="footer-update-indicator",
                n_clicks=0,
                className="btn btn-link p-0 border-0",
                style={
                    "color": "#198754",
                    "fontWeight": "500",
                    "fontSize": "0.75rem",
                    "textDecoration": "none",
                },
            ),
            className="mt-1 text-center",
            style={"lineHeight": "1.2"},
        )
    else:
        footer_update_children = None

    return dbc.Container(
        [
            html.Div(
                id="app-notifications",
                style={
                    "position": "fixed",
                    "top": "5px",
                    "right": "-132px",
                    "zIndex": "9999",
                    "width": "520px",
                },
            ),
            dcc.Store(id="version-check-info", data=version_info),
            dcc.Store(id="update-toast-shown", storage_type="session", data=False),
            dcc.Store(id="update-status-store", data=None),
            dcc.Store(id="migration-status", storage_type="session", data=None),
            create_jira_config_modal(),
            create_field_mapping_modal(),
            create_save_query_modal(),
            create_unsaved_changes_modal(),
            create_delete_query_modal(),
            create_query_creation_modal(),
            create_about_dialog(),
            create_help_system_layout(),
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="app-init-complete", data=False),
            dcc.Store(id="current-settings", data=settings),
            dcc.Store(id="current-statistics", data=statistics),
            dcc.Store(id="is-sample-data", data=is_sample_data),
            dcc.Store(id="jira-issues-store", data=None),
            dcc.Store(id="jira-metadata-store", data=None),
            dcc.Store(id="jira-config-hash", data=None),
            dcc.Store(id="jira-config-save-trigger", data=0),
            dcc.Store(id="trigger-auto-metrics-calc", data=None),
            dcc.Store(
                id="calculation-results",
                data={
                    "total_points": estimated_total_points,
                    "avg_points_per_item": avg_points_per_item,
                },
            ),
            dcc.Store(id="date-range-weeks", data=None),
            dcc.Store(id="chart-cache", data={}),
            dcc.Store(id="ui-state", data={"loading": False, "last_tab": None}),
            dcc.Store(id="viewport-size", data="desktop"),
            dcc.Store(id="metrics-refresh-trigger", data=None),
            dcc.Interval(
                id="download-progress-poll",
                interval=1000,
                n_intervals=0,
                disabled=True,
            ),
            dcc.Interval(
                id="viewport-detector",
                interval=1000,
                n_intervals=0,
                max_intervals=-1,
            ),
            dcc.Store(
                id="mobile-nav-state",
                data={
                    "drawer_open": False,
                    "active_tab": "tab-burndown",
                    "swipe_enabled": True,
                },
                storage_type="memory",
            ),
            dcc.Store(
                id="parameter-panel-state",
                data={"is_open": False, "user_preference": False},
                storage_type="local",
            ),
            html.Div(
                [
                    create_parameter_panel(
                        settings, is_open=False, statistics=statistics
                    ),
                    create_improved_settings_panel(),
                    create_import_export_flyout(),
                    create_desktop_tabs_only(),
                ],
                className="param-panel-sticky",
            ),
            html.Div(id="panel-backdrop", className="panel-backdrop"),
            html.Div(
                dcc.Graph(id="forecast-graph", style={"display": "none"}),
                id="forecast-graph-container",
            ),
            html.Div(
                [
                    dbc.Alert(
                        html.Div(
                            [
                                html.I(className="fas fa-info-circle me-2 text-info"),
                                html.Span(
                                    [
                                        html.Strong("Using Sample Data"),
                                        html.Br(),
                                        html.Small(
                                            "You're currently viewing demo data. "
                                            "Upload your own data using the form "
                                            "below or add entries manually to start "
                                            "tracking your project.",
                                            style={"opacity": "0.85"},
                                        ),
                                    ]
                                ),
                            ],
                            className="d-flex align-items-start",
                        ),
                        id="sample-data-alert",
                        color="info",
                        dismissable=True,
                        is_open=is_sample_data,
                        className="mb-3",
                    ),
                ],
                id="sample-data-banner",
            ),
            create_mobile_navigation_system(),
            create_full_width_layout(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.Div(id="tab-content"),
                            ]
                        ),
                    ],
                    className="shadow-sm",
                ),
                row_class="mb-4",
            ),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className=(
                                                "fas fa-chart-line me-1 text-primary"
                                            ),
                                            style={"fontSize": "0.8rem"},
                                        ),
                                        html.Span(
                                            f"v{__version__}",
                                            id="footer-version-text",
                                            className="fw-medium text-secondary",
                                        ),
                                    ],
                                    style={"fontSize": "0.8rem"},
                                ),
                                xs=12,
                                sm=4,
                                className=(
                                    "d-flex align-items-center justify-content-center "
                                    "justify-content-sm-start mb-1 mb-sm-0"
                                ),
                            ),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.A(
                                            [
                                                html.I(
                                                    className="fab fa-github me-1",
                                                    style={"fontSize": "0.85rem"},
                                                ),
                                                "GitHub",
                                            ],
                                            href="https://github.com/niksavis/burndown-chart",
                                            target="_blank",
                                            className=(
                                                "text-decoration-none "
                                                "text-primary fw-medium me-3"
                                            ),
                                            style={
                                                "fontSize": "0.85rem",
                                                "transition": "opacity 0.2s",
                                            },
                                        ),
                                        html.A(
                                            [
                                                html.I(
                                                    className=(
                                                        "fas fa-question-circle me-1"
                                                    ),
                                                    style={"fontSize": "0.85rem"},
                                                ),
                                                "About",
                                            ],
                                            id="about-button",
                                            href="#",
                                            className=(
                                                "text-decoration-none "
                                                "text-primary fw-medium"
                                            ),
                                            style={
                                                "fontSize": "0.85rem",
                                                "transition": "opacity 0.2s",
                                            },
                                        ),
                                    ],
                                    className=(
                                        "d-flex align-items-center "
                                        "justify-content-center"
                                    ),
                                ),
                                xs=12,
                                sm=4,
                                className="mb-1 mb-sm-0",
                            ),
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className="fas fa-clock me-1",
                                            style={"fontSize": "0.8rem"},
                                        ),
                                        f"{datetime.now().strftime('%b %d, %Y')}",
                                    ],
                                    className="text-muted",
                                    style={"fontSize": "0.8rem"},
                                ),
                                xs=12,
                                sm=4,
                                className=(
                                    "d-flex align-items-center justify-content-center "
                                    "justify-content-sm-end"
                                ),
                            ),
                        ],
                        className="g-1",
                    ),
                    html.Div(
                        id="footer-update-container",
                        children=footer_update_children,
                    ),
                ],
                className="mt-2 mb-1 py-2",
                style={
                    "backgroundColor": "#f8f9fa",
                    "borderTop": "1px solid #dee2e6",
                    "borderRadius": "4px",
                    "padding": "0.5rem 0.75rem",
                },
            ),
        ],
        fluid=True,
        className="px-3 pb-3",
    )
