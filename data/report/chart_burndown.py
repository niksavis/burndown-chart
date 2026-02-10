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

    # Calculate label positions based on chronological order to prevent overlap
    from datetime import datetime

    date_labels = []
    if milestone:
        date_labels.append(
            ("milestone", milestone, "Milestone", "#ffc107", "#000", 3, [10, 5])
        )
    if forecast_date:
        date_labels.append(
            ("forecast", forecast_date, "Forecast", "#198754", "#fff", 2, [5, 5])
        )
    if deadline:
        date_labels.append(("deadline", deadline, "Deadline", "#dc3545", "#fff", 2, []))

    # Sort by date chronologically
    date_labels.sort(key=lambda x: datetime.strptime(x[1], "%Y-%m-%d"))

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
