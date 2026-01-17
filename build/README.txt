================================================================================
                         BURNDOWN CHART
                    Quick Start Guide for Windows
================================================================================

VERSION: 2.5.0

GETTING STARTED
---------------

1. Run the Application
   - Double-click "BurndownChart.exe" to start
   - A terminal window will open showing status messages
   - The app will automatically open in your default web browser

2. Access the Dashboard
   - If the browser doesn't open automatically, visit:
     http://127.0.0.1:8050
   - Bookmark this URL for easy access

3. First-Time Setup
   - Click Settings (top right corner)
   - Go to "JIRA Configuration" tab
   - Enter your JIRA URL and API token
   - Click "Fetch Metadata" to test connection
   - Click "Auto-Configure" to set up field mappings
   - Click "Update Data" to sync your issues

SYSTEM REQUIREMENTS
-------------------

- Windows 10 or later (64-bit)
- No Python installation required
- Internet connection for JIRA sync

WHAT THIS APP DOES
------------------

Burndown Chart helps project managers track agile projects by:
- Forecasting completion dates (best/worst/likely scenarios)
- Calculating project health scores (0-100)
- Tracking velocity and burndown trends
- Analyzing DORA and Flow metrics
- Generating shareable HTML reports

All data stays on your computer - no cloud services or tracking.

GETTING YOUR JIRA API TOKEN
----------------------------

1. Log into JIRA
2. Go to Profile Settings > Security
3. Create a new API Token
4. Copy the token and paste it into the app

Note: Token location varies by JIRA version. Contact your admin if you
can't find it.

TROUBLESHOOTING
---------------

Q: Port 8050 is already in use
A: Close other apps using port 8050, or edit app.py to use a different port

Q: The app won't start
A: Check Windows Defender - it may flag unsigned executables. Click "More info"
   and "Run anyway" to allow the app to run.

Q: Can't connect to JIRA
A: Verify your JIRA URL and API token. Try the test instance:
   URL: https://jira.atlassian.com
   Query: project = JRASERVER

Q: No data showing
A: Run "Auto-Configure" in Settings > Configure JIRA Mappings, then click
   "Update Data" to sync your issues.

MULTIPLE PROJECTS
-----------------

To track different teams, use the profile dropdown (top navigation bar) to
switch between project configurations.

REPORTS
-------

Generate standalone HTML reports via Settings > Import/Export > Generate Report.
Reports work offline and can be shared via email.

DATA STORAGE
------------

All data stored locally in: profiles/burndown.db
No telemetry or external services.

DOCUMENTATION
-------------

Full documentation available at:
https://github.com/niksavis/burndown-chart

LICENSE
-------

MIT License - See LICENSE file for details

SUPPORT
-------

For issues or questions:
https://github.com/niksavis/burndown-chart/issues

================================================================================
                    Thank you for using Burndown Chart!
================================================================================
