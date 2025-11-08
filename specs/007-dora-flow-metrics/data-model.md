# Data Model: DORA and Flow Metrics Dashboard

**Feature**: `007-dora-flow-metrics`  
**Phase**: Phase 1 - Design & Contracts  
**Date**: 2025-10-27

## Overview

This document defines the data entities, relationships, and state transitions for the DORA and Flow Metrics feature. All entities align with the existing JSON-based persistence layer and Jira REST API integration.

---

## Core Entities

### 1. Field Mapping Configuration

**Purpose**: Maps Jira custom field IDs to internal metric calculation fields

**Storage**: `app_settings.json` under `dora_flow_config.field_mappings`

**Schema**:
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
        "required": true,
        "description": "When the code was deployed to production"
      },
      "customfield_10200": {
        "name": "Work Type",
        "type": "select",
        "required": true,
        "options": ["Feature", "Defect", "Risk", "Technical_Debt"],
        "description": "Category of work item for Flow Distribution"
      }
    }
  }
}
```

**Attributes**:
- `field_mappings.dora.<internal_field_name>`: String - Jira custom field ID (e.g., "customfield_10100")
- `field_mappings.flow.<internal_field_name>`: String - Jira custom field ID
- `field_metadata.<field_id>.name`: String - Human-readable field name from Jira
- `field_metadata.<field_id>.type`: Enum - Field type (datetime, number, text, select, checkbox)
- `field_metadata.<field_id>.required`: Boolean - Whether field is required for metric calculation
- `field_metadata.<field_id>.description`: String - Field purpose explanation

**Validation Rules**:
- Field IDs must start with "customfield_" or be standard Jira fields (created, resolutiondate)
- Type must match expected type for internal field (deployment_date → datetime)
- Required fields must be mapped before calculating dependent metrics

**Relationships**:
- One configuration per application instance
- Referenced by MetricCalculation entities
- Validated against JiraCustomField entities

---

### 2. Metric Value

**Purpose**: Represents a calculated DORA or Flow metric with performance tier and metadata

**Storage**: `metrics_cache.json` (temporary cache) and returned in callback responses

**Schema**:
```json
{
  "metric_name": "deployment_frequency",
  "metric_type": "dora",
  "value": 45.2,
  "unit": "deployments/month",
  "performance_tier": "High",
  "performance_tier_color": "yellow",
  "calculation_timestamp": "2025-01-31T10:00:00.000Z",
  "time_period_start": "2025-01-01T00:00:00.000Z",
  "time_period_end": "2025-01-31T23:59:59.999Z",
  "error_state": "success",
  "error_message": null,
  "excluded_issue_count": 2,
  "total_issue_count": 52,
  "details": {
    "benchmark_elite": 100,
    "benchmark_high": 30,
    "benchmark_medium": 5,
    "benchmark_low": 1,
    "trend_direction": "up",
    "trend_percentage": 12.5
  }
}
```

**Attributes**:
- `metric_name`: String (Required) - Unique identifier (deployment_frequency, lead_time_for_changes, etc.)
- `metric_type`: Enum (Required) - "dora" | "flow"
- `value`: Float (Nullable) - Calculated metric value (null if error)
- `unit`: String (Required) - Display unit (deployments/month, days, percentage, etc.)
- `performance_tier`: Enum (Nullable) - "Elite" | "High" | "Medium" | "Low" | null
- `performance_tier_color`: Enum - "green" | "yellow" | "orange" | "red"
- `calculation_timestamp`: DateTime (Required) - When metric was calculated (UTC ISO 8601)
- `time_period_start`: DateTime (Required) - Start of measurement period
- `time_period_end`: DateTime (Required) - End of measurement period
- `error_state`: Enum (Required) - "success" | "missing_mapping" | "no_data" | "calculation_error"
- `error_message`: String (Nullable) - User-friendly error explanation
- `excluded_issue_count`: Integer - Number of issues excluded due to missing data
- `total_issue_count`: Integer - Total issues considered for calculation
- `details`: Object - Additional metric-specific information

**Validation Rules**:
- If error_state != "success", value must be null
- performance_tier only valid for DORA metrics (null for Flow metrics except distribution)
- calculation_timestamp must be <= current time
- time_period_end must be >= time_period_start
- value must be >= 0 if not null

**State Transitions**:
```
[Calculation Requested] → [Validating Mappings] → [Fetching Data] → [Calculating] → [Success/Error]
                             ↓                        ↓                ↓
                          [Missing Mapping]      [No Data]        [Calculation Error]
