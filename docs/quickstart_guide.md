# Burndown - First-Time Setup Guide

**Audience**: New users setting up the application for the first time  
**Time Required**: 15-30 minutes  
**Prerequisites**: JIRA instance access, API token

This guide walks you through the complete first-time setup process from launching the app to viewing your first burndown chart.

---

## Setup Overview

The application uses a **progressive disclosure** design - each step unlocks the next. Follow this sequence:

1. **Profile Creation** - Create your workspace
2. **JIRA Connection** - Connect to your JIRA instance
3. **Field Mapping** - Map JIRA fields to metrics
4. **Query Creation** - Define what issues to track
5. **Parameter Configuration** - Set deadline, milestones, data points
6. **Data Update** - Fetch and analyze data

**Related Guides**:
- [JIRA Configuration Guide](jira_configuration.md)
- [Profile Management Guide](profile_management.md)
- [Query Management Guide](query_management.md)
- [JQL Editor Guide](jql_editor.md)

---

## Step 1: Create a Profile

**What**: Profiles are workspaces that isolate settings for different projects or teams.

**How**:
1. Click **"Profile Settings"** in the left sidebar
2. Enter profile name (e.g., "Apache Kafka", "Q1 Project")
3. Add optional description
4. Click **"Create Profile"**

**Notes**:
- First-time users must create their first profile manually (no default profile is created)
- You can create multiple profiles for different projects
- Switching profiles changes ALL settings (JIRA connection, queries, mappings)

---

## Step 2: Configure JIRA Connection

**What**: Connect to your JIRA instance to fetch issue data.

**How**:
1. Click **"JIRA Connection"** → **"Configure JIRA"**
2. Enter your JIRA URL:
   - JIRA Cloud: `https://yourcompany.atlassian.net`
   - JIRA Server/Data Center: `https://jira.yourcompany.com`
3. Generate API token:
   - **JIRA Cloud**: Go to your Atlassian account settings → Security → API tokens → Create and label new token
   - **JIRA Server**: Navigate to your user profile → Personal Access Tokens → Create token
4. Paste token into **"API Token"** field
5. Adjust **"API Version"** if needed (default: `v2`, use `v3` for newer JIRA Cloud)
6. Click **"Test Connection"** → wait for ✅ success
7. Click **"Save Configuration"**

**Configuration Fields**:

| Field              | Description               | Default       | Notes                                               |
| ------------------ | ------------------------- | ------------- | --------------------------------------------------- |
| **Base URL**       | JIRA instance URL         | None          | Required. No trailing slash                         |
| **API Token**      | Authentication token      | None          | Required for authentication                         |
| **API Version**    | REST API version          | `v2`          | Use `v3` for newer JIRA Cloud                       |
| **Estimate Field** | Story points custom field | Auto-detected | Optional. Stored in JIRA config, not field mappings |

**Note**: The Estimate Field (story points) is stored separately in JIRA configuration rather than in Field Mappings. This allows the app to normalize story points across all metrics without duplicating the configuration.

**Troubleshooting**:
- **401 Unauthorized**: Check token validity, regenerate if expired
- **404 Not Found**: Verify JIRA URL, check API version (try `v2` for older servers)
- **Network Error**: Check firewall, VPN, or proxy settings

---

## Step 3: Map JIRA Fields to Metrics

**What**: Tell the app which JIRA fields contain deployment dates, work types, statuses, etc.

**How**:

### Option A: Auto-Configure (Recommended)
1. Navigate to **"Field Mappings"** section
2. Click **"Auto-Configure"** button
3. Review detected mappings
4. **Important**: Navigate to **"Project"** tab and configure:
   - **Development Projects**: Projects containing feature work (e.g., `PROJ, FEAT`)
   - **DevOps Projects**: Projects containing infrastructure/deployment work (e.g., `INFRA, DEVOPS`)
5. Adjust field mappings if needed (see manual configuration below)
6. Click **"Save Mappings"**

