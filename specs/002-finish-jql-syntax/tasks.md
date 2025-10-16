# Implementation Tasks: Complete JQL Syntax Highlighting

**Feature**: Complete JQL Syntax Highlighting with Real-time Visual Feedback  
**Branch**: `002-finish-jql-syntax`  
**Date**: 2025-10-15  
**Status**: Ready for Implementation

## Overview

This document provides dependency-ordered, TDD-driven tasks for implementing real-time JQL syntax highlighting. Tasks are organized by user story to enable independent implementation and testing.

**Implementation Approach**: Test-Driven Development (TDD) - Red → Green → Refactor
- Write failing tests first (RED)
- Implement minimum code to pass tests (GREEN)
- Refactor for quality (REFACTOR)

---

## Task Summary

| Phase     | Story      | Task Count | Can Parallelize | Independent Test                        |
| --------- | ---------- | ---------- | --------------- | --------------------------------------- |
| Phase 1   | Setup      | 3          | No              | N/A (infrastructure)                    |
| Phase 2   | Foundation | 5          | 2 tasks         | N/A (shared code)                       |
| Phase 3   | US1 (P1)   | 14         | 6 tasks         | ✅ Keyword/operator highlighting visible |
| Phase 4   | US2 (P2)   | 6          | 3 tasks         | ✅ ScriptRunner functions highlighted    |
| Phase 5   | US3 (P3)   | 6          | 3 tasks         | ✅ Syntax errors indicated               |
| Phase 6   | Polish     | 4          | 2 tasks         | N/A (cross-cutting)                     |
| **Total** |            | **38**     | **16 parallel** | **3 independent stories**               |

---

## Dependencies & Execution Order

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundation)
    ↓
Phase 3 (US1 - P1) ← MVP (minimum viable product)
    ↓ (optional dependency)
Phase 4 (US2 - P2) ← Can start independently if US1 complete
    ↓ (optional dependency)
Phase 5 (US3 - P3) ← Can start independently if US1 complete
    ↓