```

**Relationships**:
- Depends on FieldMappingConfiguration
- Cached in MetricCacheEntry
- Displayed in UI via MetricCard component

---

### 3. Metric Cache Entry

**Purpose**: Caches calculated metrics with TTL to improve performance

**Storage**: `metrics_cache.json`

**Schema**:
```json
{
  "cache_version": "1.0",
  "entries": {
    "dora_2025-01-01_2025-01-31_a3f5c8d9": {
      "cache_key": "dora_2025-01-01_2025-01-31_a3f5c8d9",
      "metric_type": "dora",
      "time_period_start": "2025-01-01T00:00:00.000Z",
      "time_period_end": "2025-01-31T23:59:59.999Z",
      "field_mapping_hash": "a3f5c8d9",
      "metrics": {
        "deployment_frequency": { /* MetricValue object */ },
        "lead_time_for_changes": { /* MetricValue object */ },
        "change_failure_rate": { /* MetricValue object */ },
        "mean_time_to_recovery": { /* MetricValue object */ }
      },
      "calculated_at": "2025-01-31T10:00:00.000Z",
      "expires_at": "2025-01-31T11:00:00.000Z",
      "ttl_seconds": 3600
    }
  },
  "max_entries": 100,
  "eviction_policy": "LRU"
}
```

**Attributes**:
- `cache_key`: String (Required) - Unique identifier combining metric type, time period, and field mapping hash
- `metric_type`: Enum (Required) - "dora" | "flow"
- `time_period_start`: DateTime (Required) - Start of cached period
- `time_period_end`: DateTime (Required) - End of cached period
- `field_mapping_hash`: String (Required) - MD5 hash of field mappings used for calculation
- `metrics`: Object (Required) - Dictionary of MetricValue objects keyed by metric_name
- `calculated_at`: DateTime (Required) - When cache entry was created
- `expires_at`: DateTime (Required) - When cache entry becomes invalid
- `ttl_seconds`: Integer (Required) - Time-to-live in seconds (default: 3600)

**Validation Rules**:
- expires_at must be > calculated_at
- cache_key must be unique within entries
- field_mapping_hash must match current field mappings or entry is invalid

**Cache Invalidation Triggers**:
1. expires_at < current_time (TTL expired)
2. field_mapping_hash != current field mapping hash (configuration changed)
3. Manual refresh requested by user
4. Cache file version mismatch (CACHE_VERSION updated)
5. LRU eviction when max_entries exceeded

**Relationships**:
- Contains multiple MetricValue entities
- References FieldMappingConfiguration via hash
- Managed by metrics_cache.py module

---

### 4. Jira Custom Field

**Purpose**: Represents available custom fields from Jira instance for field mapping configuration

**Source**: Jira REST API `/rest/api/3/field`

**Runtime Schema** (not persisted):
```python
{
  "field_id": "customfield_10100",
  "field_name": "Deployment Date",
  "field_type": "datetime",
  "is_custom": True,
  "schema": {
    "type": "datetime",
    "system": "com.atlassian.jira.plugin.system.customfieldtypes:datetime"
  }
}
```

**Attributes**:
- `field_id`: String (Required) - Jira field ID (customfield_XXXXX or standard field)
- `field_name`: String (Required) - Display name from Jira
- `field_type`: Enum (Required) - Mapped from schema.type: "datetime" | "number" | "text" | "select" | "checkbox"
- `is_custom`: Boolean (Required) - True if field ID starts with "customfield_"
- `schema`: Object (Required) - Original Jira schema object

**Type Mapping**:

| Jira Schema Type | Internal Type | Example           |
| ---------------- | ------------- | ----------------- |
| datetime         | datetime      | customfield_10100 |
| number           | number        | customfield_10101 |
| string           | text          | customfield_10102 |
| option           | select        | customfield_10103 |
| array (option)   | multiselect   | customfield_10104 |
| checkbox         | checkbox      | customfield_10105 |

**Validation Rules**:
- field_type must be compatible with target internal field
- Incompatible mappings trigger validation errors in UI

**Relationships**:
- Fetched from Jira API on demand
- Used in FieldMappingConfiguration
- Cached in memory during configuration session

---

### 5. Time Period Selection

**Purpose**: Defines the time range for metric calculations

**Storage**: UI state (dash.dcc.Store) - not persisted

**Schema**:
```python
{
  "preset": "30d",  # "7d" | "30d" | "90d" | "custom"
  "start_date": "2025-01-01T00:00:00.000Z",
  "end_date": "2025-01-31T23:59:59.999Z",
  "display_label": "Last 30 days"
}
```

**Attributes**:
- `preset`: Enum (Required) - Preset selection or "custom"
- `start_date`: DateTime (Required) - Start of period (UTC ISO 8601)
- `end_date`: DateTime (Required) - End of period (UTC ISO 8601)
- `display_label`: String (Required) - Human-readable label for UI

**Validation Rules**:
- end_date must be >= start_date
- Date range must be <= 1 year (365 days)
- Dates must be in UTC timezone

**Relationships**:
- Used by MetricValue calculations
- Included in MetricCacheEntry cache key
- Selected via UI dropdown or date picker

---

### 6. Jira Issue (Extended for Metrics)

**Purpose**: Jira issue data with custom fields for metric calculations

**Source**: Jira REST API with custom field expansion

**Schema**:
```json
{
  "key": "PROJ-123",
  "fields": {
    "created": "2025-01-15T10:00:00.000Z",
    "resolutiondate": "2025-01-20T15:30:00.000Z",
    "status": {
      "name": "Done",
      "statusCategory": {"key": "done"}
    },
    "customfield_10100": "2025-01-18T14:00:00.000Z",  # Deployment Date
    "customfield_10101": "Production",                # Target Environment
    "customfield_10102": "2025-01-15T12:00:00.000Z",  # Code Commit Date
    "customfield_10200": "Feature"                     # Flow Item Type
  },
  "changelog": {
    "histories": [
      {
        "created": "2025-01-16T09:00:00.000Z",
        "items": [
          {
            "field": "status",
            "fromString": "To Do",
            "toString": "In Progress"
          }
        ]
      }
    ]
  }
}
```

**Extended Attributes** (beyond standard Jira fields):
- Custom fields mapped via FieldMappingConfiguration
- Changelog used for Flow Efficiency calculations (status transitions)

**Validation Rules**:
- Issues with missing required custom fields are excluded from calculations
- Excluded issue count tracked in MetricValue.excluded_issue_count

**Relationships**:
- Retrieved via data/jira_simple.py
- Cached in jira_cache.json (existing mechanism)
- Processed by data/dora_calculator.py and data/flow_calculator.py

---

## Entity Relationships

```
┌─────────────────────────────┐
│ Field Mapping Configuration │
│ (app_settings.json)         │
└──────────────┬──────────────┘
               │ uses
               ↓
