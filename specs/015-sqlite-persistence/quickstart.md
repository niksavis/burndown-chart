# Quickstart: SQLite Persistence Layer

**Feature**: 015-sqlite-persistence  
**Audience**: Developers working with the persistence layer  
**Prerequisites**: Familiarity with Python, SQLite basics

## Overview

The SQLite persistence layer replaces JSON file operations with database queries while maintaining the same profile/query workspace architecture. All persistence operations go through an abstract interface (`PersistenceBackend`) that allows testing with mock backends and future support for remote databases.

## Architecture

```
Business Logic Layer (data/profile_manager.py, data/query_manager.py)
                    ↓
    Persistence Interface (contracts/persistence_interface.py)
                    ↓
      ┌─────────────┴──────────────┐
      ↓                            ↓
SQLiteBackend                JSONBackend (legacy)
(data/persistence/sqlite_backend.py)  (data/persistence/json_backend.py)
      ↓                            ↓
profiles/burndown.db          profiles/{id}/*.json
```

## Database Location

**Path**: `profiles/burndown.db`

**Files Created**:
- `profiles/burndown.db` - Main database file
- `profiles/burndown.db-wal` - Write-Ahead Log (WAL mode)
- `profiles/burndown.db-shm` - Shared memory file (WAL mode)

**Important**: When moving database to different machine, copy all 3 files!

## Common Operations

### 1. Getting a Database Connection

```python
from data.database import get_db_connection

# Always use context manager for automatic commit/rollback
with get_db_connection() as conn:
    cursor = conn.execute("SELECT * FROM profiles WHERE id = ?", ("kafka",))
    row = cursor.fetchone()
    # conn.commit() called automatically on success
    # conn.rollback() called automatically on exception
```

**Key Points**:
- Each connection sets WAL mode automatically
- Connections have 10-second timeout for locking
- Row factory set to `sqlite3.Row` for dict-like access
- Never store connections globally - create per-operation

### 2. Using the Persistence Layer

```python
from data.persistence import get_backend

# Get singleton backend instance
backend = get_backend()

# Load profile
profile = backend.get_profile("kafka")
if profile:
    print(f"Profile: {profile['name']}")
    print(f"JIRA URL: {profile['jira_config']['base_url']}")

# Save profile
backend.save_profile({
    "id": "new-profile",
    "name": "New Project",
    "created_at": datetime.now().isoformat(),
    "last_used": datetime.now().isoformat(),
    "jira_config": {"base_url": "https://jira.example.com"},
    "field_mappings": {},
    "forecast_settings": {"pert_factor": 1.2, "deadline": None, "data_points_count": 12},
    # ... other required fields
})

# List queries
queries = backend.list_queries("kafka")
for query in queries:
    print(f"{query['name']}: {query['jql']}")
```

### 3. Working with JSON Columns

JSON columns are automatically serialized/deserialized by the backend:

```python
# Backend handles JSON conversion
profile = backend.get_profile("kafka")

# Access nested config
jira_url = profile["jira_config"]["base_url"]
pert_factor = profile["forecast_settings"]["pert_factor"]

# Update and save
profile["field_mappings"]["dora"]["deployment_field"] = "customfield_10001"
backend.save_profile(profile)
```

### 4. Cache Operations with TTL

```python
from datetime import datetime, timedelta

# Save to cache with 24-hour expiration
expires_at = datetime.now() + timedelta(hours=24)
backend.save_jira_cache(
    profile_id="kafka",
    query_id="12w",
    cache_key="abc123",  # Hash of (JQL + fields)
    response={"issues": [...], "total": 50},
    expires_at=expires_at
)

# Get from cache (returns None if expired)
cache = backend.get_jira_cache("kafka", "12w", "abc123")
if cache:
    issues = cache["issues"]
else:
    # Cache miss or expired - fetch from JIRA
    pass

# Cleanup expired entries (background task)
deleted_count = backend.cleanup_expired_cache()
print(f"Cleaned up {deleted_count} expired cache entries")
```

### 5. Metrics Snapshots

```python
# Save weekly snapshot
backend.save_metrics_snapshot(
    profile_id="kafka",
    query_id="12w",
    snapshot_date="2025-W12",  # ISO week format
    metric_type="dora",
    metrics={
        "deployment_frequency": 2.5,
        "lead_time_days": 4.2,
        "change_failure_rate": 0.08,
        "mttr_hours": 3.5
    },
    forecast={  # Optional (Feature 009)
        "predicted_value": 2.7,
        "confidence_interval": [2.0, 3.4]
    }
)

# Get historical snapshots (last 12 weeks)
snapshots = backend.get_metrics_snapshots(
    profile_id="kafka",
    query_id="12w",
    metric_type="dora",
    limit=12
)

# Plot trend
for snap in snapshots:
    print(f"{snap['snapshot_date']}: Deployment Frequency = {snap['metrics']['deployment_frequency']}")
```

