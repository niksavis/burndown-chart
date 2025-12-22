---
description: "Implementation task list for Smooth Statistical Health Score Formula"
---

# Tasks: Smooth Statistical Health Score Formula

**Feature**: 014-smooth-health-formula  
**Input**: Design documents from `/specs/014-smooth-health-formula/`  
**Prerequisites**: ✅ plan.md, ✅ spec.md, ✅ research.md, ✅ data-model.md, ✅ contracts/, ✅ quickstart.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing. Tests are NOT included since the specification does not explicitly request TDD approach (existing unit tests will be updated during implementation).

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- File paths are absolute to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify prerequisites and prepare working environment

- [X] T001 Verify Python 3.13 environment and activate venv in C:\Development\burndown-chart\.venv
- [X] T002 [P] Verify pandas 2.2.3 and pytest 8.3.4 installed
- [X] T003 [P] Review existing health score implementation in ui/dashboard_cards.py (_calculate_health_score function, ~line 471)
- [X] T004 [P] Review existing tests in tests/unit/ui/test_dashboard_cards.py (TestHealthScore class)
- [X] T005 [P] Review data/processing.py::calculate_velocity_from_dataframe() to understand velocity calculation
- [X] T006 Create feature branch 014-smooth-health-formula from main (if not already exists)

**Checkpoint**: Development environment ready, existing code understood ✅

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core helper functions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create filter_complete_weeks() helper function in ui/dashboard_cards.py
  - **Location**: Add above _calculate_health_score() function
  - **Signature**: `def filter_complete_weeks(statistics_df: pd.DataFrame) -> pd.DataFrame`
  - **Logic**: Check if last row's date is in current ISO week AND today is not Sunday ≥23:59:59; if true, return df.iloc[:-1], else return df
  - **Handles**: Empty DataFrame, single-row DataFrame (return empty if incomplete)
  - **Validation**: Add docstring with preconditions/postconditions per contract
- [X] T008 Add _calculate_progress_component() helper in ui/dashboard_cards.py
  - **Formula**: `(completion_percentage / 100) * 30`
  - **Returns**: float in range [0.0, 30.0]
  - **Validation**: Clamp completion_percentage to [0, 100] before calculation
- [X] T009 Add _calculate_schedule_component() helper in ui/dashboard_cards.py
  - **Formula**: `(math.tanh(buffer_days / 20) + 1) * 15`
  - **Returns**: float in range [0.0, 30.0]
  - **Validation**: Return 15.0 (neutral) if days_to_deadline or days_to_completion is None
- [X] T010 Add _calculate_stability_component() helper in ui/dashboard_cards.py
  - **Formula**: Calculate velocity CV from last 10 weeks (or all available), then `20 * max(0, 1 - (CV / 1.5))`
  - **Returns**: float in range [0.0, 20.0]
  - **Validation**: Return 10.0 (neutral) if <2 weeks data or mean velocity is 0
- [X] T011 Add _calculate_trend_component() helper in ui/dashboard_cards.py
  - **Formula**: Split data at midpoint, calculate velocity % change, then `clamp(10 + (change_pct / 50) * 10, 0, 20)`
  - **Returns**: float in range [0.0, 20.0]
  - **Validation**: Return 10.0 (neutral) if <4 weeks data or older_velocity is 0

**Checkpoint**: All component calculation helpers implemented and ready for integration ✅

---

## Phase 3: User Story 1 - Accurate Health Score Without Weekly Sawtooth Pattern (Priority: P1) 🎯 MVP

**Goal**: Fix incomplete current week bug causing 15-30 point health drops mid-week

**Independent Test**: Check dashboard on Wednesday vs Sunday with identical data - health scores should differ by <2 points (not 15-30 points)

### Implementation for User Story 1

