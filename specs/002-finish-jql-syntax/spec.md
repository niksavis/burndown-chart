# Feature Specification: Complete JQL Syntax Highlighting with Real-time Visual Feedback

**Feature Branch**: `002-finish-jql-syntax`  
**Created**: 2025-10-15  
**Status**: Draft  
**Input**: User description: "Finish JQL syntax highlighting implementation with real-time visual feedback in textarea, supporting native JIRA JQL and ScriptRunner extension syntax"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Visual Syntax Highlighting Overlay (Priority: P1)

As a user typing a JQL query, I want to see syntax highlighting appear in real-time as I type so I can immediately identify keywords, strings, field names, and catch syntax errors before submitting the query.

**Why this priority**: This is the highest priority because it directly addresses the core feature request - making syntax highlighting visible while typing. The existing implementation has parsing functions but no visual display, making them effectively invisible to users. This story delivers the minimum viable visual feedback.

**Independent Test**: Can be fully tested by typing a JQL query in the main textarea and observing colored highlighting appear for keywords (blue), strings (green), and operators (gray) in real-time as each character is typed. Delivers value by preventing syntax errors without requiring query submission.

**Acceptance Scenarios**:

1. **Given** the JQL textarea is empty, **When** I type "project = TEST", **Then** I see "project" in default color, "=" highlighted as an operator, and "TEST" in default color
2. **Given** I have typed "project = ", **When** I type "TEST AND status", **Then** "AND" is immediately highlighted in blue as a keyword
3. **Given** I type "status = ", **When** I type '"Done"' (with quotes), **Then** the entire quoted string including quotes is highlighted in green
4. **Given** I am typing quickly, **When** syntax highlighting updates occur, **Then** the cursor position remains stable and typing is not interrupted
5. **Given** I paste a 500-character JQL query, **When** the paste completes, **Then** syntax highlighting renders across the entire query within 300ms

---

### User Story 2 - ScriptRunner Extension Syntax Support (Priority: P2)

As a ScriptRunner user, I want the syntax highlighter to recognize ScriptRunner-specific functions and keywords (issueFunction in, etc.) so I can compose advanced queries with the same visual guidance as native JIRA JQL.

**Why this priority**: This is secondary because it extends the base syntax highlighting to support a popular JIRA extension. Most users will benefit from P1 (native JQL), while power users with ScriptRunner installed will benefit from this enhancement.

**Independent Test**: Can be fully tested by typing ScriptRunner-specific syntax like "issueFunction in linkedIssuesOf('TEST-1')" and verifying that "issueFunction", "in", and "linkedIssuesOf" are highlighted as keywords/functions. Delivers value independently from P1 by supporting advanced query patterns.

**Acceptance Scenarios**:

1. **Given** I type "issueFunction in", **When** the query contains ScriptRunner syntax, **Then** "issueFunction" and "in" are highlighted as keywords
2. **Given** I type a ScriptRunner function like "linkedIssuesOf", **When** the function name is complete, **Then** it is highlighted as a function (distinct from keywords)
3. **Given** I use multiple ScriptRunner functions in one query, **When** typing the query, **Then** all ScriptRunner functions are recognized and highlighted correctly

---

### User Story 3 - Error Prevention with Invalid Syntax Indication (Priority: P3)

As a user composing a JQL query, I want to see visual indicators for common syntax errors (unclosed quotes, invalid operators) so I can fix them before submitting the query to JIRA.

**Why this priority**: This is tertiary because basic syntax highlighting (P1) already helps users avoid errors by making query structure visible. This story adds explicit error detection, which is helpful but not required for the core functionality.