Auto-configure analyzes your last 100 issues to detect:
- Deployment/resolution dates
- Work types (Story, Bug, Task)
- Status fields
- Custom fields with deployment/incident data

**Note**: Auto-configure does NOT set Development Projects or DevOps Projects - you must configure these manually in the **"Project"** tab.

**Verified**: `auto_configure.py` initializes `development_projects` and `devops_projects` as empty lists and only populates `development_projects` if a JQL query is provided, but this is for internal defaults. User must explicitly configure both lists in the UI.

### Option B: Manual Configuration
1. Navigate to **"Field Mappings"** section
2. Navigate to **"Project"** tab first:
   - **Development Projects**: Enter comma-separated project keys (e.g., `PROJ, FEAT, APP`)
   - **DevOps Projects**: Enter comma-separated project keys (e.g., `INFRA, PLATFORM, OPS`)
3. Expand metric category (DORA or Flow)
4. For each field:
   - Click dropdown → select JIRA field
   - For filter fields: Add `=Value` suffix (e.g., `customfield_11309=PROD`)
5. Click **"Save Mappings"**

### Understanding Project Separation

**Why Separate Development and DevOps Projects?**
- **Development Projects**: Track feature development cycle time (coding → deployment)
- **DevOps Projects**: Track infrastructure/deployment cycle time (request → implementation)
- Separating them prevents mixing different workflows with different performance characteristics

**What if I use the same project in both?**
- ⚠️ **Metrics will be inflated**: The app counts deployments and incidents from BOTH project lists
- ⚠️ **Double-counting risk**: If project `PROJ` is in both lists, its work is counted twice in DORA metrics
- ✅ **Use case**: Small teams where development and DevOps work happens in same project - include ONLY in Development Projects
- ✅ **Recommended**: Keep lists mutually exclusive (no overlapping project keys)

**Example Configurations**:

| Scenario                      | Development Projects | DevOps Projects | Notes                                   |
| ----------------------------- | -------------------- | --------------- | --------------------------------------- |
| Separate teams                | `PROJ, FEAT`         | `INFRA, OPS`    | Cleanest separation                     |
| Single team, separate project | `PROJ`               | `PROJ-INFRA`    | Use suffixes to distinguish             |
| Single team, same project     | `PROJ`               | _(leave empty)_ | All work tracked as development         |
| Multi-team organization       | `TEAM1, TEAM2, WEB`  | `PLATFORM, SRE` | Scale to multiple development teams     |
| No infrastructure work        | `PROJ`               | _(leave empty)_ | DevOps metrics will show N/A or no data |

**Namespace Syntax**: The app supports advanced field references:
- `*.created` - Standard JIRA field (any project)
- `customfield_10100` - Custom field ID
- `customfield_11309=PROD` - Custom field with value filter (for environments)
- `*.Status:Deployed.DateTime` - Status change timestamp (from changelog)

See [Namespace Syntax Guide](namespace_syntax.md) for advanced patterns.

---

## Step 4: Field Mapping Reference

### Required Fields by Metric Category

**Understanding Namespace Syntax**:

The app uses **namespace syntax** to extract values from JIRA changelog history rather than relying solely on current field values. This enables precise timestamp tracking for status transitions and deployments.

**Syntax Patterns**:
- `*.created` - Standard JIRA field (asterisk means "any project")
- `customfield_10100` - Direct custom field reference
- `customfield_11309=PROD` - Custom field with value filter (e.g., production environment)
- `*.Status:Deployed.DateTime` - **Changelog-based**: Timestamp when status changed to "Deployed"

**Why Changelog-Based?**
- Standard fields like `resolutiondate` only show when an issue closed, not when it was deployed
- Namespace syntax `Status:Deployed.DateTime` extracts the exact moment status changed to "Deployed" from changelog
- Enables accurate Lead Time and Deployment Frequency metrics without custom date fields

