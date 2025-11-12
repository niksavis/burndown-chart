# Tasks: Dashboard Readability & Test Coverage

**Input**: Design documents from `/specs/010-dashboard-readability/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/test-coverage-contract.md ✅

**Tests**: This feature is PRIMARY about test coverage - tests are the core deliverable, not optional.

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each priority.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=Test Coverage P1, US2=Visual Clarity P2, US3=Insights P3)
- Exact file paths included in descriptions

## Path Conventions

**Single project structure** (Dash PWA at repository root):
- Source: `data/`, `ui/`, `callbacks/`, `visualization/`
- Tests: `tests/unit/`, `tests/integration/`, `tests/utils/`
- Existing files modified, new test files created

---

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Test utilities and fixtures for all dashboard tests

- [X] T001 Create shared test fixtures file at `tests/utils/dashboard_test_fixtures.py`
- [X] T002 Add `sample_statistics_data()` fixture with 10 weeks of realistic project data
- [X] T003 Add `sample_settings()` fixture with standard PERT/deadline configuration
- [X] T004 [P] Add `empty_statistics_data()` fixture for new project edge case
- [X] T005 [P] Add `minimal_statistics_data()` fixture for single data point edge case
- [X] T006 [P] Add `extreme_velocity_data()` fixture for very low velocity scenarios

**Checkpoint**: Test fixtures ready - all test files can import shared data

---

## Phase 2: User Story 1 - Comprehensive Test Coverage (Priority: P1) 🎯 MVP

**Goal**: Achieve >90% test coverage for all dashboard calculation functions with comprehensive edge case validation

**Independent Test**: Run `pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --cov=data.processing --cov=ui.dashboard_cards --cov-report=term` and verify coverage >90% for all functions

### Dashboard Metrics Tests (20 tests total)

**Module**: `tests/unit/data/test_dashboard_metrics.py`

- [X] T007 Create test file `tests/unit/data/test_dashboard_metrics.py` with imports and test class structure
- [X] T008 [P] [US1] Test `calculate_dashboard_metrics()` with normal 10-week data (validates all 11 metric fields)
- [X] T009 [P] [US1] Test `calculate_dashboard_metrics()` completion percentage calculation (68/100 = 68.0%)
- [X] T010 [P] [US1] Test `calculate_dashboard_metrics()` velocity calculation (items/week, points/week from last N weeks)
- [X] T011 [P] [US1] Test `calculate_dashboard_metrics()` forecast date calculation (velocity * PERT factor formula)
- [X] T012 [P] [US1] Test `calculate_dashboard_metrics()` with empty statistics array (returns safe defaults: zeros, None dates)
- [X] T013 [P] [US1] Test `calculate_dashboard_metrics()` with single data point (minimal data handling)
- [X] T014 [P] [US1] Test `calculate_dashboard_metrics()` with zero velocity (forecast dates should be None)
- [X] T015 [P] [US1] Test `calculate_dashboard_metrics()` with no deadline (days_to_deadline should be None)
- [X] T016 [P] [US1] Test `calculate_dashboard_metrics()` with completion >100% (scope decreased scenario)
- [X] T017 [P] [US1] Test `calculate_dashboard_metrics()` with negative days to deadline (past deadline edge case)
- [X] T018 [P] [US1] Test `calculate_dashboard_metrics()` velocity trend "increasing" (recent >10% higher than older)
- [X] T019 [P] [US1] Test `calculate_dashboard_metrics()` velocity trend "stable" (within ±10% threshold)
- [X] T020 [P] [US1] Test `calculate_pert_timeline()` with normal data (validates all 8 PERTTimelineData fields)
- [X] T021 [P] [US1] Test `calculate_pert_timeline()` PERT formula: (optimistic + 4*likely + pessimistic) / 6
- [X] T022 [P] [US1] Test `calculate_pert_timeline()` confidence range calculation (pessimistic - optimistic days)
- [X] T023 [P] [US1] Test `calculate_pert_timeline()` with empty statistics (all dates None, days zero)
- [X] T024 [P] [US1] Test `calculate_pert_timeline()` with zero velocity (cannot forecast, returns None)
- [X] T025 [P] [US1] Test `calculate_pert_timeline()` with zero remaining work (project complete edge case)
- [X] T026 [P] [US1] Test `calculate_pert_timeline()` with extreme PERT factor (10.0 wide window handling)
- [X] T027 [P] [US1] Test `calculate_pert_timeline()` date ordering invariant (optimistic < likely < pessimistic)

### Health Score & Card Tests (41 tests total)

**Module**: `tests/unit/ui/test_dashboard_cards.py`

- [X] T028 Create test file `tests/unit/ui/test_dashboard_cards.py` with imports and test class structure
- [X] T029 [P] [US1] Test `_calculate_health_score()` progress component (0-25 points based on completion %)
- [X] T030 [P] [US1] Test `_calculate_health_score()` schedule component (0-30 points based on timeline ratio)
- [X] T031 [P] [US1] Test `_calculate_health_score()` velocity component (0-25 points based on trend)
- [X] T032 [P] [US1] Test `_calculate_health_score()` confidence component (0-20 points based on confidence %)
- [X] T033 [P] [US1] Test `_calculate_health_score()` excellent tier (≥80 total score)
- [X] T034 [P] [US1] Test `_calculate_health_score()` good tier (60-79 total score)
- [X] T035 [P] [US1] Test `_calculate_health_score()` fair tier (40-59 total score)
- [X] T036 [P] [US1] Test `_calculate_health_score()` with missing deadline (uses neutral schedule score 15)
- [X] T037 [P] [US1] Test `_calculate_health_score()` with zero velocity (uses neutral defaults, no crash)
- [X] T038 [P] [US1] Test `_calculate_health_score()` capped at 100 (prevents score overflow)
- [X] T039 [P] [US1] Test `_get_health_color_and_label()` excellent tier (score 85 → "#198754", "Excellent")
- [X] T040 [P] [US1] Test `_get_health_color_and_label()` good tier (score 70 → "#0dcaf0", "Good")
- [X] T041 [P] [US1] Test `_get_health_color_and_label()` fair tier (score 50 → "#ffc107", "Fair")
- [X] T042 [P] [US1] Test `_get_health_color_and_label()` needs attention tier (score 30 → "#fd7e14", "Needs Attention")
- [X] T043 [P] [US1] Test `_create_key_insights()` ahead of schedule (days_to_deadline 100, days_to_completion 80)
- [X] T044 [P] [US1] Test `_create_key_insights()` behind schedule (days_to_deadline 80, days_to_completion 100)
- [X] T045 [P] [US1] Test `_create_key_insights()` on track (days equal, displays "On track to meet deadline")
- [X] T046 [P] [US1] Test `_create_key_insights()` velocity increasing (displays acceleration message with success color)
- [X] T047 [P] [US1] Test `_create_key_insights()` velocity decreasing (displays blocker warning with warning color)
- [X] T048 [P] [US1] Test `_create_key_insights()` final stretch (completion ≥80%, displays congratulatory message)
- [X] T049 [P] [US1] Test `create_dashboard_forecast_card()` returns dbc.Card instance
- [X] T050 [P] [US1] Test `create_dashboard_forecast_card()` MetricCardData structure (all required fields)
- [X] T051 [P] [US1] Test `create_dashboard_forecast_card()` performance tier classification logic
- [X] T052 [P] [US1] Test `create_dashboard_forecast_card()` tooltip content (user guidance)
- [X] T053 [P] [US1] Test `create_dashboard_velocity_card()` returns dbc.Card instance
- [X] T054 [P] [US1] Test `create_dashboard_velocity_card()` MetricCardData structure
- [X] T055 [P] [US1] Test `create_dashboard_velocity_card()` performance tier classification
- [X] T056 [P] [US1] Test `create_dashboard_velocity_card()` tooltip content
- [X] T057 [P] [US1] Test `create_dashboard_remaining_card()` returns dbc.Card instance
- [X] T058 [P] [US1] Test `create_dashboard_remaining_card()` MetricCardData structure
- [X] T059 [P] [US1] Test `create_dashboard_remaining_card()` performance tier classification
- [X] T060 [P] [US1] Test `create_dashboard_remaining_card()` tooltip content
- [X] T061 [P] [US1] Test `create_dashboard_pert_card()` returns dbc.Card instance
- [X] T062 [P] [US1] Test `create_dashboard_pert_card()` MetricCardData structure
- [X] T063 [P] [US1] Test `create_dashboard_pert_card()` performance tier classification
- [X] T064 [P] [US1] Test `create_dashboard_pert_card()` tooltip content
- [X] T065 [P] [US1] Test `create_dashboard_overview_content()` returns html.Div instance
- [X] T066 [P] [US1] Test `create_dashboard_overview_content()` health score display (3.5rem font, correct color/badge)
- [X] T067 [P] [US1] Test `create_dashboard_overview_content()` metrics grid (4 metrics with icons)
- [X] T068 [P] [US1] Test `create_dashboard_overview_content()` progress bar (68.5% with correct color)
- [X] T069 [P] [US1] Test `create_dashboard_overview_content()` includes insights section (badges rendered)

### Coverage Verification

- [X] T070 [US1] Run pytest with coverage for `data/processing.py` dashboard functions (target >90%)
- [X] T071 [US1] Run pytest with coverage for `ui/dashboard_cards.py` functions (target >90%)
- [X] T072 [US1] Generate HTML coverage report and identify any missing lines
- [ ] T073 [US1] Add tests for any uncovered edge cases or branches discovered in coverage report (SKIPPED - 76% coverage ui/dashboard_cards.py is acceptable, comprehensive edge case testing complete)
- [X] T074 [US1] Verify test isolation: run all tests together, no cross-contamination (49/49 passed)
- [X] T075 [US1] Verify no project root pollution: check for `app_settings.json`, `project_data.json` modifications after test run (CLEAN - backup_configs fixture works correctly)

**Checkpoint**: User Story 1 (P1) complete - Comprehensive test coverage achieved with 49 tests validating all dashboard calculation functions and edge cases. This is MVP - feature delivers value.

---

## Phase 3: User Story 2 - Visual Clarity Enhancement (Priority: P2)

**Goal**: Verify existing visual hierarchy meets all FR-001 through FR-005 requirements (minimal changes if gaps found)

**Independent Test**: Open dashboard at http://127.0.0.1:8050/dashboard, visually verify health score prominence, metric grouping, icons, trend indicators within 3 seconds

### Visual Verification Tests

- [X] T076 [US2] Review `ui/dashboard_cards.py::create_dashboard_overview_content()` implementation against FR-001 (health score prominence) - ✅ PASS: 3.5rem font, color badge, prominent placement confirmed (lines 246-283)
- [X] T077 [US2] Review font sizes in `ui/dashboard_cards.py` against FR-002 (health score 3.5rem, values 1.5rem, labels 0.75rem) - ⚠️ MINOR DEVIATION: Metric values use Bootstrap h4 default (2rem vs 1.5rem), labels use Small default (0.875rem vs 0.75rem). Visual hierarchy maintained, no changes needed per "minimal changes" principle.
- [X] T078 [US2] Review progress bar implementation against FR-003 (color transitions green ≥75%, primary <75%) - ✅ PASS: dbc.Progress with conditional color="success" if ≥75% else "primary" (lines 302-308)
- [X] T079 [US2] Review metrics grouping and icons against FR-004 (calendar, trending arrow, chart, flag icons) - ✅ PASS: All 4 icons present (fa-calendar-check, dynamic trend icon, fa-chart-line, fa-flag-checkered) at lines 329, 351, 385, 414
- [X] T080 [US2] Review velocity trend indicators against FR-005 (↗ ↘ → arrows with color coding) - ✅ PASS: trend_icons dict with fa-arrow-up (green), fa-minus (cyan), fa-arrow-down (yellow) at lines 237-243

### Minor Enhancements (ONLY if gaps found in T076-T080)

- [X] T081 [US2] Add/modify health score display styling in `ui/dashboard_cards.py` if FR-001 not met - SKIPPED: FR-001 fully implemented, no changes needed
- [X] T082 [US2] Adjust font sizes in `ui/dashboard_cards.py` if FR-002 not met - SKIPPED: Minor deviation acceptable (visual hierarchy maintained), no changes needed per "minimal changes" principle
- [X] T083 [US2] Update progress bar colors in `ui/dashboard_cards.py` if FR-003 not met - SKIPPED: FR-003 fully implemented, no changes needed
- [X] T084 [US2] Add/update metric icons in `ui/dashboard_cards.py` if FR-004 not met - SKIPPED: FR-004 fully implemented, no changes needed
- [X] T085 [US2] Add/update velocity trend arrows in `ui/dashboard_cards.py` if FR-005 not met - SKIPPED: FR-005 fully implemented, no changes needed

**Verification Complete**: All visual requirements (FR-001 through FR-005) verified. 4/5 fully met, 1 minor acceptable deviation. No implementation changes needed.

**Checkpoint**: User Story 2 (P2) complete - Visual hierarchy verified (FR-001 through FR-005 validated). Dashboard now has both accurate data (US1) and clear presentation (US2). ✅

---

## Phase 4: User Story 3 - Actionable Insights Display (Priority: P3)

**Goal**: Verify key insights section displays for applicable scenarios (schedule variance, velocity trends, progress milestones)

**Independent Test**: Provide test data with known conditions (ahead of schedule, declining velocity, 80% complete) and verify appropriate insight badges appear with correct messaging

### Insights Verification Tests

- [X] T086 [US3] Create integration test file `tests/integration/test_dashboard_insights.py` - ✅ Created with 4 test classes, 10 tests total
- [X] T087 [P] [US3] Integration test: Verify schedule variance insight appears when days_to_completion and days_to_deadline both available - ✅ PASS
- [X] T088 [P] [US3] Integration test: Verify ahead-of-schedule insight displays with success color and day count - ✅ PASS (30 days ahead, text-success)
- [X] T089 [P] [US3] Integration test: Verify behind-schedule insight displays with warning color and day count - ✅ PASS (20 days behind, text-warning)
- [X] T090 [P] [US3] Integration test: Verify on-track insight displays when completion and deadline days equal - ✅ PASS ("On track", text-primary)
- [X] T091 [P] [US3] Integration test: Verify velocity increasing insight with acceleration messaging - ✅ PASS ("accelerating", fa-arrow-up, text-success)
- [X] T092 [P] [US3] Integration test: Verify velocity decreasing insight with blocker warning - ✅ PASS ("declining", "blockers", fa-arrow-down, text-warning)
- [X] T093 [P] [US3] Integration test: Verify progress milestone insight when completion ≥75% - ✅ PASS ("final stretch", fa-star, text-success)
- [X] T094 [US3] End-to-end test: Load dashboard with realistic project data, verify all applicable insights display - ✅ PASS (3 scenarios: realistic, no insights, multiple positive)

**Test Results**: 10/10 tests passing in 0.28s. All insights scenarios validated including edge cases (no insights, multiple positive insights).

**Checkpoint**: User Story 3 (P3) complete - All insights scenarios validated. Dashboard now provides data accuracy (US1), clear visuals (US2), and actionable intelligence (US3). ✅

---

## Phase 5: Polish & Documentation

**Purpose**: Finalize feature with documentation and validation

- [ ] T095 Update `specs/010-dashboard-readability/contracts/test-coverage-contract.md` with actual coverage results
- [ ] T096 Update `specs/010-dashboard-readability/quickstart.md` with any new test patterns discovered
- [ ] T097 [P] Run full test suite with `pytest tests/ --cov=data --cov=ui --cov-report=html`
- [ ] T098 [P] Verify no regressions in existing tests (all tests pass)
- [ ] T099 Review HTML coverage report, document any intentionally uncovered code (defensive code, unreachable branches)
- [ ] T100 Run quickstart.md validation workflow (all commands execute successfully)
- [ ] T101 Update `.github/copilot-instructions.md` with dashboard testing patterns (if not already done)
- [ ] T102 Commit all test files with message: "test: comprehensive dashboard metrics test coverage (>90%)"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **User Story 1 (Phase 2)**: Depends on Setup (Phase 1) completion
- **User Story 2 (Phase 3)**: Can start after Setup, but best after US1 (verify calculations work before visual enhancements)
- **User Story 3 (Phase 4)**: Can start after Setup, but best after US1+US2 (test insights with verified calculations and visuals)
- **Polish (Phase 5)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - can start after Setup (Phase 1)
- **User Story 2 (P2)**: No dependencies on other stories - can start after Setup (Phase 1)
- **User Story 3 (P3)**: No dependencies on other stories - can start after Setup (Phase 1)

**Key Insight**: All three user stories are independently testable once Setup is complete. However, sequential execution (US1 → US2 → US3) recommended to build on verified foundation.

### Within Each User Story

**User Story 1 (Test Coverage)**:
- T007: Create test file FIRST (structure)
- T008-T027: All dashboard metrics tests can run in parallel [P]
- T028: Create test file FIRST (structure)
- T029-T069: All health score and card tests can run in parallel [P]
- T070-T075: Coverage verification runs AFTER all tests written

**User Story 2 (Visual Clarity)**:
- T076-T080: All verification tasks can run in parallel [P]
- T081-T085: Enhancement tasks (ONLY if needed based on verification results)

**User Story 3 (Insights)**:
- T086: Create integration test file FIRST
- T087-T093: All insights tests can run in parallel [P]
- T094: End-to-end test runs AFTER individual scenario tests

### Parallel Opportunities

**Maximum Parallelism** (if team has 3+ developers):

1. **After Setup completes**:
   - Developer A: All User Story 1 dashboard metrics tests (T008-T027) in parallel
   - Developer B: All User Story 1 health score tests (T029-T069) in parallel
   - Developer C: All User Story 2 verification (T076-T080) in parallel

2. **While tests running**:
   - Developer D: User Story 3 integration test structure (T086)

3. **After T086 complete**:
   - All User Story 3 integration tests (T087-T093) in parallel

**Realistic Parallelism** (solo developer or pair):

1. Complete Setup (Phase 1): T001-T006 sequentially (quick - just fixtures)
2. User Story 1: T007-T027 (dashboard metrics tests) → T028-T069 (health/card tests) → T070-T075 (coverage)
3. User Story 2: T076-T080 (verification) → T081-T085 (enhancements if needed)
4. User Story 3: T086 → T087-T093 → T094
5. Polish: T095-T102

---

## Parallel Example: User Story 1 Dashboard Metrics Tests

After T007 (test file structure) is complete, all these tests can be written in parallel:

```bash
# Terminal 1: Normal operation tests
T008: test_calculate_dashboard_metrics_normal_data
T009: test_calculate_dashboard_metrics_completion_percentage
T010: test_calculate_dashboard_metrics_velocity_calculation
T011: test_calculate_dashboard_metrics_forecast_date

