"""
Icon Implementation Sample

This file demonstrates how to use the new icon utility functions to create consistent
icon+text patterns throughout the application.

This is a reference implementation that shows how to convert existing icon usage
to the new standardized approach.
"""

from dash import html
from ui.icon_utils import (
    create_icon,
    create_icon_text,
    create_icon_stack,
)


def example_before_refactoring():
    """
    Example of inconsistent icon usage before refactoring.
    """
    return html.Div(
        [
            # Inconsistent icon implementation
            html.Div(
                [
                    html.I(
                        className="fas fa-info-circle text-info ml-2",
                        style={"cursor": "pointer", "marginLeft": "5px"},
                    ),
                    html.Span("Information text", style={"marginLeft": "5px"}),
                ],
                className="d-flex align-items-center",
            ),
            # Inconsistent spacing and alignment
            html.Div(
                [
                    html.I(
                        className="fas fa-tasks",
                        style={"color": "#0d6efd", "marginRight": "8px"},
                    ),
                    html.Span("73 items remaining"),
                ],
                className="d-flex",
            ),
            # Another inconsistent implementation
            html.Div(
                [
                    html.Span("Project on schedule "),
                    html.I(
                        className="fas fa-check-circle",
                        style={"color": "green"},
                    ),
                ]
            ),
        ]
    )


def example_after_refactoring():
    """
    Example of standardized icon usage after refactoring.
    """
    return html.Div(
        [
            # Standardized information icon+text
            create_icon_text(
                icon="info", text="Information text", color="info", alignment="center"
            ),
            # Standardized tasks icon+text
            create_icon_text(
                icon="items",  # Using semantic icon name
                text="73 items remaining",
                icon_color="primary",
                alignment="center",
            ),
            # Standardized check icon+text with right-aligned icon
            create_icon_text(
                icon="success",  # Using semantic icon name
                text="Project on schedule",
                color="success",
                icon_position="right",
                alignment="center",
            ),
            # Standalone icon with tooltip (for small UI elements)
            html.Div(
                [
                    create_icon(
                        icon="warning",
                        color="warning",
                        size="lg",
                        id="warning-icon",
                        with_fixed_width=True,
                    ),
                    html.Div(
                        "Approach with caution",
                        id="warning-tooltip",
                        style={"display": "none"},
                    ),
                ]
            ),
            # Stacked icon for combined meaning
            create_icon_stack(
                primary_icon="chart",
                secondary_icon="success",
                primary_color="primary",
                secondary_color="success",
            ),
        ]
    )


def example_icon_sizing():
    """
    Example of consistent icon sizing based on hierarchy.
    """
    return html.Div(
        [
            # Section header with large icon
            html.H3(
                [
                    create_icon(
                        icon="data", size="xl", color="primary", with_space_right=True
                    ),
                    "Data Overview",
                ],
                className="d-flex align-items-center",
            ),
            # Standard paragraph with medium icon
            html.P(
                [
                    create_icon_text(
                        icon="info",
                        text="This is a medium-sized icon for standard content",
                        icon_size="md",
                        alignment="center",
                    )
                ]
            ),
            # Small inline icon
            html.Span(
                [
                    "Check the ",
                    create_icon(
                        icon="settings",
                        size="sm",
                        with_space_left=True,
                        with_space_right=True,
                    ),
                    " settings for more options",
                ],
                className="small text-muted d-flex align-items-center",
            ),
        ]
    )
