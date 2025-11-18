# Field Mapping Requirements Analysis

## Executive Summary

Based on PM-Metrics-Formulas.md, we need to map **data variables** (not just fields) from JIRA to calculate DORA and Flow metrics. The challenge: every JIRA instance is different, and variables can come from:

1. **Direct field values** (e.g., `customfield_10100 = "2025-01-15"`)
2. **Field value matching** (e.g., `status.name = "Done"`)
3. **Changelog events** (e.g., status transition timestamps)
4. **Derived calculations** (e.g., time between changelog events)
5. **Conditional logic** (e.g., only for specific issue types or projects)

## Variables Required for Each Metric

### DORA Metrics

#### 1. Deployment Frequency (DF)
**Formula:** `DF(W) = Number of Successful Deployments / W`

**Variables Needed:**
- **Deployment Event** (boolean/count)
  - Source options:
    - Custom field: `customfield_XXXXX = "Deployed"`
    - Status transition: changelog event `status changed to "Deployed to Production"`
    - Fix version: `fixVersions[*].releaseDate` exists
    - Label: `labels contains "deployed"`
- **Deployment Success** (boolean)
  - Source options:
    - Custom field: `customfield_XXXXX = true/false`
    - Status value: `status.name not in ["Rollback", "Failed Deployment"]`
    - Resolution: `resolution.name = "Deployed Successfully"`
- **Time Window Filter** (W = 7 days)
  - Deployment timestamp within window

**Conditional Logic:**
- Filter by project: `project.key in ["PROJ1", "PROJ2"]`
- Filter by issue type: `issuetype.name in ["Deployment Task", "Release"]`
- Filter by environment: `customfield_environment = "Production"`

#### 2. Lead Time for Changes (LT)
**Formula:** `LT(W) = median((Deployment_j - Commit_j) / 1 day)`

**Variables Needed:**
- **Commit Timestamp** ($\text{Commit}_j$)
  - Source options:
    - Custom field: `customfield_XXXXX` (datetime)
    - Created date: `created` (if commits tracked as issues)
    - Changelog: first transition to "In Development"
    - External link: extract from git commit URL
- **Deployment Timestamp** ($\text{Deployment}_j$)
  - Source options:
    - Custom field: `customfield_XXXXX` (datetime)
    - Status transition: changelog event timestamp
    - Fix version: `fixVersions[0].releaseDate`
    - Resolution date: `resolutiondate`

**Conditional Logic:**
- Only for deployed items (see Deployment Event above)
- Exclude non-code changes (e.g., `issuetype != "Bug"`)

#### 3. Change Failure Rate (CFR)
**Formula:** `CFR(W) = (Failed Deployments / Total Deployments) × 100%`

**Variables Needed:**
- **Deployment Failed** (boolean)
  - Source options:
    - Custom field: `customfield_XXXXX = false` (deployment_successful)
    - Status: `status.name in ["Rollback", "Failed"]`
    - Linked issue: has linked "Hotfix" or "Incident"
    - Label: `labels contains "deployment-failure"`
- **Total Deployments** (count)
  - Same as Deployment Event above

**Conditional Logic:**
- Only production deployments: `customfield_environment = "Production"`
- Exclude planned rollbacks vs. failure rollbacks

#### 4. Mean Time to Recovery (MTTR)
**Formula:** `MTTR(W) = median((R_i - F_i) / m)`

**Variables Needed:**
- **Incident Detected Timestamp** ($F_i$)
  - Source options:
    - Custom field: `customfield_XXXXX` (datetime)
    - Created date: `created` (if issue type = "Incident")
    - Changelog: transition to "In Progress" for incidents
    - External system: timestamp from monitoring tool
- **Service Restored Timestamp** ($R_i$)
  - Source options:
    - Custom field: `customfield_XXXXX` (datetime)
    - Resolution date: `resolutiondate`
    - Changelog: transition to "Resolved" or "Closed"
    - Custom status: transition to "Service Restored"

