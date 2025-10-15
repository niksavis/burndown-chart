# Tasks: JQL Query Enhancements

**Feature**: 001-add-jql-query  
**Date**: 2025-10-15  
**Status**: Ready for Implementation

## Task Execution Guidelines

### Execution Order
- **Sequential**: Tasks marked with story labels (e.g., `[US1]`) must be completed in order within that story
- **Parallel**: Tasks marked with `[P]` can be executed simultaneously with other `[P]` tasks in the same phase
- **Dependencies**: Some tasks depend on prior tasks being complete (noted in descriptions)

### Task Format
- `- [ ] [TaskID] [P?] [Story?] Task description`
  - `[TaskID]`: Unique identifier (e.g., TASK-001)
  - `[P]`: Parallelizable task (optional)
  - `[Story?]`: User story reference - US1, US2, US3 (optional)

### Story Independence
Each user story can be implemented and tested independently:
- **US1 (P1)**: Character count display - Can be implemented and shipped alone
- **US2 (P2)**: Syntax highlighting - Requires US1 foundation but can be tested independently
- **US3 (P3)**: Mobile responsiveness - Validates US1+US2 work on mobile devices

---

## Phase 0: Setup & Prerequisites

### Environment Preparation
- [ ] [TASK-001] [P] Ensure virtual environment is activated: `.\.venv\Scripts\activate; python --version`
- [ ] [TASK-002] [P] Verify all dependencies installed: `.\.venv\Scripts\activate; pip list | Select-String "dash"`
- [ ] [TASK-003] [P] Run existing tests to establish baseline: `.\.venv\Scripts\activate; pytest tests/ -v`
- [ ] [TASK-004] [P] Create feature branch: `git checkout -b 001-add-jql-query`

### Test File Structure Setup
- [ ] [TASK-005] [P] Create unit test directory structure if needed: `New-Item -ItemType Directory -Force -Path "tests\unit\ui"`
- [ ] [TASK-006] [P] Create integration test directory structure if needed: `New-Item -ItemType Directory -Force -Path "tests\integration"`

---

## Phase 1: User Story 1 - Real-time Character Count (Priority P1)

### TDD: Red Phase (Create Failing Tests)
- [ ] [TASK-101] [US1] Create `tests/unit/ui/test_character_count.py` with test for character counting function
  - Test: `test_calculate_character_count_basic()` - verify len() returns correct count for simple query
  - Test: `test_calculate_character_count_unicode()` - verify unicode character handling
  - Test: `test_calculate_character_count_empty()` - verify empty string returns 0
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_character_count.py -v` (should FAIL)

- [ ] [TASK-102] [US1] Add test for warning threshold detection
  - Test: `test_should_show_warning_below_threshold()` - verify no warning at 1799 chars
  - Test: `test_should_show_warning_at_threshold()` - verify warning at 1800 chars
  - Test: `test_should_show_warning_above_threshold()` - verify warning at 2000+ chars
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_character_count.py::test_should_show_warning_below_threshold -v` (should FAIL)

- [ ] [TASK-103] [US1] Add test for character count display component
  - Test: `test_character_count_display_format()` - verify "X / 2000 characters" format
  - Test: `test_character_count_display_warning_style()` - verify CSS classes applied when warning active
  - Test: `test_character_count_display_aria_label()` - verify accessibility attributes
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_character_count.py -k "display" -v` (should FAIL)

### TDD: Green Phase (Implement Minimum Code)
- [ ] [TASK-104] [US1] Create character counting utility function in `ui/cards.py`
  - Function: `calculate_character_count(query: str) -> int` - return len(query)
  - Function: `should_show_warning(count: int, threshold: int = 1800) -> bool` - return count >= threshold
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_character_count.py -v` (should PASS for utility tests)

