# Burndown Chart Generator

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An interactive web app that helps you track project progress and forecast completion dates using burndown and burnup charts.

## Quick Start

1. **Install Python 3.13+** from [python.org](https://www.python.org)

2. **Get the code:**

   ```sh
   git clone https://github.com/niksavis/burndown-chart.git
   cd burndown-chart
   ```

3. **Set up environment:**

   ```sh
   python -m venv .venv
   .venv\Scripts\activate  # On macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run the app:**

   ```sh
   python app.py
   ```

5. **Open in browser:** [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

## What Can You Do With This App?

- **Track Project Progress**: See completion trends with interactive charts
- **Switch Views**: Toggle between burndown (work remaining) and burnup (work completed) charts
- **Get Forecasts**: View optimistic, most likely, and pessimistic completion dates
- **Monitor Scope Changes**: Track when requirements grow and get alerts for significant scope changes
- **Customize Parameters**: Set deadlines, initial scope, and analysis settings
- **Export Data**: Save charts as images or download raw data for reports

## Using Your Own Data

The application supports two data sources, which you can switch between using the **Data Source** radio buttons in the web interface:

### Data Source 1: JSON Import (File Upload)

Upload a CSV or JSON file with your project data. The application will automatically detect the format and convert it to the required structure.

**CSV Format:**

```csv
date;completed_items;completed_points;created_items;created_points
2025-03-01;5;50;0;0
2025-03-02;7;70;2;15
```

**JSON Format:**

```json
[
  {
    "date": "2025-03-01",
    "completed_items": 5,
    "completed_points": 50,
    "created_items": 0,
    "created_points": 0
  }
]
```

- `date`: When work was completed (YYYY-MM-DD)
- `completed_items`: Number of tasks finished that day
- `completed_points`: Story points/effort completed that day
- `created_items`: New tasks added that day
- `created_points`: Story points/effort added that day

**Tip**: Use the included sample file `statistics.csv` to test the app's features.

### Data Source 2: JIRA API (Direct Integration)

Connect directly to your JIRA instance for automatic data sync using flexible JQL queries. This allows you to pull real-time data from any JIRA issues that match your criteria.

#### Setup Environment Variables

Create a `.env` file in the project root or set these environment variables:

```bash
# Required
JIRA_URL=https://your-jira-instance.com
JIRA_DEFAULT_JQL=project = MYPROJECT AND created >= startOfYear()

# Optional
JIRA_TOKEN=your-personal-access-token
JIRA_STORY_POINTS_FIELD=customfield_10002
JIRA_CACHE_MAX_SIZE_MB=100
```

#### Configuration Options

- **JIRA_URL**: Your JIRA instance URL (required)
- **JIRA_DEFAULT_JQL**: Default JQL query for data retrieval (optional, defaults to "project = JRASERVER")
- **JIRA_TOKEN**: Personal access token (optional for public instances)
- **JIRA_STORY_POINTS_FIELD**: Custom field ID for story points (optional)
- **JIRA_CACHE_MAX_SIZE_MB**: Cache size limit in MB (optional, defaults to 100)

#### JQL Query Configuration

The application now supports flexible JQL (JIRA Query Language) queries, giving you powerful control over which issues are included in your burndown chart. The JQL query can be configured in multiple ways with the following priority:

1. **UI Settings** (highest priority): Set directly in the web interface
2. **Environment Variable**: Set `JIRA_DEFAULT_JQL` in your `.env` file  
3. **Default Value** (lowest priority): Falls back to `"project = JRASERVER"`

#### JQL Query Examples

**Basic project filtering:**

```jql
project = MYPROJECT
```

**Multiple projects:**

```jql
project in (PROJ1, PROJ2, PROJ3)
```

**Date range filtering:**

```jql
project = MYPROJECT AND created >= startOfYear()
```

**Complex filtering with ScriptRunner functions:**

```jql
project = MYPROJECT AND assignee in membersOf("developers")
```

**Status change tracking:**

```jql
project = MYPROJECT AND status changed to "Done" during (startOfYear(), now())
```

#### Using the UI

1. Start the app and go to the **Input Parameters** section
2. In the **Data Source** section, choose between:
   - **"JSON Import"**: For uploading CSV/JSON files
   - **"JIRA API (Auto-sync)"**: For direct JIRA integration
3. In the **Data Import** section, configure your chosen data source:
   - **For JSON Import**: Use the drag-and-drop area to upload your file
   - **For JIRA API**: Configure JIRA URL, JQL query, token, and points field
4. Click the unified **"Update Data"** button to import your data
5. Your charts will automatically update with the imported data

#### Unified Data Import

The application features a single **"Update Data"** button that intelligently handles both data sources:

- **When JSON Import is selected**: The button will remind you to use the file upload area above
- **When JIRA API is selected**: The button will sync data from JIRA using your configured JQL query
- **Both workflows** will overwrite the existing `forecast_statistics.csv` file and update all charts automatically
- **Settings are preserved**: Your configuration (PERT factors, deadlines, etc.) remains unchanged during data imports

#### Public JIRA Testing

For testing, you can use Atlassian's public JIRA:

- **URL**: `https://jira.atlassian.com`
- **Project**: `JRASERVER`
- **Token**: Leave empty (public access)

#### Troubleshooting JIRA Integration

- **Connection issues?** Verify your JIRA URL is accessible
- **Authentication errors?** Check your personal access token
- **No data?** Ensure project keys are correct and contain issues in the date range
- **Large cache?** Adjust `JIRA_CACHE_MAX_SIZE_MB` or use smaller date ranges
- **Slow performance?** Cache is stored locally - subsequent loads will be faster

## Troubleshooting

### General Issues

- **Missing packages?** Make sure you're in the virtual environment (`.venv\Scripts\activate`) and run `pip install -r requirements.txt` again
- **Port in use?** Change the port in app.py: `app.run_server(debug=True, port=8060)`
- **Data issues?** Delete `forecast_settings.json` and `forecast_statistics.csv` to reset

### JIRA Integration Issues

- **Connection issues?** Verify your JIRA URL is accessible
- **Authentication errors?** Check your personal access token
- **No data?** Ensure project keys are correct and contain issues in the date range
- **Large cache?** Adjust `JIRA_CACHE_MAX_SIZE_MB` or use smaller date ranges
- **Slow performance?** Cache is stored locally - subsequent loads will be faster
- **Cache corruption?** Delete `jira_cache.json` to force refresh

## License

[MIT License](LICENSE)

**[⬆ Back to Top](#burndown-chart-generator)**
