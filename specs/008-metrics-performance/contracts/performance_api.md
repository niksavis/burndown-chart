# API Contracts: Performance Utilities Module

**Module**: `data/performance_utils.py`  
**Purpose**: Performance timing, profiling, and optimization utilities

## Public API

### Decorator: `log_performance`

**Purpose**: Decorator to log execution time of functions

**Signature**:
```python
def log_performance(operation_name: str) -> Callable
```

**Parameters**:
- `operation_name` (str): Human-readable name for the operation (appears in logs)

**Returns**: Decorator function

**Side Effects**:
- Logs operation start (INFO level)
- Logs operation completion with duration (INFO level)
- Logs operation failure with duration (ERROR level)

**Example**:
```python
from data.performance_utils import log_performance

@log_performance("DORA metrics calculation")
def calculate_dora_metrics(issues, field_mappings, time_period):
    # ... calculation logic ...
    return metrics

# Usage logs:
# INFO: Starting DORA metrics calculation
# INFO: DORA metrics calculation completed in 1.234s
```

---

### Class: `CalculationContext`

**Purpose**: Share intermediate calculation results to avoid redundant processing

**Methods**:

#### `__init__(issues: List[Dict], field_index: 'FieldMappingIndex')`

Initialize context with issues and field index

**Parameters**:
- `issues` (List[Dict]): JIRA issues to process
- `field_index` (FieldMappingIndex): Pre-built field mapping index

#### `filter_issues(filter_func: Callable, cache_key: str) -> List[Dict]`

Filter issues with caching to avoid re-filtering

**Parameters**:
- `filter_func` (Callable): Predicate function `(issue) -> bool`
- `cache_key` (str): Unique key for this filter operation

**Returns**: Filtered issues (List[Dict])

**Caching**: Results cached in-memory for duration of context object

**Example**:
```python
from data.performance_utils import CalculationContext
from data.field_mapper import FieldMappingIndex

field_index = FieldMappingIndex(field_mappings)
context = CalculationContext(issues, field_index)

# Filter completed issues (cached)
completed = context.filter_issues(
    lambda issue: issue['status'] == 'Done',
    cache_key='completed'
)

# Reuse same filter (hits cache)
completed_again = context.filter_issues(
    lambda issue: issue['status'] == 'Done',
    cache_key='completed'
)
# No re-filtering, instant return
```

#### `get_completed_issues(time_period_days: int) -> List[Dict]`

Get issues completed within time period (shared across metrics)

**Parameters**:
- `time_period_days` (int): Number of days to look back

**Returns**: Issues completed in time period (List[Dict])

**Caching**: Results cached by time period

---

### Class: `FieldMappingIndex`

**Purpose**: Pre-computed bidirectional index for O(1) field lookups

**Methods**:

#### `__init__(field_mappings: Dict[str, str])`

Build index from field mappings

**Parameters**:
- `field_mappings` (Dict[str, str]): Logical name → JIRA field ID mapping

**Example**:
```python
field_mappings = {
    "deployment_date": "customfield_10001",
    "story_points": "customfield_10002"
}
index = FieldMappingIndex(field_mappings)
```

#### `get_jira_field(logical_name: str) -> Optional[str]`

Look up JIRA field ID by logical name

**Parameters**:
- `logical_name` (str): Logical field name (e.g., "deployment_date")

**Returns**: JIRA field ID (e.g., "customfield_10001") or None if not found

**Complexity**: O(1)

**Example**:
```python
index = FieldMappingIndex(field_mappings)
jira_field = index.get_jira_field("deployment_date")
# Returns: "customfield_10001"
```

#### `get_logical_name(jira_field: str) -> Optional[str]`

Look up logical name by JIRA field ID (reverse lookup)

**Parameters**:
- `jira_field` (str): JIRA field ID (e.g., "customfield_10001")

**Returns**: Logical name (e.g., "deployment_date") or None if not found

**Complexity**: O(1)

---

### Function: `parse_jira_date`

**Purpose**: Parse JIRA date string to datetime with LRU caching

**Signature**:
```python
@lru_cache(maxsize=10000)
def parse_jira_date(date_string: str) -> Optional[datetime]
```

**Parameters**:
- `date_string` (str): JIRA date string (ISO 8601 format)

**Returns**: datetime object or None if parsing fails

**Caching**: LRU cache with 10,000 entry limit (handles typical dataset sizes)

**Supported Formats**:
- ISO 8601: `2025-11-09T14:30:45.123Z`
- ISO with timezone: `2025-11-09T14:30:45.123+00:00`
- JIRA format: `2025-11-09T14:30:45.123456`

**Example**:
```python
from data.performance_utils import parse_jira_date

dt = parse_jira_date("2025-11-09T14:30:45.123Z")
# First call: parses and caches
# Subsequent calls with same string: instant return from cache
```

---

### Class: `PerformanceTimer`

**Purpose**: Context manager for timing code blocks

**Methods**:

#### `__init__(operation_name: str, log_result: bool = True)`

Create timer for operation

**Parameters**:
- `operation_name` (str): Name for logging
- `log_result` (bool): Whether to log duration on completion

#### `__enter__() -> 'PerformanceTimer'`

Start timer

#### `__exit__(...)`

Stop timer and optionally log duration

#### `elapsed_seconds() -> float`

Get elapsed time in seconds

**Example**:
```python
from data.performance_utils import PerformanceTimer

with PerformanceTimer("Database query", log_result=True):
    results = execute_query()
# Logs: "Database query completed in 0.456s"

# Manual timing without logging
timer = PerformanceTimer("Processing", log_result=False)
with timer:
    process_data()
print(f"Took {timer.elapsed_seconds():.3f}s")
```

---

## Performance Targets

**Metric Calculations**:
- ≤1000 issues: ≤2 seconds
- 1000-5000 issues: ≤5 seconds

**Optimizations Applied**:
- Date parsing: LRU cache reduces parsing from O(n) to O(1) for repeated dates
- Field lookups: Pre-built index reduces lookups from O(n) to O(1)
- Issue filtering: Shared context prevents redundant iterations

**Expected Improvements**:
- Date parsing: 80% time reduction for datasets with repeated dates
- Field lookups: 95% time reduction vs linear search
- Issue filtering: 50% time reduction by avoiding redundant filters

---

## Testing Contract

**Unit Tests** (`tests/unit/data/test_performance_utils.py`):
- `test_log_performance_decorator_logs_duration()` - Verify logging
- `test_log_performance_decorator_logs_errors()` - Verify error logging
- `test_calculation_context_caches_filters()` - Verify filter caching
- `test_calculation_context_cache_hit_performance()` - Verify cache speedup
- `test_field_mapping_index_bidirectional()` - Verify both lookup directions
- `test_field_mapping_index_o1_complexity()` - Verify O(1) performance
- `test_parse_jira_date_caching()` - Verify LRU cache behavior
- `test_parse_jira_date_formats()` - Verify format support
- `test_performance_timer_accuracy()` - Verify timing accuracy
- `test_performance_timer_context_manager()` - Verify context manager protocol

**Performance Benchmarks** (`tests/unit/data/test_performance.py`):
- `benchmark_dora_metrics_small_dataset()` - 500 issues, assert <2s
- `benchmark_dora_metrics_medium_dataset()` - 1500 issues, assert <5s
- `benchmark_flow_metrics_small_dataset()` - 500 issues, assert <2s
- `benchmark_flow_metrics_medium_dataset()` - 1500 issues, assert <5s
- `benchmark_date_parsing_cache_speedup()` - Verify 80% improvement
- `benchmark_field_lookup_speedup()` - Verify 95% improvement
