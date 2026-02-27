"""Burndown and weekly breakdown chart generators."""

import json
from datetime import datetime

from data.velocity_projections import calculate_required_velocity


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
    from datetime import datetime

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
                                    return label.includes('W') ? 'Week ' + label : label;
                                }},
                                label: function(context) {{
                                    if (context.parsed.y === null || context.parsed.y === undefined) {{
                                        return null;
                                    }}
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(0);
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
                "label": f"PERT Forecast (Points): {forecast_points['most_likely']:.1f}",
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
                                    // Suppress entirely when no data value (PERT/EWMA on historical weeks)
                                    if (context.parsed.y === null || context.parsed.y === undefined) {{
                                        return null;
                                    }}
                                    // Labels with embedded values - return as-is without appending again
                                    if (label.startsWith('Required:') || label.startsWith('EWMA Forecast') || label.startsWith('PERT Forecast')) {{
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
