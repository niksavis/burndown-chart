"""
JQL Editor Component

Factory function for creating CodeMirror 6-based JQL editor components.
Returns html.Div() container with CodeMirror initialization target and dcc.Store() for state sync.

Architecture:
    - Python creates container structure (html.Div + dcc.Store + hidden textarea)
    - JavaScript (assets/jql_editor_init.js) initializes CodeMirror in browser
    - dcc.Store synchronizes editor value with Dash callbacks
    - Hidden textarea provides accessibility fallback

Integration:
    ```python
    from ui.jql_editor import create_jql_editor

    layout = html.Div([
        create_jql_editor(
            editor_id="jira-jql-query",
            initial_value="project = TEST",
            placeholder="Enter JQL query..."
        )
    ])

    # In callback, read from dcc.Store:
    @app.callback(
        Output(...),
        Input("jira-jql-query", "data")  # Note: "data" property, not "value"
    )
    def process_query(jql_query):
        return perform_search(jql_query)
    ```

Requirements:
    - CodeMirror 6 must be loaded via CDN in app.py external_scripts
    - assets/jql_editor_init.js must exist to initialize editors
    - assets/jql_language_mode.js must exist for JQL tokenization
    - CSS token classes (.cm-jql-*) must be defined in assets/custom.css
"""

from dash import html


def create_jql_editor(
    editor_id: str,
    initial_value: str = "",
    placeholder: str = "Enter JQL query (e.g., project = TEST AND status = Done)",
    class_name: str = "",
    rows: int = 3,
) -> html.Div:
    """
    Create a JQL editor component with CodeMirror 5 syntax highlighting.

    CRITICAL: Returns a dbc.Textarea component (source of truth for callbacks)
    wrapped in a container that JavaScript will enhance with CodeMirror overlay.

    This maintains backward compatibility - callbacks read from textarea "value" property
    exactly as before, while CodeMirror provides syntax highlighting as a visual enhancement.

    Args:
        editor_id: Unique identifier for textarea (e.g., "jira-jql-query")
        initial_value: Initial JQL query to display
        placeholder: Placeholder text when empty
        class_name: Additional CSS classes for wrapper
        rows: Number of textarea rows (default: 3)

    Returns:
        html.Div containing:
            - dbc.Textarea with id=editor_id (callbacks read from this)
            - JavaScript will enhance this textarea with CodeMirror

    Example:
        ```python
        # Create editor (drop-in replacement for dbc.Textarea)
        editor = create_jql_editor(
            editor_id="jira-jql-query",
            initial_value="project = TEST",
            placeholder="Enter JQL query...",
            rows=3
        )

        # Callbacks work exactly as before (read from "value" property)
        @app.callback(
            Output("results", "children"),
            Input("jira-jql-query", "value")  # Note: "value" not "data"
        )
        def update_results(jql_query):
            return f"Searching: {jql_query}"
        ```

    Technical Notes:
        - This is a dbc.Textarea first, CodeMirror enhancement second
        - JavaScript (assets/jql_editor_init.js) creates CodeMirror from textarea
        - CodeMirror syncs changes back to textarea automatically
        - Callbacks work unchanged - they read from textarea.value
        - CodeMirror is purely cosmetic enhancement (graceful degradation if JS fails)
    """
    import dash_bootstrap_components as dbc

    from ui.styles import create_input_style

    return html.Div(
        className=f"jql-editor-wrapper {class_name}".strip(),
        children=[
            # Source of truth: regular Dash textarea that callbacks can read
            dbc.Textarea(
                id=editor_id,  # Callbacks read from Input("jira-jql-query", "value")
                value=initial_value,  # Use "value" property for dbc.Textarea
                placeholder=placeholder,
                rows=rows,
                className="jql-editor-textarea",  # JavaScript finds by this class
                style=create_input_style(size="md"),
            ),
        ],
    )
