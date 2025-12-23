# Data Model: SQLite Database Schema

**Feature**: 015-sqlite-persistence  
**Date**: 2025-12-23  
**Purpose**: Define database schema, entity relationships, and data migration mapping.

## Entity-Relationship Overview

```
┌─────────────┐       ┌──────────────┐       ┌─────────────────┐
│  app_state  │       │   profiles   │◄──┬───│  project_data   │
│             │       │              │   │   │                 │
│ - key (PK)  │       │ - id (PK)    │   │   │ - id (PK)       │
│ - value     │       │ - name (UQ)  │   │   │ - profile_id (FK│
└─────────────┘       │ - jira_config│   │   │ - query_id (FK) │
                      │ - field_map  │   │   │ - data (JSON)   │
                      │ - settings   │   │   └─────────────────┘
                      └──────┬───────┘   │
                             │           │   ┌──────────────────┐
                             │ 1:N       ├───│  jira_cache      │
                             ▼           │   │                  │
                      ┌──────────────┐   │   │ - id (PK)        │
                      │   queries    │◄──┤   │ - profile_id (FK)│
                      │              │   │   │ - query_id (FK)  │
                      │ - id (PK)    │   │   │ - cache_key      │
                      │ - profile_id │   │   │ - response (JSON)│
                      │ - name       │   │   │ - expires_at     │
                      │ - jql        │   │   └──────────────────┘
                      └──────────────┘   │
                                         │   ┌───────────────────────┐
                                         ├───│ jira_changelog_cache  │
                                         │   │                       │
                                         │   │ - id (PK)             │
                                         │   │ - profile_id (FK)     │
                                         │   │ - query_id (FK)       │
                                         │   │ - issue_key           │
                                         │   │ - changelog (JSON)    │
                                         │   └───────────────────────┘
                                         │
                                         │   ┌───────────────────┐
                                         └───│ metrics_snapshots │
                                             │                   │
                                             │ - id (PK)         │
                                             │ - profile_id (FK) │
                                             │ - query_id (FK)   │
                                             │ - snapshot_date   │
                                             │ - metrics (JSON)  │
                                             └───────────────────┘

┌──────────────────┐
│  task_progress   │  (Independent - runtime state)
│                  │
│ - task_name (PK) │
│ - progress_%     │
│ - status         │
└──────────────────┘
```

**Legend**:
- PK = Primary Key
- FK = Foreign Key
- UQ = Unique Constraint
- 1:N = One-to-Many Relationship
- ◄── = Foreign Key Reference

## Table Schemas

### 1. profiles

**Purpose**: Store profile configurations (JIRA settings, field mappings, forecast settings)

**Mapping**: `profiles/{profile_id}/profile.json` → `profiles` table row

```sql
CREATE TABLE profiles (
    -- Primary identification
    id TEXT PRIMARY KEY,                    -- Profile ID (e.g., "default", "kafka")
    name TEXT NOT NULL UNIQUE,              -- Display name (e.g., "Apache Kafka Analysis")
    description TEXT DEFAULT '',            -- Optional description
    
    -- Timestamps
    created_at TEXT NOT NULL,               -- ISO 8601: "2025-12-23T10:30:00.000Z"
    last_used TEXT NOT NULL,                -- ISO 8601: Updated on profile switch
    
    -- JIRA connection (JSON)
    jira_config TEXT NOT NULL DEFAULT '{}', -- {base_url, token, points_field, epic_link_field, ...}
    
    -- Field mappings (JSON)
    field_mappings TEXT NOT NULL DEFAULT '{}',  -- {dora: {...}, flow: {...}}
    
    -- Forecast settings (JSON)
    forecast_settings TEXT NOT NULL DEFAULT '{"pert_factor": 1.2, "deadline": null, "data_points_count": 12}',
    
    -- Project classification (JSON)
    project_classification TEXT DEFAULT '{}',  -- {is_devops_project: bool, ...}
    
    -- Flow type mappings (JSON)
    flow_type_mappings TEXT DEFAULT '{}',  -- {feature: [...], defect: [...], ...}
    
    -- UI toggles
    show_milestone INTEGER DEFAULT 0,  -- Boolean: Show milestone markers on charts
    show_points INTEGER DEFAULT 0      -- Boolean: Show points vs items
);

-- Indexes
CREATE INDEX idx_profiles_last_used ON profiles(last_used DESC);  -- For recent profiles list
CREATE INDEX idx_profiles_name ON profiles(name);  -- For name-based lookups
```

