"""
Settings Panel Callbacks

Handles opening/closing of the settings collapsible panel and loading
default/last used JQL query.
"""

import logging

from dash import ClientsideFunction, Input, Output, State, callback, ctx, no_update

logger = logging.getLogger(__name__)


def register_clientside_callbacks(app):
    """Register clientside callbacks for panel button active states."""

    # Parameter panel button active state
    app.clientside_callback(
        ClientsideFunction(
            namespace="panelState", function_name="toggleParameterButton"
        ),
        Output("btn-expand-parameters", "className"),
        Input("parameter-collapse", "is_open"),
        State("btn-expand-parameters", "className"),
    )

    # Settings panel button active state
    app.clientside_callback(
        ClientsideFunction(
            namespace="panelState", function_name="toggleSettingsButton"
        ),
        Output("settings-button", "className"),
        Input("settings-collapse", "is_open"),
        State("settings-button", "className"),
    )

    # Data panel button active state
    app.clientside_callback(
        ClientsideFunction(namespace="panelState", function_name="toggleDataButton"),
        Output("toggle-import-export-panel", "className"),
        Input("import-export-collapse", "is_open"),
        State("toggle-import-export-panel", "className"),
    )

    # CRITICAL: Backdrop visibility - directly controlled by panel states
    app.clientside_callback(
        ClientsideFunction(namespace="panelState", function_name="updateBackdropState"),
        Output("panel-backdrop", "className"),
        [
            Input("parameter-collapse", "is_open"),
            Input("settings-collapse", "is_open"),
            Input("import-export-collapse", "is_open"),
        ],
    )


@callback(
    [
        Output("settings-collapse", "is_open", allow_duplicate=True),
        Output("parameter-collapse", "is_open", allow_duplicate=True),
        Output("import-export-collapse", "is_open", allow_duplicate=True),
    ],
    [
        Input("settings-button", "n_clicks"),
    ],
    [
        State("settings-collapse", "is_open"),
        State("parameter-collapse", "is_open"),
        State("import-export-collapse", "is_open"),
    ],
    prevent_initial_call=True,
)
def toggle_settings_panel(
    settings_clicks, settings_is_open, parameter_is_open, import_export_is_open
):
    """
    Toggle settings panel open/close and close other panels if open.

    This ensures only one flyout panel is open at a time for better UX.
    Responds to the main settings button in the parameter bar.

    Works with both accordion UI (inside flyout) and legacy UI.

    Args:
        settings_clicks: Number of clicks on main settings button
        settings_is_open: Current settings panel state
        parameter_is_open: Current parameter panel state
        import_export_is_open: Current import/export panel state

    Returns:
        tuple: (new_settings_state, new_parameter_state, new_import_export_state)
    """
    # Check which button triggered the callback
    if not ctx.triggered_id:
        logger.warning("No trigger ID - preventing panel state change")
        return no_update, no_update, no_update

    # CRITICAL FIX: Prevent firing on initial button render
    if settings_clicks is None:
        logger.warning(
            "Settings button clicks is None - this is initial render, "
            "returning no_update"
        )
        return no_update, no_update, no_update

    if settings_clicks == 0:
        logger.warning(
            "Settings button clicks is 0 - this is initial state, returning no_update"
        )
        return no_update, no_update, no_update

    new_settings_state = not settings_is_open
    logger.info(f"Toggling settings panel to: {new_settings_state}")

    # If opening settings panel, close other panels
    new_parameter_state = no_update
    new_import_export_state = no_update

    if new_settings_state:
        if parameter_is_open:
            logger.info("Closing parameter panel because settings panel is opening")
            new_parameter_state = False
        if import_export_is_open:
            logger.info("Closing import/export panel because settings panel is opening")
            new_import_export_state = False

    return (
        new_settings_state,
        new_parameter_state,
        new_import_export_state,
    )


@callback(
    [
        Output("import-export-collapse", "is_open", allow_duplicate=True),
        Output("settings-collapse", "is_open", allow_duplicate=True),
        Output("parameter-collapse", "is_open", allow_duplicate=True),
    ],
    [
        Input("toggle-import-export-panel", "n_clicks"),
    ],
    [
        State("import-export-collapse", "is_open"),
        State("settings-collapse", "is_open"),
        State("parameter-collapse", "is_open"),
    ],
    prevent_initial_call=True,
)
def toggle_import_export_panel(
    import_export_clicks, import_export_is_open, settings_is_open, parameter_is_open
):
    """
    Toggle import/export panel open/close and close other panels if open.

    Args:
        import_export_clicks: Number of clicks on Data button
        import_export_is_open: Current import/export panel state
        settings_is_open: Current settings panel state
        parameter_is_open: Current parameter panel state

    Returns:
        tuple: (new_import_export_state, new_settings_state, new_parameter_state)
    """
    if not ctx.triggered_id:
        logger.warning("No trigger ID for import/export panel")
        return no_update, no_update, no_update

    if import_export_clicks is None or import_export_clicks == 0:
        logger.warning(
            "Import/export button clicks is initial state, returning no_update"
        )
        return no_update, no_update, no_update

    new_import_export_state = not import_export_is_open
    new_settings_state = False if settings_is_open else no_update
    new_parameter_state = False if parameter_is_open else no_update

    logger.info(
        "Toggling import/export panel to: "
        f"{new_import_export_state}, closing other panels"
    )

    return new_import_export_state, new_settings_state, new_parameter_state


@callback(
    Output("settings-collapse", "is_open", allow_duplicate=True),
    Input("settings-collapse-btn", "n_clicks"),
    State("settings-collapse", "is_open"),
    prevent_initial_call=True,
)
def collapse_settings_panel(n_clicks, is_open):
    """Collapse settings panel when collapse button is clicked."""
    if n_clicks:
        logger.info("Settings collapse button clicked - closing panel")
        return False
    return no_update


@callback(
    Output("parameter-collapse", "is_open", allow_duplicate=True),
    Input("parameter-collapse-btn", "n_clicks"),
    State("parameter-collapse", "is_open"),
    prevent_initial_call=True,
)
def collapse_parameter_panel(n_clicks, is_open):
    """Collapse parameter panel when collapse button is clicked."""
    if n_clicks:
        logger.info("Parameter collapse button clicked - closing panel")
        return False
    return no_update


@callback(
    Output("import-export-collapse", "is_open", allow_duplicate=True),
    Input("import-export-collapse-btn", "n_clicks"),
    State("import-export-collapse", "is_open"),
    prevent_initial_call=True,
)
def collapse_import_export_panel(n_clicks, is_open):
    """Collapse import/export panel when collapse button is clicked."""
    if n_clicks:
        logger.info("Import/Export collapse button clicked - closing panel")
        return False
    return no_update


# Function removed - was causing undefined variable errors and not being used