### 6. App State Management

```python
# Get active selections
active_profile = backend.get_app_state("active_profile_id")
active_query = backend.get_app_state("active_query_id")

# Switch active profile
backend.set_app_state("active_profile_id", "new-profile")

# Check migration status
migration_done = backend.get_app_state("migration_complete") == "true"
```

### 7. Task Progress Tracking

```python
# Update progress during long-running task
backend.save_task_progress(
    task_name="fetch_jira_issues",
    progress_percent=75.0,
    status="running",
    message="Fetched 750 of 1000 issues"
)

# Check progress (from UI callback)
progress = backend.get_task_progress("fetch_jira_issues")
if progress:
    print(f"{progress['progress_percent']}% - {progress['message']}")

# Clear when complete
backend.clear_task_progress("fetch_jira_issues")
```

## Testing Patterns

### Unit Tests with Mock Backend

```python
import pytest
from unittest.mock import Mock
from data.persistence import set_backend, PersistenceBackend

@pytest.fixture
def mock_backend():
    """Provide mock backend for isolated testing."""
    backend = Mock(spec=PersistenceBackend)
    set_backend(backend)
    yield backend
    # Reset to real backend after test
    set_backend(None)  # Will recreate singleton

def test_get_profile_not_found(mock_backend):
    """Test error handling when profile doesn't exist."""
    mock_backend.get_profile.return_value = None
    
    from data.profile_manager import get_profile
    
    with pytest.raises(ValueError, match="Profile 'xyz' not found"):
        get_profile("xyz")
    
    mock_backend.get_profile.assert_called_once_with("xyz")
```

### Integration Tests with Temporary Database

```python
import pytest
import tempfile
from pathlib import Path
from data.persistence.sqlite_backend import SQLiteBackend
from data.persistence import set_backend

@pytest.fixture
def temp_db():
    """Provide temporary database for integration testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        backend = SQLiteBackend(db_path)
        set_backend(backend)
        yield backend

def test_profile_roundtrip(temp_db):
    """Test profile save and load with real database."""
    from data.profile_manager import create_profile, get_profile
    
    # Create profile
    profile_id = create_profile(
        name="Test Profile",
        settings={
            "jira_config": {"base_url": "https://jira.example.com"},
            "field_mappings": {},
            "forecast_settings": {"pert_factor": 1.2}
        }
    )
    
    # Load and verify
    loaded = get_profile(profile_id)
    assert loaded["name"] == "Test Profile"
    assert loaded["jira_config"]["base_url"] == "https://jira.example.com"
```

### Performance Benchmarks

```python
import pytest
from data.persistence import get_backend

@pytest.mark.benchmark
def test_get_profile_performance(benchmark, temp_db):
    """Benchmark profile load time (target: <10ms)."""
    backend = get_backend()
    
    # Setup: Create profile
    backend.save_profile({
        "id": "test",
        "name": "Test",
        "created_at": "2025-12-23T10:00:00Z",
        "last_used": "2025-12-23T10:00:00Z",
        "jira_config": {},
        "field_mappings": {},
        "forecast_settings": {}
    })
    
    # Benchmark: Load profile
    result = benchmark(backend.get_profile, "test")
    
    assert result is not None
    assert result["name"] == "Test"
    
    # Verify performance target
    assert benchmark.stats["mean"] < 0.010  # 10ms
```

## Migration Process

### Automatic Migration on Startup

```python
from data.migration import run_migration_if_needed

def app_startup():
    """Run on application startup."""
    # Check if migration needed and execute
    run_migration_if_needed()
    
    # Migration steps:
    # 1. Check if burndown.db exists and migration_complete flag set
    # 2. If not, create backup of profiles/ directory
    # 3. Initialize database schema
    # 4. Migrate all JSON files to database tables
    # 5. Validate data integrity
    # 6. Set migration_complete flag
    # 7. On failure, rollback and retry next launch
```

### Manual Export to JSON (Backup)

```python
from data.import_export import export_profile

# Export profile to JSON files for backup
export_dir = export_profile(
    profile_id="kafka",
    export_path="backups/kafka-backup"
)

# Creates:
# backups/kafka-backup/
# ├── profile.json
# ├── queries/
# │   ├── 12w.json
# │   └── bugs.json
# └── metrics/
#     └── snapshots.json
```

### Manual Import from JSON (Restore)

```python
from data.import_export import import_profile

# Import profile from JSON backup
profile_id = import_profile(
    import_path="backups/kafka-backup",
    profile_name="Kafka (Restored)"
)

print(f"Restored profile: {profile_id}")
```

## Common Pitfalls

### ❌ Don't Store Connections Globally

