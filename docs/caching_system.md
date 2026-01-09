# Caching System

## Overview

The burndown chart app uses a SQLite database for persistent storage and caching. This document explains how the caching system works.

**Note**: This document describes the current database-based caching system. Legacy JSON file caching (`jira_cache.json`, `project_data.json`) is deprecated and documented for backward compatibility only.

---

## Database Storage Architecture

### Primary Storage: SQLite Database

**Location**: `profiles/burndown.db`

**What it does**: Stores all JIRA data, statistics, metrics, and configuration in a normalized relational database.

**Note**: The `cache/` folder contains `cache.db`, which is created by Dash's diskcache library for background callback management. This is framework infrastructure and not part of the application data model.

**Key Tables** (12 total):
1. `app_state` - Application settings (key-value store)
2. `profiles` - Profile configurations
3. `queries` - Query definitions (JQL, name, timestamps)
4. `jira_issues` - Normalized JIRA issue data (replaces jira_cache.json)
5. `jira_cache` - Cache metadata (timestamps, expiry, config hashes)
6. `jira_changelog_entries` - Issue change history (replaces jira_changelog_cache.json)
7. `project_statistics` - Weekly statistics (replaces project_data.json statistics array)
8. `project_scope` - Project scope data (JSON aggregate)
9. `metrics_data_points` - Historical metrics (replaces metrics_snapshots.json)
10. `budget_settings` - Profile-level budget configuration
11. `budget_revisions` - Budget change event log
12. `task_progress` - Runtime task progress tracking

**Why database storage**:
- **Performance** - Indexed queries, no full-file parsing
- **Scalability** - Handles 100k+ issues efficiently
- **ACID guarantees** - Transactional consistency
- **Concurrent access** - Multiple processes can read simultaneously
- **Query flexibility** - SQL filtering, aggregation, joins
- **Space efficiency** - Normalized storage, no duplication

**Database structure**:
```
profiles/burndown.db (SQLite database)
├── profiles table
│   ├── team-alpha (id, name, settings)
│   └── team-beta (id, name, settings)
├── queries table
│   ├── sprint-backlog (profile: team-alpha, jql, name)
│   ├── bugs-only (profile: team-alpha, jql, name)
│   └── all-issues (profile: team-beta, jql, name)
├── jira_issues table
│   ├── Issues for team-alpha/sprint-backlog (profile_id, query_id, issue_key, ...)
│   ├── Issues for team-alpha/bugs-only
│   └── Issues for team-beta/all-issues
└── project_statistics table
    └── Weekly stats per profile/query combination

Legacy (deprecated):
profiles/
├── team-alpha/
│   └── queries/
│       ├── sprint-backlog/
│       │   └── query.json (metadata only)
│       └── bugs-only/
│           └── query.json (metadata only)
└── team-beta/
    └── queries/
        └── all-issues/
            └── query.json (metadata only)
```

**Cache invalidation**:
- JQL query changes → Delete rows from `jira_issues` table for that query
- Time period changes → Recalculate statistics, keep raw issue data
- Cache age exceeds 24 hours → Re-fetch from JIRA API
- Force refresh → Delete cached data for active query

---

### Legacy: Global Hash-Based Cache (Deprecated)

**Note**: This cache system is deprecated and being phased out. All caching now uses the SQLite database.

**Location**: `cache/{md5_hash}.json` (LEGACY - no longer used)

**What it does**: Provides cross-profile data reuse and background fetch optimization.

**Why it exists**:
- **Performance** - Fast lookup without knowing which profile/query is active
- **Reuse** - If multiple profiles use same JQL query, data is shared
- **Background optimization** - Quickly check if JIRA data changed without full fetch
- **Field mapping independence** - Cache key excludes field mappings, allowing metric recalculation without re-fetching JIRA data

**How cache keys work**:
```python
# Cache key = MD5 hash of (JQL query + time period days)
# Field mappings are NOT included in the hash

Example:
  JQL: "project = KAFKA AND created >= -30d"
  Time period: 30 days
  → Cache key: "3c73ccd8d90b2eaca573108ac9215a63.json"

# If you change field mappings (e.g., story points field):
  Same JQL + same time period
  → Same cache key
  → JIRA data reused, only metrics recalculated ✓
```

