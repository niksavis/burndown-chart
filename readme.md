# Burndown Chart Generator

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
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

## DORA & Flow Metrics

Track software delivery performance with industry-standard metrics.

### Key Metrics

| Category | Metric                | What It Measures          | Elite Target      |
| -------- | --------------------- | ------------------------- | ----------------- |
| **DORA** | Deployment Frequency  | How often you deploy      | Multiple/day      |
|          | Lead Time for Changes | Code commit to production | <1 day            |
|          | Change Failure Rate   | % of failed deployments   | 0-15%             |
|          | Mean Time to Recovery | Time to restore service   | <1 hour           |
| **Flow** | Velocity              | Items completed per week  | Team throughput   |
|          | Time                  | Start to completion       | Cycle efficiency  |
|          | Efficiency            | Active work vs. waiting   | 25-40%            |
|          | Load (WIP)            | Work in progress          | Uses Little's Law |
|          | Distribution          | Work type balance         | 40-60% features   |

**Configuration**: Click "Configure Field Mappings" on dashboard to map JIRA custom fields (deployment date, environment, work type).

**Export**: Download as CSV or JSON for external reporting.

## Troubleshooting

- **Missing packages?** Activate venv: `.venv\Scripts\activate`, then `pip install -r requirements.txt`
- **Port in use?** Run with `python app.py --port 8060`
- **JIRA connection failed?** Verify URL and token in Data Import Configuration
- **No data?** Check field mappings and JIRA data contains required fields
- **Reset**: Delete `project_data.json`, `app_settings.json`, and `jira_cache.json`

## Documentation

- **[Complete Metrics Guide](docs/metrics/METRICS_EXPLANATION.md)** - Definitions, calculations, quick start, common pitfalls
- **[License](LICENSE)** - MIT License

---

**[⬆ Back to Top](#burndown-chart-generator)**
