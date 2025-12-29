# Burndown Chart Generator

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![version](https://img.shields.io/badge/version-2.4.3-blue.svg)](https://github.com/niksavis/burndown-chart/releases)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**See when your project will finish.** Connect to JIRA, and get automatic forecasts, progress tracking, and team performance metrics - all in your browser.

**Perfect for:** Project managers, team leads, and anyone tracking agile projects who wants clear answers about timelines and team health.

## What You Get

- **📊 When Will We Finish?** - Automatic forecasts with best/worst/likely scenarios
- **📈 Is Our Team Healthy?** - Track velocity, spot bottlenecks, see trend warnings
- **🔌 Works With JIRA** - Connects directly to your JIRA projects
- **📋 Shareable Reports** - Generate HTML reports for stakeholders in seconds
- **🔒 Multiple Projects** - Switch between different teams/projects instantly

## Installation

**What you need:** Python 3.13+ installed on your computer

1. **Download the app:**
   ```bash
   git clone https://github.com/niksavis/burndown-chart.git
   cd burndown-chart
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # Or: .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

3. **Start the app:**
   ```bash
   python app.py
   ```
   
4. **Open in your browser:** [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

**First time?** You'll create your first profile through the app's guided setup.

## Connect to JIRA (Main Use Case)

**What you need:** JIRA URL, API token, and a query that finds your project's issues

### Step 1: Get Your JIRA Personal Access Token or API Token

1. Log into your JIRA account in a web browser
2. Access your user profile settings (usually via profile icon or account menu)
3. Look for Security, API tokens, or Personal Access Tokens section
4. Create a new token and copy it somewhere safe

**Note:** The exact location varies by JIRA version and configuration. Common paths include:
- Account Settings → Security → API tokens (Atlassian Cloud)
- Profile → Personal Access Tokens (JIRA Data Center/Server)
- Your administrator may provide organization-specific instructions

### Step 2: Connect the App to JIRA

1. In the app, click **Settings** (top right)
2. Go to **JIRA Configuration** section
3. Fill in:
   - **JIRA URL**: Your company's JIRA address (like `https://yourcompany.atlassian.net`)
   - **API Token**: Paste the token you created
   - **JIRA Query**: How to find your issues (like `project = MYPROJECT`)
4. Click **Fetch Metadata** - the app checks the connection and finds available fields

**💡 Don't have a JIRA query?** Try the public test: URL `https://jira.atlassian.com`, Query `project = JRASERVER` (no token needed)

### Step 3: Map Your JIRA Fields

The app needs to know which JIRA fields contain your data. Good news: it figures most of this out automatically.

1. Click **Configure JIRA Mappings** (opens a window with 5 tabs)
2. Click the **Auto-Configure** button
3. The app scans your JIRA and automatically maps:
   - Story points, status, issue types
   - Custom fields like deployment dates, severity, environment
   - Workflow statuses (completed, in progress, waiting)
4. Review the suggestions across the 5 tabs:
   - **Projects**: Which projects to track
   - **Fields**: Where to find story points, deployment dates, etc.
   - **Types**: What counts as a feature vs. bug vs. technical work
   - **Status**: Which statuses mean "done", "in progress", "waiting"
   - **Environment**: How to identify production deployments
5. Click **Save Mappings**

**💡 Tip:** Auto-Configure usually finds 80-90% of your fields correctly. Just check the ones marked in red and fix any that look wrong.

### Step 4: Load Your Data

1. Click the **Update Data** button (top of page)
2. Wait for the sync to finish (shows progress)
3. Your charts and metrics appear automatically!

**Smart Updates:** The app only downloads changed issues after the first sync. Super fast!

**Need to reload everything?** Long-press the Update Data button for 2 seconds to force a full refresh.

**Started a sync by mistake?** Click **Cancel Operation** to stop it.

## Understanding Your Metrics

### Project Health Dashboard

**What you see:**
- **When will we finish?** - Best case, worst case, most likely dates
- **Are we on track?** - Green = good, yellow = watch, red = trouble
- **How fast are we going?** - Items completed per week (velocity)
- **What's left?** - Remaining work in story points or number of items

**What to do:**
- Green health score (80-100): Keep going, share good news
- Yellow score (60-79): Watch for trends, maybe adjust timeline
- Red score (<60): Team meeting time - something needs attention

### Flow Metrics
*Measures how work moves through your development process - based on the Flow Framework*

Shows how work moves through your team:

- **Flow Velocity**: Items completed per week (is it stable?)
- **Flow Time**: Days from start to done (is it consistent?)
- **Flow Efficiency**: Percent of time actively working vs. waiting (25-40% is normal!)
- **Flow Load**: How much work in progress (less is better)
- **Flow Distribution**: Types of work (features vs. bugs vs. technical debt)

**What to do:**
- Velocity dropping? Check if team capacity changed
- Flow time increasing? Look for bottlenecks
- Too many bugs? Time to invest in quality
- Flow efficiency low? Reduce wait times and handoffs

### DORA Metrics
*DevOps Research and Assessment - industry-standard metrics for software delivery performance*

Measures how well your team delivers software:

- **Deployment Frequency**: How often you release to production
  - Elite teams: Multiple times per day
  - Good: Weekly or more
- **Lead Time**: Days from code commit to production release
  - Elite teams: Less than 1 day
  - Good: Less than 1 week
- **Change Failure Rate**: Percentage of releases that cause problems
  - Elite teams: 0-15%
  - Good: 16-30%
- **Recovery Time**: Hours to fix a production issue
  - Elite teams: Less than 1 hour
  - Good: Less than 1 day

**What to do:** Track trends over time. Small improvements each month add up!

## Common Tasks

### Switch Between Projects

Working on multiple teams or projects?

1. Click the **profile dropdown** (top navigation bar)
2. Select a different profile
3. All settings and data switch instantly

**Create new profile:** Settings → Profile Management → Create New Profile

### Save Multiple Queries Per Project

Track different views of the same project:

1. Set up a JIRA query and sync data
2. Settings → Query Management → Save Current Query
3. Give it a name (like "Sprint Backlog" or "Bugs Only")
4. Switch between saved queries anytime

### Generate Reports for Stakeholders

Create standalone HTML reports with all your metrics:

1. Settings → Import/Export → **Generate Report**
2. Choose what to include:
   - Dashboard overview
   - Burndown charts
   - Flow metrics
   - DORA metrics
3. Pick time period (4, 12, 26, or 52 weeks)
4. Click Generate → Download HTML file
5. Email it or open in any browser (works offline!)

**💡 Tip:** Generate weekly reports before team meetings so everyone sees the same data.

### Backup or Share Your Settings

**Two export modes:**

**Configuration Only** (~3KB file):
- Perfect for: Sharing JIRA setup with teammates
- Includes: URLs, queries, field mappings
- Excludes: Actual data and history
- Use when: "Here's how I configured JIRA for our project"

**Full Data** (~400KB file):
- Perfect for: Complete backup with all history
- Includes: Everything (settings + data + metrics)
- Use when: Moving to a new computer or archiving project data

**How to export:**
1. Settings → Import/Export → **Export Profile**
2. Choose mode (Configuration Only or Full Data)
3. Decide if you want to include your JIRA token (usually leave unchecked for security)
4. Download the JSON file

**How to import:**
1. Settings → Import/Export → **Import Profile**
2. Drag your JSON file or click to browse
3. If profile already exists, choose: Overwrite, Merge, or Rename
4. Done! All settings restored

**💡 Bonus:** Export includes ALL your saved queries, not just the active one.

## Need Help?

### Installation Problems

**"Python not found"**
- Install Python 3.13 or newer from [python.org](https://www.python.org)
- Make sure "Add to PATH" is checked during installation

**"Missing packages" or "ModuleNotFoundError"**
- Make sure you activated the environment: `.venv\Scripts\activate` (Windows) or `.venv/bin/activate` (macOS/Linux)
- Then run: `pip install -r requirements.txt`

**"Port already in use"**
- Another app is using port 8050
- Run with different port: `python app.py --port 8060`

### JIRA Connection Issues

**"Connection failed" or "Authentication error"**
- Double-check your JIRA URL (should include https://)
- Regenerate your API token (they expire!)
- Test the query in JIRA's web interface first

**"No data after sync"**
- Make sure your query actually returns issues in JIRA
- Try a simpler query first: `project = YOURPROJECT`

**"Missing Required Field" errors**
- Go to Settings → Configure JIRA Mappings
- Click Auto-Configure to let the app find fields automatically
- Check any fields marked in red and fix them

**Need to start over?**
- Settings → JIRA Configuration → Clear cache (forces fresh download)

### Metrics Show "No Data"

**Check field mappings:**
1. Settings → Configure JIRA Mappings
2. Make sure fields point to the right JIRA fields
3. Check that your JIRA issues actually have values in those fields

**Check status configuration:**
- Go to Status tab in Configure JIRA Mappings
- Make sure "completed" statuses are set (like "Done", "Closed")
- Make sure "in progress" statuses are set (like "In Progress", "In Review")

**DORA metrics missing?**
- Check Environment tab: Make sure production identifiers are set
- Check Projects tab: Make sure DevOps projects are marked

**Flow metrics wrong?**
- Check Types tab: Make sure work types are classified (Feature, Bug, Tech Debt)

### Profile & Data Issues

**Lost your settings?**
- Each profile saves automatically in a `profiles` folder
- Check Settings → Profile Management to see all profiles

**Want to start completely fresh?**
- Close the app
- Delete the `profiles` folder
- Start the app and create a new profile

**Export not working?**
- Make sure you have data loaded first (click Update Data)
- Try Configuration Only mode first (smaller file)

**Import not working?**
- Make sure you're importing a valid export file (JSON format)
- Choose how to handle conflicts: Overwrite, Merge, or Rename

## Advanced Features

### Multiple Projects (Profiles)

Track different teams or projects without mixing data:

1. **Create new profile:** Settings → Profile Management → Create New Profile
2. **Switch profiles:** Use dropdown in top navigation
3. **Each profile has:** Independent JIRA connection, queries, field mappings, and data

**Use case:** Manage 3 different teams, each with their own JIRA projects and settings.

### Scheduled Updates

Want fresh data without clicking Update Data?

**Manual refresh:** Click Update Data button
**Smart updates:** Only downloads changed issues (fast!)
**Force refresh:** Long-press Update Data button for 2 seconds (downloads everything)
**Cancel anytime:** Click Cancel Operation to stop

**Tip:** If you refresh the browser during an update, it continues in the background. Cancel button reappears when you return.

### Report Customization

Generate HTML reports with exactly what you need:

**Sections:**
- Dashboard: Health overview and forecasting
- Burndown Analysis: Charts, bug tracking, scope changes
- Flow Metrics: Team velocity and efficiency
- DORA Metrics: Deployment performance

**Time periods:** 4, 12, 26, or 52 weeks of history

**Output:** Single HTML file with embedded charts (works offline, no internet needed)

**How to customize report assets:** Edit [`report_dependencies.txt`](report_dependencies.txt) and run `python download_report_dependencies.py`

## Technical Reference

**For developers and advanced users**

### File Structure

When you run the app, it creates:
```
profiles/
  profiles.json                       # Registry of all profiles and active profile
  {profile_id}/
    profile.json                      # Settings and configuration
    queries/
      {query_id}/
        query.json                    # Query definition (JQL, name, description)
        project_data.json             # Metrics and statistics
        jira_cache.json               # Downloaded JIRA issues
        jira_changelog_cache.json     # Issue change history
        metrics_snapshots.json        # Historical data
```

### Data Flow

1. **JIRA Sync:** Connects to JIRA API using your token
2. **Smart Caching:** Only downloads changed issues after first sync
3. **Field Mapping:** Translates JIRA fields to app metrics
4. **Calculation Engine:** Computes DORA and Flow metrics
5. **Visualization:** Generates interactive charts

### API Integration

- **JIRA REST API:** Paginated requests (100 issues per page)
- **Caching:** 24-hour TTL with version tracking
- **Delta Updates:** Only fetches issues modified since last sync
- **Rate Limiting:** Respects JIRA API limits

### Security

- **API tokens:** Stored locally, never sent to external servers
- **Export safety:** JIRA tokens excluded by default
- **Local only:** All data stays on your machine
- **No telemetry:** No usage tracking or data collection

## More Information

**Detailed metric documentation:**
- **[Metrics Index](docs/metrics_index.md)** - Complete guide to all metrics
- **[Project Dashboard Metrics](docs/dashboard_metrics.md)** - Health score, velocity, forecasting
- **[DORA Metrics](docs/dora_metrics.md)** - Deployment frequency, lead time, CFR, MTTR
- **[Flow Metrics](docs/flow_metrics.md)** - Velocity, time, efficiency, load, distribution

---

**[⬆ Back to Top](#burndown-chart-generator)**
