"""Modern Tab Wrapper for consistent DORA/Flow-style design across all tabs.

This module provides a reusable wrapper that adds the modern visual design to any tab content,
ensuring consistency with DORA and Flow metrics pages.
"""

from typing import Optional, List, Any
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_modern_tab_wrapper(
    tab_id: str,
    tab_title: str,
    tab_icon: str,
    main_content: Any,
    overview_content: Optional[Any] = None,
    info_content: Optional[Any] = None,
    show_welcome_banner: bool = True,
    info_banner_text: Optional[str] = None,
) -> html.Div:
    """Create a modern tab wrapper with DORA/Flow-style design.

    Args:
        tab_id: Unique identifier for the tab
        tab_title: Display title for the tab
        tab_icon: Font Awesome icon class (e.g., "fa-chart-line")
        main_content: Main content (charts, cards, etc.)
        overview_content: Optional overview section content (will be wrapped in gray card)
        info_content: Optional information/help content
        show_welcome_banner: Whether to show dismissible welcome banner
        info_banner_text: Optional informational banner text

    Returns:
        Wrapped tab content with modern styling
    """
    tab_content = []

    # Welcome banner (dismissible, stored in localStorage)
    if show_welcome_banner:
        tab_content.extend(
            [
                dcc.Store(
                    id=f"{tab_id}-welcome-dismissed", storage_type="local", data=False
                ),
                html.Div(
                    id=f"{tab_id}-welcome-banner",
                    children=[],  # Will be populated by callback based on storage
                ),
            ]
        )

    # Overview section with light gray background (if provided)
    if overview_content:
        tab_content.append(
            html.Div(
                id=f"{tab_id}-overview-wrapper",
                children=[
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    id=f"{tab_id}-overview",
                                    children=overview_content,
                                ),
                            ],
                            className="pt-3 px-3 pb-0",
                        ),
                        className="mb-3 overview-section",
                        style={
                            "backgroundColor": "#f8f9fa",
                            "border": "none",
                            "borderRadius": "8px",
                        },
                    ),
                ],
                style={"display": "block"},
            )
        )

    # Info banner (if provided)
    if info_banner_text:
        tab_content.append(
            html.P(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    info_banner_text,
                ],
                className="text-muted small mb-3 mt-3",
            )
        )

    # Main content section
    tab_content.append(
        html.Div(
            id=f"{tab_id}-main-content",
            children=main_content,
            className="mb-4",
        )
    )

    # Information/help section (if provided)
    if info_content:
        tab_content.append(
            html.Div(
                id=f"{tab_id}-info-section",
                children=info_content,
                style={"display": "block"},
            )
        )

    return html.Div(
        tab_content,
        className=f"{tab_id}-container py-4",
    )


def create_tab_overview_section(metrics: List[dict]) -> html.Div:
    """Create overview section for a tab with metric summaries.

    Args:
        metrics: List of metric dictionaries with keys:
            - label: Display label
            - value: Metric value
            - color: CSS color for the value
            - icon: Optional font awesome icon class

    Returns:
        Overview section component
    """
    cols = []

    for metric in metrics:
        label = metric.get("label", "")
        value = metric.get("value", "N/A")
        color = metric.get("color", "#0d6efd")
        icon = metric.get("icon")

        col_content = [
            html.Small(label, className="text-muted text-uppercase d-block mb-1"),
            html.H4(
                value,
                className="mb-0",
                style={"color": color},
            ),
        ]

        # Add icon if provided
        if icon:
            col_content.insert(0, html.I(className=f"{icon} me-2 text-muted"))

        cols.append(
            dbc.Col(
                html.Div(
                    col_content,
                    className="text-center",
                ),
                xs=6,
                md=3,
                className="mb-3",
            )
        )

    return html.Div(
        [
            dbc.Row(cols, className="g-3"),
        ]
    )


def create_tab_info_section(
    title: str,
    icon: str,
    sections: List[dict],
    additional_content: Optional[Any] = None,
) -> dbc.Row:
    """Create information/help section for a tab.

    Args:
        title: Section title
        icon: Font Awesome icon class
        sections: List of section dictionaries with keys:
            - title: Section title
            - description: Section description
            - icon: Icon class
            - color: Icon color
        additional_content: Optional additional content after sections

    Returns:
        Information section component
    """
    section_rows = []

    # Create two columns per row
    for i in range(0, len(sections), 2):
        row_sections = sections[i : i + 2]
        row_cols = []

        for section in row_sections:
            row_cols.append(
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.I(
                                    className=f"{section['icon']} {section.get('color', 'text-primary')} me-2"
                                ),
                                html.Strong(section["title"]),
                            ],
                            className="mb-1",
                        ),
                        html.P(
                            section["description"],
                            className="text-muted small mb-0",
                        ),
                    ],
                    md=6,
                    className="mb-3",
                )
            )

        section_rows.append(dbc.Row(row_cols))

    content = [
        html.P(
            f"{title} provides insights into:",
            className="mb-3",
        ),
        *section_rows,
    ]

    if additional_content:
        content.extend(
            [
                html.Hr(className="my-3"),
                additional_content,
            ]
        )

    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.I(className=f"{icon} me-2"),
                                    f"About {title}",
                                ],
                                className="fw-bold",
                            ),
                            dbc.CardBody(content),
                        ],
                        className="border-0 shadow-sm",
                    ),
                ],
                width=12,
            ),
        ],
        className="mb-4",
    )
