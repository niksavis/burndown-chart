import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import io
import base64

# Default values
DEFAULT_PERT_FACTOR = 3
DEFAULT_TOTAL_ITEMS = 100
DEFAULT_TOTAL_POINTS = 1000
DEFAULT_DEADLINE = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")

# Sample data
SAMPLE_DATA = pd.DataFrame(
    {
        "date": [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(10, 0, -1)
        ],
        "no_items": [5, 7, 3, 6, 4, 8, 5, 6, 7, 4],
        "no_points": [50, 70, 30, 60, 40, 80, 50, 60, 70, 40],
    }
)

# Help text definitions
HELP_TEXTS = {
    "app_intro": """
        This application helps you forecast project completion based on historical progress. 
        It uses the PERT methodology to estimate when your project will be completed based on 
        optimistic, pessimistic, and most likely scenarios.
    """,
    "pert_factor": """
        The PERT factor determines how many data points to use for optimistic and pessimistic estimates.
        A higher value considers more historical data points for calculating scenarios.
        Range: 3-15 (default: 3)
    """,
    "deadline": """
        Set your project deadline here. The app will show if you're on track to meet it.
        Format: YYYY-MM-DD
    """,
    "total_items": """
        The total number of items (tasks, stories, etc.) to be completed in your project.
        This represents work quantity.
    """,
    "total_points": """
        The total number of points (effort, complexity) to be completed.
        This represents work effort/complexity.
    """,
    "csv_format": """
        Your CSV file should contain the following columns:
        - date: Date of work completed (YYYY-MM-DD format)
        - no_items: Number of items completed on that date
        - no_points: Number of points completed on that date
        
        The file can use semicolon (;) or comma (,) as separators.
        Example:
        date;no_items;no_points
        2025-03-01;5;50
        2025-03-02;7;70
    """,
    "statistics_table": """
        This table shows your historical data. You can:
        - Edit any cell by clicking on it
        - Delete rows with the 'x' button
        - Add new rows with the 'Add Row' button
        - Sort by clicking column headers
        
        Changes to this data will update the forecast immediately.
    """,
    "forecast_explanation": """
        The graph shows your burndown forecast based on historical data:
        - Solid lines: Historical progress
        - Dashed lines: Most likely forecast
        - Dotted lines: Optimistic and pessimistic forecasts
        - Blue/Green lines: Items tracking
        - Orange/Yellow lines: Points tracking
        - Red vertical line: Your deadline
        
        Where the forecast lines cross the zero line indicates estimated completion dates.
    """,
}


def read_and_clean_data(df):
    """Clean and prepare the dataframe"""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["no_items"] = pd.to_numeric(df["no_items"], errors="coerce")
    df["no_points"] = pd.to_numeric(df["no_points"], errors="coerce")
    df.dropna(subset=["no_items", "no_points"], inplace=True)
    return df


def compute_cumulative_values(df, total_items, total_points):
    """Compute cumulative values for items and points"""
    df = df.copy()
    df["cum_items"] = df["no_items"][::-1].cumsum()[::-1] + total_items
    df["cum_points"] = df["no_points"][::-1].cumsum()[::-1] + total_points
    return df


def compute_weekly_throughput(df):
    """Compute weekly throughput from daily data"""
    df = df.copy()
    # Convert string dates back to datetime for calculations
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-{r['week']}", axis=1)

    grouped = (
        df.groupby("year_week")
        .agg({"no_items": "sum", "no_points": "sum"})
        .reset_index()
    )

    return grouped


