# Tasks: DORA and Flow Metrics Dashboard

**Input**: Design documents from `/specs/007-dora-flow-metrics/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included per spec requirements for comprehensive testing strategy.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create configuration files: configuration/dora_config.py with DORA benchmarks and metric definitions
- [X] T002 [P] Create configuration files: configuration/flow_config.py with Flow metric definitions and recommended distribution ranges
- [X] T003 [P] Update configuration/__init__.py to export new config modules

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement field mapper: data/field_mapper.py with fetch_available_jira_fields(), validate_field_mapping(), save_field_mappings(), get_field_mappings_hash()
- [X] T005 [P] Implement metrics cache: data/metrics_cache.py with generate_cache_key(), load_cached_metrics(), save_cached_metrics(), invalidate_cache()
- [X] T006 [P] Create metric cards component: ui/metric_cards.py with create_metric_card() supporting success and error states
- [X] T007 Create unit test for field mapper: tests/unit/data/test_field_mapper.py with tempfile isolation
- [X] T008 [P] Create unit test for metrics cache: tests/unit/data/test_metrics_cache.py with tempfile isolation
- [X] T009 [P] Create unit test for metric cards: tests/unit/ui/test_metric_cards.py verifying rendering for all states

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View DORA Metrics Dashboard (Priority: P1) 🎯 MVP

**Goal**: Display all four DORA metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, MTTR) with performance tier indicators and error handling

**Independent Test**: Navigate to DORA & Flow Metrics tab, view pre-calculated metrics from sample Jira data, verify all four DORA metrics display with appropriate visualizations and performance tier indicators (Elite/High/Medium/Low)

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for deployment frequency calculation: tests/unit/data/test_dora_calculator.py::test_deployment_frequency_calculation with known input/output
- [X] T011 [P] [US1] Unit test for lead time calculation: tests/unit/data/test_dora_calculator.py::test_lead_time_for_changes_calculation
- [X] T012 [P] [US1] Unit test for change failure rate: tests/unit/data/test_dora_calculator.py::test_change_failure_rate_calculation
- [X] T013 [P] [US1] Unit test for MTTR calculation: tests/unit/data/test_dora_calculator.py::test_mean_time_to_recovery_calculation
- [X] T014 [P] [US1] Parametrized edge case tests: tests/unit/data/test_dora_calculator.py with pytest.mark.parametrize for empty issues, missing fields, invalid dates
- [X] T015 [P] [US1] Integration test for complete DORA workflow: tests/integration/test_dora_flow_workflow.py::test_complete_dora_workflow with field mapping → calculation → caching

### Implementation for User Story 1

- [X] T016 [US1] Implement DORA calculator: data/dora_calculator.py with calculate_deployment_frequency(), calculate_lead_time_for_changes(), calculate_change_failure_rate(), calculate_mean_time_to_recovery(), calculate_all_dora_metrics() (depends on T004)
- [X] T017 [P] [US1] Create DORA dashboard UI: ui/dora_metrics_dashboard.py with create_dora_dashboard() including time period selector and metric cards grid
- [X] T018 [P] [US1] Create DORA charts module: visualization/dora_charts.py with chart generation functions for DORA metrics
- [X] T019 [US1] Create DORA metrics callback: callbacks/dora_flow_metrics.py with update_dora_metrics() callback delegating to data layer (depends on T016)
- [X] T020 [US1] Update main layout: ui/layout.py to add "DORA & Flow Metrics" navigation tab
- [X] T021 [US1] Register DORA callback: callbacks/__init__.py to import dora_flow_metrics module
- [X] T022 [US1] Unit test for DORA dashboard UI: tests/unit/ui/test_dora_dashboard.py verifying component structure and responsive layout

**Checkpoint**: At this point, User Story 1 should be fully functional - can view DORA metrics, see performance tiers, handle errors gracefully

---

## Phase 4: User Story 3 - Configure Jira Field Mappings (Priority: P1)

**Goal**: Provide UI for administrators to configure how Jira custom fields map to internal fields required for DORA and Flow metrics

**Independent Test**: Open field mapping configuration interface, map sample Jira fields to required metric fields, save configuration, verify metrics recalculate using new mappings

**Note**: Elevated to P1 as it's a prerequisite for metrics calculation to work across different Jira configurations

### Tests for User Story 3

- [X] T023 [P] [US3] Integration test for field mapping workflow: tests/integration/test_field_mapping_workflow.py::test_configure_and_save_mappings with tempfile isolation
- [X] T024 [P] [US3] Unit test for field validation: tests/unit/data/test_field_mapper.py::test_validate_field_type_compatibility
- [X] T025 [P] [US3] Integration test for cache invalidation: tests/integration/test_field_mapping_workflow.py::test_mapping_change_invalidates_cache

### Implementation for User Story 3

- [X] T026 [P] [US3] Create field mapping modal UI: ui/field_mapping_modal.py with create_field_mapping_modal() including dropdowns for all DORA and Flow fields
- [X] T027 [US3] Create field mapping callback: callbacks/field_mapping.py with populate_field_options() and save_mappings() callbacks (depends on T004)
- [X] T028 [US3] Add "Configure Mappings" button to DORA dashboard: ui/dora_metrics_dashboard.py update
- [X] T029 [US3] Register field mapping callback: callbacks/__init__.py to import field_mapping module
- [X] T030 [US3] Unit test for field mapping modal: tests/unit/ui/test_field_mapping_modal.py verifying modal structure and validation messages

**Checkpoint**: At this point, User Stories 1 AND 3 should work together - can configure field mappings and see DORA metrics recalculate

---

## Phase 5: User Story 2 - View Flow Metrics Dashboard (Priority: P2)

**Goal**: Display all five Flow metrics (Velocity, Time, Efficiency, Load, Distribution) with trend indicators and work type breakdown

**Independent Test**: Navigate to Flow Metrics tab, view calculated metrics from Jira issues including work item distribution charts and flow efficiency trends

### Tests for User Story 2

- [X] T031 [P] [US2] Unit test for flow velocity calculation: tests/unit/data/test_flow_calculator.py::test_flow_velocity_calculation with type breakdown
- [X] T032 [P] [US2] Unit test for flow time calculation: tests/unit/data/test_flow_calculator.py::test_flow_time_calculation
- [X] T033 [P] [US2] Unit test for flow efficiency calculation: tests/unit/data/test_flow_calculator.py::test_flow_efficiency_calculation
- [X] T034 [P] [US2] Unit test for flow load calculation: tests/unit/data/test_flow_calculator.py::test_flow_load_calculation
- [X] T035 [P] [US2] Unit test for flow distribution calculation: tests/unit/data/test_flow_calculator.py::test_flow_distribution_with_recommended_ranges
- [X] T036 [P] [US2] Parametrized edge case tests: tests/unit/data/test_flow_calculator.py for missing work types, incomplete data
- [X] T037 [P] [US2] Integration test for Flow workflow: tests/integration/test_dora_flow_workflow.py::test_complete_flow_workflow

### Implementation for User Story 2

- [X] T038 [US2] Implement Flow calculator: data/flow_calculator.py with calculate_flow_velocity(), calculate_flow_time(), calculate_flow_efficiency(), calculate_flow_load(), calculate_flow_distribution(), calculate_all_flow_metrics() (depends on T004)
- [X] T039 [P] [US2] Create Flow dashboard UI: ui/flow_metrics_dashboard.py with create_flow_dashboard() including distribution pie chart
- [X] T040 [P] [US2] Create Flow charts module: visualization/flow_charts.py with chart generation for distribution and efficiency trends
- [X] T041 [US2] Add Flow metrics callback: callbacks/dora_flow_metrics.py with update_flow_metrics() callback delegating to data layer (depends on T038)
- [X] T042 [US2] Update field mapping modal: ui/field_mapping_modal.py to include Flow field mappings section (completed in Phase 4)
- [X] T043 [US2] Unit test for Flow dashboard UI: tests/unit/ui/test_flow_dashboard.py verifying distribution chart and metric cards

**Checkpoint**: All three user stories (1, 2, 3) should now work independently - DORA metrics, Flow metrics, and field configuration all functional

---

## Phase 6: User Story 4 - Select Time Period for Metrics (Priority: P2)

**Goal**: Allow users to select different time periods (last 7 days, 30 days, 90 days, custom range) to analyze trends across different timeframes

**Independent Test**: Select different time periods from dropdown, verify all metrics recalculate for selected period, check that trend charts adjust appropriately

### Tests for User Story 4

- [X] T044 [P] [US4] Integration test for time period changes: tests/integration/test_dora_flow_workflow.py::test_time_period_selection_recalculates_metrics
- [X] T045 [P] [US4] Unit test for date parsing: tests/unit/data/test_dora_calculator.py::test_time_period_parsing for 7d, 30d, 90d presets
- [X] T046 [P] [US4] Integration test for custom date range: tests/integration/test_dora_flow_workflow.py::test_custom_date_range_selection

### Implementation for User Story 4

- [X] T047 [US4] Add time period selector to DORA dashboard: ui/dora_metrics_dashboard.py update with dbc.Select and dcc.DatePickerRange (already implemented)
- [X] T048 [US4] Update DORA callback for time period input: callbacks/dora_flow_metrics.py::update_dora_metrics to handle time_period_value input (depends on T019)
- [X] T049 [US4] Add time period selector to Flow dashboard: ui/flow_metrics_dashboard.py update (already implemented)
- [X] T050 [US4] Update Flow callback for time period input: callbacks/dora_flow_metrics.py::update_flow_metrics to handle time_period_value input (depends on T041)
- [X] T051 [US4] Update cache key generation: data/metrics_cache.py::generate_cache_key to include time period in key (already implemented)

**Checkpoint**: Users can now select any time period and see metrics recalculate automatically with proper caching

---

## Phase 7: User Story 5 - View Metric Trends Over Time (Priority: P3)

**Goal**: Display trend charts for each metric over time to identify improvements or degradations in team performance

**Independent Test**: View metric card, click "Show Trend", verify line chart displays metric's value over selected time period with week-over-week data points

### Tests for User Story 5

- [X] T052 [P] [US5] Unit test for trend chart generation: tests/unit/visualization/test_dora_charts.py::test_create_trend_chart
- [X] T053 [P] [US5] Integration test for trend display: tests/integration/test_dora_flow_workflow.py::test_show_trend_expands_chart

### Implementation for User Story 5

- [X] T054 [P] [US5] Add trend chart generation to DORA charts: visualization/dora_charts.py with create_deployment_frequency_trend(), create_lead_time_trend()
- [X] T055 [P] [US5] Add trend chart generation to Flow charts: visualization/flow_charts.py with create_flow_velocity_trend(), create_flow_efficiency_trend() (already implemented)
- [X] T056 [US5] Add "Show Trend" button to metric cards: ui/metric_cards.py::create_metric_card update with collapsible trend section ✅
- [X] T057 [US5] Add trend callback: callbacks/dora_flow_metrics.py with toggle_trend_display() callback ✅
- [X] T058 [US5] Update metric calculation to include trend data: data/dora_calculator.py and data/flow_calculator.py to calculate trend_direction and trend_percentage ✅

**Checkpoint**: ✅ COMPLETE - All metrics now have trend visualization capability for historical analysis (Commit: afd3eb0)

**Additional**: ✅ T017 COMPLETE - Historical metrics storage implemented in data/persistence.py with save_metrics_snapshot(), load_metrics_history(), and get_metric_trend_data() functions. Integrated into callbacks/dora_flow_metrics.py for automatic snapshot saving. Timezone regression fixed in dora_calculator.py _parse_datetime() function. All 29 DORA/Flow tests passing.

---

## Phase 8: User Story 6 - Export Metrics Data (Priority: P3)

**Goal**: Allow users to export metrics data to CSV or JSON format for external reporting and analysis

**Independent Test**: Click "Export" button, select format (CSV/JSON), verify file downloads with all current metric values and metadata

### Tests for User Story 6

- [X] T059 [P] [US6] Unit test for CSV export: tests/unit/data/test_metrics_export.py::test_export_metrics_to_csv ✅
- [X] T060 [P] [US6] Unit test for JSON export: tests/unit/data/test_metrics_export.py::test_export_metrics_to_json ✅
- [X] T061 [P] [US6] Integration test for export workflow: tests/integration/test_dora_flow_workflow.py::test_export_metrics_downloads_file ✅

### Implementation for User Story 6

- [X] T062 [P] [US6] Create export module: data/metrics_export.py with export_to_csv() and export_to_json() functions ✅
- [X] T063 [US6] Add export buttons to dashboards: ui/dora_metrics_dashboard.py and ui/flow_metrics_dashboard.py with export buttons ✅
- [X] T064 [US6] Create export callback: callbacks/dora_flow_metrics.py with export_metrics() callback using dcc.Download ✅
- [X] T065 [US6] Register export callback: callbacks/__init__.py update (auto-imported) ✅

**Checkpoint**: ✅ COMPLETE - All user stories complete - full feature set implemented (export CSV/JSON for DORA and Flow metrics). 706/706 tests passing.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T066 [P] Add mobile responsive styling: assets/custom.css with media queries for metric cards (320px, 768px, 1024px viewports) ✅
- [X] T067 [P] Add loading indicators: ui/loading_utils.py with skeleton loading cards for metrics ✅
- [X] T068 [P] Add error boundary components: ui/error_states.py with user-friendly error messages for all error states ✅
- [X] T069 [P] Add tooltips for metric definitions: ui/tooltip_utils.py with help text for each metric ✅
- [X] T070 Performance test for 5000 issues: tests/integration/test_performance.py::test_metric_calculation_performance_5000_issues verifying < 15 seconds ✅
- [X] T071 [P] Update documentation: readme.md with DORA & Flow Metrics usage section ✅
- [X] T072 [P] Update Copilot instructions: .github/copilot-instructions.md with DORA/Flow metrics context ✅
- [X] T073 Validate quickstart guide: specs/007-dora-flow-metrics/quickstart.md - verify all implementation steps completed ✅
- [X] T074 Code cleanup and refactoring: Remove any debug logging, optimize imports, ensure consistent error handling ✅
- [X] T075 Accessibility audit: Verify keyboard navigation, ARIA labels, screen reader compatibility for all new components ✅

**Checkpoint**: ✅ COMPLETE - All polish tasks completed. Feature is production-ready with 795/795 tests passing.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 3 (Phase 4)**: Depends on Foundational (Phase 2) - Can run in parallel with US1
- **User Story 2 (Phase 5)**: Depends on Foundational (Phase 2) - Can run after US1 or in parallel
- **User Story 4 (Phase 6)**: Depends on US1 and US2 completion (needs metrics callbacks)
- **User Story 5 (Phase 7)**: Depends on US1 and US2 completion (extends metric display)
- **User Story 6 (Phase 8)**: Depends on US1 and US2 completion (exports their data)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - DORA Metrics)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P1 - Field Mapping)**: Can start after Foundational (Phase 2) - Parallel with US1, integrates afterward
- **User Story 2 (P2 - Flow Metrics)**: Can start after Foundational (Phase 2) - Independent of US1 but follows same patterns
- **User Story 4 (P2 - Time Period)**: Requires US1 and US2 callbacks - Extends both dashboards
- **User Story 5 (P3 - Trends)**: Requires US1 and US2 metrics - Adds visualization layer
- **User Story 6 (P3 - Export)**: Requires US1 and US2 data - Adds export capability

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Configuration modules before calculators
- Calculators before UI components
- UI components before callbacks
- Callbacks registered last
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 Setup**: T001, T002, T003 can all run in parallel (different config files)
- **Phase 2 Foundational**: T005, T006 can run in parallel (different modules), T007, T008, T009 tests can run in parallel
- **User Story 1 Tests**: T010-T014 can all run in parallel (different test functions)
- **User Story 1 Implementation**: T017, T018 can run in parallel (UI and visualization separate)
- **User Stories 1 and 3**: Can be worked on in parallel by different developers after Phase 2
- **User Story 2**: Can be worked on in parallel with US4 if team has capacity
- **Polish Phase**: T066-T069, T071-T072 can all run in parallel (different files)

---

## Parallel Example: User Story 1 Implementation

```bash
# After tests are written and failing, launch parallel implementation:
Task T017: "Create DORA dashboard UI: ui/dora_metrics_dashboard.py"
Task T018: "Create DORA charts module: visualization/dora_charts.py"