**Why field mappings are excluded**:
- JIRA data (issues, dates, statuses) doesn't change when field mappings change
- Only the *interpretation* of that data changes
- Re-fetching from JIRA would be wasteful when only processing config changed

---

## How Database Caching Works

### Scenario 1: First Data Load

```
1. User opens app → Profile: "Team Alpha", Query: "Sprint Backlog"
2. Check database: SELECT * FROM jira_issues WHERE profile_id='team-alpha' AND query_id='sprint-backlog'
   → Returns 0 rows (no cached data)
3. Fetch from JIRA API (200 issues)
4. Save to database:
   - INSERT INTO jira_issues (profile_id, query_id, issue_key, ...)
   - 200 rows inserted
5. Calculate statistics and save:
   - INSERT INTO project_statistics (profile_id, query_id, stat_date, ...)
6. Display data to user
```

**Result**: Database populated, future loads query from database (instant).

---

### Scenario 2: Update Data (Delta Fetch)

```
1. User clicks "Update Data" button
2. Check profile cache: jira_cache.json
   → Exists, last_updated = 2 hours ago
3. Delta fetch: Query JIRA for "updated >= last_cache_timestamp"
   → Returns only issues changed in last 2 hours (e.g., 5 issues)
4. Merge changed issues with cached data
5. Identify affected weeks from changed issues
6. Recalculate metrics only for affected weeks
7. Save merged data to cache with updated timestamp
```

**Result**: Fast incremental update, only changed data fetched and processed.

**Special cases**:
- **0 changes**: Skip metrics calculation entirely
- **>20% changed**: Fall back to full fetch (too many changes)
- **JQL changed**: Treat as Force Refresh

---

### Scenario 3: Force Refresh (Long-Press)

```
1. User long-presses "Update Data" button
2. Clear all caches (profile + global)
3. Fetch ALL issues from JIRA (ignoring cache)
4. Recalculate ALL metrics from scratch
5. Save fresh data to both caches
```

**Result**: Complete data refresh, bypasses all caching.

---

### Scenario 4: Switch Between Profiles

```
1. User switches from "Team Alpha" to "Team Beta"
2. Both use same JQL: "project = KAFKA AND created >= -30d"
3. Check profile cache: profiles/team-beta/queries/main/jira_cache.json
   → Does not exist (new profile)
4. Check global cache: cache/3c73ccd8.json
   → Exists! (Same JQL query as Team Alpha)
5. Copy data from global cache to profile cache
6. Display data instantly
```

**Result**: No JIRA API call needed, data reused across profiles.

---

### Scenario 5: Change Field Mappings

```
1. User changes story points field:
   - From: customfield_10002
   - To: customfield_10016
2. Cache key calculation:
   - JQL: "project = KAFKA..." (unchanged)
   - Time period: 30 days (unchanged)
   - Field mappings: NOT included in hash
   → Same cache key: 3c73ccd8.json
3. JIRA data reused from cache ✓
4. Metrics recalculated with new field mapping
```

**Result**: Fast recalculation without re-fetching JIRA data.

---

## When Caches Are Invalidated

### Profile Cache Invalidation

**Triggers**:
- JQL query modified (e.g., add filter, change project)
- Time period changed (e.g., -12w → -8w)
- User clicks "Force Refresh" (long-press Update Data button)
- App version upgrade with cache format changes

**Normal "Update Data" behavior**:
- Cache NOT invalidated - uses delta fetch for changed issues only
- Fetches issues with `updated >= last_cache_timestamp`
- Merges changes into existing cache

**What happens on Force Refresh**: 
- Old cache file deleted
- Fresh data fetched from JIRA (all issues)
- New cache file created

---

### Global Cache Invalidation

**Triggers**:
- Same as profile cache (JQL, time period, age, version)
- Cache key changes due to query modification

**What happens**:
- Orphaned cache files remain in `cache/` folder
- New cache file created with different hash
- Old files can be manually deleted (safe to remove entire `cache/` folder)

---

## Performance Characteristics

**Measured benefits**:
- Cache hit: **95%+ faster** than JIRA API call (instant vs 2-5 seconds)
- Cache key generation: **<0.001ms**
- Cache validation: **~0.01ms** per check
- Disk usage: **~2MB** for typical projects (negligible)