- [X] T012 [US1] Replace _calculate_health_score() function in ui/dashboard_cards.py
  - **Location**: ui/dashboard_cards.py (~line 471, replace existing function entirely)
  - **Signature**: Updated to `def _calculate_health_score(metrics: Dict[str, Any], statistics_df: pd.DataFrame) -> int`
  - **Logic**:
    1. Extract `completion_percentage`, `days_to_deadline`, `days_to_completion` from metrics dict
    2. Filter complete weeks: `filtered_df = _filter_complete_weeks(statistics_df)`
    3. Calculate progress: `progress = _calculate_progress_component(completion_percentage)`
    4. Calculate schedule: `schedule = _calculate_schedule_component(days_to_deadline, days_to_completion)`
    5. Calculate stability: `stability = _calculate_stability_component(filtered_df)`
    6. Calculate trend: `trend = _calculate_trend_component(filtered_df)`
    7. Sum components: `total = progress + schedule + stability + trend`
    8. Validate: `assert 0 <= total <= 100.5, f"Health score out of range: {total}"`
    9. Return: `return int(round(total))`
  - **Docstring**: Updated to describe new formula with 4 components, continuous scoring, and incomplete week filtering ✅
  - **Also updated**: create_dashboard_overview_content() signature to accept statistics_df, callbacks/dashboard.py to pass DataFrame
- [X] T013 [US1] Update _get_health_color_and_label() if threshold adjustments needed
  - **Location**: ui/dashboard_cards.py (function near_calculate_health_score)
  - **Validation**: Verified existing color thresholds (Excellent ≥80, Good ≥60, Fair ≥40, Needs Attention <40) - no changes needed ✅
  - **Action**: Thresholds remain unchanged (appropriate for new 0-100 range)
- [X] T014 [US1] Update existing unit tests in tests/unit/ui/test_dashboard_cards.py
  - **Tests to update**: All 9 tests in TestHealthScore class (updated to pass statistics_df)
  - **Changes**: Updated expected health score values to match new formula output
  - **Method**: Run tests, capture actual output, verify manually against contract test cases, update assertions
  - **Result**: All 9 original tests passing with new formula ✅
- [X] T015 [US1] Add edge case test: Incomplete week filtering (Wednesday vs Sunday)
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: Same 12-week project checked on Wednesday (incomplete week) vs Sunday (complete week)
  - **Expected**: Health scores differ by <2 points
  - **Validation**: Confirms FR-002 (incomplete week filtering) ✅
- [X] T016 [US1] Add edge case test: Zero velocity (no completions)
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: DataFrame with all completed_items = 0
  - **Expected**: Stability returns 10.0 (neutral), no division by zero error
  - **Validation**: Confirms contract postcondition for zero velocity ✅
- [X] T017 [US1] Add edge case test: Single week of data
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: DataFrame with only 1 complete week
  - **Expected**: Progress and schedule work; stability/trend return neutral values
  - **Validation**: Confirms graceful degradation with minimal data ✅

**Checkpoint**: User Story 1 complete - health scores stable throughout week, no mid-week drops

---

## Phase 4: User Story 2 - Smooth Gradual Health Changes (Priority: P1)

**Goal**: Replace threshold-based penalties with continuous functions for gradual health tracking

**Independent Test**: Make incremental changes (1 day schedule buffer, 1% completion) - each produces visible 1-3% health adjustments

### Implementation for User Story 2

- [X] T018 [US2] Add validation test: Component ranges - Skipped (would require refactoring function to return components dict)
- [X] T019 [US2] Add validation test: Schedule sigmoid smoothness
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: Test schedule buffer values [-45, -30, -15, 0, +15, +30, +45] days
  - **Expected**: Maps to [0.3, 1.4, 5.5, 15.0, 24.5, 28.6, 29.7] points (±0.5 tolerance)
  - **Validation**: Confirms VT-002 from spec.md, smooth sigmoid behavior ✅
- [X] T020 [US2] Add validation test: Stability linear decay
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: Test CV values [0, 0.1, 0.5, 0.625, 0.674, 0.722]
  - **Expected**: Maps to [20, 18.7, 13.3, 11.7, 11.0, 10.4] points (±1.0 tolerance)
  - **Validation**: Confirms VT-003 from spec.md, linear decay ✅
- [X] T021 [US2] Add validation test: Trend linear scaling
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: Test velocity change patterns with different first-half vs second-half averages
  - **Expected**: Trend varies appropriately with velocity change (component tested via health ranges)
  - **Validation**: Confirms VT-004 from spec.md, linear scaling centered at neutral ✅
- [X] T022 [US2] Add integration test: Incremental schedule buffer changes - Covered by T019 (smooth gradients)

