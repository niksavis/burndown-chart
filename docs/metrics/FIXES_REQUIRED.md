# DORA & Flow Metrics - Fixes Required

**Created**: October 31, 2025
**Status**: 🔧 In Progress

## Overview

This document outlines specific fixes needed for DORA and Flow metrics based on IMPLEMENTATION_GUIDE.md requirements.

## 1. DORA Metrics Calculation Fixes

### 1.1 Deployment Frequency

**Current Implementation**: `data/dora_calculator.py::calculate_deployment_frequency_v2()`

**Issues**:
- ❌ Not properly extracting `fixVersion.releaseDate` from operational tasks
- ❌ Not filtering by `releaseDate <= today` (deployments in future should be excluded)
- ❌ Not handling multiple fixVersions per operational task

**Required Fix** (per IMPLEMENTATION_GUIDE.md lines 530-547):
```python
# Extract deployment date from fixVersion object's releaseDate field
deployment_count = count(
    operational_tasks 
    WHERE status IN completion_statuses
    AND issuetype == "Operational Task"
    AND fixVersion.releaseDate BETWEEN start_date AND end_date
)
```

**Files to Modify**:
- `data/dora_calculator.py` - Fix `calculate_deployment_frequency_v2()` function

---

### 1.2 Lead Time for Changes

**Current Implementation**: `data/dora_calculator.py::calculate_lead_time_for_changes_v2()`

**Issues**:
- ❌ Missing changelog-based "In Deployment" status timestamp extraction
- ❌ Not implementing fixVersion matching between development and operational tasks
- ❌ Missing fallback logic (use "Done" status if "In Deployment" not found)

**Required Fix** (per IMPLEMENTATION_GUIDE.md lines 549-591):
```python
# For each development issue:
start_time = changelog_timestamp(issue, status="In Deployment")

# Fallback: If never reached "In Deployment", use "Done"
if not start_time:
    start_time = changelog_timestamp(issue, status="Done")

matching_op_tasks = find_operational_tasks_with_matching_fixversion(issue.fixVersions)
for op_task in matching_op_tasks:
    # At least ONE fixVersion must match
    if any(fv.id in [dev_fv.id for dev_fv in issue.fixVersions] for fv in op_task.fixVersions):
        end_time = op_task.fixVersion.releaseDate
```

**Files to Modify**:
- `data/dora_calculator.py` - Fix `calculate_lead_time_for_changes_v2()`
- `data/changelog_processor.py` - Verify changelog timestamp extraction
- `data/fixversion_matcher.py` - Verify fixVersion matching logic

---

### 1.3 Change Failure Rate

**Current Implementation**: `data/dora_calculator.py::calculate_change_failure_rate_v2()`

**Issues**:
- ❌ Not properly parsing `customfield_12708` value
- ❌ Not treating ONLY "Yes" as failure (should treat "No", "None", null, empty as success)
- ❌ Not filtering by `fixVersion.releaseDate <= today`

**Required Fix** (per IMPLEMENTATION_GUIDE.md lines 593-621):
```python
total_deployments = count(
    operational_tasks 
    WHERE status IN completion_statuses
    AND ANY(fixVersion.releaseDate <= today)
)

failed_deployments = count(
    operational_tasks 
    WHERE status IN completion_statuses
    AND ANY(fixVersion.releaseDate <= today)
    AND customfield_12708 == "Yes"  # ONLY "Yes" indicates failure
)

change_failure_rate = (failed_deployments / total_deployments) * 100
```

**Files to Modify**:
- `data/dora_calculator.py` - Fix `calculate_change_failure_rate_v2()`

---

### 1.4 Mean Time to Recovery (MTTR)

**Current Implementation**: `data/dora_calculator.py::calculate_mttr_v2()`

**Issues**:
- ❌ Not filtering bugs by `customfield_11309 == "PROD"` (exact match, case-sensitive)
- ❌ Not implementing fixVersion matching for bug fixes
- ❌ Missing fallback to `resolutiondate` if no operational task found

