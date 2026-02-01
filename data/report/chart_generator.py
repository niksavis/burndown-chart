"""Chart generation functions for HTML reports.

This module contains Chart.js script generators for various visualizations
including burndown charts, weekly breakdowns, scope changes, bug trends,
and work distribution charts.
"""

import json
import logging
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)


def generate_chart_scripts(metrics: Dict[str, Any], sections: List[str]) -> List[str]:
    """
    Generate Chart.js initialization scripts for visualizations.

    Args:
        metrics: Calculated metrics dictionary
        sections: List of sections to generate charts for

    Returns:
        List of JavaScript code strings
    """
    scripts = []

    # Burndown chart with milestone/forecast/deadline
    if "burndown" in sections and metrics.get("burndown", {}).get("has_data"):
        dashboard_metrics = metrics.get("dashboard", {})
        scripts.append(
            generate_burndown_chart(
                metrics["burndown"],
                dashboard_metrics.get("milestone"),
                dashboard_metrics.get("forecast_date"),
                dashboard_metrics.get("deadline"),
                dashboard_metrics.get("show_points", False),
            )
        )

    # Weekly breakdown chart (for burndown section)
    if "burndown" in sections and metrics.get("burndown", {}).get("weekly_data"):
        scripts.append(
            generate_weekly_breakdown_chart(
                metrics["burndown"]["weekly_data"],
                metrics.get("dashboard", {}).get("show_points", False),
            )
        )

    # Scope changes chart
    if "burndown" in sections and metrics.get("scope", {}).get("has_data"):
        scripts.append(generate_scope_changes_chart(metrics))

    # Bug trends chart
    if (
        "burndown" in sections
        and metrics.get("bug_analysis", {}).get("has_data")
        and metrics["bug_analysis"].get("weekly_stats")
    ):
        scripts.append(
            generate_bug_trends_chart(metrics["bug_analysis"]["weekly_stats"])
        )

    # Work distribution chart (for flow section)
    if "flow" in sections and metrics.get("flow", {}).get("has_data"):
        scripts.append(generate_work_distribution_chart(metrics["flow"]))

    return scripts


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

    # Build annotations for milestone, forecast, deadline with named keys
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

    # Format as key: value pairs
    annotations_js = ",\n                ".join(
        [f"{k}: {v}" for k, v in annotations.items()]
    )

    # Build datasets conditionally
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

    # Build scales conditionally
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
    dates = [w["date"] for w in weekly_data]
    dates_js = json.dumps(dates)
    items_created = [w["created_items"] for w in weekly_data]
    items_closed = [-w["completed_items"] for w in weekly_data]
    points_created = [w["created_points"] for w in weekly_data]
    points_closed = [-w["completed_points"] for w in weekly_data]

    # Build datasets conditionally
    datasets = [
        {
            "label": "Items Created",
            "data": items_created,
            "backgroundColor": "#6ea8fe",  # Light blue for created
            "stack": "items",
        },
        {
            "label": "Items Closed",
            "data": items_closed,
            "backgroundColor": "#0d6efd",  # Dark blue for closed
            "stack": "items",
        },
    ]

    if show_points:
        datasets.extend(
            [
                {
                    "label": "Points Created",
                    "data": points_created,
                    "backgroundColor": "#ffb976",  # Light orange for created
                    "stack": "points",
                },
                {
                    "label": "Points Closed",
                    "data": points_closed,
                    "backgroundColor": "#fd7e14",  # Dark orange for closed
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


def generate_scope_changes_chart(metrics: Dict[str, Any]) -> str:
    """Generate Chart.js script for scope changes over time chart."""
    statistics = metrics.get("statistics", [])
    if not statistics:
        return ""

    df = pd.DataFrame(statistics)

    # Convert date to datetime and generate week labels
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore
    df["year"] = df["date"].dt.isocalendar().year  # type: ignore
    # Use vectorized string formatting to avoid DataFrame return issues
    df["week_label"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    # Group by week to aggregate daily data
    weekly_df = (
        df.groupby("week_label")
        .agg({"created_items": "sum", "completed_items": "sum"})
        .reset_index()
    )

    weeks_js = json.dumps(weekly_df["week_label"].tolist())
    created_items_js = json.dumps(weekly_df["created_items"].tolist())
    completed_items_js = json.dumps(weekly_df["completed_items"].tolist())

    return f"""
    (function() {{
        const ctx = document.getElementById('scopeChangesChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {weeks_js},
                    datasets: [
                        {{
                            label: 'Items Created',
                            data: {created_items_js},
                            backgroundColor: 'rgba(220, 53, 69, 0.8)',
                            borderColor: 'rgba(220, 53, 69, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Items Completed',
                            data: {completed_items_js},
                            backgroundColor: 'rgba(25, 135, 84, 0.8)',
                            borderColor: 'rgba(25, 135, 84, 1)',
                            borderWidth: 1
                        }}
                    ]
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
                            beginAtZero: true,
                            grid: {{ color: '#e9ecef' }},
                            title: {{ display: true, text: 'Items' }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: true, position: 'bottom' }},
                        tooltip: {{
                            callbacks: {{
                                afterBody: function(context) {{
                                    const idx = context[0].dataIndex;
                                    const created = context[0].chart.data.datasets[0].data[idx];
                                    const completed = context[0].chart.data.datasets[1].data[idx];
                                    const net = created - completed;
                                    return 'Net Change: ' + (net > 0 ? '+' : '') + net + ' items';
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """


def generate_bug_trends_chart(weekly_stats: List[Dict]) -> str:
    """Generate Chart.js script for bug trends chart showing only items with warning backgrounds."""
    weeks_js = json.dumps(
        [s.get("week_start_date", s.get("week", ""))[:10] for s in weekly_stats]
    )
    bugs_created_js = json.dumps([s.get("bugs_created", 0) for s in weekly_stats])
    bugs_resolved_js = json.dumps([s.get("bugs_resolved", 0) for s in weekly_stats])

    # Calculate warning periods (3+ consecutive weeks where created > resolved)
    annotations = {}
    consecutive_negative_weeks = 0
    warning_start_idx = None

    for idx, stat in enumerate(weekly_stats):
        if stat.get("bugs_created", 0) > stat.get("bugs_resolved", 0):
            consecutive_negative_weeks += 1
            if consecutive_negative_weeks == 1:
                warning_start_idx = idx
        else:
            # Check if we had 3+ consecutive negative weeks
            if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
                # Get week labels for this warning period
                start_week = weekly_stats[warning_start_idx].get(
                    "week_start_date", weekly_stats[warning_start_idx].get("week", "")
                )[:10]
                end_week = weekly_stats[idx - 1].get(
                    "week_start_date", weekly_stats[idx - 1].get("week", "")
                )[:10]
                # Add background box annotation
                annotations[f"warning_{warning_start_idx}"] = f"""{{ 
                    type: 'box',
                    xMin: '{start_week}',
                    xMax: '{end_week}',
                    backgroundColor: 'rgba(255, 165, 0, 0.15)',
                    borderWidth: 0
                }}"""
            consecutive_negative_weeks = 0
            warning_start_idx = None

    # Check final period if it ends with warnings
    if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
        start_week = weekly_stats[warning_start_idx].get(
            "week_start_date", weekly_stats[warning_start_idx].get("week", "")
        )[:10]
        end_week = weekly_stats[-1].get(
            "week_start_date", weekly_stats[-1].get("week", "")
        )[:10]
        annotations[f"warning_{warning_start_idx}"] = f"""{{ 
            type: 'box',
            xMin: '{start_week}',
            xMax: '{end_week}',
            backgroundColor: 'rgba(255, 165, 0, 0.15)',
            borderWidth: 0
        }}"""

    # Build annotations JavaScript with key-value pairs
    if annotations:
        annotations_js = ",\n                                ".join(
            [f"{key}: {value}" for key, value in annotations.items()]
        )
    else:
        annotations_js = ""

    return f"""
    (function() {{
        const ctx = document.getElementById('bugTrendsChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {weeks_js},
                    datasets: [
                        {{
                            label: 'Bugs Created',
                            data: {bugs_created_js},
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.7)',
                            tension: 0.4,
                            borderWidth: 2,
                            fill: false
                        }},
                        {{
                            label: 'Bugs Closed',
                            data: {bugs_resolved_js},
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.7)',
                            tension: 0.4,
                            borderWidth: 2,
                            fill: false
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ grid: {{ display: false }} }},
                        y: {{
                            beginAtZero: true,
                            grid: {{ color: '#e9ecef' }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: true, position: 'bottom' }},
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


def generate_work_distribution_chart(flow_metrics: Dict[str, Any]) -> str:
    """Generate Chart.js script for work distribution stacked bar chart over time."""
    # Get weekly distribution history
    distribution_history = flow_metrics.get("distribution_history", [])

    if not distribution_history:
        return ""

    # Extract data for each flow type
    weeks_js = json.dumps([d["week"] for d in distribution_history])

    # Calculate percentages for each week
    feature_pct = []
    defect_pct = []
    tech_debt_pct = []
    risk_pct = []

    for week_data in distribution_history:
        total = week_data["total"]
        if total > 0:
            feature_pct.append(round((week_data["feature"] / total) * 100, 1))
            defect_pct.append(round((week_data["defect"] / total) * 100, 1))
            tech_debt_pct.append(round((week_data["tech_debt"] / total) * 100, 1))
            risk_pct.append(round((week_data["risk"] / total) * 100, 1))
        else:
            feature_pct.append(0)
            defect_pct.append(0)
            tech_debt_pct.append(0)
            risk_pct.append(0)

    feature_pct_js = json.dumps(feature_pct)
    defect_pct_js = json.dumps(defect_pct)
    tech_debt_pct_js = json.dumps(tech_debt_pct)
    risk_pct_js = json.dumps(risk_pct)

    # Also keep counts for tooltips
    feature_counts_js = json.dumps([d["feature"] for d in distribution_history])
    defect_counts_js = json.dumps([d["defect"] for d in distribution_history])
    tech_debt_counts_js = json.dumps([d["tech_debt"] for d in distribution_history])
    risk_counts_js = json.dumps([d["risk"] for d in distribution_history])

    return f"""
    (function() {{
        const ctx = document.getElementById('workDistributionChart');
        if (ctx) {{
            const featureCounts = {feature_counts_js};
            const defectCounts = {defect_counts_js};
            const techDebtCounts = {tech_debt_counts_js};
            const riskCounts = {risk_counts_js};
            
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {weeks_js},
                    datasets: [
                        {{
                            label: 'Feature',
                            data: {feature_pct_js},
                            backgroundColor: 'rgba(24, 128, 80, 0.8)',
                            borderColor: 'white',
                            borderWidth: 0.5,
                            counts: featureCounts
                        }},
                        {{
                            label: 'Defect',
                            data: {defect_pct_js},
                            backgroundColor: 'rgba(210, 50, 65, 0.8)',
                            borderColor: 'white',
                            borderWidth: 0.5,
                            counts: defectCounts
                        }},
                        {{
                            label: 'Tech Debt',
                            data: {tech_debt_pct_js},
                            backgroundColor: 'rgba(245, 120, 19, 0.8)',
                            borderColor: 'white',
                            borderWidth: 0.5,
                            counts: techDebtCounts
                        }},
                        {{
                            label: 'Risk',
                            data: {risk_pct_js},
                            backgroundColor: 'rgba(245, 185, 7, 0.8)',
                            borderColor: 'white',
                            borderWidth: 0.5,
                            counts: riskCounts
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            stacked: true,
                            grid: {{ display: false }},
                            ticks: {{
                                maxRotation: 45,
                                minRotation: 45
                            }}
                        }},
                        y: {{
                            stacked: true,
                            beginAtZero: true,
                            max: 100,
                            grid: {{ color: 'rgba(0,0,0,0.05)' }},
                            ticks: {{
                                callback: function(value) {{
                                    return value + '%';
                                }}
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ 
                            display: true, 
                            position: 'bottom',
                            labels: {{
                                boxWidth: 12,
                                padding: 10
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const count = context.dataset.counts[context.dataIndex];
                                    const pct = context.parsed.y.toFixed(1);
                                    return context.dataset.label + ': ' + pct + '% (' + count + ' items)';
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """
