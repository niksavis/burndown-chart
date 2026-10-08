from dash import Input, Output, State, callback, clientside_callback


@callback(
    Output("about-modal", "is_open"),
    [
        Input("about-button", "n_clicks"),
        Input("about-close-button", "n_clicks"),
    ],
    [State("about-modal", "is_open")],
    prevent_initial_call=True,
)
def toggle_about_modal(
    about_clicks: int | None, close_clicks: int | None, is_open: bool
) -> bool:

    return not is_open


@callback(
    Output("about-tabs", "active_tab"),
    Input("view-changelog-link", "n_clicks"),
    prevent_initial_call=True,
)
def switch_to_changelog_tab(n_clicks: int | None) -> str:

    return "about-tab-changelog"


clientside_callback(
    """
    function(isOpen, searchValue) {
        // Only run filter if modal is open
        if (isOpen) {
            return window.dash_clientside.about_dialog.filterLicenses(searchValue);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("license-count-text", "children"),
    Input("about-modal", "is_open"),
    Input("license-search-input", "value"),
    prevent_initial_call=False,
)