┌──────────────────────────────┐         ┌─────────────────┐
│ Jira Custom Field            │←────────│ Jira REST API   │
│ (runtime, from API)          │ fetches │                 │
└──────────────┬───────────────┘         └─────────────────┘
               │ validates
               ↓
┌──────────────────────────────┐
│ Metric Calculation Request   │
│ (runtime)                    │
└──────────────┬───────────────┘
               │ produces
               ↓
┌──────────────────────────────┐
│ Metric Value                 │
│ (returned to UI)             │
└──────────────┬───────────────┘
               │ cached in
               ↓
┌──────────────────────────────┐
│ Metric Cache Entry           │
│ (metrics_cache.json)         │
└──────────────┬───────────────┘
               │ invalidated by
               ↓
┌──────────────────────────────┐
│ Time Period Selection        │
│ (UI state)                   │
└──────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Field Mapping Configuration Flow

```
User clicks "Configure Field Mappings"
    ↓
[UI] Display modal with empty form
    ↓
[Callback] Fetch available fields from Jira API
    ↓
[Data Layer] Call /rest/api/3/field
    ↓
[Data Layer] Parse and filter custom fields
    ↓
[Callback] Populate dropdown options
    ↓
User selects field mappings
    ↓
User clicks "Save Configuration"
    ↓
[Callback] Validate field type compatibility
    ↓
[Data Layer] Save to app_settings.json
    ↓
[Data Layer] Invalidate metric cache (field_mapping_hash changed)
    ↓
[UI] Display success message
    ↓
[Callback] Trigger metric recalculation
```

