# Metric Variable Mapping Specification

## Purpose

This document defines **all data variables** required to calculate each DORA and Flow metric according to PM-Metrics-Formulas.md. Each variable specifies:

1. **What** data is needed (semantic meaning)
2. **Where** it can come from (JIRA field sources)
3. **How** to extract it (direct value, changelog, calculation)
4. **When** to use it (conditional filters)

## Variable Taxonomy

### Variable Source Types

1. **Field Value** - Direct field access (e.g., `customfield_10100`)
2. **Field Value Match** - Field value equals condition (e.g., `status.name == "Done"`)
3. **Changelog Event** - Detect field transition (e.g., status changed to "Deployed")
4. **Changelog Timestamp** - Extract transition timestamp
5. **Fix Version Date** - Extract release date from fixVersions
6. **Calculated** - Derived from multiple sources (e.g., sum of durations)
7. **Linked Issue** - Data from related issues

### Data Types

- **boolean** - True/false flag
- **datetime** - Timestamp (ISO 8601)
- **number** - Numeric value (integer or decimal)
- **duration** - Time span (calculated from timestamps)
- **category** - Enumerated value (Feature, Defect, Risk, Tech Debt)
- **count** - Integer count

---

## DORA Metrics Variables

### 1. Deployment Frequency

**Formula:** $\text{DF}(W) = \frac{\text{Number of Successful Deployments}}{W}$

#### Variable: `deployment_event`
- **Type**: boolean
- **Required**: Yes
- **Description**: Indicates whether an issue represents a deployment occurrence
- **Sources**:
  1. Custom field with value check: `customfield_XXXXX == "Deployed"`
  2. Status transition: changelog shows transition to "Deployed"
  3. Fix version: `fixVersions[*].releaseDate` exists
  4. Issue type: `issuetype.name == "Deployment"`
- **Filters**: 
  - Project: may need to filter to specific projects
  - Issue type: may need specific types only
  - Environment: filter to "Production" only

#### Variable: `deployment_timestamp`
- **Type**: datetime
- **Required**: Yes
- **Description**: When the deployment occurred
- **Sources**:
  1. Custom datetime field: `customfield_XXXXX`
  2. Changelog timestamp: when status changed to "Deployed"
  3. Fix version release date: `fixVersions[0].releaseDate`
  4. Resolution date: `resolutiondate` (if no better source)
- **Validation**: Must be within time window W

#### Variable: `deployment_successful`
- **Type**: boolean
- **Required**: Yes (for accurate DF)
- **Description**: Whether deployment succeeded (exclude failures from count)
- **Sources**:
  1. Custom boolean field: `customfield_XXXXX == true`
  2. Status check: `status.name not in ["Failed", "Rolled Back"]`
  3. Resolution check: `resolution.name == "Deployed Successfully"`
  4. No linked incidents: `issuelinks` does not contain type "Incident"
- **Default**: Assume true if not specified (but warn user)

#### Variable: `deployment_environment`
- **Type**: category
- **Required**: No (but recommended)
- **Description**: Which environment was deployed to (filter for Production)
- **Sources**:
  1. Custom select field: `customfield_XXXXX`
  2. Label check: `labels contains "production"`
  3. Component: `components[*].name == "Production"`
- **Filter**: Only count Production deployments for DORA

---

### 2. Lead Time for Changes

**Formula:** $\text{LT}(W) = \text{median}\left(\frac{\text{Deployment}_j - \text{Commit}_j}{1 \text{ day}}\right)$

#### Variable: `commit_timestamp`
- **Type**: datetime
- **Required**: Yes
- **Description**: When code was committed ($\text{Commit}_j$)
- **Sources**:
  1. Custom datetime field: `customfield_XXXXX` (git commit timestamp)
  2. Issue created date: `created` (if commits tracked as issues)
  3. Changelog: first transition to "In Development"
  4. External: extract from git commit URL in description/links
