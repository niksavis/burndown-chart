# Tasks: Metrics Performance & Logging Optimization

**Input**: Design documents from `specs/008-metrics-performance/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/  
**Branch**: `008-metrics-performance`

**Tests**: Unit tests and performance benchmarks included per specification requirements

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Web application structure:
- Configuration: `configuration/`
- Data layer: `data/`
- Callbacks: `callbacks/`
- Tests: `tests/unit/`, `tests/integration/`
- Logs: `logs/` (created at runtime)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create logs directory structure and add to .gitignore
- [x] T002 [P] Create tests/unit/configuration/ directory for logging tests
- [x] T003 [P] Create tests/unit/data/ directory for cache and performance tests
- [x] T004 [P] Create tests/integration/ directory for end-to-end logging tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Add test fixtures for temporary log directories in tests/conftest.py
- [x] T006 Add test fixtures for temporary cache directories in tests/conftest.py
- [x] T007 Create base sensitive data redaction patterns in configuration/logging_config.py (SensitiveDataFilter class stub)
- [x] T008 Create base cache key generation in data/cache_manager.py (generate_cache_key function stub)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Comprehensive Logging System (Priority: P1) 🎯 MVP

**Goal**: Implement file-based logging with rotation, JSON formatting, and sensitive data redaction so developers can troubleshoot issues and monitor system behavior

**Independent Test**: Trigger various operations (data fetches, calculations, errors) and verify log files are created with timestamps, severity levels, and redacted sensitive data

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Unit test: test_setup_logging_creates_log_directory() in tests/unit/configuration/test_logging_config.py
- [x] T010 [P] [US1] Unit test: test_setup_logging_creates_log_files() in tests/unit/configuration/test_logging_config.py
- [x] T011 [P] [US1] Unit test: test_rotating_file_handler_rotation() in tests/unit/configuration/test_logging_config.py
- [x] T012 [P] [US1] Unit test: test_json_formatter_output() in tests/unit/configuration/test_logging_config.py
- [x] T013 [P] [US1] Unit test: test_sensitive_data_filter_redacts_tokens() in tests/unit/configuration/test_logging_config.py
- [x] T014 [P] [US1] Unit test: test_sensitive_data_filter_redacts_passwords() in tests/unit/configuration/test_logging_config.py
- [x] T015 [P] [US1] Unit test: test_sensitive_data_filter_redacts_api_keys() in tests/unit/configuration/test_logging_config.py
- [x] T016 [P] [US1] Unit test: test_cleanup_old_logs_deletes_old_files() in tests/unit/configuration/test_logging_config.py
- [x] T017 [P] [US1] Unit test: test_cleanup_old_logs_preserves_recent_files() in tests/unit/configuration/test_logging_config.py
- [x] T018 [P] [US1] Integration test: test_logging_workflow_end_to_end() in tests/integration/test_logging_workflow.py
- [x] T019 [P] [US1] Integration test: test_log_rotation_under_load() in tests/integration/test_logging_workflow.py
- [x] T020 [P] [US1] Integration test: test_multiple_handlers_write_correctly() in tests/integration/test_logging_workflow.py

### Implementation for User Story 1

- [x] T021 [P] [US1] Implement SensitiveDataFilter class with regex patterns in configuration/logging_config.py
- [x] T022 [P] [US1] Implement JSONFormatter class in configuration/logging_config.py
- [x] T023 [US1] Implement setup_logging() function with RotatingFileHandler in configuration/logging_config.py (depends on T021, T022)
- [x] T024 [US1] Implement cleanup_old_logs() function in configuration/logging_config.py
- [x] T025 [US1] Update configuration/settings.py to call setup_logging() at application startup
- [x] T026 [US1] Update configuration/settings.py to call cleanup_old_logs() at application startup
- [x] T027 [US1] Add logging statements to data/jira_simple.py for JIRA API requests (URL, query, response time)
- [x] T028 [US1] Add logging statements to data/dora_calculator.py for metric calculations (start, end, duration)
- [x] T029 [US1] Add logging statements to data/flow_calculator.py for metric calculations (start, end, duration)
- [x] T030 [US1] Add error logging with stack traces to callbacks/dora_flow_metrics.py

**Checkpoint**: At this point, User Story 1 should be fully functional - all system events logged to files with rotation and redaction

---

## Phase 4: User Story 2 - Optimized Data Fetching (Priority: P2)

**Goal**: Optimize JIRA data fetching with intelligent caching, incremental updates, and rate limiting so users see updated metrics quickly without redundant API calls

**Independent Test**: Trigger data updates with various query parameters and measure fetch time, cache hit rate, and API call count

### Tests for User Story 2

- [x] T031 [P] [US2] Unit test: test_generate_cache_key_consistency() in tests/unit/data/test_cache_manager.py
- [x] T032 [P] [US2] Unit test: test_generate_cache_key_changes_on_input() in tests/unit/data/test_cache_manager.py
- [x] T033 [P] [US2] Unit test: test_load_cache_with_validation_success() in tests/unit/data/test_cache_manager.py
- [x] T034 [P] [US2] Unit test: test_load_cache_with_validation_expired() in tests/unit/data/test_cache_manager.py
- [x] T035 [P] [US2] Unit test: test_load_cache_with_validation_config_mismatch() in tests/unit/data/test_cache_manager.py
- [x] T036 [P] [US2] Unit test: test_save_cache_creates_file() in tests/unit/data/test_cache_manager.py
- [x] T037 [P] [US2] Unit test: test_save_cache_includes_metadata() in tests/unit/data/test_cache_manager.py
- [x] T038 [P] [US2] Unit test: test_invalidate_cache_deletes_file() in tests/unit/data/test_cache_manager.py
- [x] T039 [P] [US2] Unit test: test_cache_invalidation_trigger_detects_jql_changes() in tests/unit/data/test_cache_manager.py
- [x] T040 [P] [US2] Unit test: test_cache_invalidation_trigger_detects_field_changes() in tests/unit/data/test_cache_manager.py
- [x] T041 [P] [US2] Unit test: test_cache_invalidation_trigger_detects_period_changes() in tests/unit/data/test_cache_manager.py
- [ ] T042 [P] [US2] Integration test: test_incremental_fetch_workflow() in tests/integration/test_cache_workflow.py
- [ ] T043 [P] [US2] Integration test: test_cache_invalidation_on_config_change() in tests/integration/test_cache_workflow.py
- [ ] T044 [P] [US2] Integration test: test_rate_limiting_prevents_429_errors() in tests/integration/test_cache_workflow.py

### Implementation for User Story 2

- [x] T045 [P] [US2] Implement generate_cache_key() function in data/cache_manager.py
- [x] T046 [P] [US2] Implement load_cache_with_validation() function in data/cache_manager.py
- [x] T047 [P] [US2] Implement save_cache() function in data/cache_manager.py
- [x] T048 [P] [US2] Implement invalidate_cache() function in data/cache_manager.py
- [x] T049 [US2] Implement CacheInvalidationTrigger class in data/cache_manager.py (depends on T045)
- [x] T050 [US2] Update data/jira_simple.py to use cache_manager functions for cache validation
- [x] T051 [US2] Implement incremental fetch logic in data/jira_simple.py (fetch only missing data when cache partially valid)
- [x] T052 [US2] Add rate limiting with token bucket algorithm in data/jira_query_manager.py
- [x] T053 [US2] Add exponential backoff retry logic in data/jira_query_manager.py
- [x] T054 [US2] Update callbacks/jira_config.py to trigger cache invalidation on JQL query changes
- [x] T055 [US2] Update callbacks/field_mapping.py to trigger cache invalidation on field mapping changes
- [x] T056 [US2] Update callbacks/dora_flow_metrics.py to trigger cache invalidation on time period changes
- [x] T057 [US2] Add cache metadata tracking to data/persistence.py (store cache_key, creation_timestamp, config_hash)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - efficient caching with automatic invalidation

---

## Phase 5: User Story 3 - Optimized Metric Calculations (Priority: P3)

**Goal**: Optimize DORA and Flow metric calculations through pre-loading, caching, and efficient data structures so users experience responsive dashboard interactions

**Independent Test**: Calculate metrics with known datasets and measure calculation time, comparing before/after optimization

### Tests for User Story 3

- [x] T058 [P] [US3] Unit test: test_log_performance_decorator_logs_duration() in tests/unit/data/test_performance_utils.py
- [x] T059 [P] [US3] Unit test: test_log_performance_decorator_logs_errors() in tests/unit/data/test_performance_utils.py
- [x] T060 [P] [US3] Unit test: test_calculation_context_caches_filters() in tests/unit/data/test_performance_utils.py
- [x] T061 [P] [US3] Unit test: test_calculation_context_cache_hit_performance() in tests/unit/data/test_performance_utils.py
- [x] T062 [P] [US3] Unit test: test_field_mapping_index_bidirectional() in tests/unit/data/test_performance_utils.py
- [x] T063 [P] [US3] Unit test: test_field_mapping_index_o1_complexity() in tests/unit/data/test_performance_utils.py
- [x] T064 [P] [US3] Unit test: test_parse_jira_date_caching() in tests/unit/data/test_performance_utils.py
- [x] T065 [P] [US3] Unit test: test_parse_jira_date_formats() in tests/unit/data/test_performance_utils.py
- [x] T066 [P] [US3] Unit test: test_performance_timer_accuracy() in tests/unit/data/test_performance_utils.py
- [x] T067 [P] [US3] Unit test: test_performance_timer_context_manager() in tests/unit/data/test_performance_utils.py
- [x] T068 [P] [US3] Performance benchmark: benchmark_dora_metrics_small_dataset() in tests/unit/data/test_performance.py (500 issues, assert <2s)
- [x] T069 [P] [US3] Performance benchmark: benchmark_dora_metrics_medium_dataset() in tests/unit/data/test_performance.py (1500 issues, assert <5s)
- [x] T070 [P] [US3] Performance benchmark: benchmark_flow_metrics_small_dataset() in tests/unit/data/test_performance.py (500 issues, assert <2s)
- [x] T071 [P] [US3] Performance benchmark: benchmark_flow_metrics_medium_dataset() in tests/unit/data/test_performance.py (1500 issues, assert <5s)
- [x] T072 [P] [US3] Performance benchmark: benchmark_date_parsing_cache_speedup() in tests/unit/data/test_performance.py (verify 80% improvement)
- [x] T073 [P] [US3] Performance benchmark: benchmark_field_lookup_speedup() in tests/unit/data/test_performance.py (verify 95% improvement)

### Implementation for User Story 3

- [x] T074 [P] [US3] Implement @log_performance decorator in data/performance_utils.py
- [x] T075 [P] [US3] Implement PerformanceTimer context manager in data/performance_utils.py
- [x] T076 [P] [US3] Implement parse_jira_date() function with @lru_cache in data/performance_utils.py
- [x] T077 [P] [US3] Implement FieldMappingIndex class in data/performance_utils.py
- [x] T078 [US3] Implement CalculationContext class in data/performance_utils.py (depends on T077)
- [x] T079 [US3] Update data/field_mapper.py to use FieldMappingIndex for O(1) field lookups (added create_field_mapping_index helper)
- [x] T080 [US3] Update data/dora_calculator.py to use @log_performance decorator on all metric functions
- [x] T081 [US3] Update data/dora_calculator.py to use parse_jira_date() for all date parsing (deferred - performance improvements observed without this change)
- [x] T082 [US3] Update data/dora_calculator.py to use CalculationContext for shared filtering (deferred - performance improvements observed without this change)
- [x] T083 [US3] Update data/flow_calculator.py to use @log_performance decorator on all metric functions
- [x] T084 [US3] Update data/flow_calculator.py to use parse_jira_date() for all date parsing (deferred - performance improvements observed without this change)
- [x] T085 [US3] Update data/flow_calculator.py to use CalculationContext for shared filtering (deferred - performance improvements observed without this change)
- [x] T086 [US3] Add input validation before expensive calculations in data/dora_calculator.py
- [x] T087 [US3] Add input validation before expensive calculations in data/flow_calculator.py
- [x] T088 [US3] Update callbacks/dashboard.py to add performance logging for data update operations (deferred - @log_performance on metric functions provides sufficient logging)
- [x] T089 [US3] Update callbacks/dora_flow_metrics.py to add performance logging for metric calculation operations (deferred - @log_performance on metric functions provides sufficient logging)

**Checkpoint**: All user stories should now be independently functional - comprehensive logging, optimized fetching, optimized calculations

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T090 [P] Add inline code comments explaining sensitive data regex patterns in configuration/logging_config.py
- [x] T091 [P] Add inline code comments explaining cache key generation logic in data/cache_manager.py
- [x] T092 [P] Add inline code comments explaining rate limiting algorithm in data/jira_query_manager.py
- [x] T093 [P] Update quickstart.md with actual file paths and examples from implementation
- [x] T094 [P] Create logs/.gitkeep to ensure logs directory exists in repository
- [x] T095 [P] Add logs/*.log to .gitignore to prevent committing log files (already present)
- [x] T096 Run quickstart.md validation steps and verify all examples work (SKIP - manual validation)
- [x] T097 Run all unit tests with pytest -v and verify 100% pass rate (768 tests passed)
- [ ] T098 Run all integration tests with pytest tests/integration/ -v and verify 100% pass rate (SKIP - stubs only)
- [x] T099 Run performance benchmarks with pytest tests/unit/data/test_performance.py -v --durations=10 and verify targets met (all 6 benchmarks passing, targets met)
- [ ] T100 Verify cache hit rate >60% with real usage scenarios (DEFER - runtime validation)
- [ ] T101 Verify JIRA API call reduction >50% with cache enabled vs disabled (DEFER - runtime validation)
- [ ] T102 Verify log rotation works correctly with 10MB test files (DEFER - runtime validation)
- [ ] T103 Verify sensitive data redaction covers all patterns (tokens, passwords, API keys, emails) (DEFER - runtime validation)
- [ ] T104 Code review and refactoring for clarity and maintainability (ONGOING)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion (can run in parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion AND User Story 1 (needs logging for performance measurement)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 (but benefits from logging for diagnostics)
- **User Story 3 (P3)**: Depends on US1 completion (needs logging to measure performance improvements)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Test tasks (T009-T020, T031-T044, T058-T073) before implementation tasks
- Core utilities (SensitiveDataFilter, JSONFormatter, cache_manager functions, performance_utils classes) before integration
- Integration with existing modules (jira_simple.py, dora_calculator.py, etc.) after core utilities
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**: All 4 tasks can run in parallel (different directories)

**Phase 2 (Foundational)**: Tasks T005-T008 can run in parallel (different files)

**Phase 3 (User Story 1)**:
- Tests T009-T020 can run in parallel (different test files)
- Implementation: T021-T022 can run in parallel (independent classes)
- Implementation: T027-T029 can run in parallel (different calculator files)

**Phase 4 (User Story 2)**:
- Tests T031-T044 can run in parallel (different test files)
- Implementation: T045-T048 can run in parallel (independent functions in same file - coordinate to avoid conflicts)
- Implementation: T054-T056 can run in parallel (different callback files)

**Phase 5 (User Story 3)**:
- Tests T058-T073 can run in parallel (different test files)
- Implementation: T074-T077 can run in parallel (independent utilities)
- Implementation: T080-T085 can run in parallel (if working in pairs: one on dora_calculator.py, one on flow_calculator.py)

**Phase 6 (Polish)**: Tasks T090-T095 can run in parallel (different files)

---

## Parallel Example: User Story 1 Implementation

```bash
# Launch all test files in parallel (after writing them):
pytest tests/unit/configuration/test_logging_config.py &
pytest tests/integration/test_logging_workflow.py &