**Test coverage**:
- 35 cache-related tests
- 100% pass rate
- Tests cover: key generation, validation, save/load, invalidation, integration

---

## User Scenarios Explained

### "I have two profiles for different JIRA instances"

```
Profile: JIRA Cloud (jira.atlassian.com)
  Query: "All Issues" → jira_cache.json (200 issues)

Profile: JIRA Server (jira.mycompany.com)  
  Query: "All Issues" → jira_cache.json (500 issues)

Result: Each profile has isolated cache, no conflicts.
```

---

### "I changed field mappings but data didn't refresh"

```
This is CORRECT behavior:
- Field mappings only affect how data is processed
- Raw JIRA data (issues, dates, statuses) is unchanged
- Cache is reused for performance
- Metrics are recalculated with new mappings

If you need fresh data from JIRA:
- Click "Force Refresh" button
- Or wait 24 hours for cache to expire
```

---

### "I want to clear cache for one query"

```
Option 1 (UI): Click "Force Refresh" in Items per Week tab
  → Deletes rows from jira_issues table for active profile/query

Option 2 (SQL): Manually delete from database:
  DELETE FROM jira_issues WHERE profile_id='team-alpha' AND query_id='sprint-backlog';
  DELETE FROM jira_changelog_entries WHERE profile_id='team-alpha' AND query_id='sprint-backlog';

Option 3 (Legacy): Delete JSON files (if they exist):
  profiles/{profile_id}/queries/{query_id}/jira_cache.json (deprecated)
  profiles/{profile_id}/queries/{query_id}/jira_changelog_cache.json (deprecated)
```

---

### "Can I delete the entire database?"

```
Yes, but with caution:
- Deleting profiles/burndown.db → All data lost (profiles, queries, statistics)
- App will recreate empty database on next start
- You'll need to reconfigure profiles and re-fetch all JIRA data

Better option: Use "Force Refresh" to clear cache without losing configuration.

Legacy cache/ folder:
- cache/cache.db (Dash framework cache) → Safe to delete, auto-recreated
- cache/ folder (global cache) → No longer used for app data, safe to delete
- profiles/.../jira_cache.json files → Deprecated, safe to delete
```

---

## Technical Implementation

### Code Locations

**Database persistence**:
- `data/persistence/sqlite_backend.py` - SQLite database backend
- `data/database.py` - Database connection management
- `data/migration/schema_manager.py` - Database schema and migrations

**JIRA data operations**:
- `data/jira_simple.py` - JIRA API integration, saves to database
- Uses: `backend.save_issues(profile_id, query_id, issues)`
- Uses: `backend.get_issues(profile_id, query_id)`

**Legacy cache operations** (deprecated):
- `data/jira_simple.py` lines 1461-1464, 1507-1510 (legacy JSON files)
- `data/cache_manager.py` - Legacy cache validation (being phased out)

---

### Database Schema

**Complete 12-table schema** (from `data/migration/schema.py`):

#### 1. app_state
```sql
CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

#### 2. profiles
```sql
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    last_used TEXT NOT NULL,
    jira_config TEXT NOT NULL DEFAULT '{}',
    field_mappings TEXT NOT NULL DEFAULT '{}',
    forecast_settings TEXT NOT NULL DEFAULT '{"pert_factor": 1.2, "deadline": null, "data_points_count": 12}',
    project_classification TEXT NOT NULL DEFAULT '{}',
    flow_type_mappings TEXT NOT NULL DEFAULT '{}',
    show_milestone INTEGER DEFAULT 0,
    show_points INTEGER DEFAULT 0
);

