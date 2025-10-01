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

3. **Initial Configuration (Optional):**

   The app works immediately with sample data. For JIRA integration, you can either:
   
   - **Option A:** Configure via the web interface (recommended)
   - **Option B:** Copy `app_settings.json.example` to `app_settings.json` and edit it
   
   ```bash
   copy app_settings.json.example app_settings.json  # Windows
   cp app_settings.json.example app_settings.json    # macOS/Linux
   ```

4. **Run:**

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