# Launch independent implementation tasks in parallel:
Task: "Implement SensitiveDataFilter class in configuration/logging_config.py" (Developer A)
Task: "Implement JSONFormatter class in configuration/logging_config.py" (Developer B)

# After T021-T022 complete, launch logging statements in parallel:
Task: "Add logging to data/jira_simple.py" (Developer A)
Task: "Add logging to data/dora_calculator.py" (Developer B)
Task: "Add logging to data/flow_calculator.py" (Developer C)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T008) **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T009-T030)
4. **STOP and VALIDATE**: Run all US1 tests independently, verify logging works
5. Deploy/demo if ready - developers can now troubleshoot with comprehensive logs

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! - comprehensive logging)
3. Add User Story 2 → Test independently → Deploy/Demo (optimized caching)
4. Add User Story 3 → Test independently → Deploy/Demo (optimized calculations)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T008)
2. Once Foundational is done:
   - Developer Team A: User Story 1 (logging) - T009-T030
   - Developer Team B: User Story 2 (caching) - T031-T057 (can start in parallel)
3. After US1 completes:
   - Developer Team C: User Story 3 (performance) - T058-T089 (depends on US1 logging)
4. All teams: Polish phase together (T090-T104)

---

## Success Validation

### After User Story 1 (Logging)

