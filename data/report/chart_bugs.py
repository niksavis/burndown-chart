"""Bug trends chart generator."""

import json
from typing import Dict, List


def generate_bug_trends_chart(weekly_stats: List[Dict]) -> str:
    """Generate Chart.js script for bug trends chart showing warning backgrounds."""
    weeks_js = json.dumps(
        [
            stat.get("week_start_date", stat.get("week", ""))[:10]
            for stat in weekly_stats
        ]
    )
    bugs_created_js = json.dumps([stat.get("bugs_created", 0) for stat in weekly_stats])
    bugs_resolved_js = json.dumps(
        [stat.get("bugs_resolved", 0) for stat in weekly_stats]
    )

    annotations = {}
    consecutive_negative_weeks = 0
    warning_start_idx = None

    for idx, stat in enumerate(weekly_stats):
        if stat.get("bugs_created", 0) > stat.get("bugs_resolved", 0):
            consecutive_negative_weeks += 1
            if consecutive_negative_weeks == 1:
                warning_start_idx = idx
        else:
            if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
                start_week = weekly_stats[warning_start_idx].get(
                    "week_start_date", weekly_stats[warning_start_idx].get("week", "")
                )[:10]
                end_week = weekly_stats[idx - 1].get(
                    "week_start_date", weekly_stats[idx - 1].get("week", "")
                )[:10]
                annotations[f"warning_{warning_start_idx}"] = f"""{{ 
                    type: 'box',
                    xMin: '{start_week}',
                    xMax: '{end_week}',
                    backgroundColor: 'rgba(255, 165, 0, 0.15)',
                    borderWidth: 0
                }}"""
            consecutive_negative_weeks = 0
            warning_start_idx = None

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
