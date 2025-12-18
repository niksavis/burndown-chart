# Burndown Chart Generator

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/niksavis/burndown-chart/releases)
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
- **📋 HTML Reports**: Generate comprehensive project snapshots with charts and metrics
- **🔌 JIRA Integration**: Direct API sync with JQL queries and smart caching
- **📁 File Import**: CSV/JSON upload support
- **💾 Export**: Download reports, charts, and metrics data

## Configuration

### Profile-Based Workspaces

Each profile stores independent configuration for different projects/teams with support for multiple JQL queries:

1. **Create Profile**: Settings → Profile Management → "Create New Profile"
2. **Switch Profiles**: Use profile dropdown in top navigation
3. **Manage Queries**: Each profile can have multiple saved JQL queries
   - Save queries with custom names for quick switching
   - Each query maintains its own data cache and metrics
4. **Profile Storage**: All settings saved in `profiles/{profile_id}/`
   - Profile config: `profile.json`
   - Query data: `queries/{query_id}/project_data.json`
   - JIRA cache: `queries/{query_id}/jira_cache.json`

### JIRA Integration (Recommended)

**Step 1: Connect to JIRA**
1. Settings → JIRA Configuration
2. Enter JIRA URL and API token
3. Enter JQL query (e.g., `project = MYPROJECT`)
4. Click **Fetch Metadata** to detect available fields

**Step 2: Configure Field Mappings**
1. Settings → Configure JIRA Mappings (modal opens)
2. Click **Auto-Configure** - system automatically detects fields by name patterns:
   - Standard fields: Story Points, Status, Issue Type, Project
   - Custom fields: Deployment Date, Environment, Severity, etc.
   - Smart matching: Handles variations like "Story Points", "Estimate", "Points"
3. Review and adjust mappings across 5 tabs:
   - **Projects**: Development vs. DevOps projects
   - **Fields**: Map JIRA custom fields to metrics
   - **Types**: Issue type classifications (Feature/Defect/Tech Debt/Risk)
   - **Status**: Workflow statuses (completion, active, WIP)
   - **Environment**: Production identifiers
4. Click **Save Mappings**

**💡 Tip**: Auto-Configure typically finds 80-90% of required fields. Review suggestions and manually map any remaining fields.

**Step 3: Load Data**
1. Click **Update Data** button (fetches only changed issues since last update)
2. **Long-press Update Data** for Force Refresh (fetches all data, ignores cache)
3. Click **Cancel Operation** during fetch to stop operation
4. Data cached in `jira_cache.json` (smart delta updates)

**💡 Tip**: Operations continue if you refresh the page - Cancel Operation button appears when resuming.

**Quick Test**: Public JIRA instance `https://jira.atlassian.com` with JQL `project = JRASERVER` (no token needed)

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

**Auto-Configuration**: System detects JIRA fields by name patterns and suggests mappings. Review in Settings → Configure JIRA Mappings.

## Report Generation

Create standalone HTML reports with project metrics snapshots:

1. **Generate Report**: Settings → Import/Export → Generate Report
2. **Select Sections**: Choose metrics to include:
   - **Dashboard**: Health overview, forecast, velocity summary
   - **Burndown Analysis**: Charts, bug metrics, scope changes
   - **Flow Metrics**: Velocity, time, efficiency, work distribution
   - **DORA Metrics**: Deployment frequency, lead time, CFR, MTTR
3. **Choose Time Period**: 4, 12, 26, or 52 weeks of historical data
4. **Download**: Self-contained HTML file with embedded charts

Reports include all visualizations, metrics calculations, and data tables in a single shareable file. No external dependencies required - works offline in any browser.

**💡 Tip**: Generate weekly/monthly reports for stakeholder updates or milestone documentation.

## Export Options

- **HTML Reports**: Comprehensive project snapshots (Settings → Import/Export → Generate Report)
- **Profile Export**: Full profile backup with config and data (Settings → Import/Export → Export Profile)
- **Metrics Data**: CSV or JSON downloads from individual metric views

## Troubleshooting

**Installation Issues:**
- **Missing packages?** Activate venv: `.venv\Scripts\activate`, then `pip install -r requirements.txt`
- **Port in use?** Run with `python app.py --port 8060`

**JIRA Issues:**
- **Connection failed?** Settings → JIRA Configuration - verify URL and API token
- **No data after sync?** Check JQL query returns issues in JIRA web UI
- **"Missing Required Field" errors?** Settings → Configure JIRA Mappings - map required fields
- **Clear cache:** Delete `jira_cache.json` to force fresh data fetch

**Metrics Issues:**
- **Metrics show "No Data"?** 
  - Verify field mappings point to correct JIRA fields (Settings → Configure JIRA Mappings)
  - Check JIRA issues have values in mapped fields (not null/empty)
  - Review Status tab - ensure completion/active/WIP statuses configured
- **Wrong calculations?** 
  - DORA metrics: Check Environment tab for DevOps projects and production identifiers
  - Flow metrics: Check Types tab for work type classifications

**Profile Issues:**
- **Lost settings?** Each profile stores independent config in `profiles/{profile_id}/`
- **Switch profiles:** Use profile dropdown in top navigation
- **Manage queries:** Settings → Query Management to create, rename, or delete saved queries
- **Export/Import:** Settings → Import/Export to backup or transfer profiles
  - Export creates `.json` file with all profile data (config, queries, field mappings)
  - Import restores profile with all settings and data
- **Reset profile:** Settings → Profile Management → Delete profile and recreate

**Complete Reset:** Delete `profiles` folder

## Documentation

- **[Metrics Index](docs/metrics_index.md)** - Quick start guide to all metrics (Dashboard, DORA, Flow)
- **[Project Dashboard Metrics](docs/dashboard_metrics.md)** - Health score, velocity, forecasting
- **[DORA Metrics](docs/dora_metrics.md)** - Deployment frequency, lead time, CFR, MTTR
- **[Flow Metrics](docs/flow_metrics.md)** - Velocity, time, efficiency, load, distribution

---

**[⬆ Back to Top](#burndown-chart-generator)**