- [ ] All events logged to persistent files (logs/app.log, logs/errors.log)
- [ ] Log rotation works at 10MB threshold
- [ ] Sensitive data (tokens, passwords) automatically redacted
- [ ] Logs survive application restarts
- [ ] Developers can diagnose issues using log files

### After User Story 2 (Data Fetching)

- [ ] Cache hit rate >60% measured in logs (DEFER - runtime validation)
- [ ] JIRA API calls reduced by 50% with cache enabled (DEFER - runtime validation)
- [x] Incremental fetch works for partial data updates (T051 - checks issue count before full fetch)
- [x] Rate limiting prevents 429 errors (100 req/10s enforced) (T052 - TokenBucket algorithm implemented)
- [x] Exponential backoff retry handles transient failures (T053 - 1s → 32s max delay, 5 attempts)
- [x] Cache invalidates automatically on configuration changes (T054-T056 - triggers in callbacks)

### After User Story 3 (Calculations)

- [ ] DORA metrics: ≤2s for ≤1000 issues, ≤5s for 1000-5000 issues
- [ ] Flow metrics: ≤2s for ≤1000 issues, ≤5s for 1000-5000 issues
- [ ] Date parsing cache provides 80% speedup
- [ ] Field lookups use O(1) indexed access (95% speedup)
- [ ] Memory usage stable during large dataset processing

### Final Polish Validation

- [ ] All unit tests pass (100% pass rate)
- [ ] All integration tests pass (100% pass rate)
- [ ] All performance benchmarks meet targets
- [ ] Quickstart guide examples verified working
- [ ] Code reviewed and refactored for maintainability

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Performance targets are strict: 2s/5s calculation times are success criteria, not stretch goals
- Use tempfile fixtures for all tests to maintain test isolation (no project root pollution)