- [ ] [TASK-105] [US1] Create character count display component in `ui/cards.py`
  - Function: `character_count_display(count: int, max_chars: int = 2000, show_warning: bool = False) -> dbc.InputGroup`
  - Component structure: `dbc.InputGroupText` with icon + text, conditional warning CSS class
  - Include: `aria-live="polite"` for screen reader announcements
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_character_count.py -v` (all tests should PASS)

### CSS Styling
- [ ] [TASK-106] [P] [US1] Add character count warning styles to `assets/custom.css`
  - Class: `.character-count-warning` with amber/orange color (#ff8800)
  - Class: `.character-count-normal` with default text color
  - Class: `.character-count-icon` for warning icon styling
  - Responsive: Ensure readable on 320px+ viewports

### Integration with Main Textarea
- [ ] [TASK-107] [US1] Add character count display to main JQL textarea in `ui/cards.py` (modify existing JQL input card)
  - Locate existing JQL textarea creation in `ui/cards.py`
  - Add character count display below textarea using `character_count_display()` component
  - Add hidden `dcc.Store(id="jql-character-count-state")` for state management
  - Add `dcc.Interval(id="jql-debounce-interval", interval=300, disabled=True)` for debouncing

### Callback Implementation
- [ ] [TASK-108] [US1] Create character count callback in `callbacks/settings.py`
  - Callback: Listen to JQL textarea value changes, enable debounce interval
  - Callback: After 300ms interval fires, update character count state in dcc.Store
  - Callback: Update character count display based on stored state
  - Pattern: Use `dcc.Interval` enabled/disabled pattern for debouncing (see research.md Q2)
  - Run app: `.\.venv\Scripts\activate; python app.py` and manually test typing

### Integration Testing
- [ ] [TASK-109] [US1] Create `tests/integration/test_jql_character_count.py` with Playwright tests
  - Test: `test_character_count_displays_on_page_load()` - verify "0 / 2000 characters" on fresh load
  - Test: `test_character_count_updates_after_typing()` - type "project = TEST", verify "14 / 2000"
  - Test: `test_character_count_shows_warning_at_threshold()` - paste 1800+ char query, verify warning color
  - Test: `test_character_count_debounces_rapid_typing()` - type rapidly, verify updates at 300ms intervals
  - Run: `.\.venv\Scripts\activate; pytest tests/integration/test_jql_character_count.py -v -s`

### US1 Validation Checkpoint
- [ ] [TASK-110] [US1] Run Quickstart Validation Scenario 1 from `quickstart.md`
  - Manual test: Type short query, verify character count displays
  - Manual test: Type query approaching 1800 chars, verify warning appears
  - Manual test: Verify debouncing works (count doesn't update every keystroke)
  - Manual test: Clear textarea, verify count returns to "0 / 2000 characters"
  - **Success Criteria**: All FR-001, FR-002, FR-003 scenarios pass

- [ ] [TASK-111] [US1] US1 Independent Ship Check - Can we ship this story alone?
  - Verify: Character count works without syntax highlighting
  - Verify: All US1 tests pass independently: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_character_count.py tests/integration/test_jql_character_count.py -v`
  - Verify: No broken functionality if US2/US3 are not implemented
  - **Decision Point**: MVP can be shipped with just US1 if time-constrained

---

## Phase 2: User Story 2 - Syntax Highlighting (Priority P2)

### TDD: Red Phase (Create Failing Tests)
- [ ] [TASK-201] [US2] Create `tests/unit/ui/test_syntax_highlighting.py` with JQL parsing tests
  - Test: `test_parse_jql_keywords()` - verify "AND", "OR", "IN" are detected as keywords
  - Test: `test_parse_jql_strings()` - verify quoted strings like "Done" are detected
  - Test: `test_parse_jql_mixed_query()` - verify complex query with keywords + strings
  - Test: `test_parse_jql_case_insensitive()` - verify "and" and "AND" both recognized
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_syntax_highlighting.py -v` (should FAIL)

- [ ] [TASK-202] [US2] Add test for syntax token rendering
  - Test: `test_render_keyword_token_as_mark_element()` - verify html.Mark with "jql-keyword" class
  - Test: `test_render_string_token_as_mark_element()` - verify html.Mark with "jql-string" class
  - Test: `test_render_plain_text_token()` - verify plain text without wrapping
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_syntax_highlighting.py -k "render" -v` (should FAIL)

### TDD: Green Phase (Implement Minimum Code)
- [ ] [TASK-203] [US2] Create JQL keyword registry in `ui/components.py`
  - Constant: `JQL_KEYWORDS: FrozenSet[str]` with ["AND", "OR", "NOT", "IN", "IS", "WAS", "EMPTY", "NULL", ...] (see data-model.md Section 3)
  - Function: `is_jql_keyword(word: str) -> bool` - case-insensitive keyword detection
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_syntax_highlighting.py::test_parse_jql_keywords -v` (should PASS)

- [ ] [TASK-204] [US2] Create JQL syntax parser in `ui/components.py`
  - Function: `parse_jql_syntax(query: str) -> List[SyntaxToken]` - tokenize query into keywords, strings, operators, text
  - Logic: Split on whitespace, check keywords, detect quoted strings, return list of SyntaxToken dicts
  - See: data-model.md Section 2 for SyntaxToken schema and example
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_syntax_highlighting.py -k "parse" -v` (should PASS)

