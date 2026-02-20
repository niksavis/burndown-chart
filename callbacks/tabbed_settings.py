"""
Tabbed Settings Panel Callbacks

Manages dynamic updates to tabbed settings panel including:
- Status icon updates for tab labels (unique to tabbed UI)

NOTE: Data operations button management is handled by accordion_settings.py
which works for both UIs since component IDs are the same.

NOTE: Tab label status icons are NOT implemented because dbc.Tab v2.0.2
does not support label_id parameter. This would require upgrading to a newer
version of dash-bootstrap-components or using a different approach.
"""

import logging

logger = logging.getLogger(__name__)

# Tab label callback disabled - dbc.Tab v2.0.2 doesn't support label_id
# @callback(
#     [
#         Output("profile-tab-label", "children"),
#         Output("jira-tab-label", "children"),
#         Output("fields-tab-label", "children"),
#         Output("queries-tab-label", "children"),
#         Output("data-tab-label", "children"),
#     ],
#     Input("configuration-status-store", "data"),
#     prevent_initial_call=False,
# )
# def update_tab_labels_with_status(config_status):
#     ...

logger.info(
    "[Callbacks] Tabbed settings panel callbacks registered "
    "(tab label updates disabled - dbc 2.0.2 limitation)"
)
