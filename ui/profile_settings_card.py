from dash import html

from ui.profile_selector import create_profile_selector_panel


def create_profile_settings_card() -> html.Div:

    return html.Div(
        [
            html.Div(
                [
                    html.I(className="fas fa-user me-2 text-primary"),
                    html.Span("Profile Management", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            create_profile_selector_panel(),
        ]
    )