- **Validation**: Must be before deployment timestamp

#### Variable: `deployment_timestamp`
- **Type**: datetime
- **Required**: Yes
- **Description**: When code was deployed ($\text{Deployment}_j$)
- **Sources**: Same as Deployment Frequency above

#### Variable: `is_code_change`
- **Type**: boolean
- **Required**: No (but recommended)
- **Description**: Filter to only code changes (exclude config, docs)
- **Sources**:
  1. Issue type: `issuetype.name in ["Story", "Bug", "Task"]`
  2. Custom field: `customfield_XXXXX == "Code Change"`
  3. Label: `labels contains "code-change"`
- **Filter**: Exclude non-code items from Lead Time calculation

---

### 3. Change Failure Rate

**Formula:** $\text{CFR}(W) = \frac{\text{Number of Failed Deployments}}{\text{Total Number of Deployments}} \times 100\%$

#### Variable: `deployment_failed`
- **Type**: boolean
- **Required**: Yes
- **Description**: Whether deployment failed or required rollback
- **Sources**:
  1. Custom boolean field: `customfield_XXXXX == false` (deployment_successful)
  2. Status: `status.name in ["Failed", "Rolled Back", "Hotfix Required"]`
  3. Linked issues: has linked "Incident" or "Hotfix" issue
  4. Resolution: `resolution.name in ["Failed", "Rolled Back"]`
- **Logic**: Inverse of `deployment_successful`

#### Variable: `total_deployments`
- **Type**: count
- **Required**: Yes
- **Description**: Total deployment attempts (successful + failed)
- **Sources**: Count of all `deployment_event == true` (see DF above)

#### Variable: `failure_reason`
- **Type**: category
- **Required**: No
- **Description**: Why deployment failed (for analysis)
- **Sources**:
  1. Custom select field: `customfield_XXXXX`
  2. Labels: extract from labels
  3. Comments: parse from comments (advanced)

---

### 4. Mean Time to Recovery (MTTR)

**Formula:** $\text{MTTR}(W) = \text{median}\left(\frac{\sum_{i=1}^{m} (R_i - F_i)}{m}\right)$

#### Variable: `incident_detected_timestamp`
- **Type**: datetime
- **Required**: Yes
- **Description**: When incident/failure was detected ($F_i$)
- **Sources**:
  1. Custom datetime field: `customfield_XXXXX`
  2. Issue created: `created` (if issue type = "Incident")
  3. Changelog: transition to "In Progress" for incident issues
  4. Custom status: transition to "Incident Detected"
- **Validation**: Must be before restoration timestamp

#### Variable: `service_restored_timestamp`
- **Type**: datetime
- **Required**: Yes
- **Description**: When service was restored ($R_i$)
- **Sources**:
  1. Custom datetime field: `customfield_XXXXX`
  2. Resolution date: `resolutiondate`
  3. Changelog: transition to "Resolved" or "Closed"
  4. Custom status: transition to "Service Restored"
- **Validation**: Must be after detection timestamp

#### Variable: `is_production_incident`
- **Type**: boolean
- **Required**: Yes
- **Description**: Filter to only production incidents
- **Sources**:
  1. Custom field: `customfield_affected_environment == "Production"`
  2. Issue type: `issuetype.name in ["Incident", "Production Bug"]`
  3. Priority: `priority.name in ["Critical", "Blocker"]`
  4. Label: `labels contains "production-incident"`
- **Filter**: Only count production incidents for MTTR

#### Variable: `incident_severity`
- **Type**: category
- **Required**: No
- **Description**: Incident severity (for filtering/analysis)
- **Sources**:
  1. Priority: `priority.name`
  2. Custom field: `customfield_XXXXX`
  3. Label: extract severity from labels

---

## Flow Metrics Variables

### 5. Flow Velocity

**Formula:** $\text{Flow Velocity}(W) = \frac{\text{Number of Completed Flow Items}}{W}$

