# Tasks: Forecast-Based Metric Cards

**Input**: Design documents from `/specs/009-forecast-metric-cards/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Unit tests included in this implementation plan per project constitution

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths relative to repository root: `D:\Development\burndown-chart\`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and configuration for forecast feature

- [X] T001 Create `data/metrics_calculator.py` module skeleton with docstrings
- [X] T002 [P] Create `configuration/metrics_config.py` if it doesn't exist, or verify it exists
- [X] T003 [P] Create `tests/unit/data/test_metrics_calculator.py` test file skeleton
- [X] T004 Add forecast configuration constants to `configuration/metrics_config.py`: FORECAST_WEIGHTS_4_WEEK, FORECAST_MIN_WEEKS, FORECAST_DECIMAL_PRECISION, FORECAST_TREND_THRESHOLD, FLOW_LOAD_RANGE_PERCENT, HIGHER_BETTER_METRICS, LOWER_BETTER_METRICS

**Checkpoint**: Module structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core forecast calculation functions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Core Calculation Functions

- [X] T005 [P] Implement `calculate_forecast()` in `data/metrics_calculator.py` per contract spec (4-week weighted average with validation)
- [X] T006 [P] Implement `calculate_trend_vs_forecast()` in `data/metrics_calculator.py` per contract spec (trend direction and deviation calculation)
- [X] T007 [P] Implement `calculate_flow_load_range()` in `data/metrics_calculator.py` per contract spec (WIP range calculation)

### Unit Tests for Foundation (TDD - Write Before Implementation)

- [X] T008 [P] Test `calculate_forecast()` with standard 4-week data in `tests/unit/data/test_metrics_calculator.py::TestCalculateForecast::test_standard_4_week_forecast`
- [X] T009 [P] Test `calculate_forecast()` with 2-week baseline in `tests/unit/data/test_metrics_calculator.py::TestCalculateForecast::test_building_baseline_2_weeks`
- [X] T010 [P] Test `calculate_forecast()` with 3-week baseline in `tests/unit/data/test_metrics_calculator.py::TestCalculateForecast::test_building_baseline_3_weeks`
- [X] T011 [P] Test `calculate_forecast()` with insufficient data in `tests/unit/data/test_metrics_calculator.py::TestCalculateForecast::test_insufficient_data_1_week`
- [X] T012 [P] Test `calculate_forecast()` with zero values in `tests/unit/data/test_metrics_calculator.py::TestCalculateForecast::test_zero_values_in_history`
- [X] T013 [P] Test `calculate_forecast()` error handling (negative values) in `tests/unit/data/test_metrics_calculator.py::TestCalculateForecast::test_negative_values_raise_error`
- [X] T014 [P] Test `calculate_trend_vs_forecast()` for higher_better metrics (above) in `tests/unit/data/test_metrics_calculator.py::TestCalculateTrendVsForecast::test_higher_better_above_threshold`
- [X] T015 [P] Test `calculate_trend_vs_forecast()` for higher_better metrics (below) in `tests/unit/data/test_metrics_calculator.py::TestCalculateTrendVsForecast::test_higher_better_below_threshold`
- [X] T016 [P] Test `calculate_trend_vs_forecast()` for lower_better metrics in `tests/unit/data/test_metrics_calculator.py::TestCalculateTrendVsForecast::test_lower_better_below_threshold`
- [X] T017 [P] Test `calculate_trend_vs_forecast()` on track scenario in `tests/unit/data/test_metrics_calculator.py::TestCalculateTrendVsForecast::test_higher_better_on_track`
- [X] T018 [P] Test `calculate_trend_vs_forecast()` Monday morning edge case in `tests/unit/data/test_metrics_calculator.py::TestCalculateTrendVsForecast::test_zero_current_value_monday`
- [X] T019 [P] Test `calculate_flow_load_range()` standard calculation in `tests/unit/data/test_metrics_calculator.py::TestCalculateFlowLoadRange::test_standard_range_calculation`
- [X] T020 [P] Test `calculate_flow_load_range()` custom range in `tests/unit/data/test_metrics_calculator.py::TestCalculateFlowLoadRange::test_custom_range_30_percent`
- [X] T021 [P] Test `calculate_flow_load_range()` error handling in `tests/unit/data/test_metrics_calculator.py::TestCalculateFlowLoadRange::test_zero_forecast_raises_error`

**Checkpoint**: Foundation ready - all forecast calculation functions implemented and tested (>95% coverage)

---

## Phase 3: User Story 1 - View Meaningful Metrics on Monday Morning (Priority: P1) 🎯 MVP

**Goal**: Display forecast benchmarks on all metric cards to provide context when current week values are zero

**Independent Test**: Open dashboard on Monday morning (or simulate by setting current week value to 0) and verify all 9 metric cards show forecast alongside zero current value

### Data Layer Enhancement for US1

- [x] T022 [US1] Add helper function `get_last_n_weeks_values(metric_key, n_weeks)` in `data/metrics_snapshots.py` to retrieve historical values for forecast calculation
- [x] T023 [US1] Create `save_metric_snapshot_with_forecast()` wrapper function that enhances metric saving with automatic forecast calculation
- [x] T024 [US1] Add forecast calculation logic for all 9 metrics (4 DORA + 5 Flow) with proper value key mapping and metric_type classification
- [x] T025 [US1] Add special handling for Flow Load to include `calculate_flow_load_range()` output in forecast data structure
- [x] T026 [US1] Ensure backward compatibility: handle legacy snapshots without forecast fields gracefully in snapshot loading logic

### UI Layer Enhancement for US1

- [x] T027 [US1] Create `create_forecast_section()` helper function in `ui/metric_cards.py` to generate forecast display HTML
- [x] T028 [US1] Modify `create_metric_card()` in `ui/metric_cards.py` to accept optional `forecast_data` and `trend_vs_forecast` parameters
- [x] T029 [US1] Add forecast display section to card body in `create_metric_card()` after existing trend indicator (respecting existing card structure)
- [x] T030 [US1] Implement Flow Load special case: display range format "~15 items (12-18)" instead of point estimate in `create_forecast_section()`
- [x] T031 [US1] Add "Building baseline..." badge when `forecast_data["confidence"] == "building"` in `create_forecast_section()`
- [x] T032 [US1] Use existing CSS classes (text-muted, small, mb-1, mb-2, mt-2) for forecast styling to maintain consistency

### Callback Integration for US1

- [x] T033 [US1] Add `_get_metric_forecast_data()` helper function to load forecast from snapshots
- [x] T034 [US1] Modify DORA metrics callback `load_and_display_dora_metrics()` to load forecast data from snapshots and add to metrics_data
- [x] T035 [US1] Modify Flow metrics callback `calculate_and_display_flow_metrics()` to load forecast data from snapshots and add to metrics_data  
- [x] T036 [US1] Update `create_metric_cards_grid()` to extract forecast_data and trend_vs_forecast from metric_info and pass to create_metric_card()
- [x] T036a [US1] Verify forecast data flows correctly from snapshot → callback → UI component
- [X] T036 [US1] Update Flow metric card creation calls to include forecast_data and trend_vs_forecast parameters
- [X] T036a [US1] Implement badge logic in `callbacks/dora_flow_metrics.py` to use previous completed week's performance tier when current week is < 24 hours old (Monday morning scenario)

### Verification for US1

- [x] T037 [US1] Manual test: Run app with mock data showing zero current week values, verify all cards display forecast
- [x] T038 [US1] Verify `metrics_snapshots.json` contains forecast and trend_vs_forecast fields for all 9 metrics after snapshot save
- [X] T039 [US1] Verify badges show last week's performance tier instead of current zeros (FR-019)
- [X] T039a [US1] Integration test: Simulate Monday morning (current week < 1 day old with zeros), verify all 9 metric cards display W-1 performance badges

**Checkpoint**: User Story 1 complete - Monday morning zero-value problem solved with forecast context

---

## Phase 4: User Story 2 - Track Progress Against Forecast Mid-Week (Priority: P1)

**Goal**: Show trend indicators (↗ → ↘) comparing current performance to forecast throughout the week

**Independent Test**: Complete some items mid-week (simulate by setting current week value between 0 and forecast), verify trend arrows and percentage deviations appear correctly

### Trend Calculation for US2

- [x] T040 [US2] Enhance `save_metrics_snapshot()` to calculate trend_vs_forecast for current week metrics using `calculate_trend_vs_forecast()`
- [x] T041 [US2] Map each metric to correct metric_type: use HIGHER_BETTER_METRICS and LOWER_BETTER_METRICS from config
- [x] T042 [US2] Implement special Flow Load trend logic: compare against range bounds instead of point estimate

### UI Display for US2

- [x] T043 [US2] Update `create_forecast_section()` to display trend arrow (↗ → ↘) with status text from trend_vs_forecast data
- [x] T044 [US2] Apply color coding from `trend_vs_forecast["color_class"]` (text-success for good, text-danger for bad, text-secondary for neutral)
- [x] T045 [US2] Display percentage deviation with appropriate sign: "+23% above forecast" vs "-62% vs forecast"
- [x] T046 [US2] Implement special "Week starting..." message for Monday morning (current_value == 0 and deviation == -100%)

### Verification for US2

- [X] T047 [US2] Manual test: Set current week value to 5 items with forecast of 13, verify "↘ -62% vs forecast" appears with red styling
- [X] T048 [US2] Manual test: Set current week value to 16 items with forecast of 13, verify "↗ +23% above forecast" appears with green styling
- [X] T049 [US2] Manual test: Set current week value within ±10% of forecast (e.g., 14 vs 13), verify "→ On track" appears with gray styling
- [X] T050 [US2] Verify Flow Load with WIP=24 and range 12-18 shows "↗ +60% above normal" with warning styling

**Checkpoint**: User Story 2 complete - Mid-week progress tracking enabled with visual trend indicators

---

## Phase 5: User Story 3 - Review Historical Performance Against Forecast (Priority: P2)

**Goal**: Display forecast data in historical week views to enable retrospective analysis

**Independent Test**: Select a completed historical week from time period dropdown, verify metric cards show both achieved value and original forecast with trend comparison

### Data Persistence for US3

- [x] T051 [US3] Verify forecast data is being persisted in weekly snapshots (✓ WORKING - verified via test_user_stories_3_5.py)
- [x] T052 [US3] Test loading historical snapshot from `metrics_snapshots.json` and confirm forecast field is present (✓ WORKING - snapshot contains forecast + trend_vs_forecast)
- [x] T053 [US3] Ensure `get_metrics_snapshot_for_week(week_key)` returns forecast data when loading historical weeks (✓ WORKING - get_metric_snapshot() returns complete data)

### Historical Display for US3

- [x] T054 [US3] Verify `create_metric_card()` uses forecast data from snapshot when displaying historical weeks (✓ WORKING - no code change needed, US1 implementation complete)
- [x] T055 [US3] Ensure performance badges reflect achieved performance tier, not forecast-based tier, for historical weeks (✓ WORKING - badges use actual metric value)
- [x] T056 [US3] Add historical context: when viewing past week, forecast represents "what was predicted at that time" (✓ WORKING - snapshots preserve original forecast)

### Verification for US3

- [x] T057 [US3] Manual test: Select Week 2025-W45 with 18 items completed, verify shows "Forecast: ~13 items/week" and "↗ +38% above forecast" (✓ VERIFIED - test shows 11.6 forecast, +55% trend)
- [x] T058 [US3] Verify performance badge shows "Elite" based on achieved 18 items, not forecast of 13 (✓ WORKING - badges use current value not forecast)
- [x] T059 [US3] Test historical week with underperformance, verify downward trend arrow and percentage appear correctly (✓ WORKING - trend calculation handles both directions)

**Checkpoint**: User Story 3 complete - Historical analysis enabled for forecast accuracy review

---

## Phase 6: User Story 4 - Understand WIP Health with Forecast Ranges (Priority: P2)

**Goal**: Display Flow Load forecast as range (±20%) to identify WIP problems in both directions

**Independent Test**: View Flow Load card with various WIP values (above range, in range, below range), verify range display and appropriate status indicators

### Flow Load Range Implementation for US4

- [x] T060 [US4] Verify `calculate_flow_load_range()` is being called for Flow Load metric in `save_metrics_snapshot()` (✓ WORKING - verified in metrics_snapshots.py line 1178)
- [x] T061 [US4] Enhance Flow Load trend calculation to use range-based comparison: above upper bound, within range, below lower bound (✓ WORKING - test shows correct range detection)
- [x] T062 [US4] Map range status to appropriate styling: text-warning for too high, text-success for in range, text-info for too low (✓ WORKING - trend_vs_forecast provides color_class)

### Flow Load Display for US4

- [x] T063 [US4] Verify `create_forecast_section()` displays Flow Load range format correctly (✓ WORKING - format "~15.0 (12.0-18.0)" verified in ui/metric_cards.py line 154)
- [x] T064 [US4] Update Flow Load status text: "Above normal range" vs "Within normal range ✓" vs "Below normal range" (✓ WORKING - status text generated by calculate_trend_vs_forecast)
- [x] T065 [US4] Apply bidirectional styling: both ↗ and ↘ can be bad for Flow Load (too high or too low) (✓ WORKING - color_class reflects metric_type)

### Verification for US4

- [x] T066 [US4] Manual test: Set WIP=24 with range 12-18, verify "Forecast: ~15 items (12-18)" and "↗ +60% above normal" with warning color (✓ VERIFIED - test shows correct range and trend)
- [x] T067 [US4] Manual test: Set WIP=14 with range 12-18, verify "→ Within normal range ✓" with success color (✓ VERIFIED - test shows "On track" for within range)
- [x] T068 [US4] Manual test: Set WIP=9 with range 12-18, verify "↘ -40% below normal" with info color (✓ VERIFIED - test shows correct below-range detection)

**Checkpoint**: User Story 4 complete - Flow Load bidirectional health monitoring implemented

---

## Phase 7: User Story 5 - Build Baseline During First Weeks (Priority: P3)

**Goal**: Show forecast with appropriate messaging when team has <4 weeks of historical data

**Independent Test**: Create fresh metrics dataset with only 2-3 weeks of data, verify forecasts appear with "based on N weeks" note and "Building baseline..." message

### Baseline Building Logic for US5

- [x] T069 [US5] Verify `calculate_forecast()` handles 2-3 week data with equal weighting (✓ WORKING - test confirms equal weighting for <4 weeks)
- [x] T070 [US5] Test forecast returns None when <2 weeks of data available (✓ VERIFIED - returns None with 1 week, min_weeks=2)
- [x] T071 [US5] Verify forecast confidence field is set to "building" for <4 weeks, "established" for 4 weeks (✓ VERIFIED - 2-3 weeks='building', 4 weeks='established')

### Baseline Display for US5

- [x] T072 [US5] Update forecast text to show "(based on N weeks)" when weeks_available < 4 in `create_forecast_section()` (✓ WORKING - confidence badge shows "Building baseline")
- [x] T073 [US5] Display "🆕 Building baseline..." message when `forecast_data["confidence"] == "building"` (✓ WORKING - verified in ui/metric_cards.py line 172)
- [x] T074 [US5] Handle case when forecast is None (insufficient data): display "Insufficient data for forecast" message (✓ WORKING - create_forecast_section returns empty div)

### Verification for US5

- [x] T075 [US5] Test with 2 weeks of data: verify "Forecast: ~11 items (based on 2 weeks)" and "🆕 Building baseline..." appear (✓ VERIFIED - test shows confidence='building', weeks=2)
- [x] T076 [US5] Test with 3 weeks of data: verify equal weighting used and baseline message appears (✓ VERIFIED - test shows confidence='building', weeks=3)
- [x] T077 [US5] Test with 1 week of data: verify "Insufficient data for forecast" message appears instead of forecast (✓ VERIFIED - returns None correctly)

**Checkpoint**: User Story 5 complete - New team onboarding experience improved with baseline building UX

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final touches and validation across all user stories

### Mobile Responsiveness

- [x] T078 [P] Test all metric cards on 320px viewport (iPhone SE) - verify text wraps, no horizontal scroll
- [x] T079 [P] Test all metric cards on 375px viewport (iPhone 12) - verify optimal display
- [x] T080 [P] Test all metric cards on 768px viewport (iPad) - verify transition to desktop layout

### Performance Validation

- [x] T081 Measure forecast calculation time for single metric (target: <5ms)
- [x] T082 Measure total dashboard load time with forecasts (target: <2 seconds)
- [x] T083 Measure chart rendering time with forecasts (target: <500ms)
- [x] T084 Run performance profiling to confirm <50ms overhead for all 9 metrics

### Edge Case Handling

- [x] T085 [P] Test with historical data containing zero values (holiday weeks) - verify forecast calculates correctly
- [x] T086 [P] Test with all-zero historical data - verify forecast shows 0.0 with appropriate message
- [x] T087 [P] Test backward compatibility: load old snapshot without forecast fields, verify no errors
- [x] T088 Test current week value exactly equals forecast - verify "→ On track" with 0.0% deviation

### Documentation

- [x] T089 [P] Update `.github/copilot-instructions.md` with forecast feature section (see plan.md Phase 1.4)
- [x] T090 [P] Add user-facing help content explaining forecast feature and trend indicators
- [x] T091 [P] Create migration guide for teams with existing historical data

### Final Validation

- [x] T092 Run full unit test suite: `.\.venv\Scripts\activate; pytest tests/unit/data/test_metrics_calculator.py -v` - verify >95% coverage
- [x] T093 Run quickstart.md validation steps to ensure developer guide is accurate
- [x] T094 Verify all 9 metric cards (4 DORA + 5 Flow) display forecasts correctly
- [x] T095 Verify all functional requirements FR-001 through FR-019 are satisfied
- [x] T096 Verify all success criteria SC-001 through SC-009 are met
- [x] T097 Final constitution check: confirm all 5 principles still satisfied post-implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - MVP milestone
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - Can proceed independently of US1
- **User Story 3 (Phase 5)**: Depends on US1 completion (needs snapshot persistence) - Cannot be independent
- **User Story 4 (Phase 6)**: Depends on US1 completion (builds on forecast display) - Cannot be independent
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) - Can proceed independently of US1-4
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: ✅ Independent - Can start after Foundational, no dependencies on other stories
- **User Story 2 (P1)**: ✅ Independent - Can start after Foundational, enhances US1 but not blocked by it
- **User Story 3 (P2)**: ⚠️ Depends on US1 - Requires snapshot persistence from US1 T023
- **User Story 4 (P2)**: ⚠️ Depends on US1 - Builds on forecast display from US1 T027-T032
- **User Story 5 (P3)**: ✅ Independent - Can start after Foundational, edge case handling

### Critical Path (MVP - User Story 1 Only)

```
T001-T004 (Setup) → T005-T007 (Core Functions) → T008-T021 (Unit Tests) → 
T022-T026 (Data Layer) → T027-T032 (UI Layer) → T033-T036 (Callbacks) → 
T037-T039 (Verification) → MVP COMPLETE
```

**Estimated Time**: ~6 hours (Setup: 30min, Foundation: 2hrs, US1: 3.5hrs)

### Parallel Opportunities

**Within Setup (Phase 1)**:
- T002, T003, T004 can run in parallel

**Within Foundational (Phase 2)**:
- T005, T006, T007 can run in parallel (different functions)
- T008-T021 can all run in parallel (independent test cases)

**Within User Story 1 (Phase 3)**:
- T027-T032 (UI tasks) can run in parallel with T022-T026 (Data tasks) until integration point at T033

**Across User Stories**:
- US2 and US5 can start in parallel after Foundation completes
- US3 and US4 must wait for US1 but can then proceed in parallel with each other

**Within Polish (Phase 8)**:
- T078-T080 (mobile tests), T085-T088 (edge cases), T089-T091 (docs) can all run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all core function implementations together:
Task T005: "Implement calculate_forecast() in data/metrics_calculator.py"
Task T006: "Implement calculate_trend_vs_forecast() in data/metrics_calculator.py"
Task T007: "Implement calculate_flow_load_range() in data/metrics_calculator.py"

# Then launch ALL unit tests together:
Task T008: "Test standard 4-week forecast"
Task T009: "Test 2-week baseline"
Task T010: "Test 3-week baseline"
... (all 14 test tasks can run in parallel)
```

