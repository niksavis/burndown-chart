# Feature 012: Rule-Based Variable Mapping System

## Overview

**Status**: ✅ **Phase 1 Complete** - Core infrastructure implemented, UI pending  
**Branch**: `012-rule-based-variable-mapping` (merged to 011)  
**Dependencies**: Feature 011 (Profile Workspace Switching)  
**Current Release**: v3.0-alpha (backend only)  
**Target Release**: v3.0-stable (with full UI)

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

### Phase 1: Core Infrastructure (✅ COMPLETE)

**Tasks:**

- [x] T001: Create comprehensive specifications
  - field_mapping_requirements.md
  - metric_variable_mapping_spec.md
  - mapping_architecture_proposal.md
  - field_mapping_analysis_summary.md

- [x] T002: Create Pydantic data models
  - ✅ data/variable_mapping/models.py (all source types)
  - ✅ VariableMapping, SourceRule, MappingFilter
  - ✅ Validation logic and unit tests

- [x] T003: Implement VariableExtractor
  - ✅ data/variable_mapping/extractor.py (584 lines)
  - ✅ All 6 source types: field_value, field_value_match, changelog_timestamp, changelog_event, fixversion, calculated
  - ✅ Filter evaluation
  - ✅ Unit tests with sample JIRA data

- [x] T004: Create metric variable definitions
  - ✅ configuration/metric_variables.py (1074 lines)
  - ✅ Complete DORA variables catalog
  - ✅ Complete Flow variables catalog
  - ✅ Default mapping configurations

- [x] T005: Build migration tool
  - ✅ data/mapping_migration.py
  - ✅ Backward compatibility layer (use_variable_extraction flag)
  - ⚠️  UI migration workflow pending (Phase 3)

**Status**: ✅ **100% Complete** - Core infrastructure production-ready

### Phase 2: Metric Integration (⚠️ PARTIAL)

**Tasks:**

- [ ] T006: Update DORA calculator
  - ❌ NOT STARTED - Still uses legacy field access
  - Replace hardcoded field access with variable extraction
  - Deployment Frequency, Lead Time, CFR, MTTR

- [x] T007: Update Flow calculator
  - ✅ COMPLETE - Uses VariableExtractor with use_variable_extraction flag
  - Flow Velocity, Flow Time, Flow Efficiency, Flow Load, Flow Distribution
  - Backward compatibility maintained

- [x] T008: Add changelog analysis support
  - ✅ COMPLETE - ChangelogEventSource and ChangelogTimestampSource implemented
  - Parse changelog from JIRA API
  - Calculate durations in statuses
  - ⚠️  Needs validation with real JIRA data

- [x] T009: Integration tests
  - ✅ COMPLETE - 1212/1212 tests passing
  - Tests with sample JIRA data
  - Fallback behavior tested
  - Filter conditions tested

**Status**: ⚠️ **60% Complete** - Flow metrics integrated, DORA pending

### Phase 3: User Interface (❌ NOT STARTED)

**Tasks:**

- [ ] T010: Create metric configuration wizard
  - ❌ NOT STARTED - UI wizard components not built
  - Metric selection
  - Variable mapping forms
  - Sample data preview
  - Validation feedback

- [ ] T011: Build variable mapping UI components
  - ❌ NOT STARTED - UI components not implemented
  - Source type selectors
  - Filter configuration
  - Pattern matching inputs
  - Changelog event selectors

- [ ] T012: Migration UI workflow
  - ❌ NOT STARTED - Migration UI not built
  - Convert existing field_mappings to variable_mappings
  - Show before/after comparison
  - Validate migration

- [ ] T013: Variable extraction preview
  - ❌ NOT STARTED - Preview feature not implemented
  - Show extracted values for sample issues
  - Debug failed extractions
  - Test configurations

**Status**: ❌ **0% Complete** - No UI components implemented

### Phase 4: Testing & Documentation (⚠️ PARTIAL)

**Tasks:**

- [x] T014: Comprehensive unit tests
  - ✅ COMPLETE - All source types tested
  - ✅ All filter conditions tested
  - ✅ Edge cases and error handling tested
  - 1212/1212 tests passing

- [x] T015: Integration tests
  - ✅ COMPLETE - End-to-end metric calculation tested
  - ✅ Multiple source fallback tested
  - ✅ Changelog extraction tested (with sample data)
  - ⚠️  Needs validation with real JIRA changelog data

- [ ] T016: Performance testing
  - ❌ NOT STARTED - Benchmarks not established
  - Extraction speed benchmarks
  - Caching effectiveness
  - Large dataset handling

- [ ] T017: User documentation
  - ❌ NOT STARTED - End-user docs not written
  - Configuration guide
  - Metric-specific examples
  - Troubleshooting guide

- [x] T018: Developer documentation
  - ✅ PARTIAL - Architecture specs exist
  - ✅ field_mapping_requirements.md
  - ✅ metric_variable_mapping_spec.md
  - ❌ Adding new source types guide missing
  - ❌ Adding new variables guide missing

**Status**: ⚠️ **50% Complete** - Tests complete, docs partial

---

## 📊 Implementation Status Summary

### ✅ What's Built and Working (Phase 1 Complete)

**Backend Infrastructure** - Production Ready:
- `data/variable_mapping/models.py` (317 lines)
  - All 6 source types: FieldValueSource, FieldValueMatchSource, ChangelogEventSource, ChangelogTimestampSource, FixVersionSource, CalculatedSource
  - VariableMapping and VariableMappingCollection models
  - Full validation logic with Pydantic
  
- `data/variable_mapping/extractor.py` (584 lines)
  - VariableExtractor class with priority-ordered source evaluation
  - Changelog parsing and duration calculations
  - Filter evaluation for conditional mappings
  - Caching support
  
- `configuration/metric_variables.py` (1074 lines)
  - Complete DORA variables catalog (deployment_event, deployment_timestamp, commit_timestamp, etc.)
  - Complete Flow variables catalog (work_completed_timestamp, work_type_category, etc.)
  - Default mapping configurations
  
- `data/mapping_migration.py`
  - Backward compatibility layer
  - use_variable_extraction flag (defaults True)
  
- **Flow Calculator Integration**
  - `data/flow_calculator.py` uses VariableExtractor
  - Backward compatible via flag
  - All 1212 tests passing

### ⚠️ What's Partially Done (Phase 2 - 60%)

**Metric Integration**:
- ✅ Flow metrics: Velocity, Time, Efficiency, Load, Distribution
- ✅ Changelog analysis infrastructure
- ❌ DORA metrics: Still use legacy field access
- ⚠️ Changelog validation: Tested with sample data, needs real JIRA validation

### ❌ What's NOT Built (Phases 3-4 - UI Pending)

**User Interface** (0% complete):
- ❌ Metric configuration wizard
- ❌ Variable mapping UI components
- ❌ Migration UI workflow
- ❌ Sample data preview
- ❌ Field selector dropdowns
- ❌ Filter condition builder

**Documentation** (Partial):
- ✅ Architecture specs (field_mapping_requirements.md, etc.)
- ❌ End-user configuration guide
- ❌ Metric-specific examples
- ❌ Troubleshooting guide

**Performance** (Not measured):
- ❌ Extraction speed benchmarks
- ❌ Caching effectiveness metrics
- ❌ Large dataset handling tests

### 🎯 Recommendation

**Keep this spec as a roadmap for Phases 2-4**. The backend infrastructure (Phase 1) is production-ready with 1212 passing tests. The remaining work is primarily UI/UX for end-user configuration and DORA metric integration.

---

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

## Troubleshooting

### Missing or Empty Field Mappings After Auto-Configure

**Symptom**: After running auto-configure, some DORA/Flow fields are empty or not detected (e.g., `change_failure`, `affected_environment`, `target_environment`).

**Root Cause**: Not all JIRA instances have these custom fields. Different organizations configure JIRA differently:
- **Apache JIRA**: Open-source project JIRA typically lacks deployment/environment tracking fields
- **Corporate JIRA**: Enterprise instances usually have comprehensive custom field setups
- **Sparse Data**: Fields may exist but have too few values to meet detection thresholds (40% for sprint field)

**Expected Behavior**: This is NORMAL for JIRA instances without these custom fields. The application will:
1. Show empty dropdowns in Configure JIRA Mappings modal
2. Fall back to changelog-based extraction for missing field mappings
3. Skip metrics that require unavailable data (e.g., deployment metrics without deployment fields)

**How to Verify Your JIRA Has These Fields**:

1. **Via JIRA Web UI**:
   - Go to any issue in your project
   - Click "Configure Fields" or view Custom Fields section
   - Look for fields like "Deployment Date", "Change Failure", "Affected Environment"

2. **Via JIRA API** (requires authentication):
   ```powershell
   # Get all custom fields
   $headers = @{
       "Authorization" = "Bearer YOUR_TOKEN"
       "Content-Type" = "application/json"
   }
   Invoke-RestMethod -Uri "https://your-jira.com/rest/api/2/field" -Headers $headers | 
       Where-Object { $_.custom -eq $true } | 
       Select-Object id, name, schema
   ```

3. **Via App Logs**:
   - Open browser DevTools → Console tab
   - Look for field detection results in JIRA metadata store
   - Check `jira_cache.json` for available custom fields

**Solutions**:

1. **For Missing DORA Fields** (deployment_date, deployment_successful, change_failure):
   - If your team doesn't track deployments in JIRA: Use alternative DORA data sources
   - If fields exist but not detected: Manually configure field IDs in Configure JIRA Mappings modal
   - If fields don't exist: Create custom fields in JIRA or skip DORA metrics

2. **For Missing Environment Fields** (affected_environment, target_environment):
   - If environments not tracked in JIRA: Configure production environment values manually
   - If fields exist but not detected: Lower detection threshold or configure manually
   - If fields don't exist: Create custom fields or use JQL filters instead

3. **For Low Detection Confidence** (field exists but threshold not met):
   - Current threshold: 40% of issues must have the field populated
   - Workaround: Manually configure field ID even if auto-detect fails
   - Future enhancement: Make thresholds configurable per field type

**Manual Field Configuration**:

If auto-configure doesn't detect your fields but you know they exist:
1. Open "Configure JIRA Mappings" modal
2. Click "Fields" tab
3. Manually enter the custom field ID (e.g., `customfield_10042`)
4. Click Save
5. Test with "Calculate Metrics" to verify data extraction works

### Java Class Names in Environment Dropdown

**Symptom**: Environment dropdown shows Java class names like `com.atlassian.jira.plugin.devstatus.rest.SummaryItemBean`.

**Root Cause**: JIRA's Development panel custom field contains Java class metadata.

**Fix**: ✅ Fixed in v3.0-alpha - Java class patterns are now filtered from environment field detection.

**If Still Occurring**:
1. Clear browser cache and refresh
2. Re-run auto-configure
3. Check app version is ≥ v3.0-alpha
4. Report bug if issue persists

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

- 2025-11-26: Added troubleshooting section for sparse JIRA instances and missing field mappings
- 2025-11-26: Fixed field mapping save/load bug (render_tab_content state initialization)
- 2025-11-26: Fixed Java class name filter for environment field detection
- 2025-11-18: Feature created, comprehensive specifications completed
