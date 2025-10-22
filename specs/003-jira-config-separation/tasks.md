# Tasks: JIRA Configuration Separation

**Input**: Design documents from `/specs/003-jira-config-separation/`
**Prerequisites**: plan.md (tech stack), spec.md (user stories P1-P3), research.md (8 decisions), data-model.md (2 entities), contracts/dash-callbacks.md (6 callbacks)

**Tests**: This feature specification does NOT explicitly request tests. Tests are marked OPTIONAL and may be added later per constitutional amendments (test-first is aspirational, not blocking).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Project structure: Dash web application with `ui/`, `callbacks/`, `data/`, `tests/` at repository root
- Follows existing patterns in `ui/cards.py`, `data/persistence.py`, `callbacks/settings.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify prerequisites and create basic structure for new components

- [X] T001 Verify Python 3.11+ environment and virtual environment activated
- [X] T002 Verify all dependencies installed (Dash 3.1.1, dash-bootstrap-components 2.0.2, Flask 3.1.0, requests 2.32.3)
- [X] T003 Review existing code patterns in ui/cards.py, data/persistence.py, callbacks/settings.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data persistence and connection testing infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add `load_jira_configuration()` function to data/persistence.py
- [X] T005 [P] Add `save_jira_configuration()` function to data/persistence.py
- [X] T006 [P] Add `validate_jira_config()` function to data/persistence.py with validation rules from data-model.md
- [X] T007 [P] Add `migrate_jira_config()` function to data/persistence.py for backward compatibility with legacy jira_token field
- [X] T008 [P] Add `get_default_jira_config()` helper function to data/persistence.py
- [X] T009 Add `construct_jira_endpoint()` function to data/jira_simple.py for URL construction
- [X] T010 [P] Add `test_jira_connection()` function to data/jira_simple.py with 10-second timeout and error handling per research.md Section 4

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Initial JIRA Configuration (Priority: P1) 🎯 MVP

**Goal**: Enable first-time users to configure JIRA connection settings once (base URL, token, API version, cache settings) with connection testing and persistence

**Independent Test**: Open the app as a new user, click "Configure JIRA" button, fill in valid JIRA credentials (base URL, token), test connection, save configuration, verify settings persist on reload

### Implementation for User Story 1

- [X] T011 [P] [US1] Create `create_jira_config_modal()` function in ui/jira_config_modal.py with Bootstrap modal structure and 6 form fields per data-model.md
- [X] T012 [P] [US1] Create `create_jira_config_button()` function in ui/jira_config_modal.py for "Configure JIRA" button
- [X] T013 [US1] Add modal callback module: create callbacks/jira_config.py with module docstring and imports
- [X] T014 [P] [US1] Implement "Open Modal" callback in callbacks/jira_config.py (Input: jira-config-button n_clicks, Output: jira-config-modal is_open) per contracts/dash-callbacks.md
- [X] T015 [P] [US1] Implement "Load Configuration" callback in callbacks/jira_config.py (Input: modal is_open, Output: 6 form field values) per contracts/dash-callbacks.md
- [X] T016 [US1] Implement "Test Connection" callback in callbacks/jira_config.py (Input: test button n_clicks, State: base_url/api_version/token, Output: connection status alert) per contracts/dash-callbacks.md
- [X] T017 [US1] Implement "Save Configuration" callback in callbacks/jira_config.py (Input: save button n_clicks, State: all 6 form fields, Output: modal close + status) per contracts/dash-callbacks.md
- [X] T018 [P] [US1] Implement "Cancel Configuration" callback in callbacks/jira_config.py (Input: cancel button n_clicks, Output: modal close) per contracts/dash-callbacks.md
- [X] T019 [US1] Add jira_config_modal import and component to ui/layout.py or ui/cards.py (integrate modal into app layout)
- [X] T020 [US1] Add configuration button to Data Source card in ui/cards.py via create_jira_config_button()
- [X] T021 [US1] Add callback registration to app.py if needed (verify callbacks are auto-discovered)
- [X] T022 [US1] Test complete workflow: open modal, enter valid config, test connection (should succeed), save, verify app_settings.json updated with jira_config structure
- [X] T023 [US1] Test persistence: restart app, reopen modal, verify form fields pre-filled with saved configuration

**Checkpoint**: At this point, User Story 1 should be fully functional - users can configure JIRA settings and persist them

---

## Phase 4: User Story 2 - Modifying Existing Configuration (Priority: P2)

**Goal**: Enable existing users to update JIRA configuration settings (token refresh, cache tuning, API version change) without disrupting saved JQL queries

**Independent Test**: With existing JIRA configuration, open config modal, modify token or cache settings, save, verify changes take effect without affecting JQL query profiles in jira_query_profiles.json

### Implementation for User Story 2

- [X] T024 [US2] Add pre-filled form state handling to "Load Configuration" callback in callbacks/jira_config.py (display current values when user has existing config)
- [X] T025 [US2] Add last_test_timestamp and last_test_success display to modal in ui/jira_config_modal.py (show when connection was last tested)
- [X] T026 [US2] Add validation warning in callbacks/jira_config.py for high cache_size_mb values (>500MB) per data-model.md business rule
- [X] T027 [US2] Update "Save Configuration" callback in callbacks/jira_config.py to preserve existing jira_config fields not shown in form
- [X] T028 [US2] Add API version change warning in ui/jira_config_modal.py (inform users when switching v2 ↔ v3) per research.md Section 2
- [X] T032.5 [US2] Remove legacy JIRA field duplication: update save_app_settings() to stop writing duplicate fields, update get_jira_config() to read from jira_config structure, remove unused helper functions, add automatic cleanup on load
- [X] T032.6 [UX] Improve modal button layout and message behavior: separate Save/Close actions, keep modal open after save, auto-dismiss success messages (4s), improve button hierarchy (Cancel left, Test/Save right)
- [ ] T029 [US2] Test configuration update workflow: modify token, test connection (verify new token validated), save, verify JQL query profiles remain intact
- [ ] T030 [US2] Test cancel workflow: open modal, change settings, click cancel, reopen modal, verify changes were not saved
- [ ] T031 [US2] Test API version switch: change v3 to v2, save, verify construct_jira_endpoint() generates correct path (/rest/api/2/search)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - initial config and modification workflows are functional

---

## Phase 5: User Story 3 - Simplified JQL Query Workflow (Priority: P3)

**Goal**: Simplify Data Source interface by removing JIRA configuration fields, leaving only JQL query editing functionality

**Independent Test**: With valid JIRA configuration, navigate to Data Source interface, verify only JQL query fields visible, click "Configure JIRA" button to access settings, verify clean separation

### Implementation for User Story 3

- [X] T032 [US3] Remove JIRA URL input field from Data Source card in ui/cards.py (if present)
- [X] T033 [P] [US3] Remove JIRA token input field from Data Source card in ui/cards.py (if present)
- [X] T034 [P] [US3] Remove cache size input field from Data Source card in ui/cards.py (if present)
- [X] T035 [P] [US3] Remove max results input field from Data Source card in ui/cards.py (if present)
- [X] T036 [P] [US3] Remove points field input field from Data Source card in ui/cards.py (if present)
- [X] T037 [US3] Verify "Configure JIRA" button is prominently displayed in Data Source interface (added in T020)
- [X] T038 [US3] Update any callbacks in callbacks/settings.py that reference legacy jira_token field to use jira_config structure from persistence
- [X] T039 [US3] Add configuration status indicator to Data Source card (e.g., "JIRA Connected ✓" or "Configure JIRA to begin")
- [X] T040 [US3] Add error handling for unconfigured state: display helpful message with "Configure JIRA" button when user tries to query without configuration per FR-018
- [ ] T041 [US3] Test simplified Data Source interface: verify only JQL query fields remain, count fields removed (target: 5+ per SC-005)
- [ ] T042 [US3] Test unconfigured workflow: reset app_settings.json jira_config, restart app, verify user prompted to configure before querying
- [ ] T043 [US3] Test error message with config link: simulate query with invalid token, verify error suggests opening configuration modal

**Checkpoint**: All user stories should now be independently functional - JIRA configuration is fully separated from JQL query interface

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, code quality, and documentation

- [ ] T044 [P] Add mobile-responsive styling to jira_config_modal.py (ensure 44px touch targets per mobile-first guidelines)
- [ ] T045 [P] Add ARIA labels to all form inputs in ui/jira_config_modal.py for screen reader accessibility
- [ ] T046 [P] Add input validation feedback (red/green borders) to form fields in ui/jira_config_modal.py
- [ ] T047 Code review and refactoring: ensure consistent error handling across all callbacks in callbacks/jira_config.py
- [ ] T048 [P] Update app docstrings and type hints in new modules (ui/jira_config_modal.py, callbacks/jira_config.py)
- [ ] T049 Verify all success criteria from spec.md: 3-minute config time (SC-001), 10-second connection test (SC-002), 5+ fields removed (SC-005)
- [ ] T050 Performance testing: verify configuration save/load < 500ms, connection test < 10s per plan.md technical context
- [ ] T051 [P] Manual accessibility testing: keyboard navigation through modal, screen reader compatibility
- [ ] T052 Run quickstart.md validation: complete Phase 1-4 checklist, verify all common pitfalls avoided

**OPTIONAL - Add if needed**:
- [ ] T053 [P] Unit tests for data validation in tests/unit/data/test_persistence.py (validate_jira_config, migrate_jira_config)
- [ ] T054 [P] Unit tests for connection testing in tests/unit/data/test_jira_simple.py (test_jira_connection, construct_jira_endpoint)
- [ ] T055 [P] Unit tests for modal component rendering in tests/unit/ui/test_jira_config_modal.py
- [ ] T056 Playwright integration tests for complete configuration workflow in tests/integration/test_jira_config_workflow.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 modal and callbacks existing (T011-T023)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 configuration button (T020) but can proceed independently

### Within Each User Story

**User Story 1 (P1)**:
1. UI Components first: T011 (modal), T012 (button) - can run in parallel
2. Callback module setup: T013 (create module)
3. Callbacks implementation: T014, T015, T016, T017, T018 - many marked [P] can run in parallel
4. Integration: T019 (add to layout), T020 (add button), T021 (register callbacks)
5. Testing: T022, T023 - sequential after implementation

**User Story 2 (P2)**:
- Most tasks can run in parallel (T024-T028) as they modify different parts of existing components
- Testing tasks (T029-T031) sequential after implementation

**User Story 3 (P3)**:
- UI cleanup tasks (T032-T036) can run in parallel - all marked [P]
- Integration tasks (T037-T040) sequential
- Testing tasks (T041-T043) sequential after implementation

### Parallel Opportunities

**Foundational Phase (Phase 2)**:
```bash
# Can run in parallel after T004:
T005 (save_jira_configuration)
T006 (validate_jira_config)
T007 (migrate_jira_config)
T008 (get_default_jira_config)
T010 (test_jira_connection)

