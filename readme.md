# Burndown Chart Generator

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/niksavis/burndown-chart/releases)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Interactive web app for agile project forecasting with JIRA integration and comprehensive DORA & Flow metrics.

## Quick Start

1. **Install:**
   ```bash
   git clone https://github.com/niksavis/burndown-chart.git
   cd burndown-chart
   python -m venv .venv
   .venv\Scripts\activate  # Windows (.venv/bin/activate on macOS/Linux)
   pip install -r requirements.txt
   ```

2. **Run:**
   ```bash
   python app.py
   ```
   Open: [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

## Core Features

- **📊 Interactive Burndown/Burnup Charts**: Track remaining and completed work with forecasting
- **🔮 PERT Forecasting**: Optimistic, most likely, and pessimistic completion predictions
- **📈 DORA Metrics**: Deployment Frequency, Lead Time, Change Failure Rate, MTTR
- **🌊 Flow Metrics**: Velocity, Time, Efficiency, Load (WIP), Distribution
- **🔌 JIRA Integration**: Direct API sync with JQL queries and smart caching
- **📁 File Import**: CSV/JSON upload support
- **💾 Export**: Download charts and metrics data

## Data Sources

### JIRA Integration (Recommended)

Configure via web interface **Data Import Configuration** section:

1. Navigate to **Input Parameters → Data Import Configuration**
2. Enter:
   - **JIRA URL**: Your JIRA instance endpoint
   - **JQL Query**: Filter for your project (e.g., `project = MYPROJECT`)
   - **API Token**: Personal access token (optional for public instances)
   - **Story Points Field**: Custom field ID (optional)
3. Click **Update Data** to sync

**Quick Test**: Try `https://jira.atlassian.com/rest/api/2/search` with JQL `project = JRASERVER` (no token needed).

### File Upload (Alternative)

Upload CSV or JSON files with project statistics:

**CSV Format:**
```csv
date;completed_items;completed_points;created_items;created_points
2025-03-01;5;50;0;0
2025-03-02;7;70;2;15
```

**JSON Format:**
```json
{
  "project_scope": {
    "total_items": 100,
    "total_points": 500,
    "completed_items": 25,
    "completed_points": 120
  },
  "statistics": [
    {"date": "2025-03-01", "completed_items": 5, "completed_points": 50}
  ]
}
```

## Metrics Overview

Track project health, delivery performance, and process efficiency.

### Key Metrics by Category

| Category           | Metric                | What It Measures          | Target/Tier        |
| ------------------ | --------------------- | ------------------------- | ------------------ |
| **Project Health** | Health Score          | Overall project status    | 80-100 (Excellent) |
|                    | Completion Forecast   | Days to completion        | On/ahead schedule  |
|                    | Current Velocity      | Items/points per week     | Stable trend       |
|                    | Remaining Work        | Items/points to complete  | Decreasing         |
| **DORA**           | Deployment Frequency  | How often you deploy      | ≥7/week (Elite)    |
|                    | Lead Time for Changes | Code commit to production | <1 day (Elite)     |
|                    | Change Failure Rate   | % of failed deployments   | 0-15% (Elite)      |
|                    | Mean Time to Recovery | Time to restore service   | <1 hour (Elite)    |
| **Flow**           | Flow Velocity         | Items completed per week  | Stable throughput  |
|                    | Flow Time             | Start to completion       | Consistent cycle   |
|                    | Flow Efficiency       | Active work vs. waiting   | 25-40%             |
|                    | Flow Load (WIP)       | Work in progress          | <P25 threshold     |
|                    | Flow Distribution     | Work type balance         | 40-50% features    |

**Configuration**: Click "Configure Field Mappings" on dashboard to map JIRA custom fields (deployment date, environment, work type).

**Export**: Download as CSV or JSON for external reporting.

## Troubleshooting

- **Missing packages?** Activate venv: `.venv\Scripts\activate`, then `pip install -r requirements.txt`
- **Port in use?** Run with `python app.py --port 8060`
- **JIRA connection failed?** Verify URL and token in Data Import Configuration
- **No data?** Check field mappings and JIRA data contains required fields
- **Full reset**: Delete `project_data.json`, `app_settings.json`, `jira_cache.json`, and `metrics_snapshots.json`

## Documentation

- **[Metrics Index](docs/metrics_index.md)** - Quick start guide to all metrics (Dashboard, DORA, Flow)
- **[Project Dashboard Metrics](docs/dashboard_metrics.md)** - Health score, velocity, forecasting
- **[DORA Metrics](docs/dora_metrics.md)** - Deployment frequency, lead time, CFR, MTTR
- **[Flow Metrics](docs/flow_metrics.md)** - Velocity, time, efficiency, load, distribution
- **[License](LICENSE)** - MIT License

---

**[⬆ Back to Top](#burndown-chart-generator)**
