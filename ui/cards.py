"""
UI Cards Module - Dashboard Component Library

This module provides card components that make up the main UI sections
of the application. Cards are the primary building blocks for dashboard layouts.

CARD CREATION PATTERNS
=======================

This module contains multiple card creation functions. Use the following guide
to choose the appropriate function for your needs:

1. **Atomic Card Functions** (Preferred for new code):
   - `create_info_card()` - Generic info display with icon, value, unit
   - `create_unified_metric_card()` - Standardized metrics with trend, forecast
   - `create_unified_metric_row()` - Row container for metric cards

   When to use: New dashboard sections, reusable metric displays
   Benefits: Consistent styling, encapsulation, maintainability

2. **Legacy Card Functions** (Avoid for new code):
   - `create_dashboard_metrics_card()` - Old dashboard overview (pre-Feature 010)
   - `create_project_status_card()` - Legacy project status display
   - `create_project_summary_card()` - Deprecated summary layout

   When to use: Only when maintaining existing code that uses these functions
   Migration: Gradually refactor to use atomic card functions

3. **Specialized Card Functions**:
   - `create_forecast_graph_card()` - Chart container with tab navigation
   - `create_pert_analysis_card()` - PERT timeline visualization
   - `create_input_parameters_card()` - Settings form card
   - `create_statistics_data_card()` - Data table display

   When to use: Specific use cases that require custom layouts
   Pattern: Single responsibility, configurable via parameters

COMPONENT CONTRACTS
===================

All card functions follow these contracts:

**Input Parameters**:
- Required parameters first, optional with defaults after
- Use type hints for all parameters
- Provide docstrings with parameter descriptions

**Return Type**:
- Always return Dash components (dbc.Card, dbc.Row, html.Div)
- Never return None or raw data structures
- Use consistent return types across similar functions

**Styling**:
- Use `ui.style_constants` for colors, spacing, tokens
- Avoid inline styles - prefer CSS classes
- Use Bootstrap classes (dbc.*) for responsive layouts

**Error Handling**:
- Validate inputs, provide sensible defaults
- Never crash - return placeholder UI on errors
- Log errors but don't expose to user

REFACTORING GUIDELINES
=======================

When adding new card functionality:
1. Check if `create_info_card()` or `create_unified_metric_card()` can be extended
2. If not, create new function following atomic component pattern
3. Add comprehensive docstring with usage example
4. Use multi_replace_string_in_file for batch updates when consolidating duplicates

DRY Principle: If you copy card code 3+ times, extract to a helper function.
KISS Principle: Prefer simple, focused functions over monolithic card builders.

Examples:
    >>> # Good: Reusable atomic card
    >>> create_info_card(
    ...     title="Velocity",
    ...     value=8.5,
    ...     unit="items/week",
    ...     icon="tachometer-alt"
    ... )

    >>> # Bad: Inline card construction with duplicated patterns
    >>> dbc.Card([
    ...     dbc.CardHeader([html.I(className="fas fa-tachometer-alt"), "Velocity"]),
    ...     dbc.CardBody([html.H3("8.5"), html.Small("items/week")])
    ... ])
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, cast

import dash_bootstrap_components as dbc
import pandas as pd

# Third-party library imports
from dash import dcc, html

# Application imports
from configuration import COLOR_PALETTE, HELP_TEXTS
from configuration.settings import (
    CHART_HELP_TEXTS,
    PROJECT_HELP_TEXTS,
    STATISTICS_HELP_TEXTS,
)
from ui.button_utils import create_button

# Import character count components (Feature 001-add-jql-query)
from ui.components import (
    create_character_count_display,
    should_show_character_warning,
)

# Import JQL editor component (Feature 002-finish-jql-syntax)
from ui.jql_editor import create_jql_editor

# Import JIRA config button (Feature 003-jira-config-separation)
from ui.jira_config_modal import create_jira_config_button

# Import design tokens
from ui.style_constants import get_card_style, get_color, get_spacing

# Import styling functions from utility modules
from ui.styles import (
    create_card_header_with_tooltip,
    create_rhythm_text,
    create_standardized_card,
)
from ui.tooltip_utils import (
    create_dismissible_tooltip,
    create_enhanced_tooltip,
    create_expandable_tooltip,
    create_info_tooltip,
)

# Type definition for StyleCellConditional
StyleCellConditional = Dict[str, Any]


#######################################################################
# ATOMIC COMPONENT BUILDERS (Following Component Contracts)
#######################################################################


def create_info_card(
    title: str | html.Span,  # Accept both string and Dash component
    value: Any,
    icon: str = "",
    subtitle: str = "",
    variant: str = "default",
    clickable: bool = False,
    click_id: str = "",
    size: str = "md",
    **kwargs,
) -> dbc.Card:
    """
    Create information display card for metrics/statistics.

    This function follows the component builder contract specification
    in specs/006-ux-ui-redesign/contracts/component-builders.md

    Args:
        title: Card title/label (required) - can be string or Dash component for rich formatting
        value: Primary value to display (required)
        icon: Optional Font Awesome icon name (without "fa-" prefix)
        subtitle: Optional subtitle/description
        variant: Color variant - "default", "primary", "success", "warning", "danger"
        clickable: Whether card should be interactive
        click_id: ID for click callback (required if clickable=True)
        size: Card size - "sm", "md", "lg"
        **kwargs: Additional props (className, style, etc.)

    Returns:
        dbc.Card with standardized info display layout

    Raises:
        ValueError: If title or value is empty, or clickable=True but click_id empty

    Examples:
        >>> create_info_card("Days to Completion", 53, icon="calendar-check",
        ...                  subtitle="Based on current velocity", variant="primary")
        >>> create_info_card("Remaining Items", 42, icon="tasks",
        ...                  clickable=True, click_id="goto-burndown")

    ID Pattern: card-{title-slugified}[-{click_id}]

    Layout:
        - Header: icon + title
        - Body: large value + subtitle
        - Footer: optional action link (if clickable)
    """
    # Validation
    # For component titles, we can't easily validate - just check for None/empty
    title_str = str(title) if isinstance(title, str) else "component-title"
    if not title or (isinstance(title, str) and title.strip() == ""):
        raise ValueError("Title is required and cannot be empty")

    if value is None or str(value).strip() == "":
        raise ValueError("Value is required and cannot be empty")

    valid_variants = ["default", "primary", "success", "warning", "danger"]
    if variant not in valid_variants:
        raise ValueError(
            f"Invalid variant '{variant}'. Must be one of: {', '.join(valid_variants)}"
        )

    if clickable and (not click_id or click_id.strip() == ""):
        raise ValueError("click_id is required when clickable=True")

    # Generate card ID - use title_str for slugification
    title_slug = re.sub(r"[^a-z0-9]+", "-", title_str.lower()).strip("-")
    card_id = f"card-{title_slug}"
    if click_id:
        card_id += f"-{click_id}"

    # Get card styling from design tokens
    card_style = get_card_style(variant=variant, elevated=clickable)

    # Build icon if provided
    icon_element = None
    if icon:
        icon_class = f"fas fa-{icon}" if not icon.startswith("fa-") else icon
        icon_color = get_color(
            f"{variant}-500" if variant != "default" else "neutral-600"
        )
        icon_element = html.I(
            className=icon_class,
            style={
                "fontSize": "1.5rem" if size == "lg" else "1.25rem",
                "color": icon_color,
                "marginRight": get_spacing("sm"),
            },
        )

    # Build header with icon and title
    header_content = []
    if icon_element:
        header_content.append(icon_element)

    # Handle both string and component titles
    if isinstance(title, str):
        header_content.append(html.Span(title, style={"fontWeight": "600"}))
    else:
        # Title is already a component (e.g., with help icon)
        header_content.append(title)

    card_header = dbc.CardHeader(
        header_content,
        style={
            "display": "flex",
            "alignItems": "center",
            "backgroundColor": get_color("neutral-50"),
            "borderBottom": f"1px solid {get_color('neutral-200')}",
            "padding": get_spacing("sm" if size == "sm" else "md"),
        },
    )

    # Build body with value and subtitle
    value_style = {
        "fontSize": "2.5rem" if size == "lg" else "2rem" if size == "md" else "1.5rem",
        "fontWeight": "700",
        "color": get_color(f"{variant}-600" if variant != "default" else "neutral-900"),
        "lineHeight": "1.2",
        "marginBottom": get_spacing("xs") if subtitle else "0",
    }

    body_content = [html.Div(str(value), style=value_style)]

    if subtitle:
        subtitle_style = {
            "fontSize": "0.875rem",
            "color": get_color("neutral-600"),
            "marginTop": get_spacing("xs"),
        }
        body_content.append(html.Div(subtitle, style=subtitle_style))

    card_body = dbc.CardBody(
        body_content,
        style={
            "padding": get_spacing("md" if size == "lg" else "sm"),
            "textAlign": "center",
        },
    )

    # Build optional footer for clickable cards
    card_footer = None
    if clickable:
        footer_link = html.A(
            [
                "View Details ",
                html.I(className="fas fa-arrow-right", style={"marginLeft": "0.25rem"}),
            ],
            style={
                "fontSize": "0.875rem",
                "color": get_color("primary-500"),
                "textDecoration": "none",
                "fontWeight": "500",
            },
        )
        card_footer = dbc.CardFooter(
            footer_link,
            style={
                "backgroundColor": get_color("neutral-50"),
                "borderTop": f"1px solid {get_color('neutral-200')}",
                "padding": get_spacing("sm"),
                "textAlign": "center",
            },
        )

    # Merge custom styles with design token styles
    custom_style = kwargs.pop("style", {})
    final_style = {**card_style, **custom_style}

    # Add hover effect for clickable cards
    if clickable:
        final_style.update(
            {
                "cursor": "pointer",
                "transition": "transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
            }
        )
        # Add className for hover effect via CSS
        custom_class = kwargs.pop("className", "")
        kwargs["className"] = f"{custom_class} card-clickable".strip()

    # Build card
    card_components = [card_header, card_body]
    if card_footer:
        card_components.append(card_footer)

    return dbc.Card(
        card_components,
        id=card_id,
        style=final_style,
        **kwargs,
    )


def create_dashboard_metrics_card(
    metrics: dict,
    card_type: str,
    variant: str = "default",
    **kwargs,
) -> dbc.Card:
    """
    Create specialized dashboard metrics card with enhanced visualization.

    This function supports User Story 2: Dashboard as Primary Landing View.
    It creates metric cards specifically designed for the Dashboard tab with
    appropriate icons, colors, and formatting for each metric type.

    User Story 6: Contextual Help System - Adds help icons to metric cards.

    Args:
        metrics: DashboardMetrics dictionary from calculate_dashboard_metrics()
        card_type: Type of metric card - "forecast", "velocity", "remaining", "pert"
        variant: Color variant override (auto-selected based on card_type if "default")
        **kwargs: Additional props passed to dbc.Card

    Returns:
        dbc.Card: Formatted dashboard metrics card with help icon

    Raises:
        ValueError: If card_type is invalid

    Example:
        >>> metrics = calculate_dashboard_metrics(stats, settings)
        >>> card = create_dashboard_metrics_card(metrics, "forecast")

    Card Types:
        - "forecast": Completion forecast with confidence
        - "velocity": Current velocity trend
        - "remaining": Remaining work (items/points)
        - "pert": PERT timeline estimates
    """
    # Import help system function for tooltips
    from ui.help_system import create_dashboard_metric_tooltip

    # Validate card type
    valid_types = ["forecast", "velocity", "remaining", "pert"]
    if card_type not in valid_types:
        raise ValueError(
            f"Invalid card_type '{card_type}'. Must be one of: {', '.join(valid_types)}"
        )

    # Configure card based on type
    # Map card_type to help content key
    card_configs = {
        "forecast": {
            "title": "Completion Forecast",
            "icon": "calendar-check",
            "variant": "default",
            "value_field": "days_to_completion",
            "value_suffix": " days",
            "subtitle_template": "{completion_percentage}% complete • {completion_confidence}% confidence",
            "help_key": "completion_forecast",
        },
        "velocity": {
            "title": "Current Velocity",
            "icon": "tachometer-alt",
            "variant": "default",
            "value_field": "current_velocity_items",
            "value_suffix": " items/week",
            "subtitle_template": "{current_velocity_points} pts/week • {velocity_trend}",
            "help_key": "velocity_trend",
        },
        "remaining": {
            "title": "Remaining Work",
            "icon": "tasks",
            "variant": "default",
            "value_field": "remaining_items",
            "value_suffix": " items",
            "subtitle_template": "{remaining_points} story points remaining",
            "help_key": "remaining_work",
        },
        "pert": {
            "title": "Timeline Range",
            "icon": "clock",
            "variant": "default",
            "value_field": "days_to_deadline",
            "value_suffix": " days to deadline",
            "subtitle_template": "Forecast: {days_to_completion} days",
            "help_key": "pert_expected",
        },
    }

    config = card_configs[card_type]

    # Override variant if specified
    if variant != "default":
        config["variant"] = variant

    # Extract value
    value = metrics.get(config["value_field"], "N/A")
    if value is not None and value != "N/A":
        value = f"{value}{config['value_suffix']}"
    else:
        value = "N/A"

    # Format subtitle with metrics
    try:
        subtitle = config["subtitle_template"].format(**metrics)
    except (KeyError, ValueError):
        subtitle = ""

    # Create title with help icon
    title_with_help = html.Span(
        [
            html.Span(config["title"]),
            html.Span(
                create_dashboard_metric_tooltip(config["help_key"]),
                style={"marginLeft": "0.5rem"},
            ),
        ],
        style={"display": "flex", "alignItems": "center"},
    )

    # Extract 'id' from kwargs to avoid conflict with create_info_card's auto-generated ID
    # We'll let create_info_card generate the ID based on the title
    # The dashboard callback uses container IDs, not the card IDs directly
    kwargs.pop("id", None)  # Remove any id from kwargs

    # Create card using create_info_card
    return create_info_card(
        title=title_with_help,
        value=value,
        icon=config["icon"],
        subtitle=subtitle,
        variant=config["variant"],
        **kwargs,
    )


#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _get_default_data_source():
    """
    Determine the default data source based on persisted settings.

    Returns:
        str: "JIRA" (default) or "CSV" based on last_used_data_source setting
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        # Use persisted value, default to JIRA (swapped order)
        data_source = app_settings.get("last_used_data_source", "JIRA")
        # Return JIRA if the value is empty or None
        return data_source if data_source else "JIRA"
    except (ImportError, Exception):
        return "JIRA"  # Default to JIRA if import fails or any other error


def _get_default_jql_query():
    """
    Get the default JQL query from app settings.

    Returns:
        str: JQL query from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jql_query", "project = JRASERVER")
    except ImportError:
        return "project = JRASERVER"


def _get_default_jql_profile_id():
    """
    Get the active JQL profile ID from app settings.

    Returns:
        str: Profile ID from settings or empty string if none
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("active_jql_profile_id", "")
    except (ImportError, Exception):
        return ""


# Legacy JIRA helper functions removed - JIRA configuration is now managed
# via the JIRA Configuration modal (jira_config structure in profile.json)


def _get_default_jira_story_points_field():
    """
    Get the default JIRA story points field from app settings.

    Returns:
        str: Story points field from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_story_points_field", "")
    except ImportError:
        return ""


def _get_default_jira_cache_max_size():
    """
    Get the default JIRA cache max size from app settings.

    Returns:
        int: Cache max size from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_cache_max_size", 100)
    except ImportError:
        return 100


def _get_default_jira_max_results():
    """
    Get the default JIRA max results from app settings.

    Returns:
        int: Max results from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_max_results", 1000)
    except ImportError:
        return 1000


def _get_query_profile_options():
    """
    Get options for the query profile dropdown.

    Returns:
        List of option dictionaries for the dropdown in format [{"label": str, "value": str}]
    """
    try:
        from data.jira_query_manager import load_query_profiles

        profiles = load_query_profiles()
        options = []

        # Add saved query profiles only (no default profiles)
        for profile in profiles:
            label = profile["name"]
            if profile.get("is_default", False):
                label += " [Default]"  # Add indicator for default
            options.append(
                {
                    "label": label,
                    "value": profile["id"],
                }
            )

        # Don't add "New Query" option - keep dropdown for saved queries only
        return options

    except (ImportError, Exception):
        # Return empty list if query manager fails
        return []


#######################################################################
# CARD COMPONENTS
#######################################################################


def create_forecast_graph_card():
    """
    Create the forecast graph card component with customized download filename.

    Returns:
        Dash Card component with the forecast graph
    """
    # Generate the current date for the filename
    current_date = datetime.now().strftime("%Y%m%d")
    default_filename = f"burndown_forecast_{current_date}"

    # Create the card header with tooltip and Phase 9.2 Progressive Disclosure help button
    header_content = create_card_header_with_tooltip(
        "Forecast Graph",
        tooltip_id="forecast-graph",
        tooltip_text=HELP_TEXTS["forecast_explanation"],
        help_key="forecast_graph_overview",
        help_category="forecast",
    )

    # Create the card body content
    body_content = dcc.Graph(
        id="forecast-graph",
        style={
            "height": "700px"
        },  # Updated from 650px to match the height in apply_layout_settings
        config={
            # Only specify the filename, let Plotly handle the rest of the export settings
            "toImageButtonOptions": {
                "filename": default_filename,
            },
        },
    )

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        body_className="p-2",  # Less padding to maximize graph space
        shadow="sm",
    )


def create_forecast_info_card():
    """
    Create the forecast methodology information card component with concise explanation.

    Returns:
        Dash Card component with concise forecast methodology explanation
    """
    # Generate a unique ID for this collapse component
    collapse_id = "forecast-info-collapse"

    # Create the card body content with optimized layout
    body_content = html.Div(
        [
            # Concise introduction paragraph with enhanced PERT methodology tooltip
            create_rhythm_text(
                [
                    html.Strong("PERT Forecast: "),
                    "Estimates based on optimistic, most likely, and pessimistic scenarios from your historical data.",
                    create_expandable_tooltip(
                        id_suffix="pert-methodology-main",
                        summary_text="PERT uses 3-point estimation for realistic forecasts",
                        detailed_text=CHART_HELP_TEXTS["pert_forecast_methodology"],
                        variant="primary",
                        placement="right",
                    ),
                ],
                element_type="paragraph",
            ),
            # Compact list with less styling and more concise descriptions
            html.Div(
                className="row g-2 mb-2",
                children=[
                    html.Div(
                        className="col-12 col-md-6",
                        children=html.Div(
                            className="border rounded p-2",
                            children=[
                                html.Div(
                                    [
                                        html.Strong("Line Colors:"),
                                        create_dismissible_tooltip(
                                            id_suffix="chart-legend-colors",
                                            help_text=CHART_HELP_TEXTS[
                                                "chart_legend_explained"
                                            ],
                                            variant="info",
                                            placement="top",
                                        ),
                                    ]
                                ),
                                html.Ul(
                                    [
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Blue",
                                                    style={
                                                        "color": COLOR_PALETTE["items"],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Orange",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "points"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Most likely",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Teal",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "optimistic"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Gold",
                                                    style={  # Fixed double curly braces to single
                                                        "color": "rgb(184, 134, 11)",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Optimistic",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Indigo",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "pessimistic"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Brown",
                                                    style={
                                                        "color": "rgb(165, 42, 42)",
                                                    },
                                                ),
                                                ": Pessimistic",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Red",
                                                    style={
                                                        "color": "red",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Deadline",
                                            ]
                                        ),
                                    ],
                                    className="mb-0 ps-3",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                        ),
                    ),
                    html.Div(
                        className="col-12 col-md-6",
                        children=html.Div(
                            className="border rounded p-2",
                            children=[
                                html.Div(
                                    [
                                        html.Strong("Reading Guide:"),
                                        create_enhanced_tooltip(
                                            id_suffix="reading-guide-enhanced",
                                            help_text=CHART_HELP_TEXTS[
                                                "historical_data_influence"
                                            ],
                                            variant="success",
                                            placement="left",
                                            smart_positioning=True,
                                            icon_class="fas fa-chart-line",
                                        ),
                                    ]
                                ),
                                html.Ul(
                                    [
                                        html.Li(
                                            [
                                                "Solid lines: Historical data ",
                                                create_info_tooltip(
                                                    CHART_HELP_TEXTS[
                                                        "chart_legend_explained"
                                                    ],
                                                    "Visual legend and line type meanings",
                                                ),
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                "Dashed/dotted: Forecasts ",
                                                create_info_tooltip(
                                                    CHART_HELP_TEXTS[
                                                        "forecast_confidence_bands"
                                                    ],
                                                    "Understanding forecast uncertainty ranges",
                                                ),
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                "Scope changes: Chart annotations ",
                                                create_info_tooltip(
                                                    CHART_HELP_TEXTS[
                                                        "scope_change_indicators"
                                                    ],
                                                    "How scope changes are shown on the main chart",
                                                ),
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                "Data points: Accuracy factor ",
                                                create_info_tooltip(
                                                    CHART_HELP_TEXTS[
                                                        "data_points_precision"
                                                    ],
                                                    "How number of data points affects forecast precision",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="mb-0 ps-3",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
        style={"textAlign": "left"},
    )

    # Return a card with collapsible body content
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="mobile-touch-target-sm border-0",
                                    ),
                                    create_info_tooltip(
                                        "forecast-info",
                                        "How to interpret the forecast graph.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(body_content, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",  # Changed from "mb-3 shadow-sm mt-3" to "my-2" for consistent 8px margins
    )


def create_pert_analysis_card():
    """
    Create the PERT analysis card component.

    Returns:
        Dash Card component for PERT analysis
    """
    # Create the card header with tooltip and Phase 9.2 Progressive Disclosure help button
    header_content = create_card_header_with_tooltip(
        "PERT Analysis",
        tooltip_id="pert-info",
        tooltip_text="PERT (Program Evaluation and Review Technique) estimates project completion time based on optimistic, pessimistic, and most likely scenarios.",
        help_key="pert_analysis_detailed",
        help_category="forecast",
    )

    # Create the card body content
    body_content = html.Div(id="pert-info-container", className="text-center")

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        className="mb-3 h-100",
        body_className="p-3",
        shadow="sm",
    )


def create_input_parameters_card(
    current_settings, avg_points_per_item, estimated_total_points
):
    """
    Create the data import configuration card.

    Note: Project Timeline and Remaining Work Scope parameters have been moved to the
    Parameter Panel (collapsible top section) for better UX.

    Args:
        current_settings: Dictionary with current application settings
        avg_points_per_item: Current average points per item (unused but kept for compatibility)
        estimated_total_points: Estimated total points (unused but kept for compatibility)

    Returns:
        Dash Card component for data import configuration
    """
    # Create the card header
    header_content = create_card_header_with_tooltip(
        "Data Import Configuration",
        tooltip_id="data-import-config",
        tooltip_text="Configure data sources and import settings for your project.",
        help_key="data_import_guide",
        help_category="data",
    )

    # Create the card body content - only Data Import Configuration
    body_content = [
        # Data Source Selection
        html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-database me-2",
                            style={"color": COLOR_PALETTE["optimistic"]},
                        ),
                        "Data Source",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Data Source:",
                                        create_info_tooltip(
                                            "data-source",
                                            "Choose between JIRA API (recommended) or JSON/CSV file upload.",
                                        ),
                                    ],
                                    className="fw-medium mb-2",
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
                            width=12,
                        ),
                    ],
                ),
                # Data Export Action
                html.Hr(className="my-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    "Export Options:", className="fw-medium mb-2"
                                ),
                                html.Div(
                                    [
                                        create_button(
                                            text="Export Data",
                                            id="export-project-data-button",
                                            variant="secondary",
                                            icon_class="fas fa-file-export",
                                        ),
                                        html.Small(
                                            "Export complete project data as JSON",
                                            className="text-muted mt-1 d-block",
                                        ),
                                        html.Div(
                                            dcc.Download(
                                                id="export-project-data-download"
                                            )
                                        ),
                                    ]
                                ),
                            ],
                            width=12,
                        ),
                    ],
                ),
            ],
            className="mb-4 p-3 bg-light rounded-3",
        ),
        # Data Import Configuration
        html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-upload me-2",
                            style={"color": COLOR_PALETTE["items"]},
                        ),
                        "Data Import Configuration",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
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
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Upload CSV/JSON File:",
                                            className="fw-medium",
                                        ),
                                        dcc.Upload(
                                            id="upload-data",
                                            children=html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-cloud-upload-alt fa-2x mb-2"
                                                    ),
                                                    html.Br(),
                                                    "Drag and Drop or Click to Select",
                                                ],
                                                className="d-flex flex-column justify-content-center align-items-center h-100",
                                                style={"lineHeight": "1.2"},
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
                                                "transition": "all 0.2s ease",
                                            },
                                            multiple=False,
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                    ],
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
                        # Configure JIRA Button
                        create_jira_config_button(),
                        # JIRA Configuration Status Indicator
                        html.Div(
                            id="jira-config-status-indicator",
                            className="mt-2 mb-3",
                            children=[],
                        ),
                        # JQL Query Management Section
                        html.Div(
                            [
                                html.H6(
                                    [
                                        html.I(className="fas fa-code me-2"),
                                        "JQL Query Management",
                                    ],
                                    className="mb-3 text-primary border-bottom pb-2",
                                ),
                                # JQL Query Input
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "JQL Query:", className="fw-medium"
                                                ),
                                                create_jql_editor(
                                                    editor_id="jira-jql-query",
                                                    initial_value=_get_default_jql_query(),
                                                    placeholder="project = MYPROJECT AND created >= startOfYear()",
                                                    rows=1,
                                                ),
                                                html.Div(
                                                    id="jira-jql-character-count-container",
                                                    children=[
                                                        create_character_count_display(
                                                            count=len(
                                                                _get_default_jql_query()
                                                                or ""
                                                            ),
                                                            warning=should_show_character_warning(
                                                                _get_default_jql_query()
                                                            ),
                                                        )
                                                    ],
                                                    className="mb-2",
                                                ),
                                                html.Small(
                                                    "Write your JQL query here, then use the buttons below to save or manage it.",
                                                    className="text-muted",
                                                ),
                                            ],
                                            width=12,
                                            className="mb-3",
                                        ),
                                    ],
                                ),
                                # Query Actions
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
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
                                                        html.Div(
                                                            [
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
                                                                    },
                                                                ),
                                                            ],
                                                            className="d-inline-block me-2 mb-2",
                                                        ),
                                                        create_button(
                                                            text="Clear",
                                                            id="clear-jql-query-button",
                                                            variant="outline-secondary",
                                                            icon_class="fas fa-eraser",
                                                            size="sm",
                                                            className="me-2 mb-2",
                                                        ),
                                                    ],
                                                    className="d-flex flex-wrap justify-content-start",
                                                ),
                                            ],
                                            width=12,
                                            className="mb-3",
                                        ),
                                    ],
                                ),
                                # Feedback section
                                html.Div(
                                    id="jira-jql-query-save-status",
                                    className="text-center mt-2",
                                    children=[],
                                ),
                            ],
                            className="p-3 bg-light rounded mb-3",
                        ),
                        # Action Buttons
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                create_button(
                                                    text="Update Data",
                                                    id="update-data-unified",
                                                    variant="primary",
                                                    icon_class="fas fa-sync-alt",
                                                    className="mb-2",
                                                ),
                                                html.Small(
                                                    "Fetches JIRA data and automatically calculates project scope",
                                                    className="text-muted d-block",
                                                ),
                                            ]
                                        ),
                                    ],
                                    width=12,
                                    className="text-center mb-3",
                                ),
                            ],
                        ),
                        # Status indicator
                        html.Div(
                            id="jira-cache-status",
                            className="text-center text-muted small",
                            children="Ready to fetch JIRA data",
                        ),
                    ],
                ),
            ],
            className="mb-4 p-3 bg-light rounded-3",
        ),
    ]

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        className="mb-3 h-100 shadow-sm",
        body_className="p-3",
        shadow="sm",
    )


def create_statistics_data_card(current_statistics):
    """
    Create the statistics data card component with standardized table styling.

    Args:
        current_statistics: List of dictionaries containing current statistics data

    Returns:
        Dash Card component for statistics data
    """
    import dash_bootstrap_components as dbc
    import numpy as np
    import pandas as pd
    from dash import dash_table, html

    from ui.styles import NEUTRAL_COLORS, get_vertical_rhythm

    # Create the card header with tooltip and Phase 9.2 Progressive Disclosure help button
    header_content = create_card_header_with_tooltip(
        "Weekly Progress Data",
        tooltip_id="statistics-data",
        tooltip_text="Weekly tracking of completed and newly created work items and story points. Each Monday date represents work done during that week (Monday through Sunday). This data drives all velocity calculations and forecasting.",
        help_key="weekly_progress_data_explanation",
        help_category="statistics",
    )

    # Convert to DataFrame for automatic column type detection
    statistics_df = pd.DataFrame(current_statistics)

    # Ensure required columns exist in the DataFrame
    required_columns = [
        "date",
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    for col in required_columns:
        if col not in statistics_df.columns:
            statistics_df[col] = 0  # Add missing columns with default values

    # Function to create a responsive table wrapper
    def create_responsive_table_wrapper(table_component, max_height=None, className=""):
        """
        Create a mobile-responsive wrapper for tables that handles overflow with scrolling.
        """
        container_style = {
            "overflowX": "auto",
            "width": "100%",
            "WebkitOverflowScrolling": "touch",  # Smooth scrolling on iOS
        }

        if max_height:
            container_style["maxHeight"] = max_height
            container_style["overflowY"] = "auto"

        return html.Div(
            table_component,
            className=f"table-responsive {className}",
            style=container_style,
        )

    # Function to detect appropriate column alignment based on data type
    def detect_column_alignment(dataframe, column_name):
        """
        Automatically detect appropriate alignment for a column based on its data type.
        """
        if column_name not in dataframe.columns:
            return "left"  # Default to left alignment

        # Get data type of the column
        dtype = dataframe[column_name].dtype

        # Check for date-related columns by name
        date_related_names = ["date", "time", "day", "month", "year", "deadline"]
        if any(date_term in column_name.lower() for date_term in date_related_names):
            return "center"

        # Check for numeric types
        if (
            pd.api.types.is_numeric_dtype(dtype)
            or dtype == np.dtype("float64")
            or dtype == np.dtype("int64")
        ):
            return "right"

        # Check for boolean types
        if pd.api.types.is_bool_dtype(dtype):
            return "center"

        # Default to left alignment for text and other types
        return "left"

    # Generate a dictionary of optimal column alignments for all columns
    def generate_column_alignments(dataframe):
        """
        Generate a dictionary of optimal column alignments for all columns in a DataFrame.
        """
        alignments = {}
        for column in dataframe.columns:
            alignments[column] = detect_column_alignment(dataframe, column)
        return alignments

    # Create standardized styling for data tables
    def create_standardized_table_style(stripe_color=None, mobile_optimized=True):
        """
        Create standardized styling for data tables with responsive behavior.
        """
        if stripe_color is None:
            stripe_color = NEUTRAL_COLORS.get("gray-100", "#f8f9fa")

        # Use vertical rhythm system for consistent table spacing
        cell_padding_v = "0.5rem"
        cell_padding_h = "0.75rem"

        style_dict = {
            "style_table": {
                "overflowX": "auto",
                "borderRadius": "4px",
                "border": f"1px solid {NEUTRAL_COLORS.get('gray-300', '#dee2e6')}",
                "marginBottom": get_vertical_rhythm("section"),
                "WebkitOverflowScrolling": "touch",  # Improved scroll on iOS
            },
            "style_header": {
                "backgroundColor": NEUTRAL_COLORS.get("gray-200", "#e9ecef"),
                "fontWeight": "bold",
                "textAlign": "center",
                "padding": f"{cell_padding_v} {cell_padding_h}",
                "borderBottom": f"2px solid {NEUTRAL_COLORS.get('gray-400', '#ced4da')}",
            },
            "style_cell": {
                "padding": f"{cell_padding_v} {cell_padding_h}",
                "fontFamily": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
                "textAlign": "left",
                "whiteSpace": "normal",
                "height": "auto",
                "lineHeight": "1.5",
                "minWidth": "100px",
                "maxWidth": "500px",
            },
            "style_data": {
                "border": f"1px solid {NEUTRAL_COLORS.get('gray-200', '#e9ecef')}",
            },
            "style_data_conditional": [
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": stripe_color,
                }
            ],
        }

        # Add mobile optimizations if requested
        if mobile_optimized:
            # Add mobile-specific styling for better touch interactions
            style_dict["css"] = [
                # Optimize for touch scrolling
                {
                    "selector": ".dash-spreadsheet-container",
                    "rule": "touch-action: pan-y; -webkit-overflow-scrolling: touch;",
                },
                # Ensure text wraps on small screens
                {
                    "selector": ".dash-cell-value",
                    "rule": "white-space: normal !important; word-break: break-word !important;",
                },
                # Improve filter icon appearance
                {
                    "selector": ".dash-filter",
                    "rule": "padding: 2px 5px; border-radius: 3px; background-color: rgba(0, 0, 0, 0.05);",
                },
                # Hide case-sensitive toggle (simplify filtering UI)
                {"selector": ".dash-filter--case", "rule": "display: none;"},
                # Add indicator to show field is editable on hover
                {
                    "selector": "td.cell--editable:hover",
                    "rule": "background-color: rgba(13, 110, 253, 0.08) !important;",
                },
                # Improve column sorting indication
                {
                    "selector": ".dash-header-cell .column-header--sort",
                    "rule": "opacity: 1 !important; color: #0d6efd !important;",
                },
                # Add better focus indication for keyboard navigation
                {
                    "selector": ".dash-cell-value:focus",
                    "rule": "outline: none !important; box-shadow: inset 0 0 0 2px #0d6efd !important;",
                },
            ]

        return style_dict

    # Create a direct implementation of data table with enhanced responsive features
    def create_enhanced_data_table(
        data,
        columns,
        id,
        editable=False,
        row_selectable=False,
        page_size=None,
        include_pagination=False,
        sort_action=None,
        filter_action=None,
        column_alignments=None,
        sort_by=None,
        mobile_responsive=True,
        priority_columns=None,
    ):
        """
        Create a data table with standardized styling and enhanced mobile responsiveness.
        """
        # Get base styling
        table_style = create_standardized_table_style(
            mobile_optimized=mobile_responsive
        )  # Apply column-specific alignments if provided
        style_cell_conditional: List[StyleCellConditional] = []
        if column_alignments:
            style_cell_conditional = [
                cast(
                    StyleCellConditional,
                    {"if": {"column_id": col_id}, "textAlign": alignment},
                )
                for col_id, alignment in column_alignments.items()
            ]  # Add mobile optimization for columns if needed
        if mobile_responsive and priority_columns:
            # Create conditional styling for non-priority columns on mobile
            for col in columns:
                if col["id"] not in priority_columns:
                    style_cell_conditional.append(
                        cast(
                            StyleCellConditional,
                            {
                                "if": {"column_id": col["id"]},
                                "className": "mobile-hidden",
                                "media": "screen and (max-width: 767px)",
                            },
                        )
                    )

        # Add highlighting for editable cells
        if editable:
            style_data_conditional = table_style["style_data_conditional"] + [
                {
                    "if": {"column_editable": True},
                    "backgroundColor": "rgba(0, 123, 255, 0.05)",
                    "cursor": "pointer",
                },
                # Add more visual feedback for selected cell
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "rgba(13, 110, 253, 0.15)",
                    "border": "1px solid #0d6efd",
                },
                # Show validation indicators for numeric columns
                *[
                    {
                        "if": {
                            "column_id": col["id"],
                            "filter_query": f"{{{col['id']}}} < 0",
                        },
                        "backgroundColor": "rgba(220, 53, 69, 0.1)",
                        "color": "#dc3545",
                    }
                    for col in columns
                    if col.get("type") == "numeric"
                ],
            ]
        else:
            style_data_conditional = table_style["style_data_conditional"]

        # Set up pagination properties
        if include_pagination:
            pagination_settings = {
                "page_action": "native",
                "page_current": 0,
                "page_size": page_size if page_size else 10,
                "page_count": None,
            }
        else:
            pagination_settings = {}  # Create the table with enhanced styling and responsive features
        return dash_table.DataTable(
            id=id,
            data=data,
            columns=columns,
            editable=editable,
            row_selectable="multi" if row_selectable else None,
            row_deletable=editable,
            sort_action=sort_action,
            filter_action=filter_action,
            sort_by=sort_by,  # Set default sorting
            style_table=table_style["style_table"],
            style_header=table_style["style_header"],
            style_cell=table_style["style_cell"],
            style_cell_conditional=style_cell_conditional,  # type: ignore # Ignore type error for style_cell_conditional
            style_data=table_style["style_data"],
            style_data_conditional=style_data_conditional,
            css=table_style.get("css", []),
            tooltip_delay=0,
            tooltip_duration=None,
            **pagination_settings,
        )

    # Define standard column configuration to ensure consistent columns
    columns = [
        {
            "name": "Week Start (Monday)",
            "id": "date",
            "type": "text",
        },
        {
            "name": "Items Done This Week",
            "id": "completed_items",
            "type": "numeric",
        },
        {
            "name": "Points Done This Week",
            "id": "completed_points",
            "type": "numeric",
        },
        {
            "name": "New Items Added",
            "id": "created_items",
            "type": "numeric",
        },
        {
            "name": "New Points Added",
            "id": "created_points",
            "type": "numeric",
        },
    ]

    # Set column alignments based on data type
    column_alignments = {
        "date": "center",
        "completed_items": "right",
        "completed_points": "right",
        "created_items": "right",
        "created_points": "right",
    }

    # Create the enhanced table with consistent columns
    statistics_table = create_enhanced_data_table(
        data=statistics_df.to_dict("records"),
        columns=columns,
        id="statistics-table",
        editable=True,
        row_selectable=False,
        page_size=10,
        include_pagination=True,
        sort_action="native",
        filter_action="native",
        column_alignments=column_alignments,
        sort_by=[{"column_id": "date", "direction": "desc"}],
    )

    # Create help text for data input
    help_text = html.Div(
        [
            html.Small(
                [
                    html.I(className="fas fa-info-circle me-1 text-info"),
                    "Enter weekly data for work completed and created. Each Monday date represents work done during that full week (Monday through Sunday, inclusive).",
                ],
                className="text-muted",
            ),
            html.Small(
                [
                    html.I(className="fas fa-calendar-week me-1 text-info"),
                    html.Strong("Weekly Timeboxes: "),
                    "Monday date = work completed/created from that Monday through the following Sunday (7-day period, inclusive). Use the ",
                    html.Code("Add Row"),
                    " button to add new weekly entries.",
                ],
                className="text-muted d-block mt-1",
            ),
            html.Small(
                [
                    html.I(className="fas fa-plus-circle me-1 text-info"),
                    html.Strong("Scope Tracking: "),
                    "Include both completed work (finished items/points) and created work (new items/points added to backlog) to track scope changes.",
                ],
                className="text-muted d-block mt-1",
            ),
            html.Small(
                [
                    html.I(className="fas fa-calendar-alt me-1 text-info"),
                    html.Strong("Date Format: "),
                    "Always use Monday dates in ",
                    html.Code("YYYY-MM-DD"),
                    " format (e.g., 2025-09-22 for the week of Sept 22-28, inclusive).",
                ],
                className="text-muted d-block mt-1",
            ),
        ],
        className="mb-3",
    )

    # Wrap the table in a responsive container
    responsive_table = create_responsive_table_wrapper(statistics_table)

    # Create column explanations section
    column_explanations = html.Div(
        [
            # Collapsible button for column explanations
            dbc.Button(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Column Explanations",
                ],
                id="column-explanations-toggle",
                color="info",
                outline=True,
                size="sm",
                className="mb-2",
            ),
            # Collapsible content
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Data Column Definitions", className="mb-3"),
                            html.Div(
                                [
                                    # Week Start (Monday) explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-calendar-week me-1 text-primary"
                                                    ),
                                                    "Week Start (Monday):",
                                                ]
                                            ),
                                            html.Span(
                                                " Data collection date (weekly snapshots). Each Monday represents work done during that full week (Monday-Sunday).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "date-field-column",
                                                STATISTICS_HELP_TEXTS["date_field"],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # Items Done This Week explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-check-circle me-1 text-success"
                                                    ),
                                                    "Items Done This Week:",
                                                ]
                                            ),
                                            html.Span(
                                                " Number of work items (stories, tasks, tickets) completed during this weekly period.",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "completed-items-column",
                                                STATISTICS_HELP_TEXTS[
                                                    "completed_items"
                                                ],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # Points Done This Week explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-star me-1 text-warning"
                                                    ),
                                                    "Points Done This Week:",
                                                ]
                                            ),
                                            html.Span(
                                                " Story points or effort units completed during this weekly period.",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "completed-points-column",
                                                STATISTICS_HELP_TEXTS[
                                                    "completed_points"
                                                ],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # New Items Added explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-plus-circle me-1 text-info"
                                                    ),
                                                    "New Items Added:",
                                                ]
                                            ),
                                            html.Span(
                                                " Number of new work items added to the project during this period (scope growth).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "created-items-column",
                                                STATISTICS_HELP_TEXTS["created_items"],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # New Points Added explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-plus-square me-1 text-secondary"
                                                    ),
                                                    "New Points Added:",
                                                ]
                                            ),
                                            html.Span(
                                                " Story points for new work items added during this period (scope change impact).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "created-points-column",
                                                STATISTICS_HELP_TEXTS["created_points"],
                                            ),
                                        ],
                                        className="mb-0",
                                    ),
                                ],
                                className="small",
                            ),
                        ]
                    ),
                    color="light",
                ),
                id="column-explanations-collapse",
                is_open=False,
            ),
        ],
        className="mb-3",
    )

    # Create the card body content
    body_content = [
        # Add help text at the top
        help_text,
        # Add column explanations section
        column_explanations,
        # Add space before table
        html.Div(className="mb-3"),
        # Add the responsive table
        responsive_table,
        # Create a row for table actions with better styling
        html.Div(
            [
                # Button for adding rows with tooltip
                html.Div(
                    [
                        create_button(
                            text="Add Row",
                            id="add-row-button",
                            variant="primary",
                            icon_class="fas fa-plus",
                        ),
                        dbc.Tooltip(
                            "Adds a new weekly entry with Monday date 7 days after the most recent entry. Enter work completed and created during that week (Monday-Sunday).",
                            target="add-row-button",
                            placement="top",
                        ),
                    ],
                    className="me-2 mb-2 mb-sm-0",  # Add right margin and bottom margin on mobile
                    style={"display": "inline-block"},
                ),
                # Button to clear filters - resized and repositioned
                html.Div(
                    create_button(
                        text="Clear Filters",
                        id="clear-filters-button",
                        variant="outline-secondary",
                        icon_class="fas fa-filter",
                    ),
                    className="me-2 mb-2 mb-sm-0",  # Add right margin and bottom margin on mobile
                    style={"display": "inline-block"},
                ),
            ],
            className="d-flex flex-wrap justify-content-center align-items-center mt-4",
            # Use flex-wrap to allow buttons to wrap on mobile
        ),
    ]

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        body_className="p-3",
        shadow="sm",
    )


def create_project_status_card(statistics_df, settings):
    """
    Create a comprehensive project status card with metrics and indicators.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings

    Returns:
        A Dash card component for project status summary
    """
    try:
        import dash_bootstrap_components as dbc
        import pandas as pd
        from dash import html

        # Extract key metrics from settings (these represent remaining work)
        remaining_items = settings.get("total_items", 0)
        remaining_points = settings.get("total_points", 0)

        # Calculate completed items and points from statistics
        completed_items = (
            int(statistics_df["completed_items"].sum())
            if not statistics_df.empty
            else 0
        )
        completed_points = (
            int(statistics_df["completed_points"].sum())
            if not statistics_df.empty
            else 0
        )

        # Calculate true project totals (completed + remaining)
        total_items = remaining_items + completed_items
        total_points = round(
            remaining_points + completed_points
        )  # Round to nearest integer
        remaining_points = round(
            remaining_points
        )  # Round remaining points to nearest integer

        # Calculate percentages based on true project totals
        items_percentage = (
            int((completed_items / total_items) * 100) if total_items > 0 else 0
        )
        points_percentage = (
            int((completed_points / total_points) * 100) if total_points > 0 else 0
        )

        # Calculate average weekly velocity and coefficient of variation (last 10 weeks)
        # Create a copy of the DataFrame to avoid SettingWithCopyWarning
        recent_df = statistics_df.copy() if not statistics_df.empty else pd.DataFrame()

        # Default values if no data is available
        avg_weekly_items = 0
        avg_weekly_points = 0
        stability_status = "Unknown"
        stability_color = "secondary"
        stability_icon = "fa-question-circle"

        # Convert to datetime to ensure proper week grouping
        if not recent_df.empty:
            # Use proper pandas assignment with .loc to avoid SettingWithCopyWarning
            recent_df.loc[:, "date"] = pd.to_datetime(recent_df["date"])

            # Add week and year columns
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year

            # Group by week to get weekly data
            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"completed_items": "sum", "completed_points": "sum"})
                .reset_index()
                .tail(10)  # Consider only the last 10 weeks
            )

            # Calculate average weekly velocity
            avg_weekly_items = weekly_data["completed_items"].mean()
            avg_weekly_points = weekly_data["completed_points"].mean()

            # Calculate standard deviation for coefficient of variation
            std_weekly_items = weekly_data["completed_items"].std()
            std_weekly_points = weekly_data["completed_points"].std()

            # Calculate coefficient of variation (CV = std/mean)
            cv_items = (
                (std_weekly_items / avg_weekly_items * 100)
                if avg_weekly_items > 0
                else 0
            )
            cv_points = (
                (std_weekly_points / avg_weekly_points * 100)
                if avg_weekly_points > 0
                else 0
            )

            # Count zero weeks and high weeks (outliers)
            zero_item_weeks = len(weekly_data[weekly_data["completed_items"] == 0])
            zero_point_weeks = len(weekly_data[weekly_data["completed_points"] == 0])
            high_item_weeks = len(
                weekly_data[weekly_data["completed_items"] > avg_weekly_items * 2]
            )
            high_point_weeks = len(
                weekly_data[weekly_data["completed_points"] > avg_weekly_points * 2]
            )

            # Calculate overall stability score (0-100)
            stability_score = max(
                0,
                100
                - cv_items * 0.5
                - cv_points * 0.5
                - zero_item_weeks * 10
                - zero_point_weeks * 10
                - high_item_weeks * 5
                - high_point_weeks * 5,
            )
            stability_score = min(100, max(0, stability_score))

            # Determine velocity consistency status
            if stability_score >= 80:
                stability_status = "Consistent"
                stability_color = "success"
                stability_icon = "fa-check-circle"
            elif stability_score >= 50:
                stability_status = "Moderate"
                stability_color = "warning"
                stability_icon = "fa-exclamation-circle"
            else:
                stability_status = "Variable"
                stability_color = "danger"
                stability_icon = "fa-times-circle"

        # Calculate days of data available
        if not statistics_df.empty:
            if "date" in statistics_df.columns:
                earliest_date = pd.to_datetime(statistics_df["date"].min())
                latest_date = pd.to_datetime(statistics_df["date"].max())
                days_of_data = (
                    (latest_date - earliest_date).days + 1
                    if earliest_date and latest_date
                    else 0
                )
            else:
                days_of_data = 0
        else:
            days_of_data = 0

        # Create the card component
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H4("Project Status Summary", className="d-inline"),
                        create_info_tooltip(
                            "project-status",
                            "Summary of your project's current progress and metrics.",
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        # Project Completion Stats Row
                        dbc.Row(
                            [
                                # Items Completion
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                "Items Completion",
                                                create_info_tooltip(
                                                    "items-completion-status",
                                                    "Percentage of total work completed based on historical progress data. Items: (Completed Items ÷ Total Items) × 100%. Different percentages indicate varying complexity or estimation accuracy.",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"{items_percentage}%",
                                                    style={
                                                        "fontSize": "24px",
                                                        "fontWeight": "bold",
                                                        "color": COLOR_PALETTE["items"],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        f"Completed: {completed_items} of {total_items} items",
                                                    ],
                                                    className="text-muted small",
                                                ),
                                            ],
                                            className="text-center mb-2",
                                        ),
                                        # Progress bar for items
                                        dbc.Progress(
                                            value=items_percentage,
                                            color="info",
                                            className="mb-3",
                                            style={"height": "10px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                                # Points Completion
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                "Points Completion",
                                                create_info_tooltip(
                                                    "points-completion-status",
                                                    "Percentage of total work completed based on historical progress data. Points: (Completed Points ÷ Total Points) × 100%. Points typically reflect effort/complexity better than item count.",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"{points_percentage}%",
                                                    style={
                                                        "fontSize": "24px",
                                                        "fontWeight": "bold",
                                                        "color": COLOR_PALETTE[
                                                            "points"
                                                        ],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        f"Completed: {completed_points} of {total_points} points",
                                                    ],
                                                    className="text-muted small",
                                                ),
                                            ],
                                            className="text-center mb-2",
                                        ),
                                        # Progress bar for points
                                        dbc.Progress(
                                            value=points_percentage,
                                            color="warning",
                                            className="mb-3",
                                            style={"height": "10px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                            ],
                            className="mb-4",
                        ),
                        # Metrics Row
                        dbc.Row(
                            [
                                # Weekly Averages
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                "Weekly Averages",
                                                create_info_tooltip(
                                                    "weekly-averages-status",
                                                    "Average completion rates over recent weeks, showing sustainable team velocity. These metrics help predict future performance and identify capacity changes.",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-tasks me-2",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "items"
                                                                ]
                                                            },
                                                        ),
                                                        f"{float(avg_weekly_items):.2f}",
                                                        html.Small(" items/week"),
                                                    ],
                                                    className="d-flex align-items-center mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-2",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ]
                                                            },
                                                        ),
                                                        f"{float(avg_weekly_points):.2f}",
                                                        html.Small(" points/week"),
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                                # Velocity Stability
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                "Velocity Stability",
                                                create_info_tooltip(
                                                    "velocity-stability-status",
                                                    "Measure of how consistent your team's weekly completion rates are. Stable: Low variation (predictable). Variable: High week-to-week changes (less predictable).",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                html.I(
                                                    className=f"fas {stability_icon} me-2",
                                                    style={
                                                        "color": f"var(--bs-{stability_color})"
                                                    },
                                                ),
                                                html.Span(
                                                    stability_status,
                                                    style={
                                                        "color": f"var(--bs-{stability_color})",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                            ],
                                            className="d-flex align-items-center ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                                # Dataset Info
                                dbc.Col(
                                    [
                                        html.H6("Dataset Info", className="mb-3"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-calendar-alt me-2 text-secondary"
                                                        ),
                                                        f"{days_of_data} days of data",
                                                    ],
                                                    className="d-flex align-items-center mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-table me-2 text-secondary"
                                                        ),
                                                        f"{len(statistics_df) if not statistics_df.empty else 0} data points",
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                            ],
                        ),
                    ],
                    className="py-4",
                ),
            ],
            className="mb-4 shadow-sm",
        )

    except Exception as e:
        # Return an error card if something goes wrong
        import dash_bootstrap_components as dbc
        from dash import html

        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Project Status Summary", className="text-danger")
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-exclamation-triangle text-danger me-2"
                                ),
                                html.Span(
                                    "Unable to display project information. Please ensure you have valid project data.",
                                    className="text-danger",
                                ),
                            ],
                            className="d-flex align-items-center mb-2",
                        ),
                        html.Small(f"Error: {str(e)}", className="text-muted"),
                    ]
                ),
            ],
            className="mb-4 shadow-sm",
        )


def create_project_summary_card(
    statistics_df, settings, pert_data=None, show_points=True
):
    """
    Create a card with project dashboard information optimized for side-by-side layout.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings
        pert_data: Dictionary containing PERT analysis data (optional)
        show_points: Whether points tracking is enabled

    Returns:
        A Dash card component with project dashboard information
    """
    try:
        # Make a copy of statistics_df to avoid modifying the original
        statistics_df = (
            statistics_df.copy() if not statistics_df.empty else pd.DataFrame()
        )

        # Convert 'date' column to datetime right at the beginning
        if not statistics_df.empty and "date" in statistics_df.columns:
            statistics_df["date"] = pd.to_datetime(statistics_df["date"])

        # Calculate values needed for the dashboard
        if not statistics_df.empty:
            # Add week and year columns
            recent_df = statistics_df.tail(10).copy()
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year

            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"completed_items": "sum", "completed_points": "sum"})
                .reset_index()
            )

            # Calculate metrics needed for PERT table
            avg_weekly_items = weekly_data["completed_items"].mean()
            avg_weekly_points = weekly_data["completed_points"].mean()
        else:
            avg_weekly_items = 0
            avg_weekly_points = 0

        # Format deadline string for display
        deadline_date = settings.get("deadline")
        deadline_obj = None
        if deadline_date:
            deadline_str = deadline_date
            try:
                deadline_obj = datetime.strptime(deadline_date, "%Y-%m-%d")
                days_to_deadline = (deadline_obj - datetime.now()).days
            except (ValueError, TypeError):
                days_to_deadline = None
        else:
            deadline_str = "Not set"
            days_to_deadline = None

        # Create the pert_info content
        if pert_data:
            try:
                pert_time_items = pert_data.get("pert_time_items")
                pert_time_points = pert_data.get("pert_time_points")

                # If both PERT values are None, provide a placeholder message
                if pert_time_items is None and pert_time_points is None:
                    pert_info_content = html.Div(
                        "Forecast available after data processing",
                        className="text-muted text-center py-2",
                        style={"fontSize": "1rem"},
                    )
                else:
                    # Format PERT data for compact display
                    current_date = datetime.now()

                    if pert_time_items is not None:
                        items_completion_date = current_date + timedelta(
                            days=pert_time_items
                        )
                        items_completion_str = items_completion_date.strftime(
                            "%Y-%m-%d"
                        )
                        items_days = int(pert_time_items)
                        items_weeks = round(pert_time_items / 7, 1)
                    else:
                        items_completion_str = "Unknown"
                        items_days = "--"
                        items_weeks = "--"

                    if pert_time_points is not None:
                        points_completion_date = current_date + timedelta(
                            days=pert_time_points
                        )
                        points_completion_str = points_completion_date.strftime(
                            "%Y-%m-%d"
                        )
                        points_days = int(pert_time_points)
                        points_weeks = round(pert_time_points / 7, 1)
                    else:
                        points_completion_str = "Unknown"
                        points_days = "--"
                        points_weeks = "--"

                    # Create compact PERT info content with optimized spacing
                    pert_info_content = html.Div(
                        [
                            # Title
                            html.H6(
                                [
                                    "Project Completion Forecast",
                                    create_info_tooltip(
                                        id_suffix="project-completion-forecast",
                                        help_text=PROJECT_HELP_TEXTS[
                                            "completion_timeline"
                                        ],
                                    ),
                                ],
                                className="border-bottom pb-1 mb-3",
                                style={"fontSize": "1.1rem", "fontWeight": "bold"},
                            ),
                            # PERT Forecast in compact table format
                            dbc.Row(
                                [
                                    # Items Forecast Column
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                            "fontSize": "1rem",
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Items Completion:",
                                                        style={
                                                            "fontSize": "0.95rem",
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                    create_info_tooltip(
                                                        id_suffix="items-completion-forecast",
                                                        help_text=PROJECT_HELP_TEXTS[
                                                            "completion_timeline"
                                                        ],
                                                    ),
                                                ],
                                                className="mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        f"{items_completion_str}",
                                                        className="fw-bold",
                                                        style={
                                                            "fontSize": "1rem",
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                        },
                                                    ),
                                                ],
                                                className="ms-3 mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        f"{items_days} days ({items_weeks} weeks)",
                                                        style={"fontSize": "0.9rem"},
                                                    ),
                                                ],
                                                className="ms-3",
                                            ),
                                        ],
                                        width=6 if show_points else 12,
                                        className="px-2",
                                    ),
                                ]
                                + (
                                    [
                                        # Points Forecast Column - only show if points tracking is enabled
                                        dbc.Col(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-1",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ],
                                                                "fontSize": "1rem",
                                                            },
                                                        ),
                                                        html.Span(
                                                            "Points Completion:",
                                                            style={
                                                                "fontSize": "0.95rem",
                                                                "fontWeight": "bold",
                                                            },
                                                        ),
                                                        create_info_tooltip(
                                                            id_suffix="points-completion-forecast",
                                                            help_text=PROJECT_HELP_TEXTS[
                                                                "completion_timeline"
                                                            ],
                                                        ),
                                                    ],
                                                    className="mb-1",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            f"{points_completion_str}",
                                                            className="fw-bold",
                                                            style={
                                                                "fontSize": "1rem",
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ],
                                                            },
                                                        ),
                                                    ],
                                                    className="ms-3 mb-1",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            f"{points_days} days ({points_weeks} weeks)",
                                                            style={
                                                                "fontSize": "0.9rem"
                                                            },
                                                        ),
                                                    ],
                                                    className="ms-3",
                                                ),
                                            ],
                                            width=6,
                                            className="px-2",
                                        ),
                                    ]
                                    if show_points
                                    else []
                                ),
                                className="mb-4",  # Increased bottom margin for better spacing
                            ),
                            # Weekly velocity section
                            html.H6(
                                [
                                    "Weekly Velocity",
                                    create_info_tooltip(
                                        id_suffix="weekly-velocity-summary",
                                        help_text=PROJECT_HELP_TEXTS["weekly_averages"],
                                    ),
                                ],
                                className="border-bottom pb-1 mb-3",
                                style={"fontSize": "1.1rem", "fontWeight": "bold"},
                            ),
                            dbc.Row(
                                [
                                    # Items velocity
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                            "fontSize": "1rem",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f"{float(avg_weekly_items):.2f}",
                                                        className="fw-bold",
                                                        style={
                                                            "fontSize": "1.1rem",
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                        },
                                                    ),
                                                    html.Small(
                                                        " items/week",
                                                        style={"fontSize": "0.9rem"},
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                        ],
                                        width=6 if show_points else 12,
                                        className="px-2",
                                    ),
                                ]
                                + (
                                    [
                                        # Points velocity - only show if points tracking is enabled
                                        dbc.Col(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-1",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ],
                                                                "fontSize": "1rem",
                                                            },
                                                        ),
                                                        html.Span(
                                                            f"{float(avg_weekly_points):.2f}",
                                                            className="fw-bold",
                                                            style={
                                                                "fontSize": "1.1rem",
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ],
                                                            },
                                                        ),
                                                        html.Small(
                                                            " points/week",
                                                            style={
                                                                "fontSize": "0.9rem"
                                                            },
                                                        ),
                                                    ],
                                                    className="mb-2",
                                                ),
                                            ],
                                            width=6,
                                            className="px-2",
                                        ),
                                    ]
                                    if show_points
                                    else []
                                ),
                                className="mb-3",  # Added bottom margin to prevent overlap
                            ),
                            # Deadline section if available
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-calendar-alt me-1 text-secondary",
                                                style={"fontSize": "1rem"},
                                            ),
                                            html.Span(
                                                "Deadline: ",
                                                style={
                                                    "fontSize": "0.95rem",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            html.Span(
                                                deadline_str,
                                                style={"fontSize": "0.95rem"},
                                            ),
                                            html.Span(
                                                f" ({days_to_deadline} days remaining)"
                                                if days_to_deadline is not None
                                                else "",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "marginLeft": "8px",
                                                },
                                            ),
                                        ],
                                        className="mt-2",
                                    ),
                                ]
                            )
                            if deadline_date
                            else html.Div(),
                        ],
                        className="mb-2",  # Added bottom margin to prevent overlap with card border
                    )
            except Exception as pert_error:
                pert_info_content = html.P(
                    f"Error: {str(pert_error)}",
                    className="text-danger p-2",
                    style={"fontSize": "1rem"},
                )
        else:
            pert_info_content = html.Div(
                "Project forecast will display here once data is available",
                className="text-muted text-center py-3",
                style={"fontSize": "1rem"},
            )

        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H4(
                            "Project Dashboard",
                            className="d-inline",
                        ),
                        create_info_tooltip(
                            "project-dashboard",
                            "Project analysis based on your historical data.",
                        ),
                    ],
                    className="py-2",
                ),
                dbc.CardBody(
                    [
                        # The content is directly placed here without any header or section dividers
                        html.Div(
                            pert_info_content,
                            id="project-dashboard-pert-content",
                            className="pt-1 pb-2",  # Added padding at top and bottom
                        ),
                    ],
                    className="p-3",  # Increased padding for better spacing
                ),
            ],
            className="mb-3 shadow-sm h-100",
        )
    except Exception as e:
        # Fallback card in case of errors
        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H4(
                        "Project Dashboard",
                        className="d-inline",
                        style={"fontSize": "1.4rem"},  # Increased heading size
                    )
                ),
                dbc.CardBody(
                    [
                        html.P(
                            "Unable to display project information. Please ensure you have valid project data.",
                            className="text-danger mb-1",
                            style={"fontSize": "1rem"},
                        ),
                        html.Small(f"Error: {str(e)}", className="text-muted"),
                    ],
                    className="p-3",
                ),
            ],
            className="mb-3 shadow-sm h-100",
        )


def create_items_forecast_info_card(statistics_df=None, pert_data=None):
    """
    Create a concise forecast information card for the Items per Week tab.

    Args:
        statistics_df: DataFrame containing the project statistics (optional)
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        Dash Card component with items forecast explanation
    """

    # Extract metrics from statistics if available
    if statistics_df is not None and not statistics_df.empty:
        # Convert to datetime to ensure proper week grouping
        recent_df = statistics_df.copy()
        recent_df["date"] = pd.to_datetime(recent_df["date"])
        recent_df["week"] = recent_df["date"].dt.isocalendar().week
        recent_df["year"] = recent_df["date"].dt.isocalendar().year

        # Use tail(10) to focus on recent data
        recent_df = recent_df.tail(10)

    # Generate a unique ID for this collapse component
    collapse_id = "items-forecast-info-collapse"

    # The card content with chart elements and forecast method
    chart_info = html.Div(
        className="row g-3",
        children=[
            # Column 1: Chart Elements
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "Chart Elements",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Span(
                                            "Blue Bars",
                                            style={
                                                "color": COLOR_PALETTE["items"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Historical weekly completed items",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Dark Blue Line",
                                            style={
                                                "color": "#0047AB",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Weighted 4-week moving average",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Patterned Bar",
                                            style={
                                                "color": COLOR_PALETTE["items"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Next week's forecast",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
            # Column 2: Forecast Method
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "PERT Forecast Method",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Strong("Most Likely: "),
                                        "Average of recent weekly data",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Optimistic: "),
                                        "Average of highest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Pessimistic: "),
                                        "Average of lowest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Weighted Average: "),
                                        "Recent weeks weighted [10%, 20%, 30%, 40%]",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
        ],
    )

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Items Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="mobile-touch-target-sm border-0",
                                    ),
                                    create_info_tooltip(
                                        "items-forecast-info",
                                        "Understanding the weekly items forecast chart and trends.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(chart_info, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",  # Changed from "mt-3 mb-2 shadow-sm" to "my-2" for consistent 8px margins
    )


def create_points_forecast_info_card(statistics_df=None, pert_data=None):
    """
    Create a concise forecast information card for the Points per Week tab.

    Args:
        statistics_df: DataFrame containing the project statistics (optional)
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        Dash Card component with points forecast explanation
    """

    # Extract metrics from statistics if available
    if statistics_df is not None and not statistics_df.empty:
        # Convert to datetime to ensure proper week grouping
        recent_df = statistics_df.copy()
        recent_df["date"] = pd.to_datetime(recent_df["date"])
        recent_df["week"] = recent_df["date"].dt.isocalendar().week
        recent_df["year"] = recent_df["date"].dt.isocalendar().year

        # Use tail(10) to focus on recent data
        recent_df = recent_df.tail(10)

    # Generate a unique ID for this collapse component
    collapse_id = "points-forecast-info-collapse"

    # The card content with chart elements and forecast method
    chart_info = html.Div(
        className="row g-3",
        children=[
            # Column 1: Chart Elements
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "Chart Elements",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Span(
                                            "Orange Bars",
                                            style={
                                                "color": COLOR_PALETTE["points"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Historical weekly completed points",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Tomato Line",
                                            style={
                                                "color": "#FF6347",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Weighted 4-week moving average",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Patterned Bar",
                                            style={
                                                "color": COLOR_PALETTE["points"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Next week's forecast with confidence interval",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
            # Column 2: Forecast Method
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "PERT Forecast Method",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Strong("Most Likely: "),
                                        "Average of recent weekly data",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Optimistic: "),
                                        "Average of highest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Pessimistic: "),
                                        "Average of lowest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Weighted Average: "),
                                        "Recent weeks weighted [10%, 20%, 30%, 40%]",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
        ],
    )

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Points Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="mobile-touch-target-sm border-0",
                                    ),
                                    create_info_tooltip(
                                        "points-forecast-info",
                                        "Understanding the weekly points forecast chart and trends.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(chart_info, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",
    )


#######################################################################
# UNIFIED METRIC CARD COMPONENTS
#######################################################################


def create_unified_metric_card(
    title: str,
    value: str,
    icon: str,
    status_color: str,
    status_bg: str,
    status_border: str,
    secondary_info: str = "",
    tertiary_info: str = "",
    help_text: str = "",
    card_id: str = "",
) -> dbc.Col:
    """
    Create a unified metric card following the Bug Analysis Dashboard design pattern.

    This component provides consistent styling across all tabs:
    - Icon circle with status-based coloring
    - Three lines of information (title/value, secondary, tertiary)
    - Responsive layout (full width mobile, configurable desktop columns)
    - Equal height cards with h-100 class

    Args:
        title: Main metric title/label
        value: Primary metric value to display
        icon: FontAwesome icon class (e.g., "fa-check-circle")
        status_color: Primary status color (hex)
        status_bg: Background color with transparency
        status_border: Border color with transparency
        secondary_info: Second line of contextual information
        tertiary_info: Third line of contextual information (date range, etc.)
        help_text: Optional tooltip text for help icon
        card_id: Optional ID for the card element

    Returns:
        dbc.Col: Responsive column containing the metric card

    Example:
        >>> card = create_unified_metric_card(
        ...     title="Resolution Rate",
        ...     value="73.2%",
        ...     icon="fa-check-circle",
        ...     status_color="#28a745",
        ...     status_bg="rgba(40, 167, 69, 0.1)",
        ...     status_border="rgba(40, 167, 69, 0.2)",
        ...     secondary_info="123 closed / 168 total • Good",
        ...     tertiary_info="[Date] May 22, 2025 - Oct 23, 2025",
        ... )
    """
    from ui.style_constants import METRIC_CARD

    # Build card content layers
    card_content = [
        # Icon circle with status color
        html.Div(
            html.I(
                className=f"fas {icon}",
                style={"color": status_color, "fontSize": "1.25rem"},
            ),
            className="d-flex align-items-center justify-content-center rounded-circle me-3",
            style={
                "width": METRIC_CARD["icon_circle_size"],
                "height": METRIC_CARD["icon_circle_size"],
                "backgroundColor": METRIC_CARD["icon_bg"],
                "flexShrink": "0",
            },
        ),
        # Text content column
        html.Div(
            [
                # Line 1: Title and value
                html.Div(
                    [
                        html.Span(f"{title}: ", className="text-muted small"),
                        html.Span(
                            value, className="fw-bold", style={"fontSize": "1.1rem"}
                        ),
                    ],
                    className="mb-1",
                ),
                # Line 2: Secondary information
                html.Div(secondary_info, className="small text-muted")
                if secondary_info
                else None,
                # Line 3: Tertiary information
                html.Div(tertiary_info, className="small text-muted")
                if tertiary_info
                else None,
            ],
            className="flex-grow-1",
            style={"minWidth": "0"},  # Allow text truncation if needed
        ),
        # Optional help icon
        html.I(
            className="fas fa-info-circle text-info ms-2",
            style={"cursor": "pointer", "fontSize": "0.875rem"},
            id=f"help-{card_id}" if card_id else None,
        )
        if help_text
        else None,
    ]

    # Create the card
    card = html.Div(
        card_content,
        className="compact-trend-indicator d-flex align-items-center p-3 rounded h-100",
        style={
            "backgroundColor": status_bg,
            "border": f"{METRIC_CARD['border_width']} solid {status_border}",
            "minHeight": METRIC_CARD["min_height"],
        },
        id=card_id if card_id else None,
    )

    # Wrap in responsive column (full width mobile, can be adjusted via className)
    return dbc.Col(
        card,
        width=12,  # Full width on mobile
        md=4,  # 3 columns on tablet/desktop
        className="mb-2",
    )


def create_unified_metric_row(cards: List[dbc.Col]) -> dbc.Row:
    """
    Create a responsive row of unified metric cards.

    Args:
        cards: List of metric card columns (from create_unified_metric_card)

    Returns:
        dbc.Row: Row containing metric cards with responsive layout

    Example:
        >>> cards = [
        ...     create_unified_metric_card(...),
        ...     create_unified_metric_card(...),
        ...     create_unified_metric_card(...),
        ... ]
        >>> row = create_unified_metric_row(cards)
    """
    return dbc.Row(
        cards,
        className="g-2 mb-3",  # g-2 for consistent gutter spacing
    )
