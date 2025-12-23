# Data Model: SQLite Database Schema

**Feature**: 015-sqlite-persistence  
**Date**: 2025-12-24 (Revised)  
**Purpose**: Define database schema, entity relationships, and data migration mapping.

**Key Design Decision**: Normalize large collections (jira_cache → jira_issues, jira_changelog_cache → jira_changelog_entries, project_data → project_statistics + project_scope, metrics_snapshots → metrics_data_points) to avoid storing 100k+ line JSON blobs in TEXT columns. This enables indexed queries, efficient filtering, and better performance for DORA/Flow metric calculations.

## Entity-Relationship Overview

```
┌─────────────┐       ┌──────────────┐      
│  app_state  │       │   profiles   │      
│             │       │              │      
│ - key (PK)  │       │ - id (PK)    │      
│ - value     │       │ - name (UQ)  │      
└─────────────┘       │ - jira_config│ (JSON - small ~1KB)      
                      │ - field_map  │ (JSON - small ~1KB)      
                      │ - settings   │ (JSON - small ~1KB)      
                      └──────┬───────┘   
                             │ 1:N       
                             ▼           
                      ┌──────────────┐   
                      │   queries    │   
                      │              │   
                      │ - id (PK)    │   
                      │ - profile_id │ (FK → profiles)  
                      │ - name       │   
                      │ - jql        │   
                      └──────┬───────┘   
                             │ 1:N       
                             ├───────────────────────────────┬────────────────────┬───────────────────┐
                             │                               │                    │                   │
                             ▼                               ▼                    ▼                   ▼
                      ┌────────────────┐          ┌────────────────────┐  ┌──────────────┐  ┌──────────────────────┐
                      │  jira_issues   │          │  project_statistics│  │ project_scope│  │  metrics_data_points │
                      │                │          │                    │  │              │  │                      │
                      │ - id (PK)      │          │ - id (PK)          │  │ - id (PK)    │  │ - id (PK)            │
                      │ - profile_id   │ (FK)     │ - profile_id       │  │ - profile_id │  │ - profile_id         │ (FK)
                      │ - query_id     │ (FK)     │ - query_id         │  │ - query_id   │  │ - query_id           │ (FK)
                      │ - cache_key    │          │ - stat_date        │  │ - scope_data │  │ - snapshot_date      │ (ISO week)
                      │ - issue_key    │          │ - week_label       │  │ - updated_at │  │ - metric_category    │ (dora|flow)
                      │ - summary      │          │ - completed_items  │  └──────────────┘  │ - metric_name        │ (deployment_freq|...)
                      │ - status       │          │ - completed_points │                    │ - metric_value       │
                      │ - assignee     │          │ - created_items    │                    │ - metric_unit        │
                      │ - issue_type   │          │ - created_points   │                    │ - excluded_count     │
                      │ - priority     │          │ - velocity_items   │                    │ - calc_metadata      │ (JSON)
                      │ - resolution   │          │ - velocity_points  │                    │ - forecast_value     │
                      │ - created      │          │ - recorded_at      │                    │ - forecast_low       │
                      │ - updated      │          └────────────────────┘                    │ - forecast_high      │
                      │ - resolved     │                                                     │ - calculated_at      │
                      │ - points       │                                                     └──────────────────────┘
                      │ - project_key  │          
                      │ - project_name │          
                      │ - fix_versions │ (JSON)   
                      │ - labels       │ (JSON)   
                      │ - components   │ (JSON)   
                      │ - custom_flds  │ (JSON)   
                      │ - expires_at   │          
                      │ - fetched_at   │          
                      └────────┬───────┘          
                               │ 1:N       
                               ▼           
                      ┌──────────────────────────┐
                      │ jira_changelog_entries   │
                      │                          │
                      │ - id (PK)                │
                      │ - profile_id             │ (FK)
                      │ - query_id               │ (FK)
                      │ - issue_key              │ (FK → jira_issues)
                      │ - change_date            │
                      │ - author                 │
                      │ - field_name             │
                      │ - field_type             │
                      │ - old_value              │
                      │ - new_value              │
                      │ - expires_at             │
                      └──────────────────────────┘

┌──────────────────┐
│  task_progress   │  (Independent - runtime state)
│                  │
│ - task_name (PK) │
│ - progress_%     │
│ - status         │
│ - message        │
│ - updated_at     │
└──────────────────┘
```

