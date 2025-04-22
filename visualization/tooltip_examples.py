"""
Examples of how to use the tooltip styling system from ui.styles
This file provides examples and best practices for implementing consistent
tooltips across all charts in the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import random

# Third-party library imports
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Application imports
from ui.styles import (
    format_hover_template,
    create_hoverlabel_config,
    get_tooltip_style,
    create_chart_layout_config,
    TOOLTIP_STYLES,
    COLOR_PALETTE,
)


def create_tooltip_demo_chart():
    """
    Create a demonstration chart showing all tooltip variants

    Returns:
        A Plotly figure object with examples of all tooltip styles
    """
    # Create sample data
    x = list(range(10))

    # Create figure
    fig = go.Figure()

    # Add a trace for each tooltip style
    for style_name in TOOLTIP_STYLES:
        # Generate y values with some randomness for visual separation
        y = [i + np.random.normal(0, 0.5) for i in x]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                name=f"{style_name.capitalize()} Style",
                line=dict(width=2),
                marker=dict(size=8),
                hovertemplate=format_hover_template(
                    title=f"{style_name.capitalize()} Tooltip",
                    fields={
                        "X Value": "%{x}",
                        "Y Value": "%{y:.2f}",
                    },
                    extra_info=f"This is a {style_name} style tooltip example",
                ),
                hoverlabel=create_hoverlabel_config(style_name),
            )
        )

    # Update layout
    fig.update_layout(
        **create_chart_layout_config(
            title="Tooltip Style Variants",
            xaxis_title="X Axis",
            yaxis_title="Y Axis",
        )
    )

    return fig


def create_complex_tooltip_example():
    """
    Create an example with more complex tooltip content

    Returns:
        A Plotly figure showing more advanced tooltip usage
    """
    # Create sample data
    dates = pd.date_range(start="2025-01-01", periods=30, freq="D")
    values = np.cumsum(np.random.normal(5, 2, 30))
    velocity = [values[i] - values[i - 1] if i > 0 else 0 for i in range(len(values))]

    # Create figure
    fig = go.Figure()

    # Add main trace with complex tooltip
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Progress",
            line=dict(color=COLOR_PALETTE["primary"], width=3),
            marker=dict(size=8),
            hovertemplate=format_hover_template(
                title="Daily Progress",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Total": "%{y:.1f}",
                    "Daily Change": [f"{v:.1f}" for v in velocity],
                    "Status": [
                        "Good" if v > 5 else "Warning" if v > 2 else "Alert"
                        for v in velocity
                    ],
                },
                extra_info="Hover over points to see details",
            ),
            hoverlabel=create_hoverlabel_config("info"),
            # Store extra data for tooltip
            customdata=velocity,
        )
    )

    # Update layout
    fig.update_layout(
        **create_chart_layout_config(
            title="Complex Tooltip Example",
            xaxis_title="Date",
            yaxis_title="Cumulative Value",
        )
    )

    return fig


def create_conditional_tooltips_example():
    """
    Create an example with conditional tooltip styling based on values

    Returns:
        A Plotly figure showing conditionally styled tooltips
    """
    # Create sample data
    x = list(range(15))
    y = [np.random.normal(10, 5) for _ in range(15)]

    # Determine colors based on values
    tooltip_styles = []
    for val in y:
        if val > 15:
            tooltip_styles.append("success")
        elif val > 10:
            tooltip_styles.append("info")
        elif val > 5:
            tooltip_styles.append("default")
        elif val > 0:
            tooltip_styles.append("warning")
        else:
            tooltip_styles.append("error")

    # Create figure
    fig = go.Figure()

    # Add individual points with conditional tooltips
    for i, (x_val, y_val, style) in enumerate(zip(x, y, tooltip_styles)):
        fig.add_trace(
            go.Scatter(
                x=[x_val],
                y=[y_val],
                mode="markers",
                marker=dict(
                    size=12,
                    color=get_tooltip_style(style)["backgroundColor"],
                ),
                name=f"Point {i}",
                showlegend=False,
                hovertemplate=format_hover_template(
                    title=f"{style.capitalize()} Value",
                    fields={
                        "Position": f"{x_val}",
                        "Value": f"{y_val:.2f}",
                    },
                ),
                hoverlabel=create_hoverlabel_config(style),
            )
        )

    # Add a legend with style explanations
    for style in set(tooltip_styles):
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(
                    size=10,
                    color=get_tooltip_style(style)["backgroundColor"],
                ),
                name=f"{style.capitalize()} ({style})",
            )
        )

    # Update layout
    fig.update_layout(
        **create_chart_layout_config(
            title="Conditional Tooltip Styling",
            xaxis_title="X Axis",
            yaxis_title="Value",
        )
    )

    return fig


if __name__ == "__main__":
    # Example usage in a Dash application
    # This section would be uncommented and used if running directly
    """
    import dash
    from dash import dcc, html
    
    app = dash.Dash(__name__)
    
    app.layout = html.Div([
        html.H1("Tooltip Styling Examples"),
        
        html.H2("Basic Tooltip Variants"),
        dcc.Graph(figure=create_tooltip_demo_chart()),
        
        html.H2("Complex Tooltip Example"),
        dcc.Graph(figure=create_complex_tooltip_example()),
        
        html.H2("Conditional Tooltips"),
        dcc.Graph(figure=create_conditional_tooltips_example()),
    ])
    
    if __name__ == "__main__":
        app.run_server(debug=True)
    """
