"""
Component Utilities Module

Small utility widgets for common UI patterns.
Extracted from ui/components.py during refactoring (bd-rnol).
"""

import dash_bootstrap_components as dbc
from dash import html

from ui.button_utils import create_button
from ui.icon_utils import create_icon_text


def create_export_buttons(chart_id=None, statistics_data=None):
    """
    Create a row of export buttons for charts or statistics data.

    Args:
        chart_id: ID of the chart for export filename
        statistics_data: Statistics data to export
            (if provided, shows statistics export button)

    Returns:
        Dash Div component with export buttons
    """
    buttons = []

    if chart_id:
        # Add PNG export button for charts using the new button styling system
        png_button = create_button(
            children=[html.I(className="fas fa-file-image me-2"), "Export Image"],
            id=f"{chart_id}-png-button",
            variant="secondary",
            size="sm",
            outline=True,
            tooltip="Export chart as image",
            className="me-2",
        )
        buttons.append(png_button)

    return html.Div(
        buttons,
        className="d-flex justify-content-end mb-3",
    )


def create_error_alert(
    message="An unexpected error occurred. Please try again later.",
    title="Error",
    error_details=None,
):
    """
    Creates a standardized Bootstrap Alert component for displaying errors.

    Args:
        message (str): The main user-friendly error message.
        title (str): The title for the alert.
        error_details (str, optional): Additional technical details to display,
                                       potentially hidden by default.

    Returns:
        dbc.Alert: A Dash Bootstrap Components Alert.
    """
    children = [
        html.H4(
            create_icon_text("error", title, size="md"),
            className="alert-heading d-flex align-items-center",
        ),
        html.P(message),
    ]
    if error_details:
        children.extend(
            [
                html.Hr(),
                html.P(f"Details: {error_details}", className="mb-0 small text-muted"),
            ]
        )

    return dbc.Alert(
        children,
        color="danger",
        dismissable=True,
        className="error-alert",
    )
