from typing import Any

from dash import html

SCRIPTRUNNER_FUNCTIONS = frozenset(
    [
        "linkedIssuesOf",
        "issuesInEpics",
        "subtasksOf",
        "parentsOf",
        "epicsOf",
        "hasLinks",
        "hasComments",
        "hasAttachments",
        "lastUpdated",
        "expression",
        "dateCompare",
        "aggregateExpression",
        "issueFieldMatch",
        "linkedIssuesOfRecursive",
        "workLogged",
    ]
)


def is_scriptrunner_function(word: str) -> bool:

    if not word or not isinstance(word, str):
        return False

    return word in SCRIPTRUNNER_FUNCTIONS


def detect_syntax_errors(tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:

    if not tokens:
        return []

    errors = []

    for token in tokens:
        if not isinstance(token, dict):
            continue

        if token.get("type") == "string":
            text = token.get("text", "")
            if text and len(text) > 0:
                if text[0] in ('"', "'"):
                    if len(text) < 2 or text[-1] != text[0]:
                        errors.append(
                            {
                                "error_type": "unclosed_string",
                                "start": token.get("start", 0),
                                "end": token.get("end", len(text)),
                                "token": token,
                                "message": "Unclosed string literal",
                            }
                        )

    return errors


def create_jql_syntax_highlighter(
    component_id: str,
    value: str = "",
    placeholder: str = "Enter JQL query...",
    rows: int = 5,
    disabled: bool = False,
    aria_label: str = "JQL Query Input",
) -> html.Div:

    rows = max(1, min(20, rows))

    if len(value) > 5000:
        value = value[:5000]

    return html.Div(
        [
            html.Div(
                id=f"{component_id}-highlight",
                className="jql-syntax-highlight",
                contentEditable="false",
            ),
            html.Textarea(
                children=value,
                id=component_id,
                className="jql-syntax-input",
                placeholder=placeholder,
                rows=rows,
                disabled=disabled,
                maxLength=5000,
                title=aria_label,
            ),
        ],
        id=f"{component_id}-wrapper",
        className="jql-syntax-wrapper",
    )
