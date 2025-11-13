# Tasks: Profile & Query Management System

**Input**: Design documents from `/specs/011-profile-workspace-switching/`
**Prerequisites**: plan.md (required), spec.md (required), concept.md (technical design)

**Tests**: Tests are included as this feature requires comprehensive validation for data migration, cache isolation, and performance targets.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses Python Dash PWA structure at repository root:
- Core modules: `data/`, `ui/`, `callbacks/`, `visualization/`
- Tests: `tests/unit/`, `tests/integration/`
- Configuration: `configuration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and test fixtures for profile/query isolation

- [x] T001 Create `tests/fixtures/temp_profiles_dir.py` fixture with tempfile.TemporaryDirectory() for test isolation
- [x] T002 Create `tests/fixtures/sample_profile_data.py` fixture with realistic profile/query test data
- [x] T003 [P] Create `tests/fixtures/sample_jira_cache.py` fixture with mock JIRA response data
- [x] T004 [P] Update pytest.ini to include profile management test markers (profile_tests, migration_tests, performance_tests)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Path abstraction layer that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete - all existing code depends on this

- [x] T005 Add path abstraction functions to `data/persistence.py`: get_active_profile_workspace(), get_active_query_workspace(), get_profile_file_path(filename)
- [x] T006 Update `data/persistence.py::load_app_settings()` to use get_profile_file_path("app_settings.json")
- [x] T007 Update `data/persistence.py::save_app_settings()` to use get_profile_file_path("app_settings.json") with atomic write pattern
- [x] T008 Update `data/persistence.py::load_project_data()` to use get_profile_file_path("project_data.json")
- [x] T009 Update `data/persistence.py::save_project_data()` to use get_profile_file_path("project_data.json") with atomic write pattern
- [x] T010 [P] Create `tests/unit/data/test_persistence_path_abstraction.py` with tests for backward compatibility (profiles.json missing = legacy mode)
- [x] T011 [P] Run full existing test suite to verify path abstraction doesn't break existing features

**Checkpoint**: Path abstraction layer complete - existing code works transparently with or without profiles

---

## Phase 3: User Story 5 - First-Time Migration (Priority: P1) 🎯 MVP Foundation

**Goal**: Automatically migrate existing users' data to profiles/default/ on first run without data loss

**Independent Test**: Simulate pre-profile installation (root-level cache files), start app, verify all files moved to profiles/default/ without corruption

**Why First**: This must be implemented before other user stories so existing users don't lose data when profile features are deployed. It's the foundation for safe rollout.

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T012 [P] [US5] Create `tests/integration/test_migration.py::test_migrate_to_profiles_moves_all_files()` - verify app_settings.json, jira_cache.json, project_data.json, metrics_snapshots.json, cache/ all move to profiles/default/queries/default/
- [x] T013 [P] [US5] Create `tests/integration/test_migration.py::test_migration_creates_backup()` - verify .backup copies created before migration
- [x] T014 [P] [US5] Create `tests/integration/test_migration.py::test_migration_idempotent()` - run migration twice, verify second run does nothing
- [x] T015 [P] [US5] Create `tests/integration/test_migration.py::test_migration_data_preservation()` - compare checksums before/after migration
- [x] T016 [P] [US5] Create `tests/integration/test_migration.py::test_migration_rollback_on_failure()` - simulate disk error, verify rollback from backup
- [x] T017 [P] [US5] Create `tests/integration/test_migration.py::test_migration_completes_under_5_seconds()` - test with 50MB cache data

### Implementation for User Story 5

- [x] T018 [US5] Create `data/migration.py::migrate_to_profiles()` function - detect profiles.json missing, create profiles/default/ directory structure
- [x] T019 [US5] Implement backup creation in `data/migration.py::create_migration_backup()` - copy root files to *.backup before moving
- [x] T020 [US5] Implement file move logic in `data/migration.py::move_root_files_to_default_profile()` - move app_settings.json, jira_cache.json, project_data.json, metrics_snapshots.json, cache/ directory
- [x] T021 [US5] Implement profiles.json creation in `data/migration.py::initialize_profiles_registry()` - create profiles.json with default profile as active
- [x] T022 [US5] Implement rollback function in `data/migration.py::rollback_migration()` - restore from .backup files if migration fails
- [x] T023 [US5] Add migration hook to `app.py` startup - call migrate_to_profiles() before app initialization with error handling
- [x] T024 [US5] Add migration status logging in `data/migration.py` - log migration start, completion, failure, rollback
- [x] T025 [US5] Implement `data/migration.py::cleanup_migration_artifacts()` - archive obsolete jira_query_profiles.json to _migrated_backup/

**Checkpoint**: Existing users can upgrade without data loss - migration tested with 50MB cache in <5 seconds

---

## Phase 4: User Story 1 - Switch Between Queries Within Profile (Priority: P1) 🎯 MVP Core

**Goal**: Enable instant (<50ms) switching between different time periods using same forecast settings

**Independent Test**: Create profile with PERT 1.5 and deadline 2025-12-31, add two queries with different JQL, switch between them, verify <50ms and same PERT/deadline used

**Why This Priority**: This is the core value proposition - eliminating 3-6 minute cache invalidation delays

### Tests for User Story 1 ⚠️

- [x] T026 [P] [US1] Create `tests/unit/data/test_query_manager.py::test_create_query_validates_name_unique_within_profile()` - ensure query names unique per profile (case-insensitive)
- [x] T027 [P] [US1] Create `tests/unit/data/test_query_manager.py::test_create_query_creates_dedicated_cache_directory()` - verify profiles/{profile_id}/queries/{query_id}/ created
- [x] T028 [P] [US1] Create `tests/unit/data/test_query_manager.py::test_switch_query_updates_active_query_id()` - verify profiles.json updated with new active_query_id
- [x] T029 [P] [US1] Create `tests/unit/data/test_query_manager.py::test_delete_query_prevents_deleting_last_query()` - verify error when trying to delete only query
- [x] T030 [P] [US1] Create `tests/unit/data/test_query_manager.py::test_delete_query_prevents_deleting_active_query()` - verify error when trying to delete active query
- [ ] T031 [P] [US1] Create `tests/integration/test_cache_isolation.py::test_query_cache_isolation()` - create 2 queries, verify cache files don't overlap
- [x] T032 [P] [US1] Create `tests/integration/test_profile_switching_workflow.py::test_query_switch_latency_under_50ms()` - measure time from switch to dashboard reload
- [ ] T033 [P] [US1] Create `tests/integration/test_profile_switching_workflow.py::test_query_switch_preserves_cache()` - switch away and back, verify no JIRA API calls

### Implementation for User Story 1

- [x] T034 [P] [US1] Create `data/query_manager.py` module with Query class (to_dict, from_dict methods)
- [x] T035 [US1] Implement `data/query_manager.py::create_query()` - validate name unique within profile, create directory structure, initialize query.json
- [x] T036 [US1] Implement `data/query_manager.py::switch_query()` - update active_query_id in profiles.json and profile.json with atomic write
- [x] T037 [US1] Implement `data/query_manager.py::delete_query()` - validate safety checks (not active, not last query), remove directory
- [ ] T038 [US1] Implement `data/query_manager.py::duplicate_query()` - copy query workspace, reset timestamps, create new query ID
- [x] T039 [US1] Implement `data/query_manager.py::get_queries_for_profile()` - load queries list from profile.json
- [x] T040 [US1] Create `ui/query_selector.py` component - query dropdown (8 cols) with button group (4 cols), responsive stack on mobile, includes empty state for no queries
- [x] T041 [US1] Add query management buttons to `ui/query_selector.py` - button group with [Create] [Duplicate] [Delete] buttons, disabled states for delete
- [x] T042 [US1] Create `ui/query_create_modal.py` component - centered Bootstrap modal with name, JQL, description fields, real-time name validation ("✓ available" or "✗ exists")
- [ ] T043 [US1] Create `ui/query_delete_modal.py` component - centered Bootstrap modal with type-to-confirm deletion pattern
- [x] T044 [US1] Create `callbacks/query_management.py::handle_query_switch()` callback - switch query, show skeleton screen, trigger page reload, populate JQL editor with query's JQL
- [x] T045 [US1] Create `callbacks/query_management.py::handle_create_query()` callback - validate form with real-time name check, call create_query(), update dropdown, show success message
- [x] T046 [US1] Create `callbacks/query_management.py::handle_delete_query()` callback - validate confirmation text matches query name, call delete_query(), update dropdown
- [ ] T047 [US1] Create `callbacks/query_management.py::handle_duplicate_query()` callback - call duplicate_query(), update dropdown, switch to new query
- [ ] T047a [US1] Create `callbacks/query_management.py::validate_query_name_realtime()` callback - check name uniqueness while user types in creation modal
- [x] T048 [US1] Integrate query selector into `ui/settings_panel.py` - replace "Saved Queries" section, position below profile selector, above JQL editor
- [ ] T049 [US1] Add "Last Updated" timestamp display to query selector tooltip in `ui/query_selector.py`
- [ ] T050 [US1] Add real-time JQL syntax validation to query creation modal in `ui/query_create_modal.py` - show error message for invalid syntax

**Checkpoint**: Users can create multiple queries and switch between them in <50ms with cache preservation

---

## Phase 5: User Story 2 - Create New Query in Profile (Priority: P1) 🎯 MVP Completion

**Goal**: Enable creating multiple JQL query variations within profile to analyze different data slices

**Independent Test**: Create profile, add new query with custom JQL, verify query inherits profile settings and has dedicated cache

**Why This Priority**: This enables the core use case - analyzing multiple query variations with consistent settings

### Implementation for User Story 2 (Minimal - Core Logic Already in US1)

- [ ] T051 [US2] Add query limit validation (max 100 queries per profile) to `data/query_manager.py::create_query()`
- [ ] T052 [US2] Add disk space check to `data/query_manager.py::create_query()` - warn if <100MB available
- [ ] T053 [US2] Add query count display to profile selector in `ui/profile_selector.py` - show "X queries" badge
- [ ] T054 [US2] Add query examples/templates to `ui/query_create_modal.py` - prepopulate with "Last 12 Weeks", "Last 52 Weeks" options
- [ ] T055 [US2] Add JQL validation error messages to `ui/query_create_modal.py` - display specific syntax errors

**Checkpoint**: Users can efficiently create multiple query variations with helpful templates and validation

---

## Phase 6: User Story 3 - Switch Between Profiles (Priority: P2)

**Goal**: Enable switching between profiles representing different organizations with different settings

**Independent Test**: Create two profiles with different JIRA URLs and PERT factors, switch between them, verify settings don't cross-contaminate

### Tests for User Story 3 ⚠️

- [ ] T056 [P] [US3] Create `tests/unit/data/test_profile_manager.py::test_create_profile_validates_name_unique()` - ensure profile names unique (case-insensitive)
- [ ] T057 [P] [US3] Create `tests/unit/data/test_profile_manager.py::test_create_profile_creates_directory_structure()` - verify profiles/{profile_id}/ and queries/ subdirectory
- [ ] T058 [P] [US3] Create `tests/unit/data/test_profile_manager.py::test_switch_profile_updates_active_profile_id()` - verify profiles.json updated
- [ ] T059 [P] [US3] Create `tests/unit/data/test_profile_manager.py::test_switch_profile_loads_most_recent_query()` - verify active_query_id set to last_used query
- [ ] T060 [P] [US3] Create `tests/unit/data/test_profile_manager.py::test_delete_profile_prevents_deleting_last_profile()` - verify error when only one profile
- [ ] T061 [P] [US3] Create `tests/unit/data/test_profile_manager.py::test_delete_profile_prevents_deleting_active_profile()` - verify error when active
- [ ] T062 [P] [US3] Create `tests/integration/test_profile_switching_workflow.py::test_profile_switch_latency_under_100ms()` - measure profile switch time
- [ ] T063 [P] [US3] Create `tests/integration/test_cache_isolation.py::test_profile_cache_isolation()` - create 2 profiles, verify no cross-contamination

### Implementation for User Story 3

- [ ] T064 [P] [US3] Create `data/profile_manager.py` module with Profile class (to_dict, from_dict methods)
- [ ] T065 [US3] Implement `data/profile_manager.py::load_profiles_metadata()` - load profiles.json with schema validation
- [ ] T066 [US3] Implement `data/profile_manager.py::save_profiles_metadata()` - atomic write to profiles.json (temp file + rename)
- [ ] T067 [US3] Implement `data/profile_manager.py::get_active_profile()` - return active Profile object from profiles.json
- [ ] T068 [US3] Implement `data/profile_manager.py::create_profile()` - validate name, create directory, initialize profile.json, add to registry
- [ ] T069 [US3] Implement `data/profile_manager.py::switch_profile()` - update active_profile_id, update last_used timestamp, set active_query_id to most recent
- [ ] T070 [US3] Implement `data/profile_manager.py::delete_profile()` - validate safety checks (not active, not last), remove directory
- [ ] T071 [US3] Implement `data/profile_manager.py::duplicate_profile()` - copy profile workspace, reset timestamps, create new profile ID
- [ ] T072 [US3] Create `ui/profile_selector.py` component - profile dropdown (8 cols) with button group (4 cols), responsive stack on mobile, tooltip showing JIRA URL/PERT/query count on profile name hover
- [ ] T073 [US3] Add profile management buttons to `ui/profile_selector.py` - button group with [Create] [Duplicate] [Delete] buttons, disabled states for delete
- [ ] T074 [US3] Create `ui/profile_create_modal.py` component - centered Bootstrap modal with name, description, clone_from_active toggle, real-time name validation ("✓ available" or "✗ exists")
- [ ] T075 [US3] Create `ui/profile_delete_modal.py` component - centered Bootstrap modal with type-to-confirm deletion pattern
- [ ] T076 [US3] Create `callbacks/profile_management.py::handle_profile_switch()` callback - switch profile, show skeleton screen, trigger page reload, load most recent query from profile
- [ ] T077 [US3] Create `callbacks/profile_management.py::handle_create_profile()` callback - validate form with real-time name check, call create_profile(), update dropdown, show success message
- [ ] T078 [US3] Create `callbacks/profile_management.py::handle_delete_profile()` callback - validate confirmation text matches profile name, call delete_profile(), update dropdown
- [ ] T079 [US3] Create `callbacks/profile_management.py::handle_duplicate_profile()` callback - call duplicate_profile(), update dropdown, switch to new profile
- [ ] T079a [US3] Create `callbacks/profile_management.py::validate_profile_name_realtime()` callback - check name uniqueness while user types in creation modal
- [ ] T080 [US3] Integrate profile selector into `ui/settings_panel.py` - position at top of JIRA Integration section, above query selector
- [ ] T081 [US3] Add profile metadata tooltip to `ui/profile_selector.py` - show JIRA URL, PERT factor, query count on profile name hover/tap

**Checkpoint**: Users can manage multiple profiles with different JIRA instances and switch between them in <100ms

---

## Phase 7: User Story 4 - Create New Profile from Existing (Priority: P2)

**Goal**: Enable duplicating profiles to quickly set up similar project configurations

**Independent Test**: Duplicate profile, verify JIRA config copied, modify duplicate's settings, confirm original unchanged

### Implementation for User Story 4 (Minimal - Core Logic Already in US3)

- [ ] T082 [US4] Add profile limit validation (max 50 profiles) to `data/profile_manager.py::create_profile()`
- [ ] T083 [US4] Add clone queries option to `ui/profile_create_modal.py` - checkbox to copy queries when duplicating
- [ ] T084 [US4] Implement query cloning in `data/profile_manager.py::duplicate_profile()` - if clone_queries=True, copy all queries with new IDs
- [ ] T085 [US4] Add profile templates/examples to `ui/profile_create_modal.py` - prepopulate with common JIRA configurations
- [ ] T086 [US4] Add profile export/import helpers to `data/profile_manager.py` - strip credentials before export

**Checkpoint**: Users can efficiently duplicate profiles with optional query cloning for similar project setup

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T087 [P] Add profile/query validation schema to `data/schema.py` - JSON schema for profile.json and query.json
- [ ] T088 [P] Add error recovery for corrupted profile workspace in `data/profile_manager.py::detect_corrupted_profile()` - auto-switch to default
- [ ] T089 [P] Add profile switching cancellation logic in `callbacks/profile_management.py` - cancel in-progress JIRA fetch when switching
- [ ] T090 [P] Add helpful tooltips to profile/query labels in `ui/profile_selector.py` and `ui/query_selector.py` - explain Profile vs Query difference (using existing help_system.py pattern)
- [ ] T091 [P] Add onboarding tutorial for first-time profile users in `ui/profile_onboarding_modal.py` - show centered Bootstrap modal on first profile creation explaining profile/query hierarchy
- [ ] T092 [P] Update README.md with profile/query management section - user guide with screenshots
- [ ] T093 [P] Create troubleshooting guide in docs/troubleshooting-profiles.md - common issues and solutions
- [ ] T094 [P] Add profile analytics to `data/profile_manager.py::get_profile_statistics()` - track profile usage, cache sizes
- [ ] T095 [P] Implement profile workspace cleanup in `data/profile_manager.py::cleanup_profile_workspace()` - archive old query caches
- [ ] T096 Add performance monitoring to profile/query switches - log slow operations (>100ms profile, >50ms query)
- [ ] T097 Run full integration test suite with realistic data (50 profiles, 100 queries each)
- [ ] T098 Run performance test suite to validate all success criteria (SC-001 through SC-012)
- [ ] T099 Code cleanup and refactoring - remove obsolete comments, unused imports
- [ ] T100 Security review - validate JIRA token handling, prevent path traversal attacks

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 5 (Phase 3)**: Depends on Foundational - MUST complete first (migration foundation)
- **User Story 1 (Phase 4)**: Depends on Foundational + US5 - Core MVP functionality
- **User Story 2 (Phase 5)**: Depends on US1 (reuses query management code)
- **User Story 3 (Phase 6)**: Can start after Foundational (independent of US1/US2)
- **User Story 4 (Phase 7)**: Depends on US3 (reuses profile duplication code)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 5 (P1 - Migration)**: Can start after Foundational - No dependencies on other stories (MUST complete first)
- **User Story 1 (P1 - Query Switching)**: Can start after US5 - No dependencies on other stories
- **User Story 2 (P1 - Query Creation)**: Depends on US1 (reuses query_manager.py)
- **User Story 3 (P2 - Profile Switching)**: Can start after Foundational - Independent of US1/US2
- **User Story 4 (P2 - Profile Duplication)**: Depends on US3 (reuses profile_manager.py)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/managers before UI components
- UI components before callbacks
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 Setup**: All 4 tasks can run in parallel (different fixtures)
- **Phase 2 Foundational**: T010, T011 can run in parallel after T005-T009 complete
- **User Story 5 Tests**: T012-T017 all parallel (different test functions)
- **User Story 1 Tests**: T026-T033 all parallel (different test files/functions)
- **User Story 1 UI**: T040, T042, T043 parallel (different component files)
- **User Story 3 Tests**: T056-T063 all parallel (different test functions)
- **User Story 3 UI**: T072, T074, T075 parallel (different component files)
- **Phase 8 Polish**: Most tasks parallel (different files/concerns)

---

## Parallel Example: User Story 1 Implementation

```bash
# After tests are written and failing, launch parallel implementation tasks:

