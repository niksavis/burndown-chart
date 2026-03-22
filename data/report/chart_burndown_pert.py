"""Weekly items and points PERT/EWMA forecast charts.

Generates focused Chart.js charts for weekly items and story points
with PERT and EWMA forecast projections.
Part of data/report/chart_burndown.py split.
"""

import json
from datetime import datetime

from data.metrics.forecast_calculator import calculate_ewma_forecast
from data.processing import generate_weekly_forecast
from data.velocity_projections import calculate_required_velocity


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
            except KeyError, ValueError, IndexError:
                pass

    # Calculate required velocity using midnight-today (matches app calculation exactly)
    required_items = None
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
        except ValueError, ZeroDivisionError:
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
                                    return label.includes('W')
                                        ? 'Week ' + label
                                        : 'Forecast: ' + label;
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
            except KeyError, ValueError, IndexError:
                pass

    # Calculate required velocity using midnight-today (matches app calculation exactly)
    required_points = None
    if deadline and remaining_points is not None and remaining_points > 0:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            current_date = datetime.combine(datetime.now().date(), datetime.min.time())
            raw = calculate_required_velocity(
                remaining_points,
                deadline_date,
                current_date=current_date,
                time_unit="week",
            )
            required_points = round(raw, 1) if raw != float("inf") else None
        except ValueError, ZeroDivisionError:
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
                                    return label.includes('W')
                                        ? 'Week ' + label
                                        : 'Forecast: ' + label;
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