**Example**: `*.Status:Deployed.DateTime` searches the issue's changelog history for when status changed to "Deployed" and returns that timestamp. This is more accurate than using `resolutiondate` for deployment tracking.

See [Namespace Syntax Guide](namespace_syntax.md) for advanced patterns and field resolution rules.

---

#### Dashboard Metrics (Basic Project Tracking)
**Minimal Setup**: Uses standard JIRA fields - no custom mappings required
- ✅ Works with: `created`, `updated`, `status`, `issuetype`
- 📊 Provides: Health score, velocity, remaining work, completion forecast

#### DORA Metrics (DevOps Performance)

| Field Name               | Purpose                     | Required | Typical JIRA Mapping                             | Custom Field Needed?              |
| ------------------------ | --------------------------- | -------- | ------------------------------------------------ | --------------------------------- |
| **Deployment Date**      | When code deployed          | Yes      | `resolutiondate` or `*.Status:Deployed.DateTime` | Optional (can use changelog)      |
| **Target Environment**   | Filter production deploys   | Optional | `customfield_11309=PROD`                         | Yes (if filtering by environment) |
| **Change Failure**       | Identify failed deployments | Optional | `customfield_12708=Yes`                          | Yes (checkbox field)              |
| **Incident Start**       | Bug/incident opened         | Yes      | `created`                                        | No (standard field)               |
| **Incident End**         | Bug/incident resolved       | Yes      | `resolutiondate`                                 | No (standard field)               |
| **Affected Environment** | Filter production bugs      | Optional | `customfield_11309=PROD`                         | Yes (if filtering by environment) |
| **Severity Level**       | Bug priority                | Optional | `priority` or `customfield_11000`                | Optional                          |

#### Flow Metrics (Work Process Health)

| Field Name              | Purpose                               | Required | Typical JIRA Mapping                         | Custom Field Needed?         |
| ----------------------- | ------------------------------------- | -------- | -------------------------------------------- | ---------------------------- |
| **Work Item Type**      | Classify work (Feature/Bug/Debt/Risk) | Yes      | `issuetype` or `customfield_10301`           | Optional (can use issuetype) |
| **Work Started Date**   | When work begins                      | Yes      | `created` or `*.Status:InProgress.DateTime`  | Optional (can use changelog) |
| **Work Completed Date** | When work finishes                    | Yes      | `resolutiondate` or `*.Status:Done.DateTime` | Optional (can use changelog) |
| **Status**              | Current state                         | Yes      | `status`                                     | No (standard field)          |
| **Estimate**            | Story points/effort                   | Optional | `customfield_10002` ("Story Points")         | Yes (for velocity tracking)  |
| **Effort Category**     | Secondary classification              | Optional | `customfield_10301` ("Effort Type")          | Optional                     |

### Common Custom Field Patterns

#### Story Points
```
Field ID: customfield_10002
Field Name: Story Points
Field Type: Number
Required In: Flow Metrics (optional)
```

#### Environment (Production/SIT/DEV)
```
Field ID: customfield_11309
Field Name: Environment
Field Type: Select List (single choice)
Values: DEV, SIT, PROD
Required In: DORA Metrics (optional)
Mapping Syntax: customfield_11309=PROD
```

#### Deployment Failed (Change Failure)
```
Field ID: customfield_12708
Field Name: Deployment Failed?
Field Type: Checkbox or Select List
Values: Yes/No or Checked/Unchecked
Required In: DORA Metrics (optional)
Mapping Syntax: customfield_12708=Yes
```

#### Effort/Work Type
```
Field ID: customfield_10301
Field Name: Effort Category
Field Type: Select List (single choice)
Values: Feature, Defect, Tech Debt, Risk
Required In: Flow Metrics (optional)
```

---

## Step 5: Create Custom Fields in JIRA (If Needed)

**When**: Only if you want advanced DORA/Flow metrics and don't have existing custom fields