**Legend**:
- PK = Primary Key
- FK = Foreign Key
- UQ = Unique Constraint
- 1:N = One-to-Many Relationship
- ◄── = Foreign Key Reference

**Table Count**: 10 tables (normalized from original 8-table design)
- **Core**: app_state, profiles, queries
- **JIRA data (normalized)**: jira_issues, jira_changelog_entries
- **Project data (normalized)**: project_statistics, project_scope
- **Metrics (normalized)**: metrics_data_points
- **Runtime**: task_progress

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

### 4. jira_issues (Normalized Cache)

**Purpose**: Store individual JIRA issues (replaces jira_cache JSON blob)

**Mapping**: `profiles/{profile_id}/queries/{query_id}/jira_cache.json` → Individual `jira_issues` table rows

**Design Rationale**: Instead of storing 1000+ issues as one massive JSON blob, store each issue as a row with indexed columns. This enables:
- Fast queries: "Get all issues with status=Done" without loading entire cache
- Indexed filtering: Filter by status, assignee, priority, issue_type
- Memory efficiency: Load only needed issues, not entire 100k+ JSON string
- DORA/Flow metrics: Calculate metrics via indexed queries on status transitions

```sql
CREATE TABLE jira_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    cache_key TEXT NOT NULL,          -- Links to same cache fetch batch
    
    -- JIRA issue identification
    issue_key TEXT NOT NULL,          -- "KAFKA-1234"
    issue_id TEXT,                    -- JIRA internal ID
    
    -- Commonly queried fields (indexed)
    summary TEXT,                     -- Issue title
    status TEXT,                      -- "Done", "In Progress", "To Do"
    assignee TEXT,                    -- Assignee display name
    reporter TEXT,                    -- Reporter display name
    issue_type TEXT,                  -- "Bug", "Story", "Task", "Operational Task"
    priority TEXT,                    -- "High", "Medium", "Low"
    resolution TEXT,                  -- "Fixed", "Won't Fix", NULL if unresolved
    
    -- Timestamps (for metrics)
    created TEXT NOT NULL,            -- ISO 8601: Issue creation date
    updated TEXT,                     -- ISO 8601: Last updated
    resolved TEXT,                    -- ISO 8601: Resolution date (NULL if open)
    
    -- Story points and estimation
    points REAL,                      -- Story points (can be decimal)
    
    -- Project and categorization
    project_key TEXT,                 -- "KAFKA", "DEVOPS"
    project_name TEXT,                -- "Apache Kafka"
    
    -- JSON columns for complex nested data
    fix_versions TEXT,                -- JSON array: [{"id": "...", "name": "Release_2025_01"}]
    labels TEXT,                      -- JSON array: ["urgent", "bug-fix"]
    components TEXT,                  -- JSON array: [{"name": "core"}]
    custom_fields TEXT,               -- JSON object: All custom fields not in schema
    
    -- TTL (inherited from parent cache fetch)
    expires_at TEXT NOT NULL,         -- ISO 8601: When cache entry expires
    cached_at TEXT NOT NULL,          -- ISO 8601: When fetched from JIRA
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    
    -- Unique per issue within query cache
    UNIQUE(profile_id, query_id, cache_key, issue_key)
);

-- Indexes for fast filtering and metrics calculations
CREATE INDEX idx_jira_issues_query ON jira_issues(profile_id, query_id);
CREATE INDEX idx_jira_issues_key ON jira_issues(issue_key);  -- Lookup by key
CREATE INDEX idx_jira_issues_status ON jira_issues(profile_id, query_id, status);  -- Filter by status
CREATE INDEX idx_jira_issues_assignee ON jira_issues(profile_id, query_id, assignee);  -- Filter by assignee
CREATE INDEX idx_jira_issues_type ON jira_issues(profile_id, query_id, issue_type);  -- Filter by type
CREATE INDEX idx_jira_issues_resolved ON jira_issues(profile_id, query_id, resolved);  -- Filter resolved issues
CREATE INDEX idx_jira_issues_project ON jira_issues(project_key);  -- Filter by project
CREATE INDEX idx_jira_issues_expiry ON jira_issues(expires_at);  -- Cleanup expired cache
CREATE INDEX idx_jira_issues_cache ON jira_issues(profile_id, query_id, cache_key);  -- Batch operations
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

### 5. jira_changelog_entries (Normalized Changelog)

**Purpose**: Store individual changelog entries (replaces jira_changelog_cache JSON blob)

**Mapping**: `profiles/{profile_id}/queries/{query_id}/jira_changelog_cache.json` → Individual `jira_changelog_entries` rows

**Design Rationale**: DORA metrics require querying specific field changes (e.g., "when did status change to Done?"). Storing 1000+ changelog entries as JSON blobs forces full deserialization. Normalized table enables indexed queries like "Get all status changes to 'Done' in last week" without parsing JSON.

```sql
CREATE TABLE jira_changelog_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    
    -- Issue identification
    issue_key TEXT NOT NULL,          -- "KAFKA-1234" (FK → jira_issues)
    
    -- Change metadata
    change_date TEXT NOT NULL,        -- ISO 8601: When change occurred
    author TEXT,                      -- Who made the change (displayName)
    
    -- Field change details
    field_name TEXT NOT NULL,         -- "status", "assignee", "fixVersions"
    field_type TEXT,                  -- "jira", "custom"
    old_value TEXT,                   -- "In Progress"
    new_value TEXT,                   -- "Done"
    
    -- TTL (inherited from issue cache)
    expires_at TEXT NOT NULL,         -- ISO 8601
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    FOREIGN KEY (issue_key) 
        REFERENCES jira_issues(issue_key) ON DELETE CASCADE
);

