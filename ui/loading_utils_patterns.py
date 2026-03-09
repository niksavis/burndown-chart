"""
Loading Utilities Patterns Module

Pattern-specific loading states including content placeholders, unified
loading state factory, async containers, lazy tabs, and data sections.
"""

#######################################################################
# IMPORTS
#######################################################################
import warnings

import dash_bootstrap_components as dbc

# Third-party library imports
from dash import html

from ui.loading_utils_core import (
    create_growing_spinner,
    create_loading_overlay,
    create_skeleton_loader,
    create_spinner,
)

# Application imports
from ui.style_constants import (
    NEUTRAL_COLORS,
    PRIMARY_COLORS,
    SEMANTIC_COLORS,
)

#######################################################################
# CONTENT PLACEHOLDERS
#######################################################################


def create_content_placeholder(
    type="table", text=None, icon=None, height="100px", className=""
):
    """
    Creates a placeholder indicating the type of content being loaded.

    Args:
        type (str, optional): The type of content
            ("table", "chart", "text", "data", "image", "file", "form").
            Defaults to "table". Determines default icon and text.
        text (str, optional): Custom text to display in the placeholder.
                              Overrides default text if provided. Defaults to None.
        icon (str, optional): Custom Font Awesome icon class
            (e.g., "fas fa-cog") to display.
            Overrides default icon if provided. Defaults to None.
        height (str, optional): CSS height of the placeholder container.
            Defaults to "100px".
        className (str, optional): Additional CSS classes to apply. Defaults to "".

    Returns:
        html.Div: A Div containing the placeholder icon and text.
    """
    # Default settings by type
    type_defaults = {
        "data": {
            "icon": "fas fa-database",
            "message": "Loading data...",
            "color": SEMANTIC_COLORS.get("secondary"),
        },
        "chart": {
            "icon": "fas fa-chart-bar",
            "message": "Preparing chart...",
            "color": PRIMARY_COLORS.get("primary"),
        },
        "table": {
            "icon": "fas fa-table",
            "message": "Loading table data...",
            "color": SEMANTIC_COLORS.get("success"),
        },
        "image": {
            "icon": "fas fa-image",
            "message": "Loading image...",
            "color": SEMANTIC_COLORS.get("info"),
        },
        "file": {
            "icon": "fas fa-file-alt",
            "message": "Loading file...",
            "color": SEMANTIC_COLORS.get("warning"),
        },
        "form": {
            "icon": "fas fa-wpforms",
            "message": "Preparing form...",
            "color": SEMANTIC_COLORS.get("secondary"),
        },
    }

    # Get defaults for the specified type or use generic data defaults
    defaults = type_defaults.get(type, type_defaults["data"])

    # Use provided text and icon or fall back to defaults
    display_text = text if text is not None else defaults["message"]
    display_icon = icon if icon is not None else defaults["icon"]

    return html.Div(
        [
            html.I(
                className=f"{display_icon} fa-3x mb-3",
                style={"color": defaults["color"], "opacity": "0.7"},
            ),
            html.Div(display_text, className="text-muted"),
        ],
        className=(
            "d-flex flex-column justify-content-center "
            f"align-items-center py-5 {className}"
        ),
        style={
            "backgroundColor": NEUTRAL_COLORS.get("gray-100"),
            "border": f"1px dashed {NEUTRAL_COLORS.get('gray-300')}",
            "borderRadius": "0.5rem",
            "minHeight": "200px",  # Keep a minimum height
            "height": height,  # Allow overriding height
        },
    )


#######################################################################
# HIGH-LEVEL LOADING COMPONENTS
#######################################################################


def create_loading_state(
    children=None,
    is_loading=False,
    type="spinner",  # spinner, growing, skeleton, overlay, placeholder
    style_key="primary",
    size_key="md",
    message="Loading...",
    className="",
    id=None,
):
    """
    Unified loading state component that provides a consistent interface
    for all loading state types.

    Args:
        children: Content to display when not loading (required for overlay type)
        is_loading (bool): Whether to show the loading state
        type (str): Type of loading component
            ('spinner', 'growing', 'skeleton', 'overlay', 'placeholder')
        style_key (str): Color style key (primary, secondary, success, etc.)
        size_key (str): Size key (xs, sm, md, lg, xl)
        message (str): Message to display with the loading indicator
        className (str): Additional CSS classes
        id (str): Component ID

    Returns:
        Dash component: A loading state component of the specified type
    """
    # If not loading and we have children, just return the children
    if not is_loading and children is not None:
        return html.Div(children, className=className, id=id)

    if type == "spinner":
        return create_spinner(
            style_key=style_key,
            size_key=size_key,
            text=message,
            className=className,
            id=id,
        )

    elif type == "growing":
        return create_growing_spinner(
            style_key=style_key,
            size_key=size_key,
            count=3,
            variant="circle",
            className=className,
        )

    elif type == "skeleton":
        # Determine skeleton type based on children or default to "text"
        skeleton_type = "text"
        if children is not None:
            children_str = str(children).lower()
            if "chart" in children_str or "graph" in children_str:
                skeleton_type = "chart"
            elif "card" in children_str:
                skeleton_type = "card"
            elif "img" in children_str or "image" in children_str:
                skeleton_type = "image"

        return create_skeleton_loader(
            type=skeleton_type,
            lines=3 if skeleton_type == "text" else 1,
            className=className,
        )

    elif type == "overlay":
        if children is None:
            raise ValueError("Children must be provided when using 'overlay' type")

        return create_loading_overlay(
            children=children,
            style_key=style_key,
            size_key=size_key,
            text=message,
            is_loading=is_loading,
            className=className,
        )

    elif type == "placeholder":
        # Determine placeholder type based on children or default to "data"
        placeholder_type = "data"
        if children is not None:
            children_str = str(children).lower()
            if "chart" in children_str or "graph" in children_str:
                placeholder_type = "chart"
            elif "table" in children_str:
                placeholder_type = "table"
            elif "img" in children_str or "image" in children_str:
                placeholder_type = "image"

        return create_content_placeholder(
            type=placeholder_type, text=message, className=className
        )

    else:
        # Invalid type, return default spinner
        warnings.warn(
            f"Invalid loading type '{type}'. Using default spinner.",
            UserWarning,
            stacklevel=2,
        )
        return create_spinner(
            style_key=style_key,
            size_key=size_key,
            text=message,
            className=className,
            id=id,
        )