CREATE INDEX idx_profiles_last_used ON profiles(last_used DESC);
CREATE INDEX idx_profiles_name ON profiles(name);
```

#### 3. queries
```sql
CREATE TABLE IF NOT EXISTS queries (
    id TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    name TEXT NOT NULL,
    jql TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_used TEXT NOT NULL,
    PRIMARY KEY (profile_id, id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE INDEX idx_queries_profile ON queries(profile_id, last_used DESC);
CREATE INDEX idx_queries_name ON queries(profile_id, name);
```

#### 4. jira_issues (normalized - replaces jira_cache.json)
```sql
CREATE TABLE IF NOT EXISTS jira_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    issue_key TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    issue_type TEXT,
    priority TEXT,
    resolution TEXT,
    created TEXT,
    updated TEXT,
    resolved TEXT,
    points REAL,
    project_key TEXT,
    project_name TEXT,
    fix_versions TEXT,
    labels TEXT,
    components TEXT,
    custom_fields TEXT,
    expires_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    UNIQUE(profile_id, query_id, issue_key)
);

CREATE INDEX idx_jira_issues_query ON jira_issues(profile_id, query_id);
CREATE INDEX idx_jira_issues_key ON jira_issues(profile_id, query_id, issue_key);
CREATE INDEX idx_jira_issues_status ON jira_issues(profile_id, query_id, status);
CREATE INDEX idx_jira_issues_assignee ON jira_issues(profile_id, query_id, assignee);
CREATE INDEX idx_jira_issues_type ON jira_issues(profile_id, query_id, issue_type);
CREATE INDEX idx_jira_issues_resolved ON jira_issues(resolved DESC);
CREATE INDEX idx_jira_issues_project ON jira_issues(project_key);
CREATE INDEX idx_jira_issues_expiry ON jira_issues(expires_at);
CREATE INDEX idx_jira_issues_cache ON jira_issues(cache_key);
```

#### 5. jira_cache (metadata table)
```sql
CREATE TABLE IF NOT EXISTS jira_cache (
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    issue_count INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    PRIMARY KEY (profile_id, query_id, cache_key),
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE
);

CREATE INDEX idx_jira_cache_key ON jira_cache(profile_id, query_id, cache_key);
```

#### 6. jira_changelog_entries (normalized - replaces jira_changelog_cache.json)
```sql
CREATE TABLE IF NOT EXISTS jira_changelog_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    issue_key TEXT NOT NULL,
    change_date TEXT NOT NULL,
    author TEXT NOT NULL,
    field_name TEXT NOT NULL,
    field_type TEXT DEFAULT 'jira',
    old_value TEXT,
    new_value TEXT,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id, query_id, issue_key) REFERENCES jira_issues(profile_id, query_id, issue_key) ON DELETE CASCADE
);

CREATE INDEX idx_changelog_query ON jira_changelog_entries(profile_id, query_id);
CREATE INDEX idx_changelog_issue ON jira_changelog_entries(profile_id, query_id, issue_key);
CREATE INDEX idx_changelog_field ON jira_changelog_entries(field_name);
CREATE INDEX idx_changelog_date ON jira_changelog_entries(change_date DESC);
CREATE INDEX idx_changelog_status ON jira_changelog_entries(field_name, new_value) WHERE field_name='status';
CREATE INDEX idx_changelog_expiry ON jira_changelog_entries(expires_at);
```

#### 7. project_statistics (normalized - replaces project_data.statistics)
```sql
CREATE TABLE IF NOT EXISTS project_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    stat_date TEXT NOT NULL,
    week_label TEXT,
    remaining_items INTEGER,
    remaining_total_points REAL,
    items_added INTEGER DEFAULT 0,
    items_completed INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    completed_points REAL DEFAULT 0.0,
    created_items INTEGER DEFAULT 0,
    created_points REAL DEFAULT 0.0,
    velocity_items REAL DEFAULT 0.0,
    velocity_points REAL DEFAULT 0.0,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    UNIQUE(profile_id, query_id, stat_date)
);

CREATE INDEX idx_project_stats_query ON project_statistics(profile_id, query_id);
CREATE INDEX idx_project_stats_date ON project_statistics(profile_id, query_id, stat_date DESC);
CREATE INDEX idx_project_stats_week ON project_statistics(week_label);
```

#### 8. project_scope
```sql
CREATE TABLE IF NOT EXISTS project_scope (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    scope_data TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    UNIQUE(profile_id, query_id)
);

CREATE INDEX idx_project_scope_query ON project_scope(profile_id, query_id);
```

#### 9. metrics_data_points (normalized - replaces metrics_snapshots.json)
```sql
CREATE TABLE IF NOT EXISTS metrics_data_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    query_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    metric_category TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    excluded_issue_count INTEGER DEFAULT 0,
    calculation_metadata TEXT,
    forecast_value REAL,
    forecast_confidence_low REAL,
    forecast_confidence_high REAL,
    calculated_at TEXT NOT NULL,
    FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
    UNIQUE(profile_id, query_id, snapshot_date, metric_category, metric_name)
);

