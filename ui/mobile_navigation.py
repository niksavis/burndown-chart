import dash_bootstrap_components as dbc
from dash import html

from configuration.settings import get_bug_analysis_config


def create_mobile_drawer_navigation(tabs_config):

    drawer_items = []

    for tab in tabs_config:
        drawer_items.append(
            html.Li(
                dbc.Button(
                    [html.I(className=f"{tab['icon']} me-3"), tab["label"]],
                    id=f"drawer-{tab['id']}",
                    color="link",
                    className="mobile-drawer-item w-100 text-start",
                    style={"color": "#495057"},
                ),
                className="mb-2",
            )
        )

    return html.Div(
        [
            html.Div(
                id="mobile-drawer-overlay",
                className="mobile-drawer-overlay",
                style={"display": "none"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H6("Navigation", className="mb-0 text-muted"),
                            dbc.Button(
                                html.I(className="fas fa-times"),
                                id="mobile-drawer-close",
                                color="link",
                                size="sm",
                                className="p-1",
                            ),
                        ],
                        className=(
                            "mobile-drawer-header d-flex "
                            "justify-content-between align-items-center "
                            "p-3 border-bottom"
                        ),
                    ),
                    html.Div(
                        html.Ul(drawer_items, className="list-unstyled mb-0"),
                        className="mobile-drawer-body p-3",
                    ),
                ],
                id="mobile-drawer",
                className="mobile-drawer",
                style={"transform": "translateX(-100%)"},
            ),
        ],
        id="mobile-drawer-container",
    )


def create_mobile_bottom_navigation(tabs_config, active_tab="tab-dashboard"):

    nav_items = []

    primary_tabs = [tab for tab in tabs_config if tab.get("show_in_bottom_nav", True)]

    for tab in primary_tabs:
        is_active = tab["id"] == active_tab
        nav_items.append(
            html.Div(
                [
                    html.Button(
                        [
                            html.I(className=tab["icon"], style={"fontSize": "1.1rem"}),
                            html.Div(
                                tab["short_label"],
                                className="mobile-bottom-nav-label",
                            ),
                        ],
                        id=f"bottom-nav-{tab['id']}",
                        className=(
                            f"mobile-bottom-nav-item {'active' if is_active else ''}"
                        ),
                        style={
                            "color": tab["color"] if is_active else "#6c757d",
                            "flexDirection": "column",
                            "border": "none",
                            "background": "rgba(13, 110, 253, 0.1)"
                            if is_active
                            else "transparent",
                            "padding": "0.375rem",
                            "minHeight": "44px",
                            "minWidth": "44px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "textDecoration": "none",
                            "transition": "all 0.2s ease",
                            "borderRadius": "0.5rem",
                            "fontWeight": "600" if is_active else "normal",
                        },
                    )
                ],
                className="mobile-bottom-nav-wrapper",
            )
        )

    nav_items.append(
        html.Div(
            [
                html.Button(
                    [
                        html.I(
                            className="fas fa-ellipsis-h", style={"fontSize": "1.1rem"}
                        ),
                        html.Div(
                            "More",
                            className="mobile-bottom-nav-label",
                        ),
                    ],
                    id="bottom-nav-more-menu",
                    className="mobile-bottom-nav-item",
                    style={
                        "color": "#6c757d",
                        "flexDirection": "column",
                        "border": "none",
                        "background": "transparent",
                        "padding": "0.375rem",
                        "minHeight": "44px",
                        "minWidth": "44px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "textDecoration": "none",
                        "transition": "all 0.2s ease",
                        "borderRadius": "0.5rem",
                    },
                )
            ],
            className="mobile-bottom-nav-wrapper",
        )
    )

    return html.Div(
        nav_items,
        id="mobile-bottom-navigation",
        className="mobile-bottom-navigation d-md-none",
    )


def create_mobile_tab_controls():

    return html.Div(
        [
            dbc.Button(
                html.I(className="fas fa-bars"),
                id="mobile-menu-toggle",
                color="outline-secondary",
                size="sm",
                className="mobile-menu-toggle d-md-none mobile-touch-target-sm",
                style={"minWidth": "44px", "minHeight": "44px"},
            ),
            html.Div(
                [
                    html.I(className="fas fa-chevron-left me-1"),
                    html.Small("Swipe to navigate", className="text-muted"),
                    html.I(className="fas fa-chevron-right ms-1"),
                ],
                id="mobile-swipe-indicator",
                className="mobile-swipe-indicator d-md-none text-center mt-2",
            ),
        ],
        className="mobile-tab-controls",
    )