def calculate_rates(grouped, total_items, total_points, pert_factor):
    """Calculate burn rates using PERT method"""
    days_per_week = 7.0

    # Ensure pert_factor is not larger than available data
    pert_factor = min(pert_factor, len(grouped) // 2) if len(grouped) > 0 else 1
    pert_factor = max(pert_factor, 1)  # Ensure at least 1

    if len(grouped) == 0:
        return 0, 0, 0, 0, 0, 0

    # Calculate rates
    optimistic_items_rate = (
        grouped["no_items"].nlargest(pert_factor).mean() / days_per_week
    )
    pessimistic_items_rate = (
        grouped["no_items"].nsmallest(pert_factor).mean() / days_per_week
    )
    most_likely_items_rate = grouped["no_items"].mean() / days_per_week

    optimistic_points_rate = (
        grouped["no_points"].nlargest(pert_factor).mean() / days_per_week
    )
    pessimistic_points_rate = (
        grouped["no_points"].nsmallest(pert_factor).mean() / days_per_week
    )
    most_likely_points_rate = grouped["no_points"].mean() / days_per_week

    # Calculate time estimates
    optimistic_time_items = (
        total_items / optimistic_items_rate if optimistic_items_rate else float("inf")
    )
    most_likely_time_items = (
        total_items / most_likely_items_rate if most_likely_items_rate else float("inf")
    )
    pessimistic_time_items = (
        total_items / pessimistic_items_rate if pessimistic_items_rate else float("inf")
    )

    optimistic_time_points = (
        total_points / optimistic_points_rate
        if optimistic_points_rate
        else float("inf")
    )
    most_likely_time_points = (
        total_points / most_likely_points_rate
        if most_likely_points_rate
        else float("inf")
    )
    pessimistic_time_points = (
        total_points / pessimistic_points_rate
        if pessimistic_points_rate
        else float("inf")
    )

    # PERT formula
    pert_time_items = (
        optimistic_time_items + 4 * most_likely_time_items + pessimistic_time_items
    ) / 6
    pert_time_points = (
        optimistic_time_points + 4 * most_likely_time_points + pessimistic_time_points
    ) / 6

    return (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    )


def daily_forecast(start_val, daily_rate, start_date):
    """Generate daily forecast values"""
    if daily_rate <= 0:
        return [start_date], [start_val]

    x_vals, y_vals = [], []
    val = start_val
    current_date = start_date

    while val > 0:
        x_vals.append(current_date)
        y_vals.append(val)
        val -= daily_rate
        current_date += timedelta(days=1)

    x_vals.append(current_date)
    y_vals.append(0)

    return x_vals, y_vals


def create_forecast_plot(df, total_items, total_points, pert_factor, deadline_str):
    """Create forecast plot with aligned y-axes"""

    # Ensure proper date format
    deadline = pd.to_datetime(deadline_str)

    # Convert string dates back to datetime for calculations
    df_calc = df.copy()
    df_calc["date"] = pd.to_datetime(df_calc["date"])

    # Compute weekly throughput
    grouped = compute_weekly_throughput(df_calc)

    # Calculate rates
    (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    ) = calculate_rates(grouped, total_items, total_points, pert_factor)

    # Compute daily rates
    items_daily_rate = (
        total_items / pert_time_items
        if pert_time_items > 0 and pert_time_items != float("inf")
        else 0
    )
    points_daily_rate = (
        total_points / pert_time_points
        if pert_time_points > 0 and pert_time_points != float("inf")
        else 0
    )

    # Get starting points for forecast
    start_date = df_calc["date"].iloc[-1] if not df_calc.empty else datetime.now()
    last_items = df_calc["cum_items"].iloc[-1] if not df_calc.empty else total_items
    last_points = df_calc["cum_points"].iloc[-1] if not df_calc.empty else total_points

    # Forecast lines for items
    items_x_avg, items_y_avg = daily_forecast(last_items, items_daily_rate, start_date)
    items_x_opt, items_y_opt = daily_forecast(
        last_items, optimistic_items_rate, start_date
    )
    items_x_pes, items_y_pes = daily_forecast(
        last_items, pessimistic_items_rate, start_date
    )

    # Forecast lines for points
    points_x_avg, points_y_avg = daily_forecast(
        last_points, points_daily_rate, start_date
    )
    points_x_opt, points_y_opt = daily_forecast(
        last_points, optimistic_points_rate, start_date
    )
    points_x_pes, points_y_pes = daily_forecast(
        last_points, pessimistic_points_rate, start_date
    )

    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # UPDATED COLORS FOR BETTER VISIBILITY

    # Historical items
    fig.add_trace(
        go.Scatter(
            x=df_calc["date"],
            y=df_calc["cum_items"],
            mode="lines+markers",
            name="Items History",
            line=dict(color="rgb(0, 99, 178)", width=3),  # Darker blue
            marker=dict(size=8, color="rgb(0, 99, 178)"),
            hovertemplate="%{x}<br>Items: %{y}",
            visible=True,
        ),
        secondary_y=False,
    )

    # Forecast (Items)
    fig.add_trace(
        go.Scatter(
            x=items_x_avg,
            y=items_y_avg,
            mode="lines",
            name="Items Forecast (Most Likely)",
            line=dict(color="rgb(0, 99, 178)", dash="dash", width=2),
            hovertemplate="%{x}<br>Items: %{y}",
            visible=True,
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=items_x_opt,
            y=items_y_opt,
            mode="lines",
            name="Items Forecast (Optimistic)",
            line=dict(color="rgb(0, 128, 0)", dash="dot", width=2),  # Green
            hovertemplate="%{x}<br>Items: %{y}",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=items_x_pes,
            y=items_y_pes,
            mode="lines",
            name="Items Forecast (Pessimistic)",
            line=dict(
                color="rgb(128, 0, 128)", dash="dot", width=2
            ),  # Purple - changed from red
            hovertemplate="%{x}<br>Items: %{y}",
        ),
        secondary_y=False,
    )

    # Historical points
    fig.add_trace(
        go.Scatter(
            x=df_calc["date"],
            y=df_calc["cum_points"],
            mode="lines+markers",
            name="Points History",
            line=dict(color="rgb(255, 127, 14)", width=3),  # Orange
            marker=dict(size=8, color="rgb(255, 127, 14)"),
            hovertemplate="%{x}<br>Points: %{y}",
        ),
        secondary_y=True,
    )

    # Forecast (Points)
    fig.add_trace(
        go.Scatter(
            x=points_x_avg,
            y=points_y_avg,
            mode="lines",
            name="Points Forecast (Most Likely)",
            line=dict(color="rgb(255, 127, 14)", dash="dash", width=2),
            hovertemplate="%{x}<br>Points: %{y}",
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=points_x_opt,
            y=points_y_opt,
            mode="lines",
            name="Points Forecast (Optimistic)",
            line=dict(
                color="rgb(184, 134, 11)", dash="dot", width=2
            ),  # Darker yellow/gold
            hovertemplate="%{x}<br>Points: %{y}",
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=points_x_pes,
            y=points_y_pes,
            mode="lines",
            name="Points Forecast (Pessimistic)",
            line=dict(
                color="rgb(165, 42, 42)", dash="dot", width=2
            ),  # Brown instead of red
            hovertemplate="%{x}<br>Points: %{y}",
        ),
        secondary_y=True,
    )

    # Calculate max values for both y-axes
    max_items = max(
        df_calc["cum_items"].max() if not df_calc.empty else total_items,
        max(items_y_avg + items_y_opt + items_y_pes),
    )
    max_points = max(
        df_calc["cum_points"].max() if not df_calc.empty else total_points,
        max(points_y_avg + points_y_opt + points_y_pes),
    )

    # Add deadline line - Changed to a more visible bright red
    fig.add_shape(
        type="line",
        x0=deadline,
        x1=deadline,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(
            color="rgb(220, 20, 60)", dash="dash", width=3
        ),  # Crimson red, thicker
    )

    # Deadline annotation at the top of the line
    fig.add_annotation(
        x=deadline,
        y=1,
        yref="paper",
        text="Deadline",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40,
        font=dict(
            color="rgb(220, 20, 60)", size=14, family="Arial, sans-serif"
        ),  # Matching red
    )

    # KEY SOLUTION: Align starting points while keeping raw y-axis values
    # Get the proportion between the two starting values
    proportion = last_points / last_items if last_items > 0 else 1

    # Calculate scale factor to align visually
    scale_factor = max_points / max_items

    # Set y-axis ranges to maintain alignment
    items_range = [0, max_items * 1.1]
    points_range = [0, max_items * scale_factor * 1.1]

    # Update layout - REMOVED TITLE to avoid overlap with legend
    fig.update_layout(
        xaxis=dict(
            title={"text": "Date", "font": {"size": 16}},
            tickmode="auto",
            nticks=20,
            gridcolor="lightgray",
            automargin=True,
        ),
        yaxis=dict(
            title={"text": "Remaining Items", "font": {"size": 16}},
            range=items_range,
            gridcolor="lightgray",
            zeroline=True,
            zerolinecolor="black",
        ),
        yaxis2=dict(
            title={"text": "Remaining Points", "font": {"size": 16}},
            overlaying="y",
            side="right",
            range=points_range,  # Use calculated range to align
            gridcolor="lightgray",
            zeroline=True,
            zerolinecolor="black",
        ),
        # Adjusted legend position
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.0,
            xanchor="center",
            x=0.5,
            font={"size": 12},
            bgcolor="rgba(255, 255, 255, 0.8)",  # Semi-transparent background
            bordercolor="lightgray",
            borderwidth=1,
        ),
        hovermode="closest",
        margin=dict(r=70, l=70, t=80, b=70),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif"},
    )

    return fig, pert_time_items, pert_time_points


