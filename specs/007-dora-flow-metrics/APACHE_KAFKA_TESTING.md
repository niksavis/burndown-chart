# Apache Kafka JIRA Testing Configuration

## Configuration Summary

The app is now configured to test DORA and Flow metrics using the **Apache Kafka JIRA** public instance.

### JIRA Connection
- **URL**: `https://issues.apache.org/jira`
- **Project**: KAFKA
- **JQL Query**: `project = KAFKA AND status = Resolved AND resolved >= -90d ORDER BY resolved DESC`
- **Authentication**: Public read-only (no token required)

### Field Mappings (Standard JIRA Fields)

Since Apache JIRA doesn't have custom DORA/Flow fields, we're using standard JIRA fields as proxies:

| Metric Field            | Mapped To        | JIRA Field Type | Notes                                                   |
| ----------------------- | ---------------- | --------------- | ------------------------------------------------------- |
| `deployment_date`       | `resolutiondate` | DateTime        | When issue was resolved (proxy for deployment)          |
| `deployment_successful` | *(empty)*        | N/A             | **NOT AVAILABLE** - Can't calculate Change Failure Rate |
| `incident_start`        | `created`        | DateTime        | When incident (bug) was reported                        |
| `incident_resolved`     | `resolutiondate` | DateTime        | When incident was fixed                                 |
| `work_started_date`     | `created`        | DateTime        | When work item was created                              |
| `work_completed_date`   | `resolutiondate` | DateTime        | When work item was completed                            |
| `work_type`             | `issuetype`      | Text            | Bug, New Feature, Improvement, Task, etc.               |
| `work_item_size`        | *(empty)*        | N/A             | **NOT AVAILABLE** - Apache doesn't use story points     |

## Metrics That Will Work

### ✅ DORA Metrics (3 out of 4)

1. **Deployment Frequency** ✅
   - Uses `resolutiondate` as proxy for deployments
   - Will show how often issues are resolved
   - **Expected**: Medium-High tier (Apache resolves many issues weekly)

2. **Lead Time for Changes** ✅
   - Calculates time from `created` to `resolutiondate`
   - Shows how long issues take to resolve
   - **Expected**: Varies by issue type (days to weeks)

3. **Change Failure Rate** ❌
   - **CANNOT CALCULATE** - requires `deployment_successful` field
   - Will show "Configure Field Mappings" error

4. **Mean Time to Recovery (MTTR)** ✅
   - Uses Bug issues: time from `created` to `resolutiondate`
   - Shows how fast bugs are fixed
   - **Expected**: Medium tier (bugs resolved in days)

### ✅ Flow Metrics (4 out of 5)

1. **Flow Velocity** ⚠️
   - Shows items completed per week
   - Breakdown by `issuetype` (not exactly Feature/Bug/Tech Debt/Risk)
   - **Expected**: High velocity (Apache resolves many issues)

2. **Flow Time** ✅
   - Average cycle time from `created` to `resolutiondate`
   - **Expected**: Days to weeks depending on issue complexity

3. **Flow Efficiency** ❌
   - **LIMITED** - Can calculate total time but not active vs. wait time
   - Will show calculation error or inaccurate results

4. **Flow Load** ✅
   - Shows work in progress (issues not yet resolved)
   - **Expected**: Variable based on current sprint

5. **Flow Distribution** ⚠️
   - Shows breakdown by `issuetype`
   - Will map: Bug → Bug, New Feature → Feature, Improvement → Feature, Task → Technical Debt
   - **Expected**: Roughly balanced distribution

## API Implementation Status

### ✅ Updated Components

1. **`data/jira_simple.py`** - Enhanced field fetching
   - Now includes fields from `field_mappings` in API requests
   - Automatically fetches custom fields if they start with `customfield_`
   - Standard fields (`created`, `resolutiondate`, `issuetype`, `status`) always included

2. **`app_settings.json`** - Configuration updated
   - JIRA URL: Apache Kafka instance
   - Field mappings: Standard fields mapped
   - JQL Query: Last 90 days of resolved issues

### API Request Example

When fetching data, the app will now request:
```
fields=key,created,resolutiondate,status,issuetype
```

This covers all standard fields needed for the mapped metrics.

## Testing Instructions

1. **Clear Cache** (to force fresh data fetch):
   ```powershell
   Remove-Item jira_cache.json
   ```

2. **Run the App**:
   ```powershell
   .\.venv\Scripts\activate; python app.py
   ```

3. **Navigate to DORA & Flow Tabs**:
   - Go to "DORA Metrics" tab
   - Click "Refresh Metrics"
   - You should see 3 metrics with data (Deployment Frequency, Lead Time, MTTR)
   - Change Failure Rate will show "Configure Field Mappings" error

4. **Check Flow Metrics**:
   - Go to "Flow Metrics" tab
   - Click "Refresh Metrics"
   - You should see 4-5 metrics with data
   - Flow Efficiency may show calculation error

## Limitations & Workarounds

### Missing Fields
- **Story Points**: Apache doesn't use story points publicly
  - **Impact**: Flow Velocity breakdown won't show accurate sizing
  - **Workaround**: Use issue count instead of story points

- **Deployment Success**: No boolean field for deployment success
  - **Impact**: Can't calculate Change Failure Rate
  - **Workaround**: Requires custom JIRA instance with this field

- **Work Type Categories**: JIRA `issuetype` doesn't map perfectly to Flow categories
  - **Impact**: Distribution chart won't match exact Flow framework categories
  - **Workaround**: Accept approximate mapping

### Authentication
- Apache JIRA is **public read-only**
- No API token required for read operations
- `token` field can remain empty in `app_settings.json`

## Expected Results

With ~90 days of Kafka resolved issues (typically 100-300 issues), you should see:

**DORA Dashboard:**
- Deployment Frequency: **30-50 deployments/month** (Medium-High tier)
- Lead Time: **3-7 days average** (High tier)
- Change Failure Rate: **Error - Missing Field Mapping**
- MTTR: **2-4 days average** (High tier)

**Flow Dashboard:**
- Velocity: **20-30 items/week**
- Flow Time: **5-10 days average**
- Flow Efficiency: **May show error or low percentage**
- Flow Load: **50-100 items in progress**
- Distribution: Bug ~30%, Feature ~50%, Task ~20%

## Next Steps for Full Testing

To test **ALL 9 metrics** with proper data:

1. **Create Free Atlassian Cloud Instance**
   - Sign up at: https://www.atlassian.com/try/cloud/signup
   - Add custom fields for DORA/Flow metrics
   - Populate with test data

2. **Update `app_settings.json`**:
   - Change `base_url` to your instance
   - Add API token
   - Update `field_mappings` with actual custom field IDs
   - Update `jql_query` to your project

3. **Test Full Feature Set**:
   - All 4 DORA metrics with proper performance tiers
   - All 5 Flow metrics with accurate calculations
   - Export to CSV/JSON
   - Trend analysis with historical data