**JIRA Cloud**:
1. Go to **⚙️ Settings** → **Issues** → **Custom Fields**
2. Click **"Create Custom Field"**
3. Select field type:
   - **Select List (single choice)** - for Environment, Work Type
   - **Checkbox** - for Deployment Failed
   - **Number Field** - for Story Points
4. Enter field name (e.g., "Environment", "Story Points")
5. For Select Lists: Add options (e.g., DEV, SIT, PROD)
6. Associate with screens (Edit Screen, Create Screen, View Screen)
7. Note the field ID (e.g., `customfield_11309`)

**JIRA Server/Data Center**:
1. Go to **Administration** → **Issues** → **Custom Fields**
2. Click **"Add Custom Field"**
3. Follow same steps as JIRA Cloud
4. Assign to appropriate project schemes

**Field Naming Best Practices**:
- Use descriptive names: "Deployment Environment" not "Env"
- Be consistent across projects if using multiple
- Document field purpose in field description

---

## Step 6: Create a Query

**What**: Define which JIRA issues to track (equivalent to saved filter)

**How**:
1. Navigate to **"Query Management"** section
2. Enter query name (e.g., "Apache Kafka Project", "Platform Team")
3. Write JQL (JIRA Query Language):
   ```jql
   project = KAFKA AND issuetype IN (Story, Bug, Task)
   ```
4. Click **"Test Query"** → verify issue count
5. Click **"Save Query"**
6. Query becomes active automatically

**Best Practice - Flight Level 2 Approach**:

The application works best with **broad, time-agnostic queries** that capture all work items:

✅ **DO**: Query entire project(s) with issue type filters
```jql
project IN (KAFKA, PLATFORM) AND issuetype IN (Story, Bug, Task)
```

❌ **DON'T**: Filter by sprint, time periods, or specific epics
```jql
# Avoid - limits historical data for metrics
project = KAFKA AND sprint = 42 AND created >= -30d
```

**Why?**
- App analyzes **full project history** for accurate velocity, lead time, and flow metrics
- Time filters (sprint, created date) break historical trend analysis
- Epic filters limit visibility into overall project flow
- Flight Level 2 (operational work) includes Stories, Bugs, Tasks but excludes Epics (strategic) and Sub-tasks (technical breakdown)

**Issue Type Filtering**:
- ✅ **Include**: Story, Bug, Task (operational work items)
- ❌ **Exclude**: Epic (strategic level), Sub-task (implementation detail)
- Reason: Epics are too large for metrics, Sub-tasks double-count work

**Recommended JQL Patterns**:

```jql
# Single project, all operational work
project = MYPROJECT AND issuetype IN (Story, Bug, Task)

# Multiple projects, same team
project IN (WEB, API, MOBILE) AND issuetype IN (Story, Bug, Task)

# Project with additional filter (e.g., component)
project = MYPROJECT AND component = Backend AND issuetype IN (Story, Bug, Task)

# Multiple teams with project prefixes
project IN (TEAM1-DEV, TEAM1-OPS, TEAM1-INFRA) AND issuetype IN (Story, Bug, Task)
```

**Tip**: Test your JQL in JIRA first (Filters → Advanced Issue Search)

---

## Step 7: Configure Parameters

**What**: Set project deadline, milestone dates, and chart preferences

**How**:

### Deadline (Optional)
1. Scroll to **"Deadline Settings"**
2. Toggle **"Show Deadline on Chart"**
3. Pick date from calendar
4. Appears as vertical line on burndown chart

### Milestone (Optional)
1. Scroll to **"Milestone Settings"**
2. Toggle **"Show Milestone on Chart"**
3. Pick date from calendar
4. Appears as vertical line on burndown chart

### Data Points Slider
1. Scroll to **"Visualization Settings"**
2. Adjust **"Data Points for Forecast"** slider (3-24)
3. Default: 12 weeks
4. More points = longer forecast range, but requires more historical data