**Conditional Logic:**
- Only production incidents: `customfield_affected_environment = "Production"`
- Filter by issue type: `issuetype.name in ["Incident", "Production Bug"]`
- Filter by severity: `priority.name in ["Critical", "Blocker"]`

---

### Flow Metrics

#### 5. Flow Velocity
**Formula:** `Flow Velocity(W) = Completed Flow Items / W`

**Variables Needed:**
- **Completion Event** (boolean/count)
  - Source options:
    - Status: `status.name in ["Done", "Closed", "Resolved"]`
    - Resolution: `resolution.name is not null`
    - Changelog: transitioned to done status
- **Completion Timestamp** ($C_i$)
  - Source options:
    - Resolution date: `resolutiondate`
    - Custom field: `customfield_XXXXX`
    - Changelog: timestamp of transition to done

**Conditional Logic:**
- Filter by work type: `issuetype.name in ["Story", "Bug", "Task"]`
- Exclude specific types: `issuetype.name not in ["Epic", "Sub-task"]`

#### 6. Flow Time
**Formula:** `Flow Time = (C_i - S_i) / n`

**Variables Needed:**
- **Work Started Timestamp** ($S_i$)
  - Source options:
    - Custom field: `customfield_XXXXX` (datetime)
    - Created date: `created`
    - Changelog: first transition to "In Progress"
    - Changelog: first status change from initial state
- **Work Completed Timestamp** ($C_i$)
  - Same as Flow Velocity above

**Conditional Logic:**
- Only completed items (see Flow Velocity)
- Exclude items with no start date

#### 7. Flow Efficiency
**Formula:** `Flow Efficiency = (Active Time / Total Flow Time) × 100%`

**Variables Needed:**
- **Active Time** (duration)
  - Source options:
    - Custom field: `customfield_XXXXX` (time tracking)
    - Changelog analysis: sum of time in active statuses
    - Derived: sum(time in ["In Progress", "In Review", "Testing"])
- **Total Flow Time** (duration)
  - Same as Flow Time above ($C_i - S_i$)

**Conditional Logic:**
- Define active statuses: `status.name in ["In Progress", "In Review"]`
- Define wait statuses: `status.name in ["Blocked", "Waiting", "Backlog"]`

#### 8. Flow Load (WIP)
**Formula:** `Flow Load = Number of Active Work Items at Time W`

**Variables Needed:**
- **Active Status** (boolean)
  - Source options:
    - Status: `status.name in ["In Progress", "In Review", "Testing"]`
    - Custom field: `customfield_XXXXX = "Active"`
    - Status category: `status.statusCategory.key = "indeterminate"`

**Conditional Logic:**
- Exclude done/closed items
- Filter by assignee/team if needed

#### 9. Flow Distribution
**Formula:** `Flow Distribution = (Items of Type j / Total Items) × 100%`

**Variables Needed:**
- **Work Type** (category: Feature, Defect, Risk, Tech Debt)
  - Source options:
    - Issue type: `issuetype.name` mapping
    - Custom field: `customfield_XXXXX` (select)
    - Labels: check for specific labels
    - Component: `components[*].name`

**Mapping Examples:**
```json
{
  "Features": ["Story", "Epic", "New Feature"],
  "Defects": ["Bug", "Defect", "Production Bug"],
  "Risks": ["Risk", "Security Issue"],
  "Tech Debt": ["Technical Debt", "Refactoring", "Improvement"]
}
```

**Conditional Logic:**
- Custom categorization rules per organization
- Multiple issue types can map to same category

#### 10. Flow Predictability (PPM)
**Formula:** `Flow Predictability = (Actual Value Delivered / Planned Value) × 100%`

**Variables Needed:**
- **Planned Business Value** (number)
  - Source options:
    - Custom field: `customfield_XXXXX` (number)
    - Story points: `customfield_storypoints`
    - Count: number of planned items
    - Priority weighting: calculated from priority
- **Actual Business Value** (number)
  - Same sources as planned, filtered by completion