#### Variable: `is_completed`
- **Type**: boolean
- **Required**: Yes
- **Description**: Whether work item is completed
- **Sources**:
  1. Status: `status.name in ["Done", "Closed", "Resolved"]`
  2. Status category: `status.statusCategory.key == "done"`
  3. Resolution: `resolution is not null`
  4. Changelog: has transition to done status
- **Validation**: Must have completion timestamp

#### Variable: `completion_timestamp`
- **Type**: datetime
- **Required**: Yes
- **Description**: When work was completed ($C_i$)
- **Sources**:
  1. Resolution date: `resolutiondate`
  2. Custom field: `customfield_XXXXX`
  3. Changelog: timestamp of transition to done status
  4. Updated date: `updated` (if no better source)
- **Validation**: Must be within time window W

#### Variable: `is_flow_item`
- **Type**: boolean
- **Required**: No
- **Description**: Filter to flow-eligible items
- **Sources**:
  1. Issue type: `issuetype.name in ["Story", "Bug", "Task", "Improvement"]`
  2. Exclude: `issuetype.name not in ["Epic", "Sub-task"]`
  3. Custom field: `customfield_XXXXX == true`
- **Filter**: Exclude non-flow items (Epics, organizational issues)

---

### 6. Flow Time

**Formula:** $\text{Flow Time}(W) = \frac{\sum_{i=1}^{n} (C_i - S_i)}{n}$

#### Variable: `work_started_timestamp`
- **Type**: datetime
- **Required**: Yes
- **Description**: When work began ($S_i$)
- **Sources**:
  1. Custom field: `customfield_XXXXX` (work start date)
  2. Changelog: first transition to "In Progress"
  3. Changelog: first status change from initial state
  4. Created date: `created` (fallback, may include queue time)
- **Note**: Ideally from changelog to exclude queue time

#### Variable: `work_completed_timestamp`
- **Type**: datetime
- **Required**: Yes
- **Description**: When work finished ($C_i$)
- **Sources**: Same as `completion_timestamp` in Flow Velocity

#### Variable: `flow_time_duration`
- **Type**: duration
- **Required**: No (calculated)
- **Description**: Total elapsed time ($C_i - S_i$)
- **Calculation**: `work_completed_timestamp - work_started_timestamp`
- **Unit**: Days (or hours for shorter cycles)

---

### 7. Flow Efficiency

**Formula:** $\text{Flow Efficiency}(W) = \frac{\text{Active Time}}{\text{Total Flow Time}} \times 100\%$

#### Variable: `active_time`
- **Type**: duration
- **Required**: Yes
- **Description**: Time spent in active work states
- **Sources**:
  1. Custom field: `customfield_XXXXX` (time tracking)
  2. Changelog analysis: sum of durations in active statuses
  3. Calculated: sum(time in "In Progress", "In Review", "Testing")
- **Requires**: Status change timestamps from changelog

#### Variable: `total_flow_time`
- **Type**: duration
- **Required**: Yes
- **Description**: Total elapsed time from start to completion
- **Calculation**: Same as `flow_time_duration` above

#### Variable: `active_statuses`
- **Type**: category[]
- **Required**: Yes
- **Description**: Which statuses count as "active work"
- **Sources**:
  1. Configuration: user defines active statuses
  2. Default: ["In Progress", "In Review", "Testing", "In Development"]
- **Usage**: Filter changelog events to sum active time

#### Variable: `wait_statuses`
- **Type**: category[]
- **Required**: No
- **Description**: Which statuses count as "waiting" (inverse of active)
- **Sources**:
  1. Configuration: user defines wait statuses
  2. Default: ["Blocked", "Waiting", "Backlog", "To Do"]
- **Usage**: For analysis of waste in system

---

### 8. Flow Load (WIP)

**Formula:** $\text{Flow Load}(W) = \text{Number of Active Work Items at Time } W$

