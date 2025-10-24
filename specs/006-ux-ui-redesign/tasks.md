---
description: "Task list for UX/UI and Architecture Redesign implementation"
---

# Tasks: Unified UX/UI and Architecture Redesign

**Input**: Design documents from `/specs/006-ux-ui-redesign/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/component-builders.md, contracts/callbacks.md, quickstart.md

**Tests**: Comprehensive test coverage is included for validation and quality assurance (Phase 9: Integration & Testing). Tests are written after implementation to verify functionality, not using strict TDD red-green-refactor approach. All new code should have >80% test coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Web application structure:
- UI layer: `ui/` (presentation components)
- Callbacks: `callbacks/` (event handlers)
- Business logic: `data/` (calculations, persistence)
- Tests: `tests/unit/`, `tests/integration/`
- Assets: `assets/` (CSS, JavaScript)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and design system foundation

- [ ] T001 Verify branch `006-ux-ui-redesign` exists and is current
- [ ] T002 [P] Document current state by capturing screenshots of existing UI for comparison in `specs/006-ux-ui-redesign/docs/before/`
- [ ] T003 [P] Review and understand current codebase structure in `ui/`, `callbacks/`, and `data/` directories
- [ ] T004 [P] Verify all dependencies are installed: Dash 3.1.1, dash-bootstrap-components 2.0.2, Plotly, pytest 8.3.4, playwright

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Design system and component infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Enhance design tokens in `ui/style_constants.py` with complete DESIGN_TOKENS structure including colors, spacing, typography, layout, and animation values
- [X] T006 [P] Create base component builder utilities in `ui/button_utils.py` following component-builders.md contracts for atoms (buttons, icons)
- [X] T007 [P] Create input field builders in `ui/components.py` following component-builders.md contracts for labeled inputs
- [X] T008 [P] Create card component builders in `ui/cards.py` following component-builders.md contracts for info cards
- [X] T009 Create tab configuration registry TAB_CONFIG in `ui/tabs.py` defining all 6 tabs with order, icons, colors, and help content IDs
- [X] T010 [P] Create navigation state entity schemas in `data/schema.py` for NavigationState, ParameterPanelState, MobileNavigationState, and LayoutPreferences
- [X] T011 [P] Add design tokens export to CSS variables in `assets/custom.css` for runtime styling consistency
- [X] T012 Verify design system foundation by creating sample components using new builders in a test file (can be deleted after verification)

**Checkpoint**: Foundation ready - design system established, component builders available, user story implementation can now begin

---

## Phase 3: User Story 1 - Quick Parameter Adjustments While Viewing Charts (Priority: P1) 🎯 MVP

**Goal**: Allow users to adjust forecast parameters (PERT factors, deadlines, scope) while viewing charts without scrolling

**Independent Test**: Verify parameter controls are visible in a collapsible sticky panel below header when viewing any chart. Test by: (1) Viewing burndown chart, (2) Expanding parameter panel, (3) Adjusting deadline, (4) Verify chart updates without scrolling required.

### Implementation for User Story 1

- [X] T013 [P] [US1] Create ParameterPanelState entity implementation in `data/persistence.py` with load/save functions for localStorage
- [X] T014 [P] [US1] Create parameter panel collapsed bar component in `ui/components.py` using `create_parameter_bar_collapsed()` showing key values and expand button
- [X] T015 [US1] Create parameter panel expanded section component in `ui/components.py` using `create_parameter_panel_expanded()` with responsive grid layout of all input fields
- [X] T016 [US1] Implement complete collapsible parameter panel organism in `ui/components.py` using `create_parameter_panel()` combining collapsed bar and dbc.Collapse expanded section
- [X] T017 [US1] Create client-side callback for parameter panel toggle in `callbacks/settings.py` using `toggle_parameter_panel()` to handle expand/collapse without server round-trip
- [X] T018 [US1] Create server-side callback for parameter summary update in `callbacks/settings.py` using `update_parameter_summary()` to display current values in collapsed bar
- [X] T019 [US1] Add sticky positioning CSS for parameter panel in `assets/custom.css` with `.param-panel-sticky` class using `position: sticky; top: 60px; z-index: 1020;`
- [X] T020 [US1] Integrate parameter panel into main layout in `ui/layout.py` by adding it below header and above tab content
- [X] T021 [US1] Add parameter panel state persistence callback in `callbacks/settings.py` using dcc.Store to save is_open state to localStorage
- [X] T022 [US1] Update existing parameter change callbacks in `callbacks/settings.py` to read from new parameter panel input field IDs
- [X] T023 [US1] Test parameter panel collapse/expand functionality manually across all tabs to verify no layout shifts
- [X] T024 [US1] Test parameter changes update charts immediately while panel remains visible and accessible

**Checkpoint**: Parameter panel is sticky, collapsible, shows key values when collapsed, and all parameters are accessible while viewing charts

---

## Phase 4: User Story 2 - Dashboard as Primary Landing View (Priority: P1)

**Goal**: Show Project Dashboard with summary metrics immediately when opening app as the first tab and default view

**Independent Test**: Open application in fresh browser session. Verify Dashboard tab is active and displays completion forecast, remaining work, and velocity metrics within 2 seconds without requiring navigation.

### Implementation for User Story 2

- [X] T025 [P] [US2] Create DashboardMetrics calculation function in `data/processing.py` using `calculate_dashboard_metrics(statistics, settings)` returning all metric fields defined in data-model.md
- [X] T026 [P] [US2] Create PERTTimelineData calculation function in `data/processing.py` using `calculate_pert_timeline(statistics, settings)` returning optimistic/pessimistic/most-likely dates
- [X] T027 [P] [US2] Create dashboard metrics card organism in `ui/cards.py` using `create_dashboard_metrics_card(metrics, card_type, variant)` for forecast, velocity, remaining, and PERT cards
- [X] T028 [P] [US2] Create dashboard PERT timeline visualization function in `visualization/charts.py` using `create_pert_timeline_chart(pert_data)` returning horizontal timeline Plotly figure
- [X] T029 [US2] Create dashboard layout module in `ui/dashboard.py` with `create_dashboard_layout()` composing metrics cards in responsive grid (2x2 on desktop, stacked on mobile)
- [X] T030 [US2] Create dashboard callbacks module in `callbacks/dashboard.py` with `update_dashboard_metrics()` callback following contracts/callbacks.md DC-001 specification
- [X] T031 [US2] Add dashboard PERT timeline callback in `callbacks/dashboard.py` with `update_pert_timeline()` following contracts/callbacks.md DC-002 specification
- [X] T032 [US2] Update TAB_CONFIG in `ui/tabs.py` to set Dashboard tab order=0 (first position) with id="tab-dashboard", icon="fa-tachometer-alt", label="Dashboard"
- [X] T033 [US2] Create dashboard tab component in `ui/tabs.py` using `create_tab_item("Dashboard", "tab-dashboard", icon="tachometer-alt", content=dashboard_layout)` - ✅ TAB_CONFIG already includes dashboard
- [X] T034 [US2] Register dashboard callbacks in `callbacks/__init__.py` by importing and registering all callbacks from callbacks/dashboard.py
- [X] T035 [US2] Create navigation initialization callback in `callbacks/mobile_navigation.py` using `initialize_default_tab()` to return "tab-dashboard" on app load - ✅ Updated default tab in mobile navigation
- [X] T036 [US2] Update main layout in `ui/layout.py` to ensure Dashboard tab is first in dbc.Tabs children array - ✅ Updated active_tab to tab-dashboard in create_tabs()
- [X] T037 [US2] Test Dashboard loads as default on fresh app startup and displays all metric cards
- [X] T038 [US2] Test Dashboard metrics update when parameter panel values change
- [X] T039 [US2] Test Dashboard cards are clickable and navigate to corresponding detail chart tabs

**Checkpoint**: Dashboard tab is first in navigation, loads by default, displays all key metrics within 2 seconds, and metrics update with parameter changes

---

## Phase 5: User Story 3 - Consistent Visual Language and Component Patterns (Priority: P2)

**Goal**: Ensure all UI components use consistent styling, navigation patterns, and interaction behaviors across all views

**Independent Test**: Audit all tabs and verify 100% component compliance with design tokens. Check that all buttons use same variants, all cards have consistent padding/shadows, all inputs share focus states, and navigation uses consistent active states.

### Implementation for User Story 3

- [ ] T040 [P] [US3] Refactor all existing buttons in `ui/layout.py` to use `create_action_button()` from `ui/button_utils.py` instead of inline dbc.Button definitions
- [ ] T041 [P] [US3] Refactor all existing input fields in `ui/components.py` to use `create_input_field()` or `create_labeled_input()` builders instead of inline definitions
- [ ] T042 [P] [US3] Refactor existing forecast info card in `ui/cards.py` to use `create_info_card()` builder with standardized styling
- [ ] T043 [P] [US3] Refactor existing statistics cards in `ui/cards.py` to use `create_info_card()` builder replacing inline styling
- [ ] T044 [US3] Update tab navigation styling in `ui/tabs.py` to use design tokens for active state: primary color background with rgba opacity for all tabs
- [ ] T045 [US3] Update mobile bottom navigation styling in `ui/mobile_navigation.py` to match desktop tab active states using same design tokens
- [ ] T046 [US3] Create consistent card styling mixin in `assets/custom.css` using `.card-consistent` class with standardized border-radius, box-shadow, and padding from design tokens
- [ ] T047 [US3] Apply consistent card styling to all existing cards by adding `.card-consistent` class or using card builder variants
- [ ] T048 [US3] Standardize all form input focus states in `assets/custom.css` using `.form-control:focus` selector with primary color border and box-shadow
- [ ] T049 [US3] Audit and update all color values in `assets/custom.css` to reference CSS variables from design tokens instead of hardcoded hex values
- [ ] T050 [US3] Create visual consistency validation checklist and verify all components across all 6 tabs
- [ ] T051 [US3] Test navigation between tabs shows consistent active state indicators on both desktop and mobile
- [ ] T052 [US3] Test all buttons across app follow semantic color conventions (primary for main actions, danger for destructive, secondary for cancel)

**Checkpoint**: All UI components use design tokens, consistent styling achieved across all views, navigation patterns unified

---

## Phase 6: User Story 4 - Unified Software Architecture with Clear Separation (Priority: P2)

**Goal**: Establish clear separation of concerns with consistent patterns for event handling, state management, and component composition

**Independent Test**: Code review against architecture guidelines verifying: (1) No data persistence in UI code, (2) No business logic in callbacks, (3) State managed centrally in dcc.Store, (4) All components follow builder pattern. Measure reduced cross-layer dependencies.

### Implementation for User Story 4

- [ ] T053 [P] [US4] Audit all callback modules in `callbacks/` directory to identify business logic that should move to `data/processing.py`
- [ ] T054 [P] [US4] Extract business logic from `callbacks/visualization.py` into dedicated calculation functions in `data/processing.py`
- [ ] T055 [P] [US4] Extract business logic from `callbacks/statistics.py` into dedicated calculation functions in `data/processing.py`
- [ ] T056 [P] [US4] Extract business logic from `callbacks/settings.py` into validation and transformation functions in `data/processing.py`
- [ ] T057 [US4] Create centralized state management module in `data/state_management.py` with functions for initializing, updating, and validating all UI state containers
- [ ] T058 [US4] Document state container naming conventions in `data/state_management.py` docstring with standardized names: settings-store, statistics-store, ui-state-store, nav-state-store, and usage patterns for each
- [ ] T059 [US4] Implement NavigationState management in `data/state_management.py` with `update_navigation_state(current, new_tab)` following data-model.md specifications
- [ ] T060 [US4] Update all callbacks to use centralized state management functions instead of inline state manipulation
- [ ] T061 [US4] Create architecture documentation in `specs/006-ux-ui-redesign/docs/architecture.md` documenting layer boundaries and data flow patterns
- [ ] T062 [US4] Add code organization guidelines to architecture docs showing where new features should be added (presentation vs logic vs persistence)
- [ ] T063 [US4] Create callback registration pattern documentation in `callbacks/__init__.py` docstring explaining how to add new callbacks
- [ ] T064 [US4] Verify no callbacks perform file I/O operations using grep/code search: `grep -r "import persistence" callbacks/` should return zero matches (all data operations should delegate to `data/persistence.py`)
- [ ] T065 [US4] Verify no UI components contain calculation logic using grep: `grep -r "def calculate_" ui/` should return zero matches (should delegate to `data/processing.py`)
- [ ] T066 [US4] Verify all components use design tokens by searching: `grep -r "DESIGN_TOKENS" ui/` should show usage in all component files
- [ ] T067 [US4] Run code complexity analysis to verify separation of concerns and document in architecture.md

**Checkpoint**: Clear separation between presentation, business logic, and data layers. Consistent patterns for adding new features.

---

## Phase 7: User Story 5 - Responsive Layout with Optimized Mobile Experience (Priority: P3)

**Goal**: Optimize layouts for mobile devices with touch-friendly controls, adapted navigation patterns, and prioritized essential information

**Independent Test**: Test on devices 320px-768px width verifying: (1) Touch targets minimum 44px, (2) Critical info above fold, (3) Navigation accessible without obscuring content, (4) Keyboard doesn't break layout. Measure mobile task completion rates.

### Implementation for User Story 5

- [ ] T068 [P] [US5] Create mobile parameter bottom sheet component in `ui/components.py` using `create_mobile_parameter_sheet()` as alternative to sticky panel for <768px viewports
- [ ] T069 [P] [US5] Create mobile-specific responsive breakpoints in `assets/custom.css` with media queries for 320px, 375px, 425px, 768px, and 992px
- [ ] T070 [P] [US5] Implement touch target size validation utility in `ui/style_constants.py` with `TOUCH_TARGET_MIN = "44px"` constant
- [ ] T071 [US5] Update parameter panel implementation in `ui/components.py` to conditionally render bottom sheet on mobile (<768px) and sticky panel on desktop
- [ ] T072 [US5] Create viewport detection callback in `callbacks/mobile_navigation.py` using `detect_viewport_size()` to update MobileNavigationState
- [ ] T073 [US5] Implement mobile bottom sheet toggle callback in `callbacks/mobile_navigation.py` using `toggle_mobile_bottom_sheet()` for FAB button
- [ ] T074 [US5] Update Dashboard layout in `ui/dashboard.py` to stack cards vertically on mobile with most critical metrics (forecast, completion) first
- [ ] T075 [US5] Add mobile-optimized chart configurations in `visualization/charts.py` with `get_mobile_chart_config()` reducing margins and hiding legends on small screens
- [ ] T076 [US5] Update all chart callbacks to detect viewport and apply mobile config when width < 768px
- [ ] T077 [US5] Create swipe gesture support for mobile tab navigation in `assets/mobile_navigation.js` using touch event listeners
- [ ] T078 [US5] Implement tablet landscape mode hybrid layout in `assets/custom.css` with sidebar navigation for 768px-992px viewports showing persistent navigation sidebar with media query `@media (min-width: 768px) and (max-width: 992px)`
- [ ] T079 [US5] Add keyboard appearance handling in `assets/mobile_navigation.js` to resize parameter sheet when virtual keyboard appears
- [ ] T080 [US5] Test all touch targets meet 44px minimum on mobile devices using browser dev tools mobile emulation
- [ ] T081 [US5] Test mobile bottom sheet swipe-to-dismiss functionality on actual touch devices (iOS Safari, Android Chrome)
- [ ] T082 [US5] Test mobile keyboard appearance handling with actual iOS/Android devices to verify parameter sheet resizes correctly when virtual keyboard appears and active input field remains visible
- [ ] T083 [US5] Test tablet landscape mode shows sidebar navigation with primary content area for charts

**Checkpoint**: Mobile experience optimized with touch-friendly controls, adapted navigation, and responsive layouts from 320px to 1920px

---

## Phase 8: User Story 6 - Contextual Help System with Progressive Disclosure (Priority: P3)

**Goal**: Provide contextual help that explains features when needed without cluttering the interface

**Independent Test**: Track help tooltip usage, measure time to first successful task for new users, verify help content accessible within one click from all features. Measure reduced support requests.

### Implementation for User Story 6

- [ ] T084 [P] [US6] Create help tooltip component in `ui/help_system.py` using `create_help_tooltip(content, target_id, placement)` with consistent styling
- [ ] T085 [P] [US6] Create help modal component in `ui/help_system.py` using `create_help_modal(title, content, modal_id)` for detailed explanations
- [ ] T086 [P] [US6] Add help content definitions in `configuration/help_content.py` for all Dashboard metrics (completion forecast, velocity, remaining work, PERT)
- [ ] T087 [P] [US6] Add help content definitions in `configuration/help_content.py` for all parameter inputs (PERT factor, deadline, scope values)
- [ ] T088 [US6] Add help icons to Dashboard metric cards in `ui/cards.py` using `create_icon("info-circle", variant="muted")` with tooltip triggers
- [ ] T089 [US6] Add help icons to parameter panel inputs in `ui/components.py` next to each label with contextual explanations
- [ ] T090 [US6] Create help tooltip callback in `callbacks/help_system.py` (if needed for dynamic content) or use client-side tooltips via Bootstrap
- [ ] T091 [US6] Update help modal callback in existing help system to support new help content IDs for Dashboard and parameters
- [ ] T092 [US6] Add mobile-optimized help display in `assets/help_system.css` with full-screen overlay for <768px viewports
- [ ] T093 [US6] Create first-time user guide prompt in `ui/help_system.py` with dismissible banner pointing to key features (shown once, stored in localStorage)
- [ ] T094 [US6] Test help tooltips appear on hover (desktop) and tap (mobile) without obscuring related content
- [ ] T095 [US6] Test help modals display properly on mobile with easy dismiss via outside click or close button
- [ ] T096 [US6] Test help content is concise (<50 words for tooltips) and "Learn more" links work correctly

**Checkpoint**: Contextual help available throughout app, progressive disclosure implemented, first-time user guidance provided

---

## Phase 9: Integration & Testing

**Purpose**: Validate all user stories work together and meet acceptance criteria

- [ ] T097 [P] Create integration test suite in `tests/integration/dashboard/test_dashboard_workflow.py` using Playwright to verify Dashboard loads and displays metrics
- [ ] T098 [P] Create integration test in `tests/integration/dashboard/test_parameter_panel_workflow.py` verifying parameter changes update Dashboard without scrolling
- [ ] T099 [P] Create integration test in `tests/integration/navigation/test_tab_navigation.py` verifying tab switching maintains state and Dashboard is default
- [ ] T100 [P] Create unit tests for dashboard metrics calculations in `tests/unit/data/test_dashboard_metrics.py` covering edge cases (no data, zero velocity, past deadline)
- [ ] T101 [P] Create unit tests for component builders in `tests/unit/ui/test_component_builders.py` verifying all builders follow contracts and use design tokens
- [ ] T102 [P] Create unit tests for navigation state management in `tests/unit/data/test_navigation_state.py` verifying state transitions and history tracking
- [ ] T103 Run full test suite with `.\.venv\Scripts\activate; pytest tests/ -v --cov=ui --cov=callbacks --cov=data` and verify >80% coverage for new code
- [ ] T104 Perform manual cross-browser testing on Chrome, Firefox, Safari, and Edge verifying all features work consistently
- [ ] T105 Perform manual mobile device testing on iOS Safari and Android Chrome verifying touch interactions and responsive layouts
- [ ] T106 Verify all success criteria from spec.md are met: (1) Zero scroll events for parameter access, (2) Dashboard loads <2s, (3) 100% design token compliance, (4) 44px touch targets
- [ ] T107 Create before/after comparison documentation in `specs/006-ux-ui-redesign/docs/comparison.md` with screenshots showing improvements

**Checkpoint**: All user stories tested and validated, integration verified, success criteria confirmed

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and documentation

- [ ] T108 [P] Optimize Dashboard metrics calculation performance in `data/processing.py` to ensure <50ms execution time
- [ ] T109 [P] Add loading states for all async operations using dbc.Spinner with consistent styling
- [ ] T110 [P] Implement error boundaries in callbacks to gracefully handle missing data with user-friendly messages
- [ ] T111 [P] Add transition animations in `assets/custom.css` for parameter panel expand/collapse (300ms ease-in-out)
- [ ] T112 Update main `readme.md` with new feature descriptions and updated screenshots showing Dashboard and parameter panel
- [ ] T113 Create developer documentation in `specs/006-ux-ui-redesign/docs/developer-guide.md` explaining how to add new dashboard cards and metrics
- [ ] T114 Update `quickstart.md` with lessons learned and any implementation deviations from original plan
- [ ] T115 Run performance benchmarks comparing before/after to verify ≤10% performance regression threshold
- [ ] T116 Create accessibility audit checklist and verify ARIA labels, keyboard navigation, and screen reader compatibility
- [ ] T117 Final code review focusing on architecture compliance and component consistency
- [ ] T118 Update `.github/copilot-instructions.md` with any new patterns or conventions established during implementation

**Checkpoint**: Feature complete, documented, optimized, and ready for deployment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 and US2 (P1 priority) can proceed in parallel after Phase 2
  - US3 and US4 (P2 priority) can proceed in parallel after Phase 2, but benefit from US1/US2 completion
  - US5 and US6 (P3 priority) can proceed after Phase 2, but benefit from all P1/P2 stories
- **Integration & Testing (Phase 9)**: Depends on all desired user stories being complete
- **Polish (Phase 10)**: Depends on Phase 9 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Uses component builders from Phase 2 but independent of US1
- **User Story 3 (P2)**: Benefits from US1/US2 having components to refactor, but can start after Phase 2
- **User Story 4 (P2)**: Independent of other stories, can start after Phase 2 - focuses on architecture cleanup
- **User Story 5 (P3)**: Benefits from US1 parameter panel existing to create mobile variant
- **User Story 6 (P3)**: Independent, can start after Phase 2 - adds help to any existing components

### Within Each User Story

- **US1**: T014 and T015 can run in parallel (collapsed bar and expanded section), then T016 combines them
- **US2**: T025-T028 can all run in parallel (calculations and UI components), then T029-T033 compose them
- **US3**: T040-T043 can all run in parallel (refactoring different component types)
- **US4**: T053-T056 can all run in parallel (auditing different callback modules)
- **US5**: T066-T069 can run in parallel (mobile components and breakpoints)
- **US6**: T081-T084 can all run in parallel (help components and content)

### Parallel Opportunities

**Phase 1 Setup**: T002, T003, T004 can run in parallel

**Phase 2 Foundational**: T006, T007, T008, T010, T011 can all run in parallel after T005 design tokens are established

**Phase 3 (US1)**: T013 and T014 can run in parallel

**Phase 4 (US2)**: T025, T026, T027, T028 can all run in parallel - different file locations

**Phase 5 (US3)**: T040, T041, T042, T043 can all run in parallel - refactoring different files

**Phase 6 (US4)**: T053, T054, T055, T056 can all run in parallel - auditing different files

**Phase 7 (US5)**: T066, T067, T068 can all run in parallel at start of phase

**Phase 8 (US6)**: T081, T082, T083, T084 can all run in parallel

**Phase 9 Integration**: T094, T095, T096, T097, T098, T099 can all run in parallel - independent test files

**Phase 10 Polish**: T105, T106, T107, T108 can all run in parallel

---

## Parallel Example: User Story 2 (Dashboard)

```bash
# Launch all calculation and UI component tasks together:
Task: "Create DashboardMetrics calculation function in data/processing.py"
Task: "Create PERTTimelineData calculation function in data/processing.py"
Task: "Create dashboard metrics card organism in ui/cards.py"
Task: "Create dashboard PERT timeline visualization function in visualization/charts.py"

