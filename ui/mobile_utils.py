"""
Mobile Utilities Module

This module provides tools for implementing and testing a mobile-first approach
across all application components.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_mobile_checker(id_prefix="mobile-view"):
    """
    Create a component that helps visualize and test mobile view requirements.

    Args:
        id_prefix: Prefix for component IDs

    Returns:
        A collapsible component for checking mobile view requirements
    """
    return html.Div(
        [
            dbc.Button(
                [html.I(className="fas fa-mobile-alt me-2"), "Mobile View Checker"],
                id=f"{id_prefix}-toggle",
                color="secondary",
                className="mb-3",
                outline=True,
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Mobile View Requirements", className="card-title"),
                            # Touch target checker
                            html.Div(
                                [
                                    html.H6("Touch Target Checker"),
                                    html.Div(
                                        [
                                            html.Div(
                                                html.Div(
                                                    "44x44px",
                                                    className="d-flex align-items-center justify-content-center",
                                                    style={
                                                        "height": "44px",
                                                        "width": "44px",
                                                        "border": "1px dashed #007bff",
                                                    },
                                                ),
                                                className="mb-2",
                                            ),
                                            dbc.Button(
                                                "Test Touch Target",
                                                id=f"{id_prefix}-test-button",
                                                className="mb-2",
                                            ),
                                            html.Div(
                                                id=f"{id_prefix}-touch-feedback",
                                                className="mt-2 small text-muted",
                                            ),
                                        ],
                                        className="mb-4",
                                    ),
                                    # Text truncation checker
                                    html.Div(
                                        [
                                            html.H6("Text Truncation Preview"),
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("Test Text"),
                                                    dbc.Input(
                                                        id=f"{id_prefix}-truncate-input",
                                                        placeholder="Enter long text to see truncation",
                                                        value="This is a long text that should be truncated on mobile screens using the standard pattern",
                                                        className="mb-2",
                                                    ),
                                                ]
                                            ),
                                            html.Div(
                                                "Preview:", className="mb-2 small"
                                            ),
                                            html.Div(
                                                id=f"{id_prefix}-truncate-preview",
                                                className="mobile-truncate border p-2",
                                                style={"maxWidth": "200px"},
                                            ),
                                        ],
                                        className="mb-4",
                                    ),
                                    # Breakpoint indicator
                                    html.Div(
                                        [
                                            html.H6("Current Breakpoint"),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "xs",
                                                        className="d-inline-block d-sm-none badge bg-primary me-1",
                                                    ),
                                                    html.Span(
                                                        "sm",
                                                        className="d-none d-sm-inline-block d-md-none badge bg-info me-1",
                                                    ),
                                                    html.Span(
                                                        "md",
                                                        className="d-none d-md-inline-block d-lg-none badge bg-success me-1",
                                                    ),
                                                    html.Span(
                                                        "lg",
                                                        className="d-none d-lg-inline-block d-xl-none badge bg-warning me-1",
                                                    ),
                                                    html.Span(
                                                        "xl",
                                                        className="d-none d-xl-inline-block d-xxl-none badge bg-danger me-1",
                                                    ),
                                                    html.Span(
                                                        "xxl",
                                                        className="d-none d-xxl-inline-block badge bg-secondary",
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    # Viewport size indicator
                                    html.Div(
                                        id=f"{id_prefix}-viewport-info",
                                        className="small text-muted",
                                    ),
                                    # Include invisible div that updates with window size
                                    html.Div(
                                        id=f"{id_prefix}-window-size",
                                        style={"display": "none"},
                                    ),
                                ]
                            ),
                        ]
                    ),
                    className="mt-1",
                ),
                id=f"{id_prefix}-collapse",
                is_open=False,
            ),
            # JS to track window size
            dcc.Interval(id=f"{id_prefix}-interval", interval=500, n_intervals=0),
            html.Div(id=f"{id_prefix}-output-clientside"),
        ]
    )


def create_clientside_callback(app, id_prefix="mobile-view"):
    """
    Create the clientside callback to track viewport size

    Args:
        app: The Dash app instance
        id_prefix: The prefix used for component IDs

    Returns:
        None
    """
    clientside_function = """
    function(n_intervals) {
        var width = window.innerWidth;
        var height = window.innerHeight;
        
        document.getElementById("{id_prefix}-viewport-info").innerText = 
            "Viewport size: " + width + " × " + height + "px";
            
        return JSON.stringify({width: width, height: height});
    }
    """.replace("{id_prefix}", id_prefix)

    app.clientside_callback(
        clientside_function,
        output=f"#{id_prefix}-window-size.children",
        inputs=[f"#{id_prefix}-interval.n_intervals"],
    )
