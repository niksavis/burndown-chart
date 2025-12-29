# Tasks: SQLite Database Migration

**Input**: Design documents from `/specs/015-sqlite-persistence/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not explicitly requested in spec - tests optional for this feature. Performance benchmarks included instead.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database foundation

- [ ] T001 Create persistence layer directory structure (data/persistence/, data/migration/)
- [ ] T002 [P] Create database module in data/database.py with connection management
- [ ] T003 [P] Create schema initialization script in data/migration/schema.py
- [ ] T004 Verify zero errors after Phase 1 setup

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core persistence abstraction and database infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement PersistenceBackend interface from contracts/persistence_interface.py in data/persistence/**init**.py
- [ ] T006 Implement get_db_connection() context manager with WAL mode in data/database.py
- [ ] T007 [P] Implement SQLiteBackend class in data/persistence/sqlite_backend.py (stub all methods)
- [ ] T008 [P] Implement JSONBackend class in data/persistence/json_backend.py (legacy fallback, stub all methods)
- [ ] T009 Create backend factory functions (get_backend, set_backend) in data/persistence/**init**.py
- [ ] T010 Implement database schema creation (10 normalized tables) in data/migration/schema.py per data-model.md: profiles, queries, app_state, jira_issues, jira_changelog_entries, project_statistics, project_scope, metrics_data_points, task_progress with 30+ indexes
- [ ] T011 Implement database integrity check in data/database.py (check_database_integrity function)
- [ ] T012 Add logging configuration for database operations in configuration/logging_config.py
- [ ] T013 Verify zero errors after Phase 2 foundation

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Seamless Data Migration (Priority: P1) 🎯 MVP

**Goal**: Existing users automatically migrate from JSON to SQLite on first launch with all data preserved

**Independent Test**: Create sample JSON files with known data, launch app, verify database contains identical data structure/values

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement backup creation in data/migration/backup.py (copy profiles/ to backups/migration-{timestamp}/)
- [ ] T015 [P] [US1] Implement JSON-to-database migrator in data/migration/migrator.py (migrate_profile function)
- [ ] T016 [US1] Implement app_state table operations in data/persistence/sqlite_backend.py (get_app_state, set_app_state)
- [ ] T017 [US1] Implement profiles table operations in data/persistence/sqlite_backend.py (get_profile, save_profile)
- [ ] T018 [US1] Implement queries table operations in data/persistence/sqlite_backend.py (get_query, save_query, list_queries)
- [ ] T019 [US1] Implement jira_issues table operations in data/persistence/sqlite_backend.py (get_issues, save_issues_batch, delete_expired_issues)
- [ ] T020 [US1] Implement jira_changelog_entries table operations in data/persistence/sqlite_backend.py (get_changelog_entries, save_changelog_batch)
- [ ] T021 [US1] Implement project_statistics table operations in data/persistence/sqlite_backend.py (get_statistics, save_statistics_batch)
- [ ] T022 [US1] Implement project_scope table operations in data/persistence/sqlite_backend.py (get_scope, save_scope)
- [ ] T023 [US1] Implement metrics_data_points table operations in data/persistence/sqlite_backend.py (get_metric_values, save_metrics_batch)
- [ ] T024 [US1] Implement task_progress table operations in data/persistence/sqlite_backend.py (get_task_progress, save_task_progress, clear_task_progress)
- [ ] T025 [US1] Implement legacy JSON blob methods for migration compatibility in data/persistence/sqlite_backend.py (get_jira_cache, save_jira_cache, get_project_data, save_project_data, get_metrics_snapshots)
- [ ] T026 [US1] Implement post-migration validator in data/migration/validator.py (validate_migration function)
- [ ] T027 [US1] Implement migration orchestrator in data/migration/migrator.py (run_migration_if_needed function)
- [ ] T028 [US1] Add migration status tracking to app_state table (migration_complete flag)
- [ ] T029 [US1] Integrate migration check into app.py startup (call run_migration_if_needed before Dash server starts)
- [ ] T030 [US1] Add rollback mechanism for failed migrations in data/migration/migrator.py
- [ ] T031 [US1] Verify SC-001: Migration completes <5s for 1000 cached issues (performance benchmark)
- [ ] T032 [US1] Verify SC-004: Zero data loss during migration (validation test)

**Checkpoint**: Users with existing JSON files successfully migrate to database on first launch

---

## Phase 4: User Story 2 - Fast Data Operations (Priority: P2)

**Goal**: Database CRUD operations perform equal or better than JSON file operations

**Independent Test**: Benchmark database operations against JSON file operations with realistic data (100+ cached issues, 50+ snapshots)

### Implementation for User Story 2

- [ ] T033 [P] [US2] Create performance benchmark suite in tests/performance/ directory
- [ ] T034 [P] [US2] Add composite indexes to database schema in data/migration/schema.py per data-model.md indexing strategy
- [ ] T035 [US2] Implement prepared statement caching in data/persistence/sqlite_backend.py
- [ ] T036 [US2] Implement batch insert operations for normalized tables in data/persistence/sqlite_backend.py (already done in T019-T023)
- [ ] T037 [US2] Optimize profile load query with index hints in data/persistence/sqlite_backend.py (get_profile)
- [ ] T038 [US2] Optimize query switch with composite index on (profile_id, query_id) in queries table
- [ ] T039 [US2] Update data/profile_manager.py to use get_backend() for profile operations
- [ ] T040 [US2] Update data/query_manager.py to use get_backend() for query operations
- [ ] T041 [US2] Update data/jira_simple.py to use get_backend() normalized methods (get_issues, save_issues_batch)
- [ ] T042 [US2] Update data/metrics_snapshots.py to use get_backend() normalized methods (get_metric_values, save_metrics_batch)
- [ ] T043 [US2] Verify SC-002: Database reads complete <50ms for 100 records (benchmark)
- [ ] T044 [US2] Verify SC-003: Database writes complete <100ms (benchmark)
- [ ] T045 [US2] Verify SC-005: 1000+ cached issues handled without degradation (load test)
- [ ] T046 [US2] Verify SC-008: App startup <2s with database (integration test)

**Checkpoint**: Database operations meet or exceed performance targets

---

## Phase 5: User Story 3 - Multi-Profile Database Management (Priority: P2)

**Goal**: Profile-based workspace architecture maintained with database isolation

**Independent Test**: Create two profiles with different configs, verify Profile A changes don't affect Profile B

### Implementation for User Story 3

- [ ] T047 [P] [US3] Implement profile creation in data/persistence/sqlite_backend.py with unique ID generation
- [ ] T048 [P] [US3] Implement profile deletion with CASCADE DELETE for related data in data/persistence/sqlite_backend.py (delete_profile)
- [ ] T049 [US3] Implement profile listing with last_used sorting in data/persistence/sqlite_backend.py (list_profiles)
- [ ] T050 [US3] Implement profile switching with last_used update in data/persistence/sqlite_backend.py
- [ ] T051 [US3] Implement query deletion with CASCADE DELETE in data/persistence/sqlite_backend.py (delete_query)
- [ ] T052 [US3] Update callbacks/profile_management.py to use get_backend() for profile CRUD
- [ ] T053 [US3] Update callbacks/query_management.py to use get_backend() for query CRUD
- [ ] T054 [US3] Implement profile export to JSON directory structure in data/import_export.py (export_profile function - normalized to JSON)
- [ ] T055 [US3] Implement profile import from JSON directory structure in data/import_export.py (import_profile function)
- [ ] T056 [US3] Add foreign key constraints validation to schema in data/migration/schema.py
- [ ] T057 [US3] Test profile isolation: create 2 profiles, verify data separation (integration test)
- [ ] T058 [US3] Test profile deletion: verify CASCADE DELETE removes all related data (integration test)

**Checkpoint**: Multi-profile workspace fully functional with database

---

## Phase 6: User Story 4 - Concurrent Access Safety (Priority: P3)

**Goal**: Multiple app instances or background processes safely access database without corruption

**Independent Test**: Launch two app instances, perform write operations from both, verify data integrity and no lock errors

### Implementation for User Story 4

- [ ] T059 [P] [US4] Enable WAL mode in get_db_connection() context manager in data/database.py
- [ ] T060 [P] [US4] Implement transaction management in SQLiteBackend (begin_transaction, commit, rollback) in data/persistence/sqlite_backend.py
- [ ] T061 [US4] Add connection timeout configuration (10s default) in data/database.py
- [ ] T062 [US4] Implement automatic retry logic for locked database in data/persistence/sqlite_backend.py
- [ ] T063 [US4] Add connection-per-request pattern enforcement (verify no global connections) via code review
- [ ] T064 [US4] Implement graceful handling of OperationalError (database locked) in data/persistence/sqlite_backend.py
- [ ] T065 [US4] Test concurrent reads from multiple threads (integration test with threading module)
- [ ] T066 [US4] Test concurrent writes from multiple threads (integration test with threading module)
- [ ] T067 [US4] Verify SC-006: Concurrent access completes without deadlocks (stress test)
- [ ] T068 [US4] Document WAL file requirements (copy all 3 files) in quickstart.md (already done)

**Checkpoint**: Database safely handles concurrent access scenarios

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T069 [P] Update copilot-instructions.md with persistence layer rules (already done via update-agent-context.ps1)
- [ ] T070 [P] Add database file size monitoring in data/database.py (get_database_size function)
- [ ] T071 [P] Implement cleanup_expired_cache() background task in data/persistence/sqlite_backend.py (use delete_expired_issues)
- [ ] T072 [P] Add database schema versioning to app_state table (schema_version = "1.0")
- [ ] T073 Code cleanup: Remove dead JSON file utilities following Boy Scout Rule and Constitution Principle VI
- [ ] T074 Run full test suite and verify all existing tests pass with database backend
- [ ] T075 Performance audit: Profile database operations and verify all SC-XXX targets met
- [ ] T076 [P] Verify SC-007: Database file size grows proportionally per formula in spec.md
- [ ] T077 [P] Verify SC-009: Full test suite passes with zero failures
- [ ] T078 [P] Verify SC-010: Schema supports future migrations without breaking changes
- [ ] T079 Documentation review: Verify quickstart.md examples work correctly with normalized methods
- [ ] T080 Security review: Verify no SQL injection vulnerabilities (parameterized queries only)
- [ ] T081 Final Constitution Check: Verify all 6 principles still PASS post-implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - Migration is MVP foundation
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) - Needs working database before optimization
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) - Can run parallel with US2 after US1 complete
- **User Story 4 (Phase 6)**: Depends on User Story 1 (Phase 3) - Can run parallel with US2/US3 after US1 complete
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: CRITICAL - Must complete first. All other stories need working database.
- **User Story 2 (P2)**: Depends on US1. Optimizes existing database operations.
- **User Story 3 (P2)**: Depends on US1. Can run parallel with US2.
- **User Story 4 (P3)**: Depends on US1. Can run parallel with US2/US3.

**Recommended Sequence**: US1 → (US2 || US3 || US4) → Polish

### Within Each User Story

- **US1 Migration**: Backup → Schema → Backend CRUD methods → Migrator → Validator → Integration → Benchmarks
- **US2 Performance**: Benchmarks → Indexes → Optimizations → Integration → Validation
- **US3 Multi-Profile**: CRUD operations → Import/Export → Integration → Testing
- **US4 Concurrency**: WAL mode → Transactions → Retry logic → Concurrent tests

### Parallel Opportunities

#### Phase 1 (Setup)

All Phase 1 tasks can run in parallel:

```bash
# Create directories and stub files simultaneously
T002 [P] data/database.py &
T003 [P] data/migration/schema.py &
wait
```

#### Phase 2 (Foundational)

After T005/T006 complete, these can run in parallel:

```bash
T007 [P] sqlite_backend.py &
T008 [P] json_backend.py &
wait
```

#### User Story 1 (after T016 app_state complete)

All backend CRUD implementation tasks can run in parallel:

```bash
T017 [P] profiles operations &
T018 [P] queries operations &
T019 [P] jira_cache operations &
T020 [P] jira_changelog operations &
T021 [P] project_data operations &
T022 [P] metrics_snapshots operations &
T023 [P] task_progress operations &
wait
```

#### User Story 2

Performance benchmarks and optimizations can run in parallel:

```bash
T031 [P] benchmark suite &
T032 [P] add indexes &
wait
```

#### User Story 3

CRUD operations can run in parallel:

```bash
T045 [P] profile creation &
T046 [P] profile deletion &
wait
```

#### User Story 4

Setup tasks can run in parallel:

```bash
T057 [P] WAL mode &
T058 [P] transaction management &
wait
```

#### Phase 7 (Polish)

Many polish tasks are independent:

```bash
T067 [P] documentation &
T068 [P] monitoring &
T069 [P] cleanup task &
T070 [P] schema versioning &
T074 [P] size verification &
T075 [P] test verification &
T076 [P] schema validation &
wait
```

### Critical Path

```
T001-T004 (Setup)
  ↓
