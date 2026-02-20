"""
JQL Components Module

Components for JQL query editor support including character counting and keyword detection.
Extracted from ui/components.py during refactoring (bd-rnol).
"""

import time

from dash import html

# Character count configuration (from data-model.md)
CHARACTER_COUNT_WARNING_THRESHOLD = 1800
CHARACTER_COUNT_MAX_REFERENCE = 2000

# JQL keyword registry (from data-model.md Section 3)
JQL_KEYWORDS = frozenset(
    [
        # Logical Operators
        "AND",
        "OR",
        "NOT",
        # Comparison Operators
        "IN",
        "NOT IN",
        # State Operators
        "IS",
        "IS NOT",
        "WAS",
        "WAS NOT",
        "WAS IN",
        "WAS NOT IN",
        "CHANGED",
        # Special Values
        "EMPTY",
        "NULL",
        # Text Operators
        "CONTAINS",
        "NOT CONTAINS",
        "~",
        "!~",  # Contains/Not Contains operators
        # Ordering & Pagination
        "ORDER BY",
        "ASC",
        "DESC",
        # Functions (commonly used)
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
    """
    Count characters in JQL query string.

    Handles unicode, whitespace, and edge cases per FR-001.

    Args:
        query: JQL query string (str, None, or other types)

    Returns:
        int: Character count (0 if None/empty)
    """
    if query is None:
        return 0

    # Convert to string if not already (handles numeric input)
    query_str = str(query) if not isinstance(query, str) else query

    return len(query_str)


def should_show_character_warning(query) -> bool:
    """
    Determine if character count warning should be shown.

    Per FR-002: Warning at 1800 characters (approaching JIRA's 2000 limit).

    Args:
        query: JQL query string

    Returns:
        bool: True if count >= 1800, False otherwise
    """
    count = count_jql_characters(query)
    return count >= CHARACTER_COUNT_WARNING_THRESHOLD


def create_character_count_display(count: int, warning: bool) -> html.Div:
    """
    Create character count display component.

    Per FR-003: Shows "X / 2000 characters" with warning styling.

    Args:
        count: Current character count
        warning: Whether to apply warning styling

    Returns:
        html.Div: Character count display component
    """
    # Format count with thousands separator for readability
    count_str = f"{count:,}" if count < 10000 else f"{count:,}"
    limit_str = f"{CHARACTER_COUNT_MAX_REFERENCE:,}"

    # Apply warning CSS class if needed
    css_classes = "character-count-display"
    if warning:
        css_classes += " character-count-warning"

    return html.Div(
        f"{count_str} / {limit_str} characters",
        id="jql-character-count-display",
        className=css_classes,
    )


def create_character_count_state(count: int, warning: bool, textarea_id: str) -> dict:
    """
    Create character count state dictionary for dcc.Store.

    Per data-model.md CharacterCountState schema.

    Args:
        count: Current character count
        warning: Warning state
        textarea_id: ID of textarea ("main" or "dialog")

    Returns:
        dict: State matching CharacterCountState TypedDict
    """
    # Validate textarea_id
    valid_ids = {"main", "dialog"}
    if textarea_id not in valid_ids:
        textarea_id = "main"  # Default to main if invalid

    return {
        "count": count,
        "warning": warning,
        "textarea_id": textarea_id,
        "last_updated": time.time(),
    }


def is_jql_keyword(word: str) -> bool:
    """
    Check if a word is a JQL keyword.

    Case-insensitive keyword detection per FR-004.

    Args:
        word: Word to check

    Returns:
        bool: True if word is a JQL keyword, False otherwise
    """
    if not word:
        return False

    # Check case-insensitively
    word_upper = word.upper().strip()

    # Check single keywords first
    if word_upper in JQL_KEYWORDS:
        return True

    # Check multi-word keywords (e.g., "ORDER BY", "NOT IN")
    # This handles cases where parser might split them
    for keyword in JQL_KEYWORDS:
        if " " in keyword and word_upper in keyword:
            return True

    return False