**Independent Test**: Can be fully tested by typing a query with an unclosed quote (e.g., 'status = "Done) and verifying a subtle visual indicator (underline, different color) appears on the problematic section. Delivers value by catching common errors proactively.

**Acceptance Scenarios**:

1. **Given** I type 'status = "Done' (unclosed quote), **When** I move the cursor away, **Then** the unclosed string is highlighted with a warning indicator (e.g., wavy underline)
2. **Given** I type an invalid operator like "===", **When** the operator is complete, **Then** it is highlighted as an error (e.g., red color)
3. **Given** I type a query with mismatched parentheses, **When** the query is complete, **Then** the problematic parenthesis is highlighted with a warning indicator

---

### Edge Cases

- What happens when a user types a 2000-character query with complex syntax?
  - Expected: Syntax highlighting renders within 300ms, remains performant, no dropped frames during typing
  
- How does the system handle unicode characters and emoji in JQL queries?
  - Expected: Unicode characters are treated as regular text, do not break syntax highlighting, render correctly
  
- What happens when the user rapidly types and deletes keywords (e.g., typing "AND" then backspacing)?
  - Expected: Highlighting updates smoothly, no visual artifacts, cursor remains stable
  
- How does syntax highlighting handle partial keywords during typing (e.g., "A", "AN", "AND")?
  - Expected: Highlighting only applies when a complete keyword is detected (word boundary), prevents false positives
  
- What happens when a user selects and replaces highlighted text?
  - Expected: Selection works normally, replacement text is re-parsed and highlighted, no visual glitches
  
- How does the system handle queries copied from external sources with unusual whitespace?
  - Expected: Syntax highlighting applies correctly regardless of whitespace variations (tabs, multiple spaces, newlines)
  
- What happens on mobile devices when using the textarea with syntax highlighting?
  - Expected: Touch interactions work normally, highlighting remains visible, no performance degradation on mobile CPUs

- What happens when a user accesses the app with an older/unsupported browser?
  - Expected: Graceful degradation - plain textarea displays without syntax highlighting, all core functionality (character count, query input, submission) remains available, no error messages or blocking

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use an established syntax highlighting library component with custom JQL language mode definition (NOT custom dual-layer textarea implementation)
- **FR-002**: System MUST highlight JQL keywords (AND, OR, NOT, IN, IS, WAS, etc.) in blue (#0066cc) with bold font weight
- **FR-003**: System MUST highlight string literals (quoted text) in green (#22863a) including the surrounding quotes
- **FR-004**: System MUST highlight operators (=, !=, <, >, <=, >=, ~, !~) in gray (#6c757d) with medium font weight
- **FR-005**: System MUST update syntax highlighting in real-time as the user types, with maximum 50ms delay from keystroke to highlight update
- **FR-006**: System MUST preserve cursor position and text selection during syntax highlighting updates (library handles natively)
- **FR-007**: System MUST support core ScriptRunner JQL functions (top 15 most commonly used): linkedIssuesOf, issuesInEpics, subtasksOf, parentsOf, epicsOf, hasLinks, hasComments, hasAttachments, lastUpdated, expression, dateCompare, aggregateExpression, issueFieldMatch, linkedIssuesOfRecursive, workLogged
- **FR-008**: System MUST recognize ScriptRunner extension syntax patterns (e.g., "issueFunction in linkedIssuesOf('KEY')")
- **FR-009**: System MUST indicate unclosed strings (quotes) with a warning visual indicator (e.g., red underline or orange background)
- **FR-010**: System MUST indicate invalid operators with error highlighting (e.g., red color)
- **FR-011**: System MUST maintain 60fps during typing with syntax highlighting active for queries up to 5000 characters
- **FR-012**: System MUST integrate via Dash component wrapper function (e.g., create_jql_editor()) that returns configured library component
- **FR-013**: System MUST work on mobile devices (320px+ viewports) without performance degradation
- **FR-014**: System MUST be case-insensitive for keyword matching (AND, and, And all highlighted the same)
- **FR-015**: System MUST support latest versions only of modern browsers (Chrome, Firefox, Safari, Edge) released within last 6 months
- **FR-016**: System MUST gracefully degrade to plain textarea without syntax highlighting when browser lacks required features (no error messages, all core functionality remains available)
- **FR-017**: System MUST define custom JQL language mode with tokenizer rules for keywords, operators, strings, functions, and ScriptRunner extensions
- **FR-018**: System MUST deprecate and remove existing parse_jql_syntax() and render_syntax_tokens() functions from ui/components.py (underperforming code)

### Key Entities

- **JQL Query**: The JIRA Query Language string with syntax highlighting
  - Attributes: query text, parsed tokens, highlighting overlay, cursor position
  - Constraints: Must handle queries up to 5000 characters with <50ms highlight latency

- **JQL Language Mode**: Custom syntax definition for the highlighting library
  - Tokenizer rules: keyword patterns, operator patterns, string literal patterns, function patterns
  - Token types: keyword, string, operator, text, function, error
  - Configuration: case-insensitive keyword matching, ScriptRunner function recognition

- **ScriptRunner Function**: Extended JQL function from ScriptRunner plugin
  - Core functions (top 15): linkedIssuesOf, issuesInEpics, subtasksOf, parentsOf, epicsOf, hasLinks, hasComments, hasAttachments, lastUpdated, expression, dateCompare, aggregateExpression, issueFieldMatch, linkedIssuesOfRecursive, workLogged
  - Additional functions can be added based on user demand
  - Highlighting: Function name in purple (#8b008b) to distinguish from keywords
  - All ScriptRunner functions use "issueFunction in functionName()" pattern

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see syntax highlighting appear within 50ms of typing each character in JQL queries up to 2000 characters (validated with Chrome DevTools Performance profiler)
- **SC-002**: Users typing at 100 words per minute experience zero dropped keystrokes or cursor position glitches (library handles natively)
- **SC-003**: 95% of common JQL syntax errors (unclosed quotes, invalid operators) are visually indicated before query submission
- **SC-004**: Users can compose queries using ScriptRunner syntax with the same visual guidance as native JIRA JQL
- **SC-005**: Syntax highlighting works on mobile devices (iPhone SE, 320px viewport) without causing input lag or visual artifacts
- **SC-006**: Users can select and edit highlighted text without visual glitches or loss of cursor position (library handles natively)
- **SC-007**: Pasting large queries (1000+ characters) results in complete syntax highlighting within 300ms (validated with Chrome DevTools Performance profiler)
- **SC-008**: Deprecated parse_jql_syntax() and render_syntax_tokens() functions are removed from codebase with no remaining references

## Problem Statement *(optional - helps communicate why)*

The current implementation (feature 001-add-jql-query) provides character counting and custom syntax parsing functions (parse_jql_syntax() and render_syntax_tokens()), but the syntax highlighting is not visible to users and the custom parsing implementation has performance issues.

This creates a poor user experience because:
- Users cannot visually distinguish JQL keywords from field names and values
- Syntax errors (unclosed quotes, typos in keywords) are not caught until JIRA rejects the query
- Complex queries with multiple AND/OR conditions are hard to read and verify
- ScriptRunner power users have no visual guidance for extension-specific syntax
- The existing custom parsing functions are underperforming and need to be replaced

The optimal solution is to use an established, battle-tested syntax highlighting library with custom language mode support rather than maintaining a custom implementation. This provides better performance, mobile support, and accessibility out of the box.

## Proposed Solution *(optional - high-level approach)*

Integrate an established syntax highlighting library with custom JQL language mode:

1. **Library Selection**: Use a modern, mobile-friendly syntax highlighting library that supports custom language mode definitions (e.g., CodeMirror 6, Monaco Editor, or similar)
2. **Custom JQL Language Mode**: Define JQL syntax rules including keywords (AND, OR, NOT, etc.), operators (=, !=, ~, etc.), string literals, and ScriptRunner function patterns
3. **Dash Component Wrapper**: Create a `create_jql_editor()` function that wraps the library component and integrates with Dash's component system
4. **Deprecation**: Remove existing underperforming parse_jql_syntax() and render_syntax_tokens() functions - library handles all parsing and rendering
5. **Performance Validation**: Use browser DevTools Performance profiler to verify <50ms update latency and 60fps during typing

This approach provides production-quality syntax highlighting with native mobile support, accessibility features, and better performance than a custom implementation.

## Clarifications

### Session 2025-10-15

- Q: What are the browser compatibility requirements for syntax highlighting? → A: Latest versions only (last 6 months of releases)
- Q: What ScriptRunner functions should be supported in syntax highlighting? → A: Core functions (top 10-15 most commonly used from ScriptRunner documentation)
- Q: What should happen when users access the app with unsupported/older browsers? → A: Graceful degradation (plain textarea, no highlighting)

### Session 2025-10-16

- Q: Should we build a custom dual-layer textarea solution or use an established syntax highlighting component library? → A: Use established syntax highlighting component library (NOT custom dual-layer solution)
- Q: Which syntax highlighting library should we use that supports custom JQL language definitions? → A: Custom syntax definition with flexible library (mobile-friendly, fast, supports custom language modes)
- Q: Should we keep or deprecate the existing parse_jql_syntax() and render_syntax_tokens() functions? → A: Deprecate existing parse/render functions - library handles all parsing and rendering (remove underperforming code)
- Q: How should the syntax highlighting component integrate with the Dash application? → A: Create Dash component wrapper function (e.g., create_jql_editor()) for library component
- Q: How should we validate performance targets (50ms updates, 300ms for large queries)? → A: Use browser DevTools Performance profiler for real-world measurements

## Assumptions *(optional)*

- Modern syntax highlighting libraries (CodeMirror 6, Monaco, etc.) support custom language mode definitions for domain-specific languages like JQL
- Users expect syntax highlighting similar to code editors (VSCode, Sublime Text) with keywords in blue, strings in green
- ScriptRunner extension is commonly used, making support for its syntax a valuable enhancement
- Mobile users will benefit from syntax highlighting despite smaller screen sizes
- The character count feature (from 001-add-jql-query) should continue working alongside syntax highlighting (library provides character count APIs)
- Established libraries provide better performance and maintainability than custom implementations
- Deprecating underperforming custom parsing functions is acceptable when replaced with superior library implementation

## Out of Scope *(optional)*

- **Auto-completion**: Suggesting field names, values, or completing keywords as the user types (future enhancement)
- **Syntax validation**: Checking if the query is semantically valid (e.g., valid field names, valid operators for field types)
- **Query execution**: Running queries or previewing results in the application
- **Multi-cursor editing**: Supporting multiple cursors or selections in the textarea
- **Undo/redo history**: Advanced editing features beyond browser default
- **Dark mode**: Alternative color scheme for syntax highlighting (future enhancement)
- **Accessibility**: Screen reader support and keyboard navigation enhancements (should follow existing patterns but not enhanced)
- **Internationalization**: Non-English JIRA field names or localized keywords

## Dependencies *(optional)*

- **Syntax Highlighting Library**: Requires adding a new dependency for the chosen library (e.g., dash-codemirror, react-monaco-editor, or similar Dash-compatible component)
- **CSS Framework**: Uses Dash Bootstrap Components and assets/custom.css for styling and theme integration
- **Browser APIs**: Modern browsers with ES6+ support (latest versions from last 6 months)
- **ScriptRunner Documentation**: Reference list from https://docs.adaptavist.com/sr4js/latest/features/jql-functions/included-jql-functions (50+ functions available, implementing top 15 core functions initially)
- **Performance Profiling**: Chrome DevTools Performance profiler for validating <50ms latency and 60fps targets

## Risks & Mitigations *(optional)*

- **Risk**: Adding a new library dependency increases bundle size and maintenance burden
  - **Mitigation**: Choose well-maintained library with active community; evaluate bundle size impact; ensure license compatibility; library benefits (performance, mobile support, accessibility) outweigh maintenance cost

- **Risk**: Performance degradation on large queries (2000+ characters) due to real-time highlighting
  - **Mitigation**: Choose library with proven performance at scale; validate with Chrome DevTools Performance profiler; test with 5000-character queries; library should handle debouncing and optimization internally

- **Risk**: Syntax highlighting may conflict with existing character count feature
  - **Mitigation**: Integrate character count using library's APIs (most provide document length methods); test character count accuracy with highlighted queries

- **Risk**: Browser compatibility issues with modern library features
  - **Mitigation**: Target latest browser versions only (last 6 months); implement graceful degradation to plain textarea for unsupported browsers; test on current Chrome, Firefox, Safari, Edge releases

- **Risk**: Users may expect autocomplete or validation features beyond syntax highlighting
  - **Mitigation**: Clearly scope this feature as "visual highlighting only" in documentation; mark advanced features as out of scope

- **Risk**: Library may not support JQL syntax out of the box
  - **Mitigation**: Choose library with flexible custom language mode API; define JQL tokenizer rules based on existing JQL_KEYWORDS and operator patterns; leverage library documentation and examples for custom language modes