```python
# BAD - connections not thread-safe across Dash callbacks
db_conn = sqlite3.connect("profiles/burndown.db")

@callback(...)
def my_callback():
    cursor = db_conn.execute(...)  # UNSAFE!
```

```python
# GOOD - create connection per operation
@callback(...)
def my_callback():
    with get_db_connection() as conn:
        cursor = conn.execute(...)  # SAFE
```

### ❌ Don't Forget WAL File When Moving Database

```python
# BAD - only copying main database file
shutil.copy("profiles/burndown.db", "/backup/burndown.db")

# GOOD - copy all database files
for ext in ["", "-wal", "-shm"]:
    src = f"profiles/burndown.db{ext}"
    dst = f"/backup/burndown.db{ext}"
    if Path(src).exists():
        shutil.copy(src, dst)
```

### ❌ Don't Bypass Persistence Layer

```python
# BAD - direct SQL in business logic
def get_profile(profile_id):
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        return cursor.fetchone()

# GOOD - use persistence layer
def get_profile(profile_id):
    backend = get_backend()
    return backend.get_profile(profile_id)
```

### ❌ Don't Forget JSON Serialization

```python
# BAD - storing dict directly in JSON column
conn.execute(
    "INSERT INTO profiles (id, jira_config) VALUES (?, ?)",
    ("test", {"base_url": "https://jira.example.com"})  # Will fail!
)

# GOOD - serialize to JSON string
import json
conn.execute(
    "INSERT INTO profiles (id, jira_config) VALUES (?, ?)",
    ("test", json.dumps({"base_url": "https://jira.example.com"}))
)

# BETTER - use persistence layer (handles automatically)
backend.save_profile({
    "id": "test",
    "jira_config": {"base_url": "https://jira.example.com"}
})
```

## Debugging Tips

### Enable SQL Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("data.database")
logger.setLevel(logging.DEBUG)

# SQL queries will be logged to console
```

### Inspect Database with SQLite CLI

```powershell
# Open database in SQLite shell
sqlite3 profiles\burndown.db

# Common queries
.schema profiles
SELECT * FROM profiles;
SELECT * FROM queries WHERE profile_id = 'kafka';
SELECT COUNT(*) FROM jira_cache;
```

### Check Database Integrity

```python
from data.database import check_database_integrity

# Verify database not corrupted
is_ok, errors = check_database_integrity()
if not is_ok:
    print(f"Database errors: {errors}")
```

## Performance Targets

| Operation               | Target | How to Measure                    |
| ----------------------- | ------ | --------------------------------- |
| get_profile()           | <10ms  | pytest --benchmark                |
| list_queries()          | <50ms  | Integration test with 100 queries |
| save_profile()          | <100ms | Performance test suite            |
| get_jira_cache()        | <50ms  | Benchmark with 1000 cached issues |
| cleanup_expired_cache() | <1s    | Background task monitoring        |

## Schema Evolution

### Adding New Column

```python
def upgrade_schema_to_1_1():
    """Add new_field column to profiles table."""
    with get_db_connection() as conn:
        # Check current schema version
        version = conn.execute(
            "SELECT value FROM app_state WHERE key = 'schema_version'"
        ).fetchone()[0]
        
        if version == "1.0":
            # Add new column
            conn.execute("ALTER TABLE profiles ADD COLUMN new_field TEXT DEFAULT ''")
            
            # Update schema version
            conn.execute(
                "UPDATE app_state SET value = '1.1' WHERE key = 'schema_version'"
            )
            
            logger.info("Upgraded schema from 1.0 to 1.1")
```

### Creating Index

```python
def add_performance_index():
    """Add index for common query pattern."""
    with get_db_connection() as conn:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_custom ON table_name(column_name)"
        )
```

## Useful SQL Snippets

### Count Cached Issues Per Query

```sql
SELECT profile_id, query_id, COUNT(*) as cache_entries
FROM jira_cache
WHERE expires_at > datetime('now')
GROUP BY profile_id, query_id
ORDER BY cache_entries DESC;
```

### Find Profiles Not Used Recently

```sql
SELECT id, name, last_used
FROM profiles
WHERE last_used < datetime('now', '-30 days')
ORDER BY last_used ASC;
```

### Database Size Analysis

```sql
SELECT 
    'profiles' as table_name,
    COUNT(*) as row_count,
    SUM(LENGTH(jira_config) + LENGTH(field_mappings)) as json_bytes
FROM profiles
UNION ALL
SELECT 
    'jira_cache',
    COUNT(*),
    SUM(LENGTH(response))
FROM jira_cache;
```

## Support

For issues or questions:
1. Check [data-model.md](data-model.md) for schema reference
2. Review [research.md](research.md) for design decisions
3. See [contracts/persistence_interface.py](contracts/persistence_interface.py) for interface contract
4. Open issue with [DEBUG] prefix in commit message

---

**Version**: 1.0  
**Last Updated**: 2025-12-23
