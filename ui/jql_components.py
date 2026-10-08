import time

from dash import html

CHARACTER_COUNT_WARNING_THRESHOLD = 1800
CHARACTER_COUNT_MAX_REFERENCE = 2000

JQL_KEYWORDS = frozenset(
    [
        "AND",
        "OR",
        "NOT",
        "IN",
        "NOT IN",
        "IS",
        "IS NOT",
        "WAS",
        "WAS NOT",
        "WAS IN",
        "WAS NOT IN",
        "CHANGED",
        "EMPTY",
        "NULL",
        "CONTAINS",
        "NOT CONTAINS",
        "~",
        "!~",
        "ORDER BY",
        "ASC",
        "DESC",
        "currentUser",
        "now",
        "startOfDay",
        "endOfDay",
        "startOfWeek",
        "endOfWeek",
        "startOfMonth",
        "endOfMonth",
        "startOfYear",
        "endOfYear",
    ]
)
"""
JQL keyword registry for syntax highlighting.

This frozenset contains all recognized JQL keywords, operators, and common functions.
Keywords are matched case-insensitively.

Extensibility:
    To add new keywords, operators, or functions:
    1. Add the uppercase string to the appropriate category above
    2. Multi-word keywords (e.g., "ORDER BY", "NOT IN") are supported
    3. The tokenizer will automatically detect them in queries
    4. CSS class .jql-keyword will be applied for styling

    Example - Adding new function keywords:
        "membersOf",
        "linkedIssuesOf",
        "issueFunction",

    Example - Adding new operators:
        "BEFORE",
        "AFTER",
        "DURING",

Note: Functions like currentUser(), now(), etc. are detected without parentheses.
The parser handles parentheses and arguments separately as plain text.
"""


def count_jql_characters(query) -> int:

    if query is None:
        return 0

    query_str = str(query) if not isinstance(query, str) else query

    return len(query_str)


def should_show_character_warning(query) -> bool:

    count = count_jql_characters(query)
    return count >= CHARACTER_COUNT_WARNING_THRESHOLD


def create_character_count_display(count: int, warning: bool) -> html.Div:

    count_str = f"{count:,}" if count < 10000 else f"{count:,}"
    limit_str = f"{CHARACTER_COUNT_MAX_REFERENCE:,}"

    css_classes = "character-count-display"
    if warning:
        css_classes += " character-count-warning"

    return html.Div(
        f"{count_str} / {limit_str} characters",
        id="jql-character-count-display",
        className=css_classes,
    )


def create_character_count_state(count: int, warning: bool, textarea_id: str) -> dict:

    valid_ids = {"main", "dialog"}
    if textarea_id not in valid_ids:
        textarea_id = "main"

    return {
        "count": count,
        "warning": warning,
        "textarea_id": textarea_id,
        "last_updated": time.time(),
    }


def is_jql_keyword(word: str) -> bool:

    if not word:
        return False

    word_upper = word.upper().strip()

    if word_upper in JQL_KEYWORDS:
        return True

    for keyword in JQL_KEYWORDS:
        if " " in keyword and word_upper in keyword:
            return True

    return False