### 2. Metric Calculation Flow

```
User selects time period
    ↓
[Callback] Check metric cache
    ↓
Cache hit? → [Data Layer] Return cached metrics → [UI] Display
    ↓ (cache miss)
[Data Layer] Validate field mappings exist
    ↓
Missing mappings? → [UI] Display error with "Configure Mappings" button
    ↓ (mappings valid)
[Data Layer] Fetch Jira issues for time period
    ↓
[Data Layer] Filter issues with required fields
    ↓
[Data Layer] Calculate each metric
    ↓
[Data Layer] Determine performance tier
    ↓
[Data Layer] Create MetricValue objects
    ↓
[Data Layer] Cache results with TTL
    ↓
[Callback] Return metrics to UI
    ↓
[UI] Render metric cards with values and tiers
```

### 3. Cache Invalidation Flow

```
Trigger: Field mapping changed | TTL expired | Manual refresh
    ↓
[Data Layer] Calculate new field_mapping_hash
    ↓
[Data Layer] Compare with cached entries
    ↓
[Data Layer] Mark invalid entries (hash mismatch or TTL expired)
    ↓
[Data Layer] Remove invalid entries from cache
    ↓
[Data Layer] Save updated cache file
    ↓
Next metric calculation → Cache miss → Recalculate
```

---

## State Machines

### Metric Calculation State Machine

```
States:
- IDLE: No calculation in progress
- VALIDATING: Checking field mappings
- FETCHING: Retrieving Jira data
- CALCULATING: Computing metric values
- SUCCESS: Metrics calculated successfully
- ERROR: Calculation failed

Transitions:
IDLE → VALIDATING (user selects time period)
VALIDATING → ERROR (missing field mappings)
VALIDATING → FETCHING (mappings valid)
FETCHING → ERROR (Jira API error)
FETCHING → CALCULATING (data retrieved)
CALCULATING → ERROR (calculation exception)
CALCULATING → SUCCESS (all metrics calculated)
SUCCESS → IDLE (metrics displayed)
ERROR → IDLE (error displayed)
```

### Field Mapping Configuration State Machine

```
States:
- CLOSED: Modal not visible
- LOADING: Fetching available fields
- EDITING: User modifying mappings
- VALIDATING: Checking field type compatibility
- SAVING: Persisting configuration
- SAVED: Configuration saved successfully
- ERROR: Validation or save failed

Transitions:
CLOSED → LOADING (user clicks "Configure Field Mappings")
LOADING → ERROR (API fetch failed)
LOADING → EDITING (fields loaded)
EDITING → VALIDATING (user clicks "Save")
VALIDATING → ERROR (type mismatch detected)
VALIDATING → SAVING (validation passed)
SAVING → ERROR (file write failed)
SAVING → SAVED (configuration persisted)
SAVED → CLOSED (modal closes after 2 seconds)
ERROR → EDITING (user fixes errors)
```

---

## Data Persistence

### app_settings.json (Existing file - Extended)

**Location**: Repository root  
**Purpose**: Persistent application configuration including field mappings  
**Format**: JSON

**Extended Schema**:
```json
{
  "existing_settings": "...",
  "dora_flow_config": {
    "field_mappings": { /* FieldMappingConfiguration entity */ },
    "field_metadata": { /* JiraCustomField metadata */ },
    "last_updated": "2025-01-31T10:00:00.000Z"
  }
}
```

