"""Work distribution chart generator."""

import json
from typing import Any


def generate_work_distribution_chart(flow_metrics: dict[str, Any]) -> str:
    """Generate Chart.js script for work distribution stacked bar chart over time."""
    distribution_history = flow_metrics.get("distribution_history", [])

    if not distribution_history:
        return ""

    weeks_js = json.dumps([week["week"] for week in distribution_history])

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

    feature_counts_js = json.dumps([week["feature"] for week in distribution_history])
    defect_counts_js = json.dumps([week["defect"] for week in distribution_history])
    tech_debt_counts_js = json.dumps(
        [week["tech_debt"] for week in distribution_history]
    )
    risk_counts_js = json.dumps([week["risk"] for week in distribution_history])

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
