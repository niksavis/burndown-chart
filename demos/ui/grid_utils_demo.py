"""
Grid Utils Demo Application

This script demonstrates and validates the usage of the grid_utils module.
To run this demo, execute: python demos/ui/grid_utils_demo.py
"""

# Add the project root to the path so we can import properly
import sys
from pathlib import Path

# Add the project root to the Python path (two levels up from demos/ui/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import required modules
from dash import Dash, html
import dash_bootstrap_components as dbc

# Import the new grid utilities
from ui.grid_utils import (
    # Low-level functions
    create_responsive_row,
    create_responsive_column,
    create_two_column_layout,
    create_three_column_layout,
    create_content_sidebar_layout,
    create_dashboard_layout,
    # Specialized grid functions
    create_card_grid,
    create_form_row,
    create_responsive_table_wrapper,
    create_form_section,
    create_breakpoint_visibility_examples,
)

app = Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)


# Create a simple card for testing
def create_demo_card(title, content, color="primary"):
    return dbc.Card(
        [
            dbc.CardHeader(title),
            dbc.CardBody([html.P(content, className="card-text")]),
        ],
        className=f"border-{color}",
    )


# Create examples of all grid layouts
app.layout = html.Div(
    [
        html.H1("Grid Utils Demo", className="mb-4"),
        # Example 1: Breakpoint Visibility Test
        html.H2("Breakpoint Visibility Test", className="mb-3"),
        html.P("Resize your browser to see which breakpoints are active:"),
        create_breakpoint_visibility_examples(),
        html.Hr(className="my-5"),
        # Example 2: Simple Two Column Layout
        html.H2("Two Column Layout", className="mb-3"),
        create_two_column_layout(
            left_content=create_demo_card(
                "Left Column", "This content takes up 4 columns on md+ screens."
            ),
            right_content=create_demo_card(
                "Right Column",
                "This content takes up 8 columns on md+ screens.",
                "success",
            ),
            left_width=4,
            right_width=8,
            breakpoint="md",
        ),
        html.Hr(className="my-5"),
        # Example 3: Three Column Layout
        html.H2("Three Column Layout", className="mb-3"),
        create_three_column_layout(
            left=create_demo_card("Left", "3/12 width on lg+ screens."),
            middle=create_demo_card("Middle", "5/12 width on lg+ screens.", "info"),
            right=create_demo_card("Right", "4/12 width on lg+ screens.", "warning"),
            left_width=3,
            middle_width=5,
            right_width=4,
            breakpoint="lg",
        ),
        html.Hr(className="my-5"),
        # Example 4: Content Sidebar Layout
        html.H2("Content Sidebar Layout", className="mb-3"),
        create_content_sidebar_layout(
            content=create_demo_card(
                "Main Content",
                "This is the main content area that takes up most of the width.",
            ),
            sidebar=create_demo_card(
                "Sidebar",
                "This is the sidebar that will be on the right at larger screens.",
                "secondary",
            ),
            sidebar_position="right",
            sidebar_width=3,
            content_width=9,
            stack_until="lg",
        ),
        html.Hr(className="my-5"),
        # Example 5: Card Grid
        html.H2("Card Grid", className="mb-3"),
        html.P("A grid of cards that changes columns based on screen size:"),
        create_card_grid(
            cards=[
                create_demo_card(
                    f"Card {i + 1}",
                    f"This is card {i + 1} content.",
                    color=["primary", "success", "info", "warning", "danger"][i % 5],
                )
                for i in range(6)
            ],
            cols_by_breakpoint={"xs": 1, "sm": 2, "md": 3, "lg": 3},
            equal_height=True,
        ),
        html.Hr(className="my-5"),
        # Example 6: Dashboard Layout
        html.H2("Dashboard Layout", className="mb-3"),
        html.P(
            "A complex dashboard layout with main content, sidebar, and optional secondary content."
        ),
        create_dashboard_layout(
            main_content=create_demo_card(
                "Main Dashboard Area",
                "This is where your primary charts and visualizations would go.",
            ),
            side_content=create_demo_card(
                "Sidebar",
                "This area typically contains filters and controls.",
                "secondary",
            ),
            secondary_content=create_demo_card(
                "Secondary Content",
                "This content is only visible on xl+ screens. Try resizing your browser window.",
                "info",
            ),
            stack_until="md",
            main_width=8,
            side_width=4,
            secondary_display_breakpoint="xl",
        ),
        html.Hr(className="my-5"),
        # Example 7: Low-level responsive row example
        html.H2("Advanced Row Customization", className="mb-3"),
        html.P("Using low-level grid functions for maximum control:"),
        create_responsive_row(
            [
                create_responsive_column(
                    create_demo_card(
                        "Column 1", "Order changes at different breakpoints"
                    ),
                    xs=12,
                    md=4,
                    order_by_breakpoint={"xs": "3", "md": "1"},
                ),
                create_responsive_column(
                    create_demo_card(
                        "Column 2", "Order changes at different breakpoints", "success"
                    ),
                    xs=12,
                    md=4,
                    order_by_breakpoint={"xs": "1", "md": "2"},
                ),
                create_responsive_column(
                    create_demo_card(
                        "Column 3", "Order changes at different breakpoints", "danger"
                    ),
                    xs=12,
                    md=4,
                    order_by_breakpoint={"xs": "2", "md": "3"},
                ),
            ],
            row_class_by_breakpoint={"xs": "flex-column", "md": "flex-row"},
            alignment_by_breakpoint={
                "xs": "align-items-center",
                "md": "align-items-stretch",
            },
        ),
        html.Hr(className="my-5"),
        # Example 8: Form layout
        html.H2("Form Layout", className="mb-3"),
        create_form_section(
            title="User Information",
            help_text="Enter your personal information below.",
            components=[
                create_form_row(
                    [
                        html.Div(
                            [
                                html.Label("First Name"),
                                dbc.Input(type="text", placeholder="Enter first name"),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Last Name"),
                                dbc.Input(type="text", placeholder="Enter last name"),
                            ]
                        ),
                    ],
                    columns=[6, 6],
                ),
                create_form_row(
                    [
                        html.Div(
                            [
                                html.Label("Email"),
                                dbc.Input(type="email", placeholder="Enter email"),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Phone Number"),
                                dbc.Input(type="tel", placeholder="Enter phone number"),
                            ]
                        ),
                    ],
                    columns=[8, 4],
                ),
            ],
        ),
        html.Hr(className="my-5"),
        # Example 9: Table wrapper
        html.H2("Responsive Table", className="mb-3"),
        create_responsive_table_wrapper(
            dbc.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("ID", className="text-center"),
                                html.Th("Product Name"),
                                html.Th("Category"),
                                html.Th("Price"),
                                html.Th("Stock"),
                                html.Th("Actions"),
                            ]
                        )
                    ),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td("001", className="text-center"),
                                    html.Td("Product Alpha"),
                                    html.Td("Electronics"),
                                    html.Td("$299.99"),
                                    html.Td("15"),
                                    html.Td(
                                        dbc.Button("View", color="primary", size="sm")
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td("002", className="text-center"),
                                    html.Td("Product Beta"),
                                    html.Td("Home & Kitchen"),
                                    html.Td("$149.50"),
                                    html.Td("24"),
                                    html.Td(
                                        dbc.Button("View", color="primary", size="sm")
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td("003", className="text-center"),
                                    html.Td("Product Gamma"),
                                    html.Td("Office Supplies"),
                                    html.Td("$89.99"),
                                    html.Td("7"),
                                    html.Td(
                                        dbc.Button("View", color="primary", size="sm")
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True,
            )
        ),
    ],
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "20px"},
)

if __name__ == "__main__":
    print("Starting Grid Utils Demo server on http://127.0.0.1:8050/")
    app.run(debug=True)
