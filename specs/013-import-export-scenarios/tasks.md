# Tasks: Enhanced Import/Export Options

**Feature**: 013-import-export-scenarios  
**Input**: Design documents from `/specs/013-import-export-scenarios/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and verification of existing infrastructure

- [ ] T001 Verify existing import/export foundation in data/import_export.py (T009 implementation)
- [ ] T002 Verify existing test fixtures use tempfile pattern in tests/conftest.py
- [ ] T003 [P] Review existing ExportManifest dataclass structure in data/import_export.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data layer functions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement strip_credentials() function in data/import_export.py with deep copy pattern
- [X] T005 [P] Add unit test test_strip_credentials_removes_token() in tests/unit/data/test_import_export.py
- [X] T006 [P] Add unit test test_strip_credentials_preserves_other_fields() in tests/unit/data/test_import_export.py
- [X] T007 Extend ExportManifest dataclass with export_mode field in data/import_export.py
- [X] T008 [P] Add unit test test_validate_import_data_format_check() in tests/unit/data/test_import_export.py
- [X] T009 Implement validate_import_data() function in data/import_export.py (4-stage validation)
- [X] T010 [P] Add unit test test_resolve_profile_conflict_overwrite() in tests/unit/data/test_import_export.py
- [X] T011 [P] Add unit test test_resolve_profile_conflict_merge() in tests/unit/data/test_import_export.py
- [X] T012 [P] Add unit test test_resolve_profile_conflict_rename() in tests/unit/data/test_import_export.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Share Configuration Without Credentials (Priority: P1) 🎯 MVP

**Goal**: Enable secure configuration sharing with token excluded by default

**Independent Test**: Export profile with default settings (token excluded), share the file, import on another system with own credentials

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement export_profile_with_mode() function with CONFIG_ONLY mode in data/import_export.py
- [X] T014 [P] [US1] Add unit test test_export_config_only_excludes_query_data() in tests/unit/data/test_import_export.py
- [X] T015 [P] [US1] Add unit test test_export_config_only_strips_token_by_default() in tests/unit/data/test_import_export.py
- [X] T016 [P] [US1] Add export mode radio buttons component in ui/import_export_panel.py (CONFIG_ONLY as default)
- [X] T017 [P] [US1] Add "Include JIRA Token" checkbox component in ui/import_export_panel.py (default: unchecked)
- [X] T018 [US1] Update export_profile_callback() in callbacks/import_export.py to accept mode and token params
- [X] T019 [US1] Implement show_token_warning_callback() in callbacks/import_export.py (trigger modal on checkbox)
- [X] T020 [P] [US1] Add token warning modal component in ui/import_export_panel.py with security consequences list
- [X] T021 [US1] Implement confirm_token_warning_callback() in callbacks/import_export.py (handle proceed/cancel)
- [X] T022 [US1] Add integration test test_config_only_export_excludes_cache_files() in tests/integration/test_import_export_scenarios.py
- [X] T023 [US1] Add integration test test_export_config_only_file_size_validation() in tests/integration/test_import_export_scenarios.py

**Checkpoint**: User Story 1 complete - can export configuration securely without credentials

---

## Phase 4: User Story 2 - Export Configuration Only for Team Standardization (Priority: P2)

**Goal**: Enable team standardization by sharing query definitions without data overhead

**Independent Test**: Export configuration-only, verify minimal file size, import on clean system, verify queries work when connected to JIRA

### Implementation for User Story 2

- [ ] T024 [P] [US2] Add unit test test_export_config_only_size_reduction() in tests/unit/data/test_import_export.py (verify 90%+ reduction)
- [ ] T025 [P] [US2] Update export_profile_callback() to show file size in success toast in callbacks/import_export.py
- [ ] T026 [US2] Update import_profile_callback() to detect CONFIG_ONLY mode in callbacks/import_export.py
- [ ] T027 [US2] Add toast notification logic for "Sync with JIRA to fetch data" message in callbacks/import_export.py
- [ ] T028 [US2] Add integration test test_config_only_import_prompts_for_token() in tests/integration/test_import_export_scenarios.py
- [ ] T029 [US2] Add integration test test_config_only_no_data_until_sync() in tests/integration/test_import_export_scenarios.py

**Checkpoint**: User Stories 1 AND 2 complete - can share configuration and standardize teams

---

## Phase 5: User Story 3 - Share Complete Snapshot for Offline Review (Priority: P2)

**Goal**: Enable offline analysis by exporting complete data snapshot

**Independent Test**: Export full data, import on disconnected system (no JIRA credentials), verify all charts/metrics render without "Update Data"

### Implementation for User Story 3

- [ ] T030 [P] [US3] Extend export_profile_with_mode() to support FULL_DATA mode in data/import_export.py
- [ ] T031 [P] [US3] Add unit test test_export_full_data_includes_query_data() in tests/unit/data/test_import_export.py
- [ ] T032 [P] [US3] Add unit test test_export_full_data_single_query_only() in tests/unit/data/test_import_export.py (not all queries)
- [ ] T033 [US3] Update export mode radio buttons to include "Full Profile with Data" option in ui/settings.py
- [ ] T034 [US3] Update export_profile_callback() to conditionally load query_data based on mode in callbacks/import_export.py
- [ ] T035 [US3] Update import_profile_callback() to write query_data files when present in callbacks/import_export.py
- [ ] T036 [US3] Add data age timestamp display logic after import in callbacks/import_export.py
- [ ] T037 [US3] Add integration test test_full_data_import_no_token_prompt() in tests/integration/test_import_export_scenarios.py
- [ ] T038 [US3] Add integration test test_full_data_charts_render_immediately() in tests/integration/test_import_export_scenarios.py

**Checkpoint**: User Stories 1, 2, AND 3 complete - full range of export modes available

---

## Phase 6: User Story 4 - Secure Sharing with Token Inclusion Option (Priority: P3)

**Goal**: Enable power users to backup/migrate with credentials included (explicit opt-in)

**Independent Test**: Export with token included, import on new system, verify immediate JIRA access without re-entering credentials

### Implementation for User Story 4

- [ ] T039 [P] [US4] Add unit test test_export_with_token_includes_credentials() in tests/unit/data/test_import_export.py
- [ ] T040 [P] [US4] Add unit test test_export_manifest_token_flag_consistency() in tests/unit/data/test_import_export.py
- [ ] T041 [US4] Update export_profile_with_mode() to conditionally call strip_credentials() in data/import_export.py
- [ ] T042 [US4] Update import_profile_callback() to skip token prompt when token present in callbacks/import_export.py
- [ ] T043 [US4] Add security warning tooltip near "Include Token" checkbox in ui/settings.py
- [ ] T044 [US4] Add integration test test_token_included_no_import_prompt() in tests/integration/test_import_export_scenarios.py
- [ ] T045 [US4] Add integration test test_token_warning_modal_shown_on_checkbox() in tests/integration/test_import_export_scenarios.py

**Checkpoint**: All user stories complete - all export scenarios supported

---

## Phase 7: Cross-Story Integration - Conflict Resolution (Foundational for all imports)

**Goal**: Handle profile name conflicts during import for all modes

**Independent Test**: Import file when profile exists, verify conflict modal with merge/overwrite/rename options

- [X] T046 Implement resolve_profile_conflict() function in data/import_export.py (overwrite/merge/rename strategies)
- [ ] T047 [P] Add unit test test_resolve_conflict_overwrite_strategy() in tests/unit/data/test_import_export.py
- [ ] T048 [P] Add unit test test_resolve_conflict_merge_preserves_token() in tests/unit/data/test_import_export.py
- [ ] T049 [P] Add unit test test_resolve_conflict_rename_appends_timestamp() in tests/unit/data/test_import_export.py
- [ ] T050 [P] Add conflict resolution modal component in ui/settings.py (radio: merge/overwrite/rename)
- [ ] T051 Update import_profile_callback() to detect conflicts and show modal in callbacks/import_export.py
- [ ] T052 Implement resolve_conflict_callback() in callbacks/import_export.py (handle button clicks)
- [ ] T053 Add integration test test_import_conflict_merge_strategy() in tests/integration/test_import_export_scenarios.py
- [ ] T054 Add integration test test_import_conflict_overwrite_strategy() in tests/integration/test_import_export_scenarios.py
- [ ] T055 Add integration test test_import_conflict_rename_strategy() in tests/integration/test_import_export_scenarios.py

**Checkpoint**: Conflict resolution complete - all import scenarios handle existing profiles gracefully

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Refinements, error handling, logging, documentation

- [ ] T056 [P] Add comprehensive logging for all import/export operations in data/import_export.py
- [ ] T057 [P] Add error handling with user-friendly messages in callbacks/import_export.py
- [ ] T058 [P] Add export operation to audit trail (FR-015) in data/import_export.py
- [ ] T059 [P] Verify all toast notifications follow existing pattern in ui/toast_notifications.py
- [ ] T060 [P] Update quickstart.md with manual testing checklist completion verification
- [ ] T061 Run full test suite: pytest tests/ -v
- [ ] T062 Verify zero type errors using get_errors tool
- [ ] T063 Run performance validation tests (export <3s, file size 90% reduction)
- [ ] T064 Manual smoke test: all scenarios from quickstart.md checklist
- [ ] T065 Update documentation if needed (readme.md feature mention)

---

## Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundation)
    ↓
    ├──→ Phase 3 (US1) ──┐
    ├──→ Phase 4 (US2) ──┤
    ├──→ Phase 5 (US3) ──┼──→ Phase 7 (Conflict Resolution)
    └──→ Phase 6 (US4) ──┘           ↓
                                 Phase 8 (Polish)
```