CREATE INDEX idx_metrics_query ON metrics_data_points(profile_id, query_id);
CREATE INDEX idx_metrics_date ON metrics_data_points(profile_id, query_id, snapshot_date DESC);
CREATE INDEX idx_metrics_name ON metrics_data_points(profile_id, query_id, metric_name, snapshot_date DESC);
CREATE INDEX idx_metrics_category ON metrics_data_points(metric_category);
CREATE INDEX idx_metrics_value ON metrics_data_points(metric_name, metric_value);
```

#### 10. budget_settings
```sql
CREATE TABLE IF NOT EXISTS budget_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL UNIQUE,
    time_allocated_weeks INTEGER NOT NULL,
    team_cost_per_week_eur REAL,
    cost_rate_type TEXT DEFAULT 'weekly',
    currency_symbol TEXT DEFAULT '€',
    budget_total_eur REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE INDEX idx_budget_settings_profile ON budget_settings(profile_id);
```

#### 11. budget_revisions
```sql
CREATE TABLE IF NOT EXISTS budget_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    revision_date TEXT NOT NULL,
    week_label TEXT NOT NULL,
    time_allocated_weeks_delta INTEGER DEFAULT 0,
    team_cost_delta REAL DEFAULT 0,
    budget_total_delta REAL DEFAULT 0,
    revision_reason TEXT,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE INDEX idx_budget_revisions_profile ON budget_revisions(profile_id);
CREATE INDEX idx_budget_revisions_week ON budget_revisions(profile_id, week_label);
```

#### 12. task_progress
```sql
CREATE TABLE IF NOT EXISTS task_progress (
    task_name TEXT PRIMARY KEY,
    progress_percent REAL NOT NULL,
    status TEXT NOT NULL,
    message TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);
```

---

## Developer Notes

### Working with Database Cache

**Loading cached data**:
```python
from data.persistence.factory import get_backend

backend = get_backend()
issues = backend.get_issues(profile_id, query_id, limit=10000)
```

**Saving data to cache**:
```python
backend.save_issues(profile_id, query_id, issues)
backend.save_statistics(profile_id, query_id, statistics)
```

**Invalidating cache**:
```python
# Delete cached issues for a query
backend.delete_issues(profile_id, query_id)

# Or use higher-level invalidation
from data.cache_manager import invalidate_all_cache
invalidate_all_cache()  # Clears database cache
```

### Migration from JSON to Database

The app automatically migrates data from legacy JSON files to the database:
1. On first run, checks for `jira_cache.json` files
2. Imports data into SQLite database
3. Marks JSON files as legacy (can be safely deleted)

See `data/migration/json_to_db_migrator.py` for migration logic.

### Testing Cache Behavior

```powershell
# Run all cache-related tests
.\.venv\Scripts\activate; pytest tests/ -v -k "cache"

# Output: 35 tests, all passing (69.33s)
```

---

## Summary

**SQLite Database (current)**:
- Single source of truth for all data
- ACID transactions and data integrity
- Indexed queries for fast retrieval
- Normalized schema eliminates duplication
- Supports concurrent access
- 10-100x faster than JSON file parsing for large datasets

**Legacy JSON files (deprecated)**:
- `jira_cache.json` - Replaced by `jira_issues` table
- `jira_changelog_cache.json` - Replaced by `jira_changelog_entries` table
- `project_data.json` - Replaced by `project_statistics` table
- `metrics_snapshots.json` - Replaced by `metrics_data_points` table
- `cache/{hash}.json` - No longer used

**Benefits of database storage**:
- **Performance**: O(log n) indexed lookups vs O(n) file parsing
- **Reliability**: Transactional consistency, no corruption risk
- **Scalability**: Handles 100k+ issues efficiently
- **Maintainability**: SQL queries easier than JSON manipulation
- **Features**: Complex filtering, aggregation, joins

---

*Document Version: 2.1 (Corrected Schema) | Last Updated: January 2026*