# Parallel group 1 (UI components - different files):
Task T040: "Create ui/query_selector.py component"
Task T042: "Create ui/query_create_modal.py component"  
Task T043: "Create ui/query_delete_modal.py component"

# Sequential (data layer must complete first):
Task T034: "Create data/query_manager.py module"
Task T035-T039: "Implement query management functions"

# Parallel group 2 (callbacks - after data layer ready):
Task T044: "handle_query_switch callback"
Task T045: "handle_create_query callback"
Task T046: "handle_delete_query callback"
Task T047: "handle_duplicate_query callback"
```

---

## Implementation Strategy

### MVP First (US5 + US1 + US2 Only)

1. Complete Phase 1: Setup (fixtures and test infrastructure)
2. Complete Phase 2: Foundational (path abstraction - CRITICAL)
3. Complete Phase 3: User Story 5 (migration - protect existing users)
4. Complete Phase 4: User Story 1 (query switching - core value)
5. Complete Phase 5: User Story 2 (query creation - complete MVP)
6. **STOP and VALIDATE**: Test migration + query switching workflow end-to-end
7. Deploy/demo if ready (users can now switch queries, existing data preserved)

### Incremental Delivery

1. Foundation (Phase 1-2) → Path abstraction ready
2. Add US5 (Migration) → Existing users protected
3. Add US1 (Query Switching) → Core feature usable
4. Add US2 (Query Creation) → MVP complete! 🎯
5. Add US3 (Profile Switching) → Multi-tenancy enabled
6. Add US4 (Profile Duplication) → Efficiency improvements
7. Polish (Phase 8) → Production-ready

### Parallel Team Strategy

With 3 developers after Foundational phase completes:

1. Team completes Setup + Foundational together (Phase 1-2)
2. Developer A: User Story 5 (Migration) - MUST complete first
3. Once US5 done, parallel work begins:
   - Developer A: User Story 1 + 2 (Query management)
   - Developer B: User Story 3 + 4 (Profile management)
   - Developer C: Polish tasks (Phase 8) + integration testing

---

## Success Criteria Validation

### Performance Tests (Must Pass)

- [ ] SC-001: Query switch <50ms (test_query_switch_latency_under_50ms)
- [ ] SC-002: Profile switch <100ms (test_profile_switch_latency_under_100ms)
- [ ] SC-003: Cache hit rate >90% (test_query_switch_preserves_cache)
- [ ] SC-007: Profile creation <500ms (manual validation)
- [ ] SC-008: Query creation <500ms (manual validation)
- [ ] SC-012: Migration <5s for 50MB (test_migration_completes_under_5_seconds)

### Data Integrity Tests (Must Pass)

- [ ] SC-005: Migration data preservation 100% (test_migration_data_preservation)
- [ ] SC-010: Cache isolation 100% (test_query_cache_isolation, test_profile_cache_isolation)
- [ ] SC-011: Prevent accidental deletion 100% (test_delete_query_prevents_*, test_delete_profile_prevents_*)

### Scale Tests (Must Pass)

- [ ] SC-006: Support 50 profiles × 100 queries (manual load test)

### User Workflow Tests (Must Pass)

- [ ] SC-004: Compare queries <10s total (manual timed workflow)
- [ ] SC-009: Create 5 queries <3min (manual timed workflow)

---

## Notes

- **[P]** tasks = different files, no dependencies - safe to parallelize
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Migration (US5) MUST complete before other user stories to protect existing users
- Query management (US1/US2) and Profile management (US3/US4) can proceed in parallel after US5
- Tests follow pytest patterns with tempfile.TemporaryDirectory() for isolation
- All file operations use atomic writes (temp file + rename) to prevent corruption
- Windows PowerShell environment - use Test-Path, Remove-Item, etc. (no Unix commands)
- Virtual environment activation required for all Python/pytest commands