### Forecast Range (Advanced)
1. Scroll to **"Forecast Settings"**
2. Adjust **"Forecast Range"** slider (3-12 weeks)
3. Default: 6 weeks
4. Controls how many weeks of historical data to sample for best and worst case forecasts
5. Lower range = more responsive to recent changes, higher range = more stable long-term forecast
6. See [Dashboard Metrics Guide](dashboard_metrics.md) for PERT calculation details

---

## Step 8: Update Data

**What**: Fetch issues from JIRA and calculate metrics

**How**:
1. Click **"Update Data"** button (right sidebar)
2. Wait for progress bar:
   - Fetching issues from JIRA
   - Parsing changelog history
   - Calculating metrics
   - Rendering charts
3. View results in **"Project Dashboard"** tab

**First-Time Tips**:
- First update takes longer (fetching changelog history)
- Subsequent updates are faster (incremental)
- Click **"Update Data"** whenever:
  - You change queries
  - You update field mappings
  - JIRA data changes significantly

**Troubleshooting**:
- **"No data available"**: Check query returns issues (Test Query in Step 6)
- **"DORA metrics unavailable"**: Verify field mappings (Step 3)
- **Long load times**: Reduce query scope, check network connectivity

---

## Step 9: Interpret Your First Chart

After data update completes, you should see:

### Project Dashboard Tab
- **Burndown Chart**: Actual progress (orange), ideal line (blue), forecast (gray)
- **Health Score**: 6-dimensional assessment (0-100 scale)
- **Statistics Cards**: Velocity, remaining work, completion date
- **Insights Panel**: Automated alerts for risks and trends

### DORA & Flow Metrics Tab
- **DORA Cards**: Deployment frequency, lead time, change failure rate, MTTR
- **Flow Cards**: Velocity, flow time, efficiency, WIP, distribution
- **Charts**: Weekly trends over time

**What to Look For**:
- ✅ **Burndown slope decreasing** = Good progress
- ⚠️ **Burndown slope flat** = Velocity issues
- ❌ **Burndown slope increasing** = Scope creep
- 📊 **Health score 70+** = Healthy project
- 📉 **Health score <50** = Risk, investigate

---

## Typical Field Mapping Configurations

### Minimal Setup (Dashboard Metrics Only)
**No custom fields needed** - uses standard JIRA fields:
```yaml
# Auto-detected, no mapping required
created: (standard field)
updated: (standard field)
status: (standard field)
issuetype: (standard field)
```

**Provides**: Health score, velocity, remaining work, completion forecast

---

### DORA Metrics Setup (Production Deployments)

#### Scenario A: Using Changelog Only (No Custom Fields)
```yaml
Deployment Date: *.Status:Deployed.DateTime
Incident Start: created
Incident End: resolutiondate
```

**Custom Fields Needed**: None (uses JIRA standard fields + changelog)  
**Limitation**: Cannot filter by environment (counts all deployments)

#### Scenario B: With Environment Filtering (Requires Custom Field)
```yaml
Deployment Date: *.Status:Deployed.DateTime
Target Environment: customfield_11309=PROD
Change Failure: customfield_12708=Yes
Incident Start: created
Incident End: resolutiondate
Affected Environment: customfield_11309=PROD
```

**Custom Fields Needed**:
1. **Environment** (`customfield_11309`) - Select List (DEV, SIT, PROD)
2. **Deployment Failed** (`customfield_12708`) - Checkbox (Yes/No)

**Provides**: Deployment frequency, lead time, change failure rate, MTTR (production-only)

---

### Flow Metrics Setup (Work Process)

#### Scenario A: Using Issue Type Only (Minimal)
```yaml
Work Item Type: issuetype
Work Started Date: created
Work Completed Date: resolutiondate
Status: status
```

**Custom Fields Needed**: None (uses standard JIRA fields)  
**Limitation**: Work distribution based on JIRA issue types only

