"""
UI Components Module

This module provides reusable UI components like tooltips, modals, and information tables
that are used across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import time
from datetime import datetime, timedelta
from typing import Optional

import dash_bootstrap_components as dbc

# Third-party library imports
from dash import html

# Application imports
from configuration import COLOR_PALETTE
from configuration.settings import (
    FORECAST_HELP_TEXTS,
    PROJECT_HELP_TEXTS,
    VELOCITY_HELP_TEXTS,
)
from ui.button_utils import create_button
from ui.icon_utils import create_icon_text
from ui.styles import create_form_feedback_style
from ui.tooltip_utils import (
    create_calculation_step_tooltip,
    create_formula_tooltip,
    create_info_tooltip,
    create_statistical_context_tooltip,
)

# Define common trend icons and colors
TREND_ICONS = {
    "stable": "fas fa-equals",
    "up": "fas fa-arrow-up",
    "down": "fas fa-arrow-down",
}

TREND_COLORS = {
    "stable": "#6c757d",  # Gray
    "up": "#28a745",  # Green
    "down": "#dc3545",  # Red
}

#######################################################################
# JQL CHARACTER COUNT (Feature 001-add-jql-query)
#######################################################################

# Character count configuration (from data-model.md)
CHARACTER_COUNT_WARNING_THRESHOLD = 1800
CHARACTER_COUNT_MAX_REFERENCE = 2000


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


#######################################################################
# JQL SYNTAX HIGHLIGHTING (Feature 001-add-jql-query, Phase 2)
#######################################################################

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
Keywords are matched case-insensitively by is_jql_keyword() and parse_jql_syntax().

Extensibility:
    To add new keywords, operators, or functions:
    1. Add the uppercase string to the appropriate category above
    2. Multi-word keywords (e.g., "ORDER BY", "NOT IN") are supported
    3. The parser will automatically detect them in queries
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


def parse_jql_syntax(query):
    """
    Parse JQL query into syntax tokens for highlighting.

    Tokenizes query into keywords, strings, operators, and text per FR-004, FR-005.

    Tokenization Approach:
        This parser uses a character-by-character state machine approach:
        1. String Detection: Quotes (", ') trigger string token capture until closing quote
        2. Word Boundaries: Whitespace and operators define token boundaries
        3. Keyword Matching: Words are checked against JQL_KEYWORDS (case-insensitive)
        4. Operator Detection: Special characters (=, !, <, >, ~) create operator tokens
        5. Fallback: Everything else is plain text

        The parser preserves exact character positions (start/end indices) for each token,
        allowing accurate reconstruction of the original query with highlighting applied.

    Token Types:
        - "keyword": JQL reserved words (AND, OR, IN, IS, etc.)
        - "string": Quoted text literals ("Done", 'In Progress')
        - "operator": Comparison symbols (=, !=, <, >, ~, !~)
        - "text": Field names, values, and other plain text

    Args:
        query: JQL query string (str or None)

    Returns:
        List[dict]: List of SyntaxToken dicts with keys: text, type, start, end
                   Returns empty list if query is None/empty

    Example:
        >>> parse_jql_syntax('project = TEST AND status = "Done"')
        [
            {"text": "project", "type": "text", "start": 0, "end": 7},
            {"text": " ", "type": "text", "start": 7, "end": 8},
            {"text": "=", "type": "operator", "start": 8, "end": 9},
            {"text": " ", "type": "text", "start": 9, "end": 10},
            {"text": "TEST", "type": "text", "start": 10, "end": 14},
            {"text": " ", "type": "text", "start": 14, "end": 15},
            {"text": "AND", "type": "keyword", "start": 15, "end": 18},
            ...
        ]
    """
    if query is None or query == "":
        return []

    query_str = str(query)
    tokens = []
    i = 0

    while i < len(query_str):
        # Skip whitespace (but track it as text tokens for accurate rendering)
        if query_str[i].isspace():
            start = i
            while i < len(query_str) and query_str[i].isspace():
                i += 1
            tokens.append(
                {"text": query_str[start:i], "type": "text", "start": start, "end": i}
            )
            continue

        # Parse quoted strings (both double and single quotes)
        if query_str[i] in ('"', "'"):
            quote_char = query_str[i]
            start = i
            i += 1

            # Find matching closing quote
            while i < len(query_str) and query_str[i] != quote_char:
                # Handle escaped quotes
                if query_str[i] == "\\" and i + 1 < len(query_str):
                    i += 2
                else:
                    i += 1

            # Include closing quote if found
            if i < len(query_str):
                i += 1

            tokens.append(
                {"text": query_str[start:i], "type": "string", "start": start, "end": i}
            )
            continue

        # Parse operators
        if query_str[i] in "=!<>~":
            start = i
            # Handle multi-character operators (!=, >=, <=, !~)
            if i + 1 < len(query_str) and query_str[i + 1] in "=~":
                i += 2
            else:
                i += 1

            tokens.append(
                {
                    "text": query_str[start:i],
                    "type": "operator",
                    "start": start,
                    "end": i,
                }
            )
            continue

        # Parse special characters (parentheses, commas)
        if query_str[i] in "(),":
            tokens.append(
                {"text": query_str[i], "type": "text", "start": i, "end": i + 1}
            )
            i += 1
            continue

        # Parse words (potential keywords, functions, or field names)
        start = i
        while (
            i < len(query_str)
            and not query_str[i].isspace()
            and query_str[i] not in "=!<>~\"'(),"
        ):
            i += 1

        word = query_str[start:i]

        # Check if it's a ScriptRunner function (exact case match)
        from ui.jql_syntax_highlighter import is_scriptrunner_function
        if is_scriptrunner_function(word):
            token_type = "function"
        # Check if it's a JQL keyword (case-insensitive)
        elif is_jql_keyword(word):
            token_type = "keyword"
        else:
            # Could be a field name or value
            token_type = "text"

        tokens.append({"text": word, "type": token_type, "start": start, "end": i})

    return tokens


def render_syntax_tokens(tokens) -> list:
    """
    Render syntax tokens to Dash HTML components.

    Converts tokens to html.Mark elements with CSS classes per FR-006.
    Supports token types: keyword, string, operator, function, error.

    Args:
        tokens: List of SyntaxToken dicts

    Returns:
        list: List of html.Mark components or strings for rendering
    """
    if not tokens:
        return []

    rendered = []

    for token in tokens:
        text = token.get("text", "")
        token_type = token.get("type", "text")
        error_type = token.get("error_type")  # Optional error classification

        # Render error tokens with appropriate styling
        if token_type == "error":
            if error_type == "unclosed_string":
                rendered.append(html.Mark(text, className="jql-error-unclosed"))
            elif error_type == "invalid_operator":
                rendered.append(html.Mark(text, className="jql-error-invalid"))
            else:
                # Generic error styling
                rendered.append(html.Mark(text, className="jql-error-invalid"))
        # Render ScriptRunner functions with highlighting
        elif token_type == "function":
            rendered.append(html.Mark(text, className="jql-function"))
        # Render keywords with highlighting
        elif token_type == "keyword":
            rendered.append(html.Mark(text, className="jql-keyword"))
        # Render strings with highlighting
        elif token_type == "string":
            rendered.append(html.Mark(text, className="jql-string"))
        # Render operators with highlighting
        elif token_type == "operator":
            rendered.append(html.Mark(text, className="jql-operator"))
        # Render plain text as-is
        else:
            rendered.append(text)

    return rendered


#######################################################################
# PERT INFO TABLE COMPONENT
#######################################################################


# Add these utility functions to help with PERT table components without breaking existing functionality
def _create_header_with_icon(
    icon_class: str,
    title: str,
    color: str = "#20c997",
    tooltip_id: Optional[str] = None,
    tooltip_text: Optional[str] = None,
    help_key: Optional[str] = None,
    help_category: Optional[str] = None,
) -> html.H5:
    """Create a header with an icon for PERT info sections.

    Args:
        icon_class: The Font Awesome icon class to use
        title: The title text for the header
        color: The color to use for the icon, defaults to teal
        tooltip_id: Optional ID suffix for tooltip
        tooltip_text: Optional tooltip text to display
        help_key: Optional help content key for Phase 9.2 progressive disclosure
        help_category: Optional help category for Phase 9.2 system

    Returns:
        A styled H5 component with an icon, title, and optional tooltip/help
    """
    header_content = [
        html.I(
            className=f"{icon_class} me-2",
            style={"color": color},
        ),
        title,
    ]

    # Add progressive disclosure help system (Phase 9.2) if help parameters provided
    if help_key and help_category:
        from ui.help_system import create_help_button_with_tooltip

        header_content.append(
            html.Span(
                [
                    create_help_button_with_tooltip(
                        tooltip_text or "Click for detailed information",
                        help_key,
                        help_category,
                        tooltip_placement="bottom",
                    )
                ],
                className="ms-2",
            )
        )
    # Fallback to simple tooltip if no help system parameters
    elif tooltip_id and tooltip_text:
        header_content.append(create_info_tooltip(tooltip_id, tooltip_text))

    return html.H5(
        header_content,
        className="mb-3 border-bottom pb-2 d-flex align-items-center",
    )


def _create_forecast_row(
    label, completion_date, timeframe, bg_color, is_highlighted=False, icon=None
):
    """Create a standardized forecast row for PERT tables."""
    # Create appropriate class names based on highlight status and bg_color
    row_classes = ["forecast-row"]
    label_classes = ["label-text"]
    icon_classes = ["forecast-row-icon"]

    if is_highlighted:
        row_classes.append("highlighted")
        label_classes.append("highlighted")
        # Determine if this is a success or danger highlighted row
        if "40,167,69" in bg_color:  # Check if it's green
            row_classes.append("success")
            icon_classes.append("success")
        else:
            row_classes.append("danger")
            icon_classes.append("danger")

    # Style attribute for the background color only
    row_style = {"backgroundColor": bg_color}

    # Handle label being either a string or a list (with tooltip)
    if isinstance(label, list):
        label_content = [html.Span(label[0], className=" ".join(label_classes))]
        if len(label) > 1:  # Add tooltip if provided
            label_content.extend(label[1:])
    else:
        label_content = [html.Span(label, className=" ".join(label_classes))]

    if icon and is_highlighted:
        # Wrap the icon in a Span element for type consistency
        label_content.append(
            html.Span(html.I(className=f"{icon} ms-2 {' '.join(icon_classes)}"))
        )

    return html.Div(
        className=" ".join(row_classes),
        style=row_style,
        children=[
            html.Div(label_content, className="forecast-row-label"),
            html.Div(
                html.Span(
                    completion_date,
                    className="fw-medium",
                ),
                className="forecast-row-date",
            ),
            html.Div(html.Small(timeframe), className="forecast-row-timeframe"),
        ],
    )


def _get_trend_icon_and_color(trend_value):
    """
    Determine appropriate icon and color based on trend value.

    Args:
        trend_value (float): Percentage change in trend

    Returns:
        tuple: (icon_class, color_hex)
    """
    if abs(trend_value) < 5:  # Less than 5% change is considered stable
        return TREND_ICONS["stable"], TREND_COLORS["stable"]  # Equals sign, gray color
    elif trend_value > 0:
        return TREND_ICONS["up"], TREND_COLORS["up"]  # Up arrow, green color
    else:
        return TREND_ICONS["down"], TREND_COLORS["down"]  # Down arrow, red color


def _create_project_overview_section(
    items_percentage,
    points_percentage,
    completed_items,
    completed_points,
    actual_total_items,
    actual_total_points,
    total_items,
    remaining_points,
    similar_percentages=False,
    show_points=True,
):
    """
    Create the project overview section with progress bars.

    Args:
        items_percentage: Percentage of items completed
        points_percentage: Percentage of points completed
        completed_items: Number of completed items
        completed_points: Number of completed points
        actual_total_items: Total items (completed + remaining)
        actual_total_points: Total points (completed + remaining)
        total_items: Number of remaining items
        remaining_points: Number of remaining points
        similar_percentages: Whether items and points percentages are similar
        show_points: Whether points tracking is enabled

    Returns:
        dash.html.Div: Project overview section
    """
    return html.Div(
        [
            # Project progress section
            html.Div(
                [
                    # Combined progress for similar percentages
                    html.Div(
                        [
                            html.Div(
                                className="progress-container",
                                children=[
                                    html.Div(
                                        className="progress-bar bg-primary",
                                        style={
                                            "width": f"{items_percentage}%",
                                            "height": "100%",
                                            "transition": "width 1s ease",
                                        },
                                    ),
                                    html.Span(
                                        [
                                            f"{items_percentage}% Complete",
                                            create_info_tooltip(
                                                "combined-completion-percentage",
                                                "Percentage of total work completed based on historical progress data. Items vs Points comparison shows estimation accuracy.",
                                            ),
                                        ],
                                        className=f"progress-label {'dark-text' if items_percentage > 40 else 'light-text'}",
                                    ),
                                ],
                            ),
                            html.Div(
                                [
                                    html.Small(
                                        [
                                            html.Span(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    html.Strong(f"{completed_items}"),
                                                    f" of {actual_total_items} items",
                                                    create_info_tooltip(
                                                        id_suffix="items-progress-combined",
                                                        help_text=PROJECT_HELP_TEXTS[
                                                            "items_vs_points"
                                                        ],
                                                    ),
                                                ],
                                                className="me-3",
                                            ),
                                        ]
                                        + (
                                            [
                                                html.Span(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-1",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ]
                                                            },
                                                        ),
                                                        html.Strong(
                                                            f"{completed_points}"
                                                        ),
                                                        f" of {actual_total_points} points",
                                                        create_info_tooltip(
                                                            "points-progress-combined",
                                                            "Comparison between item-based and point-based progress tracking. Similar percentages indicate consistent estimation accuracy.",
                                                        ),
                                                    ]
                                                ),
                                            ]
                                            if show_points
                                            else []
                                        ),
                                        className="text-muted mt-2 d-block",
                                    ),
                                ],
                                className="d-flex justify-content-center",
                            ),
                        ],
                        style={"display": "block" if similar_percentages else "none"},
                        className="mb-3",
                    ),
                    # Separate progress bars for different percentages
                    html.Div(
                        [
                            # Items progress
                            html.Div(
                                [
                                    html.Div(
                                        className="d-flex justify-content-between align-items-center mb-1",
                                        children=[
                                            html.Small(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    "Items Progress",
                                                    create_info_tooltip(
                                                        "items-progress-separate",
                                                        "Progress tracking by item count. Shows (Completed Items ÷ Total Items) × 100%",
                                                    ),
                                                ],
                                                className="fw-medium",
                                            ),
                                            html.Small(
                                                [
                                                    f"{items_percentage}% Complete",
                                                    create_info_tooltip(
                                                        "items-completion-separate",
                                                        "Percentage completion based on item count progress tracking",
                                                    ),
                                                ],
                                                className="text-muted",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="progress",
                                        style={
                                            "height": "16px",
                                            "borderRadius": "4px",
                                            "overflow": "hidden",
                                            "boxShadow": "inset 0 1px 2px rgba(0,0,0,.1)",
                                        },
                                        children=[
                                            html.Div(
                                                className="progress-bar bg-info",
                                                style={
                                                    "width": f"{items_percentage}%",
                                                    "height": "100%",
                                                    "transition": "width 1s ease",
                                                },
                                            ),
                                        ],
                                    ),
                                    html.Small(
                                        f"{completed_items} of {actual_total_items} items ({total_items} remaining)",
                                        className="text-muted mt-1 d-block",
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ]
                        + (
                            [
                                # Points progress - only show if points tracking is enabled
                                html.Div(
                                    [
                                        html.Div(
                                            className="d-flex justify-content-between align-items-center mb-1",
                                            children=[
                                                html.Small(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-1",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ]
                                                            },
                                                        ),
                                                        "Points Progress",
                                                        create_info_tooltip(
                                                            id_suffix="points-progress-separate",
                                                            help_text=PROJECT_HELP_TEXTS[
                                                                "completion_percentage"
                                                            ],
                                                        ),
                                                    ],
                                                    className="fw-medium",
                                                ),
                                                html.Small(
                                                    [
                                                        f"{points_percentage}% Complete",
                                                        create_info_tooltip(
                                                            id_suffix="points-completion-separate",
                                                            help_text=PROJECT_HELP_TEXTS[
                                                                "completion_percentage"
                                                            ],
                                                        ),
                                                    ],
                                                    className="text-muted",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="progress",
                                            style={
                                                "height": "16px",
                                                "borderRadius": "4px",
                                                "overflow": "hidden",
                                                "boxShadow": "inset 0 1px 2px rgba(0,0,0,.1)",
                                            },
                                            children=[
                                                html.Div(
                                                    className="progress-bar bg-warning",
                                                    style={
                                                        "width": f"{points_percentage}%",
                                                        "height": "100%",
                                                        "transition": "width 1s ease",
                                                    },
                                                ),
                                            ],
                                        ),
                                        html.Small(
                                            f"{completed_points} of {actual_total_points} points ({remaining_points} remaining)",
                                            className="text-muted mt-1 d-block",
                                        ),
                                    ],
                                ),
                            ]
                            if show_points
                            else []
                        ),
                        style={
                            "display": "block" if not similar_percentages else "none"
                        },
                        className="mb-3",
                    ),
                ],
                className="mb-4",
            )
        ]
    )


def _create_deadline_section(deadline_date_str, days_to_deadline):
    """
    Create the project deadline visualization section.

    Args:
        deadline_date_str: Formatted deadline date
        days_to_deadline: Days remaining until deadline

    Returns:
        dash.html.Div: Deadline visualization section
    """
    return html.Div(
        [
            html.Div(
                className="d-flex align-items-center mb-2",
                children=[
                    html.I(
                        className="fas fa-calendar-day fs-3 me-3",
                        style={"color": COLOR_PALETTE["deadline"]},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Project Deadline",
                                className="text-muted small",
                            ),
                            html.Div(
                                deadline_date_str,
                                className="fs-5 fw-bold",
                            ),
                        ]
                    ),
                ],
            ),
            # Days remaining visualization
            html.Div(
                [
                    html.Div(
                        className="d-flex justify-content-between align-items-center",
                        children=[
                            html.Small("Today", className="text-muted"),
                            html.Small(
                                "Deadline",
                                className="text-muted",
                            ),
                        ],
                    ),
                    html.Div(
                        className="progress mt-1 mb-1",
                        style={
                            "height": "8px",
                            "borderRadius": "4px",
                        },
                        children=[
                            html.Div(
                                className="progress-bar bg-danger",
                                style={
                                    "width": f"{max(5, min(100, (100 - (days_to_deadline / (days_to_deadline + 30) * 100))))}%",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        html.Strong(
                            f"{days_to_deadline} days remaining",
                            style={
                                "color": "green"
                                if days_to_deadline > 30
                                else "orange"
                                if days_to_deadline > 14
                                else "red"
                            },
                        ),
                        className="text-center mt-1",
                    ),
                ],
                className="mt-2",
            ),
        ],
        className="p-3 border rounded",
        style={
            "background": "linear-gradient(to bottom, rgba(220, 53, 69, 0.05), rgba(255, 255, 255, 1))",
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
        },
    )


def _create_forecast_card(
    title,
    metric_type,
    completion_str,
    pert_time,
    color,
    avg_completion_str,
    med_completion_str,
    weeks_avg,
    avg_days,
    weeks_med,
    med_days,
    weeks_avg_color,
    weeks_med_color,
):
    """
    Create a forecast card for either items or points.

    Args:
        title: Title of the forecast card (e.g., "Items Forecast")
        metric_type: Type of metric, either "items" or "points"
        completion_str: Formatted completion date string
        pert_time: PERT estimate for completion (days)
        color: Color indicator (green/red) based on meeting deadline
        avg_completion_str: Average completion date string
        med_completion_str: Median completion date string
        weeks_avg: Number of weeks to completion based on average
        avg_days: Number of days to completion based on average
        weeks_med: Number of weeks to completion based on median
        med_days: Number of days to completion based on median
        weeks_avg_color: Color for average forecast (green/red)
        weeks_med_color: Color for median forecast (green/red)

    Returns:
        dash.html.Div: A forecast card component
    """
    return html.Div(
        [
            # Header with icon
            html.Div(
                [
                    html.I(
                        className=f"{'fas fa-tasks' if metric_type == 'items' else 'fas fa-chart-bar'} me-2",
                        style={"color": COLOR_PALETTE[metric_type]},
                    ),
                    html.Span(
                        title,
                        className="fw-medium",
                    ),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Table header
            html.Div(
                className="d-flex mb-2 px-3 py-2 bg-light rounded-top border-bottom",
                style={"fontSize": "0.8rem"},
                children=[
                    html.Div(
                        [
                            "Method",
                            create_formula_tooltip(
                                f"forecast-method-{metric_type}",
                                FORECAST_HELP_TEXTS["three_point_estimation"],
                                "Three-Point Estimation",
                                [
                                    "PERT: (Optimistic + 4×Most_Likely + Pessimistic) / 6",
                                    "Average: Historical mean completion rate",
                                    "Median: Middle value of historical rates",
                                    "Each method provides different confidence levels",
                                ],
                            ),
                        ],
                        className="text-muted d-flex align-items-center",
                        style={"width": "25%"},
                    ),
                    html.Div(
                        [
                            "Completion Date",
                            create_info_tooltip(
                                f"completion-date-{metric_type}",
                                "Projected completion date based on historical velocity and PERT analysis.",
                            ),
                        ],
                        className="text-muted text-center d-flex align-items-center justify-content-center",
                        style={"width": "45%"},
                    ),
                    html.Div(
                        [
                            "Timeframe",
                            create_info_tooltip(
                                f"timeframe-{metric_type}",
                                "Estimated duration to complete remaining work, shown in days (d) and weeks (w).",
                            ),
                        ],
                        className="text-muted text-end d-flex align-items-center justify-content-end",
                        style={"width": "30%"},
                    ),
                ],
            ),
            _create_forecast_row(
                [
                    "PERT",
                    create_formula_tooltip(
                        f"pert-forecast-{metric_type}",
                        FORECAST_HELP_TEXTS["expected_forecast"],
                        "PERT = (O + 4×M + P) / 6",
                        [
                            "O = Best case scenario (optimistic)",
                            "M = Most likely scenario (modal)",
                            "P = Worst case scenario (pessimistic)",
                            "Uses beta distribution weighting with 4x emphasis on most likely case",
                        ],
                    ),
                ],
                completion_str,
                f"{pert_time:.1f}d ({pert_time / 7:.1f}w)",
                f"rgba({color == 'green' and '40,167,69' or '220,53,69'},0.08)",
                is_highlighted=True,
                icon="fas fa-chart-line",
            ),
            # Average row
            _create_forecast_row(
                [
                    "Average",
                    create_calculation_step_tooltip(
                        f"average-forecast-{metric_type}",
                        VELOCITY_HELP_TEXTS["velocity_average"],
                        [
                            "Average = Σ(weekly_values) / n",
                            "Example: (5+7+3+6+4)/5 = 5.0 items/week",
                            "Completion = remaining_work / average_velocity",
                            "Uses arithmetic mean of recent velocity data",
                        ],
                    ),
                ],
                avg_completion_str,
                (
                    f"{avg_days:.1f}d ({weeks_avg:.1f}w)"
                    if weeks_avg != float("inf")
                    else "∞"
                ),
                f"rgba({weeks_avg_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
            ),
            # Median row
            _create_forecast_row(
                [
                    "Median",
                    create_statistical_context_tooltip(
                        f"median-forecast-{metric_type}",
                        VELOCITY_HELP_TEXTS["velocity_median"],
                        "50th percentile",
                        "More robust than average - less affected by outliers and extreme values. Better for forecasting when velocity varies significantly.",
                    ),
                ],
                med_completion_str,
                (
                    f"{med_days:.1f}d ({weeks_med:.1f}w)"
                    if weeks_med != float("inf")
                    else "∞"
                ),
                f"rgba({weeks_med_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
            ),
        ],
        className=f"{'mb-4' if metric_type == 'items' else 'mb-3'} p-3 border rounded",
        style={
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
            "background": "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))"
            if metric_type == "items"
            else "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))",
        },
    )


def _create_completion_forecast_section(
    items_completion_str,
    points_completion_str,
    pert_time_items,
    pert_time_points,
    items_color,
    points_color,
    avg_items_completion_str,
    med_items_completion_str,
    avg_points_completion_str,
    med_points_completion_str,
    weeks_avg_items,
    weeks_med_items,
    weeks_avg_points,
    weeks_med_points,
    avg_items_days,
    med_items_days,
    avg_points_days,
    med_points_days,
    weeks_avg_items_color,
    weeks_med_items_color,
    weeks_avg_points_color,
    weeks_med_points_color,
    show_points=True,  # Add parameter for points tracking
):
    """
    Create the completion forecast section.

    Args:
        Multiple parameters for both items and points forecasts
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        dash.html.Div: Completion forecast section
    """
    # Create the forecast cards list
    forecast_cards = [
        # Items Forecast Card
        _create_forecast_card(
            "Items Forecast",
            "items",
            items_completion_str,
            pert_time_items,
            items_color,
            avg_items_completion_str,
            med_items_completion_str,
            weeks_avg_items,
            avg_items_days,
            weeks_med_items,
            med_items_days,
            weeks_avg_items_color,
            weeks_med_items_color,
        ),
    ]

    # Only add points forecast card if points tracking is enabled
    if show_points:
        forecast_cards.append(
            _create_forecast_card(
                "Points Forecast",
                "points",
                points_completion_str,
                pert_time_points,
                points_color,
                avg_points_completion_str,
                med_points_completion_str,
                weeks_avg_points,
                avg_points_days,
                weeks_med_points,
                med_points_days,
                weeks_avg_points_color,
                weeks_med_points_color,
            )
        )

    return html.Div(
        [
            # Add all forecast cards
            *forecast_cards,
            # Enhanced footer with methodology explanation and tooltip
            html.Div(
                html.Small(
                    [
                        create_icon_text(
                            "fas fa-chart-line",
                            "PERT three-point estimation (optimistic + most likely + pessimistic)",
                            size="xs",
                        ),
                        create_info_tooltip(
                            "pert-methodology",
                            FORECAST_HELP_TEXTS["pert_methodology"],
                        ),
                    ],
                    className="text-muted fst-italic text-center d-flex align-items-center justify-content-center",
                ),
                className="mt-3",
            ),
        ],
        className="p-3 border rounded h-100",
    )


def _create_velocity_metric_card(
    title, value, trend, trend_icon, trend_color, color, is_mini=False
):
    """
    Create a velocity metric card (average or median).

    Args:
        title: Title of the card (Average or Median)
        value: Value to display
        trend: Trend percentage
        trend_icon: Icon for trend direction
        trend_color: Color for trend indicator
        color: Color for the value
        is_mini: Whether this is the mini version for the sparklines

    Returns:
        dash.html.Div: A velocity metric card
    """
    # Generate some demo data for the sparklines
    sparkline_bars = []
    for i in range(10):
        if title == "Average" and not is_mini:
            height = f"{10 + (i * 3) + (5 if i % 3 == 0 else -5)}px"
            bg_color = "#0d6efd" if not is_mini else "#fd7e14"
        else:
            height = f"{8 + (i * 2) + (4 if i % 2 == 0 else -3)}px"
            bg_color = "#6c757d"
            if is_mini:
                height = f"{10 + (i * 2) + (6 if i % 3 == 0 else -2)}px"

        sparkline_bars.append(
            html.Div(
                className="mx-1",
                style={
                    "width": "5px",
                    "height": height,
                    "backgroundColor": bg_color,
                    "opacity": f"{0.4 + (i * 0.06)}",
                    "borderRadius": "1px",
                },
            )
        )

    # Create the card with proper styles - remove fixed margins
    style_dict = {
        "flex": "1",
        "minWidth": "150px",
    }

    return html.Div(
        [
            # Header row with label and trend
            html.Div(
                [
                    html.Span(
                        [
                            title,
                            create_calculation_step_tooltip(
                                f"velocity-{title.lower()}",
                                VELOCITY_HELP_TEXTS[f"velocity_{title.lower()}"],
                                [
                                    f"{title} = {'Σ(values)/n' if title == 'Average' else 'middle value when sorted'}",
                                    f"Example: {'(3+5+7+4+6)/5 = 5.0' if title == 'Average' else '[3,4,5,6,7] → 5.0'}",
                                    "Based on last 10 weeks of completed work",
                                    f"{'Arithmetic mean' if title == 'Average' else '50th percentile - outlier resistant'}",
                                ],
                            ),
                            # Phase 9.2 Progressive Disclosure Help Button
                            html.Span(
                                [
                                    html.Span(
                                        [
                                            dbc.Button(
                                                html.I(
                                                    className="fas fa-question-circle"
                                                ),
                                                id={
                                                    "type": "help-button",
                                                    "category": "velocity",
                                                    "key": f"velocity_{title.lower()}_calculation",
                                                },
                                                size="sm",
                                                color="link",
                                                className="text-secondary p-1 ms-1",
                                                style={
                                                    "border": "none",
                                                    "background": "transparent",
                                                    "fontSize": "0.7rem",
                                                    "lineHeight": "1",
                                                },
                                                title=f"Get detailed help about {title.lower()} velocity",
                                            )
                                        ],
                                        className="help-button-container",
                                    )
                                ],
                                className="ms-1",
                            )
                            if title in ["Average", "Median"]
                            else create_info_tooltip(
                                f"velocity-{title.lower()}",
                                VELOCITY_HELP_TEXTS[f"velocity_{title.lower()}"],
                            ),
                        ],
                        className="fw-medium d-flex align-items-center",
                    ),
                    html.Span(
                        [
                            html.I(
                                className=f"{trend_icon} me-1",
                                style={
                                    "color": trend_color,
                                    "fontSize": "0.75rem",
                                },
                            ),
                            f"{'+' if trend > 0 else ''}{trend}%",
                            create_calculation_step_tooltip(
                                f"velocity-trend-{title.lower()}",
                                VELOCITY_HELP_TEXTS["velocity_trend"],
                                [
                                    "Trend = ((Current - Previous) / Previous) × 100",
                                    "Example: ((6.0 - 5.0) / 5.0) × 100 = +20%",
                                    "Compares recent 5 weeks vs previous 5 weeks",
                                    "Positive trend = improving velocity",
                                ],
                            ),
                        ],
                        style={"color": trend_color},
                        title="Change compared to previous period",
                        className="d-flex align-items-center",
                    ),
                ],
                className="d-flex justify-content-between align-items-center mb-2",
            ),  # Value
            html.Div(
                html.Span(
                    f"{float(value):.1f}",  # Display with 1 decimal place
                    className="fs-3 fw-bold",
                    style={"color": color},
                ),
                className="text-center mb-2" if not is_mini else "text-center mb-1",
            ),
            # Mini sparkline trend
            html.Div(
                [
                    html.Div(
                        className="d-flex align-items-end justify-content-center",
                        style={"height": "30px"},
                        children=sparkline_bars,
                    ),
                    html.Div(
                        html.Small(
                            "10-week trend",
                            className="text-muted",
                        ),
                        className="text-center mt-1",
                    ),
                ],
                title=f"Visual representation of {title.lower()} {'items' if not is_mini else 'points'} completed over the last 10 weeks",
            ),
        ],
        className="p-3 border rounded mb-3",
        style=style_dict,
    )


def _create_velocity_metric_section(
    metric_type,
    avg_weekly_value,
    med_weekly_value,
    avg_trend,
    med_trend,
    avg_trend_icon,
    avg_trend_color,
    med_trend_icon,
    med_trend_color,
):
    """
    Create a velocity metric section (items or points).

    Args:
        metric_type: Type of metric, either "items" or "points"
        avg_weekly_value: Average weekly value
        med_weekly_value: Median weekly value
        avg_trend: Average trend percentage
        med_trend: Median trend percentage
        avg_trend_icon: Icon for average trend
        avg_trend_color: Color for average trend
        med_trend_icon: Icon for median trend
        med_trend_color: Color for median trend

    Returns:
        dash.html.Div: Velocity metric section
    """
    # Set colors based on metric type
    is_items = metric_type == "items"
    avg_color = "#0d6efd" if is_items else "#fd7e14"
    med_color = "#6c757d"
    is_mini = not is_items

    return html.Div(
        [
            # Header with icon - align left instead of center
            html.Div(
                [
                    html.I(
                        className=f"{'fas fa-tasks' if is_items else 'fas fa-chart-bar'} me-2",
                        style={"color": COLOR_PALETTE[metric_type]},
                    ),
                    html.Span("Items" if is_items else "Points", className="fw-medium"),
                    create_formula_tooltip(
                        f"velocity-{metric_type}",
                        VELOCITY_HELP_TEXTS["weekly_velocity"],
                        "Weekly Average = Σ(last 10 weeks) ÷ 10",
                        [
                            "Calculates simple arithmetic mean of recent performance",
                            "Uses last 10 weeks of historical data for stability",
                            "Example: (5+7+6+8+4+9+7+6+8+5) ÷ 10 = 6.5 items/week",
                        ],
                    ),
                ],
                className="d-flex align-items-center mb-3",  # Removed justify-content-center
            ),
            # Velocity metrics - using flex layout with improved gap spacing for better responsiveness
            html.Div(
                [
                    # Average Items/Points
                    html.Div(
                        _create_velocity_metric_card(
                            "Average",
                            avg_weekly_value,
                            avg_trend,
                            avg_trend_icon,
                            avg_trend_color,
                            avg_color,
                            is_mini,
                        ),
                        className="px-2",
                        style={"flex": "1", "minWidth": "150px"},
                    ),
                    # Median Items/Points
                    html.Div(
                        _create_velocity_metric_card(
                            "Median",
                            med_weekly_value,
                            med_trend,
                            med_trend_icon,
                            med_trend_color,
                            med_color,
                            is_mini,
                        ),
                        className="px-2",
                        style={"flex": "1", "minWidth": "150px"},
                    ),
                ],
                className="d-flex flex-wrap mx-n2",  # Negative margin to offset px-2 padding
                style={"gap": "0px"},
            ),
        ],
        className=f"{'mb-4' if is_items else 'mb-3'} p-3 border rounded",
        style={
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
            "background": "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))"
            if is_items
            else "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))",
        },
    )


def _create_weekly_velocity_section(
    avg_weekly_items,
    med_weekly_items,
    avg_weekly_points,
    med_weekly_points,
    avg_items_trend,
    med_items_trend,
    avg_points_trend,
    med_points_trend,
    avg_items_icon,
    avg_items_icon_color,
    med_items_icon,
    med_items_icon_color,
    avg_points_icon,
    avg_points_icon_color,
    med_points_icon,
    med_points_icon_color,
    show_points=True,  # Add parameter for points tracking
    data_points_count=None,  # NEW PARAMETER
    total_data_points=None,  # NEW PARAMETER
):
    """
    Create the weekly velocity section.

    Args:
        Multiple parameters for velocity metrics
        show_points: Whether points tracking is enabled (default: True)
        data_points_count: Number of data points used for calculations (default: None)
        total_data_points: Total data points available (default: None)

    Returns:
        dash.html.Div: Weekly velocity section
    """
    # Create the velocity cards list
    velocity_cards = [
        # Items Velocity Card
        _create_velocity_metric_section(
            "items",
            avg_weekly_items,
            med_weekly_items,
            avg_items_trend,
            med_items_trend,
            avg_items_icon,
            avg_items_icon_color,
            med_items_icon,
            med_items_icon_color,
        ),
    ]

    # Only add points velocity card if points tracking is enabled
    if show_points:
        velocity_cards.append(
            _create_velocity_metric_section(
                "points",
                avg_weekly_points,
                med_weekly_points,
                avg_points_trend,
                med_points_trend,
                avg_points_icon,
                avg_points_icon_color,
                med_points_icon,
                med_points_icon_color,
            )
        )

    return html.Div(
        [
            # Add all velocity cards
            *velocity_cards,
            # Enhanced footer with data period explanation and tooltip
            html.Div(
                html.Div(
                    _create_velocity_footer_content(
                        data_points_count, total_data_points
                    ),
                    className="text-muted fst-italic small text-center d-flex align-items-center justify-content-center",
                ),
                className="mt-3",
            ),
        ],
        className="p-3 border rounded h-100",
    )


def create_pert_info_table(
    pert_time_items,
    pert_time_points,
    days_to_deadline,
    avg_weekly_items: float = 0.0,
    avg_weekly_points: float = 0.0,
    med_weekly_items: float = 0.0,
    med_weekly_points: float = 0.0,
    pert_factor=3,  # Add default value
    total_items=0,  # New parameter for total items
    total_points=0,  # New parameter for total points
    deadline_str=None,  # Add parameter for direct deadline string
    statistics_df=None,  # New parameter for statistics data
    milestone_str=None,  # Add parameter for milestone date string
    show_points=True,  # Add parameter for points tracking
    data_points_count=None,  # NEW PARAMETER for data filtering
):
    """
    Create the PERT information table with improved organization and visual grouping.

    Args:
        pert_time_items: PERT estimate for items (days)
        pert_time_points: PERT estimate for points (days)
        days_to_deadline: Days remaining until deadline
        avg_weekly_items: Average weekly items completed (last 10 weeks)
        avg_weekly_points: Average weekly points completed (last 10 weeks)
        med_weekly_items: Median weekly items completed (last 10 weeks)
        med_weekly_points: Median weekly points completed (last 10 weeks)
        pert_factor: Number of data points used for optimistic/pessimistic scenarios
        total_items: Total remaining items to complete
        total_points: Total remaining points to complete
        deadline_str: The deadline date string from settings
        statistics_df: DataFrame containing the statistics data
        milestone_str: Milestone date string from settings
        show_points: Whether points tracking is enabled (default: True)
        data_points_count: Number of data points to use for calculations (default: None, uses all data)

    Returns:
        Dash component with improved PERT information display
    """
    # Determine colors based on if we'll meet the deadline
    items_color = "green" if pert_time_items <= days_to_deadline else "red"
    points_color = "green" if pert_time_points <= days_to_deadline else "red"

    # Calculate weeks to complete based on average and median rates
    weeks_avg_items = (
        total_items / avg_weekly_items if avg_weekly_items > 0 else float("inf")
    )
    weeks_med_items = (
        total_items / med_weekly_items if med_weekly_items > 0 else float("inf")
    )
    weeks_avg_points = (
        total_points / avg_weekly_points if avg_weekly_points > 0 else float("inf")
    )
    weeks_med_points = (
        total_points / med_weekly_points if med_weekly_points > 0 else float("inf")
    )

    # Determine colors for weeks estimates
    weeks_avg_items_color = (
        "green" if weeks_avg_items * 7 <= days_to_deadline else "red"
    )
    weeks_med_items_color = (
        "green" if weeks_med_items * 7 <= days_to_deadline else "red"
    )
    weeks_avg_points_color = (
        "green" if weeks_avg_points * 7 <= days_to_deadline else "red"
    )
    weeks_med_points_color = (
        "green" if weeks_med_points * 7 <= days_to_deadline else "red"
    )

    # Calculate projected completion dates
    current_date = datetime.now()
    items_completion_date = current_date + timedelta(days=pert_time_items)
    points_completion_date = current_date + timedelta(days=pert_time_points)

    # Calculate dates for average and median completion (handle infinity values)
    avg_items_completion_date = (
        current_date + timedelta(days=min(weeks_avg_items * 7, 3653))
        if weeks_avg_items != float("inf")
        else current_date + timedelta(days=3653)
    )
    med_items_completion_date = (
        current_date + timedelta(days=min(weeks_med_items * 7, 3653))
        if weeks_med_items != float("inf")
        else current_date + timedelta(days=3653)
    )
    avg_points_completion_date = (
        current_date + timedelta(days=min(weeks_avg_points * 7, 3653))
        if weeks_avg_points != float("inf")
        else current_date + timedelta(days=3653)
    )
    med_points_completion_date = (
        current_date + timedelta(days=min(weeks_med_points * 7, 3653))
        if weeks_med_points != float("inf")
        else current_date + timedelta(days=3653)
    )

    # Format dates and values for display with enhanced format
    items_completion_str = items_completion_date.strftime("%Y-%m-%d")
    points_completion_str = points_completion_date.strftime("%Y-%m-%d")

    # Format dates for average and median completion
    avg_items_completion_str = avg_items_completion_date.strftime("%Y-%m-%d")
    med_items_completion_str = med_items_completion_date.strftime("%Y-%m-%d")
    avg_points_completion_str = avg_points_completion_date.strftime("%Y-%m-%d")
    med_points_completion_str = med_points_completion_date.strftime("%Y-%m-%d")

    # Enhanced formatted strings for average and median
    avg_items_days = weeks_avg_items * 7
    med_items_days = weeks_med_items * 7
    avg_points_days = weeks_avg_points * 7
    med_points_days = weeks_med_points * 7

    # Sample trend values for demonstration
    # In a production system, these would ideally be calculated from real data
    avg_items_trend = 10  # sample value: 10% increase from previous period
    med_items_trend = -5  # sample value: 5% decrease from previous period
    avg_points_trend = 0  # sample value: no change
    med_points_trend = 15  # sample value: 15% increase from previous period

    # Get icons and colors for each metric
    avg_items_icon, avg_items_icon_color = _get_trend_icon_and_color(avg_items_trend)
    med_items_icon, med_items_icon_color = _get_trend_icon_and_color(med_items_trend)
    avg_points_icon, avg_points_icon_color = _get_trend_icon_and_color(avg_points_trend)
    med_points_icon, med_points_icon_color = _get_trend_icon_and_color(med_points_trend)

    # Use the provided deadline string instead of recalculating
    if deadline_str:
        deadline_date_str = deadline_str
    else:
        # Fallback to calculation if not provided
        deadline_date = current_date + timedelta(days=days_to_deadline)
        deadline_date_str = deadline_date.strftime("%Y-%m-%d")

    # Calculate completed items and points from statistics data
    completed_items = 0
    completed_points = 0
    if statistics_df is not None and not statistics_df.empty:
        completed_items = int(statistics_df["completed_items"].sum())
        completed_points = int(statistics_df["completed_points"].sum())

    # Calculate actual total project items and points
    actual_total_items = completed_items + total_items
    actual_total_points = round(completed_points + total_points)

    # Round the remaining points to natural number for display
    remaining_points = round(total_points)

    # Calculate percentages based on actual project totals
    items_percentage = (
        int((completed_items / actual_total_items) * 100)
        if actual_total_items > 0
        else 0
    )
    points_percentage = (
        int((completed_points / actual_total_points) * 100)
        if actual_total_points > 0
        else 0
    )

    # Check if percentages are similar (within 2% of each other)
    similar_percentages = abs(items_percentage - points_percentage) <= 2

    return html.Div(
        [
            # Project Overview section at the top - full width (100%)
            html.Div(
                [
                    # Replace direct icon definition with utility function - Phase 9.2 progressive disclosure
                    _create_header_with_icon(
                        "fas fa-project-diagram",
                        "Project Overview",
                        "#20c997",
                        tooltip_text=PROJECT_HELP_TEXTS["project_overview"],
                        help_key="project_overview",
                        help_category="forecast",
                    ),
                    html.Div(
                        [
                            # Project progress section
                            _create_project_overview_section(
                                items_percentage,
                                points_percentage,
                                completed_items,
                                completed_points,
                                actual_total_items,
                                actual_total_points,
                                total_items,
                                remaining_points,
                                similar_percentages,
                                show_points,
                            ),
                            # Deadline card
                            _create_deadline_section(
                                deadline_date_str, days_to_deadline
                            ),
                        ],
                        className="p-3 border rounded h-100",
                    ),
                ],
                className="mb-4",
            ),
            # Reorganized layout: Completion Forecast and Weekly Velocity side by side
            dbc.Row(
                [
                    # Left column - Completion Forecast
                    dbc.Col(
                        [
                            # Replace direct icon definition with utility function - Phase 9.2 progressive disclosure
                            _create_header_with_icon(
                                "fas fa-calendar-check",
                                "Completion Forecast",
                                "#20c997",
                                tooltip_text=FORECAST_HELP_TEXTS["pert_methodology"],
                                help_key="pert_methodology",
                                help_category="forecast",
                            ),
                            _create_completion_forecast_section(
                                items_completion_str,
                                points_completion_str,
                                pert_time_items,
                                pert_time_points,
                                items_color,
                                points_color,
                                avg_items_completion_str,
                                med_items_completion_str,
                                avg_points_completion_str,
                                med_points_completion_str,
                                weeks_avg_items,
                                weeks_med_items,
                                weeks_avg_points,
                                weeks_med_points,
                                avg_items_days,
                                med_items_days,
                                avg_points_days,
                                med_points_days,
                                weeks_avg_items_color,
                                weeks_med_items_color,
                                weeks_avg_points_color,
                                weeks_med_points_color,
                                show_points=show_points,  # Pass show_points parameter
                            ),
                        ],
                        width=12,
                        lg=6,
                        className="mb-3 mb-lg-0",
                    ),
                    # Right column - Weekly Velocity with improved mobile responsiveness
                    dbc.Col(
                        [
                            # Add wrapper div with significant mobile-specific top margin and padding to prevent overlap
                            html.Div(
                                [
                                    _create_header_with_icon(
                                        "fas fa-tachometer-alt",
                                        "Weekly Velocity",
                                        "#6610f2",
                                        tooltip_text=VELOCITY_HELP_TEXTS[
                                            "weekly_velocity"
                                        ],
                                        help_key="weekly_velocity_calculation",
                                        help_category="velocity",
                                    ),
                                    _create_weekly_velocity_section(
                                        avg_weekly_items,
                                        med_weekly_items,
                                        avg_weekly_points,
                                        med_weekly_points,
                                        avg_items_trend,
                                        med_items_trend,
                                        avg_points_trend,
                                        med_points_trend,
                                        avg_items_icon,
                                        avg_items_icon_color,
                                        med_items_icon,
                                        med_items_icon_color,
                                        avg_points_icon,
                                        avg_points_icon_color,
                                        med_points_icon,
                                        med_points_icon_color,
                                        show_points=show_points,  # Pass show_points parameter
                                        data_points_count=data_points_count,  # NEW PARAMETER
                                        total_data_points=len(statistics_df)
                                        if statistics_df is not None
                                        and not statistics_df.empty
                                        else None,  # NEW PARAMETER
                                    ),
                                ],
                                className="mt-3 mt-lg-0",  # Add top margin for mobile
                            ),
                        ],
                        width=12,
                        lg=6,
                    ),
                ],
                className="mb-4",
            ),
        ],
    )


#######################################################################
# TREND INDICATOR COMPONENT
#######################################################################


def create_compact_trend_indicator(trend_data, metric_name="Items"):
    """
    Create a compact trend indicator component that shows performance trends in a space-efficient way.

    Args:
        trend_data: Dictionary containing trend information
        metric_name: Name of the metric being shown (Items or Points)

    Returns:
        Dash component for displaying trend information in a compact format
    """
    # Extract values from trend data or use defaults
    percent_change = trend_data.get("percent_change", 0)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)

    # Determine trend direction and colors
    if abs(percent_change) < 5:
        direction = "stable"
        icon_class = TREND_ICONS["stable"]
        text_color = TREND_COLORS["stable"]
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
    elif percent_change > 0:
        direction = "up"
        icon_class = TREND_ICONS["up"]
        text_color = TREND_COLORS["up"]
        bg_color = "rgba(40, 167, 69, 0.1)"
        border_color = "rgba(40, 167, 69, 0.2)"
    else:
        direction = "down"
        icon_class = TREND_ICONS["down"]
        text_color = TREND_COLORS["down"]
        bg_color = "rgba(220, 53, 69, 0.1)"
        border_color = "rgba(220, 53, 69, 0.2)"

    # Create the compact trend indicator
    return html.Div(
        className="compact-trend-indicator d-flex align-items-center p-2 rounded mb-3",
        style={
            "backgroundColor": bg_color,
            "border": f"1px solid {border_color}",
            "maxWidth": "100%",
        },
        children=[
            # Trend icon with circle background
            html.Div(
                className="trend-icon me-3 d-flex align-items-center justify-content-center rounded-circle",
                style={
                    "width": "36px",
                    "height": "36px",
                    "backgroundColor": "white",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "flexShrink": 0,
                },
                children=html.I(
                    className=f"{icon_class}",
                    style={"color": text_color, "fontSize": "1rem"},
                ),
            ),
            # Trend information
            html.Div(
                className="trend-info",
                style={"flexGrow": 1, "minWidth": 0},
                children=[
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline",
                        children=[
                            html.Span(
                                f"Weekly {metric_name} Trend",
                                className="fw-medium",
                                style={"fontSize": "0.9rem"},
                            ),
                            html.Span(
                                f"{abs(percent_change)}% {direction.capitalize()}",
                                style={
                                    "color": text_color,
                                    "fontWeight": "500",
                                    "fontSize": "0.9rem",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline mt-1",
                        style={"fontSize": "0.8rem", "color": "#6c757d"},
                        children=[
                            html.Span(
                                f"4-week avg: {current_avg} {metric_name.lower()}/week",
                                style={"marginRight": "15px"},
                            ),
                            html.Span(
                                f"Previous: {previous_avg} {metric_name.lower()}/week",
                                style={"marginLeft": "5px"},
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def create_trend_indicator(trend_data, metric_name="Items"):
    """
    Create a trend indicator component that shows performance trends.

    Args:
        trend_data: Dictionary containing trend information
        metric_name: Name of the metric being shown (Items or Points)

    Returns:
        Dash component for displaying trend information
    """
    # Extract values from trend data or use defaults
    percent_change = trend_data.get("percent_change", 0)
    is_significant = trend_data.get("is_significant", False)
    weeks = trend_data.get("weeks_compared", 4)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)

    # Determine trend direction based on percent change
    if abs(percent_change) < 5:
        direction = "stable"
    elif percent_change > 0:
        direction = "up"
    else:
        direction = "down"

    # Use global constants for icons and colors
    text_color = TREND_COLORS[direction]
    icon_class = TREND_ICONS[direction]

    # Determine font weight based on significance
    font_weight = "bold" if is_significant else "normal"

    # Build the component
    return html.Div(
        [
            html.H6(f"{metric_name} Trend (Last {weeks * 2} Weeks)", className="mb-2"),
            html.Div(
                [
                    html.I(
                        className=icon_class,
                        style={
                            "color": text_color,
                            "fontSize": "1.5rem",
                            "marginRight": "10px",
                        },
                    ),
                    html.Span(
                        f"{abs(percent_change)}% {'Increase' if direction == 'up' else 'Decrease' if direction == 'down' else 'Change'}",
                        style={
                            "color": text_color,
                            "fontWeight": font_weight,
                            "fontSize": "1.2rem",
                        },
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Recent Average: ", className="font-weight-bold"),
                            html.Span(f"{current_avg} {metric_name.lower()}/week"),
                        ],
                        className="mr-3",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Previous Average: ", className="font-weight-bold"
                            ),
                            html.Span(f"{previous_avg} {metric_name.lower()}/week"),
                        ],
                    ),
                ],
                className="d-flex flex-wrap small text-muted",
            ),
            # Add warning/celebration message for significant changes
            html.Div(
                html.Span(
                    f"This {'increase' if direction == 'up' else 'decrease' if direction == 'down' else 'trend'} is {'statistically significant' if is_significant else 'not statistically significant'}.",
                    className=f"{'text-success' if direction == 'up' and is_significant else 'text-danger' if direction == 'down' and is_significant else 'text-muted'}",
                ),
                className="mt-2 small",
                style={"display": "block" if is_significant else "none"},
            ),
        ],
        className="trend-indicator mb-4 p-3 border rounded",
        style={
            "backgroundColor": f"rgba({text_color.replace('#', '')}, 0.05)"
            if text_color.startswith("#")
            else "rgba(108, 117, 125, 0.05)",
        },
    )


#######################################################################
# EXPORT BUTTONS COMPONENT
#######################################################################


def create_export_buttons(chart_id=None, statistics_data=None):
    """
    Create a row of export buttons for charts or statistics data.

    Args:
        chart_id: ID of the chart for export filename
        statistics_data: Statistics data to export (if provided, shows statistics export button)

    Returns:
        Dash Div component with export buttons
    """
    buttons = []

    if chart_id:
        # Add PNG export button for charts using the new button styling system
        png_button = create_button(
            children=[html.I(className="fas fa-file-image me-2"), "Export Image"],
            id=f"{chart_id}-png-button",
            variant="secondary",
            size="sm",
            outline=True,
            tooltip="Export chart as image",
            className="me-2",
        )
        buttons.append(png_button)

    return html.Div(
        buttons,
        className="d-flex justify-content-end mb-3",
    )


#######################################################################
# FORM VALIDATION COMPONENT
#######################################################################


def create_validation_message(message, show=False, type="invalid"):
    """
    Create a validation message for form inputs with consistent styling.

    Args:
        message (str): The validation message to display
        show (bool): Whether to show the message (default: False)
        type (str): The type of validation (valid, invalid, warning)

    Returns:
        html.Div: A validation message component
    """
    # Determine the appropriate style class based on validation type
    class_name = "d-none"
    if show:
        if type == "valid":
            class_name = "valid-feedback d-block"
        elif type == "warning":
            class_name = "text-warning d-block"
        else:
            class_name = "invalid-feedback d-block"

    # Get the base style from the styling function
    base_style = create_form_feedback_style(type)

    # Add icon based on the type
    icon_class = ""
    if type == "valid":
        icon_class = "fas fa-check-circle me-1"
    elif type == "warning":
        icon_class = "fas fa-exclamation-triangle me-1"
    elif type == "invalid":
        icon_class = "fas fa-times-circle me-1"

    # Return the validation message component
    return html.Div(
        [html.I(className=icon_class) if icon_class else "", message],
        className=class_name,
        style=base_style,
    )


#######################################################################
# ERROR ALERT COMPONENT
#######################################################################


def create_error_alert(
    message="An unexpected error occurred. Please try again later.",
    title="Error",
    error_details=None,
):
    """
    Creates a standardized Bootstrap Alert component for displaying errors.

    Args:
        message (str): The main user-friendly error message.
        title (str): The title for the alert.
        error_details (str, optional): Additional technical details to display,
                                       potentially hidden by default.

    Returns:
        dbc.Alert: A Dash Bootstrap Components Alert.
    """
    children = [
        html.H4(
            create_icon_text("error", title, size="md"),
            className="alert-heading d-flex align-items-center",
        ),
        html.P(message),
    ]
    if error_details:
        children.extend(
            [
                html.Hr(),
                html.P(f"Details: {error_details}", className="mb-0 small text-muted"),
            ]
        )

    return dbc.Alert(
        children,
        color="danger",
        dismissable=True,
        className="error-alert",
    )


def _create_velocity_footer_content(data_points_count=None, total_data_points=None):
    """
    Create footer content for velocity section showing data filtering context.

    Args:
        data_points_count: Number of data points used for calculations
        total_data_points: Total data points available

    Returns:
        list: Footer content elements
    """
    # Update footer to show data filtering context
    footer_text = "Based on 10-week rolling average for forecasting accuracy"
    tooltip_key = "velocity-ten-week-calculation"
    tooltip_text = VELOCITY_HELP_TEXTS["ten_week_calculation"]

    if data_points_count is not None and total_data_points is not None:
        if data_points_count < total_data_points:
            footer_text = f"Based on last {data_points_count} weeks of data (filtered from {total_data_points} available weeks)"
            tooltip_key = "velocity-data-filtering"
            tooltip_text = f"Velocity calculations use the most recent {data_points_count} data points as selected by the 'Data Points to Include' slider."

    return [
        html.I(
            className="fas fa-calendar-week me-1",
            style={"color": "#6c757d"},
        ),
        footer_text,
        create_info_tooltip(
            tooltip_key,
            tooltip_text,
        ),
    ]
