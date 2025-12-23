# Research: SQLite Persistence Migration

**Feature**: 015-sqlite-persistence  
**Date**: 2025-12-23  
**Purpose**: Resolve all NEEDS CLARIFICATION items and establish technical foundation for Phase 1 design.

## Research Tasks

### 1. SQLite Best Practices for Python

#### Decision: Use sqlite3 with connection-per-request pattern + WAL mode

#### Rationale:
- **Thread Safety**: sqlite3 in Python is thread-safe when each thread/callback gets its own connection
- **WAL Mode**: Write-Ahead Logging allows concurrent reads during writes (critical for Dash multi-callback scenarios)
- **Connection Pooling**: Not needed for single-user local app; connection overhead negligible (<1ms)
- **Context Managers**: Use `with` statements for automatic transaction commit/rollback

#### Alternatives Considered:
1. **Single Global Connection**: Rejected - not thread-safe with Dash's threaded server
2. **SQLAlchemy ORM**: Rejected - adds complexity for simple CRUD operations, 50KB+ dependency
3. **Connection Pooling**: Rejected - overkill for single-user app, adds complexity

#### Implementation Notes:
```python
import sqlite3
from contextlib import contextmanager

DB_PATH = Path("profiles/burndown.db")

@contextmanager
def get_db_connection():
    """Get database connection with automatic commit/rollback."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode
    conn.row_factory = sqlite3.Row  # Dict-like row access
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Usage in data layer functions:
def get_profile(profile_id: str) -> Dict:
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (profile_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
```

**WAL Mode Benefits**:
- Readers don't block writers
- Writers don't block readers
- Better concurrency for Dash callbacks
- Automatic checkpoint mechanism

**File Locking on Windows**:
- WAL mode creates `-wal` and `-shm` files alongside main DB
- Users must copy all 3 files when moving database
- Document in quickstart.md

**Database Location Decision**:
- **Chosen**: `profiles/burndown.db` (inside profiles subfolder)
- **Rationale**: Enables Feature 016 (standalone packaging) portability - entire app state copyable via `profiles/` folder
- **User benefit**: "Backup your work? Copy the profiles folder" - simple, cohesive message
- **Portable mode**: Users can move app folder (exe + profiles/) to USB drive, backup location, or different machine without splitting database from profile data
- **Migration continuity**: During migration, `profiles/` contains both JSON backups and `burndown.db` - keeping them together reduces confusion
- **Alternative rejected**: Root-level `burndown.db` would split user data between root and `profiles/` subfolder, complicating backups and violating "all user data lives under profiles/" architecture

---

### 2. Schema Design for Profile/Query Hierarchy

#### Decision: Normalized tables with foreign keys + JSON columns for complex nested data

#### Rationale:
- **Foreign Keys**: Enforce referential integrity (CASCADE DELETE for profile/query hierarchy)
- **Normalization**: Separate tables for profiles, queries, cache entries allows efficient indexing
- **JSON Columns**: Store complex nested objects (field_mappings, jira_config) without over-normalization
- **Indexes**: Composite indexes on (profile_id, query_id) for fast query switching

#### Schema Overview:

