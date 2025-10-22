# Tasks: Bug Analysis Dashboard

**Input**: Design documents from `/specs/004-bug-analysis-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Unit and integration tests included per existing test structure

**Organization**: Tasks grouped by user story to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- All paths relative to repository root `D:\Development\burndown-chart\`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and configuration

- [X] T001 Add `bug_analysis_config` section to `app_settings.json` with default bug type mappings
- [X] T002 [P] Create `tests/utils/mock_bug_data.py` mock data generator skeleton
- [X] T003 [P] Create `data/bug_processing.py` module skeleton with function stubs
- [X] T004 [P] Create `data/bug_insights.py` module skeleton with rule engine structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Modify `data/jira_simple.py` to add `issuetype` to base_fields and extract `issuetype.name` from JIRA issue fields (line ~171)
- [X] T006 Verify `issuetype` field persisted in `jira_cache.json` structure after JIRA data fetch
- [X] T007 Update `configuration/settings.py` to add `get_bug_analysis_config()` accessor function
- [X] T008 Extend `data/schema.py` to add BugIssue, WeeklyBugStatistics, BugMetricsSummary types
- [X] T009 [P] Implement `tests/utils/mock_bug_data.py::generate_mock_bug_data()` with realistic distributions
- [X] T010 [P] Implement `tests/utils/mock_bug_data.py::generate_edge_case_bugs()` for boundary conditions
- [X] T011 Update `data/persistence.py::save_unified_data()` to handle optional `bug_analysis` section
- [X] T012 Update `data/persistence.py::load_unified_data()` to return empty bug_analysis if missing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Bug Metrics Overview (Priority: P1) 🎯 MVP

**Goal**: Display total bugs, open bugs, closed bugs, and resolution rate in a summary card

**Independent Test**: Load JIRA data with bugs and verify dashboard shows accurate total, open, closed counts and resolution percentage

### Tests for User Story 1

- [X] T013 [P] [US1] Create `tests/unit/data/test_bug_processing.py` with test for filter_bug_issues()
- [X] T014 [P] [US1] Add test_filter_bug_issues_mixed_types() to verify Bug filtering from Stories/Tasks
- [X] T015 [P] [US1] Add test_filter_bug_issues_no_bugs() to verify empty result when no bugs exist
- [X] T016 [P] [US1] Add test_filter_bug_issues_custom_mappings() to verify Defect/Incident mapping
- [X] T017 [P] [US1] Add test_calculate_bug_metrics_summary() to verify total/open/closed calculation
- [X] T018 [P] [US1] Add test_bug_metrics_resolution_rate() to verify percentage calculation

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement `data/bug_processing.py::filter_bug_issues()` per bug_filtering.contract.md with created_date validation
- [X] T020 [US1] Implement `data/bug_processing.py::calculate_bug_metrics_summary()` to aggregate total/open/closed bugs
- [X] T021 [US1] Add resolution rate calculation to calculate_bug_metrics_summary()
- [X] T022 [P] [US1] Create `ui/bug_analysis.py` with create_bug_metrics_card() component
- [X] T023 [P] [US1] Create `ui/bug_analysis.py::create_bug_analysis_tab()` layout function
- [X] T024 [US1] Update `ui/tabs.py` to add "Bug Analysis" tab to navigation (conditionally shown)
- [X] T025 [P] [US1] Create `callbacks/bug_analysis.py` with bug_metrics_update() callback
- [X] T025a [US1] Add timeline filter change listener to bug_metrics_update() callback for automatic recalculation
- [X] T026 [US1] Register bug analysis callbacks in `callbacks/__init__.py`
- [X] T027 [US1] Add "No bugs found" message handling in create_bug_metrics_card() for zero bugs

**Checkpoint**: Bug metrics overview displays correctly and updates with timeline filters

---

## Phase 4: User Story 2 - Track Bug Creation and Resolution Trends (Priority: P1)

**Goal**: Visualize bugs created vs closed per week with trend indicators

**Independent Test**: Generate weekly bug data and verify chart shows two trend lines with visual warnings when creation exceeds closure

### Tests for User Story 2

- [X] T028 [P] [US2] Add test_calculate_bug_statistics_weekly_bins() to test_bug_processing.py
- [X] T029 [P] [US2] Add test_bug_statistics_iso_week_assignment() to verify ISO week logic
- [X] T030 [P] [US2] Add test_bug_statistics_cumulative_open() to verify running totals
- [X] T031 [P] [US2] Add test_bug_statistics_empty_weeks() to verify weeks with zero activity
- [X] T032 [P] [US2] Create `tests/unit/ui/test_bug_charts.py` with test_bug_trend_chart_data()

### Implementation for User Story 2

- [X] T033 [P] [US2] Implement `data/bug_processing.py::calculate_bug_statistics()` per bug_statistics.contract.md including bugs resolved within timeline regardless of creation date (FR-020)
- [X] T034 [US2] Add ISO week calculation helper functions (get_iso_week, get_week_start_date)
- [X] T035 [US2] Implement weekly binning logic for bugs_created and bugs_resolved
- [X] T036 [US2] Implement cumulative_open_bugs running sum calculation
- [X] T037 [P] [US2] Implement `visualization/mobile_charts.py::create_bug_trend_chart()` returning Plotly figure with mobile optimization
- [X] T037a [US2] Add red/orange background highlights and warning icons to bug trend chart for 3+ consecutive weeks where creation > closure (FR-014)
- [X] T038 [P] [US2] Create `ui/bug_charts.py::BugTrendChart()` component wrapper calling visualization.mobile_charts.create_bug_trend_chart()
- [X] T039 [US2] Validate bug trend chart color contrast ratio (4.5:1 minimum) for creation vs closure lines
- [X] T040 [US2] Update bug_analysis_tab() layout to include bug trend chart
- [X] T041 [US2] Add bug_trend_chart_update() callback to callbacks/bug_analysis.py
- [X] T042 [US2] Implement date range filtering for bug trend chart

**Checkpoint**: Bug trends visualize correctly showing creation vs closure over time with warnings

---

## Phase 5: User Story 3 - Analyze Bug Investment (Priority: P2)

**Goal**: Display story points invested in bugs per week when available

**Independent Test**: Load bugs with story points and verify chart shows both item counts and points invested

### Tests for User Story 3

- [ ] T043 [P] [US3] Add test_bug_statistics_with_story_points() to test_bug_processing.py
- [ ] T044 [P] [US3] Add test_bug_statistics_null_story_points() to verify null handling
- [ ] T045 [P] [US3] Add test_bug_investment_calculation() to verify points aggregation
- [ ] T046 [P] [US3] Add test_capacity_percentage_calculation() to verify bug capacity metric

### Implementation for User Story 3

- [ ] T047 [US3] Extend calculate_bug_statistics() to aggregate bugs_points_created and bugs_points_resolved
- [ ] T048 [US3] Add null story points handling (treat as 0 for points, always count in items)
- [ ] T049 [US3] Add net_points calculation to weekly statistics
- [ ] T050 [US3] Extend calculate_bug_metrics_summary() to add total_bug_points and open_bug_points
- [ ] T051 [US3] Implement capacity_consumed_by_bugs calculation (bug_points / total_points)
- [ ] T052 [P] [US3] Implement `visualization/charts.py::create_bug_investment_chart()` returning Plotly figure with dual-axis (items + story points)
- [ ] T053 [P] [US3] Create `ui/bug_charts.py::BugInvestmentChart()` component wrapper calling visualization.charts.create_bug_investment_chart()
- [ ] T054 [US3] Add capacity percentage display to bug metrics card
- [ ] T055 [US3] Add warning indicator when bug capacity exceeds 30% for 2+ weeks
- [ ] T056 [US3] Update bug_analysis_tab() to include investment chart
- [ ] T057 [US3] Add "Story points data not available" message for projects without points

**Checkpoint**: Bug investment metrics display correctly with dual metric support (items + points)

---

## Phase 6: User Story 4 - Receive Actionable Quality Insights (Priority: P2)

**Goal**: Generate and display actionable recommendations based on bug patterns

**Independent Test**: Trigger various bug patterns (low resolution rate, increasing trend) and verify appropriate insights appear

### Tests for User Story 4

- [ ] T058 [P] [US4] Create `tests/unit/data/test_bug_insights.py` with test_generate_quality_insights()
- [ ] T059 [P] [US4] Add test_insight_low_resolution_rate() to verify resolution rate warning
- [ ] T060 [P] [US4] Add test_insight_increasing_bug_trend() to verify trend warning
- [ ] T061 [P] [US4] Add test_insight_high_bug_capacity() to verify capacity warning
- [ ] T062 [P] [US4] Add test_insight_positive_trend() to verify positive feedback
- [ ] T063 [P] [US4] Add test_insights_prioritization() to verify severity sorting
- [ ] T064 [P] [US4] Add test_insights_custom_thresholds() to verify threshold customization
- [ ] T065 [P] [US4] Add test_insights_max_limit() to verify 10 insight cap

### Implementation for User Story 4

- [ ] T066 [P] [US4] Define InsightType and InsightSeverity enums in data/bug_insights.py
- [ ] T067 [P] [US4] Define DEFAULT_THRESHOLDS constants in data/bug_insights.py
- [ ] T068 [P] [US4] Implement check_low_resolution_rate() rule function
- [ ] T069 [P] [US4] Implement check_increasing_bug_trend() rule function
- [ ] T070 [P] [US4] Implement check_high_bug_capacity() rule function
- [ ] T071 [P] [US4] Implement check_long_resolution_time() rule function
- [ ] T072 [P] [US4] Implement check_positive_trend() rule function
- [ ] T073 [P] [US4] Implement check_stable_quality() rule function
- [ ] T074 [P] [US4] Implement check_no_open_bugs() rule function
- [ ] T075 [US4] Implement generate_quality_insights() main function per quality_insights.contract.md
- [ ] T076 [US4] Add insight prioritization logic (severity → type → actionability)
- [ ] T077 [US4] Add 10-insight cap with most critical selection
- [ ] T078 [P] [US4] Create quality insights UI component in ui/bug_analysis.py
- [ ] T079 [US4] Add insight severity icons and color coding
- [ ] T080 [US4] Add expandable/collapsible insight details
- [ ] T081 [US4] Update bug_analysis_tab() to display insights at top
- [ ] T082 [US4] Add quality_insights_update() callback to callbacks/bug_analysis.py

**Checkpoint**: Quality insights generate correctly and display actionable recommendations

---

## Phase 7: User Story 5 - Forecast Bug Resolution Timeline (Priority: P3)

**Goal**: Display optimistic/pessimistic forecast for when open bugs will be resolved

**Independent Test**: Generate bug closure history and verify forecast shows projected completion dates with confidence intervals

### Tests for User Story 5

- [ ] T083 [P] [US5] Create `tests/unit/data/test_bug_forecasting.py` with test_forecast_bug_resolution()
- [ ] T084 [P] [US5] Add test_forecast_normal_closure_rate() to verify optimistic/pessimistic calculation
- [ ] T085 [P] [US5] Add test_forecast_zero_open_bugs() to verify immediate completion
- [ ] T086 [P] [US5] Add test_forecast_zero_closure_rate() to verify insufficient data handling
- [ ] T087 [P] [US5] Add test_forecast_insufficient_history() to verify 4-week minimum
- [ ] T088 [P] [US5] Add test_forecast_date_calculation() to verify future date accuracy
- [ ] T089 [P] [US5] Add test_forecast_week_ordering() to verify optimistic <= likely <= pessimistic

### Implementation for User Story 5

- [ ] T090 [P] [US5] Implement calculate_standard_deviation() helper in data/bug_processing.py
- [ ] T091 [P] [US5] Implement calculate_future_date() helper for date projections
- [ ] T092 [US5] Implement forecast_bug_resolution() per bug_forecasting.contract.md
- [ ] T093 [US5] Add historical closure rate calculation (last 8 weeks)
- [ ] T094 [US5] Add optimistic estimate (avg + 1 std dev)
- [ ] T095 [US5] Add pessimistic estimate (max(avg - 1 std dev, 0.1))
- [ ] T096 [US5] Add most_likely estimate (avg closure rate)
- [ ] T097 [US5] Add insufficient_data flag for < 4 weeks or zero closure
- [ ] T098 [P] [US5] Implement `visualization/charts.py::create_bug_forecast_chart()` returning Plotly figure with confidence intervals
- [ ] T099 [P] [US5] Create `ui/bug_charts.py::BugForecastChart()` component wrapper calling visualization.charts.create_bug_forecast_chart()
- [ ] T100 [US5] Add "Unable to forecast" message for zero/negative closure rate
- [ ] T101 [US5] Add "Insufficient data" message for < 4 weeks history
- [ ] T102 [US5] Update bug_analysis_tab() to include forecast chart
- [ ] T103 [US5] Add bug_forecast_update() callback to callbacks/bug_analysis.py
- [ ] T104 [US5] Add forecast recalculation on timeline filter change

**Checkpoint**: Bug resolution forecasts display correctly with confidence intervals and edge case handling

---

## Phase 8: Integration & Polish

**Purpose**: Cross-cutting improvements affecting all user stories

- [ ] T105 Update `data/persistence.py` to save bug_analysis data to project_data.json
- [ ] T106 Extend project_data.json schema to include bug_analysis section
- [ ] T107 Add backward compatibility check for projects without bug_analysis data
- [ ] T108 [P] Create `tests/integration/test_bug_analysis_workflow.py` for end-to-end Playwright tests
- [ ] T109 [P] Add integration test for bug tab navigation and rendering
- [ ] T110 [P] Add integration test for timeline filter affecting bug metrics
- [ ] T111 [P] Add integration test for JIRA data import with bug types
- [ ] T112 [P] Test bug trend chart mobile responsiveness (320px-768px viewports)
- [ ] T112a [P] Test bug metrics card mobile responsiveness (320px-768px viewports)
- [ ] T112b [P] Test quality insights panel mobile responsiveness (320px-768px viewports)
- [ ] T113 Add performance testing for 1000+ bugs (< 100ms target)
- [ ] T114 [P] Add ARIA labels to bug metrics card components
- [ ] T114a [P] Add ARIA labels and role attributes to bug trend chart
- [ ] T114b [P] Add ARIA labels to quality insights components (severity icons, expandable sections)
- [ ] T114c Test keyboard navigation through bug analysis tab (tab order, focus indicators)
- [ ] T115 Update `readme.md` to document bug analysis feature
- [ ] T116 Validate quickstart.md instructions work end-to-end
- [ ] T117 Implement error handling per NFR-001: user-friendly messages for JIRA API failures, missing issuetype field, and invalid data
- [ ] T118 Add structured logging for bug processing operations (filter, statistics, insights, forecasting)
- [ ] T119 Extract helper functions, add docstrings, and ensure PEP 8 compliance for data/bug_processing.py
- [ ] T120 Run full test suite and verify 85%+ coverage for bug modules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - Can proceed in parallel if staffed appropriately
  - Or sequentially in priority order: US1 → US2 → US3 → US4 → US5
- **Integration & Polish (Phase 8)**: Depends on desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 - No dependencies on other stories ✅ MVP FIRST
- **US2 (P1)**: Can start after Phase 2 - Reuses bug_issues from US1 but independently testable
- **US3 (P2)**: Extends US2 statistics with story points - independently testable
- **US4 (P2)**: Uses metrics from US1 and trends from US2 - independently testable
- **US5 (P3)**: Uses weekly statistics from US2 - independently testable

### Within Each User Story

1. Tests written FIRST (TDD approach)
2. Core data processing functions
3. UI components
4. Callbacks and integration
5. Edge case handling
6. Story validation checkpoint

### Parallel Opportunities

**Phase 1 Setup**: All tasks (T001-T004) can run in parallel

**Phase 2 Foundational**: 
- T009-T010 (mock data) can run in parallel
- T005-T008 (infrastructure) sequential (T005 merged JIRA changes, T006 verifies cache)
- T011-T012 (persistence) after T008

**User Story 1 Tests**: T013-T018 all parallel  
**User Story 1 Implementation**: T019, T022-T023 parallel, then T020-T021 sequential, then T024-T027

**User Story 2 Tests**: T028-T032 all parallel  
**User Story 2 Implementation**: T033-T036 sequential, T037+T038 parallel (visualization + UI wrapper), T037a+T039 sequential (visual warnings)

**User Story 3 Tests**: T043-T046 all parallel  
**User Story 3 Implementation**: T047-T051 sequential, T052-T053 parallel, T054-T057 sequential

**User Story 4 Tests**: T058-T065 all parallel  
**User Story 4 Implementation**: T066-T074 all parallel, T075-T077 sequential, T078-T082 sequential

**User Story 5 Tests**: T083-T089 all parallel  
**User Story 5 Implementation**: T090-T091 parallel, T092-T097 sequential, T098-T099 parallel, T100-T104 sequential

**Phase 8 Integration**: T108-T111 parallel, T112-T114 parallel, rest sequential

---

## Parallel Example: User Story 4 (Quality Insights)

```bash
# All tests in parallel:
Task T058: "Create tests/unit/data/test_bug_insights.py with test_generate_quality_insights()"
Task T059: "Add test_insight_low_resolution_rate()"
Task T060: "Add test_insight_increasing_bug_trend()"
Task T061: "Add test_insight_high_bug_capacity()"
Task T062: "Add test_insight_positive_trend()"
Task T063: "Add test_insights_prioritization()"
Task T064: "Add test_insights_custom_thresholds()"
Task T065: "Add test_insights_max_limit()"

