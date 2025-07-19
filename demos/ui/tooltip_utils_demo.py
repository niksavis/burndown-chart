"""
Tooltip Utils Demo Application

This script demonstrates and validates the usage of the tooltip_utils module.
To run this demo, execute: python demos/ui/tooltip_utils_demo.py
"""

# Add the project root to the path so we can import the ui module properly
# IMPORTANT: This must be done before any other imports
import sys
from pathlib import Path

# Add the project root to the Python path (two levels up from demos/ui/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Now we can import from ui modules
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

from ui.tooltip_utils import (
    create_tooltip,
    create_info_tooltip,
    create_enhanced_tooltip,
    create_form_help_tooltip,
    create_contextual_help,
    create_chart_layout_config,
    format_hover_template,
)

app = Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)

# Create examples of all tooltip types
app.layout = html.Div(
    [
        html.H1("Tooltip Utils Demo"),
        html.H2("Basic Tooltips", className="mt-4"),
        html.Div(
            [
                html.Div(
                    [
                        html.Button(
                            "Default Tooltip",
                            id="default-tooltip-btn",
                            className="me-2",
                        ),
                        create_tooltip(
                            "This is a default tooltip", target="default-tooltip-btn"
                        ),
                        html.Button(
                            "Primary Tooltip",
                            id="primary-tooltip-btn",
                            className="me-2",
                        ),
                        create_tooltip(
                            "This is a primary tooltip with longer text to demonstrate wrapping behavior",
                            target="primary-tooltip-btn",
                            variant="primary",
                        ),
                        html.Button(
                            "Success Tooltip",
                            id="success-tooltip-btn",
                            className="me-2",
                        ),
                        create_tooltip(
                            "This is a success tooltip!",
                            target="success-tooltip-btn",
                            variant="success",
                        ),
                        html.Button(
                            "Warning Tooltip",
                            id="warning-tooltip-btn",
                            className="me-2",
                        ),
                        create_tooltip(
                            "This is a warning tooltip!",
                            target="warning-tooltip-btn",
                            variant="warning",
                        ),
                        html.Button(
                            "Error Tooltip", id="error-tooltip-btn", className="me-2"
                        ),
                        create_tooltip(
                            "This is an error tooltip!",
                            target="error-tooltip-btn",
                            variant="error",
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Button(
                            "Bottom Tooltip",
                            id="bottom-tooltip-btn",
                            className="me-2 mt-3",
                        ),
                        create_tooltip(
                            "This tooltip appears below the element",
                            target="bottom-tooltip-btn",
                            position="bottom",
                        ),
                        html.Button(
                            "Left Tooltip", id="left-tooltip-btn", className="me-2 mt-3"
                        ),
                        create_tooltip(
                            "This tooltip appears to the left",
                            target="left-tooltip-btn",
                            position="left",
                        ),
                        html.Button(
                            "Right Tooltip",
                            id="right-tooltip-btn",
                            className="me-2 mt-3",
                        ),
                        create_tooltip(
                            "This tooltip appears to the right",
                            target="right-tooltip-btn",
                            position="right",
                        ),
                    ]
                ),
            ],
            className="mb-5",
        ),
        html.H2("Info Tooltips", className="mt-4"),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Field with Info Tooltip:", className="me-2"),
                        create_info_tooltip(
                            "info-tooltip-1",
                            "This is helpful information about the field",
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label("Another Field:", className="me-2 mt-3"),
                        create_info_tooltip(
                            "info-tooltip-2",
                            "This is more detailed information with additional context and guidance for the user",
                            placement="top",
                            variant="primary",
                        ),
                    ]
                ),
            ],
            className="mb-5",
        ),
        html.H2("Enhanced Tooltips", className="mt-4"),
        html.Div(
            [
                html.Div(
                    [
                        html.Span("This paragraph has ", className="me-1"),
                        create_enhanced_tooltip(
                            "enhanced-tooltip-1",
                            "Enhanced tooltips can be triggered by text or icons and support rich content.",
                            trigger_text="enhanced tooltip text",
                            variant="info",
                        ),
                        html.Span(" that can be hovered."),
                    ]
                ),
                html.Div(
                    [
                        html.Span("There is also a ", className="me-1 mt-3"),
                        create_enhanced_tooltip(
                            "enhanced-tooltip-2",
                            html.Div(
                                [
                                    html.H6("Rich Content Tooltip"),
                                    html.P(
                                        "This tooltip contains formatted HTML content including:"
                                    ),
                                    html.Ul(
                                        [
                                            html.Li("Headings"),
                                            html.Li("Lists"),
                                            html.Li("And other formatting"),
                                        ]
                                    ),
                                ]
                            ),
                            trigger_text="tooltip with rich content",
                            variant="primary",
                            icon_class="fas fa-lightbulb",
                        ),
                        html.Span(" for more complex help."),
                    ]
                ),
            ],
            className="mb-5",
        ),
        html.H2("Form Help Tooltips", className="mt-4"),
        html.Div(
            [
                html.Div(
                    [
                        create_form_help_tooltip(
                            "form-help-1",
                            "Username",
                            "Enter your username (at least 5 characters)",
                        ),
                        dbc.Input(type="text", placeholder="Username"),
                    ],
                    className="mb-3",
                ),
                html.Div(
                    [
                        create_form_help_tooltip(
                            "form-help-2",
                            "Email Address",
                            "We'll never share your email with anyone else",
                            variant="primary",
                        ),
                        dbc.Input(type="email", placeholder="Email"),
                    ],
                    className="mb-3",
                ),
                html.Div(
                    [
                        create_form_help_tooltip(
                            "form-help-3",
                            "API Key (required)",
                            "You can find your API key in your account settings",
                            variant="warning",
                        ),
                        dbc.Input(type="password", placeholder="API Key"),
                    ],
                    className="mb-3",
                ),
            ],
            className="mb-5 border p-3",
        ),
        html.H2("Contextual Help", className="mt-4"),
        html.Div(
            [
                html.P(
                    [
                        "To configure your burndown chart, you'll need to specify a deadline. ",
                        create_contextual_help(
                            "context-help-1",
                            "The deadline is the date by which all work must be completed. This is used to calculate burndown rates and projections.",
                            "Learn more about deadlines",
                        ),
                    ]
                ),
                html.P(
                    [
                        "PERT estimates ",
                        create_contextual_help(
                            "context-help-2",
                            html.Div(
                                [
                                    html.P(
                                        "PERT (Program Evaluation and Review Technique) estimates use three data points:"
                                    ),
                                    html.Ul(
                                        [
                                            html.Li("Optimistic (best case)"),
                                            html.Li("Most likely (expected case)"),
                                            html.Li("Pessimistic (worst case)"),
                                        ]
                                    ),
                                    html.P(
                                        "The weighted formula is: (Optimistic + 4*Most Likely + Pessimistic) / 6"
                                    ),
                                ]
                            ),
                            "What are PERT estimates?",
                            variant="info",
                        ),
                        " are used to provide more accurate completion projections.",
                    ]
                ),
            ],
            className="mb-5",
        ),
        html.H2("Chart Tooltips", className="mt-4"),
        html.Div(
            [
                dcc.Graph(
                    figure={
                        "data": [
                            {
                                "x": [1, 2, 3, 4, 5],
                                "y": [10, 8, 6, 4, 2],
                                "type": "scatter",
                                "name": "Items",
                                "hovertemplate": format_hover_template(
                                    "Items Remaining",
                                    {"Date": "%{x}", "Items": "%{y}"},
                                ),
                            },
                            {
                                "x": [1, 2, 3, 4, 5],
                                "y": [50, 40, 30, 20, 10],
                                "type": "scatter",
                                "name": "Points",
                                "hovertemplate": format_hover_template(
                                    "Points Remaining",
                                    {"Date": "%{x}", "Points": "%{y}"},
                                ),
                            },
                        ],
                        "layout": create_chart_layout_config(
                            title="Burndown Chart",
                            hover_mode="unified",
                            tooltip_variant="info",
                        ),
                    }
                )
            ],
            className="mb-5",
        ),
    ],
    style={"maxWidth": "800px", "margin": "0 auto", "padding": "20px"},
)


if __name__ == "__main__":
    print("Starting Tooltip Utils Demo server on http://127.0.0.1:8050/")
    app.run(debug=True)