# T009 should complete before T010 (endpoint construction needed for connection test)
```

**User Story 1 (Phase 3)**:
```bash
# Can run in parallel:
T011 (create modal UI)
T012 (create config button)

# Can run in parallel after T013:
T014 (open modal callback)
T015 (load config callback)
T018 (cancel callback)

# T016 (test connection) and T017 (save config) can start after foundational phase
```

**User Story 3 (Phase 5)**:
```bash
# All UI cleanup tasks can run in parallel:
T032 (remove URL field)
T033 (remove token field)
T034 (remove cache field)
T035 (remove max results field)
T036 (remove points field)
```

**Polish Phase (Phase 6)**:
```bash
# Can run in parallel:
T044 (mobile styling)
T045 (ARIA labels)
T046 (validation feedback)
T048 (docstrings)
T051 (accessibility testing)
T053 (unit tests - data validation)
T054 (unit tests - connection)
T055 (unit tests - UI)
```

---

## Parallel Execution Examples

### User Story 1 Parallelization (MVP Focus)

```bash
# Phase 2: Foundational (all required before US1 starts)
Terminal 1: T004 (load_jira_configuration)
Terminal 2: T005, T006, T007, T008 (save/validate/migrate/default functions)
Terminal 3: T009 (construct_jira_endpoint) → T010 (test_jira_connection)