# All rule functions in parallel:
Task T066: "Define InsightType and InsightSeverity enums"
Task T067: "Define DEFAULT_THRESHOLDS constants"
Task T068: "Implement check_low_resolution_rate() rule"
Task T069: "Implement check_increasing_bug_trend() rule"
Task T070: "Implement check_high_bug_capacity() rule"
Task T071: "Implement check_long_resolution_time() rule"
Task T072: "Implement check_positive_trend() rule"
Task T073: "Implement check_stable_quality() rule"
Task T074: "Implement check_no_open_bugs() rule"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T012) ⚠️ CRITICAL BLOCKER
3. Complete Phase 3: User Story 1 (T013-T027) - Bug metrics overview
4. Complete Phase 4: User Story 2 (T028-T042) - Bug trends
5. **STOP and VALIDATE**: Test bug analysis with real JIRA data
6. Deploy/demo bug analysis MVP

### Incremental Delivery

1. **Foundation** (Phase 1-2): Setup + infrastructure → Ready for stories
2. **MVP** (Phase 3-4): US1 + US2 → Bug overview + trends → Deploy ✅
3. **Enhanced** (Phase 5): Add US3 → Bug investment metrics → Deploy
4. **Insights** (Phase 6): Add US4 → Quality recommendations → Deploy
5. **Forecasting** (Phase 7): Add US5 → Resolution timeline predictions → Deploy
6. **Polish** (Phase 8): Integration tests + performance tuning → Final release

