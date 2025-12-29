# Feature Specification: SQLite Database Migration

**Feature Branch**: `015-sqlite-persistence`  
**Created**: 2025-12-23  
**Status**: Draft  
**Input**: User description: "Change the data persistence from JSON files to SQLite database. All files created, updated, and deleted by the app must be replaced by database tables and queries."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seamless Data Migration (Priority: P1)

Existing users with JSON files must automatically migrate to SQLite database on first app launch after upgrade, with all data preserved and no manual intervention required.

**Why this priority**: Protects existing user data and prevents breaking changes. Without this, users lose all historical data (JIRA cache, project data, metrics history, saved queries).

**Independent Test**: Can be fully tested by creating sample JSON files with known data, launching upgraded app, and verifying database contains identical data structure and values.

**Acceptance Scenarios**:

1. **Given** user has existing `app_settings.json` with JIRA config and field mappings, **When** user launches upgraded app, **Then** database contains all settings with identical values and JSON file is backed up
2. **Given** user has `project_data.json` with statistics and metrics history, **When** app starts, **Then** database preserves all historical snapshots and scope calculations
3. **Given** user has multiple query profiles in `jira_query_profiles.json`, **When** migration runs, **Then** all saved queries are available in database with same names and JQL
4. **Given** user has cached JIRA responses in `jira_cache.json` with TTL metadata, **When** migration completes, **Then** cache entries retain expiration timestamps
5. **Given** migration fails mid-process, **When** user restarts app, **Then** system recovers from backup JSON files and retries migration

---

### User Story 2 - Fast Data Operations (Priority: P2)

App performs CRUD operations (create, read, update, delete) on database with equal or better performance than JSON file operations.

**Why this priority**: Ensures no user-facing performance degradation. Users expect instant UI updates when changing settings or loading cached data.

**Independent Test**: Benchmark database operations against JSON file operations using realistic data volumes (100+ cached issues, 50+ metric snapshots) and verify response times meet <100ms budget for user interactions.

**Acceptance Scenarios**:

1. **Given** app loads settings from database, **When** user opens Settings panel, **Then** settings appear within 100ms
2. **Given** 500 cached JIRA issues in database, **When** app queries for specific issues, **Then** results return within 50ms
3. **Given** user updates JIRA config field mapping, **When** save is clicked, **Then** database persists change within 100ms and UI reflects update
4. **Given** user deletes a saved query profile, **When** delete is confirmed, **Then** database removes entry immediately and query list updates
5. **Given** 100 weekly metric snapshots in database, **When** chart needs historical data, **Then** query completes within 200ms

---

### User Story 3 - Multi-Profile Database Management (Priority: P2)

Profile-based workspace system (`profiles/{profile_id}/`) must translate to database tables with profile isolation, where each profile's data is logically separated.

**Why this priority**: Maintains existing multi-profile architecture. Users depend on switching between different JIRA instances or project configurations.

**Independent Test**: Create two profiles with different JIRA configs, verify data isolation by confirming Profile A changes don't affect Profile B queries.

**Acceptance Scenarios**:

1. **Given** user creates new profile, **When** profile is initialized, **Then** database creates profile record with unique ID and empty query records
2. **Given** user switches from Profile A to Profile B, **When** app loads Profile B data, **Then** only Profile B's settings, queries, and cache appear
3. **Given** user deletes Profile A, **When** deletion completes, **Then** database removes all Profile A data (settings, queries, cache) and Profile B remains unaffected
4. **Given** Profile A has custom field mappings, **When** user exports Profile A settings, **Then** export includes all profile-specific data from database

---

### User Story 4 - Concurrent Access Safety (Priority: P3)

Multiple app instances or background processes can safely access database without data corruption or locked file errors.

**Why this priority**: Prevents race conditions when running automated tasks (metrics snapshots) or if users accidentally launch multiple instances.

**Independent Test**: Launch two app instances pointing to same database, perform write operations from both, verify data integrity and no lock errors.

**Acceptance Scenarios**:

1. **Given** app instance A is running, **When** instance B starts and reads cache, **Then** both instances access database without blocking
2. **Given** background task writes metrics snapshot, **When** user updates settings simultaneously, **Then** both operations complete without conflicts
3. **Given** database connection drops mid-transaction, **When** app reconnects, **Then** partial writes are rolled back and data remains consistent

---

### Edge Cases

- What happens when database file is corrupted or manually deleted while app is running?
- How does system handle migration if JSON files contain invalid/malformed data?
- What if user manually edits database file with external SQLite tool while app is running?
- How does backup/restore work with database files vs JSON files?
- What if database schema needs to evolve in future versions (migration path)?
- How does system handle database file locked by another process during startup?
- What if database file grows very large (>100MB) - does performance degrade?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST migrate all existing JSON files (`app_settings.json`, `project_data.json`, `jira_cache.json`, `jira_changelog_cache.json`, `jira_query_profiles.json`, `metrics_snapshots.json`, `task_progress.json`) to SQLite database on first launch after upgrade
- **FR-002**: System MUST create automatic backup of JSON files before migration begins, stored in `backups/{timestamp}/` directory
- **FR-003**: System MUST create database file (`burndown.db`) in `profiles/` directory on first launch if not exists
- **FR-004**: System MUST structure database with 10 normalized tables: `profiles`, `queries`, `app_state` (replaces settings), `jira_issues` (normalized cache), `jira_changelog_entries` (normalized changelog), `project_statistics` (normalized weekly stats), `project_scope`, `metrics_data_points` (normalized metrics), `task_progress`
- **FR-004a**: System MUST normalize large collections (JIRA issues 1000+, changelog entries 5000+, weekly statistics 52+, metric values 400+) as individual database rows instead of JSON TEXT blobs to enable indexed queries, efficient delta updates, and SQL-based aggregations without full deserialization
- **FR-005**: System MUST maintain profile-based data isolation where each profile's data is stored with `profile_id` foreign key
- **FR-006**: System MUST preserve all existing data structures (JIRA config, field mappings, statistics, scope, metrics history, cached responses with TTL)
- **FR-007**: System MUST implement TTL (time-to-live) expiration for JIRA cache entries (24-hour default)
- **FR-008**: System MUST support all existing CRUD operations with database queries replacing file I/O
- **FR-009**: System MUST handle concurrent database access with proper locking and transaction management
- **FR-010**: System MUST rollback database changes if transaction fails to maintain data consistency
- **FR-011**: System MUST log all database operations (create, update, delete) at DEBUG level for troubleshooting
- **FR-012**: System MUST provide database schema versioning for future migrations
- **FR-013**: System MUST validate database integrity on startup and repair/recreate if corrupted
- **FR-014**: System MUST export database to profile-compatible directory structure (`profiles/{id}/profile.json`, `queries/{id}/query.json`, `jira_cache.json`, etc.) enabling backward compatibility with JSON backend and manual editing if needed
- **FR-015**: System MUST support database import from JSON format for restore operations

### Key Data Categories

- **Profile Management**: Profile configurations with JIRA settings, field mappings, forecast parameters (stored as small JSON ~1KB)
- **Query Management**: Saved JQL queries with metadata (name, JQL string, timestamps)
- **JIRA Issue Data**: Individual issue rows with indexed columns (status, assignee, type, priority, dates) plus nested JSON for fix_versions, labels, components
- **Changelog History**: Individual change event rows (field_name, old_value, new_value, change_date) enabling status transition queries
- **Project Statistics**: Weekly data points (completed items/points, velocity) for burndown trend analysis
- **Metrics Time-Series**: Individual metric value rows (deployment_frequency, lead_time, MTTR, etc.) per week for historical trending
- **Task Progress**: Runtime state tracking (progress percent, status messages)