**Conditional Logic:**
- Only for planned items in time window
- Filter by sprint/program increment

---

## Proposed Mapping Architecture

### Concept: Hierarchical Field Mapping with Conditions

Instead of simple `internal_field → jira_field` mappings, we need **mapping rules** with:

1. **Source Definition**: Where the data comes from
2. **Value Extraction**: How to extract/calculate the value
3. **Conditional Filters**: When the mapping applies

### Data Model: Mapping Rule Structure

```json
{
  "deployment_event": {
    "metric_category": "dora",
    "data_type": "boolean",
    "description": "Identifies if an issue represents a deployment",
    "mapping_rules": [
      {
        "rule_id": "rule_001",
        "priority": 1,
        "source_type": "field_value",
        "field": "customfield_10100",
        "condition": {
          "operator": "equals",
          "value": "Deployed"
        },
        "filters": {
          "project": ["DEVOPS"],
          "issuetype": ["Deployment Task"]
        }
      },
      {
        "rule_id": "rule_002",
        "priority": 2,
        "source_type": "changelog_event",
        "field": "status",
        "condition": {
          "operator": "transition_to",
          "value": "Deployed to Production"
        },
        "extract_timestamp": true
      },
      {
        "rule_id": "rule_003",
        "priority": 3,
        "source_type": "fixversion_releasedate",
        "field": "fixVersions",
        "condition": {
          "operator": "has_releasedate",
          "environment_filter": "Production"
        }
      }
    ],
    "fallback_rule": {
      "source_type": "field_value",
      "field": "resolutiondate",
      "condition": {
        "operator": "is_not_null"
      }
    }
  },
  
  "deployment_timestamp": {
    "metric_category": "dora",
    "data_type": "datetime",
    "description": "When the deployment occurred",
    "mapping_rules": [
      {
        "rule_id": "rule_004",
        "priority": 1,
        "source_type": "field_value",
        "field": "customfield_10100",
        "value_type": "datetime"
      },
      {
        "rule_id": "rule_005",
        "priority": 2,
        "source_type": "changelog_event_timestamp",
        "field": "status",
        "condition": {
          "operator": "transition_to",
          "value": "Deployed to Production"
        }
      },
      {
        "rule_id": "rule_006",
        "priority": 3,
        "source_type": "fixversion_releasedate",
        "field": "fixVersions",
        "selector": "first"
      }
    ]
  },
  
  "work_type_category": {
    "metric_category": "flow",
    "data_type": "category",
    "description": "Flow distribution category (Feature, Defect, Risk, Tech Debt)",
    "mapping_rules": [
      {
        "rule_id": "rule_007",
        "priority": 1,
        "source_type": "field_value_mapping",
        "field": "issuetype",
        "value_mappings": {
          "Feature": ["Story", "Epic", "New Feature"],
          "Defect": ["Bug", "Defect", "Production Bug"],
          "Risk": ["Risk", "Security Issue"],
          "Tech Debt": ["Technical Debt", "Refactoring", "Improvement"]
        }
      },
      {
        "rule_id": "rule_008",
        "priority": 2,
        "source_type": "field_value",
        "field": "customfield_10200",
        "value_type": "select"
      }
    ]
  }
}
```

### Simplified UI Approach

For users, we don't expose the full complexity. Instead, we provide:

1. **Metric-Driven Configuration**
   - "To calculate Deployment Frequency, we need to know:"
   - Input 1: How do you identify deployments? [Field dropdown] [Condition dropdown]
   - Input 2: What indicates success/failure? [Field dropdown] [Value dropdown]

2. **Progressive Disclosure**
   - Basic Mode: Simple field mappings (current approach)
   - Advanced Mode: Add conditions and filters
   - Expert Mode: JSON rule editor

3. **Smart Defaults**
   - Detect common patterns (e.g., fixVersions with release dates)
   - Suggest mappings based on field names
   - Validate against metric requirements

---

## Implementation Strategy