### Parallel Team Strategy

With 3 developers after Foundational phase complete:

- **Developer A**: User Story 1 (T013-T027) + User Story 4 (T058-T082)
- **Developer B**: User Story 2 (T028-T042) + User Story 5 (T083-T104)
- **Developer C**: User Story 3 (T043-T057) + Integration (T105-T120)

Stories integrate independently via shared data contracts.

---

## Performance Targets

- **Bug filtering**: Process 1000 issues in < 50ms (T019)
- **Statistics calculation**: Process 1000 bugs over 52 weeks in < 100ms (T033)
- **Insights generation**: Generate insights for 52 weeks in < 20ms (T075)
- **Forecasting**: Calculate forecast for 52 weeks in < 10ms (T092)
- **Chart rendering**: Render all bug charts in < 500ms (T037, T098)
- **Page load**: Bug Analysis tab loads in < 2 seconds (T108)

---

## Testing Requirements

### Unit Test Coverage

- **data/bug_processing.py**: 90%+ coverage (T013-T089)
- **data/bug_insights.py**: 90%+ coverage (T058-T065)
- **ui/bug_charts.py**: 80%+ coverage (T032)

### Integration Test Coverage

- JIRA data import with bug types (T111)
- Timeline filtering affects bug metrics (T110)
- Complete bug analysis workflow (T109)

### Edge Cases Covered

- No bugs in dataset (T015, T027)
- Zero closure rate (T086)
- Insufficient forecast history (T087)
- Mixed issue types (T014)
- Null story points (T044)
- Week boundary conditions (T029)

---

## Total Tasks: 128

- **Setup**: 4 tasks
- **Foundational**: 8 tasks (BLOCKING) - merged T005+T006, kept T006 as verification
- **User Story 1 (P1)**: 16 tasks (MVP) - includes auto-update callback
- **User Story 2 (P1)**: 17 tasks (MVP) - added visual warning and color contrast validation
- **User Story 3 (P2)**: 15 tasks - split into visualization + UI wrapper pattern
- **User Story 4 (P2)**: 25 tasks
- **User Story 5 (P3)**: 22 tasks - split into visualization + UI wrapper pattern
- **Integration & Polish**: 21 tasks - added mobile/accessibility tasks, improved error handling

**Parallel Opportunities**: 70+ tasks can run in parallel across phases

**MVP Scope**: Phase 1-4 (45 tasks) delivers core bug analysis functionality

**Suggested Delivery Order**: Setup → Foundational → US1 → US2 → US3 → US4 → US5 → Polish