def create_mobile_tab_wrapper(children):

    return html.Div(
        [
            create_mobile_tab_controls(),
            html.Div(
                children,
                className="mobile-tab-content-wrapper swipe-enabled",
                id="mobile-tab-content-wrapper",
            ),
        ],
        className="mobile-tab-container",
    )


def get_mobile_tabs_config():

    tabs = [
        {
            "id": "tab-dashboard",
            "label": "Dashboard",
            "short_label": "Dashboard",
            "icon": "fas fa-tachometer-alt",
            "color": "#0d6efd",
            "show_in_bottom_nav": True,
        },
        {
            "id": "tab-burndown",
            "label": "Burndown",
            "short_label": "Chart",
            "icon": "fas fa-chart-line",
            "color": "#0d6efd",
            "show_in_bottom_nav": True,
        },
        {
            "id": "tab-scope-tracking",
            "label": "Scope Changes",
            "short_label": "Scope",
            "icon": "fas fa-project-diagram",
            "color": "#6f42c1",
            "show_in_bottom_nav": True,
        },
    ]

    bug_config = get_bug_analysis_config()
    if bug_config.get("enabled", True):
        tabs.append(
            {
                "id": "tab-bug-analysis",
                "label": "Bug Analysis",
                "short_label": "Bugs",
                "icon": "fas fa-bug",
                "color": "#dc3545",
                "show_in_bottom_nav": True,
            }
        )

    tabs.append(
        {
            "id": "tab-dora-metrics",
            "label": "DORA Metrics",
            "short_label": "DORA",
            "icon": "fas fa-rocket",
            "color": "#6610f2",
            "show_in_bottom_nav": True,
        }
    )

    tabs.append(
        {
            "id": "tab-flow-metrics",
            "label": "Flow Metrics",
            "short_label": "Flow",
            "icon": "fas fa-stream",
            "color": "#20c997",
            "show_in_bottom_nav": True,
        }
    )

    tabs.append(
        {
            "id": "tab-active-work-timeline",
            "label": "Active Work",
            "short_label": "Active",
            "icon": "fas fa-clipboard-list",
            "color": "#17a2b8",
            "show_in_bottom_nav": False,
        }
    )

    tabs.append(
        {
            "id": "tab-sprint-tracker",
            "label": "Sprint Tracker",
            "short_label": "Sprint",
            "icon": "fas fa-running",
            "color": "#ffc107",
            "show_in_bottom_nav": False,
        }
    )

    tabs.append(
        {
            "id": "tab-statistics-data",
            "label": "Weekly Data",
            "short_label": "Data",
            "icon": "fas fa-table",
            "color": "#6c757d",
            "show_in_bottom_nav": False,
        }
    )

    return tabs


def create_mobile_overflow_menu(tabs_config):

    overflow_tabs = [
        tab for tab in tabs_config if not tab.get("show_in_bottom_nav", True)
    ]

    overflow_items = []
    for tab in overflow_tabs:
        overflow_items.append(
            html.Button(
                [
                    html.I(
                        className=f"{tab['icon']} me-3",
                        style={"fontSize": "1.2rem", "color": tab["color"]},
                    ),
                    html.Span(tab["label"], style={"fontSize": "1rem"}),
                ],
                id=f"overflow-menu-{tab['id']}",
                className="mobile-overflow-menu-item w-100 text-start",
                style={
                    "border": "none",
                    "background": "transparent",
                    "padding": "1rem",
                    "display": "flex",
                    "alignItems": "center",
                    "color": "#212529",
                    "transition": "background 0.2s ease",
                },
            )
        )

    return html.Div(
        [
            html.Div(
                id="mobile-overflow-overlay",
                className="mobile-overflow-overlay",
                style={"display": "none"},
            ),
            html.Div(
                [
                    html.Div(
                        html.Div(
                            className="mobile-overflow-handle",
                            style={
                                "width": "40px",
                                "height": "4px",
                                "backgroundColor": "#dee2e6",
                                "borderRadius": "2px",
                                "margin": "0 auto",
                            },
                        ),
                        className="mobile-overflow-header p-3 text-center",
                        style={"cursor": "pointer"},
                        id="mobile-overflow-header",
                    ),
                    html.Div(
                        overflow_items,
                        className="mobile-overflow-body",
                        style={"padding": "0.5rem 0"},
                    ),
                ],
                id="mobile-overflow-menu",
                className="mobile-overflow-menu",
                style={"transform": "translateY(100%)"},
            ),
        ],
        id="mobile-overflow-container",
    )


def create_mobile_navigation_system():

    tabs_config = get_mobile_tabs_config()

    return html.Div(
        [
            create_mobile_drawer_navigation(tabs_config),
            create_mobile_bottom_navigation(tabs_config),
            create_mobile_overflow_menu(tabs_config),
        ]
    )