**Column Details**:
- `id`: Slugified from name (e.g., "Apache Kafka" → "apache-kafka")
- JSON columns: Stored as TEXT, parsed by application
- `show_milestone`, `show_points`: SQLite doesn't have BOOLEAN, use INTEGER (0/1)

**Example Row**:
```json
{
    "id": "kafka",
    "name": "Apache Kafka Analysis",
    "description": "JIRA analysis for Apache Kafka project",
    "created_at": "2025-11-08T18:15:35.030Z",
    "last_used": "2025-12-23T10:22:15.000Z",
    "jira_config": "{\"base_url\": \"https://issues.apache.org/jira\", \"token\": \"...\"}",
    "field_mappings": "{\"dora\": {\"deployment_field\": \"customfield_10001\"}}",
    "forecast_settings": "{\"pert_factor\": 1.5, \"deadline\": \"2025-12-31\", \"data_points_count\": 12}",
    "project_classification": "{}",
    "flow_type_mappings": "{}",
    "show_milestone": 0,
    "show_points": 1
}
```

---

### 2. queries

**Purpose**: Store query configurations (JQL strings, metadata)

**Mapping**: `profiles/{profile_id}/queries/{query_id}/query.json` → `queries` table row

```sql
CREATE TABLE queries (
    -- Primary identification
    id TEXT NOT NULL,                 -- Query ID (e.g., "main", "bugs", "12w")
    profile_id TEXT NOT NULL,         -- Parent profile ID
    
    -- Query configuration
    name TEXT NOT NULL,               -- Display name (e.g., "Last 12 Weeks")
    jql TEXT NOT NULL,                -- JQL query string
    description TEXT DEFAULT '',      -- Optional description
    
    -- Timestamps
    created_at TEXT NOT NULL,         -- ISO 8601
    last_used TEXT NOT NULL,          -- ISO 8601: Updated on query switch
    
    -- Composite primary key (query ID unique within profile)
    PRIMARY KEY (profile_id, id),
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    
    -- Ensure unique query names within profile
    UNIQUE(profile_id, name)
);

-- Indexes
CREATE INDEX idx_queries_profile ON queries(profile_id, last_used DESC);  -- For query list per profile
CREATE INDEX idx_queries_name ON queries(profile_id, name);  -- For name-based lookups
```

**Column Details**:
- Composite PK `(profile_id, id)`: Query IDs unique within profile scope
- `CASCADE DELETE`: Deleting profile removes all its queries automatically
- `UNIQUE(profile_id, name)`: Prevent duplicate query names in same profile

**Example Row**:
```json
{
    "id": "12w",
    "profile_id": "kafka",
    "name": "Last 12 Weeks",
    "jql": "project = KAFKA AND updated >= -12w",
    "description": "Analysis of work completed in last 12 weeks",
    "created_at": "2025-11-10T09:00:00.000Z",
    "last_used": "2025-12-23T10:20:00.000Z"
}
```

---

### 3. app_state

**Purpose**: Store application-wide state (active selections, schema version)

**Mapping**: `profiles/profiles.json` metadata → `app_state` key-value pairs

```sql
CREATE TABLE app_state (
    key TEXT PRIMARY KEY,      -- State key
    value TEXT NOT NULL        -- State value (may be JSON for complex values)
);

-- Pre-populated keys:
-- 'active_profile_id' → Currently selected profile
-- 'active_query_id' → Currently selected query
-- 'schema_version' → Database schema version (e.g., "1.0")
-- 'migration_complete' → "true" if JSON→SQLite migration finished
```

**Example Rows**:
```sql
INSERT INTO app_state (key, value) VALUES ('active_profile_id', 'kafka');
INSERT INTO app_state (key, value) VALUES ('active_query_id', '12w');
INSERT INTO app_state (key, value) VALUES ('schema_version', '1.0');
INSERT INTO app_state (key, value) VALUES ('migration_complete', 'true');
```