**Required Fix** (per IMPLEMENTATION_GUIDE.md lines 623-667):
```python
# Identify production bugs - EXACT match on "PROD"
production_bugs = [
    bug for bug in bugs 
    if bug.fields.customfield_11309 == "PROD"  # Exact match, always "PROD"
]

# For each production bug:
bug_created = parse_datetime(bug.fields.created)

# Method 1: Via Operational Task (preferred)
matching_op_tasks = find_operational_tasks_with_matching_fixversion(bug.fixVersions)

# Method 2: Fallback (no operational task)
if not fix_deployed:
    fix_deployed = parse_datetime(bug.fields.resolutiondate)

mttr_hours = (fix_deployed - bug_created).total_seconds() / 3600
```

**Files to Modify**:
- `data/dora_calculator.py` - Fix `calculate_mttr_v2()`

---

## 2. Flow Metrics Calculation Fixes

### 2.1 Flow Velocity (Two-Tier Classification)

**Current Implementation**: `data/flow_calculator.py::calculate_flow_velocity_v2()`

**Issues**:
- ❌ Not implementing two-tier classification per IMPLEMENTATION_GUIDE.md
- ❌ Bugs should ALWAYS map to "Defect" regardless of Effort Category
- ❌ Task/Story should check Effort Category field for secondary classification

**Required Fix** (per IMPLEMENTATION_GUIDE.md lines 669-739):
```python
# SIMPLIFIED Two-Tier Classification Logic:
# Primary Mapping (from issue type):
"Story" → "Feature"
"Task" → "Feature"
"Bug" → "Defect"  # ALL Bugs are Defects, regardless of Effort Category

# Secondary Mapping (from Effort Category - overrides primary for Task/Story ONLY):
For Task or Story:
    if customfield_13204 == "Technical debt" → "Technical Debt"
    elif customfield_13204 in ("Security", "GDPR Compliance", "Regulatory", "Maintenance") → "Risk"
    else → use primary (Feature)

For Bug:
    Always → "Defect" (ignore Effort Category completely)
```

**Files to Modify**:
- `data/flow_calculator.py` - Fix `calculate_flow_velocity_v2()` and `aggregate_flow_velocity_weekly()`
- `data/flow_type_classifier.py` - Implement proper two-tier classification

---

### 2.2 Flow Time (Changelog-Based)

**Current Implementation**: `data/flow_calculator.py::calculate_flow_time_v2()`

**Issues**:
- ❌ Missing changelog-based status transition tracking
- ❌ Not calculating "first time entered 'In Progress'" as start point
- ❌ Not calculating time to completion statuses as end point
- ❌ Missing both calculation methods (Active Time Only vs Total Flow Time)

**Required Fix** (per IMPLEMENTATION_GUIDE.md lines 765-809):
```python
# Method 1: Active Time Only (excludes waiting)
active_statuses = ["In Progress", "In Review", "Testing"]
start_time = first_changelog_timestamp(issue, status="In Progress")
# Calculate time in active statuses only

# Method 2: Total Flow Time (includes waiting)
start_time = first_changelog_timestamp(issue, status="In Progress")
end_time = first_changelog_timestamp(issue, status in completion_statuses)
flow_time_total_hours = (end_time - start_time).total_seconds() / 3600
```

**Files to Modify**:
- `data/flow_calculator.py` - Fix `calculate_flow_time_v2()`
- `data/changelog_processor.py` - Ensure proper timestamp extraction

---

### 2.3 Flow Load (WIP) - Positive Status Mapping

**Current Implementation**: `data/flow_calculator.py::calculate_flow_load_v2()`

**Issues**:
- ❌ May be using negative exclusion instead of positive inclusion
- ❌ Not verifying resolution = "Unresolved"