```sql
-- Profiles table
CREATE TABLE profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL,
    last_used TEXT NOT NULL,
    jira_config TEXT,  -- JSON: {base_url, token, points_field, ...}
    field_mappings TEXT,  -- JSON: {dora: {...}, flow: {...}}
    forecast_settings TEXT,  -- JSON: {pert_factor, deadline, data_points_count}
    project_classification TEXT,  -- JSON
    flow_type_mappings TEXT,  -- JSON
    show_milestone INTEGER DEFAULT 0,
    show_points INTEGER DEFAULT 0
);

CREATE INDEX idx_profiles_last_used ON profiles(last_used DESC);

-- Queries table
CREATE TABLE queries (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    name TEXT NOT NULL,
    jql TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    last_used TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    UNIQUE(profile_id, name)
);

CREATE INDEX idx_queries_profile ON queries(profile_id, last_used DESC);

-- Active selection registry (replaces profiles.json metadata)
CREATE TABLE app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Stores: active_profile_id, active_query_id, schema_version

-- JIRA cache
CREATE TABLE jira_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    cache_key TEXT NOT NULL,  -- Hash of JQL + fields
    response TEXT NOT NULL,  -- JSON: Full JIRA API response
    expires_at TEXT NOT NULL,  -- ISO 8601 timestamp
    created_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    UNIQUE(profile_id, query_id, cache_key)
);

CREATE INDEX idx_jira_cache_expiry ON jira_cache(expires_at);
CREATE INDEX idx_jira_cache_query ON jira_cache(profile_id, query_id);

-- JIRA changelog cache
CREATE TABLE jira_changelog_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    issue_key TEXT NOT NULL,
    changelog TEXT NOT NULL,  -- JSON: Changelog entries
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    UNIQUE(profile_id, query_id, issue_key)
);

CREATE INDEX idx_changelog_expiry ON jira_changelog_cache(expires_at);
CREATE INDEX idx_changelog_query ON jira_changelog_cache(profile_id, query_id);

-- Project data (statistics, scope calculations)
CREATE TABLE project_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON: Full project_data.json content
    updated_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    UNIQUE(profile_id, query_id)
);

-- Metrics snapshots
CREATE TABLE metrics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,  -- ISO week (e.g., "2025-W12")
    metric_type TEXT NOT NULL,  -- "dora" or "flow"
    metrics TEXT NOT NULL,  -- JSON: Metric values
    forecast TEXT,  -- JSON: Forecast data (optional)
    created_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    UNIQUE(profile_id, query_id, snapshot_date, metric_type)
);

CREATE INDEX idx_snapshots_query_date ON metrics_snapshots(profile_id, query_id, snapshot_date DESC);

-- Task progress (runtime state)
CREATE TABLE task_progress (
    task_name TEXT PRIMARY KEY,
    progress_percent REAL NOT NULL,
    status TEXT NOT NULL,  -- "running", "completed", "failed"
    message TEXT,
    updated_at TEXT NOT NULL
);
```

#### Alternatives Considered:
1. **Fully Normalized Field Mappings**: Rejected - creates 10+ tables for nested structures, queries become complex
2. **Single JSON Blob Per Query**: Rejected - loses querying capability, no indexes possible
3. **Separate Cache Tables Per Type**: Rejected - increases schema complexity, CRUD operations duplicated

#### TTL Implementation:
**Decision**: Application-level expiration check (not database triggers)

**Rationale**:
- Simple to implement: `WHERE expires_at > datetime('now')`
- No trigger complexity or debugging issues
- Cleanup can run as background task
- Portable across SQLite versions

```python
def get_valid_cache(profile_id: str, query_id: str, cache_key: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT response FROM jira_cache
            WHERE profile_id = ? AND query_id = ? AND cache_key = ?
            AND expires_at > datetime('now')
            """,
            (profile_id, query_id, cache_key)
        )
        row = cursor.fetchone()
        return json.loads(row['response']) if row else None

def cleanup_expired_cache():
    """Background task to remove expired entries."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM jira_cache WHERE expires_at <= datetime('now')")
        conn.execute("DELETE FROM jira_changelog_cache WHERE expires_at <= datetime('now')")
```

---

### 3. Migration Strategy

#### Decision: Atomic all-at-once migration with backup and rollback

#### Rationale:
- **Atomic**: Entire migration succeeds or fails as unit - no partial state
- **Backup First**: Copy all JSON files to `backups/migration-{timestamp}/` before starting
- **Validation**: Check data integrity before and after migration
- **Rollback**: If migration fails, restore from backup and retry on next launch

#### Migration Flow:

```python
def migrate_json_to_sqlite():
    """One-time migration from JSON files to SQLite database."""
    
    # Step 1: Check if already migrated
    if DB_PATH.exists() and _is_migration_complete():
        return  # Already migrated
    
    # Step 2: Create backup
    backup_dir = Path(f"backups/migration-{datetime.now().isoformat()}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree("profiles/", backup_dir / "profiles/", dirs_exist_ok=True)
    logger.info(f"Backup created: {backup_dir}")
    
    try:
        # Step 3: Initialize database schema
        _create_database_schema()
        
        # Step 4: Migrate data (wrapped in transaction)
        with get_db_connection() as conn:
            # Migrate profiles.json → profiles table + app_state
            _migrate_profiles_registry(conn)
            
            # Migrate each profile
            for profile_dir in Path("profiles/").iterdir():
                if not profile_dir.is_dir():
                    continue
                
                profile_id = profile_dir.name
                if profile_id in ["backups", "burndown.db"]:
                    continue
                
                # Migrate profile.json → profiles table
                _migrate_profile(conn, profile_id)
                
                # Migrate queries for this profile
                queries_dir = profile_dir / "queries"
                if queries_dir.exists():
                    for query_dir in queries_dir.iterdir():
                        if not query_dir.is_dir():
                            continue
                        
                        query_id = query_dir.name
                        _migrate_query(conn, profile_id, query_id)
                        _migrate_query_data(conn, profile_id, query_id, query_dir)
        
        # Step 5: Validate migration
        if not _validate_migration():
            raise ValueError("Migration validation failed - data mismatch detected")
        
        # Step 6: Mark migration complete
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO app_state (key, value) VALUES ('migration_complete', 'true')"
            )
        
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Rollback: Delete database, restore from backup on next launch
        if DB_PATH.exists():
            DB_PATH.unlink()
        logger.info(f"Migration rolled back. Backup available at {backup_dir}")
        raise

def _validate_migration() -> bool:
    """Validate migration by comparing record counts."""
    # Count profiles in JSON vs database
    json_profiles = len(list(Path("profiles/").iterdir()))
    with get_db_connection() as conn:
        db_profiles = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
    
    if json_profiles != db_profiles:
        logger.error(f"Profile count mismatch: JSON={json_profiles}, DB={db_profiles}")
        return False
    
    # Similar validation for queries, cache entries, etc.
    return True
```

#### Alternatives Considered:
1. **Incremental Migration**: Rejected - leaves app in hybrid state, complex to manage
2. **Background Migration**: Rejected - user must wait anyway, simpler to block on startup
3. **No Backup**: Rejected - risky, violates user trust and safety requirements

#### Data Validation:
- Compare record counts before/after (profiles, queries, cache entries)
- Validate JSON parsing for all migrated data
- Check foreign key integrity
- Verify timestamps are valid ISO 8601 format

---

### 4. Performance Optimization

#### Decision: Prepared statements + batch inserts + strategic indexes

#### Rationale:
- **Prepared Statements**: Prevent SQL injection, enable query plan caching
- **Batch Inserts**: executemany() for migration (100x faster than row-by-row)
- **Indexes**: Composite indexes on frequent queries (profile_id, query_id)
- **ANALYZE**: Run after migration to update query planner statistics

#### Implementation:

```python
# Prepared statements (parameterized queries)
def save_profile(profile: Profile):
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO profiles 
            (id, name, description, created_at, last_used, jira_config, field_mappings, forecast_settings,
             project_classification, flow_type_mappings, show_milestone, show_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile.id,
                profile.name,
                profile.description,
                profile.created_at,
                profile.last_used,
                json.dumps(profile.jira_config),
                json.dumps(profile.field_mappings),
                json.dumps(profile.forecast_settings),
                json.dumps(profile.project_classification),
                json.dumps(profile.flow_type_mappings),
                int(profile.show_milestone),
                int(profile.show_points),
            ),
        )

# Batch inserts for migration
def _migrate_jira_cache_batch(conn, profile_id: str, query_id: str, cache_entries: List[Dict]):
    """Insert cache entries in single transaction."""
    conn.executemany(
        """
        INSERT INTO jira_cache (profile_id, query_id, cache_key, response, expires_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                profile_id,
                query_id,
                entry["cache_key"],
                json.dumps(entry["response"]),
                entry["expires_at"],
                entry["created_at"],
            )
            for entry in cache_entries
        ],
    )
```

#### Benchmark Targets:

| Operation                  | Target | Validation Method               |
| -------------------------- | ------ | ------------------------------- |
| get_profile()              | <10ms  | `pytest --benchmark`            |
| list_queries_for_profile() | <50ms  | Automated test with 100 queries |
| switch_query()             | <50ms  | Performance test in test suite  |
| Save settings              | <100ms | User interaction budget         |
| Migration (1000 issues)    | <5s    | Integration test                |

#### Database File Size:
- Estimated 1KB per cached issue (JSON response compressed in SQLite)
- 100 bytes per metric snapshot
- 1000 issues + 100 snapshots = ~1.1MB
- WAL file typically <10% of main DB file

