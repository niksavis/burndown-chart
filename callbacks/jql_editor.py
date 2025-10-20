"""
JQL Editor callbacks for syncing textarea to dcc.Store.

This module provides callbacks to bridge the gap between the visible textarea
(which users interact with) and the dcc.Store (which other callbacks read from).
"""

from dash import Input, Output, callback


def register_jql_editor_callbacks(app):
    """
    Register callbacks for JQL editor synchronization.

    Args:
        app: Dash application instance
    """

    @app.callback(
        Output("jira-jql-query", "data", allow_duplicate=True),
        Input(
            "jira-jql-query-textarea", "value"
        ),  # html.Textarea does support 'value' for callbacks
        prevent_initial_call=True,  # Required when using allow_duplicate
    )
    def sync_jql_textarea_to_store(textarea_value):
        """
        Sync the JQL editor textarea value to the dcc.Store.

        This allows other callbacks that read from the Store to get the current
        editor value whenever the user types in the textarea.

        Args:
            textarea_value: Current value of the JQL textarea

        Returns:
            str: The textarea value to store in dcc.Store
        """
        return textarea_value if textarea_value is not None else ""

    @app.callback(
        Output("jira-jql-query-textarea", "value", allow_duplicate=True),
        Input("jira-jql-query", "data"),
        prevent_initial_call=True,  # Only update when Store changes (not on initial load)
    )
    def sync_jql_store_to_textarea(store_value):
        """
        Sync the dcc.Store value back to the textarea.

        This allows loading saved queries and other operations that update the Store
        to also update the visible textarea so users see the changes.

        Args:
            store_value: Current value in the dcc.Store

        Returns:
            str: The store value to display in textarea
        """
        return store_value if store_value is not None else ""
