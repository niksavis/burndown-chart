# Tasks: Complete JQL Syntax Highlighting with Real-time Visual Feedback

**Input**: Design documents from `/specs/002-finish-jql-syntax/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing

**Tests**: Integration tests using Playwright for visual validation (no unit tests for library wrapper per constitution)

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies and prepare project for CodeMirror 6 integration

- [ ] T001 Install dash-codemirror package via pip in requirements.txt
- [ ] T002 Verify dash-codemirror import works in Python environment
- [ ] T003 [P] Add CSS token styling classes to assets/custom.css for JQL syntax highlighting

**Checkpoint**: Dependencies installed and ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core CSS and deprecation cleanup that MUST be complete before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Define JQL token CSS classes in assets/custom.css (.cm-jql-keyword, .cm-jql-string, .cm-jql-operator, .cm-jql-function, .cm-jql-scriptrunner, .cm-jql-field, .cm-jql-error with WCAG AA compliant colors)
- [ ] T005 Remove deprecated parse_jql_syntax() function from ui/components.py
- [ ] T006 Remove deprecated render_syntax_tokens() function from ui/components.py
- [ ] T007 [P] Delete deprecated assets/jql_syntax.css file
- [ ] T008 [P] Delete deprecated assets/jql_syntax.js file
- [ ] T009 [P] Remove tests for deprecated functions from tests/unit/ui/test_components.py (if they exist)

**Checkpoint**: Foundation ready - CSS defined, deprecated code removed, user story implementation can begin

---

## Phase 3: User Story 1 - Real-time Visual Syntax Highlighting Overlay (Priority: P1) 🎯 MVP

**Goal**: Display color-coded syntax highlighting for JQL keywords, strings, and operators in real-time as users type

**Independent Test**: Type "project = TEST AND status = 'Done'" in the JQL editor and verify keywords appear blue, strings appear green, operators appear gray, all updating in real-time (<50ms latency)

### Tests for User Story 1 (Playwright Integration Tests)

**NOTE: Tests verify visual highlighting behavior**

- [ ] T010 [P] [US1] Create test_jql_editor_workflow.py in tests/integration/dashboard/ with Playwright setup (server fixture, browser launch)
- [ ] T011 [P] [US1] Add Playwright test for keyword highlighting in tests/integration/dashboard/test_jql_editor_workflow.py::test_keyword_highlighting (type "AND", verify blue color)
- [ ] T012 [P] [US1] Add Playwright test for string highlighting in tests/integration/dashboard/test_jql_editor_workflow.py::test_string_highlighting (type '"Done"', verify green color)
- [ ] T013 [P] [US1] Add Playwright test for operator highlighting in tests/integration/dashboard/test_jql_editor_workflow.py::test_operator_highlighting (type '=', verify gray color)
- [ ] T014 [P] [US1] Add Playwright test for cursor stability in tests/integration/dashboard/test_jql_editor_workflow.py::test_cursor_position_stable (type quickly, verify no jumps)
- [ ] T015 [P] [US1] Add Playwright test for paste performance in tests/integration/dashboard/test_jql_editor_workflow.py::test_paste_large_query (paste 500 chars, verify <300ms highlighting)

### Implementation for User Story 1

- [ ] T016 [US1] Create ui/jql_editor.py with create_jql_editor() function that returns DashCodeMirror component configured with mode="jql", lineWrapping=True, lineNumbers=False, aria-label
- [ ] T017 [US1] Create assets/jql_language_mode.js with StreamLanguage.define() for JQL tokenizer (keywords: AND/OR/NOT/IN/IS/WAS, operators: =/!=/~/!~/</>/<=/>= regex patterns, strings: quoted text regex)
- [ ] T018 [US1] Implement keyword tokenization in assets/jql_language_mode.js token() function with case-insensitive matching for AND, OR, NOT, IN, IS, WAS, EMPTY, NULL, ORDER, BY, ASC, DESC (return "jql-keyword")
- [ ] T019 [US1] Implement operator tokenization in assets/jql_language_mode.js token() function for =, !=, ~, !~, <, >, <=, >= (return "jql-operator")
- [ ] T020 [US1] Implement string literal tokenization in assets/jql_language_mode.js token() function for double-quoted and single-quoted text (return "jql-string")
- [ ] T021 [US1] Implement field name tokenization in assets/jql_language_mode.js token() function for identifiers before operators (return "jql-field")
- [ ] T022 [US1] Update app.py layout to replace dbc.Textarea with create_jql_editor() for "jira-jql-query" component
- [ ] T023 [US1] Verify existing callbacks in callbacks/settings.py work unchanged with new editor component (same id="jira-jql-query", same value property)

**Checkpoint**: At this point, User Story 1 should be fully functional - basic JQL syntax highlighting works for keywords, strings, operators

---

## Phase 4: User Story 2 - ScriptRunner Extension Syntax Support (Priority: P2)

**Goal**: Extend syntax highlighting to recognize ScriptRunner-specific functions (linkedIssuesOf, issueFunction, etc.) with distinct purple coloring

**Independent Test**: Type "issueFunction in linkedIssuesOf('TEST-1')" and verify "issueFunction", "in", and "linkedIssuesOf" are highlighted in purple as functions

### Tests for User Story 2 (Playwright Integration Tests)

- [ ] T024 [P] [US2] Add Playwright test for ScriptRunner function highlighting in tests/integration/dashboard/test_jql_editor_workflow.py::test_scriptrunner_function_highlighting (type "linkedIssuesOf(", verify purple color)
- [ ] T025 [P] [US2] Add Playwright test for issueFunction keyword in tests/integration/dashboard/test_jql_editor_workflow.py::test_issuefunction_keyword (type "issueFunction in", verify highlighted)
- [ ] T026 [P] [US2] Add Playwright test for multiple ScriptRunner functions in tests/integration/dashboard/test_jql_editor_workflow.py::test_multiple_scriptrunner_functions (type query with 3+ functions, verify all highlighted)

### Implementation for User Story 2

- [ ] T027 [US2] Add ScriptRunner function patterns to assets/jql_language_mode.js token() function for top 15 functions: linkedIssuesOf, issuesInEpics, subtasksOf, parentsOf, epicsOf, hasLinks, hasComments, hasAttachments, lastUpdated, expression, dateCompare, aggregateExpression, issueFieldMatch, linkedIssuesOfRecursive, workLogged (return "jql-scriptrunner")
- [ ] T028 [US2] Add standard JQL function patterns to assets/jql_language_mode.js token() function for currentUser(), now(), startOfDay(), endOfDay(), startOfWeek(), endOfWeek() (return "jql-function")
- [ ] T029 [US2] Implement priority ordering in assets/jql_language_mode.js token() function: ScriptRunner functions BEFORE generic keywords to prevent false keyword matches

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - basic JQL + ScriptRunner syntax highlighting

---

## Phase 5: User Story 3 - Error Prevention with Invalid Syntax Indication (Priority: P3)

**Goal**: Visual indicators for syntax errors (unclosed quotes, invalid operators) to help users fix issues before query submission

**Independent Test**: Type 'status = "Done' (unclosed quote) and verify red wavy underline appears on the problematic text

### Tests for User Story 3 (Playwright Integration Tests)

- [ ] T030 [P] [US3] Add Playwright test for unclosed string error in tests/integration/dashboard/test_jql_editor_workflow.py::test_unclosed_string_error (type 'status = "Done', verify red underline/error indicator)
- [ ] T031 [P] [US3] Add Playwright test for invalid operator error in tests/integration/dashboard/test_jql_editor_workflow.py::test_invalid_operator_error (type "===", verify error highlighting if library supports)
- [ ] T032 [P] [US3] Add Playwright test for error disappears when fixed in tests/integration/dashboard/test_jql_editor_workflow.py::test_error_indicator_clears (type unclosed quote, then close quote, verify error clears)

### Implementation for User Story 3

- [ ] T033 [US3] Implement unclosed string detection in assets/jql_language_mode.js token() function with state tracking (inString flag, check stream.eol(), return "jql-error")
- [ ] T034 [US3] Add error state management to assets/jql_language_mode.js startState() function (inString: false, stringDelimiter: null)
- [ ] T035 [US3] Implement unclosed quote error pattern in assets/jql_language_mode.js token() function to detect strings ending at EOL without closing quote (return "jql-error")

**Checkpoint**: All user stories should now be independently functional - full JQL syntax highlighting with error detection

---

## Phase 6: Mobile & Performance Validation

**Purpose**: Verify mobile responsiveness and performance targets across all user stories

- [ ] T036 [P] Add Playwright test for mobile viewport in tests/integration/dashboard/test_jql_editor_workflow.py::test_mobile_viewport_320px (set viewport 320x568, type query, verify highlighting works)
- [ ] T037 [P] Add Playwright test for keystroke latency in tests/integration/dashboard/test_jql_editor_workflow.py::test_keystroke_latency_under_50ms (measure with Performance API, assert <50ms)
- [ ] T038 [P] Add Playwright test for 60fps typing in tests/integration/dashboard/test_jql_editor_workflow.py::test_typing_60fps (type at 100 WPM, verify no dropped frames using Performance API)
- [ ] T039 Add Playwright test for large query performance in tests/integration/dashboard/test_jql_editor_workflow.py::test_large_query_5000_chars (paste 5000 char query, verify <300ms highlighting)

**Checkpoint**: Performance and mobile requirements validated across all user stories

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and documentation

- [ ] T040 [P] Update readme.md with CodeMirror 6 usage instructions and JQL syntax highlighting examples
- [ ] T041 [P] Add inline documentation to ui/jql_editor.py create_jql_editor() function with parameter descriptions and usage examples
- [ ] T042 [P] Add inline documentation to assets/jql_language_mode.js with token type descriptions and pattern explanations
- [ ] T043 Verify all deprecated functions removed by searching codebase for parse_jql_syntax and render_syntax_tokens references (should find zero matches)
- [ ] T044 Run full test suite to verify no regressions in existing functionality (pytest tests/ -v)
- [ ] T045 Validate quickstart.md instructions by following step-by-step and confirming all examples work

**Checkpoint**: Feature complete, documented, and validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T004-T009) - Core highlighting
- **User Story 2 (Phase 4)**: Depends on User Story 1 (T016-T023) - Extends base highlighting with ScriptRunner
- **User Story 3 (Phase 5)**: Depends on User Story 1 (T016-T023) - Adds error detection to base highlighting
- **Mobile & Performance (Phase 6)**: Depends on all user stories (T010-T035) - Validates complete feature
- **Polish (Phase 7)**: Depends on all previous phases - Final cleanup

### User Story Dependencies

- **User Story 1 (P1)**: Foundation ONLY (T004-T009) - No dependencies on other stories
  - **Delivers independently**: Basic JQL syntax highlighting (keywords, strings, operators)
  - **MVP scope**: This story alone is sufficient for initial release

- **User Story 2 (P2)**: User Story 1 (T016-T023) - Extends tokenizer with ScriptRunner patterns
  - **Delivers independently**: Full ScriptRunner support on top of US1
  - **Can be skipped**: If ScriptRunner not needed, US1 still delivers value

- **User Story 3 (P3)**: User Story 1 (T016-T023) - Adds error state to tokenizer
  - **Delivers independently**: Error detection on top of US1
  - **Can be skipped**: If error detection not priority, US1+US2 still deliver value

### Within Each User Story

**User Story 1**:
1. Tests can run in parallel (T010-T015) - ALL SHOULD FAIL initially
2. Core implementation (T016-T017) - Create wrapper and language mode
3. Tokenizer patterns (T018-T021) - Can run in parallel once T017 exists
4. Integration (T022-T023) - Replace component in app layout
5. Tests should NOW PASS

**User Story 2**:
1. Tests can run in parallel (T024-T026) - ALL SHOULD FAIL initially
2. Implementation (T027-T029) - Extend language mode with ScriptRunner
3. Tests should NOW PASS

**User Story 3**:
1. Tests can run in parallel (T030-T032) - ALL SHOULD FAIL initially
2. Implementation (T033-T035) - Add error detection to language mode
3. Tests should NOW PASS

### Parallel Opportunities

**Setup (Phase 1)**:
- T001-T003: All can run in parallel (different concerns)

**Foundational (Phase 2)**:
- T004: CSS definitions (blocks nothing)
- T005-T006: Python function removal (can run in parallel)
- T007-T009: Asset cleanup (can run in parallel with T005-T006)

**User Story 1 (Phase 3)**:
- T010-T015: All tests can be written in parallel
- T018-T021: All tokenizer patterns can be implemented in parallel (once T017 exists)

**User Story 2 (Phase 4)**:
- T024-T026: All tests can be written in parallel
- T027-T028: Function patterns can be implemented in parallel

**User Story 3 (Phase 5)**:
- T030-T032: All tests can be written in parallel
- T033-T035: Error detection can be implemented in parallel

**Mobile & Performance (Phase 6)**:
- T036-T039: All tests can run in parallel

**Polish (Phase 7)**:
- T040-T042: All documentation can be written in parallel

---

## Parallel Execution Examples

### Phase 3 (User Story 1) - Maximum Parallelization

**Parallel Group 1 - Tests** (can all run simultaneously):
```
T010: Create test file with Playwright setup
T011: Add keyword highlighting test
T012: Add string highlighting test  
T013: Add operator highlighting test
T014: Add cursor stability test
T015: Add paste performance test
```

**Sequential**: T016, T017 (must create files first)

**Parallel Group 2 - Tokenizer Patterns** (can all run simultaneously after T017):
```
T018: Keyword tokenization
T019: Operator tokenization
T020: String tokenization
T021: Field tokenization
```

**Sequential**: T022, T023 (integrate into app)

### Phase 4 (User Story 2) - ScriptRunner Extension

**Parallel Group 1 - Tests**:
```
T024: ScriptRunner function test
T025: issueFunction keyword test
T026: Multiple functions test
```

**Parallel Group 2 - Implementation**:
```
T027: Add ScriptRunner patterns
T028: Add standard JQL functions
T029: Priority ordering fix
```

### Recommended MVP Scope

**Minimum Viable Product**: User Story 1 ONLY (T001-T023)

**Delivers**:
- ✅ Real-time syntax highlighting for JQL keywords (blue)
- ✅ String literals highlighted (green)
- ✅ Operators highlighted (gray)
- ✅ <50ms latency, 60fps typing
- ✅ Mobile-first (320px+ viewports)
- ✅ Replaces underperforming custom functions

**Skipped in MVP**:
- ❌ ScriptRunner function support (User Story 2)
- ❌ Error detection for unclosed quotes (User Story 3)

**Incremental Delivery Path**:
1. **MVP Release**: User Story 1 → Get feedback
2. **Enhancement 1**: Add User Story 2 → ScriptRunner users benefit
3. **Enhancement 2**: Add User Story 3 → Error prevention benefit

---

## Task Summary

**Total Tasks**: 45

**Breakdown by Phase**:
- Setup: 3 tasks
- Foundational: 6 tasks
- User Story 1 (P1 - MVP): 14 tasks (6 tests + 8 implementation)
- User Story 2 (P2): 6 tasks (3 tests + 3 implementation)
- User Story 3 (P3): 6 tasks (3 tests + 3 implementation)
- Mobile & Performance: 4 tasks (validation)
- Polish: 6 tasks (documentation)

**Parallel Opportunities**: 32 tasks can run in parallel (marked with [P])

**Independent Test Criteria**:
- US1: Type "project = TEST AND status = 'Done'" → See blue/green/gray highlighting
- US2: Type "issueFunction in linkedIssuesOf('TEST-1')" → See purple function highlighting  
- US3: Type 'status = "Done' → See red error indicator on unclosed quote

**Suggested MVP**: Tasks T001-T023 (Setup + Foundational + User Story 1)

---

## Implementation Strategy

### Incremental Delivery (Recommended)

**Week 1**: MVP (User Story 1)
- Complete Setup (T001-T003)
- Complete Foundational (T004-T009)
- Complete User Story 1 (T010-T023)
- **Release**: Basic JQL syntax highlighting

**Week 2**: ScriptRunner Support (User Story 2)
- Complete User Story 2 (T024-T029)
- **Release**: Enhanced with ScriptRunner functions

**Week 3**: Error Detection (User Story 3)
- Complete User Story 3 (T030-T035)
- Complete Mobile & Performance (T036-T039)
- **Release**: Full feature with error prevention

**Week 4**: Polish
- Complete Polish (T040-T045)
- **Release**: Production-ready with documentation

### Big Bang Delivery (Alternative)

Complete all tasks T001-T045 before release
- **Pros**: Single comprehensive release
- **Cons**: Longer time to user feedback, higher integration risk

**Recommendation**: Use incremental delivery - get MVP feedback early, adjust priorities based on user needs