# Phase 3: User Story 1 (after Phase 2 completes)
Terminal 1: T011 (modal UI)
Terminal 2: T012 (button) → T020 (add button to card)
Terminal 3: T013 (callback module) → T014, T015, T018 (callbacks in parallel)
Terminal 4: T016, T017 (test/save callbacks)

# Integration and testing (sequential)
Terminal 1: T019 → T021 → T022 → T023
```

### Full Feature Parallelization (All User Stories)

```bash
# After Foundational Phase 2 completes:

Team Member 1: User Story 1 (T011-T023) - MVP focus
Team Member 2: User Story 2 (T024-T031) - starts after US1 T011-T018 complete
Team Member 3: User Story 3 (T032-T043) - starts after US1 T020 complete

# Polish Phase 6 (after all stories complete):
Team Member 1: T044-T048 (UI improvements)
Team Member 2: T049-T052 (validation and performance)
Team Member 3: T053-T056 (optional tests)
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Recommended**: Implement User Story 1 (P1) ONLY for initial MVP

**Rationale**:
- US1 delivers core value: JIRA configuration with connection testing
- US1 is independently testable and deployable
- US1 completion enables basic JIRA connectivity (foundational for all other features)
- US2 and US3 are enhancements that can be added incrementally

**MVP Tasks**: Phase 1 (T001-T003), Phase 2 (T004-T010), Phase 3 (T011-T023)

