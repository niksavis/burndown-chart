"""
JQL Editor callbacks for syncing CodeMirror to dcc.Store.

Uses polling via dcc.Interval to read CodeMirror value from JavaScript
and update the Store. This works because dcc.Store cannot be updated
directly from JavaScript.
"""

import logging

logger = logging.getLogger(__name__)


def register_jql_editor_callbacks(app):
    """
    Register callbacks for JQL editor synchronization.

    Note: With the hybrid textarea + CodeMirror approach, most synchronization
    happens automatically via CodeMirror.fromTextArea(). This callback file is
    kept for potential future enhancements, but core functionality works without it.

    Args:
        app: Dash application instance
    """
    # No callbacks needed - CodeMirror.fromTextArea() automatically syncs:
    # - User types in CodeMirror → textarea.value updates
    # - Callbacks read from Input("jira-jql-query", "value")
    # - Callbacks update Output("jira-jql-query", "value")
    # - textarea.value changes → CodeMirror reflects changes
    #
    # This is handled entirely by CodeMirror's native fromTextArea() method
    # See: assets/jql_editor_init.js for implementation details
    pass