# Both can proceed simultaneously as they work on different files
# T019 (callback) must wait for T016 (calculator) but can use T017/T018 results
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 3 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 - DORA Metrics (T010-T022)
4. Complete Phase 4: User Story 3 - Field Mapping (T023-T030)
5. **STOP and VALIDATE**: Test DORA metrics with field mapping configuration
6. Deploy/demo if ready - Core value delivered!

### Incremental Delivery

1. Complete Setup + Foundational (T001-T009) → Foundation ready
2. Add User Story 1 + 3 (T010-T030) → Test independently → Deploy/Demo (MVP with DORA metrics!)
3. Add User Story 2 (T031-T043) → Test independently → Deploy/Demo (Add Flow metrics)
4. Add User Story 4 (T044-T051) → Test independently → Deploy/Demo (Add time period selection)
5. Add User Story 5 (T052-T058) → Test independently → Deploy/Demo (Add trend analysis)
6. Add User Story 6 (T059-T065) → Test independently → Deploy/Demo (Add export capability)
7. Complete Polish (T066-T075) → Final production-ready release

Each phase adds value without breaking previous functionality.

### Parallel Team Strategy

With multiple developers after Foundational phase (T004-T009) completes:

- **Developer A**: User Story 1 - DORA Metrics (T010-T022)
- **Developer B**: User Story 3 - Field Mapping (T023-T030)
- **Developer C**: User Story 2 - Flow Metrics (T031-T043) - can start in parallel or after US1