**Why Key-Value Table**:
- Flexible: Add new state keys without schema migration
- Simple: Get/set with single query
- Atomic: Update active selections in single transaction

---

### 4. jira_cache

**Purpose**: Cache JIRA API responses with TTL expiration

**Mapping**: `profiles/{profile_id}/queries/{query_id}/jira_cache.json` → `jira_cache` table rows

```sql
CREATE TABLE jira_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    
    -- Cache key and data
    cache_key TEXT NOT NULL,          -- Hash of (JQL + fields requested)
    response TEXT NOT NULL,           -- JSON: Full JIRA API response
    
    -- TTL
    expires_at TEXT NOT NULL,         -- ISO 8601: When cache entry expires
    created_at TEXT NOT NULL,         -- ISO 8601: When entry was cached
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    
    -- Ensure unique cache entries per query
    UNIQUE(profile_id, query_id, cache_key)
);

-- Indexes
CREATE INDEX idx_jira_cache_expiry ON jira_cache(expires_at);  -- For cleanup queries
CREATE INDEX idx_jira_cache_query ON jira_cache(profile_id, query_id);  -- For query-specific lookups
```

**Column Details**:
- `cache_key`: MD5 hash of query parameters (JQL + fields + pagination)
- `response`: Entire JIRA API JSON response (issues array, pagination metadata)
- `expires_at`: Default 24 hours from created_at
- `CASCADE DELETE`: Deleting query removes its cache automatically

**TTL Enforcement**:
```sql
-- Get valid cache (application-level check)
SELECT response FROM jira_cache 
WHERE profile_id = ? AND query_id = ? AND cache_key = ?
AND expires_at > datetime('now');

-- Cleanup expired entries (background task)
DELETE FROM jira_cache WHERE expires_at <= datetime('now');
```

**Example Row**:
```json
{
    "id": 1,
    "profile_id": "kafka",
    "query_id": "12w",
    "cache_key": "abc123def456",
    "response": "{\"issues\": [{\"key\": \"KAFKA-1234\", ...}], \"total\": 50}",
    "expires_at": "2025-12-24T10:00:00.000Z",
    "created_at": "2025-12-23T10:00:00.000Z"
}
```

---

### 5. jira_changelog_cache

**Purpose**: Cache JIRA changelog data for DORA metrics calculations

**Mapping**: `profiles/{profile_id}/queries/{query_id}/jira_changelog_cache.json` → `jira_changelog_cache` table rows

```sql
CREATE TABLE jira_changelog_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    
    -- Issue identification
    issue_key TEXT NOT NULL,           -- JIRA issue key (e.g., "KAFKA-1234")
    
    -- Changelog data
    changelog TEXT NOT NULL,           -- JSON: Changelog entries array
    
    -- TTL
    expires_at TEXT NOT NULL,          -- ISO 8601: Default 24 hours
    created_at TEXT NOT NULL,          -- ISO 8601
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    
    -- Unique per issue within query
    UNIQUE(profile_id, query_id, issue_key)
);

-- Indexes
CREATE INDEX idx_changelog_expiry ON jira_changelog_cache(expires_at);
CREATE INDEX idx_changelog_query ON jira_changelog_cache(profile_id, query_id);
CREATE INDEX idx_changelog_issue ON jira_changelog_cache(issue_key);  -- For issue-specific lookups
```

**Example Row**:
```json
{
    "id": 1,
    "profile_id": "kafka",
    "query_id": "12w",
    "issue_key": "KAFKA-1234",
    "changelog": "[{\"field\": \"status\", \"from\": \"In Progress\", \"to\": \"Done\", \"created\": \"2025-12-20T15:00:00.000Z\"}]",
    "expires_at": "2025-12-24T10:00:00.000Z",
    "created_at": "2025-12-23T10:00:00.000Z"
}
```

---

### 6. project_data

**Purpose**: Store query-specific statistics, scope calculations, and metadata

**Mapping**: `profiles/{profile_id}/queries/{query_id}/project_data.json` → `project_data` table row

