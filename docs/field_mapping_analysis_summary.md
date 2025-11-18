# Field Mapping Analysis - Executive Summary

## Your Insight is Correct ✅

You're absolutely right that **no fields should be hardcoded**. The current implementation has serious limitations:

### Current Problems Found

1. **Hardcoded Assumptions**:
   - `resolutiondate` assumed for completion (Flow metrics)
   - `status` accessed directly without mapping (Flow Load)
   - `issuetype` used directly (Flow Distribution)
   - `fixVersions` used without configuration (Deployment detection)

2. **Insufficient Mappings**:
   - UI shows 15 fields, but only 8 are actually used
   - Many fields defined but never referenced in calculations
   - Some used fields (like `production_impact`) missing from UI

3. **No Conditional Logic**:
   - Can't filter by project, issue type, or environment
   - Can't map same field differently for different contexts
   - No support for value-based matching (e.g., `status.name == "Deployed"`)

4. **No Changelog Support**:
   - Can't extract timestamps from status transitions
   - Can't calculate time in different states (Flow Efficiency)
   - Missing active time tracking for efficiency metrics

## What the PM Formulas Actually Require

Based on PM-Metrics-Formulas.md analysis, metrics need **data variables**, not just fields:

### DORA Metrics Variables

| Metric                    | Variables Needed                                                                                                    | Possible Sources                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Deployment Frequency**  | deployment_event (boolean)<br>deployment_timestamp (datetime)<br>deployment_successful (boolean)                    | Custom field<br>Status transition<br>fixVersions.releaseDate<br>Issue type      |
| **Lead Time for Changes** | commit_timestamp (datetime)<br>deployment_timestamp (datetime)                                                      | Custom field<br>Changelog event<br>created date                                 |
| **Change Failure Rate**   | deployment_failed (boolean)<br>total_deployments (count)                                                            | Status value<br>Linked incidents<br>Custom field                                |
| **MTTR**                  | incident_detected_timestamp (datetime)<br>service_restored_timestamp (datetime)<br>is_production_incident (boolean) | Custom field<br>Changelog event<br>created/resolutiondate<br>Environment filter |

### Flow Metrics Variables

| Metric                | Variables Needed                                                               | Possible Sources                                                         |
| --------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| **Flow Velocity**     | is_completed (boolean)<br>completion_timestamp (datetime)                      | Status value<br>resolutiondate<br>Changelog event                        |
| **Flow Time**         | work_started_timestamp (datetime)<br>work_completed_timestamp (datetime)       | Changelog transition<br>Custom field<br>created date                     |
| **Flow Efficiency**   | active_time (duration)<br>total_flow_time (duration)<br>active_statuses (list) | **Changelog analysis**<br>Sum durations in states<br>Time tracking field |
| **Flow Load**         | is_in_progress (boolean)                                                       | Status value<br>Status category<br>Custom field                          |
| **Flow Distribution** | work_type_category (category)<br>work_type_mapping (config)                    | Issue type mapping<br>Custom field<br>Labels                             |

### Key Insight: Multiple Sources Per Variable

Every variable can come from different sources depending on JIRA setup:

**Example: `deployment_timestamp`**
- **Organization A**: Custom field `customfield_10100` (Deployment Date)
- **Organization B**: Changelog event (status → "Deployed to Production")
- **Organization C**: `fixVersions[0].releaseDate`
- **Organization D**: `resolutiondate` (proxy, not ideal)

**Current system**: Can only handle one source (Organization A)
**Proposed system**: Priority-ordered sources with fallbacks

## Proposed Architecture: Rule-Based Variable Mapping

### Core Concept

Instead of `field → field` mappings, use `variable → rules`:

```json
{
  "deployment_timestamp": {
    "variable_type": "datetime",
    "sources": [
      {
        "priority": 1,
        "type": "field_value",
        "field": "customfield_10100"
      },
      {
        "priority": 2,
        "type": "changelog_timestamp",
        "field": "status",
        "condition": {"transition_to": "Deployed to Production"}
      },
      {
        "priority": 3,
        "type": "fixversion_releasedate",
        "field": "fixVersions",
        "selector": "first"
      }
    ],
    "filters": {
      "project": ["DEVOPS"],
      "environment_field": "customfield_10200",
      "environment_value": "Production"
    }
  }
}
```

### Source Types Needed

1. **Field Value**: Direct field access
2. **Field Value Match**: Conditional (field == value)
3. **Changelog Event**: Detect transition (boolean)
4. **Changelog Timestamp**: Extract transition time
5. **Fix Version Date**: Special handling for fixVersions
6. **Calculated**: Derive from other sources (e.g., sum changelog durations)

### Filters Needed

- **Project**: `project.key in ["PROJ1", "PROJ2"]`
- **Issue Type**: `issuetype.name in ["Story", "Bug"]`
- **Environment**: `customfield_XXX == "Production"`
- **Custom JQL**: Advanced filtering

## Your Namespace Idea: Hierarchical Mapping

Your suggestion of `project.issuetype.field.value` is insightful! Let's refine it:

### Proposed Hierarchical Filter Structure

```json
{
  "deployment_event": {
    "sources": [
      {
        "priority": 1,
        "type": "field_value_match",
        "field": "status",
        "operator": "equals",
        "value": "Deployed",
        "scope": {
          "project": "DEVOPS",
          "issuetype": "Deployment Task"
        }
      },
      {
        "priority": 2,
        "type": "field_value_match",
        "field": "labels",
        "operator": "contains",
        "value": "deployed",
        "scope": {
          "project": "*",
          "issuetype": ["Story", "Bug"]
        }
      }
    ]
  }
}
```

### Scope Levels

1. **Global**: Applies to all issues (no scope specified)
2. **Project-level**: `scope: {"project": "PROJ1"}`
3. **Issue type-level**: `scope: {"issuetype": "Bug"}`
4. **Combined**: `scope: {"project": "PROJ1", "issuetype": "Bug"}`
5. **Field-level**: `field: "customfield_10100"` (already supported)
6. **Value-level**: `field: "status", value: "Done"` (conditional match)

This is cleaner than `project.issuetype.field.value` string notation, but achieves the same goal.

## Comparison with Your Namespace Approach

### Your Idea: `project.issuetype.field.value`
```
DEVOPS.Deployment.customfield_10100.Deployed
BACKEND.Story.status.Done
*.Bug.priority.Critical
```

**Pros**: Compact, easy to read
**Cons**: Hard to parse, ambiguous with JIRA's own dot notation

### Proposed: Structured Scope
```json
{
  "scope": {"project": "DEVOPS", "issuetype": "Deployment"},
  "field": "customfield_10100",
  "value": "Deployed"
}
```

**Pros**: Clear structure, extensible, type-safe
**Cons**: More verbose in JSON

**Recommendation**: Use structured approach in data model, but UI could present it as namespace-style for brevity.

## Metric-Driven UI Design

Users shouldn't need to understand variables or scopes. Instead:

### Wizard Flow Example: Deployment Frequency

```
Step 1: How do you identify deployments?

□ Custom deployment date field
  → Field: [customfield_10100 - Deployment Date ▼]
  → Projects: [All projects ⚫] or [Specific: DEVOPS, BACKEND]
  → Issue types: [All types ⚫] or [Specific: Deployment Task]

□ Status transition to "Deployed"
  → Status value: [Deployed to Production ▼]
  → Extract timestamp: [✓]
  
□ Fix version with release date
  → Use first release date

□ Issue type indicates deployment
  → Issue type: [Deployment ▼]

[✓] Allow multiple detection methods (priority order)

Step 2: Test configuration
✓ Found 23 deployments in last 7 days
  Preview: DEVOPS-123, DEVOPS-124, DEVOPS-125...

[Save Configuration]
```