### Phase 1: Enhanced Field Mapper (Backward Compatible)
- Keep current simple mappings
- Add support for value-based mappings
- Add support for changelog extraction
- Add conditional filters (project, issuetype)

### Phase 2: Rule-Based Mapping System
- Implement mapping rule data model
- Create rule evaluation engine
- Support multiple rules with priority
- Add fallback mechanisms

### Phase 3: Advanced UI
- Metric-driven configuration wizard
- Visual rule builder (no JSON editing)
- Field validation and suggestions
- Preview/test mappings on sample data

---

## Data Source Types

### 1. Direct Field Value
- Simple: `field_id` → extract value
- Example: `customfield_10100` → "2025-01-15"

### 2. Field Value Matching
- Conditional: `field_id` → check if value matches condition
- Example: `status.name == "Deployed"`

### 3. Changelog Events
- Extract from history: `field_id` → find transition event
- Example: status changed from "In Progress" to "Done" at timestamp X

### 4. Changelog Timestamp
- Timestamp extraction: `field_id` → extract event timestamp
- Example: when status became "Done"

### 5. Fix Version Date
- Special handling: `fixVersions[*].releaseDate`
- Can extract multiple dates or earliest/latest

### 6. Calculated/Derived
- Computation: sum of durations in specific statuses
- Example: Active Time = sum(time in ["In Progress", "Review"])

### 7. Linked Issue Data
- Cross-reference: check linked issues for properties
- Example: has linked issue with type "Incident"

---

## Validation Requirements

Each mapping must validate:

1. **Field Exists**: Field ID exists in JIRA instance
2. **Type Compatible**: Field type matches expected data type
3. **Value Domain**: For select fields, check allowed values
4. **Required vs Optional**: Some metrics require specific mappings
5. **Logical Consistency**: E.g., start_date < end_date

---

## Migration Path

Current simple mappings:
```json
{
  "deployment_date": "customfield_10100",
  "incident_start": "created"
}
```

Enhanced mappings (backward compatible):
```json
{
  "deployment_date": {
    "field": "customfield_10100",
    "type": "datetime"
  },
  "incident_start": {
    "field": "created",
    "type": "datetime"
  }
}
```

Full rule-based mappings:
```json
{
  "deployment_event": {
    "rules": [
      {
        "field": "customfield_10100",
        "condition": {"operator": "equals", "value": "Deployed"},
        "filters": {"project": ["DEVOPS"]}
      }
    ]
  }
}
```

---

## User Experience Flow

### Metric Configuration Wizard

```
Step 1: Select Metric to Configure
→ [Deployment Frequency]

Step 2: Define Data Sources
Question: "How do you track deployments in JIRA?"

Option A: "We have a custom deployment date field"
→ Field: [customfield_10100 - Deployment Date] ✓

Option B: "We use status transitions"
→ Status: [Deployed to Production] ✓
→ Extract timestamp: [Yes]

Option C: "We use fix versions with release dates"
→ Field: [fixVersions] ✓
→ Release date required: [Yes]

Step 3: Add Filters (Optional)
→ Only for projects: [DEVOPS, BACKEND] (optional)
→ Only for issue types: [Deployment Task] (optional)
→ Only for environment: [Production] (optional)

Step 4: Test Mapping
→ Preview: Shows 5 sample issues with extracted values
→ Validate: "Found 23 deployments in last 7 days"

Step 5: Save Configuration
→ [Save Mapping]
```

---

## Conclusion

The current simple `field → field` mapping is insufficient for real-world DORA/Flow metrics because:

1. **Variables ≠ Fields**: Metrics need data variables that may come from multiple sources
2. **Conditional Logic**: Same field means different things in different contexts
3. **Derived Values**: Some variables require calculation (e.g., changelog analysis)
4. **JIRA Diversity**: Every organization configures JIRA differently

**Recommendation**: Implement a **rule-based mapping system** with a **metric-driven UI** that guides users through configuring each variable needed for their chosen metrics.