```sql
CREATE TABLE project_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    
    -- Data payload
    data TEXT NOT NULL,                -- JSON: Full project_data.json content
    
    -- Timestamps
    updated_at TEXT NOT NULL,          -- ISO 8601: Last update timestamp
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    
    -- One project_data per query
    UNIQUE(profile_id, query_id)
);

-- Index for query lookup
CREATE INDEX idx_project_data_query ON project_data(profile_id, query_id);
```

**Data Payload Structure**:
The `data` column contains the entire `project_data.json` structure:
```json
{
    "statistics": {
        "completed": 45,
        "in_progress": 12,
        "total_points": 230,
        "velocity": 15.5
    },
    "scope": {
        "initial_points": 200,
        "added_points": 50,
        "removed_points": 20
    },
    "forecast": {
        "completion_date": "2025-12-31",
        "confidence": 0.85
    }
}
```

**Why Single JSON Column**:
- Preserves exact structure of existing project_data.json
- Minimal migration complexity
- Flexible schema evolution
- Statistics accessed as unit, not individually

---

### 7. metrics_snapshots

**Purpose**: Store weekly DORA/Flow metrics snapshots for historical trending

**Mapping**: `profiles/{profile_id}/queries/{query_id}/metrics_snapshots.json` → `metrics_snapshots` table rows

```sql
CREATE TABLE metrics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    
    -- Snapshot identification
    snapshot_date TEXT NOT NULL,       -- ISO week (e.g., "2025-W12")
    metric_type TEXT NOT NULL,         -- "dora" or "flow"
    
    -- Metrics data
    metrics TEXT NOT NULL,             -- JSON: Metric values
    forecast TEXT,                     -- JSON: Forecast data (optional, Feature 009)
    
    -- Timestamp
    created_at TEXT NOT NULL,          -- ISO 8601: When snapshot was captured
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    
    -- Unique snapshot per week per metric type
    UNIQUE(profile_id, query_id, snapshot_date, metric_type)
);

-- Indexes
CREATE INDEX idx_snapshots_query_date 
    ON metrics_snapshots(profile_id, query_id, snapshot_date DESC);  -- For historical queries
CREATE INDEX idx_snapshots_type 
    ON metrics_snapshots(metric_type);  -- Filter by DORA vs Flow
```

**Metrics Payload Examples**:

DORA Metrics:
```json
{
    "deployment_frequency": 2.5,
    "lead_time_days": 4.2,
    "change_failure_rate": 0.08,
    "mttr_hours": 3.5
}
```

Flow Metrics:
```json
{
    "flow_velocity": 12.3,
    "flow_time_days": 8.5,
    "flow_efficiency": 0.65,
    "flow_load": 45
}
```

Forecast (Feature 009):
```json
{
    "predicted_value": 15.2,
    "confidence_interval": [12.0, 18.5],
    "trend": "improving"
}
```

---

### 8. task_progress

**Purpose**: Track runtime task progress (JIRA fetches, calculations)

**Mapping**: `task_progress.json` (root level) → `task_progress` table rows

```sql
CREATE TABLE task_progress (
    task_name TEXT PRIMARY KEY,        -- Task identifier (e.g., "fetch_jira_issues")
    progress_percent REAL NOT NULL,    -- 0.0 to 100.0
    status TEXT NOT NULL,              -- "running", "completed", "failed"
    message TEXT DEFAULT '',           -- Optional status message
    updated_at TEXT NOT NULL           -- ISO 8601: Last update timestamp
);
```

**Example Rows**:
```sql
INSERT INTO task_progress (task_name, progress_percent, status, message, updated_at)
VALUES ('fetch_jira_issues', 75.0, 'running', 'Fetched 750 of 1000 issues', '2025-12-23T10:30:15.000Z');

INSERT INTO task_progress (task_name, progress_percent, status, message, updated_at)
VALUES ('calculate_metrics', 100.0, 'completed', 'Metrics calculation complete', '2025-12-23T10:35:00.000Z');
```

**Why Separate Table**:
- Runtime state, not tied to profiles/queries
- Cleared on app restart (no long-term persistence)
- Simple key-value structure

