# DORA & Flow Metrics Implementation Analysis

## Current Status: METRICS NOT IMPLEMENTED

### Critical Finding

The DORA and Flow metrics dashboards are **showing loading cards indefinitely** because the callbacks are stubbed and do NOT actually call the calculator functions.

### Evidence from Code

**File: `callbacks/dora_flow_metrics.py`**

Lines 59-91 in `update_dora_metrics()`:
```python
# TODO: Integrate with actual metric calculation
# from data.dora_calculator import calculate_all_dora_metrics
# [commented out code]

# Phase 6 stub - show parsed dates
placeholder_alert = dbc.Alert([...], color="info")
return create_dora_loading_cards_grid(), placeholder_alert
```

Lines 152-184 in `update_flow_metrics()`:
```python
# TODO: Integrate with actual metric calculation  
# from data.flow_calculator import calculate_all_flow_metrics
# [commented out code]

# Phase 6 stub - show parsed dates
placeholder_alert = dbc.Alert([...], color="info")
return create_flow_loading_cards_grid(), placeholder_alert
```

**Result**: The callbacks ALWAYS return loading cards with a "Calculating..." message, regardless of field mappings.

---

## What Actually Needs to Happen

### Phase 1: Understand Calculator Requirements

Looking at the actual calculator code in `data/dora_calculator.py` and `data/flow_calculator.py`, here's what each metric ACTUALLY needs:

#### DORA Metrics Requirements

| Metric                    | Required Fields                                   | Optional Fields         | Data Source                              |
| ------------------------- | ------------------------------------------------- | ----------------------- | ---------------------------------------- |
| **Deployment Frequency**  | `deployment_date`                                 | `deployment_successful` | Issues with deployment dates             |
| **Lead Time for Changes** | `code_commit_date`, `deployed_to_production_date` | -                       | Issues with both commit and deploy dates |
| **Change Failure Rate**   | `deployment_date`                                 | `production_impact`     | Deployment issues + Incident issues      |
| **Mean Time to Recovery** | `incident_detected_at`, `incident_resolved_at`    | -                       | Incident issues only                     |

#### Flow Metrics Requirements

| Metric                | Required Fields                            | Optional Fields  | Data Source                     |
| --------------------- | ------------------------------------------ | ---------------- | ------------------------------- |
| **Flow Velocity**     | `flow_item_type`, `completed_date`         | -                | Completed issues in time period |
| **Flow Time**         | `work_started_date`, `work_completed_date` | -                | Completed issues                |
| **Flow Efficiency**   | `active_work_hours`, `flow_time_days`      | -                | Issues with time tracking       |
| **Flow Load**         | `status`                                   | `flow_item_type` | All active (WIP) issues         |
| **Flow Distribution** | `flow_item_type`, `completed_date`         | -                | Completed issues in time period |

### Phase 2: Apache Kafka JIRA Reality Check

**Problem**: Apache Kafka JIRA is a **public issue tracker**, not a DevOps pipeline tracker. It has:
- Standard Jira fields (created, updated, resolutiondate, status, issuetype)
- Bug tracking data (bug reports, feature requests, improvements)
- **NO deployment tracking**
- **NO commit timestamps**
- **NO incident management**
- **NO time tracking fields**

**What Apache Kafka JIRA CAN provide**:
- ✅ Issue created dates
- ✅ Issue resolution dates  
- ✅ Issue statuses
- ✅ Issue types (Bug, Story, Task, Improvement)
- ❌ Deployment dates
- ❌ Commit dates
- ❌ Incident detection/resolution
- ❌ Active work hours
- ❌ Flow item categorization

### Phase 3: Feasibility Analysis

#### Metrics That CAN Work (with proxies)

**Flow Velocity** ✅ **FEASIBLE**
- Use `issuetype` as proxy for `flow_item_type`
  - Bug → Defect
  - Story/Improvement → Feature
  - Task → Technical Debt
- Use `resolutiondate` as `completed_date`
- **Result**: Can calculate items completed per period

**Flow Time** ✅ **FEASIBLE**
- Use `created` as `work_started_date`
- Use `resolutiondate` as `work_completed_date`
- **Result**: Can calculate time from created to resolved (rough proxy)

**Flow Load** ✅ **FEASIBLE**
- Use `status` field directly (already mapped)
- Count issues NOT in ['Done', 'Closed', 'Resolved']
- **Result**: Can calculate current WIP

**Flow Distribution** ✅ **FEASIBLE**
- Use `issuetype` as proxy for `flow_item_type` (same as Velocity)
- Use `resolutiondate` as `completed_date`
- **Result**: Can calculate percentage breakdown by issue type