Phase 6 (Polish)
```

**Independent Stories**: US1, US2, US3 can be implemented in parallel after Foundation complete.

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (US1) = Core syntax highlighting functionality

---

## Phase 1: Setup & Environment (3 tasks)

**Goal**: Prepare development environment and project structure for syntax highlighting implementation.

**Blocking**: All tasks are sequential (must complete before Phase 2).

### Tasks

- [ ] T001 Create new Python module ui/jql_syntax_highlighter.py with module docstring and imports
- [ ] T002 Create new CSS file assets/jql_syntax.css with file header comment
- [ ] T003 Create new JavaScript file assets/jql_syntax.js with file header comment and IIFE wrapper

---

## Phase 2: Foundation - Shared Components (5 tasks)

**Goal**: Implement shared parsing enhancements and constants needed by all user stories.

**Blocking**: Must complete before any user story implementation (US1, US2, US3).

### Tasks

- [ ] T004 [P] Add SCRIPTRUNNER_FUNCTIONS frozenset to ui/jql_syntax_highlighter.py with 15 core functions
- [ ] T005 [P] Add is_scriptrunner_function() helper function to ui/jql_syntax_highlighter.py
- [ ] T006 Modify parse_jql_syntax() in ui/components.py to detect "function" token type when preceded by "issueFunction in"
- [ ] T007 Modify render_syntax_tokens() in ui/components.py to handle "function" and "error" token types with appropriate CSS classes
- [ ] T008 Add .jql-function, .jql-error-unclosed, .jql-error-invalid CSS classes to assets/custom.css

**Parallel Opportunities**: T004 and T005 can be completed in parallel (independent functions).

---

## Phase 3: User Story 1 (P1) - Real-time Visual Syntax Highlighting (14 tasks)

**Goal**: Implement core dual-layer textarea with real-time syntax highlighting for keywords, strings, and operators.

**Independent Test Criteria**:
✅ User can type "project = TEST AND status = Done" and see:
- "AND" highlighted in blue (keyword)
- "=" highlighted in gray (operator)
- Quoted strings highlighted in green
- Cursor position remains stable during typing
- Highlighting updates within 50ms per keystroke

**Acceptance Scenarios**: 5 scenarios from spec.md (see User Story 1)

### Phase 3A: Tests (TDD Red - 4 tasks)

- [ ] T009 [P] [US1] Write test_create_jql_syntax_highlighter_returns_div() in tests/unit/ui/test_jql_syntax_highlighter.py
- [ ] T010 [P] [US1] Write test_component_has_textarea_and_highlight_div() in tests/unit/ui/test_jql_syntax_highlighter.py
- [ ] T011 [P] [US1] Write test_keyword_highlighting_appears() Playwright test in tests/integration/dashboard/test_jql_highlighting_workflow.py
- [ ] T012 [P] [US1] Write test_operator_highlighting_appears() Playwright test in tests/integration/dashboard/test_jql_highlighting_workflow.py

**Parallel Opportunities**: All 4 test tasks can be written simultaneously (independent test cases).

### Phase 3B: Component Implementation (TDD Green - 3 tasks)

- [ ] T013 [US1] Implement create_jql_syntax_highlighter() in ui/jql_syntax_highlighter.py returning html.Div with dual-layer structure
- [ ] T014 [US1] Add .jql-syntax-wrapper, .jql-syntax-input, .jql-syntax-highlight CSS to assets/jql_syntax.css with positioning and z-index
- [ ] T015 [US1] Verify tests T009-T010 pass (pytest tests/unit/ui/test_jql_syntax_highlighter.py::test_create*)

### Phase 3C: JavaScript Synchronization (3 tasks)

- [ ] T016 [P] [US1] Write test_scroll_synchronization() Playwright test in tests/integration/dashboard/test_jql_highlighting_workflow.py
- [ ] T017 [US1] Implement initializeSyntaxHighlighting() and syncScrollPosition() in assets/jql_syntax.js
- [ ] T018 [US1] Verify test T016 passes (pytest tests/integration/dashboard/test_jql_highlighting_workflow.py::test_scroll*)

### Phase 3D: Dash Callback Integration (4 tasks)

- [ ] T019 [P] [US1] Write test_update_highlighting_callback() unit test in tests/unit/ui/test_jql_syntax_highlighter.py
- [ ] T020 [US1] Implement update_jql_syntax_highlighting() callback in callbacks/settings.py
- [ ] T021 [US1] Update app layout to use create_jql_syntax_highlighter() for JQL textarea
- [ ] T022 [US1] Verify all US1 tests pass and acceptance scenarios validated (pytest tests/ -k "US1 or highlighting")

**Parallel Opportunities**: Test writing (T009-T012, T016, T019) can be done in parallel.

---

## Phase 4: User Story 2 (P2) - ScriptRunner Extension Support (6 tasks)

**Goal**: Extend syntax highlighting to recognize and highlight ScriptRunner JQL functions in purple.

**Dependencies**: Requires Phase 2 (Foundation) complete. Can start after US1 if desired, but not required.

**Independent Test Criteria**:
✅ User can type "issueFunction in linkedIssuesOf('TEST-1')" and see:
- "issueFunction" highlighted as keyword (blue)
- "in" highlighted as keyword (blue)
- "linkedIssuesOf" highlighted as function (purple)

**Acceptance Scenarios**: 3 scenarios from spec.md (see User Story 2)

### Tasks

- [ ] T023 [P] [US2] Write test_is_scriptrunner_function_returns_true_for_valid() in tests/unit/ui/test_jql_syntax_highlighter.py
- [ ] T024 [P] [US2] Write test_is_scriptrunner_function_returns_false_for_invalid() in tests/unit/ui/test_jql_syntax_highlighter.py
- [ ] T025 [P] [US2] Write test_scriptrunner_function_highlighted_purple() Playwright test in tests/integration/dashboard/test_jql_highlighting_workflow.py
- [ ] T026 [US2] Update parse_jql_syntax() context detection to mark ScriptRunner functions as "function" token type
- [ ] T027 [US2] Verify render_syntax_tokens() applies .jql-function class to function tokens
- [ ] T028 [US2] Verify all US2 tests pass and acceptance scenarios validated (pytest tests/ -k "US2 or scriptrunner")

**Parallel Opportunities**: Test writing (T023-T025) can be done in parallel.

---

## Phase 5: User Story 3 (P3) - Error Indication (6 tasks)

**Goal**: Add visual error indicators for unclosed strings and invalid operators.

**Dependencies**: Requires Phase 2 (Foundation) complete. Can start after US1 if desired, but not required.

**Independent Test Criteria**:
✅ User can type 'status = "Done' (unclosed quote) and see:
- Orange background with red wavy underline on '"Done'
- No application crash or visual glitches

**Acceptance Scenarios**: 3 scenarios from spec.md (see User Story 3)

### Tasks

- [ ] T029 [P] [US3] Write test_detect_unclosed_string_error() in tests/unit/ui/test_jql_syntax_highlighter.py
- [ ] T030 [P] [US3] Write test_detect_invalid_operator_error() in tests/unit/ui/test_jql_syntax_highlighter.py
- [ ] T031 [P] [US3] Write test_error_indication_displayed() Playwright test in tests/integration/dashboard/test_jql_highlighting_workflow.py
- [ ] T032 [US3] Implement detect_syntax_errors() in ui/jql_syntax_highlighter.py checking for unclosed quotes and invalid operators
- [ ] T033 [US3] Update update_jql_syntax_highlighting() callback to call detect_syntax_errors() and apply error styling to tokens
- [ ] T034 [US3] Verify all US3 tests pass and acceptance scenarios validated (pytest tests/ -k "US3 or error")

**Parallel Opportunities**: Test writing (T029-T031) can be done in parallel.

---

## Phase 6: Polish & Cross-Cutting Concerns (4 tasks)

**Goal**: Performance optimization, mobile testing, and documentation.

**Dependencies**: Requires US1 complete (other stories optional).

### Tasks

- [ ] T035 [P] Write test_mobile_viewport_highlighting() Playwright test for 320px viewport in tests/integration/dashboard/test_jql_highlighting_workflow.py
- [ ] T036 [P] Write test_parse_performance_under_50ms() performance test in tests/unit/ui/test_jql_syntax_highlighter.py
- [ ] T037 Run full test suite and verify 100% passing (pytest tests/ -v --cov=ui --cov=callbacks)
- [ ] T038 Update README.md or CHANGELOG.md with feature description and usage instructions

**Parallel Opportunities**: Test writing (T035-T036) can be done in parallel.

---

## Parallel Execution Examples

### Maximum Parallelization (16 tasks can run simultaneously)

**Foundation Phase** (2 parallel):
```
Developer A: T004 (SCRIPTRUNNER_FUNCTIONS) + T005 (is_scriptrunner_function)
Developer B: T008 (CSS classes)
```

**US1 Tests** (6 parallel):
```
Developer A: T009, T010 (unit tests)
Developer B: T011, T012 (integration tests)
Developer C: T016 (scroll test)
Developer D: T019 (callback test)
```

**US2 Tests** (3 parallel):
```
Developer A: T023, T024 (unit tests)
Developer B: T025 (integration test)
```

**US3 Tests** (3 parallel):
```
Developer A: T029, T030 (unit tests)
Developer B: T031 (integration test)
```

**Polish** (2 parallel):
```
Developer A: T035 (mobile test)
Developer B: T036 (performance test)
```

---

## Implementation Strategy

### MVP (Minimum Viable Product)

**Phases**: 1 + 2 + 3 = **Setup + Foundation + US1**  
**Tasks**: T001-T022 (22 tasks)  
**Delivers**: Core syntax highlighting with keywords, strings, operators visible in real-time

**Timeline Estimate**: 2-3 days with TDD workflow

### Full Feature (All User Stories)

**Phases**: 1 + 2 + 3 + 4 + 5 + 6  
**Tasks**: T001-T038 (38 tasks)  
**Delivers**: Complete syntax highlighting with ScriptRunner support and error indication

**Timeline Estimate**: 3-4 days with TDD workflow

### Incremental Delivery Strategy

1. **Sprint 1**: MVP (US1) - Deliver core highlighting
2. **Sprint 2**: US2 (ScriptRunner) - Deliver advanced query support
3. **Sprint 3**: US3 (Errors) + Polish - Deliver error prevention

---

## Testing Commands

### Run Tests by User Story

```powershell
# US1 tests only
.\.venv\Scripts\activate; pytest tests/ -k "US1 or highlighting" -v