---

## Data Migration Mapping

### JSON → SQLite Conversion

| JSON File                                               | Target Table             | Conversion Logic                                                              |
| ------------------------------------------------------- | ------------------------ | ----------------------------------------------------------------------------- |
| `profiles/profiles.json`                                | `app_state` + `profiles` | Parse registry, extract active IDs → app_state; profile list → profiles table |
| `profiles/{id}/profile.json`                            | `profiles`               | Direct mapping: profile config → single row                                   |
| `profiles/{id}/queries/{qid}/query.json`                | `queries`                | Direct mapping: query config → single row                                     |
| `profiles/{id}/queries/{qid}/jira_cache.json`           | `jira_cache`             | Parse cache entries → multiple rows (one per cached query)                    |
| `profiles/{id}/queries/{qid}/jira_changelog_cache.json` | `jira_changelog_cache`   | Parse changelog entries → multiple rows (one per issue)                       |
| `profiles/{id}/queries/{qid}/project_data.json`         | `project_data`           | Entire JSON → single row in `data` column                                     |
| `profiles/{id}/queries/{qid}/metrics_snapshots.json`    | `metrics_snapshots`      | Parse snapshot array → multiple rows (one per week/metric type)               |
| `task_progress.json` (root)                             | `task_progress`          | Parse task entries → multiple rows                                            |

### Migration Pseudocode

```python
def migrate_profiles_registry(conn):
    """Migrate profiles.json → app_state + profiles."""
    with open("profiles/profiles.json") as f:
        registry = json.load(f)
    
    # Migrate active selections to app_state
    conn.execute("INSERT INTO app_state (key, value) VALUES ('active_profile_id', ?)", 
                 (registry["active_profile_id"],))
    conn.execute("INSERT INTO app_state (key, value) VALUES ('active_query_id', ?)", 
                 (registry["active_query_id"],))
    
    # Migrate profiles list
    for profile_meta in registry["profiles"]:
        # Full profile data loaded separately from profile.json
        pass

def migrate_profile(conn, profile_id: str):
    """Migrate profiles/{id}/profile.json → profiles table."""
    profile_file = Path(f"profiles/{profile_id}/profile.json")
    with open(profile_file) as f:
        profile = json.load(f)
    
    conn.execute(
        """
        INSERT INTO profiles 
        (id, name, description, created_at, last_used, jira_config, field_mappings, 
         forecast_settings, project_classification, flow_type_mappings, show_milestone, show_points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile_id,
            profile["name"],
            profile.get("description", ""),
            profile["created_at"],
            profile["last_used"],
            json.dumps(profile["jira_config"]),
            json.dumps(profile["field_mappings"]),
            json.dumps(profile["forecast_settings"]),
            json.dumps(profile.get("project_classification", {})),
            json.dumps(profile.get("flow_type_mappings", {})),
            int(profile.get("show_milestone", False)),
            int(profile.get("show_points", False)),
        ),
    )

def migrate_query_data(conn, profile_id: str, query_id: str, query_dir: Path):
    """Migrate query data files → respective tables."""
    
    # Migrate jira_cache.json
    cache_file = query_dir / "jira_cache.json"
    if cache_file.exists():
        with open(cache_file) as f:
            cache_data = json.load(f)
        
        # Convert single JSON to multiple rows
        for cache_key, entry in cache_data.items():
            conn.execute(
                """
                INSERT INTO jira_cache 
                (profile_id, query_id, cache_key, response, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (profile_id, query_id, cache_key, json.dumps(entry["response"]), 
                 entry["expires_at"], entry["created_at"])
            )
    
    # Migrate project_data.json
    project_file = query_dir / "project_data.json"
    if project_file.exists():
        with open(project_file) as f:
            project_data = json.load(f)
        
        conn.execute(
            """
            INSERT INTO project_data (profile_id, query_id, data, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (profile_id, query_id, json.dumps(project_data), datetime.now().isoformat())
        )
    
    # Similar logic for changelog, snapshots...
```

---

## Indexing Strategy

### Index Purpose Matrix