#### Metrics That CANNOT Work

**Deployment Frequency** ❌ **NOT FEASIBLE**
- Requires: Actual deployment events
- Apache Kafka JIRA has: Bug resolution dates (not deployments)
- **Why not use resolutiondate?** Bugs being resolved ≠ code being deployed to production

**Lead Time for Changes** ❌ **NOT FEASIBLE**
- Requires: Commit timestamp → Production deployment timestamp
- Apache Kafka JIRA has: No commit tracking, no deployment tracking
- **Why not use created→resolved?** That's cycle time, not lead time (different metric)

**Change Failure Rate** ❌ **NOT FEASIBLE**
- Requires: Deployment count + Incident count (linked)
- Apache Kafka JIRA has: Bug reports (not incidents caused by deployments)

**Mean Time to Recovery** ❌ **NOT FEASIBLE**
- Requires: Incident detection → Incident resolution timestamps
- Apache Kafka JIRA has: Bug creation → Bug resolution (different concept)

---

## Recommended Action Plan

### Option 1: Enable Only Flow Metrics (4 out of 5)

**Implement these Flow metrics with proxy fields**:

1. **Flow Velocity** - Issues completed per period
2. **Flow Time** - Average time from created to resolved
3. **Flow Load** - Current work in progress
4. **Flow Distribution** - Percentage by issue type

**Disable these metrics with user-friendly messages**:
1. ❌ **Flow Efficiency** - "Requires time tracking fields not available in standard Jira"
2. ❌ **All DORA Metrics** - "Requires deployment and incident tracking (use Jira Service Management or CI/CD integration)"

### Option 2: Create Proxy Mappings with Disclaimers

Map Apache Kafka fields to DORA/Flow fields with **clear warnings** that these are approximations:

```json
{
  "field_mappings": {
    // Flow Metrics (4 working)
    "flow_item_type": "issuetype",           // Proxy: Bug→Defect, Story→Feature
    "completed_date": "resolutiondate",      // Good proxy
    "work_started_date": "created",          // Rough proxy (not ideal)
    "work_completed_date": "resolutiondate", // Good proxy
    "status": "status",                      // Direct match
    
    // DORA Metrics (0 working - all proxies are misleading)
    "deployment_date": null,                 // NOT AVAILABLE
    "code_commit_date": null,                // NOT AVAILABLE
    "deployed_to_production_date": null,     // NOT AVAILABLE
    "incident_detected_at": null,            // NOT AVAILABLE
    "incident_resolved_at": null,            // NOT AVAILABLE
    
    // Flow Efficiency (not available)
    "active_work_hours": null,               // NOT AVAILABLE
    "flow_time_days": null                   // NOT AVAILABLE
  }
}
```

### Option 3: Implement Metrics with Error States

Modify callbacks to:
1. Fetch Apache Kafka issues
2. Call calculator functions
3. Display metrics with proper error states:
   - ✅ Green: Metric calculated successfully
   - ⚠️ Yellow: Metric calculated with proxies (disclaimer shown)
   - ❌ Red: Metric cannot be calculated (missing required fields)

---

## Implementation Steps (Recommended)

### Step 1: Fix the Callbacks (Enable Calculations)

**File: `callbacks/dora_flow_metrics.py`**

Uncomment and implement the TODO sections:

```python
@callback(...)
def update_flow_metrics(...):
    from data.flow_calculator import calculate_all_flow_metrics
    from data.field_mapper import load_field_mappings
    from data.jira_simple import fetch_all_issues
    
    # Load field mappings
    mappings = load_field_mappings()
    field_map = mappings.get("field_mappings", {})
    
    # Fetch issues
    issues = fetch_all_issues()
    
    # Calculate metrics
    results = calculate_all_flow_metrics(
        issues=issues,
        field_mappings=field_map,
        start_date=start_date,
        end_date=end_date
    )
    
    # Render metric cards
    from ui.metric_cards import create_metric_card
    cards = [create_metric_card(metric_data) for metric_data in results.values()]
    
    return cards, None
```

### Step 2: Create Proxy Field Mappings

**File: `app_settings.json`**

```json
{
  "field_mappings": {
    // Working Flow Metrics
    "flow_item_type": "issuetype",
    "completed_date": "resolutiondate",
    "work_started_date": "created",
    "work_completed_date": "resolutiondate",
    "status": "status",
    
    // Non-working metrics (set to null or omit)
    "deployment_date": null,
    "code_commit_date": null,
    "deployed_to_production_date": null,
    "incident_detected_at": null,
    "incident_resolved_at": null,
    "deployment_successful": null,
    "production_impact": null,
    "active_work_hours": null,
    "flow_time_days": null
  }
}
```

