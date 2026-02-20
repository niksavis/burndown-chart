"""Scope changes chart generator."""

import json
from typing import Any

import pandas as pd


def generate_scope_changes_chart(metrics: dict[str, Any]) -> str:
    """Generate Chart.js script for scope changes over time chart."""
    statistics = metrics.get("statistics", [])
    if not statistics:
        return ""

    df = pd.DataFrame(statistics)

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore
    df["year"] = df["date"].dt.isocalendar().year  # type: ignore
    df["week_label"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

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