| Index                      | Supports Query            | Performance Goal |
| -------------------------- | ------------------------- | ---------------- |
| `idx_profiles_last_used`   | List recent profiles      | <50ms            |
| `idx_profiles_name`        | Find profile by name      | <10ms            |
| `idx_queries_profile`      | List queries in profile   | <50ms            |
| `idx_queries_name`         | Find query by name        | <10ms            |
| `idx_jira_cache_expiry`    | Cleanup expired cache     | <1s (background) |
| `idx_jira_cache_query`     | Load cache for query      | <50ms            |
| `idx_changelog_expiry`     | Cleanup expired changelog | <1s (background) |
| `idx_changelog_query`      | Load changelog for query  | <50ms            |
| `idx_changelog_issue`      | Lookup by issue key       | <10ms            |
| `idx_snapshots_query_date` | Historical metrics query  | <200ms           |
| `idx_snapshots_type`       | Filter DORA vs Flow       | <100ms           |

### Composite Index Benefits

`idx_queries_profile(profile_id, last_used DESC)`:
- Covers `WHERE profile_id = ?` (profile filtering)
- Covers `ORDER BY last_used DESC` (recent queries first)
- Single index serves both query and sort

`idx_snapshots_query_date(profile_id, query_id, snapshot_date DESC)`:
- Covers `WHERE profile_id = ? AND query_id = ?`
- Covers `ORDER BY snapshot_date DESC` (chronological history)
- Efficient for paginated time-series queries

---

## Foreign Key Relationships

### Cascade Deletion Hierarchy

```
profiles (DELETE)
    ↓ CASCADE
queries (DELETE)
    ↓ CASCADE
┌───────────────┬───────────────────┬─────────────────┬───────────────────┐
│ jira_cache    │ jira_changelog    │ project_data    │ metrics_snapshots │
└───────────────┴───────────────────┴─────────────────┴───────────────────┘
```

**Example**:
```sql
-- Deleting profile cascades to all child data
DELETE FROM profiles WHERE id = 'kafka';

-- Automatically deletes:
-- 1. All queries for 'kafka' profile
-- 2. All jira_cache entries for those queries
-- 3. All jira_changelog_cache entries
-- 4. All project_data entries
-- 5. All metrics_snapshots entries
```

**Benefit**: No orphaned data, simplified delete logic, referential integrity enforced by database.

---

## Schema Versioning

### app_state Schema Version

```sql
INSERT INTO app_state (key, value) VALUES ('schema_version', '1.0');
```

**Future Migration Path**:
```python
def upgrade_schema():
    """Upgrade database schema to latest version."""
    current_version = get_app_state("schema_version")
    
    if current_version == "1.0":
        # Upgrade to 1.1 (e.g., add new column)
        conn.execute("ALTER TABLE profiles ADD COLUMN new_field TEXT")
        set_app_state("schema_version", "1.1")
    
    if current_version == "1.1":
        # Upgrade to 1.2
        # ...
```

---

## Data Validation Rules

| Validation                    | Rule                       | Enforcement         |
| ----------------------------- | -------------------------- | ------------------- |
| Profile name unique           | `UNIQUE(name)`             | Database constraint |
| Query name unique per profile | `UNIQUE(profile_id, name)` | Database constraint |
| Valid ISO 8601 timestamps     | Regex validation           | Application layer   |
| JSON columns parseable        | `json.loads()` check       | Application layer   |
| Foreign key integrity         | `FOREIGN KEY` constraints  | Database constraint |
| TTL expires_at > created_at   | Check before insert        | Application layer   |
| Progress percent in [0, 100]  | Check before insert        | Application layer   |

---

## Summary

- **8 tables**: profiles, queries, app_state, jira_cache, jira_changelog_cache, project_data, metrics_snapshots, task_progress
- **Normalized schema**: Foreign keys enforce hierarchy (Profile → Query → Data)
- **JSON columns**: Preserve complex nested structures (field_mappings, metrics)
- **Cascade deletion**: Simplifies cleanup, prevents orphaned data
- **Strategic indexes**: Composite indexes support common query patterns
- **Migration mapping**: Direct 1:1 for most files, 1:N for cache/snapshots

Ready for Phase 1: Contracts & Quickstart.
