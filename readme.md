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

### Option 1: CSV Upload (Traditional)

Upload a CSV file with your project data. Format should be:

```csv
date;completed_items;completed_points;created_items;created_points
2025-03-01;5;50;0;0
2025-03-02;7;70;2;15
```

- `date`: When work was completed (YYYY-MM-DD)
- `completed_items`: Number of tasks finished that day
- `completed_points`: Story points/effort completed that day
- `created_items`: New tasks added that day
- `created_points`: Story points/effort added that day

**Tip**: Use the included sample file `statistics.csv` to test the app's features.

### Option 2: JIRA Integration (New!)

Connect directly to your JIRA instance for automatic data sync:

#### Setup Environment Variables

Create a `.env` file in the project root or set these environment variables:

```bash
# Required
JIRA_URL=https://your-jira-instance.com
JIRA_PROJECTS=PROJ1,PROJ2,PROJ3

# Optional
JIRA_TOKEN=your-personal-access-token
JIRA_STORY_POINTS_FIELD=customfield_10002
JIRA_DATE_FROM=2024-01-01
JIRA_DATE_TO=2025-07-18
JIRA_CACHE_MAX_SIZE_MB=100
```

#### Configuration Options

- **JIRA_URL**: Your JIRA instance URL (required)
- **JIRA_PROJECTS**: Comma-separated list of project keys (required)
- **JIRA_TOKEN**: Personal access token (optional for public instances)
- **JIRA_STORY_POINTS_FIELD**: Custom field ID for story points (optional)
- **JIRA_DATE_FROM**: Start date for data retrieval (optional, defaults to 1 year ago)
- **JIRA_DATE_TO**: End date for data retrieval (optional, defaults to today)
- **JIRA_CACHE_MAX_SIZE_MB**: Cache size limit in MB (optional, defaults to 100)

#### Using the UI

1. Start the app and go to the **Input Parameters** section
2. Select **"JIRA API (Auto-sync)"** as your data source
3. Configure your JIRA settings in the form
4. Click **"Refresh JIRA Cache"** to fetch data
5. Your charts will automatically update with JIRA data

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