### Step 3: Add Issue Type Mapping Logic

**File: `data/flow_calculator.py`**

Add helper function to map Jira issue types to Flow item types:

```python
def _map_issue_type_to_flow_type(issue_type: str) -> str:
    """Map Jira issue type to Flow item type.
    
    Args:
        issue_type: Jira issue type (Bug, Story, Task, Improvement, etc.)
    
    Returns:
        Flow item type: Feature, Defect, Risk, or Technical_Debt
    """
    mapping = {
        "Bug": "Defect",
        "Story": "Feature",
        "Improvement": "Feature",
        "New Feature": "Feature",
        "Task": "Technical_Debt",
        "Sub-task": "Technical_Debt",
        "Epic": "Feature",
    }
    return mapping.get(issue_type, "Feature")  # Default to Feature
```

Then modify `calculate_flow_velocity()` and `calculate_flow_distribution()` to use this mapping when `flow_type_field` points to `issuetype`.

### Step 4: Update Field Mapper to Handle Proxy Fields

**File: `data/field_mapper.py`**

Add validation that checks if field is a standard field vs custom field:

```python
def validate_field_mapping_with_proxies(
    field_mappings: Dict[str, str],
    available_fields: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Validate field mappings and identify proxy fields.
    
    Returns:
        {
            "valid": True/False,
            "proxy_fields": ["field1", "field2"],  # Using standard field as proxy
            "missing_fields": ["field3"],          # Required but not mapped
            "custom_fields": ["field4"]            # Properly mapped custom fields
        }
    """
    standard_fields = ["created", "updated", "resolutiondate", "status", "issuetype"]
    proxy_fields = []
    custom_fields = []
    
    for internal_name, jira_field in field_mappings.items():
        if jira_field in standard_fields:
            proxy_fields.append(internal_name)
        else:
            custom_fields.append(internal_name)
    
    return {
        "valid": True,
        "proxy_fields": proxy_fields,
        "missing_fields": [],
        "custom_fields": custom_fields
    }
```

### Step 5: Add User Warnings in UI

**File: `ui/metric_cards.py`**

Add disclaimer badge for metrics using proxy fields:

```python
def create_metric_card_with_proxy_warning(metric_data: Dict[str, Any]) -> dbc.Card:
    """Create metric card with proxy field warning if applicable."""
    
    card = create_metric_card(metric_data)
    
    # Add warning badge if using proxy fields
    if metric_data.get("using_proxy_fields"):
        warning_badge = dbc.Badge(
            "⚠️ Using Proxy Fields",
            color="warning",
            className="ms-2",
            title="This metric uses standard Jira fields as approximations"
        )
        # Append to card header
    
    return card
```

---

## Testing Strategy

### Test 1: Flow Metrics with Proxy Fields

**Expected Results**:
- ✅ Flow Velocity: Shows count of resolved issues per period
- ✅ Flow Time: Shows average days from created→resolved
- ✅ Flow Load: Shows count of issues in "In Progress" status
- ✅ Flow Distribution: Shows breakdown by issue type (Bug/Story/Task)
- ❌ Flow Efficiency: Shows "Missing field mapping" error

### Test 2: DORA Metrics with Missing Fields

**Expected Results**:
- ❌ Deployment Frequency: Shows "Configure 'Deployment Date' field mapping"
- ❌ Lead Time: Shows "Configure field mappings: code_commit_date, deployed_to_production_date"
- ❌ Change Failure Rate: Shows "Configure 'Deployment Date' field mapping"
- ❌ MTTR: Shows "Configure field mappings: incident_detected_at, incident_resolved_at"

### Test 3: Field Mapping Modal

**Expected Results**:
- Dropdowns show all 215 Apache Kafka fields
- Warning icon next to fields mapped to standard fields (proxies)
- Save button validates and shows which metrics will work

---

## Next Steps

1. **Immediate**: Uncomment calculator calls in callbacks (20 minutes)
2. **Short-term**: Add proxy field mappings to app_settings.json (10 minutes)
3. **Medium-term**: Add issue type→flow type mapping logic (30 minutes)
4. **Long-term**: Add UI warnings for proxy fields (1 hour)

**Estimated time to see working Flow metrics**: 1-2 hours

---

## Conclusion

The "Calculating..." issue is NOT a field mapping problem - it's because the callbacks are stubbed and don't actually call the calculator functions.

Once callbacks are implemented, **4 out of 9 metrics** (all Flow metrics except Efficiency) can work with Apache Kafka JIRA using proxy field mappings, though with caveats about accuracy.

DORA metrics fundamentally require deployment and incident tracking data that Apache Kafka JIRA doesn't have.
