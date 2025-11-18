# Feature 012: Rule-Based Variable Mapping System

## Overview

**Status**: In Development  
**Branch**: `012-rule-based-variable-mapping`  
**Dependencies**: Feature 011 (Profile Workspace Switching)  
**Target Release**: v3.0

## Problem Statement

Current field mapping system has critical limitations:

1. **Hardcoded Field Access**: Many metrics directly access standard JIRA fields (`resolutiondate`, `status`, `issuetype`, `fixVersions`) without configuration
2. **No Conditional Logic**: Cannot filter by project, issue type, or environment
3. **Single Source Only**: Each variable can only map to one field (no fallbacks)
4. **No Changelog Support**: Cannot extract timestamps from status transitions or calculate time in states
5. **JIRA Diversity**: Different organizations configure JIRA differently - one-size-fits-all doesn't work

**Impact**: Metrics produce inaccurate results or fail entirely when JIRA structure doesn't match hardcoded assumptions.

## Goals

### Primary Goals

1. **No Hardcoded Fields**: All field access must be configurable through variable mappings
2. **Multiple Sources**: Support priority-ordered sources with fallback options
3. **Changelog Extraction**: Extract timestamps and durations from issue history
4. **Conditional Filters**: Filter by project, issue type, environment, custom JQL
5. **JIRA Flexibility**: Same metric works across different JIRA configurations

### Secondary Goals

6. **Backward Compatibility**: Existing simple mappings continue to work
7. **Metric-Driven UI**: Users configure variables needed for metrics, not raw field mappings
8. **Validation**: Test mappings on sample data before saving
9. **Performance**: Efficient extraction with caching

## Architecture

### Core Components

1. **Data Model** (`data/variable_mapper.py`)
   - Pydantic models for variable mappings
   - Source types: field_value, field_value_match, changelog_event, changelog_timestamp, fixversion, calculated
   - Filter model: project, issuetype, environment, custom JQL
   - Validation rules and type checking

2. **Variable Extractor** (`data/variable_extractor.py`)
   - Priority-ordered source evaluation
   - Changelog parsing and timestamp extraction
   - Duration calculations (time in statuses)
   - Caching for performance

3. **Metric Variable Definitions** (`configuration/metric_variables.py`)
   - Catalog of all variables required per metric
   - Data types, descriptions, required vs. optional
   - Default mappings for common JIRA patterns

4. **Migration Tool** (`data/mapping_migration.py`)
   - Convert legacy field mappings to variable mappings
   - Backward compatibility layer
   - Validation and testing

5. **UI Components** (`ui/variable_mapping_*.py`)
   - Metric configuration wizard
   - Variable mapping form
   - Sample data preview
   - Validation feedback

6. **Updated Metric Calculators**
   - `data/dora_calculator.py` - Use variable extractor instead of direct field access
   - `data/flow_calculator.py` - Use variable extractor instead of direct field access
   - Proper error handling for missing variables

### Data Flow

```
User selects metric to configure
    ↓
Wizard asks metric-specific questions
    ↓
UI translates answers to variable mappings
    ↓
Variable mappings saved to profile settings
    ↓
Metric calculator uses VariableExtractor
    ↓
Extractor tries sources in priority order
    ↓
Value extracted and cached
    ↓
Metric calculated with extracted values
```

### Storage Format

**Profile-level** (`profiles/{profile_id}/app_settings.json`):

```json
{
  "variable_mappings": {
    "deployment_timestamp": {
      "variable_type": "datetime",
      "metric_category": "dora",
      "description": "When deployment occurred",
      "required": true,
      "sources": [
        {
          "priority": 1,
          "source": {
            "type": "field_value",
            "field": "customfield_10100",
            "value_type": "datetime"
          }
        },
        {
          "priority": 2,
          "source": {
            "type": "changelog_timestamp",
            "field": "status",
            "condition": {"transition_to": "Deployed to Production"}
          }
        }
      ],
      "filters": {
        "project": ["DEVOPS"],
        "environment_field": "customfield_10200",
        "environment_value": "Production"
      }
    }
  }
}
```

## Source Types Implemented

### Phase 1 (MVP)

1. **field_value** - Direct field access
   - Example: `customfield_10100` → datetime value
   
2. **field_value_match** - Conditional field matching
   - Example: `status.name == "Deployed"` → boolean
   
3. **changelog_timestamp** - Extract transition timestamp
   - Example: When status changed to "Done" → datetime
   
4. **fixversion_releasedate** - Fix version date extraction
   - Example: `fixVersions[0].releaseDate` → datetime

### Phase 2 (Enhanced)

5. **changelog_event** - Detect if transition occurred
   - Example: Did status change to "Deployed"? → boolean
   
6. **calculated** - Derive from other sources
   - Example: Sum time in active statuses → duration

### Phase 3 (Advanced)

7. **linked_issue** - Data from related issues
8. **custom_jql_filter** - Advanced conditional filtering
9. **multi_value_aggregate** - Aggregate across multiple values

## Variables by Metric

### DORA Metrics

#### Deployment Frequency
- `deployment_event` (boolean) - Required
- `deployment_timestamp` (datetime) - Required
- `deployment_successful` (boolean) - Optional
- `deployment_environment` (category) - Optional

#### Lead Time for Changes
- `commit_timestamp` (datetime) - Required
- `deployment_timestamp` (datetime) - Required
- `is_code_change` (boolean) - Optional

#### Change Failure Rate
- `deployment_failed` (boolean) - Required
- `total_deployments` (count) - Required
- `failure_reason` (category) - Optional

#### MTTR
- `incident_detected_timestamp` (datetime) - Required
- `service_restored_timestamp` (datetime) - Required
- `is_production_incident` (boolean) - Required
- `incident_severity` (category) - Optional

### Flow Metrics

#### Flow Velocity
- `is_completed` (boolean) - Required
- `completion_timestamp` (datetime) - Required
- `is_flow_item` (boolean) - Optional

#### Flow Time
- `work_started_timestamp` (datetime) - Required
- `work_completed_timestamp` (datetime) - Required

#### Flow Efficiency
- `active_time` (duration) - Required
- `total_flow_time` (duration) - Required
- `active_statuses` (category[]) - Required
- `wait_statuses` (category[]) - Optional

#### Flow Load
- `is_in_progress` (boolean) - Required

#### Flow Distribution
- `work_type_category` (category) - Required
- `work_type_mapping` (config) - Required
- `completed_in_window` (boolean) - Required

#### Flow Predictability
- `planned_business_value` (number) - Required
- `actual_business_value` (number) - Required
- `was_planned` (boolean) - Required
- `was_completed` (boolean) - Required

## Implementation Plan

### Phase 1: Core Infrastructure (Current)

**Tasks:**

- [x] T001: Create comprehensive specifications
  - field_mapping_requirements.md
  - metric_variable_mapping_spec.md
  - mapping_architecture_proposal.md
  - field_mapping_analysis_summary.md

- [ ] T002: Create Pydantic data models
  - VariableMapping, SourceRule, MappingFilter
  - All source type models
  - Validation logic
  - Unit tests

- [ ] T003: Implement VariableExtractor
  - Core extraction engine
  - Support for field_value, field_value_match, changelog_timestamp, fixversion
  - Filter evaluation
  - Unit tests with sample JIRA data

- [ ] T004: Create metric variable definitions
  - configuration/metric_variables.py
  - Catalog of all required variables per metric
  - Default mapping suggestions

- [ ] T005: Build migration tool
  - Convert legacy field_mappings to variable_mappings
  - Backward compatibility layer
  - Validation and testing

### Phase 2: Metric Integration

**Tasks:**

- [ ] T006: Update DORA calculator
  - Replace hardcoded field access with variable extraction
  - Deployment Frequency
  - Lead Time for Changes
  - Change Failure Rate
  - MTTR

- [ ] T007: Update Flow calculator
  - Replace hardcoded field access with variable extraction
  - Flow Velocity
  - Flow Time
  - Flow Efficiency (changelog analysis)
  - Flow Load
  - Flow Distribution
  - Flow Predictability

- [ ] T008: Add changelog analysis support
  - Parse changelog from JIRA API
  - Calculate durations in statuses
  - Cache changelog data

- [ ] T009: Integration tests
  - Test with real JIRA data
  - Test fallback behavior
  - Test filter conditions

### Phase 3: User Interface

**Tasks:**

- [ ] T010: Create metric configuration wizard
  - Metric selection
  - Variable mapping forms
  - Sample data preview
  - Validation feedback

- [ ] T011: Build variable mapping UI components
  - Source type selectors
  - Filter configuration
  - Priority ordering
  - Add/remove sources

- [ ] T012: Add sample data preview
  - Show extracted values from sample issues
  - Validation results
  - Coverage statistics

- [ ] T013: Create migration UI
  - Detect legacy mappings
  - Show conversion preview
  - One-click migration

### Phase 4: Testing & Documentation

**Tasks:**

- [ ] T014: Comprehensive unit tests
  - All source types
  - All filter conditions
  - Edge cases and error handling

- [ ] T015: Integration tests
  - End-to-end metric calculation
  - Multiple source fallback
  - Changelog extraction

- [ ] T016: Performance testing
  - Extraction speed benchmarks
  - Caching effectiveness
  - Large dataset handling

- [ ] T017: User documentation
  - Configuration guide
  - Metric-specific examples
  - Troubleshooting guide

- [ ] T018: Developer documentation
  - Architecture overview
  - Adding new source types
  - Adding new variables

## Success Criteria

1. **No Hardcoded Fields**: All metric calculations use configurable variable mappings
2. **Test Coverage**: >90% coverage for variable extraction logic
3. **Performance**: Variable extraction <5ms per issue (with caching)
4. **Backward Compatibility**: All existing field mappings work without modification
5. **User Validation**: Metric configuration wizard tested with 3+ different JIRA instances
6. **Metric Accuracy**: All DORA and Flow metrics calculate correctly with variable mappings

## Testing Strategy

### Unit Tests
- Each source type extraction logic
- Filter evaluation
- Type validation
- Error handling

### Integration Tests
- End-to-end metric calculation
- Changelog parsing
- Multiple source fallback
- Real JIRA data samples

### User Acceptance Tests
- Configure Deployment Frequency on 3 different JIRA setups
- Configure Flow Efficiency with changelog analysis
- Migrate legacy mappings
- Validate with sample data preview

## Rollout Plan

### Phase 1: Internal Testing (Week 1-2)
- Implement core infrastructure
- Test with sample JIRA data
- Developer validation

### Phase 2: Beta Testing (Week 3-4)
- Deploy to test environment
- Invite beta testers with different JIRA setups
- Collect feedback and iterate

### Phase 3: Migration Support (Week 5)
- Build migration tool
- Test backward compatibility
- Create migration guide

### Phase 4: General Availability (Week 6)
- Deploy to production
- Monitor for issues
- Provide user support

## Risks & Mitigations

### Risk: Performance degradation with changelog extraction
**Mitigation**: Implement aggressive caching, lazy loading, optional changelog fetch

### Risk: Complexity overwhelms users
**Mitigation**: Metric-driven wizard hides complexity, provide templates

### Risk: Migration breaks existing setups
**Mitigation**: Backward compatibility layer, thorough testing, gradual rollout

### Risk: JIRA API rate limiting
**Mitigation**: Cache changelog data, batch requests, respect rate limits

## Open Questions

1. Should we support custom calculation logic (e.g., Python expressions)?
2. How to handle JIRA instances with incomplete changelog history?
3. Should we provide mapping templates for common JIRA setups?
4. How to version variable mapping schema for future changes?

## References

- PM-Metrics-Formulas.md - Mathematical definitions of all metrics
- docs/field_mapping_requirements.md - Problem analysis
- docs/metric_variable_mapping_spec.md - Complete variable catalog
- docs/mapping_architecture_proposal.md - Implementation design
- docs/field_mapping_analysis_summary.md - Executive summary

## Related Features

- Feature 007: DORA & Flow Metrics
- Feature 011: Profile Workspace Switching

## Change Log

- 2025-11-18: Feature created, comprehensive specifications completed
