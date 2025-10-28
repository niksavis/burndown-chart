# Burndown Chart Generator

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Interactive web app for tracking project progress and forecasting completion dates with JIRA integration.

## Installation & Setup

1. **Prerequisites:** Python 3.13+ from [python.org](https://www.python.org)

2. **Install:**

   ```bash
   git clone https://github.com/niksavis/burndown-chart.git
   cd burndown-chart
   python -m venv .venv
   .venv\Scripts\activate  # Windows (.venv/bin/activate on macOS/Linux)
   pip install -r requirements.txt
   ```

3. **Run:**

   ```bash
   python app.py
   ```

   Then open: [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

## Features

- **📊 Interactive Charts**: Burndown (remaining work) & burnup (completed work) views
- **🔮 PERT Forecasting**: Optimistic, most likely, and pessimistic completion predictions  
- **📈 Scope Tracking**: Monitor requirement changes with alerts for significant shifts
- **🔌 JIRA Integration**: Direct API sync with flexible JQL queries and caching
- **📁 File Import**: CSV/JSON upload support with automatic format detection
- **💾 Export Options**: Download charts and data for reports
- **⚙️ Advanced Metrics**: Scope stability dashboard and growth tracking

## Data Sources

**Two Ways to Import Data:**

### 📁 File Upload (CSV/JSON)

Upload project data files. Sample formats:

**CSV Format:**

```csv
date;completed_items;completed_points;created_items;created_points
2025-03-01;5;50;0;0
2025-03-02;7;70;2;15
```

**JSON Format with Project Scope:**

```json
{
  "project_scope": {
    "total_items": 100,
    "total_points": 500,
    "completed_items": 25,
    "completed_points": 120,
    "remaining_items": 75,
    "remaining_points": 380,
    "estimated_items": 60,
    "estimated_points": 300
  },
  "statistics": [
    {
      "date": "2025-03-01",
      "completed_items": 5,
      "completed_points": 50,
      "created_items": 0,
      "created_points": 0
    },
    {
      "date": "2025-03-02", 
      "completed_items": 7,
      "completed_points": 70,
      "created_items": 2,
      "created_points": 15
    }
  ]
}
```

### 🔌 JIRA API Integration  

Connect directly to JIRA with flexible JQL queries. The app uses a **4-tier configuration priority**:

1. **Web Interface Settings** (highest priority) - values entered directly in the UI
2. **`app_settings.json` File** - persistent configuration file  
3. **Environment Variables** - system fallback values
4. **Built-in Defaults** (lowest priority) - hardcoded fallbacks

Configure via the web interface **Data Import Configuration** section, or optionally in `app_settings.json`:

#### Option 1: Web Interface (Recommended)

- Open the app and go to **Input Parameters → Data Import Configuration**
- Configure JIRA API Endpoint (URL), JQL query, token, and story points field
- Settings are automatically saved to `app_settings.json`

#### Option 2: Direct File Edit (Optional)

Edit `app_settings.json` directly with your JIRA configuration:

```json
{
  "jql_query": "project = MYPROJECT AND created >= startOfYear()",
  "jira_api_endpoint": "https://your-jira-instance.com/rest/api/2/search",
  "jira_token": "your-personal-access-token",
  "jira_story_points_field": "customfield_10002"
}
```

#### Option 3: Environment Variables (Optional)

```bash
JIRA_API_ENDPOINT=https://your-jira-instance.com/rest/api/2/search
JIRA_DEFAULT_JQL=project = MYPROJECT AND created >= startOfYear()
JIRA_TOKEN=your-personal-access-token  # Optional for public instances
JIRA_STORY_POINTS_FIELD=customfield_10002  # Optional custom field ID
```

**Quick Test**: Use `https://jira.atlassian.com/rest/api/2/search` with JQL `project = JRASERVER` (no token needed).

## DORA & Flow Metrics Dashboard

The app includes comprehensive **DevOps Research and Assessment (DORA)** and **Flow Framework** metrics for measuring software delivery performance and value stream efficiency.

### DORA Metrics

Track the four key metrics that define high-performing software teams:

#### 1. Deployment Frequency
- **What**: How often you deploy to production
- **Measures**: Team's deployment cadence and release velocity
- **Performance Tiers**:
  - **Elite**: Multiple deploys per day
  - **High**: Between once per day and once per week
  - **Medium**: Between once per week and once per month
  - **Low**: Fewer than once per month

#### 2. Lead Time for Changes
- **What**: Time from code commit to production deployment
- **Measures**: Development cycle efficiency
- **Performance Tiers**:
  - **Elite**: Less than one day
  - **High**: Between one day and one week
  - **Medium**: Between one week and one month
  - **Low**: More than one month

#### 3. Change Failure Rate
- **What**: Percentage of deployments causing production failures
- **Measures**: Release quality and stability
- **Performance Tiers**:
  - **Elite**: 0-15%
  - **High**: 16-30%
  - **Medium**: 31-45%
  - **Low**: More than 45%

#### 4. Mean Time to Recovery (MTTR)
- **What**: Average time to restore service after incident
- **Measures**: Incident response effectiveness
- **Performance Tiers**:
  - **Elite**: Less than one hour
  - **High**: Less than one day
  - **Medium**: Between one day and one week
  - **Low**: More than one week

### Flow Framework Metrics

Measure value delivery across your development pipeline:

#### 1. Flow Velocity
- **What**: Number of work items completed per time period
- **Measures**: Team throughput and productivity

#### 2. Flow Time
- **What**: Average time from work start to completion
- **Measures**: Cycle time efficiency

#### 3. Flow Efficiency
- **What**: Percentage of time work is actively progressing
- **Measures**: Process waste and wait times

#### 4. Flow Load
- **What**: Total work in progress across all stages
- **Measures**: System capacity utilization

#### 5. Flow Distribution
- **What**: Breakdown of work across four types
- **Measures**: Value stream balance
- **Types**:
  - **Features**: New capabilities (Recommended: 40-70%)
  - **Defects**: Bug fixes (Recommended: <10%)
  - **Technical Debt**: Infrastructure improvements (Recommended: 10-20%)
  - **Risk**: Security, compliance work (Recommended: 10-20%)

### Configuration

#### Field Mapping

DORA and Flow metrics require specific JIRA field mappings:

1. **Open Field Configuration**: Click "Configure Field Mappings" button on the DORA/Flow dashboard
2. **DORA Fields**:
   - **Deployment Date**: Field containing deployment/release date
   - **Deployment Successful**: Boolean field indicating deployment success
   - **Incident Start**: Field with incident creation timestamp
   - **Incident Resolved**: Field with incident resolution timestamp
3. **Flow Fields**:
   - **Work Started Date**: When work began (e.g., "In Progress" timestamp)
   - **Work Completed Date**: When work finished (e.g., "Done" timestamp)
   - **Work Type**: Field classifying work (Feature, Bug, Technical Debt, Risk)
   - **Work Item Size**: Story points or effort estimate field
4. **Save Mappings**: Configuration stored in `app_settings.json` and cached for performance

#### Time Period Selection

- **Last 7 Days**: Recent sprint or weekly metrics
- **Last 30 Days**: Monthly performance overview
- **Last 90 Days**: Quarterly trends and patterns
- **Custom Range**: Select specific date ranges for analysis

### Export Options

Export metrics data for external reporting and analysis:

- **CSV Format**: Spreadsheet-ready with headers and formatted values
  - Includes: Metric names, values, performance tiers, trends, time period
  - Opens directly in Excel, Google Sheets, or any CSV viewer
  - Example filename: `dora_metrics_20251028_143000.csv`

- **JSON Format**: Structured data for programmatic access
  - Includes: ISO 8601 timestamps, metric type, nested structures
  - Ideal for BI tools, data warehouses, or custom analytics
  - Example filename: `flow_metrics_20251028_143000.json`

**How to Export**:
1. Navigate to DORA or Flow Metrics dashboard
2. Configure time period and refresh metrics
3. Click "Export CSV" or "Export JSON" button
4. File downloads automatically with timestamp

### Trend Analysis

View historical trends for each metric:

- **Show Trend Button**: Click on any metric card to expand trend chart
- **Trend Direction**: Up/down/stable indicators with percentage change
- **Historical Data**: Line charts showing metric evolution over time
- **Benchmark Lines**: Performance tier thresholds overlaid on charts

### Troubleshooting DORA/Flow Metrics

**No Data Displayed**:
- Verify field mappings are configured correctly
- Check that JIRA issues exist in selected time period
- Ensure mapped fields contain valid data

**Incorrect Calculations**:
- Review field mapping configuration
- Verify custom field IDs match your JIRA instance
- Check that issue types are correctly classified

**Performance Issues**:
- Reduce time period range for faster calculations
- Clear metrics cache: delete relevant cache files
- Use more specific JQL queries to limit dataset

## Troubleshooting

### Common Issues

- **Missing packages?** Activate virtual environment: `.venv\Scripts\activate`, then `pip install -r requirements.txt`
- **Port in use?** Run with different port: `python app.py --port 8060` or set environment variable: `$env:BURNDOWN_PORT=8060`
- **Data issues?** Delete `project_data.json`, `app_settings.json`, and `jira_cache.json` to reset

### JIRA Issues

- **Connection failed?** Check JIRA API endpoint URL and network access
- **Auth errors?** Verify personal access token
- **No data?** Ensure project keys exist and contain issues in date range
- **Cache problems?** Delete `jira_cache.json` to force refresh

## License

[MIT License](LICENSE)

**[⬆ Back to Top](#burndown-chart-generator)**
