# Burndown Chart 🔥

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![version](https://img.shields.io/badge/version-2.7.5-blue.svg)](https://github.com/niksavis/burndown-chart/releases)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Forecast your project completion date.** Connect to JIRA and get automatic best/worst/likely scenarios based on your team's velocity. Track progress, spot bottlenecks, and generate shareable HTML reports - all running locally in your browser.

**Perfect for:** Project managers and team leads tracking agile projects.

## Key Features

- **📊 Completion Forecasts** - Best case, worst case, and most likely dates based on your team's actual velocity
- **📈 Project Health Score** - Single score (0-100) showing if you're on track with 6-dimensional analysis
- **📋 Shareable Reports** - Generate standalone HTML reports with all charts (works offline)
- **🔌 JIRA Integration** - Auto-syncs issues, smart caching only downloads what changed
- **🤖 AI Analysis Ready** - Export privacy-safe summaries for ChatGPT/Claude analysis
- **🔒 Multiple Projects** - Track different teams with separate profiles and settings
- **📊 Industry Metrics** - DORA metrics (DevOps performance) and Flow metrics (team efficiency)

**All data stays local** - No cloud services, no tracking, no telemetry.

## Download

**[📥 Download Latest Release](https://github.com/niksavis/burndown-chart/releases/latest)**

**Windows Users:** Download the Windows ZIP package - standalone executable, no Python required

**All Other Platforms:** Download source code (zip/tar.gz) - requires Python 3.13+

See installation instructions below for setup details.

## Installation

### Option 1: Windows (Standalone Executable)

**For non-technical users** - No Python installation required!

1. **Download** the latest Windows release from the [Releases page](https://github.com/niksavis/burndown-chart/releases/latest)
2. **Extract** the ZIP file to a folder of your choice (e.g., `C:\Program Files\BurndownChart`)
3. **Run** `BurndownChart\BurndownChart.exe` to start the application
4. **Open** your browser to [http://127.0.0.1:8050](http://127.0.0.1:8050)
5. **Optional**: Create a desktop shortcut to the EXE for easy access

**Note:** Windows may show a security warning on first run. Click "More info" → "Run anyway" (the app is not signed).

**Automatic Updates:** The app checks for updates automatically and notifies you when a new version is available. One-click download and install.

### Option 2: All Platforms (From Source)

**For technical users (Linux/macOS/Windows)** - Requires Python 3.13+

1. **Download** the source code from the [Releases page](https://github.com/niksavis/burndown-chart/releases/latest)
   - Click "Source code (zip)" or "Source code (tar.gz)"
   - Or clone the repository: `git clone https://github.com/niksavis/burndown-chart.git`

2. **Extract** and navigate to the project folder in terminal

3. **Install** - Create a virtual environment and install dependencies:
   
   **Windows:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```
   
   **Mac/Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

4. **Start** - Run `python app.py`

5. **Open** - Go to [http://127.0.0.1:8050](http://127.0.0.1:8050) in your browser

**For developers:** Want to work with the latest code? Clone the `main` branch:
```bash
git clone https://github.com/niksavis/burndown-chart.git
cd burndown-chart
# Follow installation steps above using requirements-dev.txt
```

**Note:** `requirements-dev.txt` includes testing/build tools. Use `requirements.txt` for production-only dependencies.

## Connecting to JIRA

### Get Your JIRA Token

1. Log into JIRA → Profile Settings → Security → Create API Token
2. Copy the token somewhere safe

**Note:** Token location varies by JIRA version (Cloud vs Data Center). Check with your admin if you can't find it.

### Connect in the App

1. **Settings** (top right) → **JIRA Configuration**
2. Enter:
   - **JIRA URL**: `https://yourcompany.atlassian.net`
   - **API Token**: Paste your token
   - **Query**: `project = MYPROJECT` (or try public test: `https://jira.atlassian.com` with query `project = JRASERVER`)
3. **Fetch Metadata** → **Configure JIRA Mappings** → **Auto-Configure**
4. Review the 5 tabs (the app auto-detects ~90% of fields) → **Save Mappings**
5. **Update Data** → Wait for sync → Done!

**Smart sync:** After first load, only downloads changed issues (fast!). Long-press Update Data for full refresh.

## What You'll See

### Dashboard
- **Completion Forecast**: Best/worst/likely dates based on velocity
- **Health Score** (0-100): Green (>80) = on track, Yellow (60-79) = watch closely, Red (<60) = needs attention
- **Velocity Chart**: Items completed per week with trend
- **Burndown Chart**: Remaining work vs. time with confidence bands

### Flow Metrics
Measures how work moves through your process:
- **Velocity**: Items/week (stability indicator)
- **Flow Time**: Start to done (cycle time)
- **Efficiency**: Active work vs. waiting (25-40% is normal)
- **Work Distribution**: Features vs. bugs vs. tech debt

### DORA Metrics  
Industry-standard DevOps performance:
- **Deployment Frequency**: Releases per day/week
- **Lead Time**: Commit to production (days)
- **Change Failure Rate**: % of releases with issues
- **Recovery Time**: Hours to fix production issues

**Learn more:** [Metrics Index](docs/metrics_index.md)

## Common Tasks

**Generate Reports:** Settings → Import/Export → Generate Report → Choose sections → Download HTML

**Multiple Projects:** Use profile dropdown (top nav) to switch between teams instantly

**Backup/Share Settings:** Settings → Import/Export → Export Profile (Configuration Only = small, Full Data = includes history)

**AI Analysis:** Settings → Import/Export → AI Prompt → Generate (privacy-safe summary for ChatGPT/Claude)

**Save Queries:** Track different views (e.g., "Sprint Backlog", "Bugs Only") - Settings → Query Management

## Troubleshooting

**Installation issues?**
- Missing Python? [Download 3.13+](https://www.python.org/downloads/) and check "Add to PATH"
- Missing packages? Activate environment first: `.venv\Scripts\activate` (Win) or `source .venv/bin/activate` (Mac)
- Port 8050 taken? Run `python app.py --port 8060`

**JIRA connection problems?**
- Click **Fetch Metadata** to test connection
- Regenerate token if expired (they do expire!)
- Try public test first: `https://jira.atlassian.com` with query `project = JRASERVER`
- Check query returns issues in JIRA web interface

**No data showing?**
- Run **Auto-Configure** in Settings → Configure JIRA Mappings
- Check Status tab: Set "Done", "Closed" as completed statuses
- For DORA: Check Environment tab for production identifiers
- For Flow: Check Types tab for work type classification

**Need fresh start?** Close app, delete `profiles` folder, restart

## How It Works

**Data Storage:** Everything stored locally in SQLite database (`profiles/burndown.db`). No cloud, no external services.

**JIRA Sync:** 
- First sync: Downloads all issues matching your query (paginated, 100/page)
- Subsequent syncs: Only downloads changed issues (delta updates)
- Smart caching with 24-hour TTL

**Security:**
- API tokens stored locally only
- No telemetry or tracking
- Export excludes tokens by default
- All processing happens on your machine

**Tech Stack:** Python 3.13, Dash/Plotly (UI), SQLite (storage), Waitress (server)

## Documentation

📚 **[Complete Documentation](docs/readme.md)** - Metrics guides, configuration, and architecture reference

For getting started with metrics, see the [Metrics Index](docs/metrics_index.md).

---

**License:** MIT | **Python:** 3.13+ | **Version:** 2.7.5

**[⬆ Back to Top](#burndown-chart-)**
