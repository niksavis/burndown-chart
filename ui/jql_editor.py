from dash import html


def create_jql_editor(
    editor_id: str,
    initial_value: str = "",
    placeholder: str = "Enter JQL query (e.g., project = TEST AND status = Done)",
    class_name: str = "",
    rows: int = 3,
) -> html.Div:

    import dash_bootstrap_components as dbc  # noqa: PLC0415

    return html.Div(
        className=f"jql-editor-wrapper {class_name}".strip(),
        children=[
            html.Div(
                id=f"{editor_id}-container",
                className="jql-codemirror-container",
                style={
                    "border": "1px solid #ced4da",
                    "borderRadius": "0.375rem",
                },
                **{  # type: ignore[arg-type]
                    "data-editor-id": editor_id,
                    "data-initial-value": initial_value,
                    "data-placeholder": placeholder,
                },
            ),
            dbc.Textarea(
                id=editor_id,
                value=initial_value,
                placeholder=placeholder,
                rows=rows,
                className="form-control",
                style={"display": "none"},
            ),
        ],
    )