- [ ] [TASK-205] [US2] Create syntax token renderer in `ui/components.py`
  - Function: `render_syntax_tokens(tokens: List[SyntaxToken]) -> List[html.Mark | str]` - convert tokens to Dash HTML
  - Logic: Wrap keywords in `html.Mark(className="jql-keyword")`, strings in `html.Mark(className="jql-string")`, plain text as-is
  - See: data-model.md Section 2 for rendering example
  - Run: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_syntax_highlighting.py -v` (all tests should PASS)

### CSS Styling
- [ ] [TASK-206] [P] [US2] Add syntax highlighting styles to `assets/custom.css`
  - Class: `.jql-keyword` with blue color (#0066cc), font-weight 600
  - Class: `.jql-string` with green color (#22863a)
  - Class: `.jql-operator` with default color (optional enhancement)
  - Ensure: `background-color: transparent` for all (html.Mark has yellow background by default)

### Integration with Textareas
- [ ] [TASK-207] [US2] Enhance main JQL textarea with syntax highlighting in `ui/cards.py`
  - Modify existing JQL textarea to use `dcc.Textarea` with `children` property for rendered syntax
  - Add callback to re-render textarea children when query changes
  - Use `render_syntax_tokens(parse_jql_syntax(query_value))` in callback

- [ ] [TASK-208] [US2] Enhance save dialog JQL textarea with syntax highlighting in `ui/components.py`
  - Locate save dialog textarea creation (likely in modal component)
  - Apply same syntax highlighting pattern as main textarea
  - Ensure consistency: Same keyword colors, same rendering logic
  - Verify: Character count also appears in dialog (should already work from US1 if using same component)

### Callback Implementation
- [ ] [TASK-209] [US2] Create syntax highlighting callback in `callbacks/settings.py`
  - Callback: Listen to JQL textarea value, parse syntax, update textarea children with html.Mark elements
  - Debounce: Reuse 300ms debounce interval from US1 to prevent performance issues
  - Performance: Benchmark parsing time for 5000-char query (should be <10ms per research.md)
  - Run app: `.\.venv\Scripts\activate; python app.py` and manually test highlighting appears

### Integration Testing
- [ ] [TASK-210] [US2] Create `tests/integration/test_jql_syntax_highlighting.py` with Playwright tests
  - Test: `test_syntax_highlighting_displays_keywords()` - type "project = TEST AND status = Done", verify "AND" is blue
  - Test: `test_syntax_highlighting_displays_strings()` - type 'status = "Done"', verify "Done" is green
  - Test: `test_syntax_highlighting_in_save_dialog()` - open save dialog, verify syntax highlighting works
  - Test: `test_syntax_highlighting_consistency()` - verify main textarea and dialog have identical styling
  - Run: `.\.venv\Scripts\activate; pytest tests/integration/test_jql_syntax_highlighting.py -v -s`

### US2 Validation Checkpoint
- [ ] [TASK-211] [US2] Run Quickstart Validation Scenario 2 from `quickstart.md`
  - Manual test: Type query with keywords, verify "AND", "OR", "IN" highlighted blue
  - Manual test: Type query with strings, verify quoted values highlighted green
  - Manual test: Open save dialog, verify syntax highlighting works in dialog textarea
  - Manual test: Edit query in save dialog, verify highlighting updates
  - **Success Criteria**: All FR-004, FR-005, FR-006 scenarios pass

- [ ] [TASK-212] [US2] US2 Independent Ship Check - Can we ship US1+US2 without US3?
  - Verify: Syntax highlighting works on desktop browsers
  - Verify: All US2 tests pass: `.\.venv\Scripts\activate; pytest tests/unit/ui/test_syntax_highlighting.py tests/integration/test_jql_syntax_highlighting.py -v`
  - Verify: No performance degradation from US1 (character count still works smoothly)
  - **Decision Point**: Desktop-only release acceptable before mobile testing

---

## Phase 3: User Story 3 - Mobile Responsiveness (Priority P3)

### CSS Mobile Optimization
- [ ] [TASK-301] [P] [US3] Add mobile-responsive styles to `assets/custom.css`
  - Media query: `@media (max-width: 767px)` for mobile styles
  - Style: `.jql-textarea` with `font-size: 14px`, `word-wrap: break-word`, `overflow-wrap: break-word`
  - Style: `.character-count-display` with `font-size: 12px`, responsive spacing
  - Style: `.jql-keyword`, `.jql-string` maintain readability on small screens

### Manual Testing (No Automated Tests Required)
- [ ] [TASK-302] [US3] Test on mobile viewport 320px (iPhone SE)
  - Set browser to 320px width
  - Verify: Character count readable without horizontal scroll
  - Verify: Syntax highlighting visible on small screen
  - Verify: JQL textarea text wraps properly, no overflow
  - Verify: Warning color visible and distinguishable

- [ ] [TASK-303] [US3] Test on mobile viewport 375px (iPhone 12/13)
  - Set browser to 375px width
  - Verify: All features from 320px test
  - Verify: Touch targets for textarea are at least 44px
  - Verify: Character count updates smoothly when typing on mobile

- [ ] [TASK-304] [US3] Test on tablet viewport 768px (iPad)
  - Set browser to 768px width
  - Verify: Layout transitions smoothly from mobile to tablet
  - Verify: No layout breaks or text overflow
  - Verify: Character count and syntax highlighting still functional

### US3 Validation Checkpoint
- [ ] [TASK-305] [US3] Run Quickstart Validation Scenario 3 from `quickstart.md` (mobile section)
  - Manual test: Type query on mobile viewport, verify no horizontal scrolling
  - Manual test: Verify character count readable on 320px screen
  - Manual test: Verify syntax highlighting colors distinguishable on mobile
  - Manual test: Verify touch targets meet 44px minimum
  - **Success Criteria**: All FR-007, FR-008, FR-009 scenarios pass

- [ ] [TASK-306] [US3] Full Feature Validation - All user stories complete
  - Run all tests: `.\.venv\Scripts\activate; pytest tests/unit/ui/ tests/integration/ -k "character_count or syntax_highlighting" -v`
  - Verify: All tests pass (unit + integration)
  - Verify: No regressions in existing functionality
  - **Ready for PR**: All 3 user stories implemented and validated

---

## Phase 4: Polish & Documentation

### Code Quality
- [ ] [TASK-401] [P] Run linter on modified files: `.\.venv\Scripts\activate; pylint ui/cards.py ui/components.py callbacks/settings.py`
  - Fix any linting errors or warnings
  - Ensure code follows project conventions

- [ ] [TASK-402] [P] Run type checker if available: `.\.venv\Scripts\activate; mypy ui/cards.py ui/components.py callbacks/settings.py`
  - Add type hints if missing (SyntaxToken, CharacterCountState TypedDicts)
  - Fix any type errors

### Performance Validation
- [ ] [TASK-403] Test performance with large query (5000 characters)
  - Paste 5000-char query into textarea
  - Verify: Character count updates within 300ms
  - Verify: Syntax highlighting renders within 500ms
  - Verify: UI maintains 60fps (use Chrome DevTools Performance tab)
  - **Target**: No dropped frames during typing

### Accessibility Validation
- [ ] [TASK-404] Test with screen reader (NVDA on Windows or Narrator)
  - Start screen reader
  - Type in JQL textarea, verify character count is announced via `aria-live="polite"`
  - Verify warning state is announced when crossing 1800 chars
  - Verify syntax highlighting does not interfere with screen reader (should read plain text)

### Documentation Updates
- [ ] [TASK-405] [P] Update `readme.md` with character count feature description
  - Add section: "JQL Query Enhancements"
  - Document: Real-time character count with 1800-char warning threshold
  - Document: Syntax highlighting for keywords and strings
  - Add screenshot or GIF if possible

- [ ] [TASK-406] [P] Document JQL keyword extensibility in code comments
  - Add docstring to `JQL_KEYWORDS` constant explaining how to extend keyword list
  - Add comment in `parse_jql_syntax()` explaining tokenization approach

---

## Phase 5: Pre-PR Checklist

### Final Quality Gates
- [ ] [TASK-501] Run full test suite: `.\.venv\Scripts\activate; pytest tests/ -v`
  - All unit tests pass
  - All integration tests pass
  - No new test failures introduced

- [ ] [TASK-502] Run test coverage report: `.\.venv\Scripts\activate; pytest --cov=ui --cov=callbacks --cov-report=html`
  - Review coverage for `ui/cards.py`, `ui/components.py`, `callbacks/settings.py`
  - Aim for 90%+ coverage on new code

- [ ] [TASK-503] Manual validation of all Quickstart scenarios
  - Scenario 1 (Character Count): All steps pass ✅
  - Scenario 2 (Syntax Highlighting): All steps pass ✅
  - Scenario 3 (Mobile Responsive): All steps pass ✅

- [ ] [TASK-504] Constitutional compliance check
  - **Article I (Mobile-First)**: Verify 320px+ viewport support ✅
  - **Article III (Performance)**: Verify 60fps maintained, 300ms debounce ✅
  - **Article V (Accessibility)**: Verify screen reader compatibility ✅
  - **Article VI (Simplicity)**: Verify zero new dependencies ✅

### Git & PR Preparation
- [ ] [TASK-505] Commit changes with descriptive message
  ```powershell
  git add ui/cards.py ui/components.py callbacks/settings.py assets/custom.css tests/
  git commit -m "feat: Add JQL character count and syntax highlighting (001-add-jql-query)

  - Add real-time character count with 1800-char warning threshold (US1)
  - Add syntax highlighting for JQL keywords and strings (US2)
  - Add mobile-responsive layout for 320px+ viewports (US3)
  - Include unit tests (test_character_count.py, test_syntax_highlighting.py)
  - Include integration tests (test_jql_character_count.py, test_jql_syntax_highlighting.py)

  Closes #001"
  ```

- [ ] [TASK-506] Push feature branch: `git push origin 001-add-jql-query`

- [ ] [TASK-507] Create pull request with description from `spec.md`
  - Title: "JQL Query Enhancements: Character Count + Syntax Highlighting"
  - Description: Copy "Problem Statement" and "Proposed Solution" sections from spec.md
  - Link to specs directory: Reference `specs/001-add-jql-query/spec.md`
  - Add screenshots: Include before/after images showing character count and syntax highlighting

---

## Estimated Completion

### MVP Scope (User Story 1 Only)
- **Tasks**: TASK-001 to TASK-111 (11 tasks in Phase 1)
- **Estimated Time**: 2-3 hours
- **Deliverable**: Real-time character count with warning threshold
- **Shippable**: Yes - provides immediate value without syntax highlighting

### Full Scope (All User Stories)
- **Tasks**: TASK-001 to TASK-507 (50 tasks across 5 phases)
- **Estimated Time**: 4-6 hours for experienced developer
- **Deliverable**: Character count + syntax highlighting + mobile responsive
- **Shippable**: Yes - complete feature implementation

### Parallel Execution Opportunities
- **Phase 0**: All tasks (TASK-001 to TASK-006) can run in parallel
- **Phase 1**: TASK-106 (CSS) can run parallel with TASK-101 to TASK-105 (tests + implementation)
- **Phase 2**: TASK-206 (CSS) can run parallel with TASK-201 to TASK-205 (tests + implementation)
- **Phase 3**: TASK-301 (CSS) can run parallel with TASK-302 to TASK-304 (manual testing)
- **Phase 4**: TASK-401, TASK-402, TASK-405, TASK-406 can run in parallel

---

## Task Summary

- **Total Tasks**: 50
- **User Story 1 (P1)**: 11 tasks (TASK-101 to TASK-111) - Character count
- **User Story 2 (P2)**: 12 tasks (TASK-201 to TASK-212) - Syntax highlighting
- **User Story 3 (P3)**: 6 tasks (TASK-301 to TASK-306) - Mobile responsive
- **Setup**: 6 tasks (TASK-001 to TASK-006)
- **Polish**: 6 tasks (TASK-401 to TASK-406)
- **Pre-PR**: 7 tasks (TASK-501 to TASK-507)

**Parallelizable Tasks**: 15 tasks marked with `[P]` can execute simultaneously

**Next Action**: Begin with Phase 0 setup tasks, then proceed to User Story 1 (P1) for MVP delivery

**Ready to Start**: ✅ All prerequisites complete, tasks ready for execution