**Access Pattern**:
- Read: `data.persistence.load_app_settings()`
- Write: `data.persistence.save_app_settings()`

---

### metrics_cache.json (New file)

**Location**: Repository root  
**Purpose**: Temporary cache for calculated metrics  
**Format**: JSON  
**TTL**: 1 hour per entry  
**Max Size**: 100 entries (LRU eviction)

**Schema**: See MetricCacheEntry entity above

**Access Pattern**:
- Read: `data.metrics_cache.load_cached_metrics(cache_key)`
- Write: `data.metrics_cache.save_cached_metrics(cache_key, metrics)`
- Invalidate: `data.metrics_cache.invalidate_cache()`

---

### jira_cache.json (Existing - No changes)

**Location**: Repository root  
**Purpose**: Cache for Jira API responses  
**Format**: JSON  
**TTL**: 24 hours

**Usage**: Existing mechanism in `data/jira_simple.py` will be used for Jira issue data. No changes needed to cache structure.

---

## Validation Rules Summary

### Field Mapping Validation

1. **Required Mappings**:
   - DORA metrics require: deployment_date, deployed_to_production_date, code_commit_date
   - Flow metrics require: flow_item_type, work_started_date, work_completed_date

2. **Type Compatibility**:
   - DateTime internal fields → datetime Jira field type only
   - Number internal fields → number Jira field type only
   - Select internal fields → option or array Jira field type

3. **Field Existence**:
   - All mapped field IDs must exist in Jira instance
   - Validation done by checking against `/rest/api/3/field` response

### Metric Value Validation

1. **Value Ranges**:
   - Deployment Frequency: >= 0 deployments/period
   - Lead Time: >= 0 days
   - Change Failure Rate: 0-100%
   - MTTR: >= 0 hours
   - Flow Velocity: >= 0 items/period
   - Flow Time: >= 0 days
   - Flow Efficiency: 0-100%
   - Flow Load: >= 0 items
   - Flow Distribution: sum of percentages = 100%

2. **Time Period Validation**:
   - start_date < end_date
   - Date range <= 365 days
   - Dates in UTC timezone

3. **Error State Validation**:
   - If error_state != "success", value must be null
   - error_message required when error_state != "success"

---

## Migration Considerations

**No database migrations required** - Feature uses existing JSON file persistence.

**Configuration Migration**:
- Existing `app_settings.json` files will gain `dora_flow_config` key on first save
- Default value: empty field_mappings, prompt user to configure
- Backward compatible: Existing settings remain unchanged

**Cache File Creation**:
- `metrics_cache.json` created on first metric calculation
- No data loss if file doesn't exist (fresh calculation)

---

## Performance Considerations

### Data Volume Estimates

- **Field Mappings**: ~15 fields × 200 bytes = 3 KB
- **Metric Cache Entry**: ~9 metrics × 500 bytes = 4.5 KB per time period
- **Max Cache Size**: 100 entries × 4.5 KB = 450 KB
- **Jira Issues**: 5,000 issues × 2 KB = 10 MB (cached in jira_cache.json)

**Total Additional Storage**: < 500 KB for metrics cache

### Query Performance

- **Cache Hit**: < 200ms (read JSON file, deserialize, return)
- **Cache Miss**: 5-15 seconds (Jira API + calculation for 5,000 issues)
- **Field Mapping Load**: < 50ms (read app_settings.json)
- **Available Fields Fetch**: < 2 seconds (Jira API `/rest/api/3/field`)

### Optimization Strategies

1. **Lazy Loading**: Don't calculate metrics until user navigates to tab
2. **Incremental Display**: Show cached metrics immediately, recalculate in background
3. **Parallel Calculation**: Calculate DORA and Flow metrics concurrently
4. **Pandas Vectorization**: Use pandas for date arithmetic (10x faster than loops)

---

## Data Model Complete

All entities defined with:
- ✅ Complete schema definitions
- ✅ Validation rules specified
- ✅ Relationships documented
- ✅ State transitions defined
- ✅ Persistence strategy established
- ✅ Performance considerations addressed

Ready to proceed to contract generation.