# US2 tests only
.\.venv\Scripts\activate; pytest tests/ -k "US2 or scriptrunner" -v

# US3 tests only
.\.venv\Scripts\activate; pytest tests/ -k "US3 or error" -v

# All unit tests
.\.venv\Scripts\activate; pytest tests/unit/ui/test_jql_syntax_highlighter.py -v

# All integration tests
.\.venv\Scripts\activate; pytest tests/integration/dashboard/test_jql_highlighting_workflow.py -v

# Full test suite with coverage
.\.venv\Scripts\activate; pytest tests/ -v --cov=ui --cov=callbacks --cov-report=html
```

### Performance Validation

```powershell
# Verify <50ms parse time
.\.venv\Scripts\activate; pytest tests/unit/ui/test_jql_syntax_highlighter.py::test_parse_performance_under_50ms -v

# Measure actual parse time
.\.venv\Scripts\activate; python -c "
import time
from ui.components import parse_jql_syntax
query = 'project = TEST AND ' * 500  # ~5000 chars
start = time.time()
tokens = parse_jql_syntax(query)
duration = (time.time() - start) * 1000
print(f'Parse time: {duration:.2f}ms (target: <50ms)')
"
```

---

## Task Validation Checklist

Before marking a task complete, verify:

- [ ] **Tests Written First** (TDD Red): Failing test exists before implementation
- [ ] **Tests Pass** (TDD Green): Implementation passes all related tests
- [ ] **Code Quality** (TDD Refactor): Code follows Python style guide, has docstrings, type hints
- [ ] **No Regressions**: Existing tests still pass (pytest tests/ -v)
- [ ] **Performance**: No degradation in page load or interaction time
- [ ] **Mobile**: Works on 320px viewport (if UI change)
- [ ] **Accessibility**: Keyboard navigation and screen reader compatibility maintained
- [ ] **Documentation**: Docstrings and inline comments added

---

## Progress Tracking

### Completion Status

| Phase               | Tasks Complete | Total Tasks | Percentage |
| ------------------- | -------------- | ----------- | ---------- |
| Phase 1: Setup      | 0              | 3           | 0%         |
| Phase 2: Foundation | 0              | 5           | 0%         |
| Phase 3: US1 (P1)   | 0              | 14          | 0%         |
| Phase 4: US2 (P2)   | 0              | 6           | 0%         |
| Phase 5: US3 (P3)   | 0              | 6           | 0%         |
| Phase 6: Polish     | 0              | 4           | 0%         |
| **Overall**         | **0**          | **38**      | **0%**     |

### Milestones

- [ ] **Milestone 1**: MVP Complete (US1) - Tasks T001-T022
- [ ] **Milestone 2**: ScriptRunner Support (US2) - Tasks T023-T028
- [ ] **Milestone 3**: Error Indication (US3) - Tasks T029-T034
- [ ] **Milestone 4**: Production Ready - All tasks complete

---

## Notes

**TDD Workflow Reminder**:
1. Write failing test (RED)
2. Run test to verify it fails: `pytest <test_file>::<test_name> -v`
3. Implement minimum code (GREEN)
4. Run test to verify it passes: `pytest <test_file>::<test_name> -v`
5. Refactor for quality (REFACTOR)
6. Run all tests to verify no regressions: `pytest tests/ -v`

**File Paths**:
- Python modules: `ui/jql_syntax_highlighter.py`, `ui/components.py`, `callbacks/settings.py`
- CSS: `assets/jql_syntax.css`, `assets/custom.css`
- JavaScript: `assets/jql_syntax.js`
- Tests: `tests/unit/ui/test_jql_syntax_highlighter.py`, `tests/integration/dashboard/test_jql_highlighting_workflow.py`

**Performance Targets**:
- Parse time: <50ms for 5000 char queries (FR-005)
- Render time: <300ms for paste operations (SC-007)
- Frame rate: 60fps during typing (FR-011)

**Browser Support**: Latest versions only (last 6 months) of Chrome, Firefox, Safari, Edge per FR-015