**Note**: See [data-model.md](data-model.md) for complete 10-table schema with entity relationships, indexing strategy, and migration mapping

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Existing users complete automatic migration from JSON to SQLite within 5 seconds for datasets up to 1000 cached issues
- **SC-002**: All database read operations complete within 50ms for typical query sizes (100 records)
- **SC-003**: All database write operations complete within 100ms maintaining existing performance budget
- **SC-004**: Zero data loss during migration - 100% of JSON data successfully transfers to database
- **SC-005**: Database operations handle 1000+ cached JIRA issues without performance degradation
- **SC-006**: Concurrent database access from multiple processes completes without deadlocks or corruption
- **SC-007**: Database file size grows proportionally: ~(issue_count × 1KB) + (changelog_entries × 200B) + (weekly_stats × 100B) + (metric_values × 80B) + index_overhead (20% of data), excluding WAL journal files
- **SC-008**: App startup time remains under 2 seconds initial page load budget with database
- **SC-009**: Full test suite passes with zero failures after replacing JSON with database persistence
- **SC-010**: Database schema supports future migrations without breaking changes to existing data

## Scope & Boundaries *(optional)*

### In Scope

- SQLite database as replacement for JSON file persistence
- Automatic migration from JSON to database with backup
- Profile-based data isolation in database tables
- TTL expiration for cache entries
- Database integrity validation and repair
- Transaction management for data consistency
- Export/import functionality for backup/restore
- Database schema versioning for future migrations

### Out of Scope

- Remote database support (PostgreSQL, MySQL) - SQLite only for this feature
- Database encryption at rest (future security enhancement)
- Real-time sync between multiple devices (single-user local database)
- Database compression or optimization features
- Multi-user concurrent write scenarios (app designed for single user)
- Cloud backup of database file (user can manually backup file)

## Dependencies & Assumptions *(optional)*

### Dependencies

- SQLite library already available in Python standard library (`sqlite3`)
- Existing JSON file structure is well-documented and stable
- All JSON files use consistent schema across app versions

### Assumptions

- Users run app on systems with file write permissions to project directory
- Database file can be stored in project root without permission issues
- SQLite performance is sufficient for expected data volumes (<10,000 records per table)
- Users do not manually edit JSON files between app versions
- Database file size under 100MB is acceptable for local storage
- Single user operates the app at a time (no simultaneous multi-user access)

## Risk Assessment *(optional)*

### Technical Risks

- **Data Loss During Migration** (High Impact, Low Likelihood): Mitigate with automatic JSON backups before migration and rollback mechanism
- **Performance Regression** (Medium Impact, Medium Likelihood): Mitigate with benchmarking and query optimization, ensure <100ms response times
- **Database Corruption** (High Impact, Low Likelihood): Mitigate with integrity checks on startup, automatic repair, and backup/restore functionality
- **Schema Evolution Complexity** (Medium Impact, High Likelihood): Mitigate with versioned schema and migration scripts for future upgrades

### User Impact Risks

- **Breaking Changes for Advanced Users** (Low Impact, Low Likelihood): Users who manually edit JSON files will need to use export/import instead
- **Learning Curve for Troubleshooting** (Low Impact, Medium Likelihood): Users accustomed to editing JSON files must learn database export/import commands

## Testing Strategy *(optional)*

### Unit Tests

- Test database connection management (open, close, error handling)
- Test CRUD operations for each entity (profiles, queries, settings, cache)
- Test migration logic with sample JSON files
- Test TTL expiration for cache entries
- Test transaction rollback on errors
- Test database integrity validation

### Integration Tests

- Test end-to-end migration from JSON to database with realistic data
- Test profile switching with database persistence
- Test concurrent database access from multiple threads
- Test app startup with existing database vs first-time database creation
- Test export to JSON and import from JSON roundtrip

### Performance Tests

- Benchmark database read operations vs JSON file reads
- Benchmark database write operations vs JSON file writes
- Test database performance with 1000+ cached issues
- Test migration performance with large JSON files (>10MB)

### User Acceptance Tests

- Verify existing user workflows work identically with database
- Verify profile creation, switching, and deletion
- Verify JIRA cache refresh and expiration
- Verify metrics snapshot history preservation
- Verify settings persistence across app restarts
