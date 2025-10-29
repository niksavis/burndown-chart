# Project Filtering Implementation

## Overview

Implemented comprehensive project filtering to support multi-project Jira setups where development work and operational deployments are tracked in separate projects.

## Architecture

### Cross-Project Setup

- **Development Projects**: DEV1, DEV2, etc. - contain Stories, Tasks, Bugs, Epics
- **DevOps Projects**: DEVOPS (and others) - contain Operational Tasks for deployment tracking
- **Unified JQL Query**: `project in (DEV1, DEVOPS) and type in (Story, Task, Bug, Operational Task)`
- **Configuration-Based Filtering**: `devops_projects: ["DEVOPS"]` array in `app_settings.json`

### Design Decision: Unified Query with Post-Fetch Filtering

**Approach**: Fetch all issues with single JQL query, then filter by project type based on metric needs.

**Benefits**:
- **Maintainability**: Single query to manage instead of separate queries per metric
- **Performance**: One API call vs multiple calls
- **Flexibility**: Easy to add new projects or change filtering logic
- **Data Consistency**: All metrics work from same dataset snapshot

## Implementation

### New Module: `data/project_filter.py`

Provides filtering functions for different metric types:

#### Core Functions

```python
# Project identification
get_issue_project_key(issue) -> str
get_issue_type(issue) -> str
is_devops_issue(issue, devops_projects) -> bool
is_development_issue(issue, devops_projects) -> bool

# Metric-specific filters
filter_development_issues(issues, devops_projects) -> List[Dict]
filter_devops_issues(issues, devops_projects) -> List[Dict]
filter_deployment_issues(issues, devops_projects) -> List[Dict]
filter_incident_issues(issues, devops_projects, ...) -> List[Dict]
filter_work_items(issues, devops_projects, work_item_types) -> List[Dict]

# Analytics
get_project_summary(issues, devops_projects) -> Dict
```

#### Filtering Rules

| Metric Type               | Project Filter                                           | Issue Type Filter        | Additional Filters                   |
| ------------------------- | -------------------------------------------------------- | ------------------------ | ------------------------------------ |
| **Burndown/Velocity**     | Development projects only                                | Stories, Tasks, Bugs     | Exclude devops_projects              |
| **Deployment Frequency**  | DevOps projects only                                     | Operational Tasks        | Match deployment criteria            |
| **Change Failure Rate**   | DevOps projects (deployments) + Dev projects (incidents) | Operational Tasks + Bugs | Production incidents only            |
| **Mean Time to Recovery** | Development projects only                                | Bugs                     | Production environment = "PROD"      |
| **Lead Time for Changes** | Development projects only                                | Stories, Tasks           | Links to deployments via fixVersions |
| **Flow Metrics**          | Development projects only                                | Stories, Tasks           | Active status values                 |

### DORA Calculator Updates

Updated all DORA metric functions to support project filtering:

```python
# Updated function signatures
calculate_deployment_frequency(..., devops_projects: Optional[List[str]] = None)
calculate_lead_time_for_changes(..., devops_projects: Optional[List[str]] = None)
calculate_change_failure_rate(..., devops_projects: Optional[List[str]] = None)
calculate_mean_time_to_recovery(..., devops_projects: Optional[List[str]] = None)
```

**Key Changes**:
- Added `devops_projects` parameter to all metric functions
- Filters issues at function entry using appropriate filter functions
- Maintains backward compatibility (empty/None devops_projects = no filtering)
- Adds `filtered_issue_count` to metric results for transparency

### Configuration Updates

**`app_settings.json`** additions:

```json
{
  "jql_query": "project in (DEV1, DEVOPS) and type in (Story, Task, Bug, Operational Task) and created >= -52w",
  "devops_projects": ["DEVOPS"],
  "field_mapping_notes": {
    "note_1": "Multi-project setup: Development in DEV1, Deployments in DEVOPS",
    "note_2": "devops_projects array specifies which projects contain Operational Tasks",
    "note_3": "Burndown/velocity metrics automatically exclude devops_projects",
    "note_4": "DORA metrics filter to appropriate projects based on metric type",
    ...
  }
}
```

## Testing

### Test Coverage

**31 comprehensive tests** in `tests/unit/data/test_project_filter.py`:

- **Project Key Extraction**: 4 tests
- **Issue Type Extraction**: 4 tests
- **DevOps Project Detection**: 6 tests
- **Development Issue Filtering**: 4 tests
- **DevOps Issue Filtering**: 3 tests
- **Deployment Issue Filtering**: 2 tests
- **Incident Issue Filtering**: 4 tests
- **Work Item Filtering**: 2 tests
- **Project Summary**: 2 tests

**Updated DORA tests** to include project structure:
- Added `project` and `issuetype` fields to test fixtures
- Updated function calls to pass `devops_projects` parameter
- All 14 DORA tests passing

**Total Test Results**: 775 tests passing (100% pass rate)

### Test Examples

```python
def test_filter_deployment_issues_operational_tasks_only():
    """Only Operational Tasks from DevOps projects are deployments."""
    issues = [
        {"key": "DEVOPS-1", "fields": {
            "project": {"key": "DEVOPS"},
            "issuetype": {"name": "Operational Task"}
        }},
        {"key": "DEVOPS-2", "fields": {
            "project": {"key": "DEVOPS"},
            "issuetype": {"name": "Bug"}  # Not a deployment
        }},
        {"key": "DEV1-1", "fields": {
            "project": {"key": "DEV1"},
            "issuetype": {"name": "Operational Task"}  # Wrong project
        }}
    ]
    
    filtered = filter_deployment_issues(issues, ["DEVOPS"])
    
    assert len(filtered) == 1
    assert filtered[0]["key"] == "DEVOPS-1"
```