-- Indexes for DORA metrics calculations
CREATE INDEX idx_changelog_query ON jira_changelog_entries(profile_id, query_id);
CREATE INDEX idx_changelog_issue ON jira_changelog_entries(issue_key);  -- All changes for issue
CREATE INDEX idx_changelog_field ON jira_changelog_entries(profile_id, query_id, field_name);  -- All status changes
CREATE INDEX idx_changelog_date ON jira_changelog_entries(profile_id, query_id, change_date);  -- Time-based queries
CREATE INDEX idx_changelog_status_transition ON jira_changelog_entries(profile_id, query_id, field_name, new_value);  -- "status" → "Done"
CREATE INDEX idx_changelog_expiry ON jira_changelog_entries(expires_at);  -- Cleanup
```

**Example Row**:
```json
{
    "id": 1,
    "profile_id": "kafka",
    "query_id": "12w",
    "issue_key": "KAFKA-1234",
    "change_date": "2025-12-20T15:00:00.000Z",
    "author": "John Doe",
    "field_name": "status",
    "field_type": "jira",
    "old_value": "In Progress",
    "new_value": "Done",
    "expires_at": "2025-12-24T10:00:00.000Z"
}
```

---

### 6. project_statistics (Normalized Weekly Stats)

**Purpose**: Store individual weekly statistics entries (replaces project_data.json statistics array)

**Mapping**: `profiles/{profile_id}/queries/{query_id}/project_data.json` → Individual `project_statistics` rows + separate `project_scope` table

**Design Rationale**: project_data.json contains two types of data:
1. **Statistics array**: Can grow to 52+ weeks (large, needs normalization)
2. **Scope/metadata**: Small aggregates (keep as JSON in separate table)

```sql
CREATE TABLE project_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    
    -- Week identification
    stat_date TEXT NOT NULL,          -- ISO date: "2025-12-01" (week start)
    week_label TEXT,                  -- ISO week: "2025-W48" (optional)
    
    -- Completed work
    completed_items INTEGER DEFAULT 0,
    completed_points REAL DEFAULT 0.0,
    
    -- Created work (scope changes)
    created_items INTEGER DEFAULT 0,
    created_points REAL DEFAULT 0.0,
    
    -- Velocity (can be calculated or cached)
    velocity_items REAL DEFAULT 0.0,
    velocity_points REAL DEFAULT 0.0,
    
    -- Timestamp
    recorded_at TEXT NOT NULL,        -- ISO 8601: When stat was recorded
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    
    -- One stat per week per query
    UNIQUE(profile_id, query_id, stat_date)
);

