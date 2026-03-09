"""Daily burndown chart generator.

Generates the Chart.js cumulative burndown chart with forecast projection lines.
Part of data/report/chart_burndown.py split.
"""

import json
from datetime import datetime


def _iso_week_str(date_str: str) -> str | None:
    """Convert a YYYY-MM-DD date string to ISO week label 'YYYY-WWW'."""
    try:
        import pandas as pd

        dt = pd.to_datetime(date_str)
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"
    except Exception:
        return None


def generate_burndown_chart(
    burndown_metrics: dict,
    milestone: str,
    forecast_date: str,
    deadline: str,
    show_points: bool = False,
    statistics: list[dict] | None = None,
    pert_factor: int = 3,
) -> str:
    """Generate Chart.js script for burndown chart with forecasts and
    milestone/forecast/deadline lines.

    The x-axis is a sorted, unified timeline of all ISO weeks: historical data
    weeks plus the milestone, forecast, and deadline weeks. Historical data is
    padded with null for weeks beyond the last known data point, and a linear
    forecast projection line is drawn from the last known remaining count to
    zero at the forecast week.

    Args:
        burndown_metrics: Historical burndown data
        milestone: Milestone date string (YYYY-MM-DD)
        forecast_date: Forecast completion date string (YYYY-MM-DD)
        deadline: Deadline date string (YYYY-MM-DD)
        show_points: Whether to show points data
        statistics: Statistics data (unused, kept for signature compatibility)
        pert_factor: PERT factor (unused, kept for signature compatibility)
    """

    historical = burndown_metrics.get("historical_data", {})
    raw_dates = historical.get("dates", [])
    items = historical.get("remaining_items", [])
    points = historical.get("remaining_points", [])

    # Build mapping: iso_week -> (remaining_items, remaining_points)
    hist_map: dict[str, tuple] = {}
    for i, date_str in enumerate(raw_dates):
        week = _iso_week_str(date_str)
        if week:
            it = items[i] if i < len(items) else None
            pt = points[i] if i < len(points) else None
            hist_map[week] = (it, pt)

    # Collect all special date weeks (milestone, forecast, deadline)
    special: dict[str, dict] = {}
    for key, date_str, color, text_color, dash in [
        ("milestone", milestone, "#ffc107", "#000", [10, 5]),
        ("forecast", forecast_date, "#198754", "#fff", [5, 5]),
        ("deadline", deadline, "#dc3545", "#fff", []),
    ]:
        if not date_str:
            continue
        week = _iso_week_str(date_str)
        if not week:
            continue
        try:
            readable = datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y")
        except ValueError:
            readable = date_str
        special[key] = {
            "week": week,
            "label": f"{key.capitalize()}\\n{readable}",
            "color": color,
            "text_color": text_color,
            "dash": dash,
        }

    # Build unified, chronologically sorted labels array
    all_weeks_set = set(hist_map.keys()) | {v["week"] for v in special.values()}
    all_weeks = sorted(all_weeks_set)
    dates_js = json.dumps(all_weeks)

    # Build padded data arrays: null for weeks outside historical range
    items_padded = [hist_map.get(w, (None, None))[0] for w in all_weeks]
    points_padded = [hist_map.get(w, (None, None))[1] for w in all_weeks]

    # Build forecast projection line: from last known remaining → 0 at forecast week
    # Uses linear interpolation between last data point and forecast week
    forecast_items_proj: list = [None] * len(all_weeks)
    forecast_points_proj: list = [None] * len(all_weeks)
    has_forecast_line = False

    if special.get("forecast") and hist_map:
        forecast_week = special["forecast"]["week"]
        # Find last historical week index
        hist_weeks = sorted(hist_map.keys())
        last_hist_week = hist_weeks[-1]
        last_items = hist_map[last_hist_week][0]
        last_points = hist_map[last_hist_week][1]

        last_idx = (
            all_weeks.index(last_hist_week) if last_hist_week in all_weeks else -1
        )
        forecast_idx = (
            all_weeks.index(forecast_week) if forecast_week in all_weeks else -1
        )

        if last_idx >= 0 and forecast_idx > last_idx and last_items is not None:
            steps = forecast_idx - last_idx
            for s in range(steps + 1):
                idx = last_idx + s
                frac = s / steps
                forecast_items_proj[idx] = round(last_items * (1 - frac), 1)
                if show_points and last_points is not None:
                    forecast_points_proj[idx] = round(last_points * (1 - frac), 1)
            has_forecast_line = True

    # Annotation vertical lines: sorted chronologically to assign yAdjust top-to-bottom
    # Sort special entries by week so labels stack in timeline order
    sorted_special = sorted(special.items(), key=lambda kv: kv[1]["week"])
    base_y = -90
    spacing = 30
    annotations = {}
    for idx, (key, meta) in enumerate(sorted_special):
        y_adjust = base_y + idx * spacing
        week = meta["week"]
        label = meta["label"]
        color = meta["color"]
        text_color = meta["text_color"]
        dash = meta["dash"]
        dash_str = f"[{', '.join(map(str, dash))}]" if dash else "[]"
        width = 3 if key == "milestone" else 2
        annotations[key] = (
            f"{{type:'line',xMin:'{week}',xMax:'{week}',"
            f"borderColor:'{color}',borderWidth:{width},borderDash:{dash_str},"
            f"label:{{display:true,content:'{label}',position:'start',"
            f"yAdjust:{y_adjust},backgroundColor:'{color}',color:'{text_color}'}}}}"
        )

    annotations_js = ",\n                ".join(
        f"{k}: {v}" for k, v in annotations.items()
    )

    # Datasets
    datasets = [
        {
            "label": "Remaining Items",
            "data": items_padded,
            "borderColor": "#0d6efd",
            "backgroundColor": "rgba(13, 110, 253, 0.1)",
            "fill": True,
            "tension": 0.3,
            "borderWidth": 2,
            "pointRadius": 3,
            "yAxisID": "y",
            "spanGaps": False,
        }
    ]

    if show_points:
        datasets.append(
            {
                "label": "Remaining Points",
                "data": points_padded,
                "borderColor": "#fd7e14",
                "backgroundColor": "rgba(253, 126, 20, 0.1)",
                "fill": True,
                "tension": 0.3,
                "borderWidth": 2,
                "pointRadius": 3,
                "yAxisID": "y1",
                "spanGaps": False,
            }
        )

    if has_forecast_line:
        datasets.append(
            {
                "label": "Forecast (Items)",
                "data": forecast_items_proj,
                "borderColor": "#198754",
                "backgroundColor": "rgba(25, 135, 84, 0.08)",
                "fill": False,
                "tension": 0,
                "borderWidth": 2,
                "borderDash": [6, 4],
                "pointRadius": 0,
                "yAxisID": "y",
                "spanGaps": False,
            }
        )
        if show_points:
            datasets.append(
                {
                    "label": "Forecast (Points)",
                    "data": forecast_points_proj,
                    "borderColor": "#fd7e14",
                    "backgroundColor": "rgba(253, 126, 20, 0.08)",
                    "fill": False,
                    "tension": 0,
                    "borderWidth": 2,
                    "borderDash": [6, 4],
                    "pointRadius": 0,
                    "yAxisID": "y1",
                    "spanGaps": False,
                }
            )

    datasets_js = json.dumps(datasets)

    scales_config: dict = {
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
            "min": 0,
        },
    }

    if show_points:
        scales_config["y1"] = {
            "type": "linear",
            "display": True,
            "position": "right",
            "title": {"display": True, "text": "Points"},
            "grid": {"drawOnChartArea": False},
            "min": 0,
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
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    const label = context[0].label;
                                    return label.includes('W')
                                        ? 'Week ' + label
                                        : label;
                                }},
                                label: function(context) {{
                                    if (
                                        context.parsed.y === null
                                        || context.parsed.y === undefined
                                    ) {{
                                        return null;
                                    }}
                                    return (
                                        context.dataset.label
                                        + ': '
                                        + context.parsed.y.toFixed(0)
                                    );
                                }}
                            }}
                        }},
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
