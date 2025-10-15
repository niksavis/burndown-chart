# Feature Specification: JQL Query Enhancements

**Feature Branch**: `001-add-jql-query`  
**Created**: 2025-10-15  
**Status**: Draft  
**Input**: User description: "Add JQL query preview and character count to the Saved Queries dropdown interface"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Character Count Display (Priority: P1)

As a user entering a long JQL query, I want to see the character count in real-time so I can avoid exceeding JIRA's query length limits (typically 1000-2000 characters).

**Why this priority**: This is the highest priority because it prevents a critical failure mode - users submitting queries that are rejected by JIRA due to length limits. This delivers immediate value by providing proactive feedback during query composition.

**Independent Test**: Can be fully tested by typing into the JQL textarea and observing the character count update in real-time. Delivers immediate value by preventing query length errors without requiring query save functionality.

**Acceptance Scenarios**:

1. **Given** the JQL textarea is empty, **When** I type a query, **Then** the character count displays "X / 2000 characters" below the textarea and updates as I type
2. **Given** I have typed 1850 characters, **When** the count exceeds 1800 characters, **Then** the display changes to a warning color (e.g., amber/orange)
3. **Given** I am typing quickly, **When** character count updates occur, **Then** the updates are debounced to 300ms intervals to maintain 60fps performance
4. **Given** I am on a mobile device (320px viewport), **When** viewing the character count, **Then** the display remains readable and does not break the layout

---

### User Story 2 - Syntax Highlighting in Query Input Fields (Priority: P2)

As a user editing a JQL query (in either the main textarea or save dialog), I want to see syntax highlighting so I can visually distinguish keywords, operators, and values for easier query composition and verification.

**Why this priority**: This is secondary because it enhances query readability and composition but isn't required for basic functionality. It adds polish and reduces errors by making query structure more obvious.

**Independent Test**: Can be fully tested by typing JQL in both the main textarea and save dialog, verifying syntax highlighting appears in both locations. Delivers value by improving query composition accuracy without requiring the character count feature.

**Acceptance Scenarios**:

1. **Given** I type a JQL query in the main textarea, **When** the query contains keywords (AND, OR, IN, etc.), **Then** keywords are highlighted in a distinct color
2. **Given** I type a JQL query in the main textarea, **When** the query contains string values (in quotes), **Then** string values are highlighted in a distinct color
3. **Given** I open the save dialog to edit a query, **When** viewing the JQL textarea in the dialog, **Then** the same syntax highlighting is applied as in the main textarea
4. **Given** I am on a mobile device, **When** viewing syntax-highlighted queries, **Then** the highlighting remains readable and does not affect performance

---

### User Story 3 - Mobile-Responsive Layout (Priority: P3)

As a mobile user, I want the character count and query preview to display properly on small screens without breaking the layout.

**Why this priority**: This is tertiary because the features should work on mobile by following existing mobile-first patterns. This story ensures we validate mobile behavior explicitly but the implementation should naturally support mobile.

**Independent Test**: Can be fully tested by resizing the browser to 320px, 768px, and 1024px viewports and verifying all UI elements remain functional and readable.

**Acceptance Scenarios**:

1. **Given** I am on a 320px viewport, **When** viewing the JQL textarea with character count, **Then** the character count displays below the textarea without horizontal scrolling
2. **Given** I am on a mobile device, **When** opening the save modal, **Then** the query preview is readable and does not require horizontal scrolling
3. **Given** I switch between portrait and landscape orientations, **When** viewing the interface, **Then** all elements re-flow appropriately

---

### Edge Cases

- What happens when a user pastes a 5000-character query that exceeds the limit in either textarea?
  - Expected: Character count shows "5000 / 2000 characters" in warning color in the respective textarea, but save is not blocked (JIRA will reject on submission with appropriate error handling)
  
- How does the system handle special characters (emoji, unicode) in character counting?
  - Expected: Count each unicode character as 1 character, matching standard JavaScript string length behavior, consistent across both textareas
  
- What happens when the user rapidly types and deletes text?
  - Expected: Debouncing ensures updates occur at 300ms intervals, preventing excessive re-renders in both character count and syntax highlighting
  
- How does syntax highlighting handle extremely long single-line queries?
  - Expected: Syntax highlighting applies without performance degradation, text wraps naturally, maintains readability
  
- What happens when a user copies text from the main textarea and pastes it into the save dialog (or vice versa)?
  - Expected: Character count and syntax highlighting update immediately in the destination textarea, maintaining consistent behavior
  
- How does the system handle malformed JQL syntax (e.g., unclosed quotes)?
  - Expected: Syntax highlighting does its best-effort highlighting, but no error messages (syntax validation is out of scope)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a character count below ALL JQL textareas (main textarea and save dialog) showing "X / 2000 characters" format
