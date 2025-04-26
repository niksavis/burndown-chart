"""
Import Organization Example

This module demonstrates the proper import organization structure according to
the project's conventions/imports.md guidelines.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports

# Third-party library imports
from dash import html

# Application imports
from data.processing import calculate_total_points  # Feature-specific imports last


#######################################################################
# MODULE CONSTANTS
#######################################################################
DEFAULT_COLOR = "#0d6efd"
MAX_ITEMS = 100


#######################################################################
# HELPER FUNCTIONS
#######################################################################
def format_date(date_obj):
    """Format a date object as YYYY-MM-DD."""
    return date_obj.strftime("%Y-%m-%d")


#######################################################################
# MAIN COMPONENT FUNCTION
#######################################################################
def create_example_component(data, title="Example Component"):
    """
    Create an example component with properly organized imports.

    Args:
        data: The data to display
        title: Title for the component

    Returns:
        A Dash component
    """
    # Function implementation here...
    return html.Div(
        [
            html.H3(title),
            html.P(f"Data processing result: {calculate_total_points(data, 10, 50)}"),
        ]
    )


#######################################################################
# Function to avoid circular imports by using runtime imports
#######################################################################
def get_stats_component():
    """
    Example of a function that uses runtime imports to avoid circular dependencies.

    Returns:
        A statistics component
    """
    # Import at function level to avoid circular dependency
    from callbacks.statistics import create_stats_display

    return create_stats_display()