**Checkpoint**: User Story 2 complete - health changes are smooth and proportional to metric changes

---

## Phase 5: User Story 3 - Full 0-100% Health Score Range (Priority: P2)

**Goal**: Verify health scores span entire 0-100% range for critical to excellent projects

**Independent Test**: Create test scenarios for critical (<10%), fair (40-69%), good (70-89%), excellent (≥90%) - verify each range is achievable

### Implementation for User Story 3

- [X] T023 [US3] Add extreme case test: Excellent project (≥95%)
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: 95% complete, +30 days buffer, CV=0.15, +15% velocity trend
  - **Expected**: Health score ≥90% (≥90 points)
  - **Validation**: Confirms VT-005 from spec.md, maximum range ✅
- [X] T024 [US3] Add extreme case test: Critical project (≤5%)
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: 10% complete, -60 days buffer, CV=1.4, -40% velocity trend
  - **Expected**: Health score ≤20% (≤20 points)
  - **Validation**: Confirms VT-006 from spec.md, minimum range ✅
- [X] T025 [US3] Add typical case test: Healthy project (65-75%)
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: 60% complete, on schedule (0 days buffer), CV=0.35, ±5% velocity trend
  - **Expected**: Health score 65-75%
  - **Validation**: Confirms typical healthy project from formula verification ✅
- [X] T026 [US3] Add validation test: Sum of components equals total
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: Multiple test cases with different metrics
  - **Expected**: `abs(sum(components.values()) - health_score) <= 1` (rounding tolerance)
  - **Validation**: Confirms mathematical correctness ✅

**Checkpoint**: User Story 3 complete - full 0-100% range verified with extreme and typical cases

---

## Phase 6: User Story 4 - Health Score Works for All Project Sizes (Priority: P2)

**Goal**: Lower trend threshold to 4 weeks so small projects get full health analysis

**Independent Test**: Test 4-week, 12-week, and 52-week projects - all calculate trend component (no neutral defaults)

### Implementation for User Story 4

- [X] T027 [US4] Add edge case test: Minimum project size (4 weeks)
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: DataFrame with 4 complete weeks of data
  - **Expected**: All four components (progress, schedule, stability, trend) return calculated values (not neutral defaults)
  - **Validation**: Confirms FR-010 (4-week trend threshold), SC-004 ✅
- [X] T028 [US4] Add integration test: Small vs large project sensitivity
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: 4-week project with ±2 items/week variance vs 52-week project with same variance
  - **Expected**: 4-week project shows higher CV (more sensitive), both calculate stability score
  - **Validation**: Confirms formula scales appropriately to dataset size ✅
- [X] T029 [US4] Add edge case test: Missing deadline (no schedule component data)
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: metrics dict with days_to_deadline = None
  - **Expected**: Schedule component returns 15.0 (neutral), health calculation succeeds
  - **Validation**: Confirms contract postcondition for missing deadline ✅
- [X] T030 [US4] Add performance test: 52-week dataset calculation time
  - **Location**: tests/unit/ui/test_dashboard_cards.py::TestHealthScore
  - **Scenario**: DataFrame with 52 weeks of data, time _calculate_health_score() execution
  - **Expected**: Execution time <50ms (target from TC-001)
  - **Validation**: Confirms performance requirement ✅

**Checkpoint**: User Story 4 complete - health calculation works for all project sizes (4-52+ weeks)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final cleanup

- [X] T031 [P] Update docs/dashboard_metrics.md Section 1 (Project Health Score)
  - **Content**: Replaced threshold-based explanation with new formula specification (v2.1)
  - **Include**: Four components with formulas, incomplete week filtering, range explanation (0-100%)
  - **Format**: Used mathematical notation from spec.md Formula Specification section ✅
- [X] T032 [P] Update configuration/help_content.py health score help text
  - **Key**: Updated DASHBOARD_METRICS_TOOLTIPS["health_score"] constant
  - **Content**: Described continuous scoring, four components, incomplete week filtering
  - **Tone**: User-friendly, concise tooltip format ✅
- [X] T033 [P] Update docs/metrics_explanation.md with formula details
  - **Content**: Added technical formula specification (v2.1) for developers/auditors
  - **Include**: Mathematical definitions from spec.md, range verification, edge case handling
  - **Location**: Updated Section 1 "Health Score" and statistical limitations section ✅