- **FR-002**: System MUST update the character count in real-time as the user types in ANY JQL textarea, with debouncing at 300ms intervals
- **FR-003**: System MUST change the character count display to a warning color when count exceeds 1800 characters in ANY JQL textarea
- **FR-004**: System MUST apply syntax highlighting to JQL keywords (AND, OR, NOT, IN, etc.) in ALL JQL textareas (main and save dialog)
- **FR-005**: System MUST apply syntax highlighting to JQL string values (quoted text) in ALL JQL textareas
- **FR-006**: System MUST apply syntax highlighting to JQL field names and operators in ALL JQL textareas
- **FR-007**: System MUST maintain consistent feature parity between main JQL textarea and save dialog textarea (both have character count + syntax highlighting)
- **FR-008**: System MUST maintain mobile-responsive layout for character count on viewports 320px and wider
- **FR-009**: System MUST match the existing InputGroup design pattern used for the Total Points field
- **FR-010**: System MUST maintain 60fps performance during typing in queries up to 5000 characters with syntax highlighting active
- **FR-011**: Character counting MUST include all characters (whitespace, special characters, unicode) using standard string length calculation

### Key Entities *(include if feature involves data)*

- **JQL Query**: The JIRA Query Language string entered by the user
  - Attributes: query text, character count, syntax-highlighted display
  - Constraints: No maximum enforced by application (JIRA enforces ~2000 char limit)
  - Context: Can be edited in main textarea or save dialog textarea
  
- **Character Count State**: Real-time tracking of query length
  - Attributes: current count, warning threshold (1800), maximum reference (2000)
  - Behavior: Updates debounced at 300ms intervals
  - Scope: Applies to ALL JQL textareas (main and dialog)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see character count update within 300ms of stopping typing in ANY JQL textarea
- **SC-002**: Character count display remains readable on mobile viewports (320px+) without horizontal scrolling
- **SC-003**: Syntax highlighting applies consistently across main textarea and save dialog textarea
- **SC-004**: No performance degradation (60fps maintained) when typing in queries up to 5000 characters with syntax highlighting active
- **SC-005**: Warning color activates when character count exceeds 1800, providing visual feedback before approaching JIRA's limit
- **SC-006**: 100% of users can identify query length status without reading documentation (visual feedback is self-explanatory)
- **SC-007**: Users experience consistent behavior when switching between main textarea and save dialog (no feature loss)

## Assumptions

- JIRA's query length limit is approximately 2000 characters (common limit, but may vary by JIRA instance)
- Users understand that warning color indicates approaching a limit
- The existing InputGroup pattern provides consistent styling that should be reused
- The save modal already contains a JQL textarea that can be enhanced with the same features as the main textarea
- Character counting uses JavaScript string length (UTF-16 code units), which matches JIRA's counting method
- Mobile users expect touch-friendly interfaces following existing mobile-first patterns
- Users expect consistent behavior when editing queries in different contexts (main textarea vs dialog)
- Syntax highlighting can be implemented without requiring a heavyweight code editor component (e.g., Monaco, CodeMirror)

## Dependencies

- Existing JQL textarea component in the main UI
- Existing JQL textarea component in the save modal/dialog
- Existing save modal implementation
- Existing InputGroup design pattern (from Total Points field)
- Existing mobile-first CSS patterns and responsive utilities
- Existing Dash callback infrastructure for real-time updates
- Syntax highlighting library or CSS implementation (to be determined in planning phase)

## Out of Scope

- JQL syntax validation beyond character counting (e.g., checking for valid field names, operators)
- Auto-completion for JQL keywords (e.g., dropdown suggestions while typing)
- Query history or undo/redo functionality
- Customizable character count limits (hardcoded to 2000)
- Advanced syntax highlighting (e.g., error highlighting for invalid syntax)
- Real-time query validation against JIRA API (checking if query will execute successfully)
- Syntax highlighting in non-editable query displays (e.g., saved query list items)

## Non-Functional Requirements

### Performance
- Character count updates must be debounced to 300ms to prevent excessive re-renders
- UI must maintain 60fps during typing in large queries (up to 5000 characters)
- No blocking operations during character counting

### Accessibility
- Character count must be announced to screen readers using aria-live regions
- Warning state must be indicated with color AND text (not color alone)
- All interactive elements must be keyboard navigable

### Mobile-First Design
- All components must work on 320px+ viewports before desktop
- Touch targets must meet 44px minimum size requirement
- Text must be readable without zooming on mobile devices

### Maintainability
- Must follow existing patterns in `.github/copilot-instructions.md`
- Must reuse existing InputGroup design pattern
- Must integrate with existing callback structure in `callbacks/settings.py`