**Required Fix** (per IMPLEMENTATION_GUIDE.md lines 811-848):
```python
# Configuration: WIP statuses defined in config (positive mapping)
wip_statuses = config.get_wip_included_statuses()
# Returns: ["In Progress", "In Review", "Ready for Testing", "Testing", "In Deployment"]

wip_count = count(
    issues 
    WHERE status IN wip_statuses  # POSITIVE inclusion
    AND issuetype IN issue_types
    AND resolution = "Unresolved"
)
```

**Files to Modify**:
- `data/flow_calculator.py` - Verify `calculate_flow_load_v2()` uses positive inclusion

---

### 2.4 Flow Efficiency (Active vs Waiting Time)

**Current Implementation**: `data/flow_calculator.py::calculate_flow_efficiency_v2()`

**Issues**:
- ❌ Missing changelog-based time-in-status tracking
- ❌ Not calculating separate active_time and total_time
- ❌ Not using positive mapping for active statuses

**Required Fix** (per IMPLEMENTATION_GUIDE.md lines 850-895):
```python
# Configuration: Active statuses defined in config (positive mapping)
active_statuses = config.get_active_statuses()
# Returns: ["In Progress", "In Review", "Testing"]

# Parse changelog to calculate time in each status
for status_transition in issue.changelog:
    time_in_status = calculate_duration(status_transition)
    total_time += time_in_status
    
    if status_transition.status in active_statuses:  # POSITIVE check
        active_time += time_in_status

flow_efficiency = (active_time / total_time) * 100
```

**Files to Modify**:
- `data/flow_calculator.py` - Fix `calculate_flow_efficiency_v2()`
- `data/changelog_processor.py` - Add time-in-status calculation helper

---

### 2.5 Flow Distribution (Weekly Aggregation)

**Current Implementation**: `data/flow_calculator.py::aggregate_flow_distribution_weekly()`

**Issues**:
- ❌ Not calculating percentages correctly
- ❌ Not matching two-tier classification logic from Flow Velocity

**Required Fix**:
```python
velocity = calculate_flow_velocity(issues)
total = sum(velocity.values())

distribution = {
    flow_type: (count / total) * 100 
    for flow_type, count in velocity.items()
}
```

**Files to Modify**:
- `data/flow_calculator.py` - Fix `aggregate_flow_distribution_weekly()`

---

## 3. UI Improvements

### 3.1 Unified Metric Card with Weekly Trend

**Current Implementation**: `ui/metric_cards.py::create_metric_card()`

**Issues**:
- ✅ Metric card exists but doesn't show weekly trend graph inline
- ❌ Trend is in collapsible section, should be always visible
- ❌ Missing weekly data visualization (line chart)

**Required Fix**:
- Modify metric card to include miniature weekly trend sparkline
- Show latest week value prominently
- Show trend graph below value (always visible, not collapsible)

**Files to Modify**:
- `ui/metric_cards.py` - Add inline trend graph to `create_metric_card()`

---

### 3.2 DORA Metrics Dashboard

**Current Implementation**: `callbacks/dora_flow_metrics.py::calculate_and_display_dora_metrics()`

**Issues**:
- ❌ Only shows current period metrics, no weekly breakdown
- ❌ Doesn't calculate weekly aggregates

**Required Fix**:
- Calculate metrics per ISO week (last N weeks based on Data Points slider)
- Pass weekly data to metric cards for trend visualization
- Show current week value + trend

**Files to Modify**:
- `callbacks/dora_flow_metrics.py` - Add weekly aggregation to DORA callback

---

### 3.3 Flow Metrics Dashboard

**Current Implementation**: `callbacks/dora_flow_metrics.py::calculate_and_display_flow_metrics()`

**Issues**:
- ❌ Basic card layout without proper metric cards component
- ❌ Doesn't match DORA dashboard style
- ❌ Missing weekly trend visualization

**Required Fix**:
- Use same `create_metric_cards_grid()` as DORA
- Calculate weekly aggregates for all metrics
- Unified visual style with DORA dashboard

**Files to Modify**:
- `callbacks/dora_flow_metrics.py` - Rewrite Flow metrics callback to match DORA style

---