T005-T013 (Foundational) ← BLOCKING
  ↓
T014-T030 (US1 Migration) ← MVP CRITICAL PATH
  ↓
┌─────────────┬───────────────┬────────────────┐
│  T031-T044  │   T045-T056   │   T057-T066    │
│  (US2 Perf) │  (US3 Multi)  │  (US4 Concur)  │
└─────────────┴───────────────┴────────────────┘
  ↓
T067-T079 (Polish)
```

**Minimum Viable Product (MVP)**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only)

---

## Implementation Strategy

### MVP First Approach

1. **Week 1**: Phase 1 (Setup) + Phase 2 (Foundation) - Working database infrastructure
2. **Week 2**: Phase 3 (User Story 1) - Migration working, users can upgrade
3. **Week 3**: Phase 4 (User Story 2) - Performance optimization
4. **Week 4**: Phase 5-6 (User Stories 3-4) - Multi-profile + concurrency
5. **Week 5**: Phase 7 (Polish) - Final validation

### Incremental Delivery

- **Milestone 1**: Database foundation (Phase 1-2) - Ready for migration implementation
- **Milestone 2**: Migration MVP (Phase 3) - Existing users can upgrade safely
- **Milestone 3**: Performance parity (Phase 4) - Database as fast as JSON
- **Milestone 4**: Feature complete (Phase 5-7) - All user stories delivered

### Risk Mitigation

- **Data Loss Risk**: T014 (backup) MUST complete before any migration (T015+)
- **Performance Risk**: T029/T041-T043 benchmarks validate targets before release
- **Corruption Risk**: T011 (integrity check) + T024 (validator) catch issues early
- **Rollback Plan**: T028 (rollback mechanism) enables safe recovery from failed migrations

---

## Success Metrics

- [ ] SC-001: Migration <5s for 1000 issues (T029 benchmark)
- [ ] SC-002: Read operations <50ms (T041 benchmark)
- [ ] SC-003: Write operations <100ms (T042 benchmark)
- [ ] SC-004: Zero data loss (T030 validation)
- [ ] SC-005: 1000+ issues handled (T043 load test)
- [ ] SC-006: No deadlocks (T065 stress test)
- [ ] SC-007: File size proportional (T074 validation)
- [ ] SC-008: Startup <2s (T044 integration)
- [ ] SC-009: All tests pass (T075 verification)
- [ ] SC-010: Schema extensible (T076 validation)

---

**Total Tasks**: 81 (updated from 79 - added normalized method implementation tasks)  
**MVP Tasks (Phase 1-3)**: 32 (updated from 30)  
**Parallel Opportunities**: 25+ tasks marked [P]  
**Estimated Effort**: 5-8 weeks (single developer)

---

**Version**: 1.0  
**Last Updated**: 2025-12-23
