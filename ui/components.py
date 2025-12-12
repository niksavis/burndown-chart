"""
UI Components Module

This module provides reusable UI components like tooltips, modals, and information tables
that are used across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import re
import time
from datetime import datetime, timedelta
from typing import Optional, Any

import dash_bootstrap_components as dbc

# Third-party library imports
from dash import dcc, html

# Application imports
from configuration import COLOR_PALETTE
from configuration.settings import (
    FORECAST_HELP_TEXTS,
    PROJECT_HELP_TEXTS,
    VELOCITY_HELP_TEXTS,
)
from ui.button_utils import create_button
from ui.icon_utils import create_icon_text
from ui.style_constants import get_spacing, get_color
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
# ATOMIC COMPONENT BUILDERS (Following Component Contracts)
#######################################################################


def create_input_field(
    label: str,
    input_type: str = "text",
    input_id: str = "",
    placeholder: str = "",
    value: Any = None,
    required: bool = False,
    size: str = "md",
    **kwargs,
) -> html.Div:
    """
    Create a labeled input field with validation support.

    This function follows the component builder contract specification
    in specs/006-ux-ui-redesign/contracts/component-builders.md

    Args:
        label: Display label for input field (required)
        input_type: HTML input type - "text", "number", "date", "email", "password", "tel", "url"
        input_id: Unique ID for input element (if empty, generated from label)
        placeholder: Placeholder text
        value: Initial/current value
        required: Whether field is required
        size: Input size - "sm", "md", "lg"
        **kwargs: Additional props (min, max, step, disabled, invalid, valid, etc.)

    Returns:
        html.Div containing dbc.Label and dbc.Input

    Raises:
        ValueError: If label is empty or input_type is invalid

    Examples:
        >>> create_input_field("Deadline", input_type="date", value="2025-12-31")
        >>> create_input_field("PERT Factor", input_type="number", min=1.0, max=3.0, step=0.1)
        >>> create_input_field("Email", input_type="email", required=True)

    ID Pattern: input-{label-slugified} or provided input_id

    Accessibility:
        - Label properly associated with input via htmlFor/id
        - Required fields marked with aria-required
        - Invalid state communicated via aria-invalid
    """
    # Validation
    if not label or label.strip() == "":
        raise ValueError("Label is required and cannot be empty")

    valid_input_types = ["text", "number", "date", "email", "password", "tel", "url"]
    if input_type not in valid_input_types:
        raise ValueError(
            f"Invalid input_type '{input_type}'. Must be one of: {', '.join(valid_input_types)}"
        )

    # Generate ID from label if not provided
    if not input_id:
        label_slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        input_id = f"input-{label_slug}"

    # dbc.Input handles accessibility internally via 'required' and 'invalid' props
    # No need to add aria-* attributes manually

    # Get spacing from design tokens
    spacing = get_spacing("sm")

    # Create the input field
    # Note: dbc.Input automatically handles aria-required when required=True
    # and aria-invalid when invalid=True
    input_field = dbc.Input(
        type=input_type,  # type: ignore[arg-type]
        id=input_id,
        placeholder=placeholder,
        value=value,
        required=required,
        size=size,
        **kwargs,
    )

    # Create label with required indicator
    label_content = label
    if required:
        label_content = [
            label,
            html.Span(" *", style={"color": get_color("danger")}),
        ]

    label_element = dbc.Label(
        label_content, html_for=input_id, style={"marginBottom": spacing}
    )

    # Return wrapped in div
    return html.Div(
        [label_element, input_field],
        style={"marginBottom": get_spacing("md")},
    )


def create_labeled_input(
    label: str,
    input_id: str,
    input_type: str = "text",
    value: Any = None,
    help_text: str = "",
    error_message: str = "",
    size: str = "md",
    **kwargs,
) -> html.Div:
    """
    Create input field with label, help text, and error message support.

    This function follows the component builder contract specification
    in specs/006-ux-ui-redesign/contracts/component-builders.md

    Args:
        label: Display label text (required)
        input_id: Unique ID for input (required)
        input_type: HTML input type
        value: Initial value
        help_text: Optional help text displayed below input
        error_message: Error message (shown only if invalid=True in kwargs)
        size: Component size
        **kwargs: Additional props passed to dbc.Input (invalid, valid, disabled, etc.)

    Returns:
        html.Div containing label, input, help text, and error feedback

    Raises:
        ValueError: If label or input_id is empty

    Examples:
        >>> create_labeled_input("PERT Factor", "pert-input", input_type="number",
        ...                      help_text="Typically 1.5-2.0", min=1.0, max=3.0)
        >>> create_labeled_input("Deadline", "deadline-input", input_type="date",
        ...                      error_message="Date must be in future", invalid=True)

    Accessibility:
        - Help text linked via aria-describedby
        - Error messages linked via aria-describedby
        - Invalid state properly communicated
    """
    # Validation
    if not label or label.strip() == "":
        raise ValueError("Label is required and cannot be empty")

    if not input_id or input_id.strip() == "":
        raise ValueError("input_id is required and cannot be empty")

    valid_input_types = ["text", "number", "date", "email", "password", "tel", "url"]
    if input_type not in valid_input_types:
        raise ValueError(
            f"Invalid input_type '{input_type}'. Must be one of: {', '.join(valid_input_types)}"
        )

    # Build aria-describedby references for accessibility
    # Note: dbc.Input doesn't accept aria-describedby directly, but we can
    # link help text and errors through proper HTML structure and IDs
    help_text_id = f"{input_id}-help" if help_text else None
    error_id = f"{input_id}-error" if error_message else None

    # Create input element
    # dbc.Input handles aria-invalid automatically when invalid=True
    input_element = dbc.Input(
        type=input_type,  # type: ignore[arg-type]
        id=input_id,
        value=value,
        size=size,
        **kwargs,
    )

    # Create components list
    components = [dbc.Label(label, html_for=input_id), input_element]

    # Add help text if provided
    if help_text:
        components.append(dbc.FormText(help_text, id=help_text_id, color="muted"))

    # Add error feedback if provided and invalid
    if error_message and kwargs.get("invalid", False):
        components.append(dbc.FormFeedback(error_message, id=error_id, type="invalid"))

    # Return as Div (FormGroup is deprecated in dbc 2.x)
    return html.Div(components, style={"marginBottom": get_spacing("md")})


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
                                "Projected completion date based on historical velocity and confidence window analysis.",
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
                    "Confidence Window",
                    create_formula_tooltip(
                        f"pert-forecast-{metric_type}",
                        FORECAST_HELP_TEXTS["expected_forecast"],
                        "Confidence Window = (O + 4×M + P) / 6",
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
                            "Confidence Window three-point estimation (optimistic + most likely + pessimistic)",
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


#######################################################################
# PARAMETER PANEL COMPONENTS (User Story 1)
#######################################################################


def create_parameter_bar_collapsed(
    pert_factor: float,
    deadline: str,
    scope_items: int,
    scope_points: int,
    id_suffix: str = "",
    remaining_items: int | None = None,
    remaining_points: int | None = None,
    show_points: bool = True,
    data_points: int | None = None,
    profile_name: str | None = None,
    query_name: str | None = None,
) -> html.Div:
    """
    Create collapsed parameter bar showing key values and expand button.

    This component supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    When collapsed, it displays a compact summary of current parameter values with an
    expand button to show the full parameter panel.

    Args:
        pert_factor: Current PERT factor value
        deadline: Current deadline date string
        scope_items: Total number of items in scope (fallback)
        scope_points: Total story points in scope (fallback)
        id_suffix: Suffix for generating unique IDs
        remaining_items: Number of items remaining to complete (preferred display)
        remaining_points: Number of points remaining to complete (preferred display)
        show_points: Whether to show points data
        data_points: Number of weeks of data used for forecasting
        profile_name: Name of active profile (if in profiles mode)
        query_name: Name of active query (if in profiles mode)

    Returns:
        html.Div: Collapsed parameter bar component

    Example:
        >>> create_parameter_bar_collapsed(1.5, "2025-12-31", 100, 500, remaining_items=50)
    """
    from ui.style_constants import DESIGN_TOKENS

    bar_id = f"parameter-bar-collapsed{'-' + id_suffix if id_suffix else ''}"
    expand_btn_id = f"btn-expand-parameters{'-' + id_suffix if id_suffix else ''}"

    # Use remaining values if available, otherwise fall back to scope values
    display_items = remaining_items if remaining_items is not None else scope_items
    display_points = remaining_points if remaining_points is not None else scope_points

    # Determine label based on what we're showing
    items_label = "Remaining" if remaining_items is not None else "Scope"

    # Create points display only if enabled
    points_display = []
    if show_points:
        # Round points to natural number for display
        display_points_rounded = int(round(display_points))
        points_display = [
            html.Span(
                [
                    html.I(className="fas fa-chart-bar me-1"),
                    html.Span(
                        f"{items_label}: ",
                        className="text-muted d-none d-lg-inline",
                        style={"fontSize": "0.85em"},
                    ),
                    html.Span(
                        f"{display_points_rounded:,}", style={"fontSize": "0.85em"}
                    ),
                ],
                className="param-summary-item",
                title=f"{items_label}: {display_points_rounded:,} points",
            ),
        ]

    # Build profile/query display section if in profiles mode
    profile_query_display = []
    if profile_name and query_name:
        profile_query_display = [
            html.Span(
                [
                    html.I(className="fas fa-folder me-1"),
                    html.Span(
                        profile_name,
                        className="text-muted d-none d-lg-inline",
                        style={"fontSize": "0.85em"},
                    ),
                    html.Span(
                        " / ",
                        className="text-muted d-none d-lg-inline",
                        style={"fontSize": "0.85em"},
                    ),
                    html.I(className="fas fa-search me-1"),
                    html.Span(
                        query_name,
                        className="text-muted d-none d-lg-inline",
                        style={"fontSize": "0.85em"},
                    ),
                ],
                className="param-summary-item me-1 me-sm-2 profile-query-display",
                title=f"Profile: {profile_name} | Query: {query_name}",
            ),
        ]

    return html.Div(
        [
            # Single row with all items on the same level
            html.Div(
                [
                    # Summary items (left side)
                    html.Div(
                        profile_query_display
                        + [
                            html.Span(
                                [
                                    html.I(className="fas fa-sliders-h me-1"),
                                    html.Span(
                                        "Window: ",
                                        className="text-muted d-none d-lg-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{pert_factor}w", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Confidence Window: {pert_factor} weeks (samples best/worst case from your velocity history)",
                            ),
                            html.Span(
                                [
                                    html.I(className="fas fa-chart-line me-1"),
                                    html.Span(
                                        "Data: ",
                                        className="text-muted d-none d-lg-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{data_points}w", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Data Points: {data_points} weeks of historical data used for forecasting",
                                style={"display": "inline" if data_points else "none"},
                            )
                            if data_points
                            else html.Span(),
                            html.Span(
                                [
                                    html.I(className="fas fa-calendar me-1"),
                                    html.Span(
                                        "Deadline: ",
                                        className="text-muted d-none d-lg-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{deadline}", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Project deadline: {deadline}",
                            ),
                            html.Span(
                                [
                                    html.I(className="fas fa-tasks me-1"),
                                    html.Span(
                                        f"{items_label}: ",
                                        className="text-muted d-none d-lg-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{display_items:,}",
                                        style={"fontSize": "0.85em"},
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"{items_label}: {display_items:,} items",
                            ),
                        ]
                        + points_display,
                        className="d-flex align-items-center flex-wrap flex-grow-1",
                    ),
                    # Buttons (right side)
                    html.Div(
                        [
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-sliders-h",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Parameters",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id=expand_btn_id,
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "flexShrink": "0",
                                },
                                title="Adjust project parameters",
                            ),
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-cog",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Settings",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id="settings-button",
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                                title="Configure JIRA and queries",
                            ),
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-exchange-alt",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Data",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id="toggle-import-export-panel",
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                                title="Import or export data",
                            ),
                        ],
                        className="d-flex justify-content-end align-items-center flex-nowrap flex-shrink-0",
                        style={"minWidth": "fit-content"},
                    ),
                ],
                className="d-flex align-items-center justify-content-between flex-wrap",
            ),
        ],
        className="parameter-bar-collapsed",
        id=bar_id,
        style={
            "padding": DESIGN_TOKENS["spacing"]["sm"],
            "backgroundColor": DESIGN_TOKENS["colors"]["gray-100"],
            "borderRadius": DESIGN_TOKENS["layout"]["borderRadius"]["md"],
            "marginBottom": DESIGN_TOKENS["spacing"]["xs"],
        },
    )


def create_settings_tab_content(
    settings: dict,
    id_suffix: str = "",
) -> html.Div:
    """
    Create settings tab content for data source configuration and import/export.

    This replaces the old Data Import Configuration card, now accessible from
    the Parameter Panel Settings tab.

    Args:
        settings: Dictionary containing current settings
        id_suffix: Suffix for generating unique IDs

    Returns:
        html.Div: Settings tab content with data source config and import/export
    """
    from ui.jql_editor import create_jql_editor
    from ui.jira_config_modal import create_jira_config_button
    from ui.button_utils import create_button

    # Import helper functions from cards module
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ui.cards import (
        _get_default_data_source,
        _get_default_jql_query,
        _get_default_jql_profile_id,
        _get_query_profile_options,
    )

    return html.Div(
        [
            # Data Source Selection
            html.Div(
                [
                    html.H6(
                        [
                            html.I(
                                className="fas fa-database me-2",
                                style={"color": "#20c997"},
                            ),
                            "Data Source",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    dbc.RadioItems(
                        id="data-source-selection",
                        options=[
                            {"label": "JIRA API", "value": "JIRA"},
                            {"label": "JSON/CSV Import", "value": "CSV"},
                        ],
                        value=_get_default_data_source(),
                        inline=True,
                        className="mb-3",
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # CSV Upload Container
            html.Div(
                id="csv-upload-container",
                style={
                    "display": "none"
                    if _get_default_data_source() == "JIRA"
                    else "block"
                },
                children=[
                    html.H6(
                        [
                            html.I(
                                className="fas fa-upload me-2",
                                style={"color": "#0d6efd"},
                            ),
                            "File Upload",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(
                            [
                                html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                                html.Br(),
                                "Drag and Drop or Click to Select",
                            ],
                            className="text-center",
                        ),
                        style={
                            "width": "100%",
                            "height": "100px",
                            "borderWidth": "2px",
                            "borderStyle": "dashed",
                            "borderRadius": "8px",
                            "borderColor": "#dee2e6",
                            "backgroundColor": "#f8f9fa",
                            "cursor": "pointer",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                        },
                        multiple=False,
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # JIRA Configuration Container
            html.Div(
                id="jira-config-container",
                style={
                    "display": "block"
                    if _get_default_data_source() == "JIRA"
                    else "none"
                },
                children=[
                    # JIRA Connection Button
                    html.H6(
                        [
                            html.I(
                                className="fas fa-plug me-2", style={"color": "#0d6efd"}
                            ),
                            "JIRA Connection",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    create_jira_config_button(),
                    html.Div(
                        id="jira-config-status-indicator",
                        className="mt-2 mb-3",
                        children=[],
                    ),
                    # JQL Query Management
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(
                                        className="fas fa-code me-2",
                                        style={"color": "#6610f2"},
                                    ),
                                    "JQL Query",
                                ],
                                className="mb-3",
                                style={"fontSize": "0.9rem", "fontWeight": "600"},
                            ),
                            create_jql_editor(
                                editor_id="jira-jql-query",
                                initial_value=_get_default_jql_query(),
                                placeholder="project = MYPROJECT AND created >= startOfYear()",
                                rows=3,
                            ),
                            html.Div(
                                id="jira-jql-character-count-container",
                                children=[
                                    create_character_count_display(
                                        count=len(_get_default_jql_query() or ""),
                                        warning=should_show_character_warning(
                                            _get_default_jql_query()
                                        ),
                                    )
                                ],
                                className="mb-2",
                            ),
                            # Query Actions
                            html.Div(
                                [
                                    create_button(
                                        text="Save Query",
                                        id="save-jql-query-button",
                                        variant="primary",
                                        icon_class="fas fa-save",
                                        size="sm",
                                        className="me-2 mb-2",
                                    ),
                                    dcc.Dropdown(
                                        id="jql-profile-selector",
                                        options=_get_query_profile_options(),
                                        value=_get_default_jql_profile_id(),
                                        placeholder="Select saved query",
                                        clearable=True,
                                        searchable=True,
                                        style={
                                            "minWidth": "200px",
                                            "maxWidth": "300px",
                                            "display": "inline-block",
                                        },
                                        className="me-2 mb-2",
                                    ),
                                    create_button(
                                        text="Clear",
                                        id="clear-jql-query-button",
                                        variant="outline-secondary",
                                        icon_class="fas fa-eraser",
                                        size="sm",
                                        className="mb-2",
                                    ),
                                ],
                                className="d-flex flex-wrap align-items-center mb-2",
                            ),
                            html.Div(
                                id="jira-jql-query-save-status",
                                className="text-center mt-2 mb-3",
                                children=[],
                            ),
                            # Update Data Button
                            create_button(
                                text="Update Data",
                                id="update-data-unified",
                                variant="primary",
                                icon_class="fas fa-sync-alt",
                                className="w-100 mb-2",
                            ),
                            html.Div(
                                id="jira-cache-status",
                                className="text-center text-muted small",
                                children="Ready to fetch JIRA data",
                            ),
                        ],
                        className="mb-3",
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # Export Options
            html.Div(
                [
                    html.H6(
                        [
                            html.I(
                                className="fas fa-file-export me-2",
                                style={"color": "#6c757d"},
                            ),
                            "Export Data",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    create_button(
                        text="Export Project Data",
                        id="export-project-data-button",
                        variant="secondary",
                        icon_class="fas fa-file-export",
                        className="w-100 mb-2",
                    ),
                    html.Small(
                        "Export complete project data as JSON",
                        className="text-muted d-block text-center",
                    ),
                    html.Div(dcc.Download(id="export-project-data-download")),
                ],
            ),
        ],
        style={"padding": "1rem"},
    )


def create_parameter_panel_expanded(
    settings: dict,
    id_suffix: str = "",
    statistics: Optional[list] = None,
) -> html.Div:
    """
    Create expanded parameter panel section with all input fields.

    This component supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    When expanded, it displays ALL forecast-critical parameter input fields matching
    the functionality of the old Input Parameters card with improved UX using sliders.

    User Story 6: Contextual Help System - Adds help icons to parameter inputs.

    Args:
        settings: Dictionary containing current parameter values (pert_factor, deadline, etc.)
        id_suffix: Suffix for generating unique IDs
        statistics: Optional list of statistics data points for calculating max data points

    Returns:
        html.Div: Expanded parameter panel with complete input fields and help tooltips

    Example:
        >>> settings = {"pert_factor": 3, "deadline": "2025-12-31", "show_milestone": True}
        >>> create_parameter_panel_expanded(settings)
    """
    from datetime import datetime
    from ui.help_system import create_parameter_tooltip

    panel_id = f"parameter-panel-expanded{'-' + id_suffix if id_suffix else ''}"

    # Extract settings with defaults
    pert_factor = settings.get("pert_factor", 3)
    deadline = (
        settings.get("deadline", "2025-12-31") or None
    )  # Convert empty string to None
    milestone = settings.get("milestone", None) or None  # Convert empty string to None
    total_items = settings.get("total_items", 0)
    estimated_items = settings.get("estimated_items", 0)
    total_points = settings.get("total_points", 0)
    estimated_points = settings.get("estimated_points", 0)
    show_points = settings.get("show_points", False)
    data_points_count = settings.get("data_points_count", 10)

    # Calculate max data points from statistics if available
    max_data_points = 52  # Default max
    if statistics and len(statistics) > 0:
        max_data_points = len(statistics)

    # Calculate dynamic marks for Data Points slider
    # 5 points: min (4), 1/4, 1/2 (middle), 3/4, max
    import math

    min_data_points = 4
    range_size = max_data_points - min_data_points
    quarter_point = math.ceil(min_data_points + range_size / 4)
    middle_point = math.ceil(min_data_points + range_size / 2)
    three_quarter_point = math.ceil(min_data_points + 3 * range_size / 4)

    data_points_marks: dict[int, dict[str, str]] = {
        min_data_points: {"label": str(min_data_points)},
        quarter_point: {"label": str(quarter_point)},
        middle_point: {"label": str(middle_point)},
        three_quarter_point: {"label": str(three_quarter_point)},
        max_data_points: {"label": str(max_data_points)},
    }

    return html.Div(
        [
            html.Div(
                [
                    # Tabbed interface matching Settings panel
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                label="Parameters",
                                tab_id="parameters-tab",
                                label_style={"width": "100%"},
                                children=[
                                    html.Div(
                                        [
                                            # No header - tab label serves as title
                                            # Section 1: Project Timeline
                                            html.Div(
                                                [
                                                    html.H6(
                                                        [
                                                            html.I(
                                                                className="fas fa-calendar-alt me-2",
                                                                style={
                                                                    "color": "#0d6efd"
                                                                },
                                                            ),
                                                            "Project Timeline",
                                                        ],
                                                        className="mb-3 text-primary",
                                                        style={
                                                            "fontSize": "0.9rem",
                                                            "fontWeight": "600",
                                                        },
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            # Deadline Date Picker
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Deadline",
                                                                            html.Span(
                                                                                " *",
                                                                                className="text-danger",
                                                                            ),
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "deadline",
                                                                                    "deadline-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dcc.DatePickerSingle(
                                                                        id="deadline-picker",
                                                                        date=deadline,
                                                                        display_format="YYYY-MM-DD",
                                                                        first_day_of_week=1,
                                                                        placeholder="Select deadline",
                                                                        min_date_allowed=datetime.now().strftime(
                                                                            "%Y-%m-%d"
                                                                        ),
                                                                        className="w-100",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        id="deadline-feedback",
                                                                        className="invalid-feedback",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Milestone Date Picker (optional - activated when date is entered)
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        "Milestone (optional)",
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dcc.DatePickerSingle(
                                                                        id="milestone-picker",
                                                                        date=milestone,
                                                                        display_format="YYYY-MM-DD",
                                                                        first_day_of_week=1,
                                                                        placeholder="Select milestone",
                                                                        min_date_allowed=datetime.now().strftime(
                                                                            "%Y-%m-%d"
                                                                        ),
                                                                        className="w-100",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        id="milestone-feedback",
                                                                        className="invalid-feedback",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Confidence Window Slider (formerly PERT Factor)
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Confidence Window",
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "pert_factor",
                                                                                    "pert-factor-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dcc.Slider(
                                                                        id="pert-factor-slider",
                                                                        min=3,
                                                                        max=12,
                                                                        value=pert_factor,
                                                                        marks={
                                                                            3: {
                                                                                "label": "3",
                                                                                "style": {
                                                                                    "color": "#ff6b6b"
                                                                                },
                                                                            },
                                                                            6: {
                                                                                "label": "6 (rec)",
                                                                                "style": {
                                                                                    "color": "#51cf66"
                                                                                },
                                                                            },
                                                                            9: {
                                                                                "label": "9"
                                                                            },
                                                                            12: {
                                                                                "label": "12",
                                                                                "style": {
                                                                                    "color": "#339af0"
                                                                                },
                                                                            },
                                                                        },
                                                                        step=1,
                                                                        tooltip={
                                                                            "placement": "bottom",
                                                                            "always_visible": False,
                                                                        },
                                                                        className="mt-2",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Data Points Slider
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Data Points",
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "data_points",
                                                                                    "data-points-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dcc.Slider(
                                                                        id="data-points-input",
                                                                        min=4,  # Fixed minimum of 4 weeks for meaningful trend analysis
                                                                        max=max_data_points,
                                                                        value=data_points_count,
                                                                        marks=data_points_marks,  # type: ignore[arg-type]
                                                                        step=1,
                                                                        tooltip={
                                                                            "placement": "bottom",
                                                                            "always_visible": False,
                                                                        },
                                                                        className="mt-2",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                        ],
                                                        className="g-3",
                                                    ),
                                                ],
                                                className="mb-4 pb-3 border-bottom",
                                            ),
                                            # Section 2: Work Scope
                                            html.Div(
                                                [
                                                    # Section header with inline Points Tracking toggle
                                                    html.Div(
                                                        [
                                                            html.H6(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-tasks me-2",
                                                                        style={
                                                                            "color": "#20c997"
                                                                        },
                                                                    ),
                                                                    "Remaining Work Scope",
                                                                ],
                                                                className="mb-0 text-success",
                                                                style={
                                                                    "fontSize": "0.9rem",
                                                                    "fontWeight": "600",
                                                                },
                                                            ),
                                                            html.Div(
                                                                [
                                                                    dcc.Checklist(
                                                                        id="points-toggle",
                                                                        options=[
                                                                            {
                                                                                "label": "Points Tracking",
                                                                                "value": "show",
                                                                            }
                                                                        ],
                                                                        value=["show"]
                                                                        if show_points
                                                                        else [],
                                                                        className="m-0",
                                                                        labelStyle={
                                                                            "display": "flex",
                                                                            "alignItems": "center",
                                                                            "fontSize": "0.8rem",
                                                                            "color": "#6c757d",
                                                                            "margin": "0",
                                                                        },
                                                                        inputStyle={
                                                                            "marginRight": "8px",
                                                                            "marginTop": "0",
                                                                        },
                                                                        style={
                                                                            "fontSize": "0.8rem"
                                                                        },
                                                                    ),
                                                                ],
                                                                className="d-flex align-items-center",
                                                            ),
                                                        ],
                                                        className="d-flex justify-content-between align-items-center mb-3",
                                                    ),
                                                    # Single Row: All 4 fields with equal width
                                                    dbc.Row(
                                                        [
                                                            # Estimated Items
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Estimated Items",
                                                                            html.Span(
                                                                                " (optional)",
                                                                                className="text-muted small",
                                                                            ),
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "completed_items",
                                                                                    "estimated-items-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dbc.Input(
                                                                        id="estimated-items-input",
                                                                        type="number",
                                                                        value=estimated_items,
                                                                        min=0,
                                                                        step=1,
                                                                        placeholder="0 if unknown",
                                                                        className="form-control-sm",
                                                                    ),
                                                                    html.Small(
                                                                        "Items with effort estimates. Leave 0 if unavailable.",
                                                                        className="text-muted d-block mt-1",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Remaining Items
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Remaining Items",
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "total_items",
                                                                                    "remaining-items-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dbc.Input(
                                                                        id="total-items-input",
                                                                        type="number",
                                                                        value=total_items,
                                                                        min=0,
                                                                        step=1,
                                                                        className="form-control-sm",
                                                                    ),
                                                                    html.Div(
                                                                        id="total-items-feedback",
                                                                        className="invalid-feedback",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Estimated Points
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Estimated Points",
                                                                            html.Span(
                                                                                " (optional)",
                                                                                className="text-muted small",
                                                                            ),
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "completed_points",
                                                                                    "estimated-points-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dbc.Input(
                                                                        id="estimated-points-input",
                                                                        type="number",
                                                                        value=estimated_points,
                                                                        min=0,
                                                                        step=1,
                                                                        placeholder="0 if unknown",
                                                                        disabled=not show_points,
                                                                        className="form-control-sm",
                                                                    ),
                                                                    html.Small(
                                                                        "Items with story point estimates. Leave 0 if unavailable.",
                                                                        className="text-muted d-block mt-1",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                                id="estimated-points-col",
                                                            ),
                                                            # Remaining Points (auto-calculated)
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Remaining Points ",
                                                                            html.Span(
                                                                                "(auto)",
                                                                                className="badge bg-secondary",
                                                                                style={
                                                                                    "fontSize": "0.65rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dbc.Input(
                                                                        id="total-points-display",
                                                                        type="text",
                                                                        value=f"{total_points:.0f}",
                                                                        disabled=True,
                                                                        className="form-control-sm",
                                                                        style={
                                                                            "backgroundColor": "#e9ecef"
                                                                        },
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                                id="total-points-col",
                                                            ),
                                                        ],
                                                        className="g-3",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="settings-tab-content",
                                    )
                                ],
                            ),
                        ],
                        id="parameter-tabs",
                        active_tab="parameters-tab",
                        className="settings-tabs",
                    ),
                ],
                className="tabbed-settings-panel blue-accent-panel",
            ),
        ],
        id=panel_id,
        className="parameter-panel-container",
        # All styling via CSS for consistency (DRY principle)
    )


def create_parameter_panel(
    settings: dict,
    is_open: bool = False,
    id_suffix: str = "",
    statistics: Optional[list] = None,
) -> html.Div:
    """
    Create complete collapsible parameter panel combining collapsed bar and expanded section.

    This component supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    It combines the collapsed bar (always visible) with the expanded panel (toggleable)
    using Bootstrap's Collapse component for smooth transitions.

    Args:
        settings: Dictionary containing current parameter values
        is_open: Whether panel should start in expanded state
        id_suffix: Suffix for generating unique IDs
        statistics: Optional list of statistics data points for calculating max data points

    Returns:
        html.Div: Complete parameter panel with collapse functionality

    Example:
        >>> settings = {"pert_factor": 1.5, "deadline": "2025-12-31"}
        >>> create_parameter_panel(settings, is_open=False)
    """
    panel_id = f"parameter-panel{'-' + id_suffix if id_suffix else ''}"
    collapse_id = f"parameter-collapse{'-' + id_suffix if id_suffix else ''}"

    # Extract key values for collapsed bar
    pert_factor = settings.get("pert_factor", 3)
    deadline = (
        settings.get("deadline", "2025-12-31") or "2025-12-31"
    )  # Ensure valid default for display
    total_items = settings.get("total_items", 0)
    total_points = settings.get("total_points", 0)
    data_points = settings.get("data_points_count")
    show_points = settings.get("show_points", True)

    # CRITICAL FIX: Pass total_items/total_points as BOTH scope AND remaining values
    # The serve_layout() calculates these as remaining work at START of window,
    # so we should display them as "Remaining" not "Scope"
    # This ensures the initial banner matches the callback-updated banner

    # Get active profile and query names for display
    from data.profile_manager import get_active_profile_and_query_display_names

    display_names = get_active_profile_and_query_display_names()
    profile_name = display_names.get("profile_name")
    query_name = display_names.get("query_name")

    return html.Div(
        [
            # Collapsed bar (always visible)
            create_parameter_bar_collapsed(
                pert_factor=pert_factor,
                deadline=deadline,
                scope_items=total_items,  # Fallback if remaining_items is None
                scope_points=total_points,  # Fallback if remaining_points is None
                remaining_items=total_items
                if total_items > 0
                else None,  # Display as "Remaining"
                remaining_points=total_points
                if total_points > 0
                else None,  # Display as "Remaining"
                show_points=show_points,  # Respect Points Tracking toggle
                id_suffix=id_suffix,
                data_points=data_points,
                profile_name=profile_name,
                query_name=query_name,
            ),
            # Expanded panel (toggleable)
            dbc.Collapse(
                create_parameter_panel_expanded(
                    settings, id_suffix=id_suffix, statistics=statistics
                ),
                id=collapse_id,
                is_open=is_open,
            ),
        ],
        id=panel_id,
        className="parameter-panel-container",
    )


#######################################################################
# MOBILE PARAMETER BOTTOM SHEET (Phase 7: User Story 5 - T068)
#######################################################################


def create_mobile_parameter_fab() -> html.Div:
    """
    Create a floating action button (FAB) to trigger mobile parameter bottom sheet.

    This FAB appears only on mobile devices (<768px) and provides quick access
    to parameter adjustments via a bottom sheet interface optimized for touch.

    Returns:
        html.Div: FAB component with mobile-only visibility

    Example:
        >>> fab = create_mobile_parameter_fab()
    """
    from ui.style_constants import DESIGN_TOKENS

    return html.Div(
        [
            dbc.Button(
                html.I(className="fas fa-sliders-h", style={"fontSize": "1.25rem"}),
                id="mobile-param-fab",
                color="primary",
                className="mobile-param-fab",
                style={
                    "position": "fixed",
                    "bottom": "80px",  # Above mobile bottom nav
                    "right": DESIGN_TOKENS["mobile"]["fabPosition"],
                    "width": DESIGN_TOKENS["mobile"]["fabSize"],
                    "height": DESIGN_TOKENS["mobile"]["fabSize"],
                    "borderRadius": "50%",
                    "boxShadow": DESIGN_TOKENS["layout"]["shadow"]["lg"],
                    "zIndex": DESIGN_TOKENS["layout"]["zIndex"]["fixed"],
                    "display": "none",  # Hidden by default, shown via CSS media query
                },
                title="Adjust Parameters",
            ),
        ],
        className="d-md-none",  # Only visible on mobile
    )


def create_mobile_parameter_bottom_sheet(
    settings: dict, statistics: Optional[list] = None
) -> dbc.Offcanvas:
    """
    Create mobile-optimized parameter bottom sheet using dbc.Offcanvas.

    This component provides a touch-friendly alternative to the sticky parameter
    panel for mobile devices. It slides up from the bottom and contains all
    parameter inputs in a mobile-optimized layout.

    Args:
        settings: Dictionary containing current parameter values
        statistics: Optional list of statistics data points for calculating max data points

    Returns:
        dbc.Offcanvas: Mobile parameter bottom sheet component

    Example:
        >>> settings = {"pert_factor": 3, "deadline": "2025-12-31"}
        >>> sheet = create_mobile_parameter_bottom_sheet(settings)
    """
    from datetime import datetime
    from ui.style_constants import DESIGN_TOKENS

    # Extract settings with defaults
    pert_factor = settings.get("pert_factor", 3)
    deadline = (
        settings.get("deadline", "2025-12-31") or None
    )  # Convert empty string to None
    milestone = settings.get("milestone", None) or None  # Convert empty string to None
    total_items = settings.get("total_items", 0)
    estimated_items = settings.get("estimated_items", 0)
    total_points = settings.get("total_points", 0)
    estimated_points = settings.get("estimated_points", 0)
    show_points = settings.get("show_points", False)
    data_points_count = settings.get("data_points_count", 10)

    # Calculate max data points from statistics if available
    max_data_points = 52  # Default max
    if statistics and len(statistics) > 0:
        max_data_points = len(statistics)

    # Calculate dynamic marks for Data Points slider
    # 5 points: min (4), 1/4, 1/2 (middle), 3/4, max
    import math

    min_data_points = 4
    range_size = max_data_points - min_data_points
    quarter_point = math.ceil(min_data_points + range_size / 4)
    middle_point = math.ceil(min_data_points + range_size / 2)
    three_quarter_point = math.ceil(min_data_points + 3 * range_size / 4)

    data_points_marks: dict[int, dict[str, str]] = {
        min_data_points: {"label": str(min_data_points)},
        quarter_point: {"label": str(quarter_point)},
        middle_point: {"label": str(middle_point)},
        three_quarter_point: {"label": str(three_quarter_point)},
        max_data_points: {"label": str(max_data_points)},
    }

    return dbc.Offcanvas(
        [
            # Header with close button
            html.Div(
                [
                    html.H5(
                        [
                            html.I(className="fas fa-sliders-h me-2"),
                            "Parameters",
                        ],
                        className="mb-0",
                    ),
                ],
                className="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom",
            ),
            # Scrollable content area
            html.Div(
                [
                    # Timeline Section
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(className="fas fa-calendar-alt me-2"),
                                    "Timeline",
                                ],
                                className="mb-3",
                            ),
                            # Deadline
                            html.Div(
                                [
                                    html.Label(
                                        "Deadline",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dcc.DatePickerSingle(
                                        id="mobile-deadline-picker",
                                        date=deadline,
                                        display_format="YYYY-MM-DD",
                                        first_day_of_week=1,
                                        placeholder="Select deadline",
                                        min_date_allowed=datetime.now().strftime(
                                            "%Y-%m-%d"
                                        ),
                                        className="w-100 mb-3",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Milestone (optional)
                            html.Div(
                                [
                                    html.Label(
                                        "Milestone (optional)",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dcc.DatePickerSingle(
                                        id="mobile-milestone-picker",
                                        date=milestone,
                                        display_format="YYYY-MM-DD",
                                        first_day_of_week=1,
                                        placeholder="Select milestone",
                                        min_date_allowed=datetime.now().strftime(
                                            "%Y-%m-%d"
                                        ),
                                        className="w-100 mb-3",
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        className="mb-4 pb-3 border-bottom",
                    ),
                    # Confidence Window Section (formerly PERT Factor)
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Forecast Settings",
                                ],
                                className="mb-3",
                            ),
                            # Confidence Window Slider
                            html.Div(
                                [
                                    html.Label(
                                        "Confidence Window",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dcc.Slider(
                                        id="mobile-pert-factor-slider",
                                        min=3,
                                        max=12,
                                        value=pert_factor,
                                        marks={
                                            3: {"label": "3"},
                                            6: {"label": "6 (rec)"},
                                            9: {"label": "9"},
                                            12: {"label": "12"},
                                        },
                                        step=1,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": False,
                                        },
                                        className="mb-2",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Data Points Slider
                            html.Div(
                                [
                                    html.Label(
                                        "Data Points (weeks)",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dcc.Slider(
                                        id="mobile-data-points-input",
                                        min=4,  # Fixed minimum of 4 weeks for meaningful trend analysis
                                        max=max_data_points,
                                        value=data_points_count,
                                        marks=data_points_marks,  # type: ignore[arg-type]
                                        step=1,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": False,
                                        },
                                        className="mb-2",
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        className="mb-4 pb-3 border-bottom",
                    ),
                    # Scope Section
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(className="fas fa-tasks me-2"),
                                    "Work Scope",
                                ],
                                className="mb-3",
                            ),
                            # Remaining Items
                            html.Div(
                                [
                                    html.Label(
                                        "Remaining Items",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dbc.Input(
                                        id="mobile-total-items-input",
                                        type="number",
                                        value=total_items,
                                        min=0,
                                        className="mb-3",
                                        style={
                                            "minHeight": DESIGN_TOKENS["mobile"][
                                                "touchTargetMin"
                                            ]
                                        },
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Estimated Items
                            html.Div(
                                [
                                    html.Label(
                                        "Estimated Items",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dbc.Input(
                                        id="mobile-estimated-items-input",
                                        type="number",
                                        value=estimated_items,
                                        min=0,
                                        className="mb-3",
                                        style={
                                            "minHeight": DESIGN_TOKENS["mobile"][
                                                "touchTargetMin"
                                            ]
                                        },
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Points Toggle
                            html.Div(
                                [
                                    dbc.Checkbox(
                                        id="mobile-points-toggle",
                                        label="Enable Points Tracking",
                                        value=show_points,
                                        className="mb-3",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Remaining Points (if points enabled)
                            html.Div(
                                [
                                    html.Label(
                                        "Remaining Points",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dbc.Input(
                                        id="mobile-total-points-input",
                                        type="number",
                                        value=total_points,
                                        min=0,
                                        disabled=not show_points,
                                        className="mb-3",
                                        style={
                                            "minHeight": DESIGN_TOKENS["mobile"][
                                                "touchTargetMin"
                                            ]
                                        },
                                    ),
                                ],
                                className="mb-3",
                                style={"display": "block" if show_points else "none"},
                                id="mobile-total-points-container",
                            ),
                            # Estimated Points (if points enabled)
                            html.Div(
                                [
                                    html.Label(
                                        "Estimated Points",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dbc.Input(
                                        id="mobile-estimated-points-input",
                                        type="number",
                                        value=estimated_points,
                                        min=0,
                                        disabled=not show_points,
                                        className="mb-3",
                                        style={
                                            "minHeight": DESIGN_TOKENS["mobile"][
                                                "touchTargetMin"
                                            ]
                                        },
                                    ),
                                ],
                                className="mb-3",
                                style={"display": "block" if show_points else "none"},
                                id="mobile-estimated-points-container",
                            ),
                        ],
                        className="mb-4",
                    ),
                ],
                style={
                    "maxHeight": DESIGN_TOKENS["mobile"]["bottomSheetMaxHeight"],
                    "overflowY": "auto",
                },
            ),
        ],
        id="mobile-parameter-sheet",
        is_open=False,
        placement="bottom",
        backdrop=True,
        scrollable=True,
        style={
            "maxHeight": DESIGN_TOKENS["mobile"]["bottomSheetMaxHeight"],
        },
        className="mobile-parameter-sheet",
    )
