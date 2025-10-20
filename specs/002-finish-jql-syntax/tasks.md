# Tasks: Complete JQL Syntax Highlig- [X]- [X] T006 Remove deprecated render_syntax_tokens() function from ui/components.py
- [X] T007 [P] Delete deprecated assets/jql_syntax.css file
- [X] T008 [P] Delete deprecated assets/jql_syntax.js file
- [X] T009 [P] Remove tests for deprecated functions from tests/unit/ui/test_components.py (if they exist)4 Define JQL token CSS classes in assets/custom.css (.cm-jql-keyword, .cm-jql-string, .cm-jql-operator, .cm-jql-function, .cm-jql-scriptrunner, .cm-jql-field, .cm-jql-error with WCAG AA compliant colors)
- [X] T005 Remove deprecated parse_jql_syntax() function from ui/components.py
- [X] T006 Remove deprecated render_syntax_tokens() function from ui/components.py
- [ ] T007 [P] Delete deprecated assets/jql_syntax.css fileg with Real-time Visual Feedback

**Input**: Design documents from `/specs/002-finish-jql-syntax/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing

**Tests**: Integration tests using Playwright for visual validation (no unit tests for library wrapper per constitution)

**CRITICAL UPDATE (2025-10-20)**: Tasks updated to reflect reality - `dash-codemirror` package does NOT exist on PyPI. Using CodeMirror 6 via CDN with JavaScript initialization instead.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare project for CodeMirror 6 integration via CDN (NO Python package installation needed)

- [X] T001 Add CodeMirror 6 library to app.py external_scripts from CDN (https://cdn.jsdelivr.net/npm/codemirror@6/dist/index.min.js)
- [X] T002 Verify CodeMirror loads in browser by opening app and checking browser console for EditorView object
- [X] T003 [P] Install Playwright for integration testing (.\.venv\Scripts\activate; pip install pytest-playwright; playwright install chromium)

**Checkpoint**: CodeMirror CDN loading verified, Playwright installed, ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core CSS and deprecation cleanup that MUST be complete before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define JQL token CSS classes in assets/custom.css (.cm-jql-keyword, .cm-jql-string, .cm-jql-operator, .cm-jql-function, .cm-jql-scriptrunner, .cm-jql-field, .cm-jql-error with WCAG AA compliant colors)
- [X] T005 Remove deprecated parse_jql_syntax() function from ui/components.py
- [X] T006 Remove deprecated render_syntax_tokens() function from ui/components.py
- [X] T007 [P] Delete deprecated assets/jql_syntax.css file
- [X] T008 [P] Delete deprecated assets/jql_syntax.js file
- [X] T009 [P] Remove tests for deprecated functions from tests/unit/ui/test_components.py (if they exist)

**Checkpoint**: Foundation ready - CSS defined, deprecated code removed, user story implementation can begin

---

## Phase 3: User Story 1 - Real-time Visual Syntax Highlighting Overlay (Priority: P1) 🎯 MVP

**Goal**: Display color-coded syntax highlighting for JQL keywords, strings, and operators in real-time as users type

**Independent Test**: Type "project = TEST AND status = 'Done'" in the JQL editor and verify keywords appear blue, strings appear green, operators appear gray, all updating in real-time (<50ms latency)

### Tests for User Story 1 (Playwright Integration Tests)

**NOTE: Tests verify visual highlighting behavior**

- [X] T010 [P] [US1] Create test_jql_editor_workflow.py in tests/integration/dashboard/ with Playwright setup (server fixture, browser launch)
- [X] T011 [P] [US1] Add Playwright test for keyword highlighting in tests/integration/dashboard/test_jql_editor_workflow.py::test_keyword_highlighting (type "AND", verify blue color)
- [X] T012 [P] [US1] Add Playwright test for string highlighting in tests/integration/dashboard/test_jql_editor_workflow.py::test_string_highlighting (type '"Done"', verify green color)
- [X] T013 [P] [US1] Add Playwright test for operator highlighting in tests/integration/dashboard/test_jql_editor_workflow.py::test_operator_highlighting (type '=', verify gray color)
- [X] T014 [P] [US1] Add Playwright test for cursor stability in tests/integration/dashboard/test_jql_editor_workflow.py::test_cursor_position_stable (type quickly, verify no jumps)
- [X] T015 [P] [US1] Add Playwright test for paste performance in tests/integration/dashboard/test_jql_editor_workflow.py::test_paste_large_query (paste 500 chars, verify <300ms highlighting)

### Implementation for User Story 1

- [X] T016 [US1] Create ui/jql_editor.py with create_jql_editor() function that returns html.Div() containing: html.Div(className="jql-editor-container") for CodeMirror, dcc.Store(id=editor_id) for state sync, html.Textarea(id=f"{editor_id}-hidden") for accessibility fallback
- [X] T017 [US1] Create assets/jql_language_mode.js with StreamLanguage.define() for JQL tokenizer (keywords: AND/OR/NOT/IN/IS/WAS, operators: =/!=/~/!~/</>/<=/>= regex patterns, strings: quoted text regex), export as window.jqlLanguageMode
- [X] T018 [US1] Create assets/jql_editor_init.js that finds .jql-editor-container elements, initializes CodeMirror EditorView with jqlLanguageMode, syncs editor changes to dcc.Store using updateListener
- [X] T019 [US1] Implement keyword tokenization in assets/jql_language_mode.js token() function with case-insensitive matching for AND, OR, NOT, IN, IS, WAS, EMPTY, NULL, ORDER, BY, ASC, DESC (return "jql-keyword")
- [X] T020 [US1] Implement operator tokenization in assets/jql_language_mode.js token() function for =, !=, ~, !~, <, >, <=, >= (return "jql-operator")
- [X] T021 [US1] Implement string literal tokenization in assets/jql_language_mode.js token() function for double-quoted and single-quoted text (return "jql-string")
- [X] T022 [US1] Implement field name tokenization in assets/jql_language_mode.js token() function for identifiers before operators (return "jql-field")
- [X] T023 [US1] Update app.py layout to replace dbc.Textarea with create_jql_editor() for "jira-jql-query" component
- [X] T024 [US1] Verify existing callbacks in callbacks/settings.py work with new editor by checking they read from dcc.Store(id="jira-jql-query") data property (may need to update from "value" to "data")

**Checkpoint**: At this point, User Story 1 should be fully functional - basic JQL syntax highlighting works for keywords, strings, operators

---

## Phase 4: User Story 2 - ScriptRunner Extension Syntax Support (Priority: P2)

**Goal**: Extend syntax highlighting to recognize ScriptRunner-specific functions (linkedIssuesOf, issueFunction, etc.) with distinct purple coloring

**Independent Test**: Type "issueFunction in linkedIssuesOf('TEST-1')" and verify "issueFunction", "in", and "linkedIssuesOf" are highlighted in purple as functions

### Tests for User Story 2 (Playwright Integration Tests)

- [X] T025 [P] [US2] Add Playwright test for ScriptRunner function highlighting in tests/integration/dashboard/test_jql_editor_workflow.py::test_scriptrunner_function_highlighting (type "linkedIssuesOf(", verify purple color)
- [X] T026 [P] [US2] Add Playwright test for issueFunction keyword in tests/integration/dashboard/test_jql_editor_workflow.py::test_issuefunction_keyword (type "issueFunction in", verify highlighted)
- [X] T027 [P] [US2] Add Playwright test for multiple ScriptRunner functions in tests/integration/dashboard/test_jql_editor_workflow.py::test_multiple_scriptrunner_functions (type query with 3+ functions, verify all highlighted)

### Implementation for User Story 2

- [X] T028 [US2] Add ScriptRunner function patterns to assets/jql_language_mode.js token() function for top 15 functions: linkedIssuesOf, issuesInEpics, subtasksOf, parentsOf, epicsOf, hasLinks, hasComments, hasAttachments, lastUpdated, expression, dateCompare, aggregateExpression, issueFieldMatch, linkedIssuesOfRecursive, workLogged (return "jql-scriptrunner")
- [X] T029 [US2] Add standard JQL function patterns to assets/jql_language_mode.js token() function for currentUser(), now(), startOfDay(), endOfDay(), startOfWeek(), endOfWeek() (return "jql-function")
- [X] T030 [US2] Implement priority ordering in assets/jql_language_mode.js token() function: ScriptRunner functions BEFORE generic keywords to prevent false keyword matches

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - basic JQL + ScriptRunner syntax highlighting

---

## Phase 5: User Story 3 - Error Prevention with Invalid Syntax Indication (Priority: P3)

**Goal**: Visual indicators for syntax errors (unclosed quotes, invalid operators) to help users fix issues before query submission

**Independent Test**: Type 'status = "Done' (unclosed quote) and verify red wavy underline appears on the problematic text

### Tests for User Story 3 (Playwright Integration Tests)

- [ ] T031 [P] [US3] Add Playwright test for unclosed string error in tests/integration/dashboard/test_jql_editor_workflow.py::test_unclosed_string_error (type 'status = "Done', verify red underline/error indicator)
- [ ] T032 [P] [US3] Add Playwright test for invalid operator error in tests/integration/dashboard/test_jql_editor_workflow.py::test_invalid_operator_error (type "===", verify error highlighting if library supports)
- [ ] T033 [P] [US3] Add Playwright test for error disappears when fixed in tests/integration/dashboard/test_jql_editor_workflow.py::test_error_indicator_clears (type unclosed quote, then close quote, verify error clears)

### Implementation for User Story 3

- [ ] T034 [US3] Implement unclosed string detection in assets/jql_language_mode.js token() function with state tracking (inString flag, check stream.eol(), return "jql-error")
- [ ] T035 [US3] Add error state management to assets/jql_language_mode.js startState() function (inString: false, stringDelimiter: null)
- [ ] T036 [US3] Implement unclosed quote error pattern in assets/jql_language_mode.js token() function to detect strings ending at EOL without closing quote (return "jql-error")

**Checkpoint**: All user stories should now be independently functional - full JQL syntax highlighting with error detection

---

## Phase 6: Mobile & Performance Validation

**Purpose**: Verify mobile responsiveness and performance targets across all user stories

- [ ] T037 [P] Add Playwright test for mobile viewport in tests/integration/dashboard/test_jql_editor_workflow.py::test_mobile_viewport_320px (set viewport 320x568, type query, verify highlighting works)
- [ ] T038 [P] Add Playwright test for keystroke latency in tests/integration/dashboard/test_jql_editor_workflow.py::test_keystroke_latency_under_50ms (measure with Performance API, assert <50ms)
- [ ] T039 [P] Add Playwright test for 60fps typing in tests/integration/dashboard/test_jql_editor_workflow.py::test_typing_60fps (type at 100 WPM, verify no dropped frames using Performance API)
- [ ] T040 Add Playwright test for large query performance in tests/integration/dashboard/test_jql_editor_workflow.py::test_large_query_5000_chars (paste 5000 char query, verify <300ms highlighting)

**Checkpoint**: Performance and mobile requirements validated across all user stories

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and documentation

- [ ] T041 [P] Update readme.md with CodeMirror 6 CDN usage instructions and JQL syntax highlighting examples
- [ ] T042 [P] Add inline documentation to ui/jql_editor.py create_jql_editor() function with parameter descriptions and usage examples
- [ ] T043 [P] Add inline documentation to assets/jql_language_mode.js with token type descriptions and pattern explanations
- [ ] T044 [P] Add inline documentation to assets/jql_editor_init.js with CodeMirror initialization steps and Store sync logic
- [ ] T045 Verify all deprecated functions removed by searching codebase for parse_jql_syntax and render_syntax_tokens references (should find zero matches)
- [ ] T046 Run full test suite to verify no regressions in existing functionality (pytest tests/ -v)
- [ ] T047 Validate quickstart.md instructions by following step-by-step and confirming all examples work

**Checkpoint**: Feature complete, documented, and validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T004-T009) - Core highlighting
- **User Story 2 (Phase 4)**: Depends on User Story 1 (T016-T024) - Extends base highlighting with ScriptRunner
- **User Story 3 (Phase 5)**: Depends on User Story 1 (T016-T024) - Adds error detection to base highlighting
- **Mobile & Performance (Phase 6)**: Depends on all user stories (T010-T036) - Validates complete feature
- **Polish (Phase 7)**: Depends on all previous phases - Final cleanup

### User Story Dependencies

- **User Story 1 (P1)**: Foundation ONLY (T004-T009) - No dependencies on other stories
  - **Delivers independently**: Basic JQL syntax highlighting (keywords, strings, operators)
  - **MVP scope**: This story alone is sufficient for initial release

- **User Story 2 (P2)**: User Story 1 (T016-T024) - Extends tokenizer with ScriptRunner patterns
  - **Delivers independently**: Full ScriptRunner support on top of US1
  - **Can be skipped**: If ScriptRunner not needed, US1 still delivers value

- **User Story 3 (P3)**: User Story 1 (T016-T024) - Adds error state to tokenizer
  - **Delivers independently**: Error detection on top of US1
  - **Can be skipped**: If error detection not priority, US1+US2 still deliver value

### Within Each User Story

**User Story 1**:
1. Tests can run in parallel (T010-T015) - ALL SHOULD FAIL initially
2. Core implementation (T016-T018) - Create container, language mode, initialization
3. Tokenizer patterns (T019-T022) - Can run in parallel once T017 exists
4. Integration (T023-T024) - Replace component in app layout, verify callbacks
5. Tests should NOW PASS

**User Story 2**:
1. Tests can run in parallel (T025-T027) - ALL SHOULD FAIL initially
2. Implementation (T028-T030) - Extend language mode with ScriptRunner
3. Tests should NOW PASS

**User Story 3**:
1. Tests can run in parallel (T031-T033) - ALL SHOULD FAIL initially
2. Implementation (T034-T036) - Add error detection to language mode
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
- T019-T022: All tokenizer patterns can be implemented in parallel (once T017 exists)

**User Story 2 (Phase 4)**:
- T025-T027: All tests can be written in parallel
- T028-T029: Function patterns can be implemented in parallel

**User Story 3 (Phase 5)**:
- T031-T033: All tests can be written in parallel
- T034-T036: Error detection can be implemented in parallel

**Mobile & Performance (Phase 6)**:
- T037-T040: All tests can run in parallel

**Polish (Phase 7)**:
- T041-T044: All documentation can be written in parallel

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

**Sequential**: T016, T017, T018 (must create files first)

**Parallel Group 2 - Tokenizer Patterns** (can all run simultaneously after T017):
```
T019: Keyword tokenization
T020: Operator tokenization
T021: String tokenization
T022: Field tokenization
```

**Sequential**: T023, T024 (integrate into app, verify callbacks)

### Phase 4 (User Story 2) - ScriptRunner Extension

**Parallel Group 1 - Tests**:
```
T025: ScriptRunner function test
T026: issueFunction keyword test
T027: Multiple functions test
```

**Parallel Group 2 - Implementation**:
```
T028: Add ScriptRunner patterns
T029: Add standard JQL functions
T030: Priority ordering fix
```

### Recommended MVP Scope

**Minimum Viable Product**: User Story 1 ONLY (T001-T024)

**Delivers**:
- ✅ Real-time syntax highlighting for JQL keywords (blue)
- ✅ String literals highlighted (green)
- ✅ Operators highlighted (gray)
- ✅ <50ms latency, 60fps typing
- ✅ Mobile-first (320px+ viewports)
- ✅ Replaces underperforming custom functions
- ✅ **No Python package dependencies** (CodeMirror via CDN)

**Skipped in MVP**:
- ❌ ScriptRunner function support (User Story 2)
- ❌ Error detection for unclosed quotes (User Story 3)

**Incremental Delivery Path**:
1. **MVP Release**: User Story 1 → Get feedback
2. **Enhancement 1**: Add User Story 2 → ScriptRunner users benefit
3. **Enhancement 2**: Add User Story 3 → Error prevention benefit

---

## Task Summary

**Total Tasks**: 47 (increased from 45 due to CDN integration complexity)

**Breakdown by Phase**:
- Setup: 3 tasks (CDN loading + Playwright)
- Foundational: 6 tasks (CSS + deprecation)
- User Story 1 (P1 - MVP): 15 tasks (6 tests + 9 implementation - added jql_editor_init.js)
- User Story 2 (P2): 6 tasks (3 tests + 3 implementation)
- User Story 3 (P3): 6 tasks (3 tests + 3 implementation)
- Mobile & Performance: 4 tasks (validation)
- Polish: 7 tasks (documentation - added jql_editor_init.js docs)

**Parallel Opportunities**: 33 tasks can run in parallel (marked with [P])

**Independent Test Criteria**:
- US1: Type "project = TEST AND status = 'Done'" → See blue/green/gray highlighting
- US2: Type "issueFunction in linkedIssuesOf('TEST-1')" → See purple function highlighting  
- US3: Type 'status = "Done' → See red error indicator on unclosed quote

**Suggested MVP**: Tasks T001-T024 (Setup + Foundational + User Story 1)

**Key Changes from Original Plan**:
- ✅ NO Python package installation (CodeMirror via CDN)
- ✅ Added jql_editor_init.js for JavaScript initialization
- ✅ Changed create_jql_editor() to return html.Div() + dcc.Store()
- ✅ Callbacks may need update from "value" to "data" property

---

## Implementation Strategy

### Incremental Delivery (Recommended)

**Week 1**: MVP (User Story 1)
- Complete Setup (T001-T003) - CDN loading + Playwright
- Complete Foundational (T004-T009) - CSS + deprecation
- Complete User Story 1 (T010-T024) - Basic syntax highlighting
- **Release**: Basic JQL syntax highlighting with CodeMirror 6 via CDN

**Week 2**: ScriptRunner Support (User Story 2)
- Complete User Story 2 (T025-T030)
- **Release**: Enhanced with ScriptRunner functions

**Week 3**: Error Detection (User Story 3)
- Complete User Story 3 (T031-T036)
- Complete Mobile & Performance (T037-T040)
- **Release**: Full feature with error prevention

**Week 4**: Polish
- Complete Polish (T041-T047)
- **Release**: Production-ready with documentation

### Big Bang Delivery (Alternative)

Complete all tasks T001-T047 before release
- **Pros**: Single comprehensive release
- **Cons**: Longer time to user feedback, higher integration risk

**Recommendation**: Use incremental delivery - get MVP feedback early, adjust priorities based on user needs