# All above tasks work on different files with no dependencies
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (8 tasks) - CRITICAL foundation
3. Complete Phase 3: User Story 1 (12 tasks) - Parameter panel accessibility
4. Complete Phase 4: User Story 2 (15 tasks) - Dashboard as landing view
5. **STOP and VALIDATE**: Test US1 + US2 independently
6. Deploy/demo MVP with core functionality

**MVP Value**: Users can see Dashboard on load (US2) and adjust parameters without scrolling (US1) - addresses primary pain points

### Incremental Delivery

1. **Sprint 1**: Setup + Foundational → Design system ready
2. **Sprint 2**: User Story 1 → Parameter panel working → Test independently
3. **Sprint 3**: User Story 2 → Dashboard as default → Test independently → **Deploy MVP**
4. **Sprint 4**: User Story 3 → Visual consistency → Test → Deploy
5. **Sprint 5**: User Story 4 → Architecture cleanup → Test → Deploy
6. **Sprint 6**: User Story 5 → Mobile optimization → Test → Deploy
7. **Sprint 7**: User Story 6 + Integration + Polish → Complete feature

### Parallel Team Strategy

With 3 developers after Foundational phase completes:

- **Developer A**: User Story 1 (Parameter Panel) - 12 tasks
- **Developer B**: User Story 2 (Dashboard) - 15 tasks  
- **Developer C**: User Story 3 (Visual Consistency) - 13 tasks