-- Indexes for time-series queries and velocity calculations
CREATE INDEX idx_project_stats_query ON project_statistics(profile_id, query_id);
CREATE INDEX idx_project_stats_date ON project_statistics(profile_id, query_id, stat_date DESC);  -- Historical queries
CREATE INDEX idx_project_stats_week ON project_statistics(week_label);  -- Group by week
```

**Benefits**:
- Query "last 12 weeks" without loading 52+ weeks
- Calculate velocity trends via SQL aggregations
- Add weekly stats incrementally (no rewrite entire file)

---

### 7. project_scope

**Purpose**: Store project scope metadata (small, keep as JSON)

**Mapping**: `profiles/{profile_id}/queries/{query_id}/project_data.json` scope section → `project_scope` row

```sql
CREATE TABLE project_scope (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    
    -- Scope data (small JSON ~1KB)
    scope_data TEXT NOT NULL,         -- JSON: {remaining_items, remaining_points, baseline, forecast}
    
    -- Timestamps
    updated_at TEXT NOT NULL,         -- ISO 8601: Last update
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    
    -- One scope per query
    UNIQUE(profile_id, query_id)
);

CREATE INDEX idx_project_scope_query ON project_scope(profile_id, query_id);
```

**Scope Data JSON Structure**:
```json
{
    "remaining_items": 60,
    "remaining_points": 240.0,
    "baseline_items": 100,
    "baseline_points": 400.0,
    "forecast": {
        "completion_date": "2025-12-31",
        "confidence": 0.85
    }
}
```

**Why JSON for scope_data**: Small aggregate data (~1KB), accessed as unit, infrequently queried

---

### 8. metrics_data_points (Normalized Metrics)

**Purpose**: Store individual metric values per week (replaces metrics_snapshots.json)

**Mapping**: `profiles/{profile_id}/queries/{query_id}/metrics_snapshots.json` → Individual `metrics_data_points` rows

**Design Rationale**: Storing 52 weeks × 8 metrics as JSON = 416 values in one blob. Normalized table enables:
- Query single metric trend: "Get deployment_frequency for last 12 weeks"
- Compare metrics: "Show all metrics for 2025-W48"
- Filter by threshold: "Find weeks where change_failure_rate > 0.1"

```sql
CREATE TABLE metrics_data_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    
    -- Snapshot identification
    snapshot_date TEXT NOT NULL,      -- ISO week: "2025-W48"
    metric_category TEXT NOT NULL,    -- "dora" or "flow"
    metric_name TEXT NOT NULL,        -- "deployment_frequency", "lead_time_days", etc.
    
    -- Metric value
    metric_value REAL NOT NULL,       -- Numeric value (2.5, 4.2, 0.08, etc.)
    metric_unit TEXT,                 -- "per_day", "days", "percent", "hours"
    
    -- Metadata
    excluded_issue_count INTEGER DEFAULT 0,  -- Issues excluded from calculation
    calculation_metadata TEXT,        -- JSON: How metric was calculated (optional)
    
    -- Forecast (Feature 009, optional)
    forecast_value REAL,              -- Predicted value
    forecast_confidence_low REAL,     -- Lower confidence bound
    forecast_confidence_high REAL,    -- Upper confidence bound
    
    -- Timestamp
    calculated_at TEXT NOT NULL,      -- ISO 8601: When metric was calculated
    
    -- Foreign key with cascade delete
    FOREIGN KEY (profile_id, query_id) 
        REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    
    -- One value per metric per week
    UNIQUE(profile_id, query_id, snapshot_date, metric_category, metric_name)
);