All three can work independently and integrate smoothly.

---

## Performance Targets

| Operation                      | Target  | Validation Task |
| ------------------------------ | ------- | --------------- |
| Metric calculation (5k issues) | < 15s   | T070            |
| Page load                      | < 2s    | Manual testing  |
| Cache hit                      | < 200ms | T008            |
| Chart rendering                | < 500ms | T052            |
| UI interaction                 | < 100ms | Manual testing  |

---

## Test Coverage Summary

- **Unit Tests**: 25 test tasks covering calculators, UI components, and data modules
- **Integration Tests**: 8 test tasks covering end-to-end workflows
- **Performance Tests**: 1 dedicated task (T070) for large dataset validation
- **Total Test Tasks**: 34 out of 75 total tasks (45% test coverage)

All tests use tempfile isolation to comply with constitution principle II (Test Isolation).

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label (US1, US2, etc.) maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests written FIRST (TDD approach) - verify they fail before implementation
- Commit after each task or logical group of tasks
- Stop at any checkpoint to validate story independently
- File paths follow existing project structure: callbacks/, data/, ui/, visualization/, configuration/, tests/
- All new files integrate with existing architecture (layered architecture, JSON persistence, Dash framework)
- Constitution compliance: Layered architecture maintained, test isolation enforced, performance budgets defined

---

## Estimated Effort

- **Phase 1 (Setup)**: 0.5 days
- **Phase 2 (Foundational)**: 2 days
- **Phase 3 (US1 - DORA)**: 3 days
- **Phase 4 (US3 - Field Mapping)**: 2 days
- **Phase 5 (US2 - Flow)**: 3 days
- **Phase 6 (US4 - Time Period)**: 1.5 days
- **Phase 7 (US5 - Trends)**: 1.5 days
- **Phase 8 (US6 - Export)**: 1 day
- **Phase 9 (Polish)**: 1.5 days

**Total**: ~16 development days (3.2 weeks with testing)

**MVP (US1 + US3)**: ~8 days (1.6 weeks)