Behind the scenes, this creates:
```json
{
  "deployment_event": {
    "sources": [
      {"priority": 1, "type": "field_value", "field": "customfield_10100", "scope": {"project": ["DEVOPS", "BACKEND"]}},
      {"priority": 2, "type": "changelog_event", "field": "status", "condition": {"transition_to": "Deployed to Production"}}
    ]
  }
}
```

## Migration Path

### Phase 1: Backward Compatibility Layer
- Keep existing simple mappings working
- Convert to new format internally
- No user-facing changes

### Phase 2: Enhanced Variable System
- Add support for multiple sources
- Add changelog extraction
- Add conditional filters
- Expose via advanced settings

### Phase 3: Metric Configuration Wizard
- Metric-driven UI for non-technical users
- Automatic variable mapping
- Sample data preview
- Migration tool for existing users

## Implementation Priorities

### Must-Have (Phase 1)
1. Variable extraction engine with priority sources
2. Changelog timestamp extraction (critical for Flow Efficiency)
3. Conditional filters (project, issuetype, environment)
4. Backward compatibility with existing mappings

### Should-Have (Phase 2)
5. Metric configuration wizard UI
6. Field value matching (status == "Done")
7. Fix version date extraction
8. Calculated variables (sum changelog durations)

### Nice-to-Have (Phase 3)
9. Custom JQL filters
10. Linked issue data extraction
11. Advanced rule JSON editor
12. Mapping templates library

## Key Questions Answered

### Q: Should we use namespace notation or structured scope?
**A**: Structured scope in data model (extensible, type-safe), but UI can present as namespace for brevity.

### Q: Are current field mappings sufficient?
**A**: No. Missing changelog support, conditional logic, and multiple source options.

### Q: What's the biggest gap in current implementation?
**A**: **Flow Efficiency** requires changelog analysis (time in active statuses), which current system cannot do.

### Q: Should everything be configurable?
**A**: Yes, with smart defaults. Standard fields (created, resolutiondate, status) can have suggested mappings, but user can override.

### Q: How to handle JIRA diversity?
**A**: Priority-ordered sources with fallbacks. Primary source might be custom field, fallback to standard fields.

## Recommended Next Steps

1. **Review Proposal** (this document + 3 detailed specs)
   - Field Mapping Requirements Analysis
   - Metric Variable Mapping Specification  
   - Mapping Architecture Proposal

2. **Decide on Scope**
   - Full implementation or phased approach?
   - Which source types to support initially?
   - UI wizard or advanced editor first?

3. **Create Pydantic Models**
   - VariableMapping, SourceRule, MappingFilter classes
   - Validation logic and type checking

4. **Build Variable Extractor**
   - Core extraction engine
   - Support for field_value, changelog_timestamp, fixversion sources
   - Unit tests with sample JIRA data

5. **Update Metric Calculators**
   - Replace hardcoded field access with variable extraction
   - Add proper error handling for missing variables
   - Comprehensive logging

6. **Create UI Wizard**
   - Metric-driven configuration flow
   - Sample data preview
   - Validation and testing

## Summary

Your instinct is correct: **no fields should be hardcoded**. The current system is too rigid for real-world JIRA diversity.

**Recommended solution**: Rule-based variable mapping system with:
- Multiple source options (priority-ordered)
- Conditional filters (project, issuetype, environment)
- Changelog extraction support
- Metric-driven UI (users configure what they need, not how to get it)
- Backward compatibility with existing simple mappings

This architecture handles the complexity of JIRA diversity while keeping the user experience simple and guided.

## Documentation Created

1. **field_mapping_requirements.md** - Problem analysis and requirements
2. **metric_variable_mapping_spec.md** - Complete variable catalog for all metrics
3. **mapping_architecture_proposal.md** - Proposed implementation with code examples
4. **field_mapping_analysis_summary.md** - This executive summary

Total: 4 comprehensive specification documents ready for implementation.