# Create info icon with tooltip
def create_info_tooltip(id_suffix, help_text):
    return html.Div(
        [
            html.I(
                className="fas fa-info-circle text-info ml-2",
                id=f"info-tooltip-{id_suffix}",
                style={"cursor": "pointer", "margin-left": "5px"},
            ),
            dbc.Tooltip(
                help_text,
                target=f"info-tooltip-{id_suffix}",
                placement="right",
                style={"max-width": "300px"},
            ),
        ],
        style={"display": "inline-block"},
    )


# Create Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",  # Font Awesome for icons
    ],
)

# Define layout with reorganized components
app.layout = dbc.Container(
    [
        # Sticky Help Button in top-right corner
        html.Div(
            [
                dbc.Button(
                    [
                        html.I(className="fas fa-question-circle mr-2"),
                        "How to Use This App",
                    ],
                    id="help-button",
                    color="info",
                    size="sm",
                    className="shadow",
                ),
            ],
            style={
                "position": "fixed",
                "top": "20px",
                "right": "20px",
                "zIndex": "1000",  # Ensure it stays on top of other elements
            },
        ),
        # App header
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Project Burndown Forecast", className="text-center my-4"
                        ),
                    ],
                    width=12,
                ),
            ]
        ),
        # Help modal with better structure
        dbc.Modal(
            [
                dbc.ModalHeader("How to Use the Project Burndown Forecast App"),
                dbc.ModalBody(
                    [
                        # Overview section
                        html.Div(
                            [
                                html.H5(
                                    "Overview", className="border-bottom pb-2 mb-3"
                                ),
                                html.P(HELP_TEXTS["app_intro"], className="ml-3"),
                            ],
                            className="mb-4",
                        ),
                        # Input Parameters section
                        html.Div(
                            [
                                html.H5(
                                    "Input Parameters",
                                    className="border-bottom pb-2 mb-3",
                                ),
                                html.Table(
                                    [
                                        html.Tbody(
                                            [
                                                html.Tr(
                                                    [
                                                        html.Td(
                                                            "PERT Factor:",
                                                            className="font-weight-bold pr-3 align-top",
                                                        ),
                                                        html.Td(
                                                            HELP_TEXTS["pert_factor"]
                                                        ),
                                                    ],
                                                    className="border-bottom",
                                                ),
                                                html.Tr(
                                                    [
                                                        html.Td(
                                                            "Deadline:",
                                                            className="font-weight-bold pr-3 align-top",
                                                        ),
                                                        html.Td(HELP_TEXTS["deadline"]),
                                                    ],
                                                    className="border-bottom",
                                                ),
                                                html.Tr(
                                                    [
                                                        html.Td(
                                                            "Total Items:",
                                                            className="font-weight-bold pr-3 align-top",
                                                        ),
                                                        html.Td(
                                                            HELP_TEXTS["total_items"]
                                                        ),
                                                    ],
                                                    className="border-bottom",
                                                ),
                                                html.Tr(
                                                    [
                                                        html.Td(
                                                            "Total Points:",
                                                            className="font-weight-bold pr-3 align-top",
                                                        ),
                                                        html.Td(
                                                            HELP_TEXTS["total_points"]
                                                        ),
                                                    ]
                                                ),
                                            ]
                                        )
                                    ],
                                    className="table table-sm ml-3",
                                ),
                            ],
                            className="mb-4",
                        ),
                        # CSV Upload section
                        html.Div(
                            [
                                html.H5(
                                    "CSV Upload Format",
                                    className="border-bottom pb-2 mb-3",
                                ),
                                html.Div(
                                    [
                                        html.Pre(
                                            """date;no_items;no_points
2025-03-01;5;50
2025-03-02;7;70""",
                                            className="bg-light p-3 border rounded",
                                        ),
                                        html.P(
                                            HELP_TEXTS["csv_format"], className="mt-2"
                                        ),
                                    ],
                                    className="ml-3",
                                ),
                            ],
                            className="mb-4",
                        ),
                        # Statistics Table section
                        html.Div(
                            [
                                html.H5(
                                    "Working with the Statistics Table",
                                    className="border-bottom pb-2 mb-3",
                                ),
                                html.Div(
                                    [
                                        html.P(HELP_TEXTS["statistics_table"]),
                                        html.Div(
                                            [
                                                html.Div(
                                                    "Date: YYYY-MM-DD format",
                                                    className="mb-1",
                                                ),
                                                html.Div(
                                                    "Items: Number of work items completed",
                                                    className="mb-1",
                                                ),
                                                html.Div(
                                                    "Points: Effort points completed",
                                                    className="mb-1",
                                                ),
                                            ],
                                            className="bg-light p-3 border rounded",
                                        ),
                                    ],
                                    className="ml-3",
                                ),
                            ],
                            className="mb-4",
                        ),
                        # Understanding the Forecast Graph
                        html.Div(
                            [
                                html.H5(
                                    "Understanding the Forecast Graph",
                                    className="border-bottom pb-2 mb-3",
                                ),
                                html.Div(
                                    [
                                        html.P(
                                            HELP_TEXTS["forecast_explanation"],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "■",
                                                            className="mr-2",
                                                            style={
                                                                "color": "rgb(0, 99, 178)"
                                                            },
                                                        ),
                                                        "Blue: Items tracking",
                                                    ],
                                                    className="col-6 mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "■",
                                                            className="mr-2",
                                                            style={
                                                                "color": "rgb(255, 127, 14)"
                                                            },
                                                        ),
                                                        "Orange: Points tracking",
                                                    ],
                                                    className="col-6 mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "■",
                                                            className="mr-2",
                                                            style={
                                                                "color": "rgb(0, 128, 0)"
                                                            },
                                                        ),
                                                        "Green: Optimistic forecast",
                                                    ],
                                                    className="col-6 mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "■",
                                                            className="mr-2",
                                                            style={
                                                                "color": "rgb(128, 0, 128)"
                                                            },
                                                        ),
                                                        "Purple: Pessimistic forecast",
                                                    ],
                                                    className="col-6 mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "■",
                                                            className="mr-2",
                                                            style={
                                                                "color": "rgb(220, 20, 60)"
                                                            },
                                                        ),
                                                        "Red line: Deadline",
                                                    ],
                                                    className="col-6 mb-2",
                                                ),
                                            ],
                                            className="row bg-light p-3 border rounded",
                                        ),
                                    ],
                                    className="ml-3",
                                ),
                            ]
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-help", className="ml-auto")
                ),
            ],
            id="help-modal",
            size="lg",
        ),
        # REORGANIZED LAYOUT: First the large Forecast Graph
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.H4("Forecast Graph", className="d-inline"),
                                        create_info_tooltip(
                                            "forecast-graph",
                                            HELP_TEXTS["forecast_explanation"],
                                        ),
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id="forecast-graph",
                                            style={"height": "650px"},
                                        ),
                                    ]
                                ),
                            ],
                            className="mb-3 shadow-sm",
                        ),
                    ],
                    width=12,
                ),
            ]
        ),
        # Second row: Input Parameters and PERT Analysis side by side
        dbc.Row(
            [
                # Left column - Input Parameters
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.H4(
                                            "Input Parameters", className="d-inline"
                                        ),
                                        create_info_tooltip(
                                            "parameters",
                                            "Change these values to adjust your project forecast.",
                                        ),
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Label(
                                                            [
                                                                "PERT Factor:",
                                                                create_info_tooltip(
                                                                    "pert-factor",
                                                                    HELP_TEXTS[
                                                                        "pert_factor"
                                                                    ],
                                                                ),
                                                            ]
                                                        ),
                                                        dcc.Slider(
                                                            id="pert-factor-slider",
                                                            min=3,
                                                            max=15,
                                                            value=DEFAULT_PERT_FACTOR,
                                                            marks={
                                                                i: str(i)
                                                                for i in range(3, 16, 2)
                                                            },
                                                            step=1,
                                                        ),
                                                    ],
                                                    width=12,
                                                    lg=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Label(
                                                            [
                                                                "Deadline:",
                                                                create_info_tooltip(
                                                                    "deadline",
                                                                    HELP_TEXTS[
                                                                        "deadline"
                                                                    ],
                                                                ),
                                                            ]
                                                        ),
                                                        dcc.DatePickerSingle(
                                                            id="deadline-picker",
                                                            date=DEFAULT_DEADLINE,
                                                            display_format="YYYY-MM-DD",
                                                            className="form-control",
                                                        ),
                                                    ],
                                                    width=12,
                                                    lg=6,
                                                ),
                                            ]
                                        ),
                                        html.Br(),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Label(
                                                            [
                                                                "Total Items:",
                                                                create_info_tooltip(
                                                                    "total-items",
                                                                    HELP_TEXTS[
                                                                        "total_items"
                                                                    ],
                                                                ),
                                                            ]
                                                        ),
                                                        dbc.Input(
                                                            id="total-items-input",
                                                            type="number",
                                                            value=DEFAULT_TOTAL_ITEMS,
                                                            min=0,
                                                            step=1,
                                                        ),
                                                    ],
                                                    width=12,
                                                    lg=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Label(
                                                            [
                                                                "Total Points:",
                                                                create_info_tooltip(
                                                                    "total-points",
                                                                    HELP_TEXTS[
                                                                        "total_points"
                                                                    ],
                                                                ),
                                                            ]
                                                        ),
                                                        dbc.Input(
                                                            id="total-points-input",
                                                            type="number",
                                                            value=DEFAULT_TOTAL_POINTS,
                                                            min=0,
                                                            step=1,
                                                        ),
                                                    ],
                                                    width=12,
                                                    lg=6,
                                                ),
                                            ]
                                        ),
                                        html.Br(),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Label(
                                                            [
                                                                "Upload Statistics CSV:",
                                                                create_info_tooltip(
                                                                    "csv-upload",
                                                                    HELP_TEXTS[
                                                                        "csv_format"
                                                                    ],
                                                                ),
                                                            ]
                                                        ),
                                                        dcc.Upload(
                                                            id="upload-data",
                                                            children=html.Div(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-file-upload mr-2"
                                                                    ),
                                                                    "Drag and Drop or ",
                                                                    html.A(
                                                                        "Select CSV File"
                                                                    ),
                                                                ]
                                                            ),
                                                            style={
                                                                "width": "100%",
                                                                "height": "60px",
                                                                "lineHeight": "60px",
                                                                "borderWidth": "1px",
                                                                "borderStyle": "dashed",
                                                                "borderRadius": "5px",
                                                                "textAlign": "center",
                                                                "margin": "10px 0",
                                                            },
                                                            multiple=False,
                                                        ),
                                                    ],
                                                    width=12,
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                            ],
                            className="mb-3 h-100 shadow-sm",
                        ),
                    ],
                    width=7,
                ),
                # Right column - PERT Analysis
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.H4("PERT Analysis", className="d-inline"),
                                        create_info_tooltip(
                                            "pert-info",
                                            "PERT (Program Evaluation and Review Technique) estimates project completion time based on optimistic, pessimistic, and most likely scenarios.",
                                        ),
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="pert-info-container",
                                            className="text-center",
                                        ),
                                    ]
                                ),
                            ],
                            className="mb-3 h-100 shadow-sm",
                        ),
                    ],
                    width=5,
                ),
            ]
        ),
        # Statistics Data Table row
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.H4(
                                            "Statistics Data", className="d-inline"
                                        ),
                                        create_info_tooltip(
                                            "statistics-data",
                                            HELP_TEXTS["statistics_table"],
                                        ),
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        dash_table.DataTable(
                                            id="statistics-table",
                                            columns=[
                                                {
                                                    "name": "Date (YYYY-MM-DD)",
                                                    "id": "date",
                                                    "type": "text",
                                                },
                                                {
                                                    "name": "Items Completed",
                                                    "id": "no_items",
                                                    "type": "numeric",
                                                },
                                                {
                                                    "name": "Points Completed",
                                                    "id": "no_points",
                                                    "type": "numeric",
                                                },
                                            ],
                                            data=SAMPLE_DATA.to_dict("records"),
                                            editable=True,
                                            row_deletable=True,
                                            sort_action="native",
                                            style_table={"overflowX": "auto"},
                                            style_cell={
                                                "textAlign": "center",
                                                "minWidth": "100px",
                                                "padding": "10px",
                                            },
                                            style_header={
                                                "backgroundColor": "#f8f9fa",
                                                "fontWeight": "bold",
                                                "border": "1px solid #ddd",
                                            },
                                            style_data={
                                                "border": "1px solid #ddd",
                                            },
                                            style_data_conditional=[
                                                {
                                                    "if": {"row_index": "odd"},
                                                    "backgroundColor": "#f9f9f9",
                                                }
                                            ],
                                            tooltip_data=[
                                                {
                                                    column: {
                                                        "value": "Click to edit",
                                                        "type": "text",
                                                    }
                                                    for column in [
                                                        "date",
                                                        "no_items",
                                                        "no_points",
                                                    ]
                                                }
                                                for _ in range(len(SAMPLE_DATA))
                                            ],
                                            tooltip_duration=None,
                                        ),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    [
                                                        html.I(
                                                            className="fas fa-plus mr-2"
                                                        ),
                                                        "Add Row",
                                                    ],
                                                    id="add-row-button",
                                                    color="primary",
                                                    className="mt-3",
                                                ),
                                            ],
                                            style={"textAlign": "center"},
                                        ),
                                    ]
                                ),
                            ],
                            className="shadow-sm",
                        ),
                    ],
                    width=12,
                ),
            ]
        ),
        # Footer
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Hr(),
                    ],
                    width=12,
                ),
            ],
            className="mt-4",
        ),
    ],
    fluid=True,
)