---

### 5. Persistence Abstraction Pattern

#### Decision: Repository pattern with abstract base class

#### Rationale:
- **Repository Pattern**: Domain-driven design - abstracts data access from business logic
- **Single Responsibility**: Each repository handles one entity type (Profile, Query, Cache)
- **Testability**: Mock repositories in unit tests, real DB in integration tests
- **Future Flexibility**: Swap SQLite for remote DB without changing business logic

#### Abstract Interface:

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict

class PersistenceBackend(ABC):
    """Abstract interface for persistence backends."""
    
    @abstractmethod
    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """Load profile configuration."""
        pass
    
    @abstractmethod
    def save_profile(self, profile: Dict) -> None:
        """Save profile configuration."""
        pass
    
    @abstractmethod
    def list_profiles(self) -> List[Dict]:
        """List all profiles."""
        pass
    
    @abstractmethod
    def delete_profile(self, profile_id: str) -> None:
        """Delete profile and cascade to queries."""
        pass
    
    # Similar methods for Query, Cache, Snapshots entities
    # ...

class SQLiteBackend(PersistenceBackend):
    """SQLite implementation of persistence backend."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def get_profile(self, profile_id: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM profiles WHERE id = ?", (profile_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            # Convert row to dict and parse JSON columns
            profile = dict(row)
            profile['jira_config'] = json.loads(profile['jira_config'])
            profile['field_mappings'] = json.loads(profile['field_mappings'])
            profile['forecast_settings'] = json.loads(profile['forecast_settings'])
            return profile
    
    # ... other methods

class JSONBackend(PersistenceBackend):
    """Legacy JSON file backend (for rollback/compatibility)."""
    
    def get_profile(self, profile_id: str) -> Optional[Dict]:
        profile_file = Path(f"profiles/{profile_id}/profile.json")
        if not profile_file.exists():
            return None
        with open(profile_file) as f:
            return json.load(f)
    
    # ... other methods
```

#### Usage in Business Logic:

```python
# data/profile_manager.py

# Singleton backend instance (can be swapped for testing)
_backend: PersistenceBackend = SQLiteBackend(DB_PATH)

def set_backend(backend: PersistenceBackend):
    """Set persistence backend (for testing)."""
    global _backend
    _backend = backend

def get_profile(profile_id: str) -> Dict:
    """Load profile configuration."""
    profile = _backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' not found")
    return profile

def save_profile(profile: Profile):
    """Save profile configuration."""
    _backend.save_profile(profile.to_dict())
```

#### Testing Strategy:

```python
# tests/unit/data/test_profile_manager.py

def test_get_profile_not_found():
    """Test error handling when profile doesn't exist."""
    # Use mock backend to isolate test
    mock_backend = Mock(spec=PersistenceBackend)
    mock_backend.get_profile.return_value = None
    
    set_backend(mock_backend)
    
    with pytest.raises(ValueError, match="Profile 'xyz' not found"):
        get_profile("xyz")

# tests/integration/test_profile_manager_sqlite.py

def test_profile_roundtrip_with_sqlite(tmp_path):
    """Test profile save/load with real SQLite database."""
    db_path = tmp_path / "test.db"
    backend = SQLiteBackend(db_path)
    set_backend(backend)
    
    # Create and save profile
    profile = Profile(id="test", name="Test Profile")
    save_profile(profile)
    
    # Load and verify
    loaded = get_profile("test")
    assert loaded["name"] == "Test Profile"
```

#### Alternatives Considered:
1. **DAO Pattern**: Rejected - more verbose, less Pythonic than repository
2. **Active Record**: Rejected - couples domain objects to database, hard to test
3. **Direct SQLite Calls**: Rejected - tight coupling, cannot swap backends

---

## Summary: All Research Complete

All NEEDS CLARIFICATION items resolved. Key decisions:

1. **SQLite with WAL mode** + connection-per-request pattern
2. **Normalized schema** with JSON columns for complex nested data
3. **Atomic migration** with backup and validation
4. **Prepared statements + batch inserts** for performance
5. **Repository pattern** with abstract persistence interface

Ready to proceed to Phase 1: Design & Contracts.