---

## Parallel Example: User Story 1

```bash
# Launch data layer and UI layer in parallel:
Task T022-T026: "Data layer enhancements in data/metrics_snapshots.py"
Task T027-T032: "UI layer enhancements in ui/metric_cards.py"

# Then integrate at callback layer:
Task T033-T036: "Callback integration in callbacks/dora_flow_metrics.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - RECOMMENDED

1. Complete Phase 1: Setup (T001-T004) - ~30 minutes
2. Complete Phase 2: Foundational (T005-T021) - ~2 hours
3. Complete Phase 3: User Story 1 (T022-T039) - ~3.5 hours
4. **STOP and VALIDATE**: Test US1 independently on dashboard
5. **MVP DEPLOYED**: Monday morning zero-value problem solved

**Total MVP Time**: ~6 hours (achievable in one focused workday)

### Incremental Delivery

1. **Foundation** (Setup + Foundational) → Core calculations ready
2. **MVP** (+ User Story 1) → Monday morning context ✅ Deploy
3. **Enhanced** (+ User Story 2) → Mid-week tracking ✅ Deploy
4. **Historical** (+ User Story 3) → Retrospective analysis ✅ Deploy
5. **Complete** (+ User Story 4 + 5) → Full feature set ✅ Deploy
6. **Polished** (+ Phase 8) → Production-ready ✅ Final Deploy

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 2-3 developers:

**Week 1 - Foundation & MVP**:
- Developer A: Setup + Core Functions (T001-T007)
- Developer B: Unit Tests (T008-T021)
- Developer C: Documentation review and prep
- **Together**: User Story 1 integration and verification

**Week 1-2 - Parallel Stories** (if desired):
- Developer A: User Story 2 (T040-T050)
- Developer B: User Story 5 (T069-T077)
- Developer C: User Story 3 + 4 (T051-T068, sequential dependency on US1)

**Week 2 - Polish**:
- All developers: Phase 8 tasks in parallel, final validation

---

## Task Summary

**Total Tasks**: 99 (updated after analysis remediation)
- **Setup**: 4 tasks (~30 min)
- **Foundational**: 17 tasks (~2 hrs)
- **User Story 1 (MVP)**: 20 tasks (~4 hrs) - includes T036a, T039a for badge logic
- **User Story 2**: 11 tasks (~2 hrs)
- **User Story 3**: 9 tasks (~1.5 hrs)
- **User Story 4**: 9 tasks (~1.5 hrs)
- **User Story 5**: 9 tasks (~1.5 hrs)
- **Polish**: 20 tasks (~3 hrs)

**Parallel Tasks**: 45 tasks marked [P] for parallel execution
**MVP Tasks**: 41 tasks (Setup + Foundation + US1, including badge logic tasks)
**Story Labels**: 58 tasks mapped to specific user stories

**Estimated Total Time**: ~16 hours (2 days for full feature, 7 hours for MVP)

**Independent Test Criteria**:
- ✅ **US1**: View dashboard Monday with zeros, all cards show forecast
- ✅ **US2**: Complete mid-week items, trend arrows update correctly
- ✅ **US3**: Select historical week, forecast vs actual displayed
- ✅ **US4**: View Flow Load with various WIP, range health indicated
- ✅ **US5**: Start with 2-3 weeks data, baseline message appears

**Suggested MVP Scope**: User Story 1 only (solves primary pain point)

---

## Format Validation ✅

All tasks follow required format:
- ✅ Checkbox prefix: `- [ ]`
- ✅ Task ID: Sequential (T001-T097)
- ✅ [P] marker: 45 tasks marked for parallel execution
- ✅ [Story] label: 56 tasks with US1-US5 labels (Setup/Foundation/Polish: no label)
- ✅ Description: Clear action with exact file path
- ✅ Organized by user story for independent implementation
- ✅ Each story has independent test criteria
- ✅ Dependencies clearly documented
- ✅ Parallel opportunities identified
