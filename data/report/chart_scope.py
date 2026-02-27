"""Scope changes chart generator."""

import json
from typing import Any

import pandas as pd


def generate_scope_changes_chart(metrics: dict[str, Any]) -> str:
    """Generate Chart.js script for scope changes over time chart.

    Displays three datasets per week:
    - Items Created bar (red)
    - Items Completed bar (green)
    - Net Scope Change line (red when positive/growing, green when negative/shrinking)

    The net line immediately highlights which weeks drove scope growth.
    """
    statistics = metrics.get("statistics", [])
    if not statistics:
        return ""

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore
    df["year"] = df["date"].dt.isocalendar().year  # type: ignore
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore
    df["week_label"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    weekly_df = (
        df.groupby("week_label")
        .agg({"created_items": "sum", "completed_items": "sum"})
        .reset_index()
        .sort_values("week_label")  # Ensure chronological order
    )

    created = weekly_df["created_items"].tolist()
    completed = weekly_df["completed_items"].tolist()
    net_change = [c - d for c, d in zip(created, completed, strict=True)]

    # Colour each net point: red if scope grew (> 0), green if shrank (<= 0)
    net_colors = [
        "rgba(220, 53, 69, 0.9)" if n > 0 else "rgba(25, 135, 84, 0.9)"
        for n in net_change
    ]

    weeks_js = json.dumps(weekly_df["week_label"].tolist())
    created_js = json.dumps(created)
    completed_js = json.dumps(completed)
    net_js = json.dumps(net_change)
    net_colors_js = json.dumps(net_colors)

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
                            type: 'bar',
                            label: 'Items Created',
                            data: {created_js},
                            backgroundColor: 'rgba(220, 53, 69, 0.7)',
                            borderColor: 'rgba(220, 53, 69, 1)',
                            borderWidth: 1,
                            order: 2,
                            yAxisID: 'y'
                        }},
                        {{
                            type: 'bar',
                            label: 'Items Completed',
                            data: {completed_js},
                            backgroundColor: 'rgba(25, 135, 84, 0.7)',
                            borderColor: 'rgba(25, 135, 84, 1)',
                            borderWidth: 1,
                            order: 2,
                            yAxisID: 'y'
                        }},
                        {{
                            type: 'line',
                            label: 'Net Scope Change',
                            data: {net_js},
                            borderColor: 'rgba(99, 102, 241, 0.9)',
                            backgroundColor: {net_colors_js},
                            borderWidth: 2,
                            borderDash: [5, 3],
                            pointRadius: 5,
                            pointHoverRadius: 7,
                            pointBackgroundColor: {net_colors_js},
                            fill: false,
                            tension: 0.2,
                            order: 1,
                            yAxisID: 'yNet'
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
                            position: 'left',
                            grid: {{ color: '#e9ecef' }},
                            title: {{ display: true, text: 'Items' }}
                        }},
                        yNet: {{
                            position: 'right',
                            grid: {{ drawOnChartArea: false }},
                            title: {{ display: true, text: 'Net Change' }},
                            ticks: {{
                                callback: function(v) {{
                                    return (v > 0 ? '+' : '') + v;
                                }}
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'bottom',
                            labels: {{ boxWidth: 12, padding: 8, font: {{ size: 11 }} }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    return 'Week ' + context[0].label;
                                }},
                                label: function(context) {{
                                    const label = context.dataset.label || '';
                                    const v = context.parsed.y;
                                    if (label === 'Net Scope Change') {{
                                        const sign = v > 0 ? '+' : '';
                                        return label + ': ' + sign + v + ' items';
                                    }}
                                    return label + ': ' + v;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
    }})();
    """