#### Scenario B: With Story Points and Custom Work Classification
```yaml
Work Item Type: customfield_10301
Work Started Date: *.Status:InProgress.DateTime
Work Completed Date: *.Status:Done.DateTime
Status: status
Estimate: customfield_10002
```

**Custom Fields Needed**:
1. **Story Points** (`customfield_10002`) - Number field
2. **Effort Category** (`customfield_10301`) - Select List (Feature, Defect, Tech Debt, Risk)

**Provides**: Flow velocity, flow time, efficiency, WIP, distribution (with story points)

---

### Full Setup (All Metrics)

**Required Custom Fields**:
1. **Story Points** (`customfield_10002`) - Number
2. **Environment** (`customfield_11309`) - Select List (DEV, SIT, PROD)
3. **Deployment Failed** (`customfield_12708`) - Checkbox
4. **Effort Category** (`customfield_10301`) - Select List (Feature, Defect, Tech Debt, Risk)

**Field Mappings**:
```yaml
# DORA Metrics
deployment_date: *.Status:Deployed.DateTime
target_environment: customfield_11309=PROD
change_failure: customfield_12708=Yes
incident_start: created
incident_end: resolutiondate
affected_environment: customfield_11309=PROD

# Flow Metrics
work_item_type: customfield_10301
work_started_date: *.Status:InProgress.DateTime
work_completed_date: *.Status:Done.DateTime
status: status
estimate: customfield_10002
```

**Provides**: All dashboard, DORA, and Flow metrics with full accuracy

---

## Common First-Time Issues

### "JIRA Configuration Not Set Up"
**Cause**: Trying to map fields before configuring JIRA connection  
**Solution**: Complete Step 2 (JIRA Connection) first

### "No Issues Returned from Query"
**Cause**: JQL query too restrictive or incorrect  
**Solution**: Test JQL in JIRA first, verify project key and issue types exist

### "DORA Metrics Unavailable"
**Cause**: Missing required field mappings  
**Solution**: Map at least `deployment_date` and `incident_start/end` fields

### "Auto-Configure Doesn't Detect Custom Fields"
**Cause**: Custom fields have generic names like "Custom Field 1"  
**Solution**: Use descriptive field names in JIRA (e.g., "Deployment Environment")

### "Chart Shows No Data"
**Cause**: Query returns 0 issues or issues have no completion dates  
**Solution**: 
- Verify query returns issues (Test Query)
- Check issues have resolution dates
- Expand date range in query

---

## What's Next?

After completing setup:

1. **Learn Metrics** → [Metrics Index](metrics_index.md) for comprehensive guides
2. **Understand Health Score** → [Project Health Formula](health_formula.md)
3. **Validate Configuration** → [Metrics Correlation Guide](metrics_correlation_guide.md)
4. **Advanced Field Mapping** → [Namespace Syntax](namespace_syntax.md)

---

## Quick Reference Card

| Step | Action                 | Where                                 | Time    |
| ---- | ---------------------- | ------------------------------------- | ------- |
| 1    | Create profile         | Profile Settings                      | 1 min   |
| 2    | Configure JIRA         | JIRA Connection → Configure JIRA      | 3 min   |
| 3    | Map fields             | Field Mappings → Auto-Configure       | 2 min   |
| 4    | Create query           | Query Management → Save Query         | 3 min   |
| 5    | Set deadline/milestone | Deadline Settings, Milestone Settings | 2 min   |
| 6    | Update data            | Update Data button (right sidebar)    | 1-5 min |
| 7    | View results           | Project Dashboard tab                 | -       |

**Total Time**: ~15 minutes (excluding custom field creation in JIRA)

---

**Version**: 2.3.0  
**Last Updated**: 2026-01-19  
**Related Docs**: [Metrics Index](metrics_index.md) · [Dashboard Metrics](dashboard_metrics.md) · [Namespace Syntax](namespace_syntax.md)