Then collaborate on US4, US5, US6, testing, and polish.

---

## Notes

- All tasks follow PowerShell development environment requirements (Windows with `.\.venv\Scripts\activate;` prefix)
- Component builders must follow contracts in `specs/006-ux-ui-redesign/contracts/component-builders.md`
- Callbacks must follow contracts in `specs/006-ux-ui-redesign/contracts/callbacks.md`
- Design tokens from `ui/style_constants.py` MUST be used instead of inline styles
- No changes to existing data formats in `data/persistence.py` (backward compatibility maintained)
- Playwright recommended for new integration tests over Selenium
- Mobile breakpoint: <768px, Tablet: 768px-992px, Desktop: ≥992px
- Touch targets on mobile must be minimum 44px × 44px
- Performance target: ≤10% regression from baseline
- Each user story should be independently testable before moving to next
- [P] tasks can run in parallel - different files, no dependencies
- [Story] label maps task to specific user story for traceability

---

## Total Task Count: 118 tasks

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 8 tasks
- Phase 3 (US1): 12 tasks
- Phase 4 (US2): 15 tasks
- Phase 5 (US3): 13 tasks
- Phase 6 (US4): 16 tasks (+3 verification tasks)
- Phase 7 (US5): 16 tasks (+1 keyboard test)
- Phase 8 (US6): 13 tasks
- Phase 9 (Integration): 11 tasks
- Phase 10 (Polish): 11 tasks

**By User Story**:
- User Story 1 (P1 - Parameter Panel): 12 tasks
- User Story 2 (P1 - Dashboard): 15 tasks
- User Story 3 (P2 - Visual Consistency): 13 tasks
- User Story 4 (P2 - Architecture): 16 tasks (+3 for verification and state naming)
- User Story 5 (P3 - Mobile): 16 tasks (+1 for keyboard handling test)
- User Story 6 (P3 - Help System): 13 tasks
- Setup + Foundational + Integration + Polish: 34 tasks

**Parallel Opportunities**: 43 tasks marked [P] can run in parallel within their phase

**MVP Scope**: Phases 1-4 (43 tasks) deliver core value - parameter accessibility and dashboard landing view

**Implementation Time Estimate**: 
- MVP (US1 + US2): ~2-3 weeks with 1-2 developers
- Full feature (all 6 stories): ~6-8 weeks with 2-3 developers
- Parallel team (3 devs): ~4-5 weeks for full feature