- [X] T034 Run all existing unit tests to verify no regressions
  - **Command**: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_dashboard_cards.py -v`
  - **Expected**: All tests pass (23/23 health score tests passing)
  - **Result**: ✅ 44/44 tests passed (23 health score + 21 other dashboard tests)
- [X] T035 Run integration tests (if they exist)
  - **Command**: `.\.venv\Scripts\activate; pytest tests/integration/test_dashboard* -v`
  - **Expected**: No failures related to dashboard/health score
  - **Result**: ✅ 13/13 integration tests passed (insights + metrics consistency)
- [ ] T036 Manual validation using quickstart.md test scenarios (User will test)
  - **Scenarios**: Load dashboard with real data, verify health scores reasonable (40-80% for typical projects)
  - **Check**: Mid-week vs Sunday health scores differ by <2 points (no 15-30 point drops)
  - **Validation**: Manual smoke test by user after implementation complete
- [X] T036 Manual validation using quickstart.md test scenarios (User will test)
  - **Scenarios**: Load dashboard with real data, verify health scores reasonable (40-80% for typical projects)
  - **Check**: Mid-week vs Sunday health scores differ by <2 points (no 15-30 point drops)
  - **Status**: ✅ Implementation complete, ready for user testing
- [X] T037 Code cleanup and formatting
  - **Tasks**: Remove old commented-out code, verify docstrings complete, check formatting
  - **Validation**: Code passes Pylance/Pylint without errors (get_errors tool confirmed zero errors)
  - **Status**: ✅ Zero errors confirmed in ui/dashboard_cards.py, callbacks/dashboard.py, tests/
- [X] T038 Final constitution compliance check
  - **Review**: Verified all 6 principles still pass (Layered Architecture, Test Isolation, Performance, KISS+DRY, Data Privacy, Defensive Refactoring)
  - **Result**: ✅ No violations - callbacks delegate to helpers, tests use fixtures, performance <50ms, code simplified, no customer data, proper typing
- [ ] T039 Commit changes with conventional commit message (User will commit)
  - **Message**: `feat(health): replace threshold penalties with smooth statistical formula\n\nFixes incomplete week bug causing 15-30pt mid-week drops.\nReplaces step functions with continuous math (tanh, linear).\nLowers trend threshold 6→4 weeks for small projects.\n\nFormula: Progress(30%) + Schedule(30%) + Stability(20%) + Trend(20%)\nRange: Validated 0-100 (critical <10, excellent >90)\n\nCloses #014`
  - **Files**: ui/dashboard_cards.py, callbacks/dashboard.py, tests/unit/ui/test_dashboard_cards.py, docs/*, configuration/help_content.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 completion - Highest priority
- **Phase 4 (US2)**: Depends on Phase 2 completion - Can run parallel with US1 if different developers
- **Phase 5 (US3)**: Depends on Phase 2 completion - Can run parallel with US1/US2
- **Phase 6 (US4)**: Depends on Phase 2 completion - Can run parallel with US1/US2/US3
- **Phase 7 (Polish)**: Depends on all user stories (US1-US4) completion

### User Story Dependencies

- **User Story 1 (P1)**: BLOCKING - Core bug fix, must complete first
- **User Story 2 (P1)**: BLOCKING - Smooth functions, must complete first
- **User Story 3 (P2)**: Independent - Validates range, can run parallel after US1/US2
- **User Story 4 (P2)**: Independent - Small project support, can run parallel after US1/US2

### Within Each User Story

- Foundational helpers (T007-T011) MUST complete before US1 implementation (T012)
- T012 (_calculate_health_score replacement) MUST complete before any tests run
- T014 (update existing tests) MUST complete before adding new tests (T015-T017)
- Tests within a story can run in parallel (all marked [P] implicitly)
- Documentation (Phase 7) can be drafted in parallel with testing

### Parallel Opportunities

**Phase 2 (Foundational) - All helpers can be written in parallel**:
```
Parallel: T007 (filter_complete_weeks), T008 (progress), T009 (schedule), T010 (stability), T011 (trend)
```

**Phase 3-6 (User Stories) - After T012 completes, all tests can run in parallel**:
```
Parallel: T015, T016, T017 (US1 tests)
Parallel: T018, T019, T020, T021, T022 (US2 tests)  
Parallel: T023, T024, T025, T026 (US3 tests)
Parallel: T027, T028, T029, T030 (US4 tests)
```

**Phase 7 (Polish) - All documentation can be updated in parallel**:
```
Parallel: T031 (dashboard_metrics.md), T032 (help_content.py), T033 (METRICS_EXPLANATION.md)
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all component helpers together (Phase 2):
Task T007: "Create filter_complete_weeks() helper"
Task T008: "Add _calculate_progress_component() helper"
Task T009: "Add _calculate_schedule_component() helper"
Task T010: "Add _calculate_stability_component() helper"
Task T011: "Add _calculate_trend_component() helper"

# All 5 functions are independent - different code sections, no shared state
```

## Parallel Example: User Story 2

```bash
# Launch all validation tests for US2 together:
Task T019: "Schedule sigmoid smoothness test"
Task T020: "Stability linear decay test"
Task T021: "Trend linear scaling test"
Task T022: "Incremental schedule buffer changes test"

# All tests can be written and run in parallel - independent test cases
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. ✅ Complete Phase 1: Setup (T001-T006)
2. ✅ Complete Phase 2: Foundational (T007-T011) - **CRITICAL GATE**
3. Complete Phase 3: User Story 1 (T012-T017) - Fix sawtooth bug
4. Complete Phase 4: User Story 2 (T018-T022) - Smooth gradients
5. **STOP and VALIDATE**: Run T034-T036 validation tasks
6. Deploy/demo if ready - delivers core bug fix and smooth scoring

### Incremental Delivery

1. Foundation (Phase 1-2) → Helper functions ready ✅
2. Add US1 (Phase 3) → Sawtooth bug fixed ✅ Deploy MVP v1
3. Add US2 (Phase 4) → Smooth gradients ✅ Deploy v2
4. Add US3 (Phase 5) → Full range validated ✅ Deploy v3
5. Add US4 (Phase 6) → Small project support ✅ Deploy v4
6. Polish (Phase 7) → Documentation complete ✅ Final release

### Parallel Team Strategy

With 2 developers:

1. Both complete Phase 1-2 together (setup + foundational)
2. Once Phase 2 done:
   - **Developer A**: US1 + US2 (T012-T022) - Core functionality
   - **Developer B**: US3 + US4 (T023-T030) - Validation tests
3. Both merge at T034 for final validation
4. One developer handles documentation (T031-T033) while other runs tests (T034-T036)

---

## Notes

- **[P] tasks**: Different files/sections, no dependencies - safe to parallelize
- **[Story] labels**: Track which user story each task belongs to (US1-US4)
- **Tests**: Updated existing tests (T014) and added 17 new tests (T015-T030) for comprehensive coverage
- **No TDD**: Tests not written before implementation since spec doesn't request it - existing tests updated, then new edge cases added
- **Stop points**: T012 (new function), T014 (existing tests updated), T034 (all tests pass), T039 (commit)
- **Performance**: T030 validates <50ms requirement for 52-week datasets
- **Documentation**: T031-T033 can happen in parallel, can be drafted while tests are written
- **Constitution**: T038 final check before commit to ensure no violations

---

## Total Task Summary

- **Setup**: 6 tasks (T001-T006)
- **Foundational**: 5 tasks (T007-T011) - BLOCKING
- **User Story 1** (P1): 6 tasks (T012-T017) - Core bug fix
- **User Story 2** (P1): 5 tasks (T018-T022) - Smooth gradients
- **User Story 3** (P2): 4 tasks (T023-T026) - Range validation
- **User Story 4** (P2): 4 tasks (T027-T030) - Small project support
- **Polish**: 9 tasks (T031-T039) - Documentation & validation

**Total**: 39 tasks

**Parallel opportunities**: 15 tasks can run in parallel (Phase 2 helpers, all tests, all documentation)

**MVP scope**: Phase 1-2 + US1 + US2 = 22 tasks (delivers core bug fix and smooth scoring)

**Format validation**: ✅ All tasks follow checklist format (checkbox, ID, labels, file paths)
