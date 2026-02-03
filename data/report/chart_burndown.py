"""Burndown and weekly breakdown chart generators."""

import json
from typing import Dict, List


def generate_burndown_chart(
    burndown_metrics: Dict,
    milestone: str,
    forecast_date: str,
    deadline: str,
    show_points: bool = False,
) -> str:
    """Generate Chart.js script for burndown chart with milestone/forecast/deadline lines."""
    historical = burndown_metrics.get("historical_data", {})
    dates = historical.get("dates", [])
    dates_js = json.dumps(dates)
    items = historical.get("remaining_items", [])
    points = historical.get("remaining_points", [])

    annotations = {}

    if milestone:
        annotations["milestone"] = f"""{{
            type: 'line',
            xMin: '{milestone}',
            xMax: '{milestone}',
            borderColor: '#ffc107',
            borderWidth: 3,
            borderDash: [10, 5],
            label: {{
                display: true,
                content: 'Milestone',
                position: 'start',
                yAdjust: -60,
                backgroundColor: '#ffc107',
                color: '#000'
            }}
        }}"""

    if forecast_date:
        annotations["forecast"] = f"""{{
            type: 'line',
            xMin: '{forecast_date}',
            xMax: '{forecast_date}',
            borderColor: '#198754',
            borderWidth: 2,
            borderDash: [5, 5],
            label: {{
                display: true,
                content: 'Forecast',
                position: 'start',
                yAdjust: -30,
                backgroundColor: '#198754',
                color: '#fff'
            }}
        }}"""

    if deadline:
        annotations["deadline"] = f"""{{
            type: 'line',
            xMin: '{deadline}',
            xMax: '{deadline}',
            borderColor: '#dc3545',
            borderWidth: 2,
            label: {{
                display: true,
                content: 'Deadline',
                position: 'start',
                yAdjust: 0,
                backgroundColor: '#dc3545',
                color: '#fff'
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
    weekly_data: List[Dict], show_points: bool = False
) -> str:
    """Generate Chart.js script for weekly breakdown chart."""
    dates = [week["date"] for week in weekly_data]
    dates_js = json.dumps(dates)
    items_created = [week["created_items"] for week in weekly_data]
    items_closed = [-week["completed_items"] for week in weekly_data]
    points_created = [week["created_points"] for week in weekly_data]
    points_closed = [-week["completed_points"] for week in weekly_data]

    datasets = [
        {
            "label": "Items Created",
            "data": items_created,
            "backgroundColor": "#6ea8fe",
            "stack": "items",
        },
        {
            "label": "Items Closed",
            "data": items_closed,
            "backgroundColor": "#0d6efd",
            "stack": "items",
        },
    ]

    if show_points:
        datasets.extend(
            [
                {
                    "label": "Points Created",
                    "data": points_created,
                    "backgroundColor": "#ffb976",
                    "stack": "points",
                },
                {
                    "label": "Points Closed",
                    "data": points_closed,
                    "backgroundColor": "#fd7e14",
                    "stack": "points",
                },
            ]
        )

    datasets_js = json.dumps(datasets)

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
                    scales: {{
                        x: {{ stacked: true, grid: {{ display: false }} }},
                        y: {{ 
                            stacked: true,
                            grid: {{ color: '#e9ecef' }},
                            ticks: {{
                                callback: function(value) {{
                                    return Math.abs(value);
                                }}
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: true, position: 'bottom' }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ' + Math.abs(context.parsed.y);
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """
