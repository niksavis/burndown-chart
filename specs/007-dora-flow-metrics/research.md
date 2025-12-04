# Research: DORA and Flow Metrics Dashboard

**Feature**: `007-dora-flow-metrics`  
**Phase**: Phase 0 - Outline & Research  
**Date**: 2025-10-27

## Research Tasks

Based on the Technical Context analysis, the following areas require research to resolve unknowns and establish best practices for implementation:

### 1. DORA Metrics Calculation Algorithms

**Task**: Research industry-standard algorithms and formulas for calculating DORA metrics from Jira data  
**Status**: ✅ RESOLVED

**Decision**: Use DORA_Flow_Jira_Mapping.md as authoritative source for metric definitions

**Rationale**: 
- The repository already contains comprehensive DORA metric documentation in `DORA_Flow_Jira_Mapping.md`
- Document provides exact calculation formulas aligned with DORA research standards
- Includes performance tier benchmarks (Elite/High/Medium/Low) from industry research
- Provides specific Jira REST API endpoints and field mappings

**Key Findings**:
- **Deployment Frequency**: `Count(Deployments to Production) / Time Period`
- **Lead Time for Changes**: `Median(Deployed_to_Production_Date - Code_Commit_Date)`
- **Change Failure Rate**: `Count(Failed Deployments) / Count(Total Deployments) × 100`
- **MTTR**: `Median(Incident_Resolved_At - Incident_Detected_At)`

**Performance Benchmarks** (from DORA research):
- Elite: Lead Time < 1 hour, MTTR < 1 hour, CFR < 15%, DF = on-demand
- High: Lead Time < 1 week, MTTR < 1 day, CFR < 30%, DF = weekly
- Medium: Lead Time < 1 month, MTTR < 1 week, CFR < 46%, DF = monthly
- Low: Lead Time > 1 month, MTTR > 1 week, CFR > 46%, DF = 6+ months

**Alternatives Considered**: 
- Custom metric definitions: Rejected - Industry standard DORA definitions ensure comparability and credibility
- Simplified calculations: Rejected - Proper benchmarking requires full DORA methodology

---

### 2. Flow Metrics Calculation Algorithms

**Task**: Research Flow metrics calculation methods and categorization strategies  
**Status**: ✅ RESOLVED

**Decision**: Implement all 5 Flow metrics per DORA_Flow_Jira_Mapping.md specification

**Rationale**:
- Flow metrics complement DORA metrics by measuring process efficiency vs delivery speed
- Existing documentation provides complete definitions and Jira field mappings
- Flow Distribution requires work categorization into 4 types (Features, Defects, Risks, Debt)

**Key Findings**:
- **Flow Velocity**: `Count(Completed Work Items) / Time Period`, segmented by type
- **Flow Time**: `Median(Work_Completed_Date - Work_Started_Date)`
- **Flow Efficiency**: `(Active Working Time / Total Flow Time) × 100`
- **Flow Load**: `Count(Issues with active status)` at point in time
- **Flow Distribution**: Percentage breakdown by work type

**Recommended Distribution Targets**:
- Features: 40-50% (new business value)
- Defects: 15-25% (quality maintenance)
- Risks: 10-15% (security, compliance)
- Technical Debt: 20-25% (sustainability)

**Alternatives Considered**:
- Simpler 3-type categorization: Rejected - Industry standard uses 4 types for balanced portfolio view
- Story points weighting: Deferred to future enhancement - Count-based metrics are simpler and sufficient for initial implementation

---

### 3. Jira REST API Custom Field Discovery

**Task**: Research Jira REST API endpoints for discovering and querying custom fields  
**Status**: ✅ RESOLVED

**Decision**: Use `/rest/api/3/field` endpoint to fetch all available fields, filter for custom fields (IDs starting with "customfield_")

**Rationale**:
- Jira organizations use custom fields extensively for workflow customization
- Field IDs vary by instance (e.g., "customfield_10002" for story points in one org, different in another)
- Must provide user-friendly dropdown with field names for configuration UI
- Need field type validation (DateTime vs Number vs Text vs Select)

**Key API Endpoints**:
```
GET /rest/api/3/field
Returns: Array of all fields with schema information
Response includes: id, name, schema.type, custom (boolean)

GET /rest/api/3/issues/{key}?fields=customfield_XXXXX
Returns: Issue data with specific custom field value
```

**Implementation Pattern**:
1. Fetch all fields on configuration modal open
2. Filter for custom fields (id starts with "customfield_")
3. Cache field list in memory (changes infrequently)
4. Validate field type compatibility when mapping (DateTime → DateTime, Number → Number, etc.)

**Existing Integration**: Current codebase already has Jira REST API integration in `data/jira_simple.py` with authentication, caching, and error handling. Will extend this module.

**Alternatives Considered**:
- Manual field ID entry: Rejected - Poor UX, error-prone
- Automatic field detection: Rejected (out of scope per spec) - Requires ML/heuristics to guess field purpose
- Static field mapping per Jira instance type: Rejected - Organizations customize fields extensively

---

### 4. Field Mapping Configuration Schema

**Task**: Design configuration schema for storing Jira field mappings in app_settings.json  
**Status**: ✅ RESOLVED

**Decision**: Store field mappings in nested structure under `dora_flow_config` key in app_settings.json

**Schema Structure**:
```json
{
  "dora_flow_config": {
    "field_mappings": {
      "dora": {
        "deployment_date": "customfield_10100",
        "target_environment": "customfield_10101",
        "code_commit_date": "customfield_10102",
        "deployed_to_production_date": "customfield_10103",
        "incident_detected_at": "customfield_10104",
        "incident_resolved_at": "customfield_10105",
        "deployment_successful": "customfield_10106",
        "production_impact": "customfield_10107"
      },
      "flow": {
        "flow_item_type": "customfield_10200",
        "work_started_date": "customfield_10201",
        "work_completed_date": "customfield_10202",
        "status_entry_timestamp": "customfield_10203",
        "active_work_hours": "customfield_10204",
        "flow_time_days": "customfield_10205"
      }
    },
    "field_metadata": {
      "customfield_10100": {
        "name": "Deployment Date",
        "type": "datetime",
        "required": true
      },
      "customfield_10200": {
        "name": "Work Type",
        "type": "select",
        "required": true
      }
    }
  }
}
```

**Rationale**:
- Nested structure separates DORA vs Flow mappings for clarity
- Field metadata enables validation and user-friendly display
- Required flag allows warning users about incomplete mappings
- Integrates with existing settings persistence (data/persistence.py)

**Alternatives Considered**:
- Separate JSON file: Rejected - Adds complexity, existing pattern uses app_settings.json
- Database storage: Rejected - Out of scope, current architecture uses JSON files
- Environment variables: Rejected - Too many mappings (15+ fields), not user-friendly

---

### 5. Metrics Caching Strategy

**Task**: Research optimal caching approach for calculated metrics with TTL and invalidation  
**Status**: ✅ RESOLVED

**Decision**: Implement simple JSON file cache with cache key based on (query parameters + field mappings + time period)

**Cache Key Structure**:
```python
cache_key = f"{metric_type}_{time_period_start}_{time_period_end}_{field_mapping_hash}"
# Example: "dora_2025-01-01_2025-01-31_a3f5c8d9"
```

**Cache File Structure** (metrics_cache.json):
```json
{
  "cache_version": "1.0",
  "entries": {
    "dora_2025-01-01_2025-01-31_a3f5c8d9": {
      "metrics": {
        "deployment_frequency": {
          "value": 45,
          "unit": "deployments/month",
          "performance_tier": "High"
        },
        "lead_time_for_changes": {
          "value": 3.5,
          "unit": "days",
          "performance_tier": "High"
        }
      },
      "calculated_at": "2025-01-31T10:00:00Z",
      "expires_at": "2025-01-31T11:00:00Z",
      "ttl_seconds": 3600
    }
  }
}
```

**TTL Strategy**:
- Default TTL: 1 hour (3600 seconds) for metric calculations
- Field mapping changes: Invalidate all cache entries
- Manual refresh: User can trigger immediate recalculation
- Cache size limit: 100 entries max, LRU eviction

**Rationale**:
- Aligns with existing caching pattern (jira_cache.json uses similar structure)
- Simple file-based approach consistent with architecture
- Hash-based cache keys ensure correct invalidation
- TTL prevents stale data while allowing fast repeated queries

**Existing Pattern**: Current codebase uses `jira_cache.json` with version tracking and expiration. Will create parallel `metrics_cache.json` with similar pattern.

**Alternatives Considered**:
- In-memory only cache: Rejected - Lost on server restart, no persistence
- Redis/Memcached: Rejected - Out of scope, adds infrastructure dependency
- No caching: Rejected - Performance requirement (metric calculation for 5k issues in 15s) necessitates caching

---

### 6. Performance Optimization for Large Datasets

**Task**: Research strategies for handling 5,000+ Jira issues efficiently  
**Status**: ✅ RESOLVED

**Decision**: Multi-layered optimization approach

**Optimization Strategies**:

1. **Jira Query Optimization**:
   - Use JQL date filters to limit result set: `created >= -90d`
   - Request only needed fields: `?fields=customfield_X,customfield_Y,created,resolutiondate`
   - Leverage existing pagination in `jira_query_manager.py` (100 issues per request)

2. **Client-Side Processing**:
   - Use pandas DataFrames for efficient aggregation and filtering
   - Pre-filter issues by relevant date ranges before calculations
   - Vectorized operations for time calculations (pandas.to_datetime, timedelta operations)

3. **Lazy Loading**:
   - Don't calculate all metrics upfront
   - Calculate metrics when user switches to DORA/Flow tab
   - Show loading indicators during calculation (dash.dependencies.Output with loading state)

4. **Progressive Enhancement**:
   - Load metric cards first with basic values
   - Load trend charts on-demand when user clicks "Show Trend"
   - Stream results for very large datasets (show partial results while calculating)

5. **Caching** (see Research Task 5):
   - Cache calculated metrics with 1-hour TTL
   - Cache Jira raw data with 24-hour TTL (existing jira_cache.json)

**Performance Targets Validation**:
- 5,000 issues × ~2ms processing per issue = ~10 seconds processing time
- Plus Jira API time (cached): ~200ms
- Plus Chart rendering: ~500ms
- **Total**: ~11 seconds ✅ Under 15-second requirement

**Existing Infrastructure**: Current codebase already handles 1,000+ issues efficiently via `jira_query_manager.py` pagination and caching. Will extend this pattern.

**Alternatives Considered**:
- Server-side aggregation in Jira: Not available via REST API
- Background job processing: Rejected - Adds complexity, users expect near-instant results
- Sampling large datasets: Rejected - Users expect accurate metrics, not estimates

---

### 7. Mobile-First Responsive Design for Metrics Dashboard

**Task**: Research best practices for displaying complex metrics on mobile devices  
**Status**: ✅ RESOLVED

**Decision**: Progressive disclosure with collapsible sections and card-based layout

**Design Patterns**:

1. **Metric Card Design**:
   - Large, tappable cards (minimum 44px touch targets per constitution)
   - Primary metric value prominently displayed (36px font)
   - Performance tier indicator as colored badge (green/yellow/orange/red)
   - "Show Details" expansion for trend charts
   - Tooltip on long-press (mobile) or hover (desktop)

2. **Layout Strategy**:
   ```
   Mobile (< 768px):  1 column, full-width cards, collapsible sections
   Tablet (768-1024): 2 columns, side-by-side cards
   Desktop (> 1024):  3-4 columns, dashboard grid layout
   ```

3. **Navigation**:
   - Tab-based navigation (DORA Metrics | Flow Metrics)
   - Sticky header with time period selector
   - Floating action button for field mapping configuration

4. **Data Visualization**:
   - Simplified charts on mobile (fewer data points, larger markers)
   - Horizontal scroll for wide charts
   - Plotly responsive config: `{"responsive": true, "displayModeBar": "mobile"}`

**Implementation Using Existing UI Components**:
- Dash Bootstrap Components (dbc.Row, dbc.Col) with responsive breakpoints
- Existing mobile navigation patterns from `ui/mobile_navigation.py`
- CSS classes from `assets/custom.css` for consistent styling

**Existing Pattern**: Current dashboard already implements mobile-first design. Will follow same pattern with `dbc.Container(fluid=True)` and responsive column widths.

**Alternatives Considered**:
- Separate mobile/desktop pages: Rejected - Increases maintenance, breaks PWA model
- Table-based layout: Rejected - Cards more readable on mobile
- Fixed desktop-only layout: Rejected - Violates constitution's mobile-first principle

---

### 8. Time Period Selection and Date Range Handling

**Task**: Research date range selection patterns and UTC timezone handling  
**Status**: ✅ RESOLVED

**Decision**: Implement dropdown with preset ranges + custom date picker, all calculations in UTC

**Time Period Options**:
- Last 7 days
- Last 30 days
- Last 90 days
- Custom range (date picker)

**Date Handling Strategy**:
1. **Storage**: All dates stored in UTC ISO 8601 format (`2025-01-31T10:00:00.000Z`)
2. **Display**: Convert to user's local timezone in UI (browser handles this automatically)
3. **Calculations**: All date arithmetic in UTC using Python datetime.timezone.utc
4. **Jira API**: Jira returns dates in UTC, no conversion needed

**Implementation Components**:
```python
# Use Dash DatePickerRange for custom ranges
dcc.DatePickerRange(
    id='custom-date-range',
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now(),
    display_format='YYYY-MM-DD'
)

# Dropdown for preset ranges
dbc.Select(
    id='time-period-selector',
    options=[
        {'label': 'Last 7 days', 'value': '7d'},
        {'label': 'Last 30 days', 'value': '30d'},
        {'label': 'Last 90 days', 'value': '90d'},
        {'label': 'Custom range', 'value': 'custom'}
    ]
)
```

**Existing Pattern**: Current dashboard uses date calculations in `data/processing.py` with datetime objects. Will extend with timezone-aware datetime using `datetime.timezone.utc`.

**Alternatives Considered**:
- Relative date strings only: Rejected - Users need custom ranges for reporting
- Local timezone calculations: Rejected - Causes inconsistencies across users in different timezones
- Week-based periods: Rejected - Industry standard uses day-based periods

---

### 9. Error Handling for Missing Jira Data

**Task**: Research graceful degradation strategies for incomplete data  
**Status**: ✅ RESOLVED

**Decision**: Implement explicit error states with actionable guidance for each failure scenario

**Error Scenarios and Handling**:

1. **Missing Required Field Mappings**:
   ```
   UI Display: "⚠️ Field Mapping Required"
   Message: "Deployment Frequency cannot be calculated. Please configure 
            the 'Deployment Date' field mapping."
   Action: [Configure Mappings] button
   ```

2. **No Data in Time Period**:
   ```
   UI Display: "📊 No Data Available"
   Message: "No deployments found in the last 30 days. Try selecting 
            a different time period."
   Action: [Change Time Period] dropdown
   ```

3. **Incomplete Jira Issue Data**:
   ```
   UI Display: Metric calculated with warning badge
   Message: "Calculated from 45 of 50 issues. 5 issues excluded due to 
            missing 'Resolution Date' field."
   Action: [View Details] expansion with list of excluded issues
   ```

4. **Jira API Errors**:
   ```
   UI Display: "❌ Connection Error"
   Message: "Unable to fetch data from Jira. Please check your connection 
            and API token."
   Action: [Retry] button, [Check Configuration] link
   ```

5. **Field Type Mismatch**:
   ```
   UI Display: "⚠️ Invalid Field Type"
   Message: "'Deployment Date' must be a DateTime field. Currently mapped 
            to Text field 'customfield_10100'."
   Action: [Fix Mapping] button
   ```

**Implementation Pattern**:
```python
# In data layer
def calculate_deployment_frequency(issues, field_mappings, time_period):
    """Returns tuple: (value, error_state, excluded_count, message)"""
    try:
        if not field_mappings.get('deployment_date'):
            return (None, 'missing_mapping', 0, 
                   "Configure 'Deployment Date' field mapping")
        
        # Calculate metric
        valid_issues = [i for i in issues if has_required_fields(i)]
        excluded_count = len(issues) - len(valid_issues)
        
        if not valid_issues:
            return (None, 'no_data', 0, 
                   f"No deployments found in {time_period}")
        
        value = len(valid_issues) / time_period.days
        message = f"Calculated from {len(valid_issues)} deployments"
        
        if excluded_count > 0:
            message += f". {excluded_count} issues excluded."
        
        return (value, 'success', excluded_count, message)
        
    except Exception as e:
        logger.error(f"Error calculating deployment frequency: {e}")
        return (None, 'calculation_error', 0, str(e))
```

**Existing Pattern**: Current codebase uses error states in `ui/error_states.py` and `ui/error_utils.py`. Will extend with metric-specific error messages.

**Alternatives Considered**:
- Silent failures: Rejected - Users need to know why metrics are missing
- Generic error messages: Rejected - Not actionable, users can't fix issues
- Throwing exceptions: Rejected - Breaks dashboard, better to show partial results

---

### 10. Testing Strategy for Metrics Calculations

**Task**: Research testing patterns for complex metric calculations with time-series data  
**Status**: ✅ RESOLVED

**Decision**: Comprehensive unit testing with fixture-based test data + integration tests with mocked Jira API

**Testing Layers**:

1. **Unit Tests** (data layer):
   ```python
   # tests/unit/data/test_dora_calculator.py
   def test_deployment_frequency_calculation():
       """Test DF calculation with known input/output"""
       issues = [
           {"key": "DEP-1", "fields": {"customfield_10100": "2025-01-15"}},
           {"key": "DEP-2", "fields": {"customfield_10100": "2025-01-20"}},
           {"key": "DEP-3", "fields": {"customfield_10100": "2025-01-25"}},
       ]
       field_mappings = {"deployment_date": "customfield_10100"}
       time_period = (datetime(2025, 1, 1), datetime(2025, 1, 31))
       
       result = calculate_deployment_frequency(issues, field_mappings, time_period)
       
       assert result.value == 3 / 31  # 3 deployments in 31 days
       assert result.error_state == 'success'
   ```

2. **Parametrized Tests** for edge cases:
   ```python
   @pytest.mark.parametrize("issues,expected_value,expected_error", [
       ([], None, 'no_data'),  # No issues
       ([{"key": "DEP-1", "fields": {}}], None, 'missing_field'),  # Missing field
       ([{"key": "DEP-1", "fields": {"customfield_10100": "invalid"}}], 
        None, 'invalid_date'),  # Invalid date format
   ])
   def test_deployment_frequency_edge_cases(issues, expected_value, expected_error):
       result = calculate_deployment_frequency(issues, mappings, period)
       assert result.value == expected_value
       assert result.error_state == expected_error
   ```

3. **Integration Tests** (workflow):
   ```python
   # tests/integration/test_dora_flow_workflow.py
   def test_complete_dora_metrics_workflow(temp_settings_file, mock_jira_api):
       """Test end-to-end: field mapping → data fetch → calculation → display"""
       # Setup field mappings
       save_field_mappings({"deployment_date": "customfield_10100"})
       
       # Mock Jira API response
       mock_jira_api.return_value = sample_jira_issues
       
       # Calculate metrics
       metrics = calculate_all_dora_metrics(time_period="30d")
       
       # Verify results
       assert metrics['deployment_frequency'].value > 0
       assert metrics['lead_time'].performance_tier in ['Elite', 'High', 'Medium', 'Low']
   ```

4. **Performance Tests**:
   ```python
   def test_metric_calculation_performance_5000_issues():
       """Verify calculation completes within 15 seconds for 5000 issues"""
       large_dataset = generate_test_issues(count=5000)
       
       start_time = time.time()
       metrics = calculate_all_dora_metrics(large_dataset, field_mappings)
       elapsed = time.time() - start_time
       
       assert elapsed < 15.0  # Constitution requirement
   ```

5. **Test Isolation** (CRITICAL - Constitution Principle II):
   ```python
   @pytest.fixture
   def temp_metrics_cache():
       """Isolated temporary cache file for testing"""
       with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
           temp_file = f.name
       yield temp_file
       if os.path.exists(temp_file):
           os.unlink(temp_file)
   
   def test_metrics_caching(temp_metrics_cache):
       """Test caching without polluting project directory"""
       with patch("data.metrics_cache.CACHE_FILE", temp_metrics_cache):
           # Test caching logic
           pass
   ```

**Test Fixtures**:
- Sample Jira issues with all required fields
- Sample issues with missing fields (edge cases)
- Large dataset generator (5000+ issues for performance testing)
- Temporary file fixtures for settings and cache

**Existing Pattern**: Current codebase uses pytest with fixtures in `tests/conftest.py`. Uses Playwright for integration tests. Will extend with DORA/Flow-specific fixtures.

**Alternatives Considered**:
- Manual testing only: Rejected - Too complex, regression risk
- Integration tests only: Rejected - Slow, hard to debug
- Mocking Jira API in unit tests: Rejected for unit tests (tests calculation logic, not API) but used in integration tests

---

## Research Summary

All research tasks have been completed successfully. Key decisions:

1. ✅ **Metrics Algorithms**: Use DORA_Flow_Jira_Mapping.md as authoritative source
2. ✅ **Jira API Integration**: Extend existing `data/jira_simple.py` with custom field queries
3. ✅ **Field Mapping Schema**: Nested JSON structure in app_settings.json
4. ✅ **Caching Strategy**: Simple JSON file cache with TTL and hash-based invalidation
5. ✅ **Performance**: Multi-layered optimization (JQL filters, pandas, lazy loading, caching)
6. ✅ **Responsive Design**: Progressive disclosure with card-based layout
7. ✅ **Date Handling**: UTC timezone for calculations, ISO 8601 storage
8. ✅ **Error Handling**: Explicit error states with actionable guidance
9. ✅ **Testing**: Comprehensive unit + integration tests with isolated fixtures

**No blocking unknowns remain.** Ready to proceed to Phase 1: Design & Contracts.

---

## Technology Stack Finalized

**Core Technologies**:
- Python 3.13
- Dash 3.1.1 (UI framework)
- Plotly 6.0.1 (charts)
- Pandas 2.2.3 (data processing)
- Requests 2.32.3 (Jira API)

**Testing Technologies**:
- Pytest 8.3.5
- Pytest-cov 6.1.1 (coverage)
- Playwright 1.55.0 (integration tests)

**No new dependencies required** - all technologies already in requirements.txt.
