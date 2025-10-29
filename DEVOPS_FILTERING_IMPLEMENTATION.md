# DevOps Project Filtering Implementation

## Overview

Implemented complete filtering architecture to exclude DevOps project issues (RI) from all burndown/velocity/statistics calculations while keeping them available for DORA metadata extraction.

## Problem Statement

**CRITICAL REQUIREMENT**: DevOps project issues (RI - Operational Tasks) must NEVER be counted in:
- Burndown charts
- Velocity calculations  
- Statistics/metrics displays
- Scope tracking

However, these issues MUST remain accessible for:
- DORA metrics (deployment frequency, lead time, change failure rate, MTTR)
- Flow metrics metadata extraction

## Implementation Summary

### Files Modified

1. **data/jira_simple.py** (`sync_jira_scope_and_data` function, lines 660-730)
   - **Change**: Added DevOps filtering immediately after cache load, before any calculations
   - **Pattern**: Filter issues → calculate scope with filtered data → generate CSV from filtered data
   ```python
   # Load issues from cache or JIRA
   cache_loaded, issues = load_jira_cache(...)
   
   # NEW: Filter out DevOps project issues
   devops_projects = config.get("devops_projects", [])
   if devops_projects:
       from data.project_filter import filter_development_issues
       issues_for_metrics = filter_development_issues(issues, devops_projects)
       filtered_count = len(issues) - len(issues_for_metrics)
       logger.info(f"Filtered out {filtered_count} DevOps project issues...")
   else:
       issues_for_metrics = issues
   
   # Use issues_for_metrics (not issues) for scope and statistics
   scope_data = calculate_jira_project_scope(issues_for_metrics, ...)
   csv_data = jira_to_csv_format(issues_for_metrics, ...)
   ```

2. **data/persistence.py** (`save_app_settings` function, lines 65-130)
   - **Change**: Added preservation of `devops_projects` and `field_mapping_notes` when saving settings
   - **Pattern**: Preserve critical configuration that should not be overwritten by UI interactions
   ```python
   if "devops_projects" in existing_settings:
       settings["devops_projects"] = existing_settings["devops_projects"]
       logger.debug("Preserved existing devops_projects during save")
   if "field_mapping_notes" in existing_settings:
       settings["field_mapping_notes"] = existing_settings["field_mapping_notes"]
       logger.debug("Preserved existing field_mapping_notes during save")
   ```

3. **data/project_filter.py** (`get_issue_project_key` function, lines 22-42)
   - **Change**: Added fallback to parse project key from issue key when `fields.project` is missing
   - **Reason**: JIRA API doesn't return `project` field unless explicitly requested in field list
   - **Pattern**: Try `fields.project.key` first, fallback to parsing "RI-8957" → "RI"
   ```python
   def get_issue_project_key(issue: Dict[str, Any]) -> str:
       try:
           # Try to get from fields.project.key first
           project_key = issue.get("fields", {}).get("project", {}).get("key", "")
           if project_key:
               return project_key

           # Fallback: parse from issue key (e.g., "RI-8957" → "RI")
           issue_key = issue.get("key", "")
           if issue_key and "-" in issue_key:
               return issue_key.split("-")[0]

           return ""
       except (AttributeError, KeyError) as e:
           logger.warning(f"Failed to extract project key from issue: {e}")
           return ""
   ```

4. **tests/unit/data/test_project_filter.py** (`test_extract_project_key_missing_fields`)
   - **Change**: Updated test to expect fallback behavior (extracting "TEST" from "TEST-1")
   - **Reason**: Fallback logic is the correct behavior for real-world JIRA data
   ```python
   def test_extract_project_key_missing_fields(self):
       """Test handling missing fields - fallback to parsing issue key."""
       issue = {"key": "TEST-1"}
       assert get_issue_project_key(issue) == "TEST"  # Changed from ""
   ```

### Configuration Structure

**app_settings.json**:
```json
{
  "jql_query": "(project = A935 AND issuetype in (Story, Task, Bug) AND created >= -52w) OR (project = RI AND issuetype = \"Operational Task\" AND created >= -52w)",
  "devops_projects": ["RI"],
  "field_mappings": {
    "affected_environment": "customfield_11309",
    "severity_level": "customfield_11000",
    "deployment_date": "customfield_14800",
    ...
  }
}
```

- **jql_query**: Multi-project query that fetches BOTH development (A935) and DevOps (RI) issues
- **devops_projects**: List of project keys to exclude from metrics (currently ["RI"])
- **field_mappings**: Drei-specific custom field mappings for DORA/Flow metrics

## Data Flow Architecture

### Before Filtering (PROBLEM):
```
JIRA API → Cache → [A935: 841 + RI: 1778] → Scope Calculator → Burndown Charts
                                                 ↓
                                             WRONG: Counted all 2,619 issues
```