-- Indexes for time-series queries and metric filtering
CREATE INDEX idx_metrics_query ON metrics_data_points(profile_id, query_id);
CREATE INDEX idx_metrics_date ON metrics_data_points(profile_id, query_id, snapshot_date DESC);  -- Historical trends
CREATE INDEX idx_metrics_name ON metrics_data_points(profile_id, query_id, metric_name, snapshot_date DESC);  -- Single metric trend
CREATE INDEX idx_metrics_category ON metrics_data_points(metric_category);  -- Filter DORA vs Flow
CREATE INDEX idx_metrics_value ON metrics_data_points(metric_name, metric_value);  -- Threshold queries
```

**Example Rows** (2025-W48 DORA metrics):
```sql
-- Deployment Frequency
INSERT INTO metrics_data_points VALUES 
(1, 'kafka', '12w', '2025-W48', 'dora', 'deployment_frequency', 2.5, 'per_day', 0, NULL, 2.7, 2.0, 3.4, '2025-12-23T10:00:00Z');

-- Lead Time for Changes
INSERT INTO metrics_data_points VALUES 
(2, 'kafka', '12w', '2025-W48', 'dora', 'lead_time_days', 4.2, 'days', 5, '{"method": "percentile_50"}', NULL, NULL, NULL, '2025-12-23T10:00:00Z');

-- Change Failure Rate
INSERT INTO metrics_data_points VALUES 
(3, 'kafka', '12w', '2025-W48', 'dora', 'change_failure_rate', 0.08, 'percent', 0, NULL, NULL, NULL, NULL, '2025-12-23T10:00:00Z');
```

**Query Patterns**:
```sql
-- Get deployment frequency trend (last 12 weeks)
SELECT snapshot_date, metric_value 
FROM metrics_data_points
WHERE profile_id='kafka' AND query_id='12w' 
  AND metric_name='deployment_frequency'
ORDER BY snapshot_date DESC LIMIT 12;

-- Find high change failure rate weeks
SELECT snapshot_date, metric_value
FROM metrics_data_points
WHERE metric_name='change_failure_rate' 
  AND metric_value > 0.1
ORDER BY snapshot_date DESC;

-- Compare all DORA metrics for specific week
SELECT metric_name, metric_value, metric_unit
FROM metrics_data_points
WHERE profile_id='kafka' AND snapshot_date='2025-W48' 
  AND metric_category='dora';
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

| JSON File                                               | Target Table(s)                        | Conversion Logic                                                                 |
| ------------------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------- |
| `profiles/profiles.json`                                | `app_state` + `profiles`               | Parse registry, extract active IDs → app_state; profile list → profiles table    |
| `profiles/{id}/profile.json`                            | `profiles`                             | Direct mapping: profile config → single row                                      |
| `profiles/{id}/queries/{qid}/query.json`                | `queries`                              | Direct mapping: query config → single row                                        |
| `profiles/{id}/queries/{qid}/jira_cache.json`           | `jira_issues`                          | **Parse issues array → multiple rows (one per issue)** with indexed columns      |
| `profiles/{id}/queries/{qid}/jira_changelog_cache.json` | `jira_changelog_entries`               | **Parse changelog array → multiple rows (one per change event)** with indexes    |
| `profiles/{id}/queries/{qid}/project_data.json`         | `project_statistics` + `project_scope` | **Parse statistics array → rows; extract scope JSON → project_scope**            |
| `profiles/{id}/queries/{qid}/metrics_snapshots.json`    | `metrics_data_points`                  | **Parse snapshots → rows per metric per week** (52 weeks × 8 metrics = 416 rows) |
| `task_progress.json` (root)                             | `task_progress`                        | Parse task entries → multiple rows                                               |

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