## Usage Examples

### Basic Filtering

```python
from data.project_filter import (
    filter_development_issues,
    filter_deployment_issues,
    filter_incident_issues
)
from configuration.settings import get_app_settings

# Load configuration
settings = get_app_settings()
devops_projects = settings.get("devops_projects", [])
all_issues = fetch_all_issues()  # From unified JQL query

# Filter for different metrics
dev_issues = filter_development_issues(all_issues, devops_projects)
deployments = filter_deployment_issues(all_issues, devops_projects)
incidents = filter_incident_issues(all_issues, devops_projects)

# Use filtered issues for calculations
burndown_data = calculate_burndown(dev_issues)
deployment_freq = calculate_deployment_frequency(deployments, field_mappings, devops_projects=devops_projects)
```

### DORA Metrics with Filtering

```python
from data.dora_calculator import (
    calculate_deployment_frequency,
    calculate_mean_time_to_recovery
)

# Deployment Frequency - filters to DevOps projects automatically
result = calculate_deployment_frequency(
    issues=all_issues,
    field_mappings=field_mappings,
    devops_projects=["DEVOPS"]
)
# Returns: metrics from Operational Tasks in DEVOPS project only

# MTTR - filters to production incidents in dev projects
result = calculate_mean_time_to_recovery(
    issues=all_issues,
    field_mappings=field_mappings,
    devops_projects=["DEVOPS"]
)
# Returns: metrics from Bugs with customfield_11309="PROD" in DEV1 project
```

### Adding New DevOps Projects

Simply update the configuration:

```json
{
  "devops_projects": ["DEVOPS", "OPS", "DEPLOY"]
}
```

All filtering logic automatically handles multiple DevOps projects.

## Performance Considerations

### Efficiency

- **Single API Call**: One Jira query fetches all needed issues
- **In-Memory Filtering**: Fast filtering operations on already-loaded data
- **No Redundant Queries**: Metrics share same dataset
- **Lazy Evaluation**: Filters applied only when metrics calculated

### Memory Usage

- Unified dataset in memory: ~1-5MB for typical 500-2000 issues
- Filtered subsets: References to original objects (minimal overhead)
- Trade-off: Slightly more memory for significantly better maintainability

## Migration Guide

### For Existing Deployments

1. **Update Configuration**:
   ```json
   {
     "jql_query": "project in (DEV_PROJECT, DEVOPS_PROJECT)",
     "devops_projects": ["DEVOPS_PROJECT"]
   }
   ```

2. **No Code Changes Required**: Filtering is automatic when devops_projects configured

3. **Backward Compatible**: If devops_projects is empty/missing, no filtering applied

### For New Deployments

1. Identify your project structure:
   - Which projects contain development work?
   - Which projects contain operational tasks/deployments?

2. Configure unified JQL query to fetch from all projects

3. Set devops_projects array to list DevOps project keys

4. Metrics will automatically filter appropriately

## Troubleshooting

### No Deployment Data

**Symptom**: Deployment Frequency shows "No data"

**Checks**:
1. Verify devops_projects is configured: `["DEVOPS"]`
2. Check JQL query includes DevOps project: `project in (DEV1, DEVOPS)`
3. Verify Operational Tasks exist in DevOps project
4. Check deployment_date field mapping

**Debug**:
```python
from data.project_filter import get_project_summary

summary = get_project_summary(all_issues, devops_projects)
print(summary)
# Shows: total_issues, development_issues, devops_issues, projects breakdown
```

### Wrong Issues in Metrics

**Symptom**: Burndown includes Operational Tasks or DORA missing deployments

**Root Cause**: Likely incorrect devops_projects configuration

**Fix**:
- Ensure devops_projects array exactly matches project keys in Jira
- Project keys are case-sensitive: "DEVOPS" ≠ "DEVOPS"

## Future Enhancements

### Potential Improvements

1. **Dynamic Project Discovery**: Auto-detect DevOps projects based on issue type distribution
2. **Project Type Validation**: Warning if devops_projects contain Stories/Tasks
3. **Performance Caching**: Cache filtered subsets if filtering becomes bottleneck
4. **Advanced Filtering**: Support project categories or custom project metadata
5. **Analytics Dashboard**: Visualize issue distribution across projects

### Extensibility

The filtering system is designed to be extended:

```python
def filter_custom_metric_issues(
    issues: List[Dict],
    devops_projects: List[str],
    custom_criteria: Dict
) -> List[Dict]:
    """Custom filtering for new metric types."""
    base_filtered = filter_development_issues(issues, devops_projects)
    # Add custom filtering logic
    return [i for i in base_filtered if meets_custom_criteria(i, custom_criteria)]
```

## References

- **Implementation**: `data/project_filter.py`
- **Tests**: `tests/unit/data/test_project_filter.py`
- **Configuration Guide**: `docs/Field_Mapping_Configuration_Guide.md`
- **DORA Calculator**: `data/dora_calculator.py`
- **Test Results**: 775 passing tests (31 new project filter tests)

## Summary

**Problem**: Multi-project Jira setup where development and deployments tracked separately

**Solution**: Unified JQL query with configuration-driven project filtering

**Benefits**:
- ✅ Single maintainable query
- ✅ Automatic metric-appropriate filtering  
- ✅ Backward compatible
- ✅ Extensible to new projects
- ✅ Comprehensive test coverage (31 tests)
- ✅ Clear configuration model

**Status**: ✅ Fully implemented and tested (775/775 tests passing)



