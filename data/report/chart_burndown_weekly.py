"""Weekly breakdown chart generator.

Generates the Chart.js weekly breakdown bar chart with PERT/EWMA forecasts.
Part of data/report/chart_burndown.py split.
"""

import json
from datetime import datetime

from data.velocity_projections import calculate_required_velocity


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
    Generate Chart.js script for weekly breakdown showing completed
    items/points with forecasts and targets.

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

    # Calculate required velocity using midnight-today (matches app calculation exactly)
    required_items = None
    required_points = None
    if deadline and remaining_items is not None and remaining_items > 0:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            current_date = datetime.combine(datetime.now().date(), datetime.min.time())
            raw = calculate_required_velocity(
                remaining_items,
                deadline_date,
                current_date=current_date,
                time_unit="week",
            )
            required_items = round(raw, 1) if raw != float("inf") else None

            if show_points and remaining_points is not None and remaining_points > 0:
                raw_pts = calculate_required_velocity(
                    remaining_points,
                    deadline_date,
                    current_date=current_date,
                    time_unit="week",
                )
                required_points = round(raw_pts, 1) if raw_pts != float("inf") else None
        except (ValueError, ZeroDivisionError):
            pass  # Skip if date parsing fails

    # Extend dates to include forecast week before building datasets
    if forecast_items:
        forecast_dates = dates + [forecast_items["date"]]
        dates_js = json.dumps(forecast_dates)

    # Build datasets in legend display order:
    # 1. Actual bars (Items Completed, Points Completed)
    # 2. EWMA forecast markers
    # 3. PERT forecast bars
    # 4. Required velocity reference lines
    # Chart.js render order: lower order value = rendered on top
    # order values control both legend sequence and tooltip ordering in Chart.js.
    # Lower order = earlier in legend. Assign 1-8 in desired display sequence:
    #   1=Items Completed, 2=Points Completed, 3=EWMA Items, 4=EWMA Points,
    #   5=PERT Items, 6=PERT Points, 7=Required Items, 8=Required Points
    datasets = [
        {
            "type": "bar",
            "label": "Items Completed",
            "data": items_completed,
            "backgroundColor": "#0d6efd",
            "yAxisID": "y",
            "order": 1,
        }
    ]

    if show_points:
        datasets.append(
            {
                "type": "bar",
                "label": "Points Completed",
                "data": points_completed,
                "backgroundColor": "#fd7e14",
                "yAxisID": "y1",
                "order": 2,
            }
        )

    # EWMA forecast markers (value embedded in label)
    if ewma_items and forecast_items:
        ewma_items_data = [None] * len(items_completed) + [ewma_items]
        datasets.append(
            {
                "type": "scatter",
                "label": f"EWMA Forecast (Items): {ewma_items:.1f}",
                "data": ewma_items_data,
                "backgroundColor": "#0d6efd",
                "pointRadius": 8,
                "pointStyle": "triangle",
                "yAxisID": "y",
                "order": 3,
            }
        )

    if show_points and ewma_points and forecast_points:
        ewma_points_data = [None] * len(points_completed) + [ewma_points]
        datasets.append(
            {
                "type": "scatter",
                "label": f"EWMA Forecast (Points): {ewma_points:.1f}",
                "data": ewma_points_data,
                "backgroundColor": "#fd7e14",
                "pointRadius": 8,
                "pointStyle": "triangle",
                "yAxisID": "y1",
                "order": 4,
            }
        )

    # PERT forecast bars (value embedded in label)
    if forecast_items:
        forecast_items_data = [None] * len(items_completed) + [
            forecast_items["most_likely"]
        ]
        datasets.append(
            {
                "type": "bar",
                "label": f"PERT Forecast (Items): {forecast_items['most_likely']:.1f}",
                "data": forecast_items_data,
                "backgroundColor": "rgba(13, 110, 253, 0.4)",
                "borderColor": "#0d6efd",
                "borderWidth": 2,
                "yAxisID": "y",
                "order": 5,
            }
        )

    if show_points and forecast_points:
        forecast_points_data = [None] * len(points_completed) + [
            forecast_points["most_likely"]
        ]
        datasets.append(
            {
                "type": "bar",
                "label": (
                    f"PERT Forecast (Points): {forecast_points['most_likely']:.1f}"
                ),
                "data": forecast_points_data,
                "backgroundColor": "rgba(253, 126, 20, 0.4)",
                "borderColor": "#fd7e14",
                "borderWidth": 2,
                "yAxisID": "y1",
                "order": 6,
            }
        )

    # Required velocity reference lines (last in legend)
    # Use distinct colors: violet for items, red for points
    if required_items:
        required_items_data = [required_items] * len(items_completed)
        if forecast_items:
            required_items_data.append(required_items)
        datasets.append(
            {
                "type": "line",
                "label": f"Required: {required_items:.1f} items/week",
                "data": required_items_data,
                "borderColor": "#8b5cf6",
                "borderWidth": 3,
                "borderDash": [8, 4],
                "fill": False,
                "yAxisID": "y",
                "pointRadius": 0,
                "order": 7,
            }
        )

    if show_points and required_points:
        required_points_data = [required_points] * len(points_completed)
        if forecast_points:
            required_points_data.append(required_points)
        datasets.append(
            {
                "type": "line",
                "label": f"Required: {required_points:.1f} points/week",
                "data": required_points_data,
                "borderColor": "#dc2626",
                "borderWidth": 3,
                "borderDash": [8, 4],
                "fill": False,
                "yAxisID": "y1",
                "pointRadius": 0,
                "order": 8,
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
                                    return label.includes('W')
                                        ? 'Week ' + label
                                        : 'Forecast: ' + label;
                                }},
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    // Suppress entirely when no data value
                                    // (PERT/EWMA on historical weeks)
                                    if (
                                        context.parsed.y === null
                                        || context.parsed.y === undefined
                                    ) {{
                                        return null;
                                    }}
                                    // Labels with embedded values are
                                    // returned as-is without appending.
                                    if (
                                        label.startsWith('Required:')
                                        || label.startsWith('EWMA Forecast')
                                        || label.startsWith('PERT Forecast')
                                    ) {{
                                        return label;
                                    }}
                                    if (label) {{
                                        label += ': ';
                                    }}
                                    label += context.parsed.y.toFixed(1);
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