def create_async_content(id, loading_state_id=None, content_type="chart"):
    """
    Create a container for async content with proper loading states.

    Args:
        id (str): ID for the component
        loading_state_id (str): ID for loading-state indicator,
            defaults to {id}-loading
        content_type (str): Type of content ('chart', 'data', 'table', etc.)

    Returns:
        html.Div: Container with loading placeholder
    """
    if loading_state_id is None:
        loading_state_id = f"{id}-loading"

    # Determine appropriate loading message
    loading_messages = {
        "chart": "Loading chart data...",
        "table": "Loading table data...",
        "data": "Loading data...",
        "image": "Loading image...",
    }

    message = loading_messages.get(content_type, "Loading...")

    return html.Div(
        [
            # Hidden loading state that can be triggered by callbacks
            html.Div(id=loading_state_id, style={"display": "none"}),
            # Initial placeholder
            create_content_placeholder(type=content_type, text=message),
            # Container for the actual content (empty initially)
            html.Div(id=id),
        ]
    )


def create_lazy_loading_tabs(
    tabs_data, tab_id_prefix="tab", content_id_prefix="tab-content"
):
    """
    Create tabs that load their content only when activated.

    Args:
        tabs_data (list): List of dictionaries with tab information:
                          [{"label": "Tab1", "content": content1, "active": True}, ...]
        tab_id_prefix (str): Prefix for tab IDs
        content_id_prefix (str): Prefix for content IDs

    Returns:
        list: A list containing the tabs component and the tab content div
    """
    tabs = []
    contents = []

    # Create each tab
    for i, tab in enumerate(tabs_data):
        tab_id = f"{tab_id_prefix}-{i}"
        content_id = f"{content_id_prefix}-{i}"

        # Create the tab
        tabs.append(
            dbc.Tab(
                label=tab["label"],
                tab_id=tab_id,
                active=tab.get("active", i == 0),
                id=tab_id,
            )
        )

        # Create the content container
        content_div = html.Div(
            # If it's the active tab, show content, otherwise show a placeholder
            tab["content"]
            if tab.get("active", i == 0)
            else create_content_placeholder(
                type=tab.get("content_type", "data"),
                text=f"Loading {tab['label']}...",
            ),
            id=content_id,
            style={"display": "block" if tab.get("active", i == 0) else "none"},
        )

        contents.append(content_div)

    return [
        dbc.Tabs(tabs, id=f"{tab_id_prefix}-container"),
        html.Div(contents, id=f"{content_id_prefix}-container"),
    ]


def create_data_loading_section(
    id,
    title=None,
    loading_message="Loading data...",
    error_message="Failed to load data",
    retry_button=True,
):
    """
    Create a section that handles data loading states including error handling.

    Args:
        id (str): Base ID for the section
        title (str): Optional title for the section
        loading_message (str): Message to display during loading
        error_message (str): Message to display on error
        retry_button (bool): Whether to show a retry button on error

    Returns:
        html.Div: A complete section with loading and error states
    """
    section_id = f"{id}-section"
    loading_id = f"{id}-loading"
    content_id = f"{id}-content"
    error_id = f"{id}-error"
    retry_id = f"{id}-retry"

    header = html.H5(title) if title else html.Div()  # Always render a component

    return html.Div(
        [
            header,
            # Loading state (hidden initially)
            html.Div(
                create_loading_state(
                    message=loading_message, type="spinner", style_key="primary"
                ),
                id=loading_id,
                style={"display": "none"},
            ),
            # Content container (empty initially)
            html.Div(id=content_id),
            # Error state (hidden initially)
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-exclamation-triangle text-danger me-2"
                            ),
                            html.Span(error_message),
                        ],
                        className="d-flex align-items-center mb-3",
                    ),
                    html.Button(
                        "Retry",
                        id=retry_id,
                        className="btn btn-outline-primary btn-sm",
                    )
                    if retry_button
                    else None,
                ],
                id=error_id,
                className="my-4 p-3 border border-danger rounded",
                style={"display": "none"},
            ),
        ],
        id=section_id,
        className="mb-4",
    )
