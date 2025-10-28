# Proxy Field Mappings for Apache Kafka JIRA

## ⚠️ Important Disclaimer

These field mappings use **standard Jira fields as proxies** for DORA and Flow metrics. They enable testing the UI but produce **approximations, not accurate measurements**.

## Field Mapping Configuration

```json
{
  "field_mappings": {
    // Flow Metrics (4 working + 1 error)
    "flow_item_type": "issuetype",           // ✅ Mapped: Bug→Defect, Story→Feature, Task→Tech Debt
    "completed_date": "resolutiondate",      // ✅ Good proxy: When issue was completed
    "work_started_date": "created",          // ⚠️ Rough proxy: Includes backlog time
    "work_completed_date": "resolutiondate", // ✅ Good proxy: When work finished
    "status": "status",                      // ✅ Direct match
    
    // DORA Metrics (4 with proxy data)
    "deployment_date": "resolutiondate",              // ⚠️ PROXY: Bug resolved ≠ Deployment
    "code_commit_date": "created",                    // ⚠️ PROXY: Issue created ≠ Code committed
    "deployed_to_production_date": "resolutiondate",  // ⚠️ PROXY: Same as deployment_date
    "incident_detected_at": "created",                // ⚠️ PROXY: Bug reported ≠ Incident detected
    "incident_resolved_at": "resolutiondate"          // ⚠️ PROXY: Bug fixed ≠ Incident resolved
  }
}
```

## What Each DORA Metric Will Actually Calculate

### 1. Deployment Frequency
- **Intended**: Deployments to production per month
- **Actual Calculation**: Issues resolved per month
- **Interpretation**: "If every resolved issue was a deployment..."
- **Accuracy**: ❌ Very misleading (issues ≠ deployments)

### 2. Lead Time for Changes
- **Intended**: Time from commit to production deployment
- **Actual Calculation**: Time from issue creation to resolution
- **Interpretation**: Issue cycle time (not lead time)
- **Accuracy**: ⚠️ Moderately useful as cycle time proxy

### 3. Change Failure Rate
- **Intended**: % of deployments causing incidents
- **Actual Calculation**: Ratio of all issues (numerator and denominator are the same dataset)
- **Interpretation**: Meaningless ratio
- **Accuracy**: ❌ Completely invalid

### 4. Mean Time to Recovery (MTTR)
- **Intended**: Average time to recover from incident
- **Actual Calculation**: Average bug resolution time
- **Interpretation**: Bug fix time (not incident recovery)
- **Accuracy**: ⚠️ Useful as bug fix time, not true MTTR

## Expected UI Behavior

### DORA Metrics Tab (After Refresh)

**Deployment Frequency Card:**
```
Deployment Frequency
~656 deployments/month

Performance Tier: Elite (very misleading!)
Trend: ↑ 5.2%
```

**Lead Time for Changes Card:**
```
Lead Time for Changes
~14 days average

Performance Tier: Medium
Trend: → Stable
```

**Change Failure Rate Card:**
```
Change Failure Rate
~100%

Performance Tier: Low (incorrect calculation)
Trend: → Stable
```

**MTTR Card:**
```
Mean Time to Recovery
~14 days (336 hours)

Performance Tier: Low
Trend: → Stable
```

### Flow Metrics Tab

All Flow metrics should continue working as before with accurate calculations.

## How to Test

### 1. Refresh DORA Metrics Tab
```
1. Navigate to "DORA & Flow Metrics" → "DORA Metrics"
2. Click the refresh button (↻)
3. Wait for calculation (~2 seconds)
4. Cards should now show numerical values (not errors)
```

### 2. Verify Calculations
```
Expected:
✅ All 4 DORA cards show numbers
✅ Performance tiers display with colors
✅ Trends show direction (↑/↓/→)
✅ No "Calculating..." animations
✅ No error messages
```

### 3. Test Time Period Selector
```
1. Change time period dropdown (7/30/90 days)
2. Click refresh
3. Metrics should recalculate for new period
```

### 4. Test Export Functionality
```
1. Click "Export CSV" button
2. Verify file downloads with metrics data
3. Click "Export JSON" button
4. Verify JSON file with full metric details
```

## Limitations to Document

### For Users/Stakeholders

> ⚠️ **Important**: These DORA metrics use approximations and should NOT be used for:
> - Executive reporting
> - Team performance evaluation
> - Benchmarking against industry standards
> - Making architectural decisions
> 
> ✅ **Acceptable uses**:
> - UI testing and development
> - Understanding metric calculation logic
> - Demonstrating chart visualizations
> - Prototyping dashboards

### For Developers

**To get accurate DORA metrics, you need**:
1. CI/CD pipeline integration (Jenkins, GitLab CI, GitHub Actions)
2. Incident management system (PagerDuty, Jira Service Management)
3. Custom Jira fields for deployment tracking
4. Issue linking between deployments and incidents

**Or**: Use a different Jira project that has proper deployment tracking configured.

## Reverting to Error States

If you want to see proper error states again (for testing validation):

```json
{
  "field_mappings": {
    "flow_item_type": "issuetype",
    "completed_date": "resolutiondate",
    "work_started_date": "created",
    "work_completed_date": "resolutiondate",
    "status": "status"
    // Remove all DORA fields
  }
}
```

Then refresh the DORA metrics tab - should show "Configure '[Field]' field mapping" errors.

## Next Development Tasks

Based on this testing configuration:

1. ✅ Verify metric card rendering with real data
2. ✅ Test performance tier color coding
3. ✅ Validate trend calculation logic
4. ✅ Check export CSV/JSON functionality
5. ✅ Test time period filtering
6. ✅ Verify mobile responsive layout
7. 📋 Add disclaimer badges to proxy metrics
8. 📋 Create admin UI for toggling proxy mode
9. 📋 Add data quality indicators
10. 📋 Document CI/CD integration patterns

---

**Summary**: Proxy mappings enable full UI testing of DORA metrics, but users must understand the data is approximate and not suitable for production use.
