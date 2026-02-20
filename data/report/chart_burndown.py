"""Burndown and weekly breakdown chart generators."""

import json
from datetime import datetime


def generate_burndown_chart(
    burndown_metrics: dict,
    milestone: str,
    forecast_date: str,
    deadline: str,
    show_points: bool = False,
    statistics: list[dict] | None = None,
    pert_factor: int = 3,
) -> str:
    """Generate Chart.js script for burndown chart with forecasts and milestone/forecast/deadline lines.

    Args:
        burndown_metrics: Historical burndown data
        milestone: Milestone date string
        forecast_date: Forecast completion date string
        deadline: Deadline date string
        show_points: Whether to show points data
        statistics: Statistics data for forecast generation
        pert_factor: PERT factor for forecast calculations
    """
    historical = burndown_metrics.get("historical_data", {})
    dates = historical.get("dates", [])

    # Convert dates from YYYY-MM-DD to ISO week format (2026-W07)
    from datetime import datetime

    import pandas as pd

    iso_week_dates = []
    for date_str in dates:
        try:
            dt = pd.to_datetime(date_str)
            year, week, _ = dt.isocalendar()
            iso_week_dates.append(f"{year}-W{week:02d}")
        except Exception:
            iso_week_dates.append(date_str)  # Fallback to original

    dates_js = json.dumps(iso_week_dates)
    items = historical.get("remaining_items", [])
    points = historical.get("remaining_points", [])

    # Calculate label positions based on chronological order to prevent overlap
    # Format annotations with human-readable dates on second line
    date_labels = []
    if milestone:
        try:
            dt = datetime.strptime(milestone, "%Y-%m-%d")
            year, week, _ = dt.isocalendar()
            week_str = f"{year}-W{week:02d}"
            readable_date = dt.strftime("%b %d, %Y")
            date_labels.append(
                (
                    "milestone",
                    week_str,
                    f"Milestone\\n{readable_date}",
                    "#ffc107",
                    "#000",
                    3,
                    [10, 5],
                )
            )
        except Exception:
            date_labels.append(
                ("milestone", milestone, "Milestone", "#ffc107", "#000", 3, [10, 5])
            )
    if forecast_date:
        try:
            dt = datetime.strptime(forecast_date, "%Y-%m-%d")
            year, week, _ = dt.isocalendar()
            week_str = f"{year}-W{week:02d}"
            readable_date = dt.strftime("%b %d, %Y")
            date_labels.append(
                (
                    "forecast",
                    week_str,
                    f"Forecast\\n{readable_date}",
                    "#198754",
                    "#fff",
                    2,
                    [5, 5],
                )
            )
        except Exception:
            date_labels.append(
                ("forecast", forecast_date, "Forecast", "#198754", "#fff", 2, [5, 5])
            )
    if deadline:
        try:
            dt = datetime.strptime(deadline, "%Y-%m-%d")
            year, week, _ = dt.isocalendar()
            week_str = f"{year}-W{week:02d}"
            readable_date = dt.strftime("%b %d, %Y")
            date_labels.append(
                (
                    "deadline",
                    week_str,
                    f"Deadline\\n{readable_date}",
                    "#dc3545",
                    "#fff",
                    2,
                    [],
                )
            )
        except Exception:
            date_labels.append(
                ("deadline", deadline, "Deadline", "#dc3545", "#fff", 2, [])
            )

    # Assign yAdjust values: space labels 30px apart starting from top (-90, -60, -30, 0...)
    # Start from -90 to ensure no overlap with chart area
    base_y = -90
    spacing = 30

    annotations = {}
    for idx, (key, date_str, label, border_color, text_color, width, dash) in enumerate(
        date_labels
    ):
        y_adjust = base_y + (idx * spacing)
        dash_str = f"[{', '.join(map(str, dash))}]" if dash else "[]"

        annotations[key] = f"""{{
            type: 'line',
            xMin: '{date_str}',
            xMax: '{date_str}',
            borderColor: '{border_color}',
            borderWidth: {width},
            borderDash: {dash_str},
            label: {{
                display: true,
                content: '{label}',
                position: 'start',
                yAdjust: {y_adjust},
                backgroundColor: '{border_color}',
                color: '{text_color}'
            }}
        }}"""

    annotations_js = ",\n                ".join(
        [f"{key}: {value}" for key, value in annotations.items()]
    )

    datasets = [
        {
            "label": "Remaining Items",
            "data": items,
            "borderColor": "#0d6efd",
            "backgroundColor": "rgba(13, 110, 253, 0.7)",
            "tension": 0.4,
            "borderWidth": 2,
            "yAxisID": "y",
        }
    ]

    if show_points:
        datasets.append(
            {
                "label": "Remaining Points",
                "data": points,
                "borderColor": "#fd7e14",
                "backgroundColor": "rgba(253, 126, 20, 0.7)",
                "tension": 0.4,
                "borderWidth": 2,
                "yAxisID": "y1",
            }
        )

    datasets_js = json.dumps(datasets)

    scales_config = {
        "x": {
            "grid": {"display": False},
            "ticks": {"maxRotation": 45, "minRotation": 45},
        },
        "y": {
            "type": "linear",
            "display": True,
            "position": "left",
            "title": {"display": True, "text": "Items"},
            "grid": {"color": "#e9ecef"},
        },
    }

    if show_points:
        scales_config["y1"] = {
            "type": "linear",
            "display": True,
            "position": "right",
            "title": {"display": True, "text": "Points"},
            "grid": {"drawOnChartArea": False},
        }

    scales_js = json.dumps(scales_config)

    return f"""
    (function() {{
        const ctx = document.getElementById('burndownChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {dates_js},
                    datasets: {datasets_js}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    scales: {scales_js},
                    plugins: {{
                        legend: {{ display: true, position: 'top' }},
                        annotation: {{
                            annotations: {{
                                {annotations_js}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def generate_weekly_breakdown_chart(
    weekly_data: list[dict],
    show_points: bool = False,
    statistics: list[dict] | None = None,
    pert_factor: int = 3,
    deadline: str | None = None,
    remaining_items: float | None = None,
    remaining_points: float | None = None,
) -> str:
    """
    Generate Chart.js script for weekly breakdown showing completed items/points with forecasts and targets.

    Shows:
    - Weekly completed bars (items and optionally points)
    - PERT forecast bars for next week (semi-transparent)
    - EWMA forecast markers (triangles)
    - Required velocity reference lines (if deadline provided)

    Args:
        weekly_data: List of weekly breakdown dictionaries
        show_points: Whether to include points data
        statistics: Full statistics data for forecast calculations
        pert_factor: PERT factor for forecast calculations
        deadline: Deadline date string (YYYY-MM-DD) for required velocity
        remaining_items: Remaining items for required velocity calculation
        remaining_points: Remaining points for required velocity calculation

    Returns:
        Chart.js initialization script
    """

    dates = [week["date"] for week in weekly_data]
    dates_js = json.dumps(dates)
    items_completed = [week["completed_items"] for week in weekly_data]
    points_completed = [week.get("completed_points", 0) for week in weekly_data]

    # Generate forecasts if statistics data available
    forecast_items = None
    forecast_points = None
    ewma_items = None
    ewma_points = None

    if statistics and len(statistics) > 0:
        try:
            from data.metrics.forecast_calculator import calculate_ewma_forecast
            from data.processing import generate_weekly_forecast

            # Check if statistics has required columns for forecast
            has_required_data = all(
                key in statistics[0] for key in ["date", "completed_items"]
            )
            has_points_data = (
                "completed_points" in statistics[0] if statistics else False
            )

            if has_required_data:
                # Generate PERT forecast
                forecast_data = generate_weekly_forecast(
                    statistics, pert_factor=pert_factor
                )
                if forecast_data["items"]["dates"]:
                    # Convert forecast date to week format to match historical data
                    next_date = forecast_data["items"].get("next_date")
                    if next_date and hasattr(next_date, "isocalendar"):
                        year, week, _ = next_date.isocalendar()
                        week_str = f"{year}-W{week:02d}"
                    else:
                        week_str = forecast_data["items"]["dates"][0]

                    forecast_items = {
                        "date": week_str,
                        "most_likely": round(
                            forecast_data["items"]["most_likely"][0], 1
                        ),
                    }

                if show_points and has_points_data and forecast_data["points"]["dates"]:
                    # Convert forecast date to week format to match historical data
                    next_date = forecast_data["points"].get("next_date")
                    if next_date and hasattr(next_date, "isocalendar"):
                        year, week, _ = next_date.isocalendar()
                        week_str = f"{year}-W{week:02d}"
                    else:
                        week_str = forecast_data["points"]["dates"][0]

                    forecast_points = {
                        "date": week_str,
                        "most_likely": round(
                            forecast_data["points"]["most_likely"][0], 1
                        ),
                    }

                # Generate EWMA forecast
                ewma_data = calculate_ewma_forecast(items_completed, alpha=0.3)
                if ewma_data:
                    ewma_items = round(ewma_data["forecast_value"], 1)

                if show_points and has_points_data:
                    ewma_data_points = calculate_ewma_forecast(
                        points_completed, alpha=0.3
                    )
                    if ewma_data_points:
                        ewma_points = round(ewma_data_points["forecast_value"], 1)
        except (KeyError, ValueError, IndexError):
            # If forecast generation fails, continue without forecasts
            pass

    # Calculate required velocity if deadline provided
    required_items = None
    required_points = None
    if deadline and remaining_items is not None and remaining_items > 0:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            # Use last week date as reference
            last_week_str = weekly_data[-1]["date"]
            # Parse the week string (format: "YYYY-WXX")
            year, week = last_week_str.split("-W")
            # Approximate the last date (end of that week)
            last_date = datetime.strptime(f"{year}-W{week}-0", "%Y-W%W-%w")

            weeks_remaining = max(1, (deadline_date - last_date).days / 7)
            required_items = round(remaining_items / weeks_remaining, 1)

            if show_points and remaining_points is not None and remaining_points > 0:
                required_points = round(remaining_points / weeks_remaining, 1)
        except (ValueError, ZeroDivisionError):
            pass  # Skip if date parsing fails

    # Build datasets with explicit order (lower order = rendered on top)
    # Bars get order 2, lines get order 0 (render on top)
    datasets = [
        {
            "type": "bar",
            "label": "Items Completed",
            "data": items_completed,
            "backgroundColor": "#0d6efd",
            "yAxisID": "y",
            "order": 2,  # Bars in back
        }
    ]

    # Add points bar if enabled
    if show_points:
        datasets.append(
            {
                "type": "bar",
                "label": "Points Completed",
                "data": points_completed,
                "backgroundColor": "#fd7e14",
                "yAxisID": "y1",
                "order": 2,  # Bars in back
            }
        )

    # Add required velocity lines with order 0 (render on top of bars)
    # Use distinct colors: violet for items, red for points (not blue/orange like bars)
    if required_items:
        required_items_data = [required_items] * len(items_completed)
        # Extend for forecast if available
        if forecast_items:
            required_items_data.append(required_items)
        datasets.append(
            {
                "type": "line",
                "label": f"Required: {required_items:.1f} items/week",
                "data": required_items_data,
                "borderColor": "#8b5cf6",  # Violet
                "borderWidth": 3,
                "borderDash": [8, 4],
                "fill": False,
                "yAxisID": "y",
                "pointRadius": 0,
                "order": 0,  # Lines on top
            }
        )

    if show_points and required_points:
        required_points_data = [required_points] * len(points_completed)
        # Extend for forecast if available
        if forecast_points:
            required_points_data.append(required_points)
        datasets.append(
            {
                "type": "line",
                "label": f"Required: {required_points:.1f} points/week",
                "data": required_points_data,
                "borderColor": "#dc2626",  # Red
                "borderWidth": 3,
                "borderDash": [8, 4],
                "fill": False,
                "yAxisID": "y1",
                "pointRadius": 0,
                "order": 0,  # Lines on top
            }
        )

    # Add PERT forecast bars if available
    if forecast_items:
        # Extend dates to include forecast
        forecast_dates = dates + [forecast_items["date"]]
        dates_js = json.dumps(forecast_dates)

        # Pad historical data with null for forecast position
        forecast_items_data = [None] * len(items_completed) + [
            forecast_items["most_likely"]
        ]
        datasets.append(
            {
                "type": "bar",
                "label": "PERT Forecast (Items)",
                "data": forecast_items_data,
                "backgroundColor": "rgba(13, 110, 253, 0.4)",
                "borderColor": "#0d6efd",
                "borderWidth": 2,
                "yAxisID": "y",
                "order": 2,
            }
        )

    if show_points and forecast_points:
        forecast_points_data = [None] * len(points_completed) + [
            forecast_points["most_likely"]
        ]
        datasets.append(
            {
                "type": "bar",
                "label": "PERT Forecast (Points)",
                "data": forecast_points_data,
                "backgroundColor": "rgba(253, 126, 20, 0.4)",
                "borderColor": "#fd7e14",
                "borderWidth": 2,
                "yAxisID": "y1",
                "order": 2,
            }
        )

    # Add EWMA forecast markers if available
    # Use array-based positioning to align with forecast bars
    if ewma_items and forecast_items:
        # Pad with nulls to align with forecast position in extended dates array
        ewma_items_data = [None] * len(items_completed) + [ewma_items]
        datasets.append(
            {
                "type": "scatter",
                "label": "EWMA Forecast (Items)",
                "data": ewma_items_data,
                "backgroundColor": "#0d6efd",  # Blue to match items bars
                "pointRadius": 8,
                "pointStyle": "triangle",
                "yAxisID": "y",
                "order": 1,
            }
        )

    if show_points and ewma_points and forecast_points:
        # Pad with nulls to align with forecast position in extended dates array
        ewma_points_data = [None] * len(points_completed) + [ewma_points]
        datasets.append(
            {
                "type": "scatter",
                "label": "EWMA Forecast (Points)",
                "data": ewma_points_data,
                "backgroundColor": "#fd7e14",  # Orange to match points bars
                "pointRadius": 8,
                "pointStyle": "triangle",
                "yAxisID": "y1",
                "order": 1,
            }
        )

    datasets_js = json.dumps(datasets)

    # Configure scales
    scales_config = {
        "x": {
            "grid": {"display": False},
            "ticks": {"maxRotation": 45, "minRotation": 45},
        },
        "y": {
            "type": "linear",
            "display": True,
            "position": "left",
            "title": {"display": True, "text": "Items"},
            "grid": {"color": "#e9ecef"},
        },
    }

    if show_points:
        scales_config["y1"] = {
            "type": "linear",
            "display": True,
            "position": "right",
            "title": {"display": True, "text": "Points"},
            "grid": {"drawOnChartArea": False},
        }

    scales_js = json.dumps(scales_config)

    return f"""
    (function() {{
        const ctx = document.getElementById('weeklyBreakdownChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {dates_js},
                    datasets: {datasets_js}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    scales: {scales_js},
                    plugins: {{
                        legend: {{ 
                            display: true, 
                            position: 'bottom',
                            labels: {{
                                boxWidth: 12,
                                padding: 8,
                                font: {{ size: 11 }}
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    const label = context[0].label;
                                    return label.includes('W') ? 'Week ' + label : 'Forecast: ' + label;
                                }},
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label) {{
                                        label += ': ';
                                    }}
                                    if (context.parsed.y !== null) {{
                                        label += context.parsed.y.toFixed(1);
                                    }}
                                    return label;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def generate_weekly_items_chart(
    weekly_data: list[dict],
    statistics: list[dict] | None = None,
    pert_factor: int = 3,
    deadline: str | None = None,
    remaining_items: float | None = None,
) -> str:
    """
    Generate Chart.js script for weekly items breakdown with forecasts.

    Separate chart focusing only on items for clarity.
    """
    if not weekly_data:
        return ""

    dates = [week["date"] for week in weekly_data]
    dates_js = json.dumps(dates)
    items_completed = [week["completed_items"] for week in weekly_data]

    # Calculate weighted 4-week moving average
    items_avg = []
    for i in range(len(items_completed)):
        if i < 3:
            items_avg.append(None)
        else:
            window = items_completed[i - 3 : i + 1]
            weights = [0.1, 0.2, 0.3, 0.4]
            w_avg = sum(w * v for w, v in zip(weights, window, strict=False))
            items_avg.append(round(w_avg, 1))

    # Generate forecasts
    forecast_items = None
    ewma_items = None

    if statistics and len(statistics) > 0:
        has_required_data = all(
            key in statistics[0] for key in ["date", "completed_items"]
        )
        if has_required_data:
            try:
                from data.metrics.forecast_calculator import calculate_ewma_forecast
                from data.processing import generate_weekly_forecast

                forecast_data = generate_weekly_forecast(
                    statistics, pert_factor=pert_factor
                )
                if forecast_data["items"]["dates"]:
                    forecast_items = {
                        "date": forecast_data["items"]["dates"][0],
                        "most_likely": round(
                            forecast_data["items"]["most_likely"][0], 1
                        ),
                    }

                ewma_data = calculate_ewma_forecast(items_completed, alpha=0.3)
                if ewma_data:
                    ewma_items = round(ewma_data["forecast_value"], 1)
            except (KeyError, ValueError, IndexError):
                pass

    # Calculate required velocity
    required_items = None
    if deadline and remaining_items is not None and remaining_items > 0:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            last_week_str = weekly_data[-1]["date"]
            year, week = last_week_str.split("-W")
            last_date = datetime.strptime(f"{year}-W{week}-0", "%Y-W%W-%w")
            weeks_remaining = max(1, (deadline_date - last_date).days / 7)
            required_items = round(remaining_items / weeks_remaining, 1)
        except (ValueError, ZeroDivisionError):
            pass

    # Build datasets
    datasets = [
        {
            "type": "bar",
            "label": "Items Completed",
            "data": items_completed,
            "backgroundColor": "#0d6efd",
        }
    ]

    if any(v is not None for v in items_avg):
        datasets.append(
            {
                "type": "line",
                "label": "4-Week Weighted Avg",
                "data": items_avg,
                "borderColor": "#0047AB",
                "borderWidth": 3,
                "fill": False,
                "spanGaps": True,
                "pointRadius": 0,
            }
        )

    # Add forecast data if available
    if forecast_items:
        forecast_dates = dates + [forecast_items["date"]]
        forecast_dates_js = json.dumps(forecast_dates)
        forecast_data = [None] * len(items_completed) + [forecast_items["most_likely"]]
        datasets.append(
            {
                "type": "bar",
                "label": "PERT Forecast",
                "data": forecast_data,
                "backgroundColor": "rgba(13, 110, 253, 0.5)",
                "borderColor": "#0d6efd",
                "borderWidth": 2,
            }
        )
    else:
        forecast_dates_js = dates_js

    if ewma_items and forecast_items:
        ewma_data = [None] * len(items_completed) + [ewma_items]
        datasets.append(
            {
                "type": "scatter",
                "label": "EWMA Forecast",
                "data": ewma_data,
                "backgroundColor": "#6c757d",
                "pointRadius": 8,
                "pointStyle": "triangle",
            }
        )

    if required_items:
        required_data = [required_items] * (
            len(items_completed) + (1 if forecast_items else 0)
        )
        datasets.append(
            {
                "type": "line",
                "label": f"Required: {required_items:.1f}/week",
                "data": required_data,
                "borderColor": "#dc3545",
                "borderWidth": 2,
                "borderDash": [5, 5],
                "fill": False,
                "pointRadius": 0,
            }
        )

    datasets_js = json.dumps(datasets)

    return f"""
    (function() {{
        const ctx = document.getElementById('weeklyItemsChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {forecast_dates_js},
                    datasets: {datasets_js}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    scales: {{
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ maxRotation: 45, minRotation: 45 }}
                        }},
                        y: {{
                            type: 'linear',
                            title: {{ display: true, text: 'Items per Week' }},
                            grid: {{ color: '#e9ecef' }},
                        }}
                    }},
                    plugins: {{
                        legend: {{ 
                            display: true, 
                            position: 'bottom',
                            labels: {{
                                boxWidth: 12,
                                padding: 6,
                                font: {{ size: 11 }}
                            }}
                        }},
                        title: {{
                            display: true,
                            text: 'Weekly Items Completed with Forecasts',
                            font: {{ size: 14, weight: 'bold' }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    const label = context[0].label;
                                    return label.includes('W') ? 'Week ' + label : 'Forecast: ' + label;
                                }},
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label) {{ label += ': '; }}
                                    label += Math.round(context.parsed.y * 10) / 10;
                                    return label;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def generate_weekly_points_chart(
    weekly_data: list[dict],
    statistics: list[dict] | None = None,
    pert_factor: int = 3,
    deadline: str | None = None,
    remaining_points: float | None = None,
) -> str:
    """
    Generate Chart.js script for weekly points breakdown with forecasts.

    Separate chart focusing only on points for clarity.
    """
    if not weekly_data:
        return ""

    dates = [week["date"] for week in weekly_data]
    dates_js = json.dumps(dates)
    points_completed = [week["completed_points"] for week in weekly_data]

    # Calculate weighted 4-week moving average
    points_avg = []
    for i in range(len(points_completed)):
        if i < 3:
            points_avg.append(None)
        else:
            window = points_completed[i - 3 : i + 1]
            weights = [0.1, 0.2, 0.3, 0.4]
            w_avg = sum(w * v for w, v in zip(weights, window, strict=False))
            points_avg.append(round(w_avg, 1))

    # Generate forecasts
    forecast_points = None
    ewma_points = None

    if statistics and len(statistics) > 0:
        has_points_data = "completed_points" in statistics[0] if statistics else False
        if has_points_data:
            try:
                from data.metrics.forecast_calculator import calculate_ewma_forecast
                from data.processing import generate_weekly_forecast

                forecast_data = generate_weekly_forecast(
                    statistics, pert_factor=pert_factor
                )
                if forecast_data["points"]["dates"]:
                    forecast_points = {
                        "date": forecast_data["points"]["dates"][0],
                        "most_likely": round(
                            forecast_data["points"]["most_likely"][0], 1
                        ),
                    }

                ewma_data = calculate_ewma_forecast(points_completed, alpha=0.3)
                if ewma_data:
                    ewma_points = round(ewma_data["forecast_value"], 1)
            except (KeyError, ValueError, IndexError):
                pass

    # Calculate required velocity
    required_points = None
    if deadline and remaining_points is not None and remaining_points > 0:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            last_week_str = weekly_data[-1]["date"]
            year, week = last_week_str.split("-W")
            last_date = datetime.strptime(f"{year}-W{week}-0", "%Y-W%W-%w")
            weeks_remaining = max(1, (deadline_date - last_date).days / 7)
            required_points = round(remaining_points / weeks_remaining, 1)
        except (ValueError, ZeroDivisionError):
            pass

    # Build datasets
    datasets = [
        {
            "type": "bar",
            "label": "Points Completed",
            "data": points_completed,
            "backgroundColor": "#fd7e14",
        }
    ]

    if any(v is not None for v in points_avg):
        datasets.append(
            {
                "type": "line",
                "label": "4-Week Weighted Avg",
                "data": points_avg,
                "borderColor": "#cc5500",
                "borderWidth": 3,
                "fill": False,
                "spanGaps": True,
                "pointRadius": 0,
            }
        )

    # Add forecast data if available
    if forecast_points:
        forecast_dates = dates + [forecast_points["date"]]
        forecast_dates_js = json.dumps(forecast_dates)
        forecast_data = [None] * len(points_completed) + [
            forecast_points["most_likely"]
        ]
        datasets.append(
            {
                "type": "bar",
                "label": "PERT Forecast",
                "data": forecast_data,
                "backgroundColor": "rgba(253, 126, 20, 0.5)",
                "borderColor": "#fd7e14",
                "borderWidth": 2,
            }
        )
    else:
        forecast_dates_js = dates_js

    if ewma_points and forecast_points:
        ewma_data = [None] * len(points_completed) + [ewma_points]
        datasets.append(
            {
                "type": "scatter",
                "label": "EWMA Forecast",
                "data": ewma_data,
                "backgroundColor": "#6c757d",
                "pointRadius": 8,
                "pointStyle": "triangle",
            }
        )

    if required_points:
        required_data = [required_points] * (
            len(points_completed) + (1 if forecast_points else 0)
        )
        datasets.append(
            {
                "type": "line",
                "label": f"Required: {required_points:.1f}/week",
                "data": required_data,
                "borderColor": "#dc3545",
                "borderWidth": 2,
                "borderDash": [5, 5],
                "fill": False,
                "pointRadius": 0,
            }
        )

    datasets_js = json.dumps(datasets)

    return f"""
    (function() {{
        const ctx = document.getElementById('weeklyPointsChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {forecast_dates_js},
                    datasets: {datasets_js}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    scales: {{
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ maxRotation: 45, minRotation: 45 }}
                        }},
                        y: {{
                            type: 'linear',
                            title: {{ display: true, text: 'Points per Week' }},
                            grid: {{ color: '#e9ecef' }},
                        }}
                    }},
                    plugins: {{
                        legend: {{ 
                            display: true, 
                            position: 'bottom',
                            labels: {{
                                boxWidth: 12,
                                padding: 6,
                                font: {{ size: 11 }}
                            }}
                        }},
                        title: {{
                            display: true,
                            text: 'Weekly Story Points Completed with Forecasts',
                            font: {{ size: 14, weight: 'bold' }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    const label = context[0].label;
                                    return label.includes('W') ? 'Week ' + label : 'Forecast: ' + label;
                                }},
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label) {{ label += ': '; }}
                                    label += Math.round(context.parsed.y * 10) / 10;
                                    return label;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """
