from dash import html


def create_scope_change_alert(alert_data):
    return html.Div()


create_scope_creep_alert = create_scope_change_alert


def create_forecast_pill(label, value, variant):

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
