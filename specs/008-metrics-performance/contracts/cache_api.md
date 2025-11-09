# API Contracts: Cache Management Module

**Module**: `data/cache_manager.py`  
**Purpose**: Enhanced caching with configuration-based invalidation and incremental updates

## Public API

### Function: `generate_cache_key`

**Purpose**: Generate deterministic cache key from configuration parameters

**Signature**:
```python
def generate_cache_key(
    jql_query: str,
    field_mappings: Dict[str, str],
    time_period_days: int
) -> str
```

**Parameters**:
- `jql_query` (str): JIRA JQL query string
- `field_mappings` (Dict[str, str]): Mapping of logical names to JIRA custom fields
- `time_period_days` (int): Time period for data fetch (30, 60, 90 days)

**Returns**: 32-character hexadecimal string (MD5 hash)

**Determinism**: Same inputs always produce same cache key

**Example**:
```python
from data.cache_manager import generate_cache_key

cache_key = generate_cache_key(
    jql_query="project = ACME AND status = Done",
    field_mappings={"deployment_date": "customfield_10001"},
    time_period_days=30
)
# Returns: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
```

---

### Function: `load_cache_with_validation`

**Purpose**: Load cached data with validation (age, config hash, version)

**Signature**:
```python
def load_cache_with_validation(
    jql_query: str,
    field_mappings: Dict[str, str],
    time_period_days: int,
    max_age_hours: int = 24
) -> Tuple[bool, Optional[Dict[str, Any]]]
```

**Parameters**:
- `jql_query` (str): Current JQL query
- `field_mappings` (Dict[str, str]): Current field mappings
- `time_period_days` (int): Current time period
- `max_age_hours` (int): Maximum cache age in hours (default 24)

**Returns**: Tuple of (cache_hit: bool, data: Optional[Dict])
- `cache_hit=True, data=<dict>` - Valid cache found
- `cache_hit=False, data=None` - No cache or invalid

**Validation Checks**:
1. Cache file exists
2. Cache age < max_age_hours
3. Config hash matches current configuration
4. Cache version matches application version

**Example**:
```python
from data.cache_manager import load_cache_with_validation

cache_hit, issues = load_cache_with_validation(
    jql_query="project = ACME",
    field_mappings={"points": "customfield_10002"},
    time_period_days=30,
    max_age_hours=24
)

if cache_hit:
    print(f"Loaded {len(issues)} issues from cache")
else:
    print("Cache miss, fetching from JIRA")
```

---

### Function: `save_cache`

**Purpose**: Save data to cache with metadata

**Signature**:
```python
def save_cache(
    jql_query: str,
    field_mappings: Dict[str, str],
    time_period_days: int,
    data: Dict[str, Any]
) -> str
```

**Parameters**:
- `jql_query` (str): JQL query used to fetch data
- `field_mappings` (Dict[str, str]): Field mappings used
- `time_period_days` (int): Time period used
- `data` (Dict[str, Any]): Data to cache (issues, changelogs)

**Returns**: Cache key (str) - for reference/logging

**Side Effects**:
- Creates cache file at `cache/<cache_key>.json`
- Writes metadata + data as JSON

**Example**:
```python
from data.cache_manager import save_cache

cache_key = save_cache(
    jql_query="project = ACME",
    field_mappings={"points": "customfield_10002"},
    time_period_days=30,
    data={"issues": [...]}
)
print(f"Saved cache with key: {cache_key}")
```

---

### Function: `invalidate_cache`

**Purpose**: Delete cache file for specific configuration

**Signature**:
```python
def invalidate_cache(
    jql_query: str,
    field_mappings: Dict[str, str],
    time_period_days: int
) -> bool
```

**Parameters**:
- `jql_query` (str): JQL query
- `field_mappings` (Dict[str, str]): Field mappings
- `time_period_days` (int): Time period

**Returns**: True if cache was deleted, False if cache didn't exist

**Side Effects**: Deletes cache file if it exists

**Example**:
```python
from data.cache_manager import invalidate_cache

deleted = invalidate_cache(
    jql_query="project = ACME",
    field_mappings={"points": "customfield_10002"},
    time_period_days=30
)
```

---

### Class: `CacheInvalidationTrigger`

**Purpose**: Detect configuration changes and trigger cache invalidation

**Methods**:

#### `__init__(settings_file: str = 'app_settings.json')`

Initialize with settings file path

#### `check_and_invalidate() -> bool`

Check if configuration changed since last check, invalidate cache if changed

**Returns**: True if cache was invalidated, False otherwise

**Side Effects**: Updates last known configuration, deletes cache if changed

**Example**:
```python
from data.cache_manager import CacheInvalidationTrigger

trigger = CacheInvalidationTrigger()

# Call on every data fetch
if trigger.check_and_invalidate():
    logger.info("Configuration changed, cache invalidated")
```

---

## Internal API (Not for external use)

### Function: `_read_cache_file(cache_key: str) -> Optional[Dict]`

Read cache file by key

### Function: `_write_cache_file(cache_key: str, cache_data: Dict) -> None`

Write cache file

### Function: `_get_cache_metadata(cache_key: str) -> Dict`

Build metadata dict for cache file

---

## Cache File Format

**Location**: `cache/<cache_key>.json`

**Structure**:
```json
{
  "metadata": {
    "cache_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "creation_timestamp": "2025-11-09T14:30:45Z",
    "expiration_timestamp": "2025-11-10T14:30:45Z",
    "version_identifier": "2.0",
    "config_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "data_size_bytes": 1048576,
    "issue_count": 850,
    "jql_query": "project = ACME AND status = Done"
  },
  "data": {
    "issues": [...],
    "changelogs": [...]
  }
}
```

---

## Configuration Change Detection

**Triggers for Invalidation**:
1. JQL query string changes
2. Field mapping additions/removals/changes
3. Time period changes (30 → 60 days)

**Not Triggers** (don't invalidate):
1. PERT factor changes (doesn't affect JIRA data)
2. Deadline changes
3. UI toggle changes

---

## Testing Contract

**Unit Tests** (`tests/unit/data/test_cache_manager.py`):
- `test_generate_cache_key_deterministic()` - Same inputs → same key
- `test_generate_cache_key_different_inputs()` - Different inputs → different keys
- `test_load_cache_with_validation_hit()` - Valid cache returns data
- `test_load_cache_with_validation_expired()` - Old cache returns None
- `test_load_cache_with_validation_wrong_config()` - Config mismatch returns None
- `test_save_cache_creates_file()` - Verify file created
- `test_save_cache_includes_metadata()` - Verify metadata complete
- `test_invalidate_cache_deletes_file()` - Verify deletion
- `test_cache_invalidation_trigger_on_jql_change()` - JQL change triggers invalidation
- `test_cache_invalidation_trigger_on_field_change()` - Field mapping change triggers invalidation
- `test_cache_invalidation_trigger_ignores_pert()` - PERT change doesn't invalidate

**Integration Tests** (`tests/integration/test_caching_workflow.py`):
- `test_end_to_end_cache_lifecycle()` - Save → load → invalidate cycle
- `test_cache_survives_app_restart()` - Persistence across sessions
- `test_concurrent_cache_access()` - Thread safety