#### Variable: `is_in_progress`
- **Type**: boolean
- **Required**: Yes
- **Description**: Whether work item is currently in progress
- **Sources**:
  1. Status: `status.name in ["In Progress", "In Review", "Testing"]`
  2. Status category: `status.statusCategory.key == "indeterminate"`
  3. Custom field: `customfield_XXXXX == "Active"`
- **Snapshot**: Measured at specific time W

#### Variable: `wip_count`
- **Type**: count
- **Required**: Yes (calculated)
- **Description**: Number of items with `is_in_progress == true`
- **Calculation**: Count of issues matching in-progress criteria
- **Note**: Can be averaged over time window W

---

### 9. Flow Distribution

**Formula:** $\text{Flow Distribution}(W) = \frac{\text{Items of Type } j}{\text{Total Items}} \times 100\%$

#### Variable: `work_type_category`
- **Type**: category
- **Required**: Yes
- **Description**: Which category this work belongs to
- **Values**: Feature | Defect | Risk | Tech Debt
- **Sources**:
  1. Issue type mapping: `issuetype.name` → category
  2. Custom field: `customfield_XXXXX` (if organization tracks explicitly)
  3. Label matching: parse labels for category keywords
  4. Component: `components[*].name` → category

#### Variable: `work_type_mapping`
- **Type**: object
- **Required**: Yes
- **Description**: How to map issue types to Flow categories
- **Example**:
  ```json
  {
    "Feature": ["Story", "Epic", "New Feature", "Enhancement"],
    "Defect": ["Bug", "Defect", "Production Bug"],
    "Risk": ["Risk", "Security Issue", "Compliance"],
    "Tech Debt": ["Technical Debt", "Refactoring", "Improvement"]
  }
  ```
- **Customization**: Each organization defines own mapping

#### Variable: `completed_in_window`
- **Type**: boolean
- **Required**: Yes
- **Description**: Filter to items completed in time window W
- **Sources**: Same as `is_completed` + `completion_timestamp` validation

---

### 10. Flow Predictability

**Formula:** $\text{Flow Predictability}(W) = \frac{\text{Actual Value}}{\text{Planned Value}} \times 100\%$

#### Variable: `planned_business_value`
- **Type**: number
- **Required**: Yes
- **Description**: Expected value for time window
- **Sources**:
  1. Story points: `customfield_storypoints`
  2. Custom field: `customfield_XXXXX` (business value)
  3. Count: number of planned items
  4. Priority weighting: calculated from priority levels
- **Aggregation**: Sum across planned items

#### Variable: `actual_business_value`
- **Type**: number
- **Required**: Yes
- **Description**: Delivered value in time window
- **Sources**: Same as planned, filtered to completed items only

#### Variable: `was_planned`
- **Type**: boolean
- **Required**: Yes
- **Description**: Whether item was in original plan
- **Sources**:
  1. Sprint assignment: `sprint` field value
  2. Custom field: `customfield_XXXXX == "Planned"`
  3. Label: `labels contains "planned"`
  4. Created before window: `created < window_start`
- **Filter**: Only count planned items for predictability

#### Variable: `was_completed`
- **Type**: boolean
- **Required**: Yes
- **Description**: Whether planned item was delivered
- **Sources**: Same as `is_completed` in Flow Velocity

---

## Average Cycle Time Variables

**Formula:** $\text{Avg Cycle Time}(W) = \frac{\sum_{i=1}^{n} (C_i - S_i)}{n}$

### Same as Flow Time Variables:
- `work_started_timestamp` ($S_i$)
- `work_completed_timestamp` ($C_i$)
- `flow_time_duration` (calculated)

---

## Cross-Metric Variables

### Standard JIRA Fields (Always Available)

These fields should be accessible without custom mapping:

- `project.key` - Project identifier
- `project.name` - Project name
- `issuetype.name` - Issue type
- `status.name` - Current status
- `status.statusCategory.key` - Status category (todo, indeterminate, done)
- `priority.name` - Priority level
- `created` - Issue creation timestamp
- `updated` - Last update timestamp
- `resolutiondate` - Resolution timestamp
- `resolution.name` - Resolution type
- `fixVersions[*].name` - Fix version names
- `fixVersions[*].releaseDate` - Fix version release dates
- `labels` - Array of labels
- `components[*].name` - Component names

### Changelog Access

All metrics requiring timestamps benefit from changelog analysis:

- **Field**: Any field that can transition
- **Events**: 
  - Status transitions: `status changed from X to Y`
  - Field updates: `field changed from A to B`
- **Timestamps**: Extract `created` timestamp from changelog item

---

## Mapping Rule Priority

When multiple sources can provide same variable, use priority:

1. **Custom Field** (highest confidence) - Explicitly tracks the data
2. **Changelog Event** (medium confidence) - Derived from history
3. **Standard Field** (variable confidence) - May not perfectly match metric intent
4. **Calculated** (depends on inputs) - Accuracy depends on source data quality

---

## Validation Rules

### Required Mappings by Metric

| Metric                | Required Variables                                                              | Optional Variables                            |
| --------------------- | ------------------------------------------------------------------------------- | --------------------------------------------- |
| Deployment Frequency  | deployment_event, deployment_timestamp                                          | deployment_successful, deployment_environment |
| Lead Time for Changes | commit_timestamp, deployment_timestamp                                          | is_code_change                                |
| Change Failure Rate   | deployment_failed, total_deployments                                            | failure_reason                                |
| MTTR                  | incident_detected_timestamp, service_restored_timestamp, is_production_incident | incident_severity                             |
| Flow Velocity         | is_completed, completion_timestamp                                              | is_flow_item                                  |
| Flow Time             | work_started_timestamp, work_completed_timestamp                                | -                                             |
| Flow Efficiency       | active_time, total_flow_time, active_statuses                                   | wait_statuses                                 |
| Flow Load             | is_in_progress                                                                  | -                                             |
| Flow Distribution     | work_type_category, work_type_mapping, completed_in_window                      | -                                             |
| Flow Predictability   | planned_business_value, actual_business_value, was_planned, was_completed       | -                                             |

### Type Validation

Each variable must validate against expected type:

- **boolean**: Field value resolves to true/false
- **datetime**: Valid ISO 8601 timestamp
- **number**: Numeric value (integer or decimal)
- **duration**: Calculated from two valid datetimes
- **category**: Value in allowed enumeration
- **count**: Non-negative integer

---

## Implementation Notes

### Backward Compatibility

Current simple mappings like:
```json
{"deployment_date": "customfield_10100"}
```

Can be interpreted as:
```json
{
  "deployment_timestamp": {
    "source_type": "field_value",
    "field": "customfield_10100",
    "data_type": "datetime"
  }
}
```

### Progressive Enhancement

Users start with simple mappings, can add:
1. Conditional filters (project, issuetype)
2. Multiple source rules with priority
3. Changelog extraction rules
4. Custom calculations

### Metric-Driven UI

Configuration wizard should ask:

**For Deployment Frequency:**
1. "How do you identify deployments?" → `deployment_event` mapping
2. "When did deployment occur?" → `deployment_timestamp` mapping
3. "How do you know if deployment succeeded?" → `deployment_successful` mapping
4. (Optional) "Which environment?" → `deployment_environment` filter

This makes it clear **why** each mapping is needed.

---

## Conclusion

Every DORA and Flow metric requires specific **data variables** (not just field mappings). This specification:

1. ✅ Lists all variables required for each metric
2. ✅ Defines variable types and validation rules
3. ✅ Provides multiple source options per variable
4. ✅ Explains conditional logic and filters
5. ✅ Supports progressive complexity (simple → advanced)
6. ✅ Maintains backward compatibility
7. ✅ Enables metric-driven user experience

Next step: Design data model and UI for rule-based variable mapping system.
