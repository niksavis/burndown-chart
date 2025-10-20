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

from dash import dcc, html


def create_jql_editor(
    editor_id: str,
    initial_value: str = "",
    placeholder: str = "Enter JQL query (e.g., project = TEST AND status = Done)",
    class_name: str = "",
) -> html.Div:
    """
    Create a JQL editor component with CodeMirror 6 syntax highlighting.

    Returns a Dash component structure that JavaScript will enhance with CodeMirror:
    - Container div with .jql-editor-container class (JavaScript target)
    - dcc.Store for value synchronization with callbacks
    - Hidden textarea for accessibility and progressive enhancement

    Args:
        editor_id: Unique identifier for this editor instance.
                  Used as base for Store ID and container data attribute.
        initial_value: Initial JQL query to display in editor (default: empty string)
        placeholder: Placeholder text shown when editor is empty
        class_name: Additional CSS classes to apply to outer container (default: empty)

    Returns:
        html.Div containing:
            - html.Div with className="jql-editor-container" (CodeMirror mount point)
            - dcc.Store with id=editor_id (holds current editor value)
            - html.Textarea (hidden, accessibility fallback)

    Example:
        ```python
        # Create editor
        editor = create_jql_editor(
            editor_id="jira-jql-query",
            initial_value="project = TEST",
            placeholder="Search issues..."
        )

        # Use in callback (read from Store's "data" property)
        @app.callback(
            Output("results", "children"),
            Input("jira-jql-query", "data")
        )
        def update_results(jql_query):
            return f"Searching: {jql_query}"
        ```

    Technical Notes:
        - CodeMirror initialization happens in assets/jql_editor_init.js
        - Editor value syncs to dcc.Store on every change (via updateListener)
        - JavaScript finds editors by .jql-editor-container class
        - Container ID links to Store ID (remove "-container" suffix to get Store ID)
        - Hidden textarea maintains value if JavaScript fails to load
    """
    return html.Div(
        className=f"jql-editor-wrapper {class_name}".strip(),
        children=[
            # Store for value synchronization (callbacks read from this)
            dcc.Store(
                id=editor_id,
                data=initial_value,
                storage_type="memory",  # Don't persist across sessions
            ),
            # CodeMirror container (JavaScript will initialize CodeMirror here)
            html.Div(
                className="jql-editor-container",
                id=f"{editor_id}-container",
                children=[
                    # Fallback textarea (visible until CodeMirror initializes, then hidden)
                    html.Textarea(
                        id=f"{editor_id}-textarea",
                        children=initial_value,  # Use 'children' for initial content
                        placeholder=placeholder,
                        className="jql-editor-textarea form-control",
                        style={
                            "fontFamily": "Monaco, Menlo, 'Ubuntu Mono', Consolas, monospace",
                            "fontSize": "14px",
                            "minHeight": "100px",
                            "resize": "vertical",
                            "width": "100%",
                        },
                    ),
                ],
            ),
        ],
    )
