# Implementation Plan: SQLite Database Migration

**Branch**: `015-sqlite-persistence` | **Date**: 2025-12-23 (Updated: 2025-12-29) | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-sqlite-persistence/spec.md`

## Implementation Status (as of 2025-12-29)

**Current Phase**: Phase 3 User Story 1 (Migration MVP) - CORE COMPLETE  
**Progress**: 48/80 tasks complete (60%) - All critical implementation done  
**Next Steps**: Integration tasks (T039-T042, T052-T053) or tests/benchmarks

**✅ Completed Phases**:
- Phase 1: Setup (4/4 tasks - 100%)
- Phase 2: Foundation (9/9 tasks - 100%)
- Phase 3: US1 Migration MVP (17/19 tasks - 89%, core complete)

**🔄 In Progress**:
- Phase 4: US2 Performance (2/13 tasks - integration pending)
- Phase 5: US3 Multi-Profile (7/12 tasks - callbacks pending)
- Phase 6: US4 Concurrent Access (5/10 tasks - tests pending)
- Phase 7: Polish (4/13 tasks - validation pending)

**Key Achievements**:
- ✅ 10-table normalized schema with 30+ indexes operational
- ✅ Full migration orchestrator with backup/restore/validation working
- ✅ All CRUD operations implemented in SQLiteBackend
- ✅ Migration integrated into app.py startup
- ✅ WAL mode, connection management, schema versioning complete

**Remaining Work**: See [tasks.md](tasks.md) for detailed task status

## Summary

Migrate all JSON file-based persistence to SQLite database while maintaining profile-based workspace architecture. Existing users will automatically migrate on first launch after upgrade with all data preserved. Implementation includes database abstraction layer to support future persistence backends, maintaining <100ms performance budget for user interactions.

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: sqlite3 (standard library), Dash, Plotly, Waitress  
**Storage**: SQLite database (profiles/burndown.db), replacing JSON files  
**Testing**: pytest, tempfile for test isolation  
**Target Platform**: Windows 10+, local desktop application  
**Project Type**: Single project (web UI with local server)  
**Performance Goals**: Database operations <100ms, migration <5s for 1000 issues  
**Constraints**: Zero data loss during migration, backward compatibility with existing profiles/  
**Scale/Scope**: Single-user local app, up to 10k JIRA issues cached, 50 profiles max

### Current Persistence Architecture

**JSON Files (per profile/query)**:
- `profiles.json` - Registry of profiles and active selection
- `profiles/{profile_id}/profile.json` - Profile settings (JIRA config, field mappings, PERT settings)
- `profiles/{profile_id}/queries/{query_id}/query.json` - Query metadata (JQL string)
- `profiles/{profile_id}/queries/{query_id}/jira_cache.json` - Cached JIRA issues
- `profiles/{profile_id}/queries/{query_id}/jira_changelog_cache.json` - Cached changelog data
- `profiles/{profile_id}/queries/{query_id}/project_data.json` - Statistics, scope calculations
- `profiles/{profile_id}/queries/{query_id}/metrics_snapshots.json` - Historical DORA/Flow metrics
- `task_progress.json` - Runtime task progress (root level)

**Key Modules Managing Persistence**:
- `data/profile_manager.py` - Profile lifecycle, path resolution
- `data/query_manager.py` - Query lifecycle, fast switching (<50ms)
- `data/jira_simple.py` - JIRA cache read/write
- `data/metrics_snapshots.py` - Metrics history persistence
- `data/import_export.py` - Profile backup/restore

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Phase 0) ✅

All principles PASS - see rationale below. Proceed to Phase 0 research.

### Post-Phase 1 Re-evaluation ✅

**Re-evaluated**: 2025-12-23 after Phase 1 design completion  
**Status**: All principles continue to PASS with design artifacts validated

### Principle I: Layered Architecture ✅

**Status**: PASS  
**Rationale**: Persistence logic implemented in `data/persistence/` layer with abstract `PersistenceBackend` interface (see `contracts/persistence_interface.py`). Callbacks remain unchanged, delegating to data layer functions. Clean separation: business logic → persistence interface → backend implementation.

### Principle II: Test Isolation ✅

**Status**: PASS  
**Rationale**: All database tests will use `tempfile.TemporaryDirectory()` for isolated test databases. Existing test infrastructure already uses tempfile patterns. Quickstart.md documents testing pattern with temporary database fixture.

### Principle III: Performance Budgets ✅

**Status**: PASS  
**Rationale**: SQLite with indexed queries provides <10ms profile load, <50ms query switch (see `data-model.md` indexing strategy). Migration completes <5s for 1000 cached issues per SC-001. WAL mode enables concurrent access for Dash multi-callback architecture.

### Principle IV: Simplicity & Reusability (KISS + DRY) ✅

**Status**: PASS  
**Rationale**: Repository pattern (`PersistenceBackend` ABC with 20+ methods) provides clean separation between business logic and storage backend. Reduces code duplication across profile/query managers. Future backends (JSON legacy, remote DB) can implement same interface. JSON columns used strategically for complex nested data (jira_config, field_mappings).

### Principle V: Data Privacy & Security ✅

**Status**: PASS  
**Rationale**: No customer data in database schema examples or documentation. All examples use placeholder profile names ("Acme Corp", "Kafka"), generic field IDs ("customfield_10001"), example domains ("jira.example.com"). Database location documented as `profiles/burndown.db` with no external identifiers.

### Principle VI: Defensive Refactoring ✅

**Status**: PASS  
**Rationale**: Migration preserves existing JSON files as backups to `backups/migration-{timestamp}/` before database conversion. Atomic migration with validation + rollback on failure. Dead code (JSON-specific utilities) will be removed following defensive refactoring protocol after migration stability confirmed. JSONBackend maintained as fallback during transition period.

## Project Structure

### Documentation (this feature)

```text
specs/015-sqlite-persistence/
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions, migration strategies
├── data-model.md        # Phase 1: Database schema, entity relationships
├── quickstart.md        # Phase 1: Developer guide for database operations
├── contracts/           # Phase 1: Database abstraction interface
│   └── persistence_interface.py  # Abstract base class for storage backends
└── checklists/
    └── requirements.md  # Spec validation (completed)