# Define callbacks
@app.callback(
    Output("statistics-table", "data"),
    [Input("add-row-button", "n_clicks"), Input("upload-data", "contents")],
    [State("statistics-table", "data"), State("upload-data", "filename")],
)
def update_table(n_clicks, contents, rows, filename):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "add-row-button":
        # Add a new empty row with date in YYYY-MM-DD format
        rows.append(
            {"date": datetime.now().strftime("%Y-%m-%d"), "no_items": 0, "no_points": 0}
        )
        return rows

    elif trigger_id == "upload-data" and contents:
        # Parse uploaded file
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        try:
            if "csv" in filename.lower():
                # Try semicolon separator first
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), sep=";")
                if (
                    "date" not in df.columns
                    or "no_items" not in df.columns
                    or "no_points" not in df.columns
                ):
                    # Try with comma separator
                    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

                # Clean data and ensure date is in YYYY-MM-DD format
                df = read_and_clean_data(df)
                return df.to_dict("records")
        except Exception as e:
            print(f"Error loading file: {e}")
            return rows

    return rows


@app.callback(
    [Output("forecast-graph", "figure"), Output("pert-info-container", "children")],
    [
        Input("pert-factor-slider", "value"),
        Input("total-items-input", "value"),
        Input("total-points-input", "value"),
        Input("deadline-picker", "date"),
        Input("statistics-table", "data"),
    ],
)
def update_graph_and_pert_info(
    pert_factor, total_items, total_points, deadline, table_data
):
    # Create dataframe from table data
    df = pd.DataFrame(table_data)

    # Process data for calculations
    df = compute_cumulative_values(df, total_items, total_points)

    # Create forecast plot and get PERT values
    fig, pert_time_items, pert_time_points = create_forecast_plot(
        df=df,
        total_items=total_items,
        total_points=total_points,
        pert_factor=pert_factor,
        deadline_str=deadline,
    )

    # Calculate days to deadline
    deadline_date = pd.to_datetime(deadline)
    days_to_deadline = (deadline_date - datetime.now()).days

    # Determine colors based on if we'll meet the deadline
    items_color = "green" if pert_time_items <= days_to_deadline else "red"
    points_color = "green" if pert_time_points <= days_to_deadline else "red"

    # Create PERT info HTML with formula in the table and improved styling
    pert_info = html.Div(
        [
            html.Table(
                [
                    html.Tbody(
                        [
                            # PERT formula as first row in the table
                            html.Tr(
                                [
                                    html.Td(
                                        "PERT Formula:",
                                        className="text-right pr-2",
                                        style={"font-weight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            dcc.Markdown(
                                                r"$E = \frac{O + 4M + P}{6}$",
                                                mathjax=True,
                                                style={"display": "inline-block"},
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Estimated Days (Items):",
                                        className="text-right pr-2",
                                        style={"font-weight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{pert_time_items:.1f}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "font-size": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={
                                            "color": items_color,
                                            "font-weight": "bold",
                                        },
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Estimated Days (Points):",
                                        className="text-right pr-2",
                                        style={"font-weight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{pert_time_points:.1f}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "font-size": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={
                                            "color": points_color,
                                            "font-weight": "bold",
                                        },
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Deadline in:",
                                        className="text-right pr-2",
                                        style={"font-weight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{days_to_deadline}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "font-size": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"font-weight": "bold"},
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        [
                                            html.P(
                                                [
                                                    "Green means on track to meet deadline, red means at risk. ",
                                                    "The PERT formula uses optimistic (O), most likely (M), and pessimistic (P) estimates.",
                                                ],
                                                className="mt-2 text-muted small",
                                                style={"text-align": "center"},
                                            )
                                        ],
                                        colSpan=2,
                                    )
                                ]
                            ),
                        ]
                    )
                ],
                className="table table-borderless",
                style={
                    "margin": "0 auto",
                    "width": "auto",
                    "border": "1px solid #eee",
                    "borderRadius": "5px",
                    "padding": "10px",
                },
            )
        ]
    )

    return fig, pert_info


# Help modal callbacks
@app.callback(
    Output("help-modal", "is_open"),
    [Input("help-button", "n_clicks"), Input("close-help", "n_clicks")],
    [State("help-modal", "is_open")],
)
def toggle_help_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