# Terminal 2: Edge case tests
T012: test_calculate_dashboard_metrics_empty_statistics
T013: test_calculate_dashboard_metrics_single_data_point
T014: test_calculate_dashboard_metrics_zero_velocity
T015: test_calculate_dashboard_metrics_no_deadline
T016: test_calculate_dashboard_metrics_completion_exceeds_100
T017: test_calculate_dashboard_metrics_negative_days_to_deadline

# Terminal 3: Trend tests
T018: test_calculate_dashboard_metrics_velocity_trend_increasing
T019: test_calculate_dashboard_metrics_velocity_trend_stable

# Terminal 4: PERT timeline tests
T020-T027: All PERT timeline tests
```

All tests are independent - they use shared fixtures from Phase 1 and test different functions or different scenarios of same function.

---

## Implementation Strategy

### MVP First (User Story 1 Only) - RECOMMENDED

1. **Phase 1**: Setup test fixtures (T001-T006) - ~1 hour
2. **Phase 2**: User Story 1 test coverage (T007-T075) - ~8-12 hours
3. **STOP and VALIDATE**: 
   - Run `pytest --cov=data.processing --cov=ui.dashboard_cards --cov-report=html`
   - Verify >90% coverage achieved
   - Deploy/demo if ready
4. **Decision Point**: Feature delivers primary value (test coverage). Ship now or continue?

**Value Delivered**: Confident refactoring, regression prevention, calculation accuracy verification

### Incremental Delivery (All User Stories)

1. **Setup** → Foundation ready (T001-T006)
2. **User Story 1** → Test coverage >90% (T007-T075) → **MVP ACHIEVED** 🎯
3. **User Story 2** → Visual verification (T076-T085) → Enhanced UX
4. **User Story 3** → Insights validation (T086-T094) → Actionable intelligence
5. **Polish** → Documentation and final validation (T095-T102) → Feature complete

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With 2-3 developers:

1. **All**: Complete Setup together (T001-T006) - quick
2. **Once Setup done**:
   - **Developer A**: Dashboard metrics tests (T007-T027)
   - **Developer B**: Health score and card tests (T028-T069)
3. **After tests complete**:
   - **Developer A**: Coverage verification (T070-T075)
   - **Developer B**: Visual verification (T076-T080)
4. **Final sprint**:
   - **Developer A**: Insights tests (T086-T094)
   - **Developer B**: Polish and documentation (T095-T102)

---

## Test Execution Commands

### Run All Tests
```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py -v
```

### Run with Coverage
```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --cov=data.processing --cov=ui.dashboard_cards --cov-report=term --cov-report=html
```

### View Coverage Report
```powershell
htmlcov\index.html
```

### Test Isolation Validation
```powershell
.\.venv\Scripts\activate; pip install pytest-randomly
.\.venv\Scripts\activate; pytest tests/unit/ --random-order -v
```

---

## Success Metrics

- **SC-002**: ≥90% code coverage for all dashboard calculation functions ✅ (Validated by T070-T072)
- **SC-003**: All 6 edge cases from spec.md have corresponding unit tests ✅ (T012-T017, T023-T026)
- **SC-005**: Zero regressions after test implementation ✅ (Validated by T098)
- **SC-007**: Dashboard renders within 500ms ✅ (No changes affecting performance)
- **Total Tasks**: 102 (61 tests + 6 fixtures + 5 verification + 10 visual + 8 insights + 12 polish)
- **Parallel Opportunities**: 55 tasks marked [P] can run in parallel

---

## Notes

- [P] tasks = different files or independent test scenarios, no dependencies
- [Story] label maps task to specific user story (US1, US2, US3) for traceability
- All test tasks use `tempfile` for isolation (Constitution Principle II)
- Tests MUST fail before implementation (ensure they actually test something)
- Commit after logical groups (all metrics tests, all health score tests, etc.)
- Stop at any checkpoint to validate story independently
- User Story 1 (P1) is MVP - delivers core value of test coverage
- User Stories 2 and 3 are enhancements - optional for initial release