```

### Source Code (repository root)

```text
data/
├── database.py          # NEW: Database connection, schema, queries
├── persistence/         # NEW: Abstraction layer
│   ├── __init__.py
│   ├── base.py          # Abstract persistence interface
│   ├── sqlite_backend.py    # SQLite implementation
│   └── json_backend.py      # Legacy JSON (for rollback)
├── migration/           # NEW: JSON to SQLite migration
│   ├── __init__.py
│   ├── migrator.py      # Migration orchestrator
│   └── validators.py    # Data integrity checks
├── profile_manager.py   # MODIFIED: Use persistence layer
├── query_manager.py     # MODIFIED: Use persistence layer
├── jira_simple.py       # MODIFIED: Use persistence layer for cache
├── metrics_snapshots.py # MODIFIED: Use persistence layer
└── import_export.py     # MODIFIED: Export/import database

tests/
├── unit/
│   └── data/
│       ├── test_database.py         # NEW: Database operations
│       ├── test_persistence_layer.py # NEW: Abstraction layer
│       ├── test_migration.py        # NEW: JSON to SQLite migration
│       ├── test_profile_manager.py  # MODIFIED: Test with DB backend
│       └── test_query_manager.py    # MODIFIED: Test with DB backend
└── integration/
    └── test_migration_endtoend.py   # NEW: Full migration flow

profiles/
└── burndown.db          # NEW: SQLite database file
```

**Structure Decision**: Single project structure maintained. New `data/persistence/` directory abstracts storage backend. `data/migration/` handles one-time JSON-to-SQLite conversion. Existing `data/` modules modified to use persistence layer instead of direct JSON I/O.

## Complexity Tracking

> No Constitution violations. KISS principle applied with abstraction layer.

| Design Decision               | Rationale                                                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Persistence abstraction layer | Enables future storage backends (remote DB, cloud sync) without rewriting business logic. Maintains SOLID principles. |
| Separate migration module     | One-time migration logic isolated from runtime persistence code. Simplifies testing and reduces coupling.             |
| Preserve JSON backup          | User safety - rollback possible if database corruption or migration bugs. Follows defensive programming.              |

## Phase 0: Outline & Research

### Research Tasks

1. **SQLite Best Practices for Python**
   - Thread safety and connection pooling for Dash callbacks
   - Transaction management patterns
   - Database file locking on Windows
   - WAL (Write-Ahead Logging) vs default journaling mode

2. **Schema Design for Profile/Query Hierarchy**
   - Foreign key relationships (Profile → Query → Cache)
   - Indexing strategy for fast query switching (<50ms)
   - JSON column vs normalized tables for field_mappings
   - TTL implementation for cache expiration

3. **Migration Strategy**
   - Atomic migration with rollback on failure
   - Incremental vs all-at-once migration
   - Data validation before/after migration
   - Handling malformed JSON files

4. **Performance Optimization**
   - Prepared statements vs raw SQL
   - Batch inserts for migration
   - Index strategy for common queries
   - Database file size management

5. **Persistence Abstraction Pattern**
   - Repository pattern vs DAO (Data Access Object)
   - Abstract base class design
   - Error handling and retry logic
   - Testing strategy for abstraction layer

### Output: research.md

Document findings for each research task with:
- **Decision**: Technology/approach chosen
- **Rationale**: Why this choice over alternatives
- **Alternatives Considered**: What was evaluated and rejected
- **Implementation Notes**: Key details for Phase 1

## Phase 1: Design & Contracts

### Deliverables

1. **data-model.md**
   - Entity-Relationship Diagram (text/Mermaid)
   - Table schemas with columns, types, constraints
   - Foreign key relationships
   - Indexing strategy
   - Data migration mapping (JSON → SQLite tables)

2. **contracts/persistence_interface.py**
   - Abstract base class for persistence backends
   - CRUD method signatures for all entities
   - Error handling contracts
   - Transaction management interface

3. **quickstart.md**
   - Developer guide for database operations
   - Example queries for common use cases
   - Testing patterns with temporary databases
   - Migration checklist for developers

### Agent Context Update

Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` to add:
- SQLite database location: `profiles/burndown.db`
- Persistence layer modules: `data/persistence/`, `data/database.py`
- Migration completed status (post-implementation)

## Phase 2: Implementation Tasks (NOT created by this command)

Phase 2 will be handled by `/speckit.tasks` command after Phase 1 design artifacts are complete.

---

## Appendix: Key Questions for Research

1. **Thread Safety**: How to safely access SQLite from multiple Dash callbacks?
2. **Migration Atomicity**: How to ensure all-or-nothing migration with automatic rollback?
3. **Cache TTL**: Best way to implement expiration (database trigger vs application logic)?
4. **Query Performance**: Will indexed SQLite queries meet <50ms query switching requirement?
5. **File Portability**: Can users still move `profiles/` directory to different machines?
6. **Backup Strategy**: How to export database to JSON for user backups?
7. **Schema Evolution**: How to handle future schema changes without breaking existing databases?
8. **Error Recovery**: What happens if database file is corrupted or deleted during runtime?
