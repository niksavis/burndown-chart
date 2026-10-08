import dash_bootstrap_components as dbc
from dash import html

from data.persistence import load_app_settings
from ui.profile_modals import (
    create_profile_deletion_modal,
    create_profile_form_modal,
)
from ui.tabbed_settings_panel import create_tabbed_settings_panel


def _get_default_jql_query():
    try:
        app_settings = load_app_settings()
        return app_settings.get("jql_query", "project = JRASERVER")
    except ImportError:
        return "project = JRASERVER"


def create_improved_settings_panel(is_open: bool = False):

    return html.Div(
        [
            dbc.Collapse(
                create_settings_panel_content(),
                id="settings-collapse",
                is_open=is_open,
            ),
            create_profile_form_modal(),
            create_profile_deletion_modal(),
        ],
        id="settings-panel",
        className="settings-panel-container",
    )


def create_settings_panel_content():

    return create_tabbed_settings_panel()


def create_settings_panel():
    return create_improved_settings_panel()
