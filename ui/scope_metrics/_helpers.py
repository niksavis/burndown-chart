"""Scope Metrics Small Helper Components

Provides small shared UI components: alert stub, forecast pill, metrics header.
"""

from dash import html

# PRINCIPAL ENGINEER: Stubbed out create_scope_change_alert
# to fix import errors.
# The alert banner was causing component lifecycle issues in Dash,
# appearing in wrong tabs.
# All scope change information is already displayed in the metrics cards above,
# making this banner redundant. The function now returns an empty div to maintain
# backwards compatibility with imports.


def create_scope_change_alert(alert_data):
    """DEPRECATED: Returns empty div. Alert banner removed to fix tab switching bug."""
    return html.Div()  # Always return empty div


# For backwards compatibility
create_scope_creep_alert = create_scope_change_alert


def create_forecast_pill(label, value, variant):
    """
    Create a forecast pill component.

    Args:
        label: The label for the pill
        value: The value to display
        variant: The color variant for the pill indicator

    Returns:
        html.Div: A forecast pill component
    """
    return html.Div(
        className=f"forecast-pill forecast-pill--{variant}",
        children=[
            html.I(className="fas fa-chart-line me-1 forecast-icon"),
            html.Small(
                [f"{label}: ", html.Strong(f"{value}", className="forecast-value")]
            ),
        ],
    )


def create_scope_metrics_header(title, icon, color):
    """
    Create a header for scope metrics similar to trend headers.

    Args:
        title: The title to display
        icon: The icon class
        color: The color class or value for the icon

    Returns:
        html.Div: A header component
    """
    return html.Div(
        className="d-flex align-items-center mb-2",
        children=[
            html.I(
                className=f"{icon} me-2 scope-metrics-header-icon",
                style={"--scope-metrics-icon-color": color},
            ),
            html.Span(title, className="fw-medium"),
        ],
    )
