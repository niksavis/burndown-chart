from typing import TypedDict

import dash_bootstrap_components as dbc
from dash import html

from configuration.settings import CHART_HELP_TEXTS
from ui.cards import create_forecast_info_card
from ui.grid_utils import create_tab_content as grid_create_tab_content
from ui.mobile_navigation import (
    get_mobile_tabs_config,
)
from ui.style_constants import get_color
from ui.tooltip_utils import create_info_tooltip


class TabConfig(TypedDict):
    id: str
    label: str
    icon: str
    unicode_icon: str
    color: str
    order: int
    requires_data: bool
    help_content_id: str


TAB_CONFIG: list[TabConfig] = [
    {
        "id": "tab-dashboard",
        "label": "Dashboard",
        "icon": "fa-tachometer-alt",
        "unicode_icon": "📊",
        "color": get_color("primary"),
        "order": 0,
        "requires_data": True,
        "help_content_id": "help-dashboard",
    },
    {
        "id": "tab-burndown",
        "label": "Burndown",
        "icon": "fa-chart-line",
        "unicode_icon": "📈",
        "color": get_color("info"),
        "order": 1,
        "requires_data": True,
        "help_content_id": "help-burndown",
    },
    {
        "id": "tab-scope-tracking",
        "label": "Scope Tracking",
        "icon": "fa-project-diagram",
        "unicode_icon": "🎯",
        "color": get_color("secondary"),
        "order": 2,
        "requires_data": True,
        "help_content_id": "help-scope",
    },
    {
        "id": "tab-bug-analysis",
        "label": "Bug Analysis",
        "icon": "fa-bug",
        "unicode_icon": "🐛",
        "color": get_color("danger"),
        "order": 3,
        "requires_data": True,
        "help_content_id": "help-bug-analysis",
    },
    {
        "id": "tab-flow-metrics",
        "label": "Flow Metrics",
        "icon": "fa-stream",
        "unicode_icon": "🌊",
        "color": get_color("success"),
        "order": 4,
        "requires_data": False,
        "help_content_id": "help-flow",
    },
    {
        "id": "tab-dora-metrics",
        "label": "DORA Metrics",
        "icon": "fa-rocket",
        "unicode_icon": "🚀",
        "color": get_color("primary"),
        "order": 5,
        "requires_data": False,
        "help_content_id": "help-dora",
    },
    {
        "id": "tab-sprint-tracker",
        "label": "Sprint Tracker",
        "icon": "fa-running",
        "unicode_icon": "🏃",
        "color": get_color("warning"),
        "order": 7,
        "requires_data": True,
        "help_content_id": "help-sprint-tracker",
    },
    {
        "id": "tab-active-work-timeline",
        "label": "Active Work",
        "icon": "fa-clipboard-list",
        "unicode_icon": "📋",
        "color": get_color("info"),
        "order": 6,
        "requires_data": True,
        "help_content_id": "help-active-work",
    },
    {
        "id": "tab-statistics-data",
        "label": "Weekly Data",
        "icon": "fa-table",
        "unicode_icon": "📅",
        "color": get_color("secondary"),
        "order": 8,
        "requires_data": True,
        "help_content_id": "help-statistics-data",
    },
]


def get_tab_by_id(tab_id: str) -> TabConfig | None:

    for tab in TAB_CONFIG:
        if tab["id"] == tab_id:
            return tab
    return None


def get_tabs_sorted() -> list[TabConfig]:

    return sorted(TAB_CONFIG, key=lambda t: t["order"])


def validate_tab_id(tab_id: str) -> bool:

    return any(tab["id"] == tab_id for tab in TAB_CONFIG)


def create_desktop_tabs_only():
    tabs_config = get_tabs_sorted()

    tabs = [
        dbc.Tab(
            label=f"{tab.get('unicode_icon', '')} {tab['label']}",
            tab_id=tab["id"],
            label_style={"cursor": "pointer"},
        )
        for tab in tabs_config
    ]

    return html.Div(
        [
            dbc.Tabs(
                tabs,
                id="chart-tabs",
                active_tab="tab-dashboard",
                className="mb-0 nav-tabs-modern d-none d-md-flex",
            )
        ],
        className="desktop-tab-navigation",
    )


def create_tabs():

    tab_config = get_mobile_tabs_config()

    tabs = []
    for tab in tab_config:
        tabs.append(
            dbc.Tab(
                label=f"{tab.get('unicode_icon', '')} {tab['label']}",
                tab_id=tab["id"],
                labelClassName="fw-bold tab-with-icon",
                activeLabelClassName="text-primary fw-bold",
                tab_style={"minWidth": "150px"},
            )
        )

    return html.Div(id="tab-content", className="tab-content-container")


def create_tab_content(active_tab, charts, statistics_df=None, pert_data=None):

    if active_tab not in [
        "tab-burndown",
        "tab-scope-tracking",
        "tab-bug-analysis",
        "tab-flow-metrics",
        "tab-dora-metrics",
        "tab-statistics-data",
    ]:
        active_tab = "tab-burndown"

    tab_info_cards = {
        "tab-burndown": create_forecast_info_card(),
        "tab-scope-tracking": html.Div(),
        "tab-bug-analysis": html.Div(),
        "tab-dora-metrics": html.Div(),
        "tab-flow-metrics": html.Div(),
        "tab-statistics-data": html.Div(),
    }

    tab_titles = {
        "tab-burndown": html.Div(
            [
                html.I(
                    className="fas fa-chart-line me-2",
                    style={"color": get_color("info")},
                ),
                "Project Burndown Forecast",
                create_info_tooltip(
                    CHART_HELP_TEXTS["burndown_vs_burnup"],
                    "Burndown vs Burnup chart differences "
                    "and when to use each approach",
                ),
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-scope-tracking": html.Div(
            [
                html.I(
                    className="fas fa-chart-bar me-2",
                    style={"color": get_color("secondary")},
                ),
                "Scope Change Analysis",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-bug-analysis": html.Div(
            [
                html.I(
                    className="fas fa-bug me-2", style={"color": get_color("danger")}
                ),
                "Bug Analysis & Quality Insights",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-dora-metrics": html.Div(
            [
                html.I(
                    className="fas fa-rocket me-2",
                    style={"color": get_color("primary")},
                ),
                "DORA Metrics",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-flow-metrics": html.Div(
            [
                html.I(
                    className="fas fa-stream me-2",
                    style={"color": get_color("success")},
                ),
                "Flow Metrics",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
        "tab-statistics-data": html.Div(
            [
                html.I(
                    className="fas fa-table me-2",
                    style={"color": get_color("secondary")},
                ),
                "Weekly Data",
            ],
            className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
        ),
    }

    return grid_create_tab_content(
        [
            html.H4(
                tab_titles.get(active_tab, "Chart View"),
                className="mb-4 pb-2 border-bottom",
            ),
            charts.get(
                active_tab, charts.get("tab-burndown", html.Div("Loading chart..."))
            ),
            tab_info_cards.get(active_tab, html.Div()),
        ],
        padding="p-4",
    )