**Estimated Time**: 3-4 hours for MVP (Setup 30min + Foundational 1-1.5hr + US1 1.5-2hr)

### Incremental Delivery

**Release 1 (MVP)**: User Story 1 - Initial JIRA Configuration (P1)
- Enables first-time JIRA setup with connection testing and persistence
- Users can configure JIRA and start querying

**Release 2**: User Story 2 - Modifying Existing Configuration (P2)
- Enables configuration updates without disrupting queries
- Improves token refresh and performance tuning workflows

**Release 3**: User Story 3 - Simplified JQL Query Workflow (P3)
- Cleans up Data Source interface
- Removes configuration clutter, focuses on query editing

**Release 4 (Polish)**: Phase 6 - Cross-Cutting Improvements
- Mobile optimization, accessibility, tests
- Performance validation

---

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 7 tasks (BLOCKING - must complete first)
- **Phase 3 (User Story 1 - P1)**: 13 tasks (MVP focus)
- **Phase 4 (User Story 2 - P2)**: 8 tasks
- **Phase 5 (User Story 3 - P3)**: 12 tasks
- **Phase 6 (Polish)**: 13 tasks (4 optional test tasks)

**Total**: 56 tasks (52 required + 4 optional tests)

**Parallel Tasks**: 24 tasks marked [P] can run in parallel (43% parallelizable)

**MVP Task Count**: 23 tasks (Phase 1-3: Setup + Foundational + US1)

**Estimated Time**: 
- MVP (US1 only): 3-4 hours
- Full feature (US1-US3): 4-6 hours per quickstart.md
- With polish and optional tests: 6-8 hours

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] All 3 user stories (P1, P2, P3) implemented and independently testable
- [ ] All 8 success criteria from spec.md validated (SC-001 through SC-008)
- [ ] All 18 functional requirements from spec.md implemented (FR-001 through FR-018)
- [ ] Zero loss of existing JQL query profiles during configuration migration (SC-004)
- [ ] Data Source interface complexity reduced by 5+ fields (SC-005)
- [ ] Configuration save/load operations < 500ms (plan.md technical context)
- [ ] Connection test operations < 10 seconds (SC-002)
- [ ] All constitution gates still pass (Simplicity, Mobile-First, Performance, Accessibility, Testing)
- [ ] Migration function tested with legacy app_settings.json structure
- [ ] Mobile responsiveness verified (modal works on 375px width screens)
- [ ] Keyboard navigation and screen reader compatibility verified
- [ ] Common pitfalls from quickstart.md avoided (token masking, URL normalization, validation, error messages)