def migrate_jira_cache_normalized(conn, profile_id: str, query_id: str, query_dir: Path):
    """Migrate jira_cache.json → jira_issues (normalized)."""
    cache_file = query_dir / "jira_cache.json"
    if not cache_file.exists():
        return
    
    with open(cache_file) as f:
        cache_data = json.load(f)
    
    # Extract issues array from cache response
    issues = cache_data.get("response", {}).get("issues", [])
    expires_at = cache_data.get("expires_at")
    
    # Batch insert individual issues
    issue_rows = []
    for issue in issues:
        fields = issue.get("fields", {})
        
        # Extract indexed columns
        issue_row = (
            profile_id,
            query_id,
            cache_data.get("cache_key", "default"),
            issue.get("key"),
            fields.get("summary", ""),
            fields.get("status", {}).get("name", ""),
            fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else "",
            fields.get("issuetype", {}).get("name", ""),
            fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
            fields.get("resolution", {}).get("name", "") if fields.get("resolution") else "",
            fields.get("created", ""),
            fields.get("updated", ""),
            fields.get("resolutiondate"),
            fields.get("customfield_10016"),  # Story Points example
            fields.get("project", {}).get("key", ""),
            fields.get("project", {}).get("name", ""),
            # JSON columns for nested data
            json.dumps(fields.get("fixVersions", [])),
            json.dumps(fields.get("labels", [])),
            json.dumps(fields.get("components", [])),
            json.dumps({k: v for k, v in fields.items() if k.startswith("customfield_")}),
            expires_at,
            datetime.now().isoformat()
        )
        issue_rows.append(issue_row)
    
    # Batch insert with executemany
    conn.executemany(
        """
        INSERT OR REPLACE INTO jira_issues 
        (profile_id, query_id, cache_key, issue_key, summary, status, assignee, 
         issue_type, priority, resolution, created, updated, resolved, points, 
         project_key, project_name, fix_versions, labels, components, custom_fields,
         expires_at, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        issue_rows
    )

def migrate_jira_changelog_normalized(conn, profile_id: str, query_id: str, query_dir: Path):
    """Migrate jira_changelog_cache.json → jira_changelog_entries (normalized)."""
    changelog_file = query_dir / "jira_changelog_cache.json"
    if not changelog_file.exists():
        return
    
    with open(changelog_file) as f:
        changelog_data = json.load(f)
    
    expires_at = changelog_data.get("expires_at")
    
    # Flatten nested changelog structure
    changelog_rows = []
    for issue_key, histories in changelog_data.get("changelogs", {}).items():
        for history in histories:
            change_date = history.get("created")
            author = history.get("author", {}).get("displayName", "")
            
            for item in history.get("items", []):
                changelog_row = (
                    profile_id,
                    query_id,
                    issue_key,
                    change_date,
                    author,
                    item.get("field"),
                    item.get("fieldtype", "jira"),
                    item.get("fromString"),
                    item.get("toString"),
                    expires_at
                )
                changelog_rows.append(changelog_row)
    
    # Batch insert
    conn.executemany(
        """
        INSERT OR REPLACE INTO jira_changelog_entries 
        (profile_id, query_id, issue_key, change_date, author, field_name, 
         field_type, old_value, new_value, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        changelog_rows
    )

def migrate_project_data_normalized(conn, profile_id: str, query_id: str, query_dir: Path):
    """Migrate project_data.json → project_statistics + project_scope (normalized)."""
    project_file = query_dir / "project_data.json"
    if not project_file.exists():
        return
    
    with open(project_file) as f:
        project_data = json.load(f)
    
    # 1. Migrate statistics array → project_statistics rows
    statistics = project_data.get("statistics", [])
    stats_rows = []
    for stat in statistics:
        stats_row = (
            profile_id,
            query_id,
            stat.get("date"),
            stat.get("week_label"),
            stat.get("completed_items", 0),
            stat.get("completed_points", 0.0),
            stat.get("created_items", 0),
            stat.get("created_points", 0.0),
            stat.get("velocity_items", 0.0),
            stat.get("velocity_points", 0.0),
            datetime.now().isoformat()
        )
        stats_rows.append(stats_row)
    
    conn.executemany(
        """
        INSERT OR REPLACE INTO project_statistics 
        (profile_id, query_id, stat_date, week_label, completed_items, completed_points,
         created_items, created_points, velocity_items, velocity_points, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        stats_rows
    )
    
    # 2. Migrate scope → project_scope row
    scope_data = project_data.get("scope", {})
    conn.execute(
        """
        INSERT OR REPLACE INTO project_scope 
        (profile_id, query_id, scope_data, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (profile_id, query_id, json.dumps(scope_data), datetime.now().isoformat())
    )

def migrate_metrics_snapshots_normalized(conn, profile_id: str, query_id: str, query_dir: Path):
    """Migrate metrics_snapshots.json → metrics_data_points (normalized)."""
    snapshots_file = query_dir / "metrics_snapshots.json"
    if not snapshots_file.exists():
        return
    
    with open(snapshots_file) as f:
        snapshots = json.load(f)
    
    # Flatten nested metrics structure
    metric_rows = []
    for snapshot in snapshots:
        snapshot_date = snapshot.get("snapshot_date")
        metric_category = snapshot.get("metric_type")  # "dora" or "flow"
        metrics = snapshot.get("metrics", {})
        forecast = snapshot.get("forecast", {})
        calculated_at = snapshot.get("created_at")
        
        # Each metric becomes a row
        for metric_name, metric_value in metrics.items():
            # Determine unit from metric name
            metric_unit = _infer_metric_unit(metric_name)
            
            # Extract forecast if available
            forecast_value = forecast.get(metric_name, {}).get("predicted_value")
            forecast_low = forecast.get(metric_name, {}).get("confidence_low")
            forecast_high = forecast.get(metric_name, {}).get("confidence_high")
            
            metric_row = (
                profile_id,
                query_id,
                snapshot_date,
                metric_category,
                metric_name,
                metric_value,
                metric_unit,
                0,  # excluded_issue_count placeholder
                None,  # calculation_metadata (optional)
                forecast_value,
                forecast_low,
                forecast_high,
                calculated_at
            )
            metric_rows.append(metric_row)
    
    # Batch insert
    conn.executemany(
        """
        INSERT OR REPLACE INTO metrics_data_points 
        (profile_id, query_id, snapshot_date, metric_category, metric_name, 
         metric_value, metric_unit, excluded_issue_count, calculation_metadata,
         forecast_value, forecast_confidence_low, forecast_confidence_high, calculated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        metric_rows
    )

def _infer_metric_unit(metric_name: str) -> str:
    """Infer metric unit from metric name."""
    unit_map = {
        "deployment_frequency": "per_day",
        "lead_time_days": "days",
        "change_failure_rate": "percent",
        "mttr_hours": "hours",
        "flow_velocity": "items_per_week",
        "flow_time_days": "days",
        "flow_efficiency": "percent",
        "flow_load": "items"
    }
    return unit_map.get(metric_name, "")

def migrate_query_data(conn, profile_id: str, query_id: str, query_dir: Path):
    """Migrate all query data files → respective normalized tables."""
    migrate_jira_cache_normalized(conn, profile_id, query_id, query_dir)
    migrate_jira_changelog_normalized(conn, profile_id, query_id, query_dir)
    migrate_project_data_normalized(conn, profile_id, query_id, query_dir)
    migrate_metrics_snapshots_normalized(conn, profile_id, query_id, query_dir)
```

**Key Changes from Original Design**:
1. **jira_cache**: Now parses issues array, extracts indexed columns (status, assignee, etc.), batch inserts with `executemany()`
2. **jira_changelog**: Flattens nested changelog structure (issue → history → items), creates individual change event rows
3. **project_data**: Splits into two tables - statistics array → `project_statistics` rows, scope object → `project_scope` JSON
4. **metrics_snapshots**: Flattens metrics object, creates one row per metric per week (52 weeks × 8 metrics = 416 rows)

**Performance**: Batch `executemany()` inserts 1000 issues in ~50ms vs 500ms+ for JSON serialization
```

---

## Indexing Strategy

### Index Purpose Matrix

| Index                      | Supports Query             | Performance Goal |
| -------------------------- | -------------------------- | ---------------- |
| `idx_profiles_last_used`   | List recent profiles       | <50ms            |
| `idx_profiles_name`        | Find profile by name       | <10ms            |
| `idx_queries_profile`      | List queries in profile    | <50ms            |
| `idx_queries_name`         | Find query by name         | <10ms            |
| `idx_jira_issues_query`    | Load issues for query      | <50ms            |
| `idx_jira_issues_key`      | Lookup by issue key        | <10ms            |
| `idx_jira_issues_status`   | Filter by status           | <100ms           |
| `idx_jira_issues_assignee` | Group by assignee          | <100ms           |
| `idx_jira_issues_type`     | Filter by issue type       | <100ms           |
| `idx_jira_issues_resolved` | Filter resolved issues     | <100ms           |
| `idx_jira_issues_project`  | Filter by project          | <100ms           |
| `idx_jira_issues_expiry`   | Cleanup expired cache      | <1s (background) |
| `idx_jira_issues_cache`    | Cache key lookups          | <50ms            |
| `idx_changelog_query`      | Load changelog for query   | <50ms            |
| `idx_changelog_issue`      | Changes for specific issue | <10ms            |
| `idx_changelog_field`      | Filter by field name       | <100ms           |
| `idx_changelog_date`       | Chronological queries      | <100ms           |
| `idx_changelog_status`     | Status transition analysis | <200ms           |
| `idx_changelog_expiry`     | Cleanup expired changelog  | <1s (background) |
| `idx_project_stats_query`  | Load stats for query       | <50ms            |
| `idx_project_stats_date`   | Time-series queries        | <100ms           |
| `idx_project_stats_week`   | Group by ISO week          | <100ms           |
| `idx_metrics_query`        | Load metrics for query     | <50ms            |
| `idx_metrics_date`         | Historical metric trends   | <100ms           |
| `idx_metrics_name`         | Single metric trend        | <100ms           |
| `idx_metrics_category`     | Filter DORA vs Flow        | <100ms           |
| `idx_metrics_value`        | Threshold queries          | <200ms           |

### Composite Index Benefits

`idx_queries_profile(profile_id, last_used DESC)`:
- Covers `WHERE profile_id = ?` (profile filtering)
- Covers `ORDER BY last_used DESC` (recent queries first)
- Single index serves both query and sort

`idx_jira_issues_query(profile_id, query_id)`:
- Covers `WHERE profile_id = ? AND query_id = ?`
- Efficient for loading all issues in a query
- Supports foreign key constraint checks

`idx_metrics_date(profile_id, query_id, snapshot_date DESC)`:
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
┌──────────────────┬─────────────────────────┬────────────────────┬────────────────────┬────────────────────┐
│ jira_issues      │ jira_changelog_entries  │ project_statistics │ project_scope      │ metrics_data_points│
└──────────────────┴─────────────────────────┴────────────────────┴────────────────────┴────────────────────┘
```

**Example**:
```sql
-- Deleting profile cascades to all child data
DELETE FROM profiles WHERE id = 'kafka';

-- Automatically deletes:
-- 1. All queries for 'kafka' profile
-- 2. All jira_issues entries for those queries
-- 3. All jira_changelog_entries
-- 4. All project_statistics entries
-- 5. All project_scope entries
-- 6. All metrics_data_points entries
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

- **10 tables**: profiles, queries, app_state, jira_issues, jira_changelog_entries, project_statistics, project_scope, metrics_data_points, task_progress (normalized from original 8-table design)
- **Normalized large collections**: Issues, changelog entries, weekly statistics, and metric data points stored as individual rows instead of JSON blobs
- **Strategic JSON usage**: Small nested data (<1KB) kept as JSON (fix_versions, labels, components, custom_fields, scope_data)
- **Foreign keys enforce hierarchy**: Profile → Query → Data with CASCADE DELETE for referential integrity
- **30+ indexes**: Composite indexes optimize common query patterns (status filtering, time-series queries, metric trends)
- **Migration mapping**: 1:N conversions for large collections (1 cache file → 1000 issue rows), batch `executemany()` for performance
- **Performance benefits**:
  - **No full deserialization**: Query "Get Done issues" without loading 1000 issues
  - **Indexed lookups**: Find issue by key in <10ms vs parsing entire cache
  - **Efficient delta updates**: UPSERT 10 changed issues in ~1ms vs 5MB cache rewrite
  - **SQL aggregations**: Calculate velocity via `SELECT AVG(velocity_points)` instead of Python loops
  - **Batch operations**: Insert 1000 issues in ~50ms vs 500ms+ JSON serialization

**Design Rationale** (per user feedback): Original JSON blob approach would store 100k+ lines in TEXT columns, defeating database purpose. Normalized schema mirrors JIRA structure, enabling indexed queries and efficient delta updates compatible with incremental fetch pattern.

Ready for Phase 1: Contracts & Quickstart.