## 4. Field Mapping Configuration

### 4.1 Add Missing Field Mappings

**Current Configuration**: `app_settings.json::field_mappings`

**Issues**:
- ❌ Missing status name mappings (WIP, completion, active, waiting)
- ❌ Missing issue type filters
- ❌ Missing operational task type configuration
- ❌ Missing change failure value mapping ("Yes" vs "No")

**Required Additions**:
```json
{
  "field_mappings": {
    "dora": {
      "change_failure_field": "customfield_12708",
      "change_failure_yes_value": "Yes",
      "operational_task_type": "Operational Task",
      "in_deployment_status": "In Deployment",
      "completion_statuses": ["Done", "Resolved", "Closed"]
    },
    "flow": {
      "wip_statuses": ["In Progress", "In Review", "Ready for Testing", "Testing", "In Deployment"],
      "active_statuses": ["In Progress", "In Review", "Testing"],
      "completion_statuses": ["Done", "Resolved", "Closed"],
      "start_status": "In Progress",
      "development_issue_types": ["Task", "Story", "Bug"]
    }
  }
}
```

**Files to Modify**:
- `app_settings.example.json` - Add all required field mappings
- `app_settings.json` - User must configure their instance

---

### 4.2 Field Mapping UI

**Current Implementation**: `callbacks/field_mapping.py` and `ui/field_mapping_modal.py`

**Issues**:
- ❌ Doesn't expose all DORA/Flow field mappings
- ❌ Missing multi-select for status lists
- ❌ Missing value mappings (e.g., "Yes" for change failure)

**Required Fix**:
- Add form fields for all DORA/Flow mappings
- Add multi-select dropdowns for status lists
- Add text inputs for value mappings
- Organize by metric category (collapsible sections)

**Files to Modify**:
- `ui/field_mapping_modal.py` - Add all DORA/Flow mapping fields
- `callbacks/field_mapping.py` - Handle save/load of new mappings

---

## 5. Testing Requirements

### 5.1 Unit Tests

**Files to Update**:
- `tests/unit/data/test_dora_calculator.py` - Test all 4 DORA metrics with v2 functions
- `tests/unit/data/test_flow_calculator.py` - Test all 5 Flow metrics with v2 functions
- `tests/unit/data/test_changelog_processor.py` - Test changelog timestamp extraction
- `tests/unit/data/test_fixversion_matcher.py` - Test fixVersion matching logic
- `tests/unit/data/test_flow_type_classifier.py` - Test two-tier classification

### 5.2 Integration Tests

**Files to Update**:
- `tests/integration/test_dora_flow_integration.py` - End-to-end DORA and Flow workflows

---

## Implementation Priority

### Phase 1: Critical Calculation Fixes (Immediate)
1. ✅ Fix Flow Velocity two-tier classification
2. ✅ Fix CFR "Yes" value parsing
3. ✅ Fix MTTR production bug filtering

### Phase 2: Changelog Integration (High Priority)
4. ⏳ Implement changelog timestamp extraction
5. ⏳ Fix Lead Time "In Deployment" status tracking
6. ⏳ Fix Flow Time changelog-based calculation
7. ⏳ Fix Flow Efficiency active vs waiting time

### Phase 3: UI Improvements (High Priority)
8. ⏳ Create unified metric card with inline trend graph
9. ⏳ Add weekly aggregation to DORA callback
10. ⏳ Rewrite Flow callback to match DORA style

### Phase 4: Field Mapping (Medium Priority)
11. ⏸️ Add all missing field mappings to config schema
12. ⏸️ Update field mapping UI to expose all mappings

### Phase 5: Testing & Documentation (Medium Priority)
13. ⏸️ Update unit tests for v2 functions
14. ⏸️ Create integration tests
15. ⏸️ Update user documentation

---

## Notes

- All changes must follow Configuration Management Principles (no hardcoded customer data)
- Use positive inclusion mapping for all status/type filters
- Implement proper error handling and logging
- Maintain backward compatibility where possible