**User Story Completion Order**:
1. **MVP First**: US1 (P1) - Share Configuration Without Credentials
2. **Parallel**: US2 (P2) + US3 (P2) - Configuration-only + Full data modes
3. **Advanced**: US4 (P3) - Token inclusion option
4. **Integration**: Phase 7 - Conflict resolution (applies to all)

**Parallel Execution Opportunities**:
- Phase 2: T005-T006, T008, T010-T012 (unit tests)
- Phase 3: T013-T015 (data layer), T016-T017 (UI), T020 (modal), T022-T023 (tests)
- Phase 4: T024-T025, T028-T029
- Phase 5: T030-T032, T037-T038
- Phase 6: T039-T040, T044-T045
- Phase 7: T047-T049 (unit tests), T050 (modal)
- Phase 8: T056-T060 (documentation and polish)

---

## Implementation Strategy

### MVP Scope (User Story 1)
- Foundation (Phase 2) + Phase 3 tasks
- Delivers core value: secure configuration sharing
- Estimated: 1.5 hours

### Incremental Delivery
1. **Release 1**: US1 only (secure sharing)
2. **Release 2**: + US2 + US3 (all export modes)
3. **Release 3**: + US4 (token inclusion)
4. **Release 4**: + Phase 7 (conflict resolution)

### Testing Strategy
- Unit tests written alongside implementation (each phase)
- Integration tests after each user story phase
- Manual smoke testing after Phase 8

---

## Task Summary

- **Total Tasks**: 65
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundation)**: 9 tasks
- **Phase 3 (US1 - P1)**: 11 tasks
- **Phase 4 (US2 - P2)**: 6 tasks
- **Phase 5 (US3 - P2)**: 9 tasks
- **Phase 6 (US4 - P3)**: 7 tasks
- **Phase 7 (Conflict)**: 10 tasks
- **Phase 8 (Polish)**: 10 tasks

**Parallelizable Tasks**: 30 tasks marked with [P]

**Independent Test Criteria Met**:
- ✅ US1: Export + import without credentials
- ✅ US2: Minimal file size + sync required
- ✅ US3: Offline viewing without sync
- ✅ US4: Token inclusion + immediate access

**Estimated Total Time**: 2-3 hours for experienced developer (per quickstart.md)