### After Filtering (SOLUTION):
```
JIRA API → Cache → [A935: 841 + RI: 1778]
                           ↓
                    Filter Function
                    ↙            ↘
              [A935: 841]    [RI: 1778]
                    ↓              ↓
            Scope Calculator   DORA Metrics
                    ↓
            Burndown Charts
                    ↓
            Statistics/Velocity
```

## Filtering Functions

### `filter_development_issues(issues, devops_projects)`
**Purpose**: Filter to ONLY development project issues (exclude DevOps)  
**Use Cases**: Burndown charts, velocity metrics, scope metrics, statistics  
**Returns**: List of issues NOT in devops_projects

### `filter_devops_issues(issues, devops_projects)`
**Purpose**: Filter to ONLY DevOps project issues  
**Use Cases**: DORA deployment counting (when combined with issue type filtering)  
**Returns**: List of issues IN devops_projects

### `is_devops_issue(issue, devops_projects)`
**Purpose**: Check if single issue is a DevOps project issue  
**Returns**: Boolean

## Test Results

**All 775 unit tests passing** ✅

Key test coverage:
- ✅ `test_extract_project_key_missing_fields` - Fallback parsing from issue key
- ✅ `test_filter_development_issues_excludes_devops` - Filtering excludes DevOps projects
- ✅ `test_filter_devops_issues_includes_only_devops` - Filtering includes only DevOps
- ✅ `test_is_devops_issue_true` / `test_is_devops_issue_false` - Classification logic
- ✅ All DORA calculator tests - DORA metrics still work with filtering
- ✅ All data processing tests - Burndown/velocity calculations unaffected

## Verification

### Filtering Correctness
- **Total issues**: 2,619 (from multi-project JQL query)
- **Development issues (A935)**: 841 (32.1%) - **COUNTED** in metrics
- **DevOps issues (RI)**: 1,778 (67.9%) - **EXCLUDED** from metrics
- **Overlap**: 0 issues (mutually exclusive filtering)
- **Accounted for**: 841 + 1,778 = 2,619 ✅

### Fallback Logic
- ✅ Handles JIRA API responses missing `fields.project`
- ✅ Parses project key from issue key (e.g., "RI-8957" → "RI")
- ✅ Works with all existing test cases

## Key Design Decisions

### 1. Filter at Data Load Point
**Decision**: Filter immediately after loading from cache, before any calculations  
**Rationale**: 
- Single point of filtering (easier to maintain)
- Prevents contamination of downstream calculations
- Clear separation: raw data → filtered data → calculated metrics

### 2. Preserve Original Issues for DORA
**Decision**: Keep full issue list available for DORA callbacks  
**Rationale**:
- DORA callbacks need access to DevOps issues for deployment metadata
- DORA calculator has its own filtering logic for deployment/incident classification
- Filtering happens at the appropriate level for each use case

### 3. Configuration-Driven Approach
**Decision**: `devops_projects` configured in app_settings.json, NOT hardcoded  
**Rationale**:
- Reusable for other customers with different project structures
- Easy to modify without code changes
- Supports multiple DevOps projects if needed

### 4. Fallback Project Key Extraction
**Decision**: Parse project key from issue key as fallback  
**Rationale**:
- JIRA API doesn't return `project` field by default
- Adding `project` to field list would increase API response size
- Issue key always contains project prefix (JIRA requirement)

## Backward Compatibility

**NONE REQUIRED** - Application not yet live, clean implementation without legacy code.

Previous considerations removed:
- ❌ No fallback to old field names (production_impact → affected_environment)
- ❌ No default parameter values for custom field IDs
- ❌ No backward-compatible filtering behavior

## Configuration Notes

Located in `app_settings.json`:

```json
"field_mapping_notes": {
  "architecture": {
    "multi_project_setup": "Using (project = A935 AND issuetype in (Story, Task, Bug)) OR (project = RI AND issuetype = 'Operational Task')",
    "devops_projects": ["RI"],
    "filtering_strategy": "RI issues excluded from burndown/velocity metrics but available for DORA calculations"
  },
  ...
}
```

## Next Steps (If Needed)

1. **Test with Live Data**: Trigger "Update Data from JIRA" and verify logs show correct filtering
2. **Verify DORA Metrics**: Navigate to DORA dashboard and ensure metrics still calculate correctly
3. **Check Statistics**: Verify that statistics cards show only A935 issue counts
4. **Validate Burndown**: Confirm burndown chart reflects only development project data

## Related Documentation

- **Architecture**: `.github/copilot-instructions.md` - Project filtering principles
- **DORA Mapping**: `docs/DORA_Flow_Jira_Mapping.md` - Field mapping documentation
- **Field Mapper**: `data/field_mapper.py` - Custom field configuration utilities
- **Project Filter**: `data/project_filter.py` - Complete filtering implementation
